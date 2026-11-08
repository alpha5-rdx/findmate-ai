"""Streamlit pages. Each public function renders one sidebar destination."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from ai.embedder import ModelLoadError
from ai.matcher import confidence_label, embedding_for, semantic_search
from config import CATEGORIES, MAX_DESC_LEN, MAX_NAME_LEN
from data.sample_data import load_samples
from database import db
from frontend import ui
from utils import auth, files
from utils.validation import clean, validate_report

IMG_TYPES = ["png", "jpg", "jpeg", "webp"]


def _threshold() -> float:
    return float(st.session_state.get("threshold", 0.60))


def _scroll_height(n: int, per_item: int, max_h: int = 640) -> int:
    """Height for a scrollable box: fits few records, caps at max_h and scrolls beyond that."""
    return int(min(max_h, max(n, 1) * per_item + 24))


def _show_errors(errors: list[str]) -> None:
    """One tidy error box listing every problem."""
    st.error("**Please fix the following:**\n\n" + "\n".join(f"- {e}" for e in errors))


# ------------------------------------------------------------ dashboard
def dashboard() -> None:
    s = db.stats(_threshold())
    ui.hero("Bring lost things home.",
            "FindMate AI reads every report by meaning, so a “dark billfold” can still find its "
            "“black leather wallet”.",
            eyebrow="Intelligent Lost & Found",
            chips=[f"{s['open_lost'] + s['open_found']} open cases",
                   f"{s['matches']} AI suggestions", "Semantic matching"])
    # Blue / amber / sky / navy accents stay distinguishable for colour-blind users.
    ui.metric_row([
        ("Lost Items", s["lost"], "🔎", f"{s['open_lost']} still open", "#0B5FFF", "#DCEBFF"),
        ("Found Items", s["found"], "📦", f"{s['open_found']} still open", "#E69F00", "#FFF1D0"),
        ("Potential Matches", s["matches"], "✨", f"at ≥ {_threshold():.0%} similarity", "#56B4E9", "#E3F4FD"),
        ("Resolved Cases", s["resolved"], "✔", "reunited with owners", "#0A1F44", "#E3E8F2")])

    if db.count_items() == 0:
        ui.empty_state("🗂️", "No reports yet",
                       "Submit a lost or found report, or load the sample dataset to try the AI matcher.")
        if st.button("Load sample dataset", type="primary"):
            with st.spinner("Loading samples and computing embeddings (first run downloads the model)..."):
                try:
                    load_samples()
                except ModelLoadError as exc:
                    st.error("Could not load the AI model.")
                    st.code(str(exc))
                    return
            st.rerun()
        return

    left, right = st.columns([3, 2])
    with left:
        ui.section("Top potential matches")
        matches = db.list_matches("pending", _threshold())
        if not matches:
            ui.empty_state("🤝", "No matches above the threshold",
                           "Lower the matching threshold in the sidebar or add more reports.")
        else:
            # Fixed-height box: grows with the data up to a limit, then scrolls.
            with st.container(height=_scroll_height(len(matches), 350, max_h=480)):
                for m in matches:
                    ui.match_card(m)
    with right:
        ui.section("Recent reports")
        items = db.list_items()
        with st.container(height=_scroll_height(len(items), 150, max_h=480)):
            for item in items:
                ui.item_card(item)
    ui.section("How FindMate AI works")
    ui.steps([("Report", "Describe what was lost or found in your own words."),
              ("Understand", "A sentence-embedding model turns each report into meaning."),
              ("Match", "Cosine similarity ranks the closest lost/found pairs."),
              ("Verify", "Confirm ownership, then an admin closes the case.")])


# -------------------------------------------------------------- reports
def report_page(kind: str) -> None:
    lost = kind == "lost"
    ui.hero("Report a Lost Item" if lost else "Report a Found Item",
            "Describe your missing belonging in as much detail as you can." if lost
            else "Describe what you found. We'll look for owners who reported it missing.",
            eyebrow="Lost report" if lost else "Found report",
            chips=["All fields required", "AI-powered matching"])

    # Every widget key includes a counter. After a successful submit the counter is
    # bumped, which gives the form brand-new (empty) widgets ready for the next response.
    # On validation errors the counter is untouched, so the user keeps what they typed.
    n = st.session_state.get(f"form_n_{kind}", 0)
    k = lambda field: f"{kind}_{n}_{field}"  # noqa: E731
    with st.form(f"report_{kind}_{n}"):
        ui.form_header("📝", "Item details", "What does it look like? The more detail, the better the match.")
        c1, c2 = st.columns(2)
        name = c1.text_input("Item name *", max_chars=MAX_NAME_LEN, placeholder="e.g. Black leather wallet",
                             key=k("name"))
        category = c2.selectbox("Category *", CATEGORIES, key=k("category"))
        description = st.text_area(
            "Detailed description *", max_chars=MAX_DESC_LEN, height=110, key=k("desc"),
            placeholder="Colour, brand, size, distinguishing marks, contents... "
                        "Use your own words - the AI understands meaning, not just keywords.")
        c3, c4 = st.columns(2)
        location = c3.text_input("Location lost *" if lost else "Location found *",
                                 placeholder="e.g. Central Library, 2nd floor", key=k("loc"))
        when = c4.date_input("Date lost *" if lost else "Date found *", value=date.today(),
                             max_value=date.today(), key=k("date"))
        ui.form_header("👤", "Contact details", "Shown only to administrators so they can reunite you.")
        c5, c6, c7 = st.columns(3)
        contact_name = c5.text_input("Your name *", placeholder="e.g. Sara Khan", key=k("cname"))
        contact_email = c6.text_input("Your email *", placeholder="name@example.com", key=k("email"))
        contact_number = c7.text_input("Contact number * (11 digits)", placeholder="e.g. 03001234567",
                                       max_chars=11, key=k("phone"))
        ui.form_header("📷", "Photo", "Optional - PNG, JPG or WEBP up to 5 MB.")
        image = st.file_uploader("Photo (optional)", type=IMG_TYPES, label_visibility="collapsed",
                                 key=k("img"))
        submitted = st.form_submit_button("🚀  Submit report", type="primary")

    if submitted:
        errors = validate_report(name, description, category, location, when,
                                 contact_name, contact_email, contact_number)
        if errors:
            _show_errors(errors)
            return
        path, img_err = files.save_image(image)
        if img_err:
            st.error(img_err)
            return
        name, description, location = clean(name), clean(description), clean(location)
        try:
            with st.spinner("Analysing description with the AI model..."):
                vec = embedding_for(name, description, category)
        except ModelLoadError as exc:
            files.remove_image(path)
            st.error("Report not saved: the AI model could not be loaded.")
            st.code(str(exc))
            return
        item_id = db.add_item(kind, name, description, category, location, when, path,
                              clean(contact_name), clean(contact_email).lower(), vec,
                              contact_number=clean(contact_number))
        with st.spinner("Searching for matches..."):
            ui.safe_run_matching()
        st.session_state[f"flash_{kind}"] = item_id          # shown under the fresh, empty form
        st.session_state[f"form_n_{kind}"] = n + 1           # new keys => cleared form
        st.rerun()

    item_id = st.session_state.pop(f"flash_{kind}", None)
    if item_id is not None:
        st.success(f"Report #{item_id} submitted successfully. The form is cleared for your next report.")
        related = [m for m in db.list_matches("pending", _threshold())
                   if m["lost_id" if lost else "found_id"] == item_id]
        if related:
            ui.section(f"{len(related)} potential match(es) found")
            ui.disclaimer()
            for m in related[:5]:
                ui.match_card(m)
        else:
            st.info("No matches yet. We'll keep checking as new reports arrive.")


# -------------------------------------------------------------- matches
def match_results() -> None:
    ui.hero("Match Results", "AI-ranked pairings of lost and found reports, highest similarity first.",
            eyebrow="AI matches", chips=[f"Threshold ≥ {_threshold():.0%}"])
    ui.disclaimer()
    thr = _threshold()
    c1, c2 = st.columns([2, 1])
    with c1:
        ui.infobar(f"🎚️ Showing matches with similarity ≥ <b>{thr:.0%}</b> "
                   "<small>(change in the sidebar)</small>")
    levels = c2.multiselect("Confidence", ["High", "Medium", "Low"], default=["High", "Medium", "Low"],
                            label_visibility="collapsed", placeholder="Confidence levels")
    matches = [m for m in db.list_matches("pending", thr) if confidence_label(m["score"]) in levels]
    if not matches:
        ui.empty_state("🤝", "No potential matches", "Try lowering the threshold, or add more lost/found reports.")
        return
    ui.section(f"{len(matches)} potential match(es)")
    with st.container(height=_scroll_height(len(matches), 350, max_h=540)):  # scrolls when long
        for m in matches:
            ui.match_card(m)


# --------------------------------------------------------------- search
def smart_search() -> None:
    ui.hero("Smart Search", "Describe what you're looking for in plain language - no exact keywords needed.",
            eyebrow="Semantic search", chips=["Understands meaning", "Ranked by similarity"])
    with st.form("search"):
        ui.form_header("🧠", "What are you looking for?", "Write it the way you would say it out loud.")
        query = st.text_input("Describe the item *", label_visibility="collapsed",
                              placeholder="e.g. something I use to unlock my car, with a red tag")
        st.markdown('<div class="fm-tips">Try: <span class="fm-tip">black phone with cracked screen</span>'
                    '<span class="fm-tip">small leather holder with cards</span>'
                    '<span class="fm-tip">bag with a laptop inside</span></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        kind = c1.selectbox("Search in", ["Found reports", "Lost reports", "Both"])
        category = c2.selectbox("Category", ["All"] + CATEGORIES)
        status = c3.selectbox("Status", ["Open cases only", "Include resolved"])
        go = st.form_submit_button("🔎  Search", type="primary")
    if not go:
        return
    if len(clean(query)) < 3:
        _show_errors(["Search text must be at least 3 characters."])
        return
    kind_arg = {"Found reports": "found", "Lost reports": "lost", "Both": None}[kind]
    try:
        with st.spinner("Searching by meaning..."):
            results = semantic_search(query, kind_arg, category, status == "Include resolved")
    except ModelLoadError as exc:
        st.error("The AI model could not be loaded.")
        st.code(str(exc))
        return
    results = [r for r in results if r["similarity"] >= 0.2]  # drop clearly unrelated hits
    if not results:
        ui.empty_state("🔍", "No relevant results", "Try different wording or widen the filters.")
        return
    ui.section(f"{len(results)} result(s) ranked by semantic similarity")
    for r in results:
        ui.item_card(r, r["similarity"])


# --------------------------------------------------------------- manage
def manage_reports() -> None:
    ui.hero("Manage Reports", "View, update or delete the reports you submitted.",
            eyebrow="My reports", chips=["Look up by email"])
    flash = st.session_state.pop("manage_flash", None)  # message set just before a rerun
    if flash:
        st.success(flash)
    with st.form("manage_lookup"):
        ui.form_header("📧", "Find your reports", "Enter the email address you used when reporting.")
        c1, c2 = st.columns([4, 1])
        email_in = c1.text_input("Email", label_visibility="collapsed", placeholder="name@example.com")
        if c2.form_submit_button("Find reports", type="primary"):
            st.session_state["manage_email"] = clean(email_in).lower()
    email = st.session_state.get("manage_email", "")
    if not email:
        ui.empty_state("📧", "Enter your email", "We'll list every report submitted with that address.")
        return
    items = db.list_items(email=email)
    if not items:
        ui.empty_state("📭", "No reports found", "Check the spelling of your email or submit a new report.")
        return
    ui.section(f"{len(items)} report(s) for {email}")
    for it in items:
        with st.expander(f"#{it['id']} · {it['kind'].upper()} · {it['name']} · {it['status']}"):
            ui.item_card(it)
            _edit_form(it)


def _edit_form(it: dict) -> None:
    if it["status"] == "resolved":
        st.info("This case is resolved and can no longer be edited.")
    else:
        with st.form(f"edit_{it['id']}"):
            ui.form_header("✏️", "Edit report", "Changes re-run the AI matching automatically.")
            c1, c2 = st.columns(2)
            name = c1.text_input("Item name", it["name"], max_chars=MAX_NAME_LEN)
            cat = c2.selectbox("Category", CATEGORIES,
                               index=CATEGORIES.index(it["category"]) if it["category"] in CATEGORIES else 0)
            desc = st.text_area("Description", it["description"], max_chars=MAX_DESC_LEN, height=100)
            c3, c4, c5 = st.columns(3)
            loc = c3.text_input("Location", it["location"])
            try:
                d0 = date.fromisoformat(it["event_date"])
            except ValueError:
                d0 = date.today()
            when = c4.date_input("Date", d0, max_value=date.today())
            phone = c5.text_input("Contact number (11 digits)", it.get("contact_number") or "", max_chars=11)
            new_img = st.file_uploader("Replace photo (optional)", type=IMG_TYPES)
            save = st.form_submit_button("💾  Save changes", type="primary")
        if save:
            errs = validate_report(name, desc, cat, loc, when, contact_number=phone)
            if errs:
                _show_errors(errs)
            else:
                path, img_err = files.save_image(new_img)
                if img_err:
                    st.error(img_err)
                    return
                try:
                    vec = embedding_for(clean(name), clean(desc), cat)  # re-embed edited text
                except ModelLoadError as exc:
                    st.error("Could not load the AI model.")
                    st.code(str(exc))
                    return
                if path:
                    files.remove_image(it["image_path"])
                db.update_item(it["id"], clean(name), clean(desc), cat, clean(loc), when,
                               path or it["image_path"], vec, contact_number=clean(phone))
                ui.safe_run_matching()
                st.session_state["manage_flash"] = "✅ Report updated successfully."
                st.rerun()
    if st.button("🗑️  Delete report", key=f"del_{it['id']}"):
        _confirm_delete(it)  # opens the confirmation dialog


@st.dialog("Delete this report?")
def _confirm_delete(it: dict) -> None:
    """Modal confirmation shown before a report is permanently removed."""
    st.markdown(f"You are about to permanently delete **#{it['id']} · {it['name']}**.")
    st.warning("This cannot be undone. Any matches linked to this report will be removed too.")
    yes, no = st.columns(2)
    if yes.button("Yes, delete", key=f"yes_{it['id']}", type="primary"):
        files.remove_image(it["image_path"])
        db.delete_item(it["id"])
        ui.safe_run_matching()
        st.session_state["manage_flash"] = "🗑️ Report deleted successfully."
        st.rerun()
    if no.button("Cancel", key=f"no_{it['id']}"):
        st.rerun()


# ---------------------------------------------------------------- admin
def _chart_colors(df) -> list[str]:
    """Colour-blind-safe series colours: found = amber, lost = blue (columns sorted alphabetically)."""
    palette = {"found": "#E69F00", "lost": "#0B5FFF"}
    return [palette[k] for k in sorted(df["kind"].unique())]


@st.dialog("Sign out of admin?")
def _confirm_signout() -> None:
    st.markdown("**Are you sure you want to sign out of the admin area?**")
    st.caption("You will need the admin password to sign in again.")
    yes, no = st.columns(2)
    if yes.button("Yes, sign out", key="so_yes", type="primary"):
        st.session_state["is_admin"] = False
        st.rerun()
    if no.button("Cancel", key="so_no"):
        st.rerun()


@st.dialog("Resolve this report?")
def _confirm_resolve(m: dict) -> None:
    st.markdown("**Are you sure to resolve this report?**")
    st.markdown(f"{m['lost_name']}  ⇄  {m['found_name']}  ({m['score']:.0%} match)")
    st.info("Both the lost and the found report will be marked as resolved and closed.")
    yes, no = st.columns(2)
    if yes.button("Yes, resolve", key=f"rs_yes_{m['id']}", type="primary"):
        db.resolve_match(m["id"])
        st.session_state["admin_flash"] = "Case resolved - both reports are now closed."
        st.rerun()
    if no.button("Cancel", key=f"rs_no_{m['id']}"):
        st.rerun()


def admin_dashboard() -> None:
    ui.hero("Admin Dashboard", "Review all reports and matches, and close resolved cases.",
            eyebrow="Administration", chips=["Restricted area"])

    # The password comes from Streamlit secrets / an environment variable - never from code.
    # If it is missing, fail closed: keep the area locked and drop any existing admin session.
    admin_password, problem = auth.load_admin_password()
    if admin_password is None:
        st.session_state["is_admin"] = False
        st.error(f"🔒 {problem}")
        st.markdown(auth.SETUP_HELP)
        return

    if not st.session_state.get("is_admin"):
        with st.form("admin_login"):
            ui.form_header("🔐", "Administrator sign in", "Enter the admin password to continue.")
            pw = st.text_input("Admin password", type="password", label_visibility="collapsed",
                               placeholder="Admin password")
            if st.form_submit_button("Sign in", type="primary"):
                if auth.verify_password(pw, admin_password):
                    st.session_state["is_admin"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
        return

    flash = st.session_state.pop("admin_flash", None)
    if flash:
        st.success(flash)

    # Prominent session bar with an amber sign-out button.
    bar, btn = st.columns([3, 1.6])
    with bar:
        ui.infobar("🛡️ Signed in as <b>Administrator</b> <small>· full access to reports and contacts</small>",
                   accent=True)
    with btn:
        if st.button("🚪  Sign out of admin", key="signout"):
            _confirm_signout()

    s = db.stats(_threshold())
    total = s["lost"] + s["found"]
    rate = (s["resolved"] / s["lost"]) if s["lost"] else 0
    ui.metric_row([
        ("Total Reports", total, "🗂️", f"{s['lost']} lost · {s['found']} found", "#0B5FFF", "#DCEBFF"),
        ("Open Cases", s["open_lost"] + s["open_found"], "📂", "awaiting resolution", "#E69F00", "#FFF1D0"),
        ("Pending Matches", s["matches"], "✨", f"≥ {_threshold():.0%}", "#56B4E9", "#E3F4FD"),
        ("Resolution Rate", f"{rate:.0%}", "📈", "resolved / lost reports", "#0A1F44", "#E3E8F2")])

    t1, t2, t3 = st.tabs(["✨ Matches", "🗂️ All reports", "📊 Statistics"])
    with t1:
        pending = db.list_matches("pending", _threshold())
        if not pending:
            ui.empty_state("🤝", "No pending matches", "Nothing to review at the current threshold.")
        for m in pending:
            ui.match_card(m, show_contacts=True)
            if st.button("✔  Mark as resolved", key=f"res_{m['id']}", type="primary"):
                _confirm_resolve(m)
        done = db.list_matches("resolved")
        if done:
            ui.section("Resolved cases")
            df = pd.DataFrame([{"Lost item": m["lost_name"], "Found item": m["found_name"],
                                "Score": f"{m['score']:.0%}"} for m in done])
            st.dataframe(df, hide_index=True)
    with t2:
        df = db.items_dataframe()
        if df.empty:
            ui.empty_state("🗂️", "No reports", "Reports will appear here once submitted.")
        else:
            f1, f2 = st.columns(2)
            kind = f1.selectbox("Type", ["All", "lost", "found"])
            status = f2.selectbox("Status", ["All", "open", "resolved"])
            if kind != "All":
                df = df[df["kind"] == kind]
            if status != "All":
                df = df[df["status"] == status]
            st.dataframe(df.drop(columns=["image_path"]), hide_index=True)
            d1, d2, d3 = st.columns([1, 1, 1])
            d1.download_button("⬇️  Download CSV", df.to_csv(index=False).encode(), "findmate_reports.csv",
                               "text/csv")
            rid = d2.number_input("Re-open report ID", min_value=0, step=1, value=0, label_visibility="collapsed")
            if d3.button("↩️  Re-open report") and rid:
                item = db.get_item(int(rid))
                if item and item["status"] == "resolved":
                    db.reopen_item(int(rid))
                    ui.safe_run_matching()
                    st.rerun()
                else:
                    st.error("No resolved report with that ID.")
    with t3:
        df = db.items_dataframe()
        if df.empty:
            ui.empty_state("📊", "No data yet", "Statistics appear after reports are submitted.")
        else:
            a, b = st.columns(2)
            with a:
                ui.section("Reports by category")
                st.bar_chart(df.groupby(["category", "kind"]).size().unstack(fill_value=0), color=_chart_colors(df))
            with b:
                ui.section("Reports by status")
                st.bar_chart(df.groupby(["status", "kind"]).size().unstack(fill_value=0), color=_chart_colors(df))
            all_m = db.list_matches(min_score=0)
            if all_m:
                ui.section("Match confidence distribution")
                st.bar_chart(pd.Series([confidence_label(m["score"]) for m in all_m]).value_counts())

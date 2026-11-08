"""FindMate AI - entry point. Run with:  streamlit run app.py"""
import streamlit as st

from config import APP_NAME, DEFAULT_THRESHOLD
from database import db
from frontend import pages, ui

st.set_page_config(page_title=f"{APP_NAME} - Lost & Found", page_icon="🔍", layout="wide")
db.init_db()  # creates folders + tables on first run
ui.inject_css()

NAV = {
    "📊  Dashboard": pages.dashboard,
    "🔎  Report Lost Item": lambda: pages.report_page("lost"),
    "📦  Report Found Item": lambda: pages.report_page("found"),
    "✨  Match Results": pages.match_results,
    "🧠  Smart Search": pages.smart_search,
    "🗂️  Manage Reports": pages.manage_reports,
    "🛡️  Admin Dashboard": pages.admin_dashboard,
}

with st.sidebar:
    ui.logo()
    choice = st.radio("Navigation", list(NAV), label_visibility="collapsed")
    st.divider()
    ui.sidebar_settings_header()
    st.slider("Matching threshold", 0.30, 0.95, DEFAULT_THRESHOLD, 0.05, key="threshold",
              help="Minimum similarity for a pair to be shown as a potential match. "
                   "Lower = more (noisier) matches, higher = fewer, stricter matches.")
    ui.sidebar_footer()

NAV[choice]()

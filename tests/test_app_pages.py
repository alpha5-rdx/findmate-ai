"""End-to-end smoke tests with Streamlit's AppTest (runs the real app.py, no browser needed)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from utils import auth

APP = str(Path(__file__).resolve().parent.parent / "app.py")
PW = "unit-test-admin-pw-2026"
ADMIN_PAGE = 6  # index of "Admin Dashboard" in the sidebar menu


def _open(page_index=0, secrets=None, session=None):
    at = AppTest.from_file(APP, default_timeout=120)
    for key, value in (secrets or {}).items():
        at.secrets[key] = value
    for key, value in (session or {}).items():
        at.session_state[key] = value
    at.run()
    if page_index:
        at.sidebar.radio[0].set_value(at.sidebar.radio[0].options[page_index]).run()
    return at


def _all_text(at) -> str:
    parts = [m.value for m in at.markdown] + [e.value for e in at.error] + [c.value for c in at.caption]
    parts += [t.value for t in at.text_input]
    return "\n".join(str(p) for p in parts)


def _is_admin(at) -> bool:
    return "is_admin" in at.session_state and bool(at.session_state["is_admin"])


def _no_secrets(monkeypatch):
    monkeypatch.setattr(auth, "_from_streamlit_secrets", lambda: None)


def test_every_page_renders_without_errors(isolated_db, monkeypatch):
    _no_secrets(monkeypatch)
    at = _open()
    assert not at.exception
    for i, option in enumerate(at.sidebar.radio[0].options):
        at.sidebar.radio[0].set_value(option).run()
        assert not at.exception, f"page {i} ({option!r}) raised: {at.exception}"


def test_admin_is_locked_when_no_password_configured(isolated_db, monkeypatch):
    _no_secrets(monkeypatch)
    at = _open(ADMIN_PAGE)
    assert not at.exception
    assert any("No admin password is configured" in e.value for e in at.error)
    assert len(at.text_input) == 0, "no password box must be offered when auth is unconfigured"
    assert at.session_state["is_admin"] is False
    assert "admin123" not in _all_text(at).lower()  # the old default is never shown or hinted


def test_existing_admin_session_is_dropped_when_config_disappears(isolated_db, monkeypatch):
    _no_secrets(monkeypatch)
    at = _open(ADMIN_PAGE, session={"is_admin": True})
    assert at.session_state["is_admin"] is False
    assert not any("Signed in as" in m.value for m in at.markdown)


def test_login_with_streamlit_secret(isolated_db):
    at = _open(ADMIN_PAGE, secrets={"ADMIN_PASSWORD": PW})
    assert not at.exception
    assert len(at.text_input) == 1 and at.text_input[0].proto.type == 1  # 1 = PASSWORD (masked input)
    at.text_input[0].set_value(PW)
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state["is_admin"] is True
    assert any("Signed in as" in m.value for m in at.markdown)


def test_wrong_password_is_rejected(isolated_db):
    at = _open(ADMIN_PAGE, secrets={"ADMIN_PASSWORD": PW})
    at.text_input[0].set_value("not-the-password")
    at.button[0].click().run()
    assert any("Incorrect password" in e.value for e in at.error)
    assert not _is_admin(at)
    assert PW not in _all_text(at)


def test_old_default_password_no_longer_works(isolated_db):
    at = _open(ADMIN_PAGE, secrets={"ADMIN_PASSWORD": PW})
    at.text_input[0].set_value("admin123")
    at.button[0].click().run()
    assert not _is_admin(at)


def test_configuring_the_revoked_default_keeps_admin_locked(isolated_db):
    at = _open(ADMIN_PAGE, secrets={"ADMIN_PASSWORD": "admin123"})
    assert any("not accepted" in e.value for e in at.error)
    assert len(at.text_input) == 0


def test_environment_variable_fallback(isolated_db, monkeypatch):
    _no_secrets(monkeypatch)
    monkeypatch.setenv(auth.ENV_VAR, PW)
    at = _open(ADMIN_PAGE)
    at.text_input[0].set_value(PW)
    at.button[0].click().run()
    assert at.session_state["is_admin"] is True


def test_admin_pages_work_after_login(isolated_db):
    from data.sample_data import load_samples

    load_samples()  # fictional demo data in the temporary database
    at = _open(ADMIN_PAGE, secrets={"ADMIN_PASSWORD": PW})
    at.text_input[0].set_value(PW)
    at.button[0].click().run()
    assert not at.exception
    assert len(at.tabs) == 3
    assert any("Mark as resolved" in b.label for b in at.button)

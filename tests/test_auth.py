"""Admin password loading / verification (utils/auth.py)."""
from pathlib import Path

import pytest

from utils import auth

STRONG = "correct-horse-battery-staple-42"


def _no_secrets(monkeypatch):
    monkeypatch.setattr(auth, "_from_streamlit_secrets", lambda: None)


def test_missing_configuration_fails_closed(monkeypatch):
    _no_secrets(monkeypatch)
    password, problem = auth.load_admin_password()
    assert password is None
    assert "no admin password" in problem.lower()


def test_unreadable_secrets_file_gives_a_specific_hint_and_stays_locked(monkeypatch):
    _no_secrets(monkeypatch)
    monkeypatch.setattr(auth, "_secrets_file_unreadable", lambda: True)
    password, problem = auth.load_admin_password()
    assert password is None
    assert "could not be read" in problem and "BOM" in problem


def test_secret_is_used(monkeypatch):
    monkeypatch.setattr(auth, "_from_streamlit_secrets", lambda: STRONG)
    assert auth.load_admin_password() == (STRONG, None)


def test_environment_fallback(monkeypatch):
    _no_secrets(monkeypatch)
    monkeypatch.setenv(auth.ENV_VAR, STRONG)
    assert auth.load_admin_password() == (STRONG, None)


def test_secret_takes_priority_over_environment(monkeypatch):
    monkeypatch.setattr(auth, "_from_streamlit_secrets", lambda: "from-secrets-123456")
    monkeypatch.setenv(auth.ENV_VAR, "from-env-123456")
    assert auth.load_admin_password()[0] == "from-secrets-123456"


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_values_are_treated_as_missing(monkeypatch, blank):
    monkeypatch.setattr(auth, "_from_streamlit_secrets", lambda: blank)
    monkeypatch.setenv(auth.ENV_VAR, blank)
    assert auth.load_admin_password()[0] is None


@pytest.mark.parametrize("weak", ["admin123", "ADMIN123", "  admin123 ", "CHANGE-ME-to-a-long-random-password",
                                  "change-me"])
def test_known_defaults_and_template_placeholder_are_rejected(monkeypatch, weak):
    monkeypatch.setattr(auth, "_from_streamlit_secrets", lambda: weak)
    password, problem = auth.load_admin_password()
    assert password is None
    assert "not accepted" in problem
    assert weak.strip() not in problem  # the UI message must not echo the value


def test_blank_secret_falls_through_to_environment(monkeypatch):
    monkeypatch.setattr(auth, "_from_streamlit_secrets", lambda: "")
    monkeypatch.setenv(auth.ENV_VAR, STRONG)
    assert auth.load_admin_password()[0] == STRONG


def test_non_string_secret_is_ignored(monkeypatch):
    # e.g. ADMIN_PASSWORD = 12345 (an int) in secrets.toml must not crash or unlock anything
    monkeypatch.setattr(auth, "_from_streamlit_secrets", lambda: None)
    assert auth.load_admin_password()[0] is None


def test_verify_password():
    assert auth.verify_password(STRONG, STRONG)
    assert not auth.verify_password("wrong", STRONG)
    assert not auth.verify_password("", STRONG)
    assert not auth.verify_password(None, STRONG)
    assert not auth.verify_password(STRONG + " ", STRONG)  # exact match only
    assert auth.verify_password("pässwörd-✓", "pässwörd-✓")  # non-ASCII is safe


def test_setup_help_contains_no_real_secret():
    assert "admin123" not in auth.SETUP_HELP
    assert auth.SECRET_KEY in auth.SETUP_HELP and auth.ENV_VAR in auth.SETUP_HELP


def test_no_hardcoded_default_password_in_source():
    """'admin123' may only appear in the revoked-defaults blocklist and in these tests."""
    root = Path(__file__).resolve().parent.parent
    offenders = []
    for path in root.rglob("*.py"):
        parts = set(path.relative_to(root).parts)
        if parts & {".venv", "venv", "tests", "__pycache__", ".git"}:
            continue
        if "admin123" in path.read_text(encoding="utf8", errors="ignore").lower():
            offenders.append(path.relative_to(root).as_posix())
    assert offenders == ["utils/auth.py"]

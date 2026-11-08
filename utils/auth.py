"""Admin password handling.

The admin password is NEVER stored in source code. It is read at runtime from, in order:

1. Streamlit secrets  -> key ``ADMIN_PASSWORD``  (``.streamlit/secrets.toml`` locally,
   or the app's *Secrets* settings on Streamlit Community Cloud)
2. Environment variable ``FINDMATE_ADMIN_PASSWORD``

If neither is set (or the value is blank / a known-revoked default) the admin area stays
locked and the UI explains how to configure it. Nothing here logs or displays the secret.
"""
from __future__ import annotations

import hmac
import os

SECRET_KEY = "ADMIN_PASSWORD"
ENV_VAR = "FINDMATE_ADMIN_PASSWORD"

# Earlier versions shipped this default and it exists in the public git history,
# so it must never be accepted again, even if someone configures it on purpose.
_REVOKED_DEFAULTS = {"admin123"}
# The template in .streamlit/secrets.toml.example starts with this; copying it unchanged must not unlock admin.
_PLACEHOLDER_PREFIX = "change-me"

SETUP_HELP = f"""\
**Admin access is locked because no admin password is configured.**

Set one of the following (use a long, random, unique password):

1. **Streamlit secrets** (recommended). Local: create `.streamlit/secrets.toml`; \
Streamlit Community Cloud: *App settings → Secrets*.
```toml
{SECRET_KEY} = "your-long-random-password"
```
2. **Environment variable**
```bash
export {ENV_VAR}="your-long-random-password"      # Windows PowerShell: $env:{ENV_VAR}="..."
```
Then restart the app."""


def _from_streamlit_secrets() -> str | None:
    """Value of ``ADMIN_PASSWORD`` in Streamlit secrets, or None if absent/unreadable."""
    try:
        import streamlit as st

        value = st.secrets.get(SECRET_KEY)  # raises when no secrets file exists
    except Exception:  # no secrets file / malformed TOML / not running under Streamlit
        return None
    return value if isinstance(value, str) else None


def _secrets_file_unreadable() -> bool:
    """True when a secrets file exists but cannot be parsed (invalid TOML, or a UTF-8 BOM)."""
    try:
        import streamlit as st

        st.secrets.get(SECRET_KEY)
    except Exception as exc:
        return "parsing" in str(exc).lower()  # Streamlit: "Error parsing secrets file at ..."
    return False


def _from_environment() -> str | None:
    return os.environ.get(ENV_VAR)


def load_admin_password() -> tuple[str | None, str | None]:
    """Return ``(password, problem)``.

    ``password`` is None when admin access must stay locked; ``problem`` then holds a
    short, secret-free reason that is safe to show in the UI.
    """
    for candidate in (_from_streamlit_secrets(), _from_environment()):
        if candidate is None or not candidate.strip():
            continue  # unset or blank -> try the next source
        lowered = candidate.strip().lower()
        if lowered in _REVOKED_DEFAULTS or lowered.startswith(_PLACEHOLDER_PREFIX):
            return None, ("The configured admin password is a publicly known default or a template "
                          "placeholder and is not accepted. Choose your own password.")
        return candidate, None
    if _secrets_file_unreadable():
        return None, ("A secrets file was found but could not be read. Check its TOML syntax and save it "
                      "as UTF-8 without a BOM (Windows Notepad / PowerShell can add one).")
    return None, "No admin password is configured."


def verify_password(candidate: str, expected: str) -> bool:
    """Constant-time comparison (avoids leaking how many characters matched)."""
    return hmac.compare_digest((candidate or "").encode("utf-8"), expected.encode("utf-8"))

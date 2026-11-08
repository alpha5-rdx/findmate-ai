"""Input validation helpers. Each returns a list of human-readable errors."""
from __future__ import annotations

import re
from datetime import date

from config import (CATEGORIES, MAX_DESC_LEN, MAX_LOCATION_LEN, MAX_NAME_LEN,
                    MIN_DESC_LEN)

MIN_FIELD_LEN = 3  # every text field needs at least this many characters
# must contain "@" and the domain must contain ".com" (e.g. a@b.com, a@b.com.pk)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]*[^@\s.]\.com(\.[A-Za-z]{2,})?$", re.IGNORECASE)
PHONE_RE = re.compile(r"^[0-9]{11}$")  # exactly 11 digits, numbers only


def clean(text) -> str:
    """Normalise whitespace; tolerate None / non-string input."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _too_short(value: str, label: str, errors: list[str]) -> bool:
    if len(value) < MIN_FIELD_LEN:
        errors.append(f"{label} must be at least {MIN_FIELD_LEN} characters.")
        return True
    return False


def validate_report(name, description, category, location, event_date,
                    contact_name=None, contact_email=None, contact_number=None) -> list[str]:
    """Contact fields are optional arguments: pass None to skip them (used by the edit form)."""
    errors: list[str] = []
    name, description, location = clean(name), clean(description), clean(location)

    if not _too_short(name, "Item name", errors) and len(name) > MAX_NAME_LEN:
        errors.append(f"Item name must be at most {MAX_NAME_LEN} characters.")

    if not _too_short(description, "Description", errors):
        if len(description) < MIN_DESC_LEN:
            errors.append(f"Description must be at least {MIN_DESC_LEN} characters "
                          "(colour, brand, marks) - detailed text gives better matches.")
        elif len(description) > MAX_DESC_LEN:
            errors.append(f"Description must be at most {MAX_DESC_LEN} characters.")

    if category not in CATEGORIES:
        errors.append("Please choose a valid category.")

    if not _too_short(location, "Location", errors) and len(location) > MAX_LOCATION_LEN:
        errors.append(f"Location must be at most {MAX_LOCATION_LEN} characters.")

    if not isinstance(event_date, date):
        errors.append("A valid date is required.")
    elif event_date > date.today():
        errors.append("The date cannot be in the future.")

    if contact_name is not None:
        _too_short(clean(contact_name), "Your name", errors)

    if contact_email is not None:
        email = clean(contact_email)
        if not _too_short(email, "Email", errors) and not EMAIL_RE.match(email):
            errors.append("Email must contain '@' and '.com' (e.g. name@example.com).")

    if contact_number is not None:
        phone = clean(contact_number)
        if not PHONE_RE.match(phone):
            errors.append("Contact number must be exactly 11 digits (numbers only, no spaces, + or dashes).")
    return errors

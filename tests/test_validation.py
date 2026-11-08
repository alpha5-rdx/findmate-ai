"""Form validation rules (utils/validation.py)."""
from datetime import date, timedelta

import pytest

from utils.validation import validate_report


def _errors(**over):
    args = dict(name="Black wallet", description="Black leather wallet with cards", category="Wallets & Bags",
                location="Central Library", event_date=date.today(), contact_name="Sara Khan",
                contact_email="sara@example.com", contact_number="03001234567")
    args.update(over)
    return validate_report(args["name"], args["description"], args["category"], args["location"],
                           args["event_date"], args["contact_name"], args["contact_email"],
                           args["contact_number"])


def test_valid_report_has_no_errors():
    assert _errors() == []


@pytest.mark.parametrize("phone", ["0300123456", "030012345678", "0300-123456", "+9230012345", "abcdefghijk", ""])
def test_contact_number_must_be_exactly_11_digits(phone):
    assert any("11 digits" in e for e in _errors(contact_number=phone))


@pytest.mark.parametrize("email", ["a@b.org", "ab.com", "a@bcom", "@b.com", "a b@c.com"])
def test_email_needs_at_sign_and_dot_com(email):
    assert any("Email" in e for e in _errors(contact_email=email))


def test_future_date_rejected():
    assert any("future" in e for e in _errors(event_date=date.today() + timedelta(days=2)))


def test_short_fields_rejected():
    errs = _errors(name="ab", location="ab", contact_name="ab")
    assert sum("at least 3" in e for e in errs) >= 3

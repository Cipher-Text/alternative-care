"""Bangladesh mobile number handling for patient identity (ADR 009)."""

import re

_BD_MOBILE = re.compile(r"^(?:\+?88)?(01[3-9][0-9]{8})$")


def normalize_bd_mobile(raw: str) -> str:
    """Return the canonical +8801XXXXXXXXX form, or raise ValueError.

    Accepts 01711111111, 8801711111111 and +8801711111111, with spaces, dashes or brackets.
    Only Bangladesh mobile numbers are supported in this phase."""
    cleaned = re.sub(r"[\s\-()]", "", raw or "")
    match = _BD_MOBILE.match(cleaned)
    if not match:
        raise ValueError("Enter a Bangladesh mobile number, e.g. 01711111111")
    return "+88" + match.group(1)


def mask_phone(phone: str) -> str:
    """For logs and responses: +88017*****111."""
    return phone[:6] + "*" * max(0, len(phone) - 9) + phone[-3:] if len(phone) > 9 else "***"

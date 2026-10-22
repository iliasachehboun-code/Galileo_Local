"""Code oracle: a span may contain masked text, never a clear personal value.

The scanner returns kinds (`email`, `phone`, `iban`, `long_digit_run`), never
the matched text, so a failure cannot copy the value into a log or a trace.
"""

from __future__ import annotations

import re

_TOKEN = re.compile(r"\[[A-Z][A-Z0-9_]{1,48}\]")
_INVISIBLE = re.compile(
    r"[\u00ad\u200b\u200c\u200d\u200e\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff]"
)
_EMAIL = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.IGNORECASE)
_IBAN = re.compile(
    r"\b[A-Z]{2}\s*\d{2}(?:\s*[A-Z0-9]){11,30}\b",
    re.IGNORECASE,
)
_PHONE = re.compile(r"(?:\+212|0)\s*[5-7](?:\s*\d){8}\b")
_LONG_DIGITS = re.compile(r"\b\d{12,}\b")

_FORBIDDEN_KEYS = frozenset(
    {
        "cin",
        "rib",
        "email",
        "phone",
        "plaintext",
        "clear_value",
        "raw_pii",
        "secret",
    }
)


def find_clear_pii(text: str) -> list[str]:
    """Kinds of clear personal data found in ``text``.

    Masked placeholders such as ``[CIMR_CIN_abcd1234]`` are removed before
    the scan. They are the allowed form of a personal value. An invisible
    character is deleted only for the email scan. For an IBAN, a phone and a
    long digit run it stays a break, so a word prefix is not glued on.
    """
    scrubbed = _TOKEN.sub(" ", text)
    found: list[str] = []
    if _EMAIL.search(_INVISIBLE.sub("", scrubbed)):
        found.append("email")
    if _PHONE.search(scrubbed):
        found.append("phone")
    if _IBAN.search(scrubbed):
        found.append("iban")
    if _LONG_DIGITS.search(scrubbed):
        found.append("long_digit_run")
    return found


def forbidden_metadata_keys(keys: list[str]) -> list[str]:
    """Metadata keys that would admit a clear personal value."""
    return sorted({key for key in keys if key.strip().lower() in _FORBIDDEN_KEYS})

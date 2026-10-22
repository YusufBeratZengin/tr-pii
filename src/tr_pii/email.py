"""Practical ASCII email detection, without DNS or SMTP requests."""

import re
from collections.abc import Iterator

from ._shared import candidates
from .models import Match

_ATOM = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
_BODY = _ATOM + r"(?:\." + _ATOM + r")*@(?:" + _LABEL + r"\.)+[A-Za-z]{2,63}"
_FORMAT = re.compile(_BODY)
# Prevent matching a valid-looking suffix of a malformed email or Unicode local part.
_PATTERN = re.compile(r"(?<![\w.!#$%&'*+/=?^`{|}~@-])" + _BODY + r"(?![\w@-])")


def validate_email(value: str) -> bool:
    """Accept common unquoted ASCII mailboxes with a dotted DNS-style domain."""
    if len(value) > 254 or _FORMAT.fullmatch(value) is None:
        return False
    local, domain = value.rsplit("@", 1)
    return len(local) <= 64 and len(domain) <= 253


def detect(text: str) -> Iterator[Match]:
    return candidates(text, _PATTERN, validate_email, "EMAIL", 0.99)

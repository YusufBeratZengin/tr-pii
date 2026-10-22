"""IPv4 and IPv6 detection using the standard library's address validator."""

import ipaddress
import re
from collections.abc import Iterator

from ._shared import candidates
from .models import Match

_V4 = re.compile(r"(?<![\w.:])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?!\w|\.[0-9])")
_V6 = re.compile(r"(?<![\w:])(?=[0-9A-Fa-f:.]*:)[0-9A-Fa-f:.]*:[0-9A-Fa-f:.]+(?![\w:])")


def validate_ip(value: str) -> bool:
    """Validate a bare IPv4/IPv6 address (no zone ID, brackets, port or CIDR)."""
    if "%" in value or "/" in value:
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def detect(text: str) -> Iterator[Match]:
    yield from candidates(text, _V4, validate_ip, "IP", 0.97)
    for candidate in _V6.finditer(text):
        # A terminal sentence full stop is punctuation, not part of an IPv6 address.
        value = candidate.group().rstrip(".")
        if ":" in value and validate_ip(value):
            yield Match("IP", candidate.start(), candidate.start() + len(value), value, 0.97)


"""Turkish identity number checksum validation; no registry lookup."""

import re
from collections.abc import Iterator

from ._shared import candidates, digits
from .models import Match

_BODY = r"(?:[1-9][0-9]{10}|[1-9][0-9]{2}([ .\u00a0])[0-9]{3}\1[0-9]{3}\1[0-9]{2})"
_FORMAT = re.compile(_BODY)
_PATTERN = re.compile(r"(?<!\w)" + _BODY + r"(?!\w)")


def validate_tckn(value: str) -> bool:
    """Accept compact or consistently separated 3-3-3-2 ASCII digits."""
    if _FORMAT.fullmatch(value) is None:
        return False
    numbers = [int(char) for char in digits(value)]
    tenth = (7 * sum(numbers[0:9:2]) - sum(numbers[1:8:2])) % 10
    return numbers[9] == tenth and numbers[10] == sum(numbers[:10]) % 10


def detect(text: str) -> Iterator[Match]:
    return candidates(text, _PATTERN, validate_tckn, "TCKN", 0.99)

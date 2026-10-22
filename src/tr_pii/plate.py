"""Ordinary Turkish province-letter-serial registration plates."""

import re
from collections.abc import Iterator

from ._shared import HSPACE, candidates
from .models import Match

_LETTER = r"[A-PR-VYZa-pr-vyz]"  # ASCII alphabet excluding Q, W and X.
_BODY = (
    r"(?:0[1-9]|[1-7][0-9]|8[01])"
    + HSPACE
    + r"*(?:"
    + _LETTER
    + HSPACE
    + r"*[0-9]{4}|"
    + _LETTER
    + r"{2}"
    + HSPACE
    + r"*[0-9]{3,4}|"
    + _LETTER
    + r"{3}"
    + HSPACE
    + r"*[0-9]{2,3})"
)
_FORMAT = re.compile(_BODY)
_PATTERN = re.compile(r"(?<!\w)" + _BODY + r"(?!\w)")


def validate_plate(value: str) -> bool:
    """Validate ordinary shapes (lowercase only when compact); no allocation lookup."""
    if _FORMAT.fullmatch(value) is None:
        return False
    # Lowercase is accepted only in compact form; spaced text like "42 at 100"
    # is ordinary prose, so spaced plates require uppercase letters.
    return not (re.search(HSPACE, value) and value != value.upper())


def detect(text: str) -> Iterator[Match]:
    return candidates(text, _PATTERN, validate_plate, "PLATE", 0.75)

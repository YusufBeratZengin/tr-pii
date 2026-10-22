"""Ten-digit Turkish tax number validation."""

import re
from collections.abc import Iterator

from ._shared import candidates, is_digits
from .models import Match

_PATTERN = re.compile(r"(?<!\w)[0-9]{10}(?!\w)")


def check_digit(prefix: str) -> str:
    """Calculate the check digit of a nine-digit ASCII prefix."""
    if not is_digits(prefix, 9):
        raise ValueError("VKN prefix must contain exactly 9 ASCII digits")
    total = 0
    for index, char in enumerate(prefix):
        shift = 9 - index
        adjusted = (int(char) + shift) % 10
        residue = (adjusted * 2**shift) % 9
        total += (residue or 9) if adjusted else 0
    return str(-total % 10)


def validate_vkn(value: str) -> bool:
    """Check format and checksum, including prefixes beginning with zero."""
    return is_digits(value, 10) and check_digit(value[:9]) == value[9]


def detect(text: str) -> Iterator[Match]:
    return candidates(text, _PATTERN, validate_vkn, "VKN", 0.85)

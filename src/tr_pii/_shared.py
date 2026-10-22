"""Small internal helpers shared by detectors."""

import re
from collections.abc import Callable, Iterator

from .models import Match

HSPACE = r"[ \t\u00a0]"
ASCII_DIGITS = re.compile(r"[0-9]+\Z")


def digits(value: str, separators: str = " .-\t\u00a0") -> str:
    """Strip only the explicitly permitted separators, never arbitrary letters."""
    return value.translate(str.maketrans("", "", separators))


def is_digits(value: str, length: int) -> bool:
    return len(value) == length and ASCII_DIGITS.fullmatch(value) is not None


def candidates(
    text: str,
    pattern: re.Pattern[str],
    validator: Callable[[str], bool],
    kind: str,
    confidence: float,
    group: int | str = 0,
) -> Iterator[Match]:
    for candidate in pattern.finditer(text):
        value = candidate.group(group)
        if validator(value):
            start, end = candidate.span(group)
            yield Match(kind, start, end, value, confidence)

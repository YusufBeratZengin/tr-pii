"""Luhn validation for 13–19 digit card candidates."""

import re
from collections.abc import Iterator

from ._shared import candidates, digits
from .models import Match

_FORMAT = re.compile(r"[0-9](?:[ -]?[0-9]){12,18}")
_PATTERN = re.compile(
    r"(?<![\w-])(?<![0-9] )[0-9](?:[ -]?[0-9]){12,18}(?![\w-]|[ -]?[0-9])"
)


def luhn_sum(value: str) -> int:
    total = 0
    for index, char in enumerate(reversed(value)):
        number = int(char) * (2 if index % 2 else 1)
        total += number - 9 if number > 9 else number
    return total


def validate_credit_card(value: str) -> bool:
    """Validate length and Luhn; issuer allocation is deliberately not checked."""
    if _FORMAT.fullmatch(value) is None:
        return False
    compact = digits(value, " -")
    return len(set(compact)) > 1 and luhn_sum(compact) % 10 == 0


def detect(text: str) -> Iterator[Match]:
    return candidates(text, _PATTERN, validate_credit_card, "CREDIT_CARD", 0.90)


"""MERSIS (central trade registry) numbers, detected only after an explicit label."""

import re
from collections.abc import Iterator

from ._shared import candidates, digits, is_digits
from .models import Match

_PATTERN = re.compile(
    r"(?<!\w)mers[iİı]s(?!\w)(?:[ \t]+(?:no|numaras[ıi])(?!\w))?\.?[ \t]*[:=]?[ \t]*"
    r"(?P<number>[0-9](?:[ \t\-]?[0-9]){15})(?![\w])",
    re.IGNORECASE,
)


def validate_mersis(value: str) -> bool:
    """Validate 16 ASCII digits (spaces or hyphens allowed); no public checksum exists."""
    return is_digits(digits(value, " -\t"), 16)


def detect(text: str) -> Iterator[Match]:
    return candidates(text, _PATTERN, validate_mersis, "MERSIS", 0.92, "number")

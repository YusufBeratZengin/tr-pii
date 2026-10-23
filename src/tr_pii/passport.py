"""Turkish passport serial numbers, detected only after an explicit label."""

import re
from collections.abc import Iterator

from ._shared import candidates
from .models import Match

_SHAPE = re.compile(r"[A-Z][0-9]{7,8}", re.ASCII)
_PATTERN = re.compile(
    r"(?<!\w)(?:pasaport|passport)(?!\w)(?:[ \t]+(?:no|numaras[ıi]|number)(?!\w))?"
    r"\.?[ \t]*[:=#]?[ \t]*(?P<serial>[A-Za-z][0-9]{7,8})(?!\w)",
    re.IGNORECASE,
)


def validate_passport(value: str) -> bool:
    """Validate the serial shape: one uppercase ASCII letter and 7 or 8 digits.

    There is no public checksum, so this checks structure only.
    """
    return _SHAPE.fullmatch(value) is not None


def _upper_shape(value: str) -> bool:
    return validate_passport(value.upper())


def detect(text: str) -> Iterator[Match]:
    return candidates(text, _PATTERN, _upper_shape, "PASSPORT", 0.85, "serial")

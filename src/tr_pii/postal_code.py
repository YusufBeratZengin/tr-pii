"""Turkish postal-code shapes, detected only after an explicit label."""

import re
from collections.abc import Iterator

from ._shared import candidates, is_digits
from .models import Match

_PATTERN = re.compile(
    r"(?<!\w)(?:posta[ \t]+kodu|PK)\.?[ \t]*[:=]?[ \t]*(?P<code>[0-9]{5})(?!\w)",
    re.IGNORECASE,
)


def validate_postal_code(value: str) -> bool:
    """Validate five ASCII digits with a province prefix 01–81, not assignment."""
    return is_digits(value, 5) and 1 <= int(value[:2]) <= 81


def detect(text: str) -> Iterator[Match]:
    return candidates(text, _PATTERN, validate_postal_code, "POSTAL_CODE", 0.80, "code")

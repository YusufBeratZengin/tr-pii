"""Public result model. Offsets refer to the original Python string."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Match:
    """An immutable finding with an exclusive end and a heuristic confidence."""

    type: str
    start: int
    end: int
    value: str
    confidence: float


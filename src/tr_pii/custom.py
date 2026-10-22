"""Explicit user terms; no built-in names, guesses or external dictionary."""

import re
from collections.abc import Iterable, Iterator

from .models import Match

_TURKISH_LOWER = str.maketrans({"I": "ı", "İ": "i"})


def turkish_lower(value: str) -> str:
    """Lowercase without merging the distinct Turkish i/ı letter pairs."""
    return value.translate(_TURKISH_LOWER).lower()


def validate_custom_term(value: str, term: str) -> bool:
    return bool(term.strip()) and turkish_lower(value) == turkish_lower(term)


def _case_pattern(term: str) -> str:
    # Per-character alternatives preserve original offsets even for Unicode
    # lowercase mappings that expand into more than one code point.
    parts: list[str] = []
    for char in term:
        if char in "iİ":
            parts.append("[iİ]")
        elif char in "ıI":
            parts.append("[ıI]")
        elif len(char.lower()) == 1 and len(char.upper()) == 1:
            variants = "".join(sorted({char.lower(), char.upper()}))
            parts.append("[" + re.escape(variants) + "]")
        else:
            parts.append(re.escape(char))
    return "".join(parts)


def detect(text: str, terms: Iterable[str]) -> Iterator[Match]:
    if isinstance(terms, str):
        raise ValueError("custom_terms must be an iterable of strings, not a single string")
    unique: dict[str, str] = {}
    for term in terms:
        if not term.strip():
            raise ValueError("Custom terms must not be empty or whitespace-only")
        unique.setdefault(turkish_lower(term), term)
    if not unique:
        return
    # Longest first handles terms sharing a start. Lookahead also finds
    # overlapping phrases with different starts for the central resolver.
    choices = "|".join(
        _case_pattern(term) for term in sorted(unique.values(), key=len, reverse=True)
    )
    pattern = re.compile(r"(?<!\w)(?=(" + choices + r")(?!\w))")
    for candidate in pattern.finditer(text):
        start, end = candidate.span(1)
        yield Match("CUSTOM", start, end, candidate.group(1), 1.0)


"""Detection orchestration, overlap selection and masking."""

import hashlib
import ipaddress
import random
from collections.abc import Callable, Iterable, Iterator
from typing import Literal

from . import (
    credit_card,
    custom,
    email,
    iban,
    ip,
    mersis,
    passport,
    phone,
    plate,
    postal_code,
    tckn,
    vkn,
)
from . import fake as _fake
from ._shared import digits
from .models import Match

Style = Literal["tag", "stars", "partial", "hash", "redact", "fake"]
STYLES = ("tag", "stars", "partial", "hash", "redact", "fake")
_DETECTORS: dict[str, Callable[[str], Iterator[Match]]] = {
    "TCKN": tckn.detect,
    "VKN": vkn.detect,
    "IBAN": iban.detect,
    "PHONE": phone.detect,
    "EMAIL": email.detect,
    "CREDIT_CARD": credit_card.detect,
    "PLATE": plate.detect,
    "IP": ip.detect,
    "POSTAL_CODE": postal_code.detect,
    "PASSPORT": passport.detect,
    "MERSIS": mersis.detect,
}
TYPES = (*_DETECTORS, "CUSTOM")


def _select_types(types: Iterable[str] | None) -> set[str]:
    if types is None:
        return set(TYPES)
    if isinstance(types, str):
        raise ValueError("types must be an iterable of type names, not a single string")
    selected = {kind.upper() for kind in types}
    unknown = selected.difference(TYPES)
    if unknown:
        raise ValueError("Unknown PII types: " + ", ".join(sorted(unknown)))
    return selected


def find(
    text: str,
    types: Iterable[str] | None = None,
    *,
    custom_terms: Iterable[str] = (),
) -> list[Match]:
    """Return non-overlapping findings in source order.

    Higher confidence wins; ties prefer length, then earlier start, then type.
    Offsets are Unicode code-point indices, with an exclusive end.
    """
    selected = _select_types(types)
    findings = [
        match
        for kind, detector in _DETECTORS.items()
        if kind in selected
        for match in detector(text)
    ]
    if "CUSTOM" in selected:
        findings.extend(custom.detect(text, custom_terms))
    if not findings:
        return []
    ranked = sorted(
        findings,
        key=lambda item: (-item.confidence, -(item.end - item.start), item.start, item.type),
    )
    occupied = bytearray(len(text))
    accepted: list[Match] = []
    for match in ranked:
        if occupied.find(b"\x01", match.start, match.end) < 0:
            accepted.append(match)
            occupied[match.start : match.end] = b"\x01" * (match.end - match.start)
    return sorted(accepted, key=lambda item: item.start)


def _canonical(match: Match) -> str:
    if match.type == "PHONE":
        return phone.national_number(match.value)
    if match.type == "IBAN":
        return iban.compact_iban(match.value)
    if match.type in {"TCKN", "VKN", "CREDIT_CARD", "POSTAL_CODE", "MERSIS"}:
        return digits(match.value)
    if match.type == "IP":
        return str(ipaddress.ip_address(match.value))
    if match.type == "PASSPORT":
        return match.value.upper()
    if match.type == "PLATE":
        return "".join(match.value.split()).upper()
    if match.type == "EMAIL":
        local, domain = match.value.rsplit("@", 1)
        return local + "@" + domain.lower()
    return custom.turkish_lower(match.value)


def _replacement(match: Match, style: Style, salt: str | None, seed: int = 0) -> str:
    if style == "tag":
        return f"[{match.type}]"
    if style == "redact":
        return "[REDACTED]"
    if style == "fake":
        return _fake.like(match.type, match.value, _canonical(match), seed)
    if style == "stars":
        return "*" * len(match.value)
    if style == "hash":
        # Length framing prevents ambiguities between salt, type and value.
        assert salt is not None
        parts = (salt, match.type, _canonical(match))
        payload = "".join(f"{len(part)}:{part}" for part in parts).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()[:16]
        return f"[{match.type}:{digest}]"
    visible = {
        "TCKN": 2,
        "VKN": 2,
        "PHONE": 4,
        "IBAN": 4,
        "CREDIT_CARD": 4,
        "POSTAL_CODE": 2,
        "PLATE": 2,
        "PASSPORT": 2,
        "MERSIS": 2,
    }.get(match.type)
    if visible is None:
        return "*" * len(match.value)
    # Keep only the requested final digits, never a name or email fragment.
    digit_positions = [i for i, char in enumerate(match.value) if "0" <= char <= "9"]
    keep = set(digit_positions[-visible:])
    return "".join(char if i in keep else "*" for i, char in enumerate(match.value))


def _validate_style(style: str, salt: str | None) -> None:
    if style not in STYLES:
        raise ValueError("style must be one of: " + ", ".join(STYLES))
    if style == "hash" and not salt:
        raise ValueError("A non-empty salt is required for hash masking")


def _mask_spans(
    text: str, matches: list[Match], style: Style, salt: str | None, seed: int = 0
) -> tuple[str, list[tuple[int, int, str]]]:
    """Return masked text and, per match, its (start, end, replacement) in the output."""
    chunks: list[str] = []
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    length = 0
    for match in matches:
        before = text[cursor : match.start]
        replacement = _replacement(match, style, salt, seed)
        chunks.extend((before, replacement))
        length += len(before)
        spans.append((length, length + len(replacement), replacement))
        length += len(replacement)
        cursor = match.end
    chunks.append(text[cursor:])
    return "".join(chunks), spans


def _mask_matches(
    text: str, matches: list[Match], style: Style, salt: str | None, seed: int = 0
) -> str:
    return _mask_spans(text, matches, style, salt, seed)[0]


def stats(matches: Iterable[Match]) -> dict[str, object]:
    """Summarize findings: total, per-type counts and total characters covered."""
    by_type: dict[str, int] = {}
    chars = 0
    total = 0
    for match in matches:
        by_type[match.type] = by_type.get(match.type, 0) + 1
        chars += match.end - match.start
        total += 1
    return {"total": total, "by_type": dict(sorted(by_type.items())), "characters": chars}


def mask(
    text: str,
    style: Style = "tag",
    types: Iterable[str] | None = None,
    salt: str | None = None,
    *,
    custom_terms: Iterable[str] = (),
    seed: int | None = None,
) -> str:
    """Mask findings. Hash masking requires an explicit non-empty salt.

    ``style="fake"`` swaps each finding for a synthetic value of the same type; the same
    input value always maps to the same fake. Pass ``seed`` for reproducible output
    (a random seed is drawn per call when omitted).
    """
    _validate_style(style, salt)
    if seed is None:
        seed = random.SystemRandom().randrange(2**32) if style == "fake" else 0
    return _mask_matches(text, find(text, types, custom_terms=custom_terms), style, salt, seed)

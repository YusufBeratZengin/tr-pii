"""Detection orchestration, overlap selection and masking."""

import hashlib
import ipaddress
from collections.abc import Callable, Iterable, Iterator
from typing import Literal

from . import credit_card, custom, email, iban, ip, phone, plate, postal_code, tckn, vkn
from ._shared import digits
from .models import Match

Style = Literal["tag", "stars", "partial", "hash"]
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
    if match.type in {"TCKN", "VKN", "CREDIT_CARD", "POSTAL_CODE"}:
        return digits(match.value)
    if match.type == "IP":
        return str(ipaddress.ip_address(match.value))
    if match.type == "PLATE":
        return "".join(match.value.split()).upper()
    if match.type == "EMAIL":
        local, domain = match.value.rsplit("@", 1)
        return local + "@" + domain.lower()
    return custom.turkish_lower(match.value)


def _replacement(match: Match, style: Style, salt: str | None) -> str:
    if style == "tag":
        return f"[{match.type}]"
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
    }.get(match.type)
    if visible is None:
        return "*" * len(match.value)
    # Keep only the requested final digits, never a name or email fragment.
    digit_positions = [i for i, char in enumerate(match.value) if "0" <= char <= "9"]
    keep = set(digit_positions[-visible:])
    return "".join(char if i in keep else "*" for i, char in enumerate(match.value))


def _validate_style(style: str, salt: str | None) -> None:
    if style not in {"tag", "stars", "partial", "hash"}:
        raise ValueError("style must be one of: tag, stars, partial, hash")
    if style == "hash" and not salt:
        raise ValueError("A non-empty salt is required for hash masking")


def _mask_matches(text: str, matches: list[Match], style: Style, salt: str | None) -> str:
    chunks: list[str] = []
    cursor = 0
    for match in matches:
        chunks.extend((text[cursor : match.start], _replacement(match, style, salt)))
        cursor = match.end
    chunks.append(text[cursor:])
    return "".join(chunks)


def mask(
    text: str,
    style: Style = "tag",
    types: Iterable[str] | None = None,
    salt: str | None = None,
    *,
    custom_terms: Iterable[str] = (),
) -> str:
    """Mask findings. Hash masking requires an explicit non-empty salt."""
    _validate_style(style, salt)
    return _mask_matches(text, find(text, types, custom_terms=custom_terms), style, salt)

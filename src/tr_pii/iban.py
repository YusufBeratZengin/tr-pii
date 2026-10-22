"""IBAN checksum validation and detection of Turkish numeric IBANs."""

import re
from collections.abc import Iterator

from ._shared import HSPACE, candidates
from .models import Match

_SPACE = re.compile(HSPACE)
_FORMAT = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", re.ASCII)
_TR_FORMAT = re.compile(r"TR[0-9]{24}", re.ASCII)
_PATTERN = re.compile(r"(?<!\w)[Tt][Rr](?:" + HSPACE + r"?[0-9]){24}(?!\w)")

# ISO 13616 country lengths; a snapshot, not a bank/account allocation registry.
_LENGTHS = {
    "AD": 24,
    "AE": 23,
    "AL": 28,
    "AT": 20,
    "AZ": 28,
    "BA": 20,
    "BE": 16,
    "BG": 22,
    "BH": 22,
    "BI": 27,
    "BR": 29,
    "BY": 28,
    "CH": 21,
    "CR": 22,
    "CY": 28,
    "CZ": 24,
    "DE": 22,
    "DJ": 27,
    "DK": 18,
    "DO": 28,
    "EE": 20,
    "EG": 29,
    "ES": 24,
    "FI": 18,
    "FK": 18,
    "FO": 18,
    "FR": 27,
    "GB": 22,
    "GE": 22,
    "GI": 23,
    "GL": 18,
    "GR": 27,
    "GT": 28,
    "HN": 28,
    "HR": 21,
    "HU": 28,
    "IE": 22,
    "IL": 23,
    "IQ": 23,
    "IS": 26,
    "IT": 27,
    "JO": 30,
    "KW": 30,
    "KZ": 20,
    "LB": 28,
    "LC": 32,
    "LI": 21,
    "LT": 20,
    "LU": 20,
    "LV": 21,
    "LY": 25,
    "MC": 27,
    "MD": 24,
    "ME": 22,
    "MK": 19,
    "MN": 20,
    "MR": 27,
    "MT": 31,
    "MU": 30,
    "NI": 28,
    "NL": 18,
    "NO": 15,
    "OM": 23,
    "PK": 24,
    "PL": 28,
    "PS": 29,
    "PT": 25,
    "QA": 29,
    "RO": 24,
    "RS": 22,
    "RU": 33,
    "SA": 24,
    "SC": 31,
    "SD": 18,
    "SE": 24,
    "SI": 19,
    "SK": 24,
    "SM": 27,
    "SO": 23,
    "ST": 25,
    "SV": 28,
    "TL": 23,
    "TN": 24,
    "TR": 26,
    "UA": 29,
    "VA": 22,
    "VG": 24,
    "XK": 20,
    "YE": 30,
}


def compact_iban(value: str) -> str:
    return _SPACE.sub("", value).upper()


def mod97(value: str) -> int:
    """Calculate incrementally, without constructing an unbounded integer."""
    remainder = 0
    for char in value:
        if "0" <= char <= "9":
            remainder = (remainder * 10 + int(char)) % 97
        else:
            remainder = (remainder * 100 + ord(char) - ord("A") + 10) % 97
    return remainder


def validate_iban(value: str) -> bool:
    """Check registered country length, ASCII format, and MOD 97-10.

    National BBAN rules and bank allocations are not checked. Turkish accounts
    use this project's stricter numeric format and zero reserved digit.
    """
    compact = compact_iban(value)
    if _FORMAT.fullmatch(compact) is None or _LENGTHS.get(compact[:2]) != len(compact):
        return False
    if not 2 <= int(compact[2:4]) <= 98:
        return False
    if compact.startswith("TR") and (_TR_FORMAT.fullmatch(compact) is None or compact[9] != "0"):
        return False
    return mod97(compact[4:] + compact[:4]) == 1


def validate_tr_iban(value: str) -> bool:
    return compact_iban(value).startswith("TR") and validate_iban(value)


def detect(text: str) -> Iterator[Match]:
    return candidates(text, _PATTERN, validate_tr_iban, "IBAN", 1.0)

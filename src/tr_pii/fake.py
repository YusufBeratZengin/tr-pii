"""Synthetic checksum-valid data for tests only, never for identity or payments.

Generated values are not reserved and can accidentally coincide with assigned
identifiers. They carry no claim about a real person, business or account.
"""

import hashlib
import ipaddress
import random
import string

from ._shared import is_digits
from .credit_card import luhn_sum
from .iban import mod97
from .vkn import check_digit


def _random_digits(length: int, seed: int | None) -> str:
    rng = random.Random(seed)
    return "".join(str(rng.randrange(10)) for _ in range(length))


def tckn(*, seed: int | None = None) -> str:
    """Generate an 11-digit synthetic TCKN with both check digits."""
    prefix = _random_digits(9, seed)
    if prefix[0] == "0":
        prefix = "9" + prefix[1:]
    numbers = [int(char) for char in prefix]
    tenth = (7 * sum(numbers[::2]) - sum(numbers[1::2])) % 10
    return prefix + str(tenth) + str((sum(numbers) + tenth) % 10)


def vkn(*, seed: int | None = None) -> str:
    """Generate a synthetic ten-digit VKN."""
    prefix = _random_digits(9, seed)
    return prefix + check_digit(prefix)


def tr_iban(*, seed: int | None = None) -> str:
    """Generate a numeric TR IBAN with an unallocated-demo bank field 00000."""
    bban = "00000" + "0" + _random_digits(16, seed)
    check = 98 - mod97(bban + "TR00")
    return f"TR{check:02d}{bban}"


def credit_card(*, length: int = 16, prefix: str = "999", seed: int | None = None) -> str:
    """Generate a Luhn-valid test number, defaulting to a non-payment prefix."""
    if not 13 <= length <= 19:
        raise ValueError("Card length must be between 13 and 19")
    if not prefix or not is_digits(prefix, len(prefix)) or len(prefix) >= length:
        raise ValueError("Card prefix must be ASCII digits shorter than the card length")
    body = prefix + _random_digits(length - len(prefix) - 1, seed)
    if len(set(body)) == 1:
        body = body[:-1] + str((int(body[-1]) + 1) % 10)
    return body + str(-luhn_sum(body + "0") % 10)


def passport(*, seed: int | None = None) -> str:
    """Generate a synthetic passport serial shape: one letter followed by 8 digits."""
    rng = random.Random(seed)
    return rng.choice(string.ascii_uppercase) + _random_digits(8, rng.randrange(2**32))


def mersis(*, seed: int | None = None) -> str:
    """Generate 16 random digits shaped like a MERSIS number (no checksum exists)."""
    return _random_digits(16, seed)


_PLATE_LETTERS = "ABCDEFGHIJKLMNOPRSTUVYZ"


def _reflow(value: str, replacement_digits: str) -> str:
    """Keep every non-digit of ``value`` and fill its digits from ``replacement_digits``."""
    pool = iter(replacement_digits)
    return "".join(next(pool) if "0" <= char <= "9" else char for char in value)


def _plate_like(value: str, rng: random.Random) -> str:
    out: list[str] = []
    province = f"{rng.randrange(1, 82):02d}"
    province_done = False
    digits_seen = 0
    for char in value:
        if "0" <= char <= "9":
            if not province_done:
                out.append(province[digits_seen])
                digits_seen += 1
                province_done = digits_seen == 2
            else:
                out.append(str(rng.randrange(10)))
        elif char.isalpha():
            letter = rng.choice(_PLATE_LETTERS)
            out.append(letter.lower() if char.islower() else letter)
        else:
            out.append(char)
    return "".join(out)


def like(kind: str, value: str, canonical: str, seed: int = 0) -> str:
    """Return a synthetic stand-in of the same type and layout as ``value``.

    The result depends only on ``seed``, ``kind`` and ``canonical``, so equal inputs
    map to equal fakes. For tests and demos only; fakes are not reserved values.
    """
    digest = hashlib.sha256(f"{seed}|{kind}|{canonical}".encode()).digest()
    sub = int.from_bytes(digest[:8], "big")
    rng = random.Random(sub)
    count = sum(char.isdigit() for char in value)
    if kind == "TCKN":
        return _reflow(value, tckn(seed=sub))
    if kind == "VKN":
        return _reflow(value, vkn(seed=sub))
    if kind == "IBAN":
        return _reflow(value, tr_iban(seed=sub)[2:])
    if kind == "CREDIT_CARD":
        return _reflow(value, credit_card(length=count, seed=sub))
    if kind == "MERSIS":
        return _reflow(value, mersis(seed=sub))
    if kind == "POSTAL_CODE":
        return f"{rng.randrange(1, 82):02d}{_random_digits(3, sub)}"
    if kind == "PASSPORT":
        letter = rng.choice(string.ascii_uppercase)
        return letter + _random_digits(count, sub)
    if kind == "PHONE":
        national = "5" + _random_digits(9, sub)
        prefix = "".join(char for char in value if char.isdigit())[: count - 10]
        return _reflow(value, prefix + national)
    if kind == "PLATE":
        return _plate_like(value, rng)
    if kind == "EMAIL":
        return f"user{digest[:4].hex()}@example.invalid"
    if kind == "IP":
        if ipaddress.ip_address(value).version == 4:
            return f"192.0.2.{rng.randrange(1, 255)}"
        return f"2001:db8::{rng.randrange(1, 65536):x}"
    return f"[{kind}]"

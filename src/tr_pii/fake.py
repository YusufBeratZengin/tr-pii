"""Synthetic checksum-valid data for tests only, never for identity or payments.

Generated values are not reserved and can accidentally coincide with assigned
identifiers. They carry no claim about a real person, business or account.
"""

import random

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


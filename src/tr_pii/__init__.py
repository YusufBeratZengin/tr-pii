"""Offline Turkish PII detection and masking."""

from .api import TYPES, Style, find, mask
from .credit_card import validate_credit_card
from .custom import validate_custom_term
from .email import validate_email
from .iban import validate_iban, validate_tr_iban
from .ip import validate_ip
from .models import Match
from .phone import validate_phone
from .plate import validate_plate
from .postal_code import validate_postal_code
from .tckn import validate_tckn
from .vkn import validate_vkn

__version__ = "0.1.0"
__all__ = [
    "TYPES",
    "Match",
    "Style",
    "find",
    "mask",
    "validate_credit_card",
    "validate_custom_term",
    "validate_email",
    "validate_iban",
    "validate_ip",
    "validate_phone",
    "validate_plate",
    "validate_postal_code",
    "validate_tckn",
    "validate_tr_iban",
    "validate_vkn",
]

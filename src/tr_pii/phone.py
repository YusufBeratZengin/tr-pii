"""Turkish mobile and geographic phone number candidates."""

import re
from collections.abc import Iterator

from ._shared import HSPACE, digits
from .models import Match

# BTK geographic area codes. 392 (Northern Cyprus) is outside this TR scope.
_AREA_CODES = frozenset(
    "212 216 222 224 226 228 232 236 242 246 248 252 256 258 262 264 266 272 274 "
    "276 282 284 286 288 312 318 322 324 326 328 332 338 342 344 346 348 352 354 "
    "356 358 362 364 366 368 370 372 374 376 378 380 382 384 386 388 412 414 416 "
    "422 424 426 428 432 434 436 438 442 446 452 454 456 458 462 464 466 472 474 "
    "476 478 482 484 486 488".split()
)
_SEP = HSPACE + r"?[-]?" + HSPACE + "?"
_BODY = (
    r"(?:(?:\+90|0090)" + _SEP + r"|0" + _SEP + r")?"
    r"(?:\([2-5][0-9]{2}\)|[2-5][0-9]{2})"
    + _SEP
    + r"[0-9]{3}"
    + _SEP
    + r"[0-9]{2}"
    + _SEP
    + r"[0-9]{2}"
)
_FORMAT = re.compile(_BODY)
_PATTERN = re.compile(r"(?<![\w+()])" + _BODY + r"(?![\w)])")
_CONTEXT = re.compile(r"(?<!\w)(?:tel(?:efon)?|cep|gsm)\.?[ \t]*[:=]?[ \t]*$", re.I)


def national_number(value: str) -> str:
    compact = digits(value, " +-()\t\u00a0")
    if compact.startswith("0090"):
        return compact[4:]
    if len(compact) == 12 and compact.startswith("90"):
        return compact[2:]
    if len(compact) == 11 and compact.startswith("0"):
        return compact[1:]
    return compact


def validate_phone(value: str) -> bool:
    """Validate TR numbering shape, independently of detection context."""
    if _FORMAT.fullmatch(value) is None:
        return False
    national = national_number(value)
    return len(national) == 10 and (national.startswith("5") or national[:3] in _AREA_CODES)


def detect(text: str) -> Iterator[Match]:
    for candidate in _PATTERN.finditer(text):
        value = candidate.group()
        compact = digits(value, " +-()\t\u00a0")
        explicit = value.startswith(("+90", "0090", "0"))
        formatted = len(value) != len(compact)
        context = _CONTEXT.search(text[max(0, candidate.start() - 32) : candidate.start()])
        if validate_phone(value) and (explicit or formatted or context):
            confidence = 0.96 if explicit or context else 0.86
            yield Match("PHONE", candidate.start(), candidate.end(), value, confidence)

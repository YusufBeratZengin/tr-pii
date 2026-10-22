# tr-pii

tr-pii detects and masks personal data in Turkish text locally, using a Python library and CLI with no runtime dependencies.

[![CI](https://github.com/YusufBeratZengin/tr-pii/actions/workflows/ci.yml/badge.svg)](https://github.com/YusufBeratZengin/tr-pii/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[Türkçe](README.tr.md)

## Why

Before sending text to an LLM or another service, remove identifiers on your own machine. Turkey-specific checks help distinguish a TCKN, VKN or TR IBAN from arbitrary digits. The library makes no network calls and includes no telemetry or bundled name list.

```python
from tr_pii import fake, mask

# Synthetic data, for tests only. Never use generated IDs as real identities.
text = f"Test kaydı: TCKN {fake.tckn(seed=7)}; dummy@example.invalid"
safe_text = mask(text)
assert safe_text == "Test kaydı: TCKN [TCKN]; [EMAIL]"
# Review safe_text before sending it to an external service.
```

## Installation

Python 3.10 or newer. From a checkout:

```sh
python -m pip install .
tr-pii --version
```

Building uses Hatchling. The installed library uses only the Python standard library. Installation may need internet access for the build backend; processing text never does.

## Quick start

```python
from tr_pii import find, mask

text = "Test e-posta: dummy@example.invalid"
matches = find(text, types=["EMAIL"])
assert matches[0].type == "EMAIL"
assert text[matches[0].start : matches[0].end] == matches[0].value
assert mask(text) == "Test e-posta: [EMAIL]"
assert mask(text, style="stars") == "Test e-posta: " + "*" * 21
```

The default `tag` style replaces each finding with its type. `stars` replaces every character of a finding, including separators. `partial` preserves the last two digits of TCKNs, VKNs, postal codes and plates, or four digits of phones, IBANs and cards. It fully masks email, IP and custom terms.

```python
from tr_pii import mask

assert mask("İZİN ve IŞIK", custom_terms=["izin", "ışık"]) == "[CUSTOM] ve [CUSTOM]"

# Public demonstration salt only. Supply your own per-project salt at runtime.
one = mask("dummy@example.invalid", style="hash", salt="public-demo-salt")
two = mask("dummy@example.invalid", style="hash", salt="public-demo-salt")
assert one == two  # [EMAIL:<16 lowercase hex characters>]
```

Hash style requires a non-empty salt and uses a length-framed salt, type and normalized value as SHA-256 input. Numeric separators, phone prefixes, IBAN/plate case, equivalent IP spellings and Turkish case variants of custom terms normalize consistently. Email domain case normalizes; email local-part case is preserved. Changing the salt changes the aliases. This is pseudonymization: short hashes can collide, repeated values remain linkable, and low-entropy inputs can be guessed if the salt is known. Keep the salt private and outside source control.

## CLI

```sh
tr-pii scan input.txt
tr-pii scan input.txt --count
tr-pii scan input.txt --count --format json
tr-pii mask input.txt --style tag --types TCKN,VKN,IBAN,PHONE,EMAIL
tr-pii mask input.txt --style partial -o output.txt
tr-pii mask - --style stars < input.txt
tr-pii mask input.txt --terms-file test-terms.txt
```

`scan` emits one JSON object per finding, including `type`, `start`, `end`, `value` and `confidence`. Use `--count` to output only the number of findings, optionally formatted as JSON (`--format json`). Its output contains the original personal data; protect it as you would the input. `mask` writes the resulting text without adding a newline; use `-o/--output FILE` to write directly to a file (refuses overwrite unless `--force` is given). Both commands accept a UTF-8 file or `-` for stdin, `--types` as comma-separated names, and `--terms-file` as a UTF-8 file with one custom term per line. Empty term-file lines are ignored. `python -m tr_pii` is equivalent to `tr-pii`.

For `--style hash`, supply the salt in the `TR_PII_SALT` environment variable through your local environment or secret manager. The CLI deliberately has no salt command-line option. Do not store a real salt in examples or committed files.

| Exit code | Meaning |
| --- | --- |
| `0` | No findings |
| `3` | At least one finding, including successful masking |
| `2` | Invalid arguments, unreadable/non-UTF-8 input, or missing hash salt |

Exit code `3` makes `scan` usable as a CI gate. When scripting `mask`, handle `3` as successful processing with findings. File errors are generic to avoid exposing input paths or values in diagnostics.

## Example output

Given synthetic input in `examples/sample.txt` (using reserved `.invalid` domain and checksum-valid `fake.tckn(seed=1)`):

```text
E-posta: dummy@example.invalid
TCKN: 29141777626
```

### Scan findings

```sh
tr-pii scan examples/sample.txt
```

Output:

```json
{"type": "EMAIL", "start": 9, "end": 30, "value": "dummy@example.invalid", "confidence": 0.99}
{"type": "TCKN", "start": 37, "end": 48, "value": "29141777626", "confidence": 0.99}
```

Exit status: `3` (findings detected).

Summary count only:

```sh
tr-pii scan examples/sample.txt --count
# 2 (exit status: 3)

tr-pii scan examples/sample.txt --count --format json
# {"count": 2} (exit status: 3)
```

### Partial masking

```sh
tr-pii mask --style partial examples/sample.txt
```

Output:

```text
E-posta: *********************
TCKN: *********26
```

Exit status: `3` (findings masked). When no findings are detected, both commands return exit status `0`.

## API summary

```python
find(text, types=None, *, custom_terms=()) -> list[Match]
mask(text, style="tag", types=None, salt=None, *, custom_terms=()) -> str
```

`Match` is an immutable dataclass: `type: str`, `start: int`, `end: int`, `value: str`, `confidence: float`. Offsets index the original Python string in Unicode code points; `end` is exclusive. Results are ordered by `start` and do not overlap. For overlapping candidates, higher confidence wins, then longer length, earlier start and alphabetical type. Confidence is a fixed heuristic ranking, not a calibrated probability.

`types=None` enables all types; an empty iterable enables none. Names are case insensitive. Unknown names, a bare string in place of a type/term iterable, empty custom terms, invalid styles and missing hash salts raise `ValueError`. Custom terms are literal whole-word/phrase matches, with Turkish `i ↔ İ` and `ı ↔ I` case handling; no names are inferred. Supply `types=["CUSTOM"]` to restrict detection to your dictionary.

| Type | Detection and public validator |
| --- | --- |
| `TCKN` | 11 ASCII digits, nonzero first digit, both check digits; compact or consistent 3-3-3-2 space/dot groups. `validate_tckn` |
| `VKN` | 10 ASCII digits and the position-weighted tax check digit. `validate_vkn` |
| `IBAN` | Numeric `TR` + 24 digits, horizontal spaces allowed, zero reserved digit, country length and MOD 97-10. `validate_tr_iban` |
| `PHONE` | TR mobile `5xx` or known geographic area code; `+90`, `0090`, `0`, spaces, hyphens and parentheses. Bare 10-digit strings need a preceding `telefon`, `tel`, `cep` or `gsm` label. `validate_phone` |
| `EMAIL` | Common unquoted ASCII mailbox with a dotted domain; no DNS lookup. `validate_email` |
| `CREDIT_CARD` | 13–19 digits, optional spaces/hyphens, Luhn; repeated single-digit strings excluded. `validate_credit_card` |
| `PLATE` | Provinces `01`–`81`; 1 letter + 4 digits, 2 letters + 3–4 digits, or 3 letters + 2–3 digits; compact/spaced. `validate_plate` |
| `IP` | IPv4/IPv6 checked by `ipaddress`; no label needed. `validate_ip` |
| `POSTAL_CODE` | Five digits with province `01`–`81`, only after `posta kodu` or `PK`. `validate_postal_code` |
| `CUSTOM` | Explicit user terms only. `validate_custom_term(value, term)` |

Validators are exported from `tr_pii` and their respective detector modules (`tckn`, `vkn`, `iban`, `phone`, `email`, `credit_card`, `plate`, `ip`, `postal_code`, `custom`). They return `bool`; phone/postal validators check a standalone value without requiring the detection context. `validate_iban` additionally checks general IBAN format, registered country length and checksum; non-TR BBAN rules are not checked. **Automatic IBAN detection covers TR only.** `TYPES`, `Match` and the `Style` type alias are public. Type information ships with `py.typed`.

## Synthetic test data

```python
from tr_pii import fake, validate_tckn, validate_vkn, validate_tr_iban, validate_credit_card

assert validate_tckn(fake.tckn(seed=1))
assert validate_vkn(fake.vkn(seed=1))
assert validate_tr_iban(fake.tr_iban(seed=1))
assert validate_credit_card(fake.credit_card(seed=1, length=19))
```

**For tests only.** These generators produce valid check digits, not registered identities or usable payment credentials. Generated values are not reserved and can accidentally coincide with assigned identifiers. Fake TR IBANs use a `00000` demo bank field; cards default to prefix `999`. Seeds make fixtures reproducible. Do not submit generated values to real services.

## Limits and cautions

- There is no 100% detection guarantee. Review results before sharing sensitive text. This library alone does not establish regulatory compliance or irreversible anonymization.
- Names need your dictionary. Addresses, unlisted names, OCR errors, obfuscated text, spelled-out digits and Unicode digit lookalikes are outside scope. Unicode normalization is not performed, preserving offsets.
- Checksums validate structure, not ownership or assignment. A checksum-valid invoice number can look like an identifier, especially with VKN's single check digit. Conversely, strict word boundaries skip identifiers embedded in product codes.
- Phone detection intentionally skips unlabelled, unformatted national 10-digit numbers. Mobile allocation and subscriber status are not checked. Non-geographic service numbers are outside scope.
- Plates cover ordinary 2–4 digit combinations above. Single-letter five-digit serials, diplomatic/special formats and province-specific letter allocations are outside scope. Q/W/X and Turkish accented letters are rejected. Spaced plates must use uppercase letters (lowercase is accepted only in compact form) to avoid matching text like "42 at 100".
- Email detection omits quoted local parts, Unicode mailboxes and domain literals. Postal validation checks the province-shaped prefix, not the PTT assignment directory. The IP validator accepts bare addresses; detection can extract an address from brackets or CIDR text.
- TR IBANs intentionally follow the numeric requirement here, although the SWIFT registry permits alphanumeric account fields. General IBAN validation does not check national BBAN structure or bank allocation. The country-length snapshot may need updating.
- `scan` returns raw values. Partial masking intentionally reveals digits; salted hashing retains relationships. Use `tag` or `stars` when this leakage is unsuitable.
- Files are processed in memory as a whole. The target is under one second for 1 MB on a typical development machine; hardware, finding density and large custom dictionaries affect runtime. This is a target, not a latency guarantee.

## Development and contributing

```sh
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m mypy
python -m build
python scripts/benchmark.py
```

Without development packages, tests also run with the standard library from a checkout:

```sh
PYTHONPATH=src python -m unittest discover -v
PYTHONPATH=src python scripts/benchmark.py
```

PowerShell: set `$env:PYTHONPATH = "src"` before running the Python commands. CI runs tests, lint, strict type checks and package builds on Python 3.10–3.14. Tests generate checksum fixtures and use reserved email/IP examples. See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution process and [CHANGELOG.md](CHANGELOG.md) for changes.

## Technical references

- [TCMB IBAN communiqué](https://www.tcmb.gov.tr/wps/wcm/connect/EN/TCMB%2BEN/Bottom%2BMenu/IBAN/Communique): TR structure and MOD 97-10.
- [SWIFT IBAN registry](https://www.swift.com/resource/iban-registry-pdf): country lengths (Release 103, September 2026).
- [BTK national numbering plan](https://btk.gov.tr/ulusal-numaralandirma-plani): mobile and geographic number structure.
- [Official Gazette, plate letter/number groups, Article 55](https://resmigazete.gov.tr/eskiler/2014/02/20140219-8.htm).

## License

[MIT](LICENSE). Copyright (c) 2026 Yusuf Berat Zengin.


# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Backward-compatible `last4` masking (final four digits of numeric identifiers; fully masked email/IP/custom terms) and per-call `placeholder` aliases such as `[IBAN_1]`, reused for normalized equal values and numbered separately per type. Both styles support the API, CLI and JSON masked offsets.
- Independent synthetic VKN digital-root and TR IBAN MOD-97 reference tests, checksum mutations, identifier shape/boundary regressions, and full/last-four/hash/placeholder checks for VKN, IBAN, passport and MERSIS. English and Turkish usage examples document the new strategies.
- Detectors for `PASSPORT` (label-gated letter + 7-8 digits) and `MERSIS` (label-gated 16 digits) with `validate_passport` / `validate_mersis`, partial masking, and matching `fake.passport` / `fake.mersis` generators.
- Masking styles `redact` (type-free `[REDACTED]`) and `fake` (checksum-valid synthetic stand-ins of the same type and layout; equal inputs give equal fakes). `mask(..., seed=)`, CLI `--fake` / `--seed` make output reproducible.
- `stats()` plus CLI `scan --stats [--format json]` for per-type summaries, and `mask --format json` reporting original and masked offsets for every finding.
- Tests for IBAN checksum rejection, plate province codes 01-81 and VKN checksum round trips.
- Reproducible terminal SVG demo generated from real CLI commands with `scripts/make-demo.py`, embedded in both READMEs and checked in CI.
- Default pytest line/branch coverage reporting with an 85% minimum, printed in every CI test job.
- Weekly Dependabot updates for Python development dependencies and GitHub Actions, and a Python CodeQL workflow.
- YAML issue forms for bug reports and feature requests, with synthetic-data guidance.
- macOS CI on Python 3.10 and 3.14, alongside the existing Ubuntu and Windows checks.
- Python and PyPI version badges, synchronized quick starts, configuration tables and FAQs in English and Turkish.
- CLI: `--output` / `-o FILE` option for `mask` command, writing masked text to file and refusing overwrite unless `--force` is specified.
- CLI: `--count` flag for `scan` command with `--format text` (default) and `--format json` summary output, preserving exit code `3` on findings.
- Release workflow: added `.github/workflows/release.yml` for PyPI trusted publishing (OIDC) and GitHub releases triggered on `v*` tags.
- CI hardening: added Windows runner matrix (Python 3.10 and 3.14), `ruff format --check`, CLI `--version` smoke tests, and installed-wheel exit-code assertions in `.github/workflows/ci.yml`.
- Community files: added `SECURITY.md` (private advisory reporting instructions and scope notes), `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), issue templates (`bug_report.md`, `false_negative.md`, `feature_request.md`), and `pull_request_template.md`.
- Quality tests: added test cases verifying avoidance of false positives on ISO dates (`2026-10-22`), invoice numbers, product codes (`TR-1234-5678`), and non-TCKN 11-digit numbers, alongside bare vs labelled phone numbers and bare VKNs.
- Example demo: added "Example output" sections to English and Turkish READMEs, backed by `examples/sample.txt` and byte-identical golden verification tests in `tests/test_examples.py`.

### Changed

- Package metadata: added `[project.urls]` (Homepage, Source, Issues, Changelog), author email, classifiers (`License :: OSI Approved :: MIT License`, `Operating System :: OS Independent`, `Intended Audience :: Developers`, `Natural Language :: Turkish`, `Topic :: Security`, `Topic :: Text Processing`), and expanded keywords in `pyproject.toml`.
- Distribution includes: included `scripts/` and `examples/` in source distribution (`sdist`) packaging.
- Documentation: replaced placeholder static CI badge with live GitHub Actions workflow badge in `README.md` and `README.tr.md`.

### Fixed

- Passport and MERSIS labels require a word boundary, avoiding false positives on concatenated product codes such as a label immediately followed by an identifier.
- Configuration: corrected `tool.mypy` files in `pyproject.toml` from non-existent `is/benchmark.py` to `scripts/benchmark.py`, allowing `python -m mypy` to exit 0 on clean checkouts.
- Benchmark references: replaced dangling `is/benchmark.py` references across `pyproject.toml`, `README.md`, `README.tr.md`, and `CONTRIBUTING.md` with `scripts/benchmark.py`.
- Test isolation: updated `tests/test_cli.py` to use `tempfile.TemporaryDirectory()` rather than relying on a gitignored directory.
- Repository hygiene: removed stray untracked directory `tmplqnfcris/`.
- Plate detection no longer matches lowercase or mixed-case spaced text such as `42 at 100`; spaced plates need uppercase letters, lowercase is accepted only in compact form.

## [0.1.0] - 2026-10-23

### Added

- Offline TCKN, VKN, numeric TR IBAN, Turkish phone, email, Luhn card, ordinary plate, IPv4/IPv6 and contextual postal-code detection.
- Public standalone validators, including general IBAN country-length and checksum validation.
- Explicit custom terms with Turkish dotted/dotless I handling.
- Immutable findings, confidence/length overlap selection, and tag, stars, partial and salted SHA-256 masking.
- Synthetic checksum-valid test generators with reproducible seeds.
- UTF-8 CLI with JSON Lines scanning, file/stdin input, filtering and exit codes for CI gates.
- Typed Python 3.10+ package with no runtime dependencies, bilingual documentation and a Python 3.10–3.14 CI matrix.

[Unreleased]: https://github.com/YusufBeratZengin/tr-pii/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/YusufBeratZengin/tr-pii/releases/tag/v0.1.0

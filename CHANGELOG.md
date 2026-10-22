# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

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

- Configuration: corrected `tool.mypy` files in `pyproject.toml` from non-existent `is/benchmark.py` to `scripts/benchmark.py`, allowing `python -m mypy` to exit 0 on clean checkouts.
- Benchmark references: replaced dangling `is/benchmark.py` references across `pyproject.toml`, `README.md`, `README.tr.md`, and `CONTRIBUTING.md` with `scripts/benchmark.py`.
- Test isolation: updated `tests/test_cli.py` to use `tempfile.TemporaryDirectory()` rather than relying on a gitignored directory.
- Repository hygiene: removed stray untracked directory `tmplqnfcris/`.
- Plate detection no longer matches lowercase or mixed-case spaced text such as `42 at 100`; spaced plates need uppercase letters, lowercase is accepted only in compact form.

## [0.1.0] - 2026-10-22

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

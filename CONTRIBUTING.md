# Contributing

Small, focused changes with a reproducible problem and meaningful tests are welcome. Discuss a new detector or a public API change in an issue before implementing it.

## Local setup

Use Python 3.10 or newer:

```sh
python -m venv .venv
# Activate .venv with your shell's activation command.
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m build
python scripts/make-demo.py --check
```

If development packages cannot be installed, run `python -m unittest discover -v` with `PYTHONPATH=src` and report which additional checks could not run. Do not claim an unavailable check passed. In PowerShell use `$env:PYTHONPATH = "src"`.

The default pytest command prints line and branch coverage and enforces an 85% combined minimum. CI runs it on Ubuntu with Python 3.10–3.14, and on Windows and macOS with Python 3.10 and 3.14.

## README terminal demo

Run `python scripts/make-demo.py` after changing CLI output or `examples/sample.txt`. The standard-library generator runs the real CLI, checks its exit codes, and writes `docs/demo.svg`. Both READMEs use this image; CI checks it with `python scripts/make-demo.py --check`. Keep all demo commands in both READMEs and use synthetic fixtures only.

## Tests and privacy

- Never submit real personal data, real names, addresses, identifiers, tokens or salts in code, fixtures, logs or issues. Use `tr_pii.fake`, invented terms, reserved `.invalid` domains and RFC documentation IP ranges.
- Fake checksum-valid identifiers are for tests only. They are not reserved and must not be sent to real services.
- Every detector needs valid and invalid cases, checksum corruption where applicable, text-boundary checks and plausible false positives. Cover overlaps, Unicode offsets and CLI status changes when relevant.
- Keep runtime code offline and free of third-party dependencies. Include type annotations and English error messages. Avoid abstractions that do not simplify the implementation.
- Run `python scripts/benchmark.py` after changing candidate patterns or overlap resolution. Record the interpreter and timings. Avoid machine-specific timing assertions in unit tests.

## Pull requests

Use Conventional Commits such as `feat:`, `fix:`, `test:`, `docs:` or `ci:`. Explain the problem, resulting behavior and checks actually run. Update both READMEs together for API or behavior changes and add a changelog entry. Keep generated data and caches out of commits.

Contributions are distributed under the project's MIT license.


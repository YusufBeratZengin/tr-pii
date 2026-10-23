## Description

Brief summary of changes made and motivation behind them.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Documentation update
- [ ] Performance improvement or refactoring
- [ ] CI or release automation

## Verification and Checks

Commands run and test results:

- [ ] `python -m pytest` passes locally with at least 85% coverage
- [ ] `python -m ruff check .` passes
- [ ] `python -m ruff format --check .` passes
- [ ] `python -m mypy` passes with strict typing
- [ ] `python scripts/make-demo.py --check` matches the current CLI output
- [ ] `python -m build && python -m twine check dist/*` passes
- [ ] `python scripts/benchmark.py` passes

## Privacy and Guidelines Checklist

- [ ] No real personal data, identity numbers, phone numbers, or confidential documents are committed
- [ ] No credentials, tokens, or private keys are staged
- [ ] Documentation changes are reflected in both `README.md` and `README.tr.md`
- [ ] CHANGELOG.md is updated under `[Unreleased]`

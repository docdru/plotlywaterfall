# Changelog

## [Unreleased]
- Modern development setup: uv with `uv.lock`, PEP 735 dependency groups, ruff (lint + format), mypy, pre-commit.
- GitHub Actions CI: lint, type check, tests on Python 3.11–3.15 (Linux/Windows/macOS), lowest-dependency and
  pre-release dependency jobs, example-notebook execution, package build; weekly scheduled run.
- Automated PyPI releases on version tags via Trusted Publishing with attestations; Dependabot for actions and dependencies.
- **Minimum Python is now 3.11** (3.8–3.10 are end-of-life; the code never ran on 3.8/3.9).
- `numpy` is now declared as a dependency (it was imported but not declared); dependencies are declared in
  `pyproject.toml` and `requirements.txt` was removed.
- Code formatted with ruff; no functional changes.

## [0.9.2.] - 2024-02-20
- Bugfix line placement in case of empty bars at certain x in other then the first group

## [0.9.1] - 2024-01-04
- Added CHANGELOG.md and using full URLs for images in README.md

## [0.9.0] - 2024-01-04
- Initial release on pypi.org
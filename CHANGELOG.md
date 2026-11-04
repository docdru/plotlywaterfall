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
- Automated AI pull-request review (Mistral) posted as a PR comment; see README "AI pull-request review".

### Added
- **Mixed signs within one bar**: categories of one bar (at an x-value or in a total) may now have
  different signs. The bar is split into narrow sub-steps that walk from its start to its end level,
  with a "net ghost" bar behind them showing the net change. New arguments `mixed_signs`
  (`"steps"` default, `"error"` for the previous behaviour), `net_ghost` and `step_order`.

### Fixed
- `total_type="sumtotal"` with groups raised `KeyError: 'Y'` unless the value column was named `Y`.
- Groups with opposite signs at the same x-value (or opposite-signed totals) raised
  "mixed signed categories in totals"; the sign check now only compares stacked bars within one group.
- The `subtotals` dict passed by the caller is no longer modified (with `total=True` it used to gain
  the total, which added an extra bar when the dict was reused).
- Colors: a `colors` dict that lacks a group or category now falls back to plotly's default color
  for it instead of failing with a long plotly validation error.
- The `connector_line` default is no longer a dict shared between instances.

### Changed
- Clear `ValueError`s for invalid input: unknown column names, missing values (NaN) in `y`,
  unknown `total_type`, and subtotal keys that are not x-values (now also checked in the constructor).
- `Waterfall` can be imported directly: `from plotlywaterfall import Waterfall`
  (`from plotlywaterfall.waterfall import Waterfall` keeps working); `plotlywaterfall.__version__` added.
- Internal cleanup: removed dead code in `add_subtotal`, one helper for bar offsets and one for colors.

## [0.9.3] - 2024-02-20
- Bugfix legend groups

## [0.9.2] - 2024-02-20
- Bugfix line placement in case of empty bars at certain x in other then the first group

## [0.9.1] - 2024-01-04
- Added CHANGELOG.md and using full URLs for images in README.md

## [0.9.0] - 2024-01-04
- Initial release on pypi.org
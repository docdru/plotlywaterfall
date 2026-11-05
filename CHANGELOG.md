# Changelog

## [Unreleased]

### Added
- **Type hints throughout** and a `py.typed` marker, so type checkers (mypy, pyright) use the
  package's annotations.
- **`waterfall(df, x=..., y=..., ...)`**: one call that returns the figure, like plotly express'
  `px.bar`. Same arguments as `Waterfall` (keyword-only after `x` and `y`, without the deprecated
  `colors`); `Waterfall` stays for building subtotals step by step.
- **New colour API in plotly-express style**: `color` (category column, group column or
  `"direction"`), `color_discrete_map` (value → colour; `(group, category)` tuples for one group's
  category), `color_discrete_sequence`, `pattern_shape` and `pattern_shape_map`.
- `color="direction"` colours increases, decreases and totals (default green / red / grey) and adds
  a legend for them.
- Keys of `color_discrete_map` / `pattern_shape_map` that match no value raise a `UserWarning`.
- **Value labels**: `value_labels` (`"bar"` default, `"segment"`, `"both"`, `None` / `False`), with one number
  format for labels and hover: `number_format` (Python format spec or function), `number_prefix`,
  `number_suffix`. Changes are signed (`+9`, `-7`), totals not.
- **Hover texts** show the x label, the segment's category and value, the step for split bars and the
  running total (previously plotly's default hover showed the internal numeric x-position).
- `title` and `labels` (column display names, as in plotly express) arguments.
- **Mixed signs within one bar**: categories of one bar (at an x-value or in a total) may now have
  different signs. The bar is split into narrow sub-steps that walk from its start to its end level,
  with a "net ghost" bar behind them showing the net change. New arguments `mixed_signs`
  (`"steps"` default, `"error"` for the previous behaviour), `net_ghost` and `step_order`.

### Changed
- `import plotlywaterfall.waterfall as m` now gives the `waterfall` function (the package exports it under
  that name). `from plotlywaterfall.waterfall import Waterfall` keeps working.
- **Value labels are shown by default** (`value_labels=None` restores unlabelled bars) and the y-axis is
  titled with the y column name (or its `labels` entry). The axis range leaves room for the labels.
- **Minimum Python is now 3.11** (3.8–3.10 are end-of-life; the code never ran on 3.8/3.9).
- `numpy` is now declared as a dependency (it was imported but not declared); dependencies are declared in
  `pyproject.toml` and `requirements.txt` was removed.
- **Default colours**: charts without category and group are coloured by direction. Charts with
  categories or groups get one colour per category (or group) taken from the template's colorway,
  so a category has the same colour in every group (previously plotly cycled colours per trace).
- Clear `ValueError`s for invalid input: unknown column names, missing values (NaN) in `y`,
  unknown `total_type`, and subtotal keys that are not x-values (now also checked in the constructor).
- `Waterfall` can be imported directly: `from plotlywaterfall import Waterfall`
  (`from plotlywaterfall.waterfall import Waterfall` keeps working); `plotlywaterfall.__version__` added.
- Internal cleanup: removed dead code in `add_subtotal`, one helper for bar offsets and one for colors.

### Deprecated
- The `colors` argument; it still works, emits a `DeprecationWarning` and will be removed in 1.0.
  See the README for the replacement.

### Fixed
- `total_type="sumtotal"` with groups raised `KeyError: 'Y'` unless the value column was named `Y`.
- Groups with opposite signs at the same x-value (or opposite-signed totals) raised
  "mixed signed categories in totals"; the sign check now only compares stacked bars within one group.
- The `subtotals` dict passed by the caller is no longer modified (with `total=True` it used to gain
  the total, which added an extra bar when the dict was reused).
- Colors: a `colors` dict that lacks a group or category now falls back to plotly's default color
  for it instead of failing with a long plotly validation error.
- The `connector_line` default is no longer a dict shared between instances.

### Development
- mypy runs with `disallow_untyped_defs` and `disallow_incomplete_defs`; CI checks that the wheel
  contains `py.typed`.
- Example gallery: CI executes the example notebook and publishes it as HTML with interactive charts on
  GitHub Pages (pull requests: `docs-site` artifact); the README image is rendered by CI as well.
- Modern development setup: uv with `uv.lock`, PEP 735 dependency groups, ruff (lint + format), mypy, pre-commit.
- GitHub Actions CI: lint, type check, tests on Python 3.11–3.15 (Linux/Windows/macOS), lowest-dependency and
  pre-release dependency jobs, example-notebook execution, package build; weekly scheduled run.
- Automated PyPI releases on version tags via Trusted Publishing with attestations; Dependabot for actions and dependencies.
- Code formatted with ruff; no functional changes.
- Automated AI pull-request review (Mistral) posted as a PR comment; see README "AI pull-request review".

## [0.9.3] - 2024-02-20
- Bugfix legend groups

## [0.9.2] - 2024-02-20
- Bugfix line placement in case of empty bars at certain x in other then the first group

## [0.9.1] - 2024-01-04
- Added CHANGELOG.md and using full URLs for images in README.md

## [0.9.0] - 2024-01-04
- Initial release on pypi.org
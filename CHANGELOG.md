# Changelog

## [Unreleased]

### Changed
- The AI pull-request review now uses the shared action
  [docdru/ai-review](https://github.com/docdru/ai-review), configured in `.github/ai-review.toml`.
  Findings carry a P0–P3 severity and the verdict follows from them. The `AI_REVIEW_MODEL`
  repository variable is no longer used: the model is set in the config.

## [1.2.0] - 2026-11-05

### Added
- **Start and end levels for bridges**: `start="EBIT 2025"` marks x-values that hold a level, not a
  change; they are drawn like totals (grey with direction colours, unsigned labels).
- **`measure` column** with plotly's `go.Waterfall` names: `"relative"` (change), `"absolute"`
  (given level, e.g. budget or actual) and `"total"` (calculated level, value ignored). Works with
  categories (stacked levels) and groups (each group its own levels).
- **`reconcile`** for given levels that the changes before them do not add up to: `"other"` (default)
  inserts a bar for the difference (`reconcile_label`, default `"Other"`), `"jump"` draws the given
  level, `"error"` raises `ValueError`.
- Example gallery: a new first part with finance examples (EBIT bridge, budget vs actual by segment,
  monthly cash-flow walk, one bridge per region, from a ledger to a bridge) and sections on order,
  dates and export.

### Changed
- Hover text of totals without categories names the total (`Subtotal: 5`) instead of `Total: 5`.
- Dates mixed with text labels on the x-axis (e.g. `"Opening"` and month ends) are formatted one by one.

## [1.1.0] - 2026-11-05

### Fixed
- **Wrong levels with groups whose rows are in a different order**: running levels were accumulated
  in each group's own row order instead of the x-axis order, so such a group's bars started at the
  wrong height. They now always follow the x-axis.
- **Dates on the x-axis** were labelled `Timestamp('2026-01-31 00:00:00')`; they are now shown as
  `Jan 2026` (dates in different months) or `2026-01-31`, in tick labels and hover.
- **The order of a pandas `Categorical` x column** was ignored; it now sets the order of the bars
  (and of groups and categories).

### Added
- `category_orders` (as in plotly express) to set the order of x, group and category values;
  the colour palette is assigned in that order.
- `x_format`: strftime pattern for date x-values or a function for any x-values.
- `number_unit` (`"k"`, `"M"`, `"bn"` or `"auto"` = one unit for the whole chart) and
  `negative_style="parentheses"` for accounting-style labels such as `($0.73M)`.

## [1.0.0] - 2026-11-05

First stable release: a one-call `waterfall()` function, mixed signs within a bar, a plotly-express
style colour API, value labels and hover texts, type hints, and an
[example gallery](https://docdru.github.io/plotlywaterfall/).

### Upgrading from 0.9
- **`colors` was removed.** Use `color` and `color_discrete_map`:

  | 0.9 `colors=` | 1.0 |
  |---|---|
  | `{"one": "red", "two": "blue"}` (per category) | `color_discrete_map={"one": "red", "two": "blue"}` |
  | `{"Group1": "red", "Group2": "blue"}` (per group) | `color="group", color_discrete_map={"Group1": "red", "Group2": "blue"}` (with your group column name) |
  | `{"Group1": {"one": "red"}}` (per group and category) | `color_discrete_map={("Group1", "one"): "red"}` |

- **Charts look different by default:** bars carry value labels (`value_labels=None` turns them
  off), charts without category and group are coloured by direction (green / red / grey), a category
  keeps its colour across groups, and the y-axis is titled with the y column.
- **Mixed signs within one bar are drawn** as sub-steps instead of raising `NotImplementedError`;
  `mixed_signs="error"` restores the old behaviour.
- **Python 3.11 or newer** is required.

### Added
- **Type hints throughout** and a `py.typed` marker, so type checkers (mypy, pyright) use the
  package's annotations.
- Options with a fixed set of values (`total_type`, `mixed_signs`, `step_order`, `value_labels`) are
  typed as `Literal`s, so editors suggest the valid values and type checkers catch typos.
- **`waterfall(df, x=..., y=..., ...)`**: one call that returns the figure, like plotly express'
  `px.bar`. Same arguments as `Waterfall` (keyword-only after `x` and `y`); `Waterfall` stays for
  building subtotals step by step.
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

### Removed
- The `colors` argument, replaced by `color` / `color_discrete_map` (see "Upgrading from 0.9").

### Fixed
- `total_type="sumtotal"` with groups raised `KeyError: 'Y'` unless the value column was named `Y`.
- Groups with opposite signs at the same x-value (or opposite-signed totals) raised
  "mixed signed categories in totals"; the sign check now only compares stacked bars within one group.
- The `subtotals` dict passed by the caller is no longer modified (with `total=True` it used to gain
  the total, which added an extra bar when the dict was reused).
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
- Automated AI pull-request review (Mistral) posted as a PR comment; see README "AI pull-request review".

## [0.9.3] - 2024-02-20
- Bugfix legend groups

## [0.9.2] - 2024-02-20
- Bugfix line placement in case of empty bars at certain x in other then the first group

## [0.9.1] - 2024-01-04
- Added CHANGELOG.md and using full URLs for images in README.md

## [0.9.0] - 2024-01-04
- Initial release on pypi.org
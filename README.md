# plotlywaterfall

[![CI](https://github.com/docdru/plotlywaterfall/actions/workflows/ci.yml/badge.svg)](https://github.com/docdru/plotlywaterfall/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/plotlywaterfall)](https://pypi.org/project/plotlywaterfall/)
[![Python versions](https://img.shields.io/pypi/pyversions/plotlywaterfall)](https://pypi.org/project/plotlywaterfall/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Description

A small package adding simple waterfall plotting capabilities on top of the plotly graphing package. Waterfall graphs are useful to display e.g. financial data such as cashflow statements in an easily digestible format. 

While plotly includes basic capabilities to plot waterfall graphs, it ships only limited features. The *plotlywaterfall* package provides simple, plotly-express-style waterfall graphs with grouping, multiple stacked categories and variable colors. 

## Installation

Requires Python 3.11 or newer.

```bash
pip install plotlywaterfall
# or
uv add plotlywaterfall
```

## Usage

More examples can be found in the example notebook (https://github.com/docdru/plotlywaterfall/blob/main/examples/examples.ipynb). Let's use this dataframe for a simple yet complete example: 

    df = pd.DataFrame({
        "X": ["A", "B", "C"]*4 + ["D", "D" ], 
        "Y": [4, 1, 8, 7, 3, 2] + [i-1 for i in [4, 1, 8, 7, 3, 2]] + [8, 5],
        "category": ["one"]*3+["two"]*3 + ["one"]*3+["two"]*3 + ["two", "three"],
        "group": ["Group1"]*6 + ["Group2"]*6 + ["Group2", "Group3"]
    })

![DF](https://raw.githubusercontent.com/docdru/plotlywaterfall/main/examples/example_df.png)


One can plot this data, with defined colors and automatic creating of total and subtotal, by using: 


    from plotlywaterfall import Waterfall

    colors = {
        "one": "red", "two": "blue", "three": "green",
        ("Group2", "one"): "salmon", ("Group2", "two"): "lightskyblue",
    }

    c = Waterfall(df, x="X", y="Y", category="category", group="group", total=True,
                  subtotals={"C": "Subtotal"}, color_discrete_map=colors)
    fig = c.get_fig()
    fig



Resulting graph:

![Example](https://raw.githubusercontent.com/docdru/plotlywaterfall/main/examples/example.png)

### Labels, number format and hover

Every bar is labelled with its change (signed, e.g. `+9`) or, for totals, its value; hovering shows
the step, its category and the running total.

| Argument | Meaning | Default |
|---|---|---|
| `value_labels` | `"bar"` (one label per bar, outside), `"segment"` (inside each stacked segment), `"both"` or `None` | `"bar"` |
| `number_format` | Python format spec for the absolute value (e.g. `",.1f"`) or a function | thousands separators, up to two decimals |
| `number_prefix` / `number_suffix` | Units around the number; the sign stays in front (`-$5M`) | `""` |
| `title` | Figure title | `None` |
| `labels` | Display names for columns, like plotly express (`{"Y": "Cashflow [MUSD]"}`); titles the axes | y-axis titled with the y column |

    Waterfall(df, x="X", y="Y", total=True, number_prefix="$", number_suffix="M",
              title="Cash bridge", labels={"Y": "Cashflow [MUSD]"}).get_fig()

### Colors

Colours work like in plotly express:

| Argument | Meaning |
|---|---|
| `color` | What drives the colour: the category column, the group column, or `"direction"` (increase / decrease / total). Default: the category column if given, else the group column, else `"direction"`. |
| `color_discrete_map` | Colour per value, e.g. `{"one": "red"}`. `(group, category)` tuples colour one group's category. With `color="direction"` the keys are `"increase"`, `"decrease"`, `"total"` (default green / red / grey). Keys that match no value raise a warning. |
| `color_discrete_sequence` | Colours for values missing from the map, assigned in order. Default: the colorway of the active plotly template. |
| `pattern_shape` | The group or category column, to give its values different fill patterns, e.g. colour by category and pattern by group. |
| `pattern_shape_map` | Pattern per value, e.g. `{"Actual": "/"}`. |

Colours are assigned per value, so a category has the same colour in every group:

    Waterfall(df, x="X", y="Y", category="category", group="group", total=True,
              pattern_shape="group").get_fig()

The older `colors` argument still works, but is deprecated and will be removed in version 1.0.

### Mixed signs

Categories of one bar may have different signs, e.g. a subsidy (+1) and a restructuring charge (−4)
at the same x-value, or a total that combines positive and negative categories. Such a bar is split
into one narrow sub-step per category that walks from the level where the bar starts to where it
ends, with a light "net ghost" bar behind it showing the net change:

    df = pd.DataFrame({
        "X": ["Revenue", "Costs", "Other", "Other"],
        "Y": [9, -7, 1, -4],
        "category": ["Operating", "Operating", "Operating", "One-off"],
    })
    Waterfall(df, x="X", y="Y", category="category", total=True).get_fig()

Options:

| Argument | Values | Default |
|---|---|---|
| `mixed_signs` | `"steps"` (split into sub-steps), `"error"` (raise `NotImplementedError`, the behaviour before 0.10) | `"steps"` |
| `net_ghost` | `True`, `False`, or a dict of plotly marker properties for the net bar | `True` |
| `step_order` | `"data"` (order of the categories in the DataFrame), `"positive_first"`, `"largest_first"` | `"data"` |

Bars whose categories share a sign are drawn as normal stacked bars. With several groups each group's
bar walks on its own; with many groups and categories the sub-steps get narrow, so increase `barwidth`.


## Disclaimer

I might maintain and improve the package. I might also not.


## Development

The project uses [uv](https://docs.astral.sh/uv/) for environments and dependency locking.

```bash
git clone https://github.com/docdru/plotlywaterfall.git
cd plotlywaterfall
uv sync                       # creates .venv with the package + all dev tools
uv run pre-commit install     # optional: run checks on every commit
```

Common tasks:

| Task | Command |
|---|---|
| Run tests | `uv run pytest` |
| Tests with coverage | `uv run pytest --cov` |
| Test another Python | `uv run --python 3.11 pytest` |
| Lint / auto-fix | `uv run ruff check --fix` |
| Format | `uv run ruff format` |
| Type check | `uv run mypy` |
| Execute example notebook | `uv run pytest --nbmake examples/ -p no:warnings` |
| Open notebooks | `uv run --with jupyterlab jupyter lab` |
| Build sdist + wheel | `uv build` |

CI (GitHub Actions) runs lint, type checks, the test suite on Python 3.11–3.15 (Linux, plus Windows; macOS on `main` and the weekly run),
a test against the lowest supported dependency versions, the example notebook, and a package build.

### AI pull-request review

Pull requests get an automated review comment (correctness and tests, API/docs consistency,
security and supply chain, surprising changes) from `.github/workflows/ai-review.yml`, which runs
`scripts/ai_review.py` against the Mistral API. The comment is updated on every push.

- **Setup:** add the repository secret `MISTRAL_API_KEY` (*Settings → Secrets and variables → Actions*).
  Optionally set the repository variable `AI_REVIEW_MODEL` to override the default model (`mistral-large-2512`).
- **Scope:** runs for non-draft PRs from branches in this repository by authors with write access;
  fork, bot and draft PRs are skipped. Mark a draft "Ready for review" to trigger it.
- **Try locally** (prints the prompt, calls nothing, posts nothing):
  `GITHUB_REPOSITORY=docdru/plotlywaterfall GITHUB_TOKEN=$(gh auth token) python scripts/ai_review.py --pr 1 --dry-run`

The review is advisory: it is not part of the required checks, and its findings should be verified.

### Releasing

1. Bump `__version__` in `src/plotlywaterfall/__about__.py` and add a `CHANGELOG.md` entry.
2. Commit, then tag and push: `git tag v0.9.4 && git push origin v0.9.4`.
3. The `Release` workflow builds the package and publishes it to PyPI via
   [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (no API token needed).

## Changelog

Refer to [CHANGELOG.md](https://github.com/docdru/plotlywaterfall/blob/main/CHANGELOG.md)
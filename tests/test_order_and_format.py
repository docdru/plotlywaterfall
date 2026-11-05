"""x-axis order, date labels, accounting negatives and number units (1.0.1)."""

import datetime

import pandas as pd
import pytest

from plotlywaterfall import Waterfall, waterfall
from plotlywaterfall._format import NumberFormatter, auto_unit


def _ticks(fig):
    return list(fig.layout.xaxis.ticktext)


def _labels(fig):
    return [a["text"] for a in fig.layout.annotations]


# --- running levels follow the x-axis in every group ---------------------------------------


def test_group_rows_in_different_order_get_the_same_levels():
    # regression: levels were accumulated in each group's own row order
    df = pd.DataFrame(
        {
            "X": ["A", "B", "C", "C", "A", "B"],
            "Y": [10, -3, 2, 2, 10, -3],
            "group": ["G1"] * 3 + ["G2"] * 3,
        }
    )
    fig = waterfall(df, x="X", y="Y", group="group", total=True)
    bases = {t["name"]: list(t["base"]) for t in fig.data}
    assert bases["G1"] == bases["G2"] == [0, 10, 7, 0]
    connectors = [s["y0"] for s in fig.layout.shapes]
    assert connectors == [10, 7, 9] * 2


# --- order of x, groups and categories -----------------------------------------------------


def test_categorical_order_of_x_is_used():
    df = pd.DataFrame(
        {"X": pd.Categorical(["B", "A", "C"], categories=["A", "B", "C", "unused"]), "Y": [1, 2, 3]}
    )
    fig = waterfall(df, x="X", y="Y", total=True)
    assert _ticks(fig) == ["A", "B", "C", "Total"]
    assert list(fig.data[0]["base"]) == [0, 2, 3, 0]  # A=2 first, then B=1, C=3


def test_category_orders_for_x():
    df = pd.DataFrame({"X": ["B", "A", "C"], "Y": [1, 2, 3]})
    fig = waterfall(df, x="X", y="Y", category_orders={"X": ["C", "A"]})
    assert _ticks(fig) == ["C", "A", "B"]  # listed values first, the rest in order of appearance


def test_total_goes_after_the_last_x_in_display_order():
    df = pd.DataFrame({"X": ["B", "A"], "Y": [1, 2]})
    fig = waterfall(df, x="X", y="Y", total=True, category_orders={"X": ["B", "A"]})
    assert _ticks(fig) == ["B", "A", "Total"]
    fig = waterfall(df, x="X", y="Y", total=True, category_orders={"X": ["A", "B"]})
    assert _ticks(fig) == ["A", "B", "Total"]


def test_category_orders_for_groups_and_categories():
    df = pd.DataFrame(
        {
            "X": ["A"] * 4,
            "Y": [1, 2, 3, 4],
            "category": ["c1", "c2", "c1", "c2"],
            "group": ["G1", "G1", "G2", "G2"],
        }
    )
    fig = waterfall(
        df,
        x="X",
        y="Y",
        category="category",
        group="group",
        category_orders={"group": ["G2", "G1"], "category": ["c2", "c1"]},
    )
    assert [(t["legendgroup"], t["name"]) for t in fig.data] == [
        ("G2", "c2"),
        ("G2", "c1"),
        ("G1", "c2"),
        ("G1", "c1"),
    ]
    stack = {(t["legendgroup"], t["name"]): t["base"][0] for t in fig.data}
    assert stack[("G2", "c2")] == 0  # c2 is stacked first
    assert stack[("G2", "c1")] == 4


def test_palette_follows_category_orders():
    df = pd.DataFrame({"X": ["A", "A"], "Y": [1, 2], "category": ["c1", "c2"]})
    fig = waterfall(
        df,
        x="X",
        y="Y",
        category="category",
        category_orders={"category": ["c2", "c1"]},
        color_discrete_sequence=["red", "blue"],
    )
    assert {t["name"]: t["marker"]["color"] for t in fig.data} == {"c2": "red", "c1": "blue"}


def test_category_orders_unknown_column():
    df = pd.DataFrame({"X": ["A"], "Y": [1]})
    with pytest.raises(ValueError, match="category_orders keys"):
        waterfall(df, x="X", y="Y", category_orders={"Region": ["EU"]})


def test_subtotal_after_categorical_x():
    df = pd.DataFrame({"X": pd.Categorical(["B", "A"], categories=["A", "B"]), "Y": [1, 2]})
    wf = Waterfall(df, x="X", y="Y")
    wf.add_subtotal("A", "Sub")
    assert _ticks(wf.get_fig()) == ["A", "Sub", "B"]


# --- date labels ---------------------------------------------------------------------------


def test_month_end_dates_are_shown_as_months():
    df = pd.DataFrame({"X": pd.date_range("2026-01-31", periods=3, freq="ME"), "Y": [5, -2, 3]})
    fig = waterfall(df, x="X", y="Y", total=True)
    assert _ticks(fig) == ["Jan 2026", "Feb 2026", "Mar 2026", "Total"]
    assert fig.data[0]["customdata"][0][0] == "Jan 2026"  # hover uses the same label


def test_days_in_one_month_are_shown_as_dates():
    df = pd.DataFrame({"X": pd.to_datetime(["2026-01-05", "2026-01-12"]), "Y": [1, 2]})
    assert _ticks(waterfall(df, x="X", y="Y")) == ["2026-01-05", "2026-01-12"]


def test_dates_with_times_and_python_dates():
    df = pd.DataFrame({"X": pd.to_datetime(["2026-01-05 09:30", "2026-01-05 17:00"]), "Y": [1, 2]})
    assert _ticks(waterfall(df, x="X", y="Y")) == ["2026-01-05 09:30", "2026-01-05 17:00"]

    df = pd.DataFrame({"X": [datetime.date(2026, 1, 1), datetime.date(2026, 2, 1)], "Y": [1, 2]})
    assert _ticks(waterfall(df, x="X", y="Y")) == ["Jan 2026", "Feb 2026"]


def test_x_format():
    df = pd.DataFrame({"X": pd.date_range("2026-01-31", periods=2, freq="ME"), "Y": [1, 2]})
    assert _ticks(waterfall(df, x="X", y="Y", x_format="%m/%y")) == ["01/26", "02/26"]

    df = pd.DataFrame({"X": [2025, 2026], "Y": [1, 2]})
    assert _ticks(waterfall(df, x="X", y="Y", x_format=lambda v: f"FY{v}")) == ["FY2025", "FY2026"]
    with pytest.raises(ValueError, match="strftime pattern"):
        waterfall(df, x="X", y="Y", x_format="%Y")


# --- accounting negatives and units --------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "signed", "expected"),
    [(-7, True, "(7)"), (9, True, "9"), (-1234.5, False, "(1,234.5)"), (0, True, "0")],
)
def test_parentheses(value, signed, expected):
    assert NumberFormatter(negative_style="parentheses")(value, signed=signed) == expected


def test_parentheses_wrap_prefix_unit_and_suffix():
    fmt = NumberFormatter(prefix="$", suffix=" USD", negative_style="parentheses", unit="M")
    assert fmt(-2_500_000) == "($2.5M USD)"


@pytest.mark.parametrize(
    ("unit", "expected"),
    [("k", "+1,250k"), ("M", "+1.25M"), ("bn", "0bn")],  # 0.00125bn rounds to zero: no sign
)
def test_units(unit, expected):
    assert NumberFormatter(unit=unit)(1_250_000, signed=True) == expected


@pytest.mark.parametrize(
    ("values", "unit"),
    [([5, 999], None), ([1_000, 3], "k"), ([-2_500_000], "M"), ([3e9, 1], "bn"), ([], None)],
)
def test_auto_unit(values, unit):
    assert auto_unit(values) == unit


def test_auto_unit_uses_one_unit_for_the_whole_chart():
    df = pd.DataFrame({"X": ["Sales", "Costs", "Tax"], "Y": [1_250_000, -730_000, -95_000]})
    fig = waterfall(df, x="X", y="Y", total=True, number_unit="auto")
    assert _labels(fig) == ["+1.25M", "-0.73M", "-0.1M", "0.42M"]


def test_accounting_chart():
    df = pd.DataFrame({"X": ["Sales", "Costs"], "Y": [1_250_000, -730_000]})
    fig = waterfall(
        df,
        x="X",
        y="Y",
        total=True,
        number_unit="k",
        negative_style="parentheses",
        number_prefix="$",
    )
    assert _labels(fig) == ["$1,250k", "($730k)", "$520k"]


def test_invalid_number_options():
    df = pd.DataFrame({"X": ["A"], "Y": [1]})
    with pytest.raises(ValueError, match="number_unit"):
        waterfall(df, x="X", y="Y", number_unit="mio")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="negative_style"):
        waterfall(df, x="X", y="Y", negative_style="red")  # type: ignore[arg-type]

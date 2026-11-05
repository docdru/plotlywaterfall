"""Given and calculated levels: measure, start, reconcile (1.2.0)."""

import numpy as np
import pandas as pd
import pytest

from plotlywaterfall import Waterfall, waterfall

INCREASE, DECREASE, TOTAL = "#2ca02c", "#d62728", "#7f7f7f"


@pytest.fixture
def bridge():
    return pd.DataFrame(
        {"X": ["EBIT 2025", "Volume", "Price", "FX", "Costs"], "Y": [100, 12, 5, -4, -9]}
    )


@pytest.fixture
def two_years():
    return pd.DataFrame(
        {
            "X": [
                "EBIT 2024",
                "Volume 25",
                "Costs 25",
                "EBIT 2025",
                "Volume 26",
                "Costs 26",
                "EBIT 2026",
            ],
            "Y": [100, 12, -5, 110, 8, -3, None],
            "measure": [
                "absolute",
                "relative",
                "relative",
                "absolute",
                "relative",
                "relative",
                "total",
            ],
        }
    )


def _bars(fig):
    (trace,) = [t for t in fig.data if t["legendgroup"] != "direction"]
    return trace


def _labels(fig):
    return [a["text"] for a in fig.layout.annotations]


def _clean(values):
    return [None if np.isnan(v) else float(v) for v in values]


# --- start shortcut ------------------------------------------------------------------------


def test_start_is_drawn_as_a_level(bridge):
    fig = waterfall(
        bridge, x="X", y="Y", start="EBIT 2025", total=True, total_column_name="EBIT 2026"
    )
    bars = _bars(fig)
    assert list(fig.layout.xaxis.ticktext) == [
        "EBIT 2025",
        "Volume",
        "Price",
        "FX",
        "Costs",
        "EBIT 2026",
    ]
    assert _clean(bars["y"]) == [100, 12, 5, -4, -9, 104]
    assert list(bars["base"]) == [0, 100, 112, 117, 113, 0]
    assert list(bars["marker"]["color"]) == [TOTAL, INCREASE, INCREASE, DECREASE, DECREASE, TOTAL]
    assert _labels(fig) == ["100", "+12", "+5", "-4", "-9", "104"]  # levels unsigned
    assert bars["customdata"][0][1] == "EBIT 2025: 100"
    assert "Increase" in [t["name"] for t in fig.data]  # legend: the start is not an increase
    assert [t["name"] for t in fig.data if t["legendgroup"] == "direction"] == [
        "Increase",
        "Decrease",
        "Total",
    ]


def test_without_start_the_first_value_is_a_change(bridge):
    fig = waterfall(bridge, x="X", y="Y")
    assert _labels(fig)[0] == "+100"


def test_start_list_and_unknown_value(bridge):
    fig = waterfall(bridge, x="X", y="Y", start=["EBIT 2025"])
    assert _labels(fig)[0] == "100"
    with pytest.raises(ValueError, match="start='EBIT 2030'"):
        waterfall(bridge, x="X", y="Y", start="EBIT 2030")


# --- measure column ------------------------------------------------------------------------


def test_reconcile_other_inserts_the_gap(two_years):
    fig = waterfall(two_years, x="X", y="Y", measure="measure")
    bars = _bars(fig)
    assert list(fig.layout.xaxis.ticktext) == [
        "EBIT 2024", "Volume 25", "Costs 25", "Other", "EBIT 2025", "Volume 26", "Costs 26", "EBIT 2026",
    ]  # fmt: skip
    assert _clean(bars["y"]) == [100, 12, -5, 3, 110, 8, -3, 115]
    assert list(bars["base"]) == [0, 100, 112, 107, 0, 110, 118, 0]
    assert [s["y0"] for s in fig.layout.shapes] == [100, 112, 107, 110, 110, 118, 115]
    assert bars["customdata"][3][1] == "Change: +3<br>Running total: 110"


def test_reconcile_jump_draws_the_given_level(two_years):
    fig = waterfall(two_years, x="X", y="Y", measure="measure", reconcile="jump")
    bars = _bars(fig)
    assert "Other" not in list(fig.layout.xaxis.ticktext)
    assert _clean(bars["y"]) == [100, 12, -5, 110, 8, -3, 115]
    # the connector arrives at 107 and the next one leaves at 110: the jump stays visible
    assert [s["y0"] for s in fig.layout.shapes] == [100, 112, 107, 110, 118, 115]


def test_reconcile_error(two_years):
    with pytest.raises(ValueError, match=r"differs from the level .* by 3"):
        waterfall(two_years, x="X", y="Y", measure="measure", reconcile="error")


def test_matching_levels_need_no_reconciliation(two_years):
    two_years.loc[3, "Y"] = 107
    for reconcile in ("other", "error"):
        fig = waterfall(two_years, x="X", y="Y", measure="measure", reconcile=reconcile)
        assert "Other" not in list(fig.layout.xaxis.ticktext)
        assert _clean(_bars(fig)["y"])[3] == 107


def test_total_rows_are_calculated_and_their_values_ignored(two_years):
    two_years.loc[6, "Y"] = 999
    fig = waterfall(two_years, x="X", y="Y", measure="measure")
    assert _clean(_bars(fig)["y"])[-1] == 115


def test_empty_measure_cells_are_changes():
    df = pd.DataFrame({"X": ["Start", "A"], "Y": [10, 2], "measure": ["absolute", None]})
    fig = waterfall(df, x="X", y="Y", measure="measure")
    assert _labels(fig) == ["10", "+2"]


def test_reconcile_label_and_several_gaps():
    df = pd.DataFrame(
        {
            "X": ["Q1", "a", "Q2", "b", "Q3"],
            "Y": [10, 1, 12, 1, 15],
            "measure": ["absolute", "relative", "absolute", "relative", "absolute"],
        }
    )
    fig = waterfall(df, x="X", y="Y", measure="measure", reconcile_label="Unexplained")
    assert list(fig.layout.xaxis.ticktext) == [
        "Q1",
        "a",
        "Unexplained",
        "Q2",
        "b",
        "Unexplained",
        "Q3",
    ]
    assert _clean(_bars(fig)["y"]) == [10, 1, 1, 12, 1, 2, 15]


# --- categories and groups -----------------------------------------------------------------


def test_plan_vs_actual_with_categories():
    df = pd.DataFrame(
        {
            "X": ["Plan", "Plan", "Volume", "Volume", "Price", "Actual", "Actual"],
            "Y": [60, 40, 5, -3, 2, 63, 38],
            "category": ["A", "B", "A", "B", "A", "A", "B"],
            "measure": ["absolute"] * 2 + ["relative"] * 3 + ["absolute"] * 2,
        }
    )
    fig = waterfall(df, x="X", y="Y", category="category", measure="measure")
    assert list(fig.layout.xaxis.ticktext) == ["Plan", "Volume", "Price", "Other", "Actual"]
    traces = {t["name"]: t for t in fig.data}
    # per category: A walks 60 -> 65 -> 67 -> 63 (gap -4), B walks 40 -> 37 -> 38 (gap +1)
    assert _clean(traces["A"]["y"]) == [60, 5, 2, -4, 63]
    assert _clean(traces["B"]["y"]) == [40, -3, None, 1, 38]
    assert _labels(fig) == ["100", "+2", "+2", "-3", "101"]


def test_each_group_has_its_own_levels():
    df = pd.DataFrame(
        {
            "X": ["Start", "A", "End"] * 2,
            "Y": [10, 2, 12, 50, -5, 40],
            "group": ["G1"] * 3 + ["G2"] * 3,
        }
    )
    fig = waterfall(df, x="X", y="Y", group="group", start=["Start", "End"])
    bars = {t["name"]: t for t in fig.data if t["legendgroup"] != "direction"}
    # G1 needs no reconciliation (10 + 2 = 12), G2 does (50 - 5 = 45, given 40)
    assert list(fig.layout.xaxis.ticktext) == ["Start", "A", "Other", "End"]
    assert _clean(bars["G1"]["y"]) == [10, 2, None, 12]
    assert _clean(bars["G2"]["y"]) == [50, -5, -5, 40]


def test_group_without_a_given_level_shows_the_calculated_one():
    df = pd.DataFrame(
        {
            "X": ["Start", "A", "End", "Start", "A"],
            "Y": [10, 2, 20, 5, 1],
            "group": ["G1"] * 3 + ["G2"] * 2,
        }
    )
    fig = waterfall(df, x="X", y="Y", group="group", start=["Start", "End"], reconcile="jump")
    bars = {t["name"]: t for t in fig.data if t["legendgroup"] != "direction"}
    assert _clean(bars["G2"]["y"]) == [5, 1, 6]


def test_sumtotal_uses_the_final_level(bridge):
    fig = waterfall(bridge, x="X", y="Y", start="EBIT 2025", total=True, total_type="sumtotal")
    total = next(t for t in fig.data if t["name"] == "Total")
    assert list(total["y"]) == [104]


# --- validation ----------------------------------------------------------------------------


def test_invalid_measures(two_years):
    with pytest.raises(ValueError, match="measure='kind' is not a column"):
        waterfall(two_years, x="X", y="Y", measure="kind")
    bad = two_years.assign(measure=two_years.measure.replace("absolute", "level"))
    with pytest.raises(ValueError, match="measure values must be one of"):
        waterfall(bad, x="X", y="Y", measure="measure")
    mixed = pd.DataFrame(
        {"X": ["A", "A"], "Y": [1, 2], "measure": ["absolute", "relative"], "c": ["c1", "c2"]}
    )
    with pytest.raises(ValueError, match="same measure"):
        waterfall(mixed, x="X", y="Y", category="c", measure="measure")
    with pytest.raises(ValueError, match="reconcile"):
        Waterfall(two_years, x="X", y="Y", measure="measure", reconcile="ignore")  # type: ignore[arg-type]


def test_missing_values_still_rejected_outside_total_rows(two_years):
    two_years.loc[1, "Y"] = None
    with pytest.raises(ValueError, match="missing values"):
        waterfall(two_years, x="X", y="Y", measure="measure")

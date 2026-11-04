"""Regression tests for bugs found in the 0.9.3 code review.

Each test fails on 0.9.3 and documents the intended behaviour.
"""

import numpy as np
import pandas as pd
import pytest

from plotlywaterfall.waterfall import Waterfall


def _total_bars(fig, name="Total"):
    return {trace["legendgroup"]: trace["y"][0] for trace in fig.data if trace["name"] == name}


# --- sum totals must use the configured value column, not a hardcoded "Y" ---------------


def test_sumtotal_with_groups_uses_configured_value_column():
    df = pd.DataFrame(
        {
            "Step": ["A", "B", "C"] * 2,
            "Amount": [3, 4, 5, 5, 6, 7],
            "Segment": ["G1"] * 3 + ["G2"] * 3,
        }
    )
    fig = Waterfall(
        df, x="Step", y="Amount", group="Segment", total=True, total_type="sumtotal"
    ).get_fig()

    assert _total_bars(fig) == {"G1": 12, "G2": 18}


# --- the sign check for totals must not compare bars of different groups ----------------


def test_groups_with_opposite_signs_at_same_x():
    df = pd.DataFrame(
        {
            "X": ["A", "B"] * 2,
            "Y": [1, 1, -1, 1],
            "group": ["G1"] * 2 + ["G2"] * 2,
        }
    )
    fig = Waterfall(df, x="X", y="Y", group="group").get_fig()

    by_group = {trace["legendgroup"]: trace for trace in fig.data}
    assert list(by_group["G1"]["base"]) == [0, 1]
    assert list(by_group["G2"]["base"]) == [0, -1]


def test_groups_with_opposite_signed_totals():
    df = pd.DataFrame(
        {
            "X": ["A", "B"] * 2,
            "Y": [1, 2, -3, -4],
            "category": ["c1", "c2"] * 2,
            "group": ["G1"] * 2 + ["G2"] * 2,
        }
    )
    fig = Waterfall(df, x="X", y="Y", category="category", group="group", total=True).get_fig()

    totals = {
        (trace["legendgroup"], trace["name"]): trace["y"][-1]
        for trace in fig.data
        if not np.isnan(trace["y"][-1])
    }
    assert totals == {("G1", "c1"): 1, ("G1", "c2"): 2, ("G2", "c1"): -3, ("G2", "c2"): -4}


def test_mixed_signed_total_within_one_group_still_rejected():
    df = pd.DataFrame(
        {
            "X": ["A", "B", "C", "D"],
            "Y": [1, 2, -3, -4],
            "category": ["c1", "c1", "c2", "c2"],
            "group": ["G1"] * 2 + ["G2"] * 2,
        }
    )
    # G1 only has c1 (positive) and G2 only has c2 (negative): fine
    Waterfall(df, x="X", y="Y", category="category", group="group", total=True).get_fig()

    df["group"] = "G1"
    with pytest.raises(NotImplementedError, match="mixed signed categories in totals"):
        Waterfall(df, x="X", y="Y", category="category", group="group", total=True).get_fig()


# --- the caller's subtotals dict must not be modified ------------------------------------


def test_subtotals_argument_is_not_mutated():
    df = pd.DataFrame({"X": ["A", "B", "C"], "Y": [1, 2, 3]})
    subtotals = {"B": "Sub"}

    Waterfall(df, x="X", y="Y", total=True, subtotals=subtotals)
    assert subtotals == {"B": "Sub"}

    wf = Waterfall(df, x="X", y="Y", subtotals=subtotals)
    wf.add_subtotal("A", "Early")
    assert subtotals == {"B": "Sub"}


def test_reusing_subtotals_dict_does_not_add_bars():
    df = pd.DataFrame({"X": ["A", "B", "C"], "Y": [1, 2, 3]})
    subtotals = {"B": "Sub"}

    Waterfall(df, x="X", y="Y", total=True, subtotals=subtotals).get_fig()
    fig = Waterfall(df, x="X", y="Y", subtotals=subtotals).get_fig()

    assert list(fig.layout.xaxis.ticktext) == ["A", "B", "Sub", "C"]


# --- clear error messages for invalid input ----------------------------------------------


def test_unknown_subtotal_key_in_constructor():
    df = pd.DataFrame({"X": ["A", "B"], "Y": [1, 2]})
    with pytest.raises(ValueError, match="Cannot find value 'Z'"):
        Waterfall(df, x="X", y="Y", subtotals={"Z": "Sub"})


def test_missing_values_are_reported_as_such():
    df = pd.DataFrame({"X": ["A", "B"], "Y": [1, np.nan]})
    with pytest.raises(ValueError, match="missing values"):
        Waterfall(df, x="X", y="Y")


@pytest.mark.parametrize("argument", ["x", "y", "group", "category"])
def test_unknown_column_is_reported(argument):
    df = pd.DataFrame({"X": ["A", "B"], "Y": [1, 2], "g": ["a", "b"], "c": ["a", "b"]})
    kwargs = {"x": "X", "y": "Y", "group": "g", "category": "c", argument: "nope"}
    with pytest.raises(ValueError, match=f"{argument}='nope' is not a column"):
        Waterfall(df, **kwargs)


def test_invalid_total_type():
    df = pd.DataFrame({"X": ["A", "B"], "Y": [1, 2]})
    with pytest.raises(ValueError, match="total_type"):
        Waterfall(df, x="X", y="Y", total=True, total_type="sum")


def test_colors_missing_a_category_falls_back_to_default():
    df = pd.DataFrame({"X": ["A", "A"], "Y": [1, 2], "category": ["one", "two"]})
    fig = Waterfall(df, x="X", y="Y", category="category", colors={"one": "red"}).get_fig()

    colors = {trace["name"]: trace["marker"]["color"] for trace in fig.data}
    assert colors == {"one": "red", "two": None}


# --- defaults are not shared between instances -------------------------------------------


def test_connector_line_default_is_not_shared():
    df = pd.DataFrame({"X": ["A", "B"], "Y": [1, 2]})
    first = Waterfall(df, x="X", y="Y")
    first._connector_line["color"] = "red"

    fig = Waterfall(df, x="X", y="Y").get_fig()
    assert fig.layout.shapes[0]["line"]["color"] == "darkgrey"


def test_top_level_import():
    import plotlywaterfall

    assert plotlywaterfall.Waterfall is Waterfall
    assert isinstance(plotlywaterfall.__version__, str)

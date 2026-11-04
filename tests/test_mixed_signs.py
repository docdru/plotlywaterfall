"""Bars whose categories have mixed signs are split into sub-steps (mixed_signs="steps")."""

import numpy as np
import pandas as pd
import pytest

from plotlywaterfall import Waterfall

BARWIDTH = 0.3
GAP = 0.01
# Single group: left edge of the bar relative to the x-value (see Waterfall._offset)
FULL_OFFSET = -(BARWIDTH + GAP / 2) / 2


@pytest.fixture
def df():
    # Revenue +9, Costs -7 (operating); Other mixes +1 operating and -4 one-off
    return pd.DataFrame(
        {
            "X": ["Revenue", "Costs", "Other", "Other"],
            "Y": [9, -7, 1, -4],
            "category": ["Operating", "Operating", "Operating", "One-off"],
        }
    )


def _traces(fig):
    return {trace["name"]: trace for trace in fig.data}


def _at(trace, position, key):
    value = trace[key]
    return value[position] if np.ndim(value) else value


def test_mixed_step_walks_from_start_to_end_level(df):
    fig = Waterfall(df, x="X", y="Y", category="category").get_fig()
    traces = _traces(fig)
    other = 2  # x-position of "Other"

    # Operating starts at the running level 2 and goes up to 3, One-off walks down from 3 to -1
    assert _at(traces["Operating"], other, "base") == 2
    assert _at(traces["Operating"], other, "y") == 1
    assert _at(traces["One-off"], other, "base") == 3
    assert _at(traces["One-off"], other, "y") == -4

    # Connectors: Revenue -> Costs at 9, Costs -> Other at 2
    assert [shape["y0"] for shape in fig.layout.shapes] == [9, 2]


def test_substeps_share_the_bar_slot_side_by_side(df):
    fig = Waterfall(df, x="X", y="Y", category="category").get_fig()
    traces = _traces(fig)
    full_offset = FULL_OFFSET
    other = 2

    first, second = traces["Operating"], traces["One-off"]
    slot = BARWIDTH / 2
    assert _at(first, other, "width") == pytest.approx(slot * 0.9)
    assert _at(second, other, "width") == pytest.approx(slot * 0.9)
    assert _at(first, other, "offset") == pytest.approx(full_offset + slot * 0.05)
    assert _at(second, other, "offset") == pytest.approx(full_offset + slot + slot * 0.05)
    # Bars that are not split keep the full width
    assert _at(first, 0, "width") == BARWIDTH
    assert _at(first, 0, "offset") == pytest.approx(full_offset)


def test_net_ghost_spans_the_net_change(df):
    fig = Waterfall(df, x="X", y="Y", category="category").get_fig()
    ghost = _traces(fig)["Net change"]

    assert list(ghost["x"]) == [2]
    assert list(ghost["base"]) == [2]
    assert list(ghost["y"]) == [-3]
    assert ghost["width"] == BARWIDTH
    assert ghost["showlegend"] is False
    # drawn first, so it sits behind the sub-steps
    assert fig.data[0]["name"] == "Net change"


def test_mixed_total_walks_from_zero(df):
    fig = Waterfall(df, x="X", y="Y", category="category", total=True).get_fig()
    traces = _traces(fig)
    total = 3

    assert _at(traces["Operating"], total, "base") == 0
    assert _at(traces["Operating"], total, "y") == 3
    assert _at(traces["One-off"], total, "base") == 3
    assert _at(traces["One-off"], total, "y") == -4
    # The connector from Other to Total sits at the net level -1, where the walk ends
    assert [shape["y0"] for shape in fig.layout.shapes] == [9, 2, -1]
    ghost = traces["Net change"]
    assert list(ghost["x"]) == [2, 3]
    assert list(ghost["base"]) == [2, 0]
    assert list(ghost["y"]) == [-3, -1]


def test_net_ghost_can_be_disabled_or_styled(df):
    fig = Waterfall(df, x="X", y="Y", category="category", net_ghost=False).get_fig()
    assert "Net change" not in _traces(fig)

    fig = Waterfall(df, x="X", y="Y", category="category", net_ghost={"color": "pink"}).get_fig()
    assert _traces(fig)["Net change"]["marker"]["color"] == "pink"


@pytest.mark.parametrize(
    ("step_order", "expected_order"),
    [
        ("data", ["Plus", "Big minus", "Small minus"]),
        ("positive_first", ["Plus", "Big minus", "Small minus"]),
        ("largest_first", ["Big minus", "Plus", "Small minus"]),
    ],
)
def test_step_order(step_order, expected_order):
    df = pd.DataFrame(
        {
            "X": ["A", "B", "B", "B"],
            "Y": [10, 2, -5, -1],
            "category": ["Plus", "Plus", "Big minus", "Small minus"],
        }
    )
    fig = Waterfall(df, x="X", y="Y", category="category", step_order=step_order).get_fig()
    traces = _traces(fig)
    b = 1
    by_offset = sorted(expected_order, key=lambda name: _at(traces[name], b, "offset"))
    assert by_offset == expected_order

    # Each sub-step starts where the previous one ended, beginning at the level 10
    running = 10
    for name in expected_order:
        assert _at(traces[name], b, "base") == running
        running += _at(traces[name], b, "y")
    assert running == 6


def test_positive_first_moves_positives_to_the_front():
    df = pd.DataFrame(
        {"X": ["A", "A"], "Y": [-3, 2], "category": ["Minus", "Plus"]},
    )
    fig = Waterfall(df, x="X", y="Y", category="category", step_order="positive_first").get_fig()
    traces = _traces(fig)
    assert _at(traces["Plus"], 0, "offset") < _at(traces["Minus"], 0, "offset")
    assert _at(traces["Plus"], 0, "base") == 0
    assert _at(traces["Minus"], 0, "base") == 2


def test_each_group_walks_on_its_own():
    df = pd.DataFrame(
        {
            "X": ["A", "B", "B"] + ["A", "B"],
            "Y": [5, 1, -3] + [5, -2],
            "category": ["c1", "c1", "c2"] + ["c1", "c2"],
            "group": ["G1"] * 3 + ["G2"] * 2,
        }
    )
    fig = Waterfall(df, x="X", y="Y", category="category", group="group").get_fig()
    g1 = {t["name"]: t for t in fig.data if t["legendgroup"] == "G1"}
    g2 = {t["name"]: t for t in fig.data if t["legendgroup"] == "G2"}

    assert _at(g1["c1"], 1, "base") == 5
    assert _at(g1["c2"], 1, "base") == 6
    assert list(g1["Net change"]["y"]) == [-2]
    # G2 has no mixed bar: plain stacked bars with scalar width, no ghost
    assert "Net change" not in g2
    assert g2["c1"]["width"] == BARWIDTH


def test_charts_without_mixed_signs_are_unchanged():
    df = pd.DataFrame({"X": ["A", "B", "B"], "Y": [3, 1, 2], "category": ["c1", "c1", "c2"]})
    fig = Waterfall(df, x="X", y="Y", category="category", total=True).get_fig()

    assert [t["name"] for t in fig.data] == ["c1", "c2"]
    assert all(t["width"] == BARWIDTH for t in fig.data)
    assert all(t["offset"] == pytest.approx(FULL_OFFSET) for t in fig.data)


def test_mixed_rows_of_one_category_are_summed_not_split():
    df = pd.DataFrame({"X": ["A", "A", "B"], "Y": [5, -2, 1], "category": ["c1", "c1", "c1"]})
    fig = Waterfall(df, x="X", y="Y", category="category").get_fig()

    assert [t["name"] for t in fig.data] == ["c1"]
    assert list(fig.data[0]["y"]) == [3, 1]


def test_error_mode_keeps_previous_behaviour(df):
    with pytest.raises(NotImplementedError, match="mixed signed categorization"):
        Waterfall(df, x="X", y="Y", category="category", mixed_signs="error")


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"mixed_signs": "split"}, ValueError),
        ({"step_order": "random"}, ValueError),
        ({"net_ghost": "yes"}, TypeError),
    ],
)
def test_invalid_options(df, kwargs, error):
    with pytest.raises(error):
        Waterfall(df, x="X", y="Y", category="category", **kwargs)

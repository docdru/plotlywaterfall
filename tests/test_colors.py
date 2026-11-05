"""Colour API: color, color_discrete_map, color_discrete_sequence, pattern_shape."""

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import pytest

from plotlywaterfall import Waterfall

INCREASE, DECREASE, TOTAL = "#2ca02c", "#d62728", "#7f7f7f"


@pytest.fixture
def simple():
    return pd.DataFrame({"X": ["Revenue", "Costs", "Tax"], "Y": [10, -6, -1]})


@pytest.fixture
def grouped():
    return pd.DataFrame(
        {
            "X": ["Revenue", "Revenue", "Costs", "Costs"] * 2,
            "Y": [4, 2, -2, -1, 3, 3, -2, -2],
            "category": ["A", "B"] * 4,
            "group": ["Plan"] * 4 + ["Actual"] * 4,
        }
    )


def _data_traces(fig):
    return [t for t in fig.data if t["legendgroup"] != "direction"]


def _legend_traces(fig):
    return [t for t in fig.data if t["legendgroup"] == "direction"]


def _colors(fig):
    return {(t["legendgroup"], t["name"]): t["marker"]["color"] for t in _data_traces(fig)}


# --- direction (default without category and group) ---------------------------------------


def test_direction_is_default_without_category_and_group(simple):
    fig = Waterfall(simple, x="X", y="Y", total=True).get_fig()

    (bars,) = _data_traces(fig)
    assert list(bars["marker"]["color"]) == [INCREASE, DECREASE, DECREASE, TOTAL]
    assert bars["showlegend"] is False
    assert [(t["name"], t["marker"]["color"]) for t in _legend_traces(fig)] == [
        ("Increase", INCREASE),
        ("Decrease", DECREASE),
        ("Total", TOTAL),
    ]


def test_direction_legend_lists_only_used_kinds(simple):
    fig = Waterfall(simple[simple.Y > 0], x="X", y="Y").get_fig()
    assert [t["name"] for t in _legend_traces(fig)] == ["Increase"]


def test_direction_colors_can_be_overridden(simple):
    fig = Waterfall(
        simple, x="X", y="Y", total=True, color_discrete_map={"decrease": "orange"}
    ).get_fig()
    (bars,) = _data_traces(fig)
    assert list(bars["marker"]["color"]) == [INCREASE, "orange", "orange", TOTAL]


def test_direction_for_categories_and_sumtotal(grouped):
    fig = Waterfall(
        grouped,
        x="X",
        y="Y",
        category="category",
        group="group",
        color="direction",
        total=True,
        total_type="sumtotal",
    ).get_fig()

    for trace in _data_traces(fig):
        if trace["name"] == "Total":
            assert trace["marker"]["color"] == TOTAL
        else:
            assert list(trace["marker"]["color"]) == [INCREASE, DECREASE]
    # without a pattern dimension the bars carry several colours: legend shows directions only
    assert all(t["showlegend"] is False for t in _data_traces(fig))


def test_direction_colors_mixed_substeps_by_their_own_sign():
    df = pd.DataFrame({"X": ["A", "A"], "Y": [3, -5], "category": ["c1", "c2"]})
    fig = Waterfall(df, x="X", y="Y", category="category", color="direction").get_fig()
    colors = {t["name"]: list(t["marker"]["color"]) for t in _data_traces(fig) if t["name"]}
    assert colors["c1"] == [INCREASE]
    assert colors["c2"] == [DECREASE]


# --- colour by category / group -------------------------------------------------------------


def test_category_is_default_and_consistent_across_groups(grouped):
    fig = Waterfall(grouped, x="X", y="Y", category="category", group="group").get_fig()
    colors = _colors(fig)
    palette = pio.templates[pio.templates.default].layout.colorway

    assert colors[("Plan", "A")] == colors[("Actual", "A")] == palette[0]
    assert colors[("Plan", "B")] == colors[("Actual", "B")] == palette[1]
    assert _legend_traces(fig) == []


def test_color_by_group(grouped):
    fig = Waterfall(
        grouped,
        x="X",
        y="Y",
        category="category",
        group="group",
        color="group",
        color_discrete_map={"Actual": "black"},
        color_discrete_sequence=["teal"],
    ).get_fig()
    colors = _colors(fig)
    assert colors[("Plan", "A")] == colors[("Plan", "B")] == "teal"
    assert colors[("Actual", "A")] == colors[("Actual", "B")] == "black"


def test_map_and_sequence_combine(grouped):
    fig = Waterfall(
        grouped,
        x="X",
        y="Y",
        category="category",
        group="group",
        color_discrete_map={"B": "red"},
        color_discrete_sequence=["navy", "gold"],
    ).get_fig()
    colors = _colors(fig)
    assert colors[("Plan", "A")] == "navy"  # first value without a mapping gets the first colour
    assert colors[("Plan", "B")] == "red"


def test_tuple_keys_colour_one_groups_category(grouped):
    fig = Waterfall(
        grouped,
        x="X",
        y="Y",
        category="category",
        group="group",
        color_discrete_map={"A": "red", ("Actual", "A"): "salmon"},
    ).get_fig()
    colors = _colors(fig)
    assert colors[("Plan", "A")] == "red"
    assert colors[("Actual", "A")] == "salmon"


def test_template_colorway_is_used():
    pio.templates["_wf_test"] = go.layout.Template(layout={"colorway": ["#111111", "#222222"]})
    previous = pio.templates.default
    pio.templates.default = "_wf_test"
    try:
        df = pd.DataFrame({"X": ["A", "B"], "Y": [1, 2], "category": ["c1", "c2"]})
        fig = Waterfall(df, x="X", y="Y", category="category").get_fig()
    finally:
        pio.templates.default = previous
    assert [t["marker"]["color"] for t in fig.data] == ["#111111", "#222222"]


def test_sumtotal_colours(grouped):
    kwargs = {"x": "X", "y": "Y", "category": "category", "group": "group", "total": True}
    kwargs["total_type"] = "sumtotal"

    fig = Waterfall(grouped, **kwargs).get_fig()
    assert {c for (g, n), c in _colors(fig).items() if n == "Total"} == {TOTAL}

    fig = Waterfall(grouped, color_discrete_map={"Total": "black"}, **kwargs).get_fig()
    assert {c for (g, n), c in _colors(fig).items() if n == "Total"} == {"black"}

    fig = Waterfall(grouped, color="group", color_discrete_map={"Plan": "blue"}, **kwargs).get_fig()
    assert _colors(fig)[("Plan", "Total")] == "blue"


# --- patterns -------------------------------------------------------------------------------


def test_pattern_by_group(grouped):
    fig = Waterfall(
        grouped, x="X", y="Y", category="category", group="group", pattern_shape="group"
    ).get_fig()
    patterns = {(t["legendgroup"], t["name"]): t["marker"]["pattern"]["shape"] for t in fig.data}
    assert patterns[("Plan", "A")] == patterns[("Plan", "B")] == ""
    assert patterns[("Actual", "A")] == patterns[("Actual", "B")] == "/"


def test_pattern_shape_map(grouped):
    fig = Waterfall(
        grouped,
        x="X",
        y="Y",
        category="category",
        group="group",
        pattern_shape="group",
        pattern_shape_map={"Plan": "x"},
    ).get_fig()
    patterns = {t["legendgroup"]: t["marker"]["pattern"]["shape"] for t in fig.data}
    assert patterns == {"Plan": "x", "Actual": ""}


def test_direction_with_pattern_keeps_trace_legend(grouped):
    fig = Waterfall(
        grouped,
        x="X",
        y="Y",
        category="category",
        group="group",
        color="direction",
        pattern_shape="category",
    ).get_fig()
    assert all(t["showlegend"] is not False for t in _data_traces(fig))
    assert [t["name"] for t in _legend_traces(fig)] == ["Increase", "Decrease"]


# --- validation -----------------------------------------------------------------------------


def test_unknown_map_keys_warn(grouped):
    with pytest.warns(UserWarning, match=r"keys \['C', \('Plan', 'Z'\)\] match no value"):
        Waterfall(
            grouped,
            x="X",
            y="Y",
            category="category",
            group="group",
            color_discrete_map={"A": "red", "C": "blue", ("Plan", "Z"): "green"},
        )


def test_unknown_pattern_keys_warn(grouped):
    with pytest.warns(UserWarning, match="pattern_shape_map keys"):
        Waterfall(
            grouped,
            x="X",
            y="Y",
            group="group",
            pattern_shape="group",
            pattern_shape_map={"Budget": "x"},
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"color": "X"},
        {"color": "nope"},
        {"pattern_shape": "Y"},
    ],
)
def test_invalid_colour_arguments(grouped, kwargs):
    with pytest.raises(ValueError):  # noqa: PT011 - the messages are checked elsewhere
        Waterfall(grouped, x="X", y="Y", category="category", group="group", **kwargs)


def test_colors_argument_was_removed(grouped):
    with pytest.raises(TypeError, match="colors"):
        Waterfall(grouped, x="X", y="Y", colors={"A": "red"})  # type: ignore[call-arg]

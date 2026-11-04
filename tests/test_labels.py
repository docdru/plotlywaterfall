"""Value labels, number formatting, hover texts, title and axis labels."""

import pandas as pd
import pytest

from plotlywaterfall import Waterfall
from plotlywaterfall._format import NumberFormatter


@pytest.fixture
def df():
    return pd.DataFrame(
        {
            "X": ["Revenue", "Costs", "Other", "Other"],
            "Y": [9, -7, 1, -4],
            "category": ["Operating", "Operating", "Operating", "One-off"],
        }
    )


def _labels(fig):
    return [(round(a["x"], 2), a["y"], a["yanchor"], a["text"]) for a in fig.layout.annotations]


def _hover(fig, name):
    (trace,) = [t for t in fig.data if t["name"] == name]
    return [tuple(row) for row in trace["customdata"]]


# --- number formatting ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "signed", "expected"),
    [
        (9, True, "+9"),
        (-7, True, "-7"),
        (0, True, "0"),
        (0.5, False, "0.5"),
        (1234.567, False, "1,234.57"),
        (-1000, False, "-1,000"),
        (0.001, True, "0"),  # rounds to zero: no sign
    ],
)
def test_default_number_format(value, signed, expected):
    assert NumberFormatter()(value, signed=signed) == expected


def test_prefix_suffix_and_spec():
    fmt = NumberFormatter(",.1f", prefix="$", suffix="M")
    assert fmt(-5, signed=True) == "-$5.0M"
    assert fmt(1234.56) == "$1,234.6M"


def test_callable_format():
    fmt = NumberFormatter(lambda v: f"{v / 1000:.0f}k")
    assert fmt(-25000, signed=True) == "-25k"


def test_invalid_format_spec():
    with pytest.raises(ValueError, match="Invalid number_format"):
        NumberFormatter("not a spec")


# --- bar labels -----------------------------------------------------------------------------


def test_bar_labels_by_default(df):
    fig = Waterfall(df, x="X", y="Y", category="category", total=True).get_fig()
    assert _labels(fig) == [
        (0.0, 9, "bottom", "+9"),  # above the top of the rising bar
        (1.0, 2, "top", "-7"),  # below the bottom of the falling bar
        (2.0, -1, "top", "-3"),  # net change of the split bar, below its lowest point
        (3.0, -1, "top", "-1"),  # totals are not signed unless negative
    ]


def test_bar_labels_per_group():
    df = pd.DataFrame({"X": ["A", "B"] * 2, "Y": [5, -2, 4, 1], "group": ["G1", "G1", "G2", "G2"]})
    fig = Waterfall(df, x="X", y="Y", group="group", total=True).get_fig()
    labels = _labels(fig)
    # two groups side by side: labels sit over the centre of each group's bar
    assert [label[3] for label in labels] == ["+5", "-2", "3", "+4", "+1", "5"]
    assert labels[0][0] < 0 < labels[3][0]


def test_sumtotal_gets_a_label():
    df = pd.DataFrame({"X": ["A", "B"], "Y": [5, -8]})
    fig = Waterfall(df, x="X", y="Y", total=True, total_type="sumtotal").get_fig()
    assert _labels(fig)[-1] == (2.0, -3, "top", "-3")  # below the negative bar


def test_no_labels(df):
    for value in (None, False):
        fig = Waterfall(df, x="X", y="Y", category="category", value_labels=value).get_fig()
        assert fig.layout.annotations == ()
        assert all(t["text"] is None for t in fig.data)


def test_segment_labels(df):
    fig = Waterfall(
        df, x="X", y="Y", category="category", total=True, value_labels="segment"
    ).get_fig()
    (operating,) = [t for t in fig.data if t["name"] == "Operating"]
    assert list(operating["text"]) == ["+9", "-7", "+1", "3"]
    assert operating["textposition"] == "inside"
    assert fig.layout.uniformtext.mode == "hide"
    assert fig.layout.annotations == ()


def test_both_labels(df):
    fig = Waterfall(df, x="X", y="Y", category="category", value_labels="both").get_fig()
    assert len(fig.layout.annotations) == 3
    assert any(t["text"] is not None for t in fig.data)


def test_invalid_value_labels(df):
    for value in ("all", "none", True):
        with pytest.raises(ValueError, match="value_labels"):
            Waterfall(df, x="X", y="Y", value_labels=value)


def test_labels_use_number_format(df):
    fig = Waterfall(
        df, x="X", y="Y", category="category", number_format=".1f", number_suffix=" M€"
    ).get_fig()
    assert [label[3] for label in _labels(fig)] == ["+9.0 M€", "-7.0 M€", "-3.0 M€"]


# --- hover ----------------------------------------------------------------------------------


def test_hover_names_the_step_and_running_total(df):
    fig = Waterfall(df, x="X", y="Y", category="category", total=True).get_fig()
    assert _hover(fig, "Operating") == [
        ("Revenue", "Operating: +9<br>Running total: 9"),
        ("Costs", "Operating: -7<br>Running total: 2"),
        ("Other", "Operating: +1<br>Step: -3<br>Running total: -1"),
        ("Total", "Operating: 3<br>Total: -1"),
    ]
    (trace,) = [t for t in fig.data if t["name"] == "Operating"]
    assert trace["hovertemplate"] == "<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>"


def test_hover_without_category_and_with_group():
    df = pd.DataFrame({"X": ["A", "B"], "Y": [5, -2], "group": ["G1", "G1"]})
    fig = Waterfall(df, x="X", y="Y", group="group", total=True).get_fig()
    (trace,) = [t for t in fig.data if t["name"] == "G1"]
    assert [tuple(row) for row in trace["customdata"]] == [
        ("A", "Change: +5<br>Running total: 5"),
        ("B", "Change: -2<br>Running total: 3"),
        ("Total", "Total: 3"),
    ]
    assert trace["hovertemplate"].endswith("<extra>G1</extra>")


def test_ghost_and_sumtotal_hover():
    df = pd.DataFrame({"X": ["A", "A"], "Y": [1, -4], "category": ["c1", "c2"]})
    fig = Waterfall(
        df, x="X", y="Y", category="category", total=True, total_type="sumtotal"
    ).get_fig()
    ghost = next(t for t in fig.data if t["name"] == "Net change")
    assert list(ghost["customdata"]) == ["-3"]
    total = next(t for t in fig.data if t["name"] == "Total")
    assert [tuple(row) for row in total["customdata"]] == [("Total", "Total: -3")]


# --- title and axis labels ------------------------------------------------------------------


def test_title_and_axis_labels(df):
    fig = Waterfall(
        df,
        x="X",
        y="Y",
        category="category",
        title="Cash bridge",
        labels={"Y": "Cash [MUSD]", "X": "Item"},
    ).get_fig()
    assert fig.layout.title.text == "Cash bridge"
    assert fig.layout.yaxis.title.text == "Cash [MUSD]"
    assert fig.layout.xaxis.title.text == "Item"


def test_default_axis_titles(df):
    fig = Waterfall(df, x="X", y="Y", category="category").get_fig()
    assert fig.layout.yaxis.title.text == "Y"
    assert fig.layout.xaxis.title.text is None
    assert fig.layout.title.text is None


def test_axis_range_leaves_room_for_labels(df):
    fig = Waterfall(df, x="X", y="Y", category="category", total=True).get_fig()
    # bars span -1 .. 9; labels sit above 9 and below -1, so autorange includes some headroom
    include = list(fig.layout.yaxis.autorangeoptions.include)
    assert include == pytest.approx([9 + 0.8, -1 - 0.8])

    fig = Waterfall(df, x="X", y="Y", category="category", value_labels=None).get_fig()
    assert fig.layout.yaxis.autorangeoptions.include is None

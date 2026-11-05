"""The one-call function waterfall() mirrors the Waterfall class."""

import inspect

import pandas as pd
import plotly.graph_objects as go
import pytest

import plotlywaterfall
from plotlywaterfall import Waterfall, waterfall


@pytest.fixture
def df():
    return pd.DataFrame(
        {
            "X": ["A", "B", "B", "C"] * 2,
            "Y": [5, 2, -4, -1, 4, 1, -2, 3],
            "category": ["c1", "c1", "c2", "c1"] * 2,
            "group": ["G1"] * 4 + ["G2"] * 4,
        }
    )


def test_exported():
    assert plotlywaterfall.waterfall is waterfall


def test_returns_the_same_figure_as_the_class(df):
    kwargs = {
        "category": "category",
        "group": "group",
        "total": True,
        "subtotals": {"B": "Sub"},
        "pattern_shape": "group",
        "number_suffix": " €",
        "title": "Bridge",
    }
    fig = waterfall(df, x="X", y="Y", **kwargs)
    assert isinstance(fig, go.Figure)
    assert fig.to_json() == Waterfall(df, x="X", y="Y", **kwargs).get_fig().to_json()


def test_signature_mirrors_the_class():
    """Every argument of Waterfall exists in waterfall() with the same default
    and annotation, so the two cannot drift apart."""
    cls = inspect.signature(Waterfall.__init__).parameters
    fn = inspect.signature(waterfall).parameters
    expected = {name for name in cls if name != "self"}
    assert set(fn) == expected
    for name in expected:
        assert fn[name].default == cls[name].default, name
        assert fn[name].annotation == cls[name].annotation, name


def test_options_are_keyword_only(df):
    with pytest.raises(TypeError):
        waterfall(df, "X", "Y", "group")  # type: ignore[misc]


def test_removed_colors_argument_is_not_offered(df):
    with pytest.raises(TypeError):
        waterfall(df, x="X", y="Y", colors={"c1": "red"})  # type: ignore[call-arg]


def test_import_path_of_earlier_versions_still_works():
    from plotlywaterfall.waterfall import Waterfall as FromModule

    assert FromModule is Waterfall

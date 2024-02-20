from plotlywaterfall.waterfall import Waterfall
import pandas as pd
import numpy as np
import pytest

@pytest.fixture
def def_df():
    return pd.DataFrame({
        "XTest": ["A", "B", "C"]*4 + ["D", "D"], 
        # "YTest": np.random.randint(0, 10, 6), 
        "YTest": [4, 1, 8, 7, 3, 2] + [i-1 for i in [4, 1, 8, 7, 3, 2]] + [2, 5],
        "categoryTest": ["one"]*3+["two"]*3 + ["one"]*3+["two"]*3 + ["two", "three"],
        "groupTest": ["Group1"]*6 + ["Group2"]*6 + ["Group2", "Group3"],
    })

def test_init_full(def_df):
    c = Waterfall(def_df, x="XTest", y="YTest", category="categoryTest", group="groupTest")
    assert c._x == "XTest"

def test_call_get_fig(def_df):
    c = Waterfall(def_df, x="XTest", y="YTest", category="categoryTest", group="groupTest")
    c.get_fig()

def test_call_get_fig_nogroup(def_df):
    c = Waterfall(def_df, x="XTest", y="YTest", category="categoryTest")
    c.get_fig()

def test_call_get_fig_nocategory(def_df):
    c = Waterfall(def_df, x="XTest", y="YTest", group="groupTest")
    c.get_fig()

@pytest.fixture
def def_fig(def_df):
    c = Waterfall(def_df, x="XTest", y="YTest", category="categoryTest", group="groupTest", total=True)
    return c.get_fig()

def test_wrong_x_subtotals(def_df):
    c = Waterfall(def_df, x="XTest", y="YTest", category="categoryTest", group="groupTest")

    with pytest.raises(ValueError) as excinfo:
        c.add_subtotal("E", "TEST")
    assert "Cannot find value " in str(excinfo.value)

def test_fig_data1(def_fig):
    assert (def_fig.data[0]["base"] == np.array([0.0, 11.0, 15.0, 0.0, 0.0])).all()
    # assert (def_fig.data[0]["YTest"] == np.array([ 4.,  1.,  8., np.nan, 13.])).all()
    # assert (def_fig.data[-1]["YTest"] == np.array([np.nan, np.nan, np.nan,  5.,  5.])).all()

def test_colors():
    df = pd.DataFrame({
        "XTest": ["A"]*2 + ["B"]*2 + ["C"]*2,
        "YTest": [i for i in range(6)],
        "categoryTest": ["one", "two"]*3,
        "groupTest": ["Group1"]*3 + ["Group2"]*3,
    })

    colors = {
        "Group1": {"one": "rgb(0,0,0)", "two": "rgb(0,0,1)"},
        "Group2": {"one": "rgb(0,0,2)", "two": "rgb(0,0,3)"},
    }
    c = Waterfall(df, x="XTest", y="YTest", category="categoryTest", group="groupTest", colors=colors)
    fig = c.get_fig()
    for i in fig.data:
        assert i["marker"]["color"] == colors[i["legendgroup"]][i["name"]]

def test_raise_error_mixed_sign1():
    df = pd.DataFrame({
        "XTest": ["A", "B"]*2, 
        # "YTest": np.random.randint(0, 10, 6), 
        "YTest": [1, 1, -1, 1],
        "categoryTest": ["one"]*2 + ["two"]*2,
        "groupTest": ["Group1"]*4
    })

    with pytest.raises(NotImplementedError) as excinfo:
        Waterfall(df, x="XTest", y="YTest", group="groupTest", category="categoryTest")
    assert "Currently mixed signed categorization is not supported (yet)" in str(excinfo.value)

def test_raise_error_mixed_sign2():
    # Should not raise exception if there is only one category per bar
    df = pd.DataFrame({
        "XTest": ["A", "B"]*2, 
        # "YTest": np.random.randint(0, 10, 6), 
        "YTest": [1, 1, -1, 1],
        "categoryTest": ["one"]*4, 
        "groupTest": ["Group1"]*2 + ["Group2"]*2
    })

    Waterfall(df, x="XTest", y="YTest", group="groupTest", category="categoryTest")

def test_raise_error_mixed_sign3():
    df = pd.DataFrame({
        "XTest": ["A", "B"]*2, 
        "YTest": [1, 1, -1, -1],
        "categoryTest": ["one"]*2 + ["two"]*2,
        "groupTest": ["Group1"]*4
    })
    with pytest.raises(NotImplementedError) as excinfo:
        Waterfall(df, x="XTest", y="YTest", group="groupTest", category="categoryTest")
    assert "Currently mixed signed categorization is not supported (yet)" in str(excinfo.value)

def test_raise_error_mixed_sign4():
    # Should not raise an error for similar signs per category and X
    df = pd.DataFrame({
        "XTest": ["A", "A", "B", "B"], 
        "YTest": [1, 1, -1, -1],
        "categoryTest": ["one", "two"]*2,
        "groupTest": ["Group1"]*4
    })
    Waterfall(df, x="XTest", y="YTest", group="groupTest", category="categoryTest")

def test_mixed_total():
    df = pd.DataFrame({
        "X": ["Product A", "Product B", "Plugins", "R&D", "Sales"],
        "Y": [3, 4, 1, -4, -3],
        "category": ["Product Sales", "Product Sales", "Licenses", "R&D", "Sales"]
    })
    with pytest.raises(NotImplementedError) as excinfo:
        Waterfall(df, x="X", y="Y", category="category", total=True).get_fig()
    assert "Currently mixed signed categories in totals are not supported (yet)" in str(excinfo.value)

def test_other_example2():
    df = pd.DataFrame({
        "X": ["Product Sales", "Product Sales", "Licenses", "Product R&D", "Product R&D", "License Mgmt"],
        "Y": [3, 4, 1, -1, -2, -0.5],
        "category": ["Product A", "Product B", "Plugins", "Product A", "Product B", "Plugins"]
    })
    fig = Waterfall(df, x="X", y="Y", category="category", total=True).get_fig()
    assert [[j for j in i["base"]] for i in fig.data] == [
        [0.0, 7.0, 8.0, 5.0, 0.0], 
        [3.0, 7.0, 7.0, 5.0, 2.0], 
        [7.0, 7.0, 5.0, 5.0, 4.0]
        ]
    nan = np.nan
    assert np.array_equal(
        [[j for j in i["y"]] for i in fig.data],
        [
            [3.0, nan, -1.0, nan, 2.0], 
            [4.0, nan, -2.0, nan, 2.0], 
            [nan, 1.0, nan, -0.5, 0.5]
        ], equal_nan=True)
    
    assert [[i["x0"], i["x1"], i["y0"], i["y1"]] for i in fig.layout.shapes] == [
        [-0.1525, 1.1475, 7.0, 7.0],
        [0.8475, 2.1475, 8.0, 8.0],
        [1.8475, 3.1475, 5.0, 5.0],
        [2.8475, 4.1475, 4.5, 4.5]
    ]

def test_other_example3():
    df = pd.DataFrame({
        "X": ["Product Sales", "Product Sales", "Licenses", "Product R&D", "Product R&D", "License Mgmt"],
        "Y": [3, 4, 1, -4, -5, -2],
        "category": ["Product A", "Product B", "Plugins", "Product A", "Product B", "Plugins"]
    })
    fig = Waterfall(df, x="X", y="Y", category="category", total=True).get_fig()
    assert [[j for j in i["base"]] for i in fig.data] == [
        [0.0, 7.0, 8.0, -1.0, 0.0], 
        [3.0, 7.0, 4.0, -1.0, -1.0], 
        [7.0, 7.0, -1.0, -1.0, -2.0]
    ]
    nan = np.nan
    assert np.array_equal(
        [[j for j in i["y"]] for i in fig.data],
        [
            [3.0, nan, -4.0, nan, -1.0], 
            [4.0, nan, -5.0, nan, -1.0], 
            [nan, 1.0, nan, -2.0, -1.0]
        ], equal_nan=True)
    
    assert [[i["x0"], i["x1"], i["y0"], i["y1"]] for i in fig.layout.shapes] == [
        [-0.1525, 1.1475, 7.0, 7.0],
        [0.8475, 2.1475, 8.0, 8.0],
        [1.8475, 3.1475, -1.0, -1.0],
        [2.8475, 4.1475, -3.0, -3.0]
    ]

def test_other_example3_nototal():
    df = pd.DataFrame({
        "X": ["Product Sales", "Product Sales", "Licenses", "Product R&D", "Product R&D", "License Mgmt"],
        "Y": [3, 4, 1, -4, -5, -2],
        "category": ["Product A", "Product B", "Plugins", "Product A", "Product B", "Plugins"]
    })
    fig = Waterfall(df, x="X", y="Y", category="category", total=False).get_fig()
    assert [[j for j in i["base"]] for i in fig.data] == [
        [0.0, 7.0, 8.0, -1.0], 
        [3.0, 7.0, 4.0, -1.0], 
        [7.0, 7.0, -1.0, -1.0]
    ]
    nan = np.nan
    assert np.array_equal(
        [[j for j in i["y"]] for i in fig.data],
        [
            [3.0, nan, -4.0, nan], 
            [4.0, nan, -5.0, nan], 
            [nan, 1.0, nan, -2.0]
        ], equal_nan=True)
    
    assert [[i["x0"], i["x1"], i["y0"], i["y1"]] for i in fig.layout.shapes] == [
        [-0.1525, 1.1475, 7, 7], 
        [0.8475, 2.1475, 8, 8], 
        [1.8475, 3.1475, -1, -1]
        ]

def test_sumtotal():
    df = pd.DataFrame({
        "X": ["A", "B", "C"],
        "Y": [3, 4, 5],
        "category": ["A", "B", "C"]
    })
    fig = Waterfall(df, x="X", y="Y", category="category", total=True, total_type="sumtotal").get_fig()
    output = {i["legendgroup"]: i["y"][0] for i in fig.data if i["name"]=="Total"}
    assert output[None] == 12

    df = pd.DataFrame({
            "X": ["A", "B", "C"] + ["A", "B", "C"],
            "Y": [3, 4, 5] + [5, 6, 7],
            "category": ["A", "B", "C"] + ["A", "B", "C"],
            "group": ["Group1"]*3 + ["Group2"]*3
    })
    fig = Waterfall(df, x="X", y="Y", category="category", group="group", total=True, total_type="sumtotal").get_fig()
    

def test_sumtotal_colorgroup():
    df = pd.DataFrame({
            "X": ["A", "B", "C"] + ["A", "B", "C"],
            "Y": [3, 4, 5] + [5, 6, 7],
            "category": ["A", "B", "C"] + ["A", "B", "C"],
            "group": ["Group1"]*3 + ["Group2"]*3
    })
    colors = {
        "Group1": "blue",
        "Group2": "red"
    }
    fig = Waterfall(df, x="X", y="Y", category="category", group="group", total=True, total_type="sumtotal", colors=colors).get_fig()
    for i in fig.data:
        assert i["marker"]["color"] == colors[i["legendgroup"]]
        

def test_empty_bar_second_group():
    df = pd.DataFrame({
        "X": ["A", "B", "C"] * 4,
        "Y": [1, 2]*3 + [2,3]*3, 
        "group": ["g1"]*6 + ["g2"]*6
    })

    df= df[~((df.X=="B") & (df.group=="g2"))]
    df["X"] = pd.Categorical(df["X"], ["A", "B", "C"])
    df = df.sort_values("X")

    c = Waterfall(df, x="X", y="Y", group="group")
    fig = c.get_fig()
    
    expected_result = np.array([
        [-0.305, 0.995, 3, 3],
        [0.695, 1.995, 6, 6],
        [0.0, 1.3, 5, 5],
        [1.0, 2.3, 5, 5]
    ])

    out = []
    for i in fig.layout.shapes:
        out.append([i["x0"], i["x1"], i["y0"], i["y1"]])
    assert np.allclose(np.array(out), expected_result)
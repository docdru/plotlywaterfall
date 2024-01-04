# plotlywaterfall

## Description 

A small package adding simple waterfall plotting capabilities on top of the plotly graphing package. Waterfall graphs are useful to display e.g. financial data such ans cashflow statements in an easily digestible format. 

While plotly includes basic capabilities to plot waterfall graphs, it ships only limited features. The *plotlywaterfall* package provides simple, plotly-express-style waterfall graphs with grouping, multiple stacked categories and variable colors. 

## Installation

Use pip3: 

`pip3 install plotlywaterfall`

## Usage

More examples can be found in the example notebook (https://github.com/docdru/plotlywaterfall/blob/main/example.ipynb). Let's use this dataframe for a simple yet complete example: 

    df = pd.DataFrame({
        "X": ["A", "B", "C"]*4 + ["D", "D" ], 
        "Y": [4, 1, 8, 7, 3, 2] + [i-1 for i in [4, 1, 8, 7, 3, 2]] + [8, 5],
        "category": ["one"]*3+["two"]*3 + ["one"]*3+["two"]*3 + ["two", "three"],
        "group": ["Group1"]*6 + ["Group2"]*6 + ["Group2", "Group3"]
    })

![DF](https://raw.githubusercontent.com/docdru/plotlywaterfall/main/examples/example_df.png)


One can plot this data, with defined colors and automatic creating of total and subtotal, by using: 


    from plotlywaterfall.waterfall import Waterfall
    
    colors = {
        "Group1": {"one": "red", "two": "blue"},
        "Group2": {"one": "salmon", "two": "lightskyblue"},
        "Group3": "green"
    }


    c = Waterfall(df, x="X", y="Y", category="category", colors=colors, group="group", total=True, subtotals={"C": "Subtotal"})
    fig = c.get_fig()
    fig



Resulting graph:

![Example](https://raw.githubusercontent.com/docdru/plotlywaterfall/main/examples/example.png)


## Disclaimer

I might maintain and improve the package. I might also not.

Known open points: 
- It is not possible to have mixed signs per X-value.
- I am note really happy with the interface for defining the colors.


## Changelog

Refer to [CHANGELOG.md](https://github.com/docdru/plotlywaterfall/blob/main/CHANGELOG.md)
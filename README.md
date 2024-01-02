# plotly-waterfall

## Description 

A small package adding simple waterfall plotting capabilities on top of the plotly graphing package. Waterfall graphs are useful to display e.g. financial data such ans cashflow statements in an easily digestible format. 

While plotly includes basic capabilities to plot waterfall graphs, it ships only limited features. This package provides simple, plotly-express-style waterfall graphs with grouping, multiple stacked categories and variable colors. 

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
    df

|    | X   |   Y | category   | group   |\n|---:|:----|----:|:-----------|:--------|\n|  0 | A   |   4 | one        | Group1  |\n|  1 | B   |   1 | one        | Group1  |\n|  2 | C   |   8 | one        | Group1  |\n|  3 | A   |   7 | two        | Group1  |\n|  4 | B   |   3 | two        | Group1  |\n|  5 | C   |   2 | two        | Group1  |\n|  6 | A   |   3 | one        | Group2  |\n|  7 | B   |   0 | one        | Group2  |\n|  8 | C   |   7 | one        | Group2  |\n|  9 | A   |   6 | two        | Group2  |\n| 10 | B   |   2 | two        | Group2  |\n| 11 | C   |   1 | two        | Group2  |\n| 12 | D   |   8 | two        | Group2  |\n| 13 | D   |   5 | three      | Group3  |


One can plot this, with defined colors and automatic creating of total and subtotal by sing following code: 


    colors = {
        "one": {"one": "red", "two": "blue"},
        "two": {"one": "salmon", "two": "lightskyblue"},
        "three": "green"
    }


    c = Waterfall(df, x="X", y="Y", category="category", colors=colors, group="group", total=True, subtotals={"C": "Subtotal"})
    fig = c.get_fig()
    fig



produces

![Example](example.png)


## Disclaimer

I might maintain and improve the package. I might also not.

Known open points: 
- It is not possible to have mixed signs per X-value.
- I am note really happy with the interface for defining the colors.

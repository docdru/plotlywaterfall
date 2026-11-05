"""The example shown in the README.

CI renders ``fig`` to the image used in the README (see scripts/build_docs.py), so keep this
file and the README code block in sync.
"""

import pandas as pd

from plotlywaterfall import Waterfall

df = pd.DataFrame(
    {
        "X": ["A", "B", "C"] * 4 + ["D", "D"],
        "Y": [4, 1, 8, 7, 3, 2] + [i - 1 for i in [4, 1, 8, 7, 3, 2]] + [8, 5],
        "category": ["one"] * 3 + ["two"] * 3 + ["one"] * 3 + ["two"] * 3 + ["two", "three"],
        "group": ["Group1"] * 6 + ["Group2"] * 6 + ["Group2", "Group3"],
    }
)

fig = Waterfall(
    df,
    x="X",
    y="Y",
    category="category",
    group="group",
    total=True,
    subtotals={"C": "Subtotal"},
    color_discrete_map={"one": "#2a78d6", "two": "#eb6834", "three": "#1baf7a"},
    pattern_shape="group",
).get_fig()
fig.update_layout(template="plotly_white")

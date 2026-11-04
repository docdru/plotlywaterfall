from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go

DEFAULT_CONNECTOR_LINE: dict[str, Any] = {"color": "darkgrey", "width": 0.75}
TOTAL_TYPES = ("category", "sumtotal")


class Waterfall:
    def __init__(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        group: str | None = None,
        category: str | None = None,
        barwidth: float = 0.3,
        gap: float = 0.01,
        connector_line: dict | None = None,
        colors: dict | None = None,
        total: bool = False,
        total_type: str = "category",
        total_column_name: str = "Total",
        subtotals: dict | None = None,
    ):
        """Instanciate Waterfall object. All configuration is done by handing the correct kwargs.

        Args:
            df (pd.DataFrame): Pandas Dataframe containing all data in correct format.
            x (str): Column containing x-values/labels
            y (str): Column containing y-values
            group (str | None, optional): If not None: column containing group labels. Defaults to None.
            category (str | None, optional): If not None: column containing category labels. Defaults to None.
            barwidth (float, optional): Width of bars, should be 0.0 to 1.0. Defaults to 0.3.
            gap (float, optional): Gap between bars of different groups. Defaults to 0.01.
            connector_line (dict, optional): Parameters defining line style for lines connecting bars. Defaults to None, which means dict(color="darkgrey", width=.75).
            colors (dict | None, optional): dict identifying colors, compare documentation / example. Groups or categories missing from the dict get plotly's default colors. Defaults to None, which uses default colors.
            total (bool, optional): If True, calculates the total and adds it as last x-value. Defaults to False.
            total_type (str, optional): How to calculate the total. Can be "category" or "sumtotal". Defaults to "category".
            total_column_name (str, optional): Label of the x-value for total . Defaults to "Total".
            subtotals (dict | None, optional): dict with subtotals which should be added in format {"where": "label_name"}. Defaults to None.

        Raises:
            TypeError: If df is not a DataFrame or subtotals is not a dict.
            ValueError: If a column does not exist, y contains missing values, total_type is
                unknown or a subtotal refers to an x-value that is not in the data.
            NotImplementedError: If values of different signs share one bar.
        """

        if not isinstance(df, pd.DataFrame):
            raise TypeError("Expected df to be of type DataFrame")
        self._df = df
        self._x = x
        self._y = y
        self._group = group
        self._category = category
        self._barwidth = barwidth
        self._gap = gap
        self._connector_line = dict(
            DEFAULT_CONNECTOR_LINE if connector_line is None else connector_line
        )
        self._colors = colors
        self._total_column_name = total_column_name
        self._test_df()
        if subtotals is None:
            subtotals = {}
        elif not isinstance(subtotals, dict):
            raise TypeError("subtotals should be of type dict")
        # Copy, so that adding the total or further subtotals never changes the caller's dict
        self._subtotals: dict = {}
        for where, name in subtotals.items():
            self.add_subtotal(where, name)
        if total_type not in TOTAL_TYPES:
            raise ValueError(f"total_type must be one of {TOTAL_TYPES}, got {total_type!r}")
        self._total = total
        self._total_type = total_type
        if total and (total_type == "category"):
            self._subtotals[self._df[self._x].unique()[-1]] = total_column_name

    def get_fig(self) -> go.Figure:
        """Creates Plotly Figure instance

        Raises:
            NotImplementedError: Certain features, such as mixed signs per x value are not (yet) supported

        Returns:
            Figure: Configured plotly.graph_objects.Figure instance
        """

        # tdf = self._get_df_merged_w_color()
        tdf = self._df.copy()
        X = self._get_x_values(tdf)

        fig = go.Figure()

        if self._group is None:
            self.__totalgroups = 1
            self._add_group(fig, X, 0, None, tdf)
        else:
            self.__totalgroups = len(tdf[self._group].unique())
            for groupno, (groupname, group) in enumerate(tdf.groupby(self._group, sort=False)):
                self._add_group(fig, X, groupno, groupname, group)

        if self._total and (self._total_type == "sumtotal"):
            self._add_sumtotal(fig, X, tdf)
            X = pd.concat(
                [X, pd.DataFrame({self._x: X[self._x].max() + 1}, index=[self._total_column_name])]
            )

        fig.update_layout(xaxis={"tickmode": "array", "tickvals": X[self._x], "ticktext": X.index})
        return fig

    def _test_df(self) -> None:
        for argument in ("x", "y", "group", "category"):
            column = getattr(self, f"_{argument}")
            if column is not None and column not in self._df.columns:
                raise ValueError(
                    f"{argument}={column!r} is not a column of df. "
                    f"Available columns: {list(self._df.columns)}"
                )
        missing = self._df[self._y].isna()
        if missing.any():
            raise ValueError(
                f"Column {self._y!r} contains missing values (NaN) in rows "
                f"{list(self._df.index[missing])}; drop or fill them first"
            )
        gb = self._x if self._group is None else [self._group, self._x]
        for _, g in self._df.groupby(gb, observed=True):
            if not (np.all(g[self._y] >= 0) | np.all(g[self._y] <= 0)):
                raise NotImplementedError(
                    "Currently mixed signed categorization is not supported (yet)"
                )

    def add_subtotal(self, x: Any, name: str) -> None:
        """Add a subtotal bar labelled `name` directly after the x-value `x`.

        Raises:
            ValueError: If `x` is not an x-value of the data.
        """
        if x not in self._df[self._x].unique():
            raise ValueError(f"Cannot find value {x!r} in data column {self._x!r}")
        self._subtotals[x] = name

    def _offset(self, groupno: int) -> float:
        """Horizontal offset of the left edge of group `groupno`'s bars from the x-value."""
        step = self._barwidth + self._gap / 2
        return -step * self.__totalgroups / 2 + step * groupno

    def _color(self, groupname: Any, categoryname: Any) -> Any:
        """Look up the color for a group/category; None means plotly's default color."""
        color = self._colors
        if isinstance(color, dict) and groupname in color:
            color = color[groupname]
        if isinstance(color, dict) and categoryname in color:
            color = color[categoryname]
        return None if isinstance(color, dict) else color

    @staticmethod
    def _check_total_signs(traces) -> None:
        """Stacked bars of one group must share a sign at every x (relevant for totals)."""
        for values in zip(*[trace["y"] for trace in traces], strict=True):
            ia = np.array(values, dtype=float)
            if not (np.all((ia >= 0) | np.isnan(ia)) | np.all((ia <= 0) | np.isnan(ia))):
                raise NotImplementedError(
                    "Currently mixed signed categories in totals are not supported (yet)"
                )

    def _get_x_values(self, tdf):
        # Define x axis and include subtotals and totals
        labels = list(tdf[self._x].unique())
        mt = [False] * len(labels)
        for total in self._subtotals:
            pos = labels.index(total) + 1
            labels.insert(pos, self._subtotals[total])
            mt.insert(pos, True)
        X = (
            pd.DataFrame({"label": labels, "makeTotal": mt})
            .reset_index()
            .set_index("label")
            .rename({"index": self._x}, axis=1)
        )
        return X

    def _add_group(self, fig, X, groupno, groupname, group):
        b = group.groupby([self._x], sort=False)[self._y].sum().cumsum().shift(1).fillna(0)
        b = X.merge(pd.DataFrame(b), left_index=True, right_index=True, how="left")[self._y].fillna(
            0
        )
        first_trace = len(fig.data)
        if self._category is None:
            b = self._add_bar(fig, X, b, None, group, groupno, groupname)
        else:
            for categoryname, category in group.groupby(self._category, sort=False, observed=True):
                b = self._add_bar(fig, X, b, categoryname, category, groupno, groupname)
        self._check_total_signs(fig.data[first_trace:])
        self._add_lines(fig, X, group, groupno)

    def _add_bar(self, fig, X, b, categoryname, category, groupno, groupname):
        values = category.groupby([self._x])[self._y].sum()
        x = X[self._x]
        y = X.merge(pd.DataFrame(values), left_index=True, right_index=True, how="left")[self._y]
        y = y.fillna(0).cumsum().where(X.makeTotal, y)

        if categoryname is None:
            name = groupname
            groupnametitle = None
        else:
            name = categoryname
            groupnametitle = groupname

        fig.add_bar(
            x=x,
            y=y,
            base=b,
            offsetgroup=groupno,
            name=name,
            marker_color=self._color(groupname, categoryname),
            legendgroup=groupname,
            legendgrouptitle_text=groupnametitle,
            width=self._barwidth,
            offset=self._offset(groupno),
        )
        return b + y.fillna(0)

    def _add_lines(self, fig, X, group, groupno):
        x = X[self._x]
        ys = group.groupby([self._x], sort=False)[self._y].sum()
        ys = (
            X.merge(pd.DataFrame(ys), left_index=True, right_index=True, how="left")[self._y]
            .fillna(0)
            .cumsum()
            .ffill()
        )
        x0s = x[0:-1] + self._offset(groupno)
        x1s = x[1:] + self._offset(groupno) + self._barwidth
        # x0s/x1s have one element less than ys; the last y is intentionally dropped
        for x0, x1, y in zip(x0s, x1s, ys, strict=False):
            if not np.isnan(y):
                fig.add_shape(x0=x0, x1=x1, y0=y, y1=y, line=self._connector_line)

    def _add_sumtotal(self, fig, X, tdf):
        x = X[self._x].max()
        if self._group is None:
            y = tdf[self._y].sum()
            self._add_total_bar_line(fig, x, y, 0, None)
        else:
            for groupno, (groupname, group) in enumerate(tdf.groupby(self._group, sort=False)):
                y = group[self._y].sum()
                self._add_total_bar_line(fig, x, y, groupno, groupname)

    def _add_total_bar_line(self, fig, x, y, groupno, groupname):
        categoryname = self._total_column_name
        fig.add_bar(
            x=[x + 1],
            y=[y],
            offsetgroup=groupno,
            name=categoryname,
            marker_color=self._color(groupname, categoryname),
            legendgroup=groupname,
            legendgrouptitle_text=groupname,
            width=self._barwidth,
            offset=self._offset(groupno),
        )

        x0 = x + self._offset(groupno)
        x1 = x + 1 + self._offset(groupno) + self._barwidth
        fig.add_shape(x0=x0, x1=x1, y0=y, y1=y, line=self._connector_line)

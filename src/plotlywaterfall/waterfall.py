from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from plotlywaterfall._coloring import Coloring

DEFAULT_CONNECTOR_LINE: dict[str, Any] = {"color": "darkgrey", "width": 0.75}
TOTAL_TYPES = ("category", "sumtotal")
MIXED_SIGNS = ("steps", "error")
STEP_ORDERS = ("data", "positive_first", "largest_first")
DEFAULT_NET_GHOST: dict[str, Any] = {
    "color": "rgba(136, 135, 128, 0.25)",
    "line": {"color": "rgb(136, 135, 128)", "width": 0.75},
}
# Share of a sub-step's slot that is filled by its bar; the rest is a small visual gap
SUBSTEP_FILL = 0.9


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
        mixed_signs: str = "steps",
        net_ghost: bool | dict = True,
        step_order: str = "data",
        color: str | None = None,
        color_discrete_map: dict | None = None,
        color_discrete_sequence: list[str] | None = None,
        pattern_shape: str | None = None,
        pattern_shape_map: dict | None = None,
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
            colors (dict | None, optional): Deprecated, will be removed in 1.0; use `color` and
                `color_discrete_map`. dict identifying colors per group, per group and category,
                or per category. Defaults to None.
            total (bool, optional): If True, calculates the total and adds it as last x-value. Defaults to False.
            total_type (str, optional): How to calculate the total. Can be "category" or "sumtotal". Defaults to "category".
            total_column_name (str, optional): Label of the x-value for total . Defaults to "Total".
            subtotals (dict | None, optional): dict with subtotals which should be added in format {"where": "label_name"}. Defaults to None.
            mixed_signs (str, optional): What to do when the categories of one bar have
                different signs (e.g. +1 and -4 at the same x, or in a total). "steps" splits
                the bar into one narrow sub-step per category that walks from the bar's start
                level to its end level. "error" raises NotImplementedError (behaviour before
                0.10). Bars whose categories share a sign are drawn as stacked bars either way.
                Defaults to "steps".
            net_ghost (bool | dict, optional): For bars split into sub-steps: draw a light bar
                behind them spanning the net change of the step. A dict is used as plotly
                marker properties of that bar. Defaults to True.
            step_order (str, optional): Order of the sub-steps within a split bar: "data"
                (order of the categories in df), "positive_first" or "largest_first" (by
                absolute value). Defaults to "data".
            color (str | None, optional): What drives the bar colours: the group column, the
                category column or "direction" (increase / decrease / total). Defaults to the
                category column, else the group column, else "direction".
            color_discrete_map (dict | None, optional): Colour per value of the `color`
                dimension, e.g. {"Product A": "red"}. Keys may also be (group, category) tuples
                to colour one group's category. With color="direction" the keys are
                "increase", "decrease" and "total". Values not in the map get colours from
                `color_discrete_sequence`; keys matching no value raise a warning.
            color_discrete_sequence (list[str] | None, optional): Colours assigned in order
                to values missing from `color_discrete_map`. Defaults to the colorway of the
                active plotly template.
            pattern_shape (str | None, optional): The group or category column, to give its
                values different fill patterns (e.g. colour by category, pattern by group).
                Defaults to None (no patterns).
            pattern_shape_map (dict | None, optional): Pattern per value of `pattern_shape`,
                e.g. {"Actual": "/"}; plotly shapes are "", "/", "\\", "x", "-", "|", "+"
                and ".". Defaults to None (assigned in that order).

        Raises:
            TypeError: If df is not a DataFrame or subtotals is not a dict.
            ValueError: If a column does not exist, y contains missing values, an option has an
                unknown value or a subtotal refers to an x-value that is not in the data.
            NotImplementedError: If mixed_signs="error" and values of different signs share
                one bar.
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
        self._total_column_name = total_column_name
        if mixed_signs not in MIXED_SIGNS:
            raise ValueError(f"mixed_signs must be one of {MIXED_SIGNS}, got {mixed_signs!r}")
        if step_order not in STEP_ORDERS:
            raise ValueError(f"step_order must be one of {STEP_ORDERS}, got {step_order!r}")
        self._mixed_signs = mixed_signs
        self._step_order = step_order
        if net_ghost is True:
            self._net_ghost: dict | None = dict(DEFAULT_NET_GHOST)
        elif isinstance(net_ghost, dict):
            self._net_ghost = dict(net_ghost)
        elif net_ghost is False or net_ghost is None:
            self._net_ghost = None
        else:
            raise TypeError("net_ghost should be a bool or a dict of marker properties")
        self._test_df()
        self._coloring = Coloring(
            df,
            group=group,
            category=category,
            color=color,
            color_discrete_map=color_discrete_map,
            color_discrete_sequence=color_discrete_sequence,
            pattern_shape=pattern_shape,
            pattern_shape_map=pattern_shape_map,
            legacy_colors=colors,
            total_name=total_column_name,
        )
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

        tdf = self._df.copy()
        X = self._get_x_values(tdf)
        self._coloring.resolve()
        self._used_directions: set[str] = set()

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

        for legend_entry in self._coloring.direction_legend(self._used_directions):
            fig.add_bar(**legend_entry)

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
        if self._mixed_signs != "error":
            return
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
        level = group.groupby([self._x], sort=False)[self._y].sum().cumsum().shift(1).fillna(0)
        level = X.merge(pd.DataFrame(level), left_index=True, right_index=True, how="left")[
            self._y
        ].fillna(0)

        if self._category is None:
            categories = [(None, group)]
        else:
            categories = list(group.groupby(self._category, sort=False, observed=True))
        # values[p, c]: height of category c's segment at x-position p (NaN = no segment)
        values = np.column_stack([self._category_values(X, category) for _, category in categories])
        level_values = level.to_numpy(dtype=float)
        bases, offsets, widths, mixed = self._layout_segments(values, level_values, groupno)

        if mixed.any() and self._net_ghost is not None:
            self._add_net_ghost(fig, X, level_values, values, mixed, groupno, groupname)

        x = X[self._x]
        is_total = X.makeTotal.to_numpy(dtype=bool)
        for c, (categoryname, _) in enumerate(categories):
            if categoryname is None:
                name = groupname
                groupnametitle = None
            else:
                name = categoryname
                groupnametitle = groupname
            fig.add_bar(
                x=x,
                y=values[:, c],
                base=bases[:, c],
                offsetgroup=groupno,
                name=name,
                marker=self._coloring.marker(groupname, categoryname, values[:, c], is_total),
                **self._legend_kwargs(),
                legendgroup=groupname,
                legendgrouptitle_text=groupnametitle,
                # Arrays only where a bar is split into sub-steps, so that ordinary charts
                # keep producing exactly the same figure as before
                width=widths[:, c] if mixed.any() else self._barwidth,
                offset=offsets[:, c] if mixed.any() else self._offset(groupno),
            )
        self._track_directions(values, is_total)
        self._add_lines(fig, X, group, groupno)

    def _legend_kwargs(self) -> dict:
        # Only set showlegend when hiding, so that figures stay identical to earlier versions
        return {} if self._coloring.show_trace_legend else {"showlegend": False}

    def _track_directions(self, values, is_total) -> None:
        """Remember which of increase / decrease / total occur, for the direction legend."""
        present = ~np.isnan(values)
        if (present & is_total[:, None]).any():
            self._used_directions.add("total")
        steps = values[present & ~is_total[:, None]]
        if (steps >= 0).any():
            self._used_directions.add("increase")
        if (steps < 0).any():
            self._used_directions.add("decrease")

    def _category_values(self, X, category) -> np.ndarray:
        """Segment heights of one category per x-position; totals hold the running sum."""
        values = category.groupby([self._x])[self._y].sum()
        y = X.merge(pd.DataFrame(values), left_index=True, right_index=True, how="left")[self._y]
        return y.fillna(0).cumsum().where(X.makeTotal, y).to_numpy(dtype=float)

    def _layout_segments(self, values, level, groupno):
        """Compute base, offset and width of every segment of one group.

        Bars whose segments share a sign are stacked in category order. Bars with mixed
        signs are split into narrow sub-steps, each starting where the previous one ended.
        """
        n_positions = values.shape[0]
        filled = np.nan_to_num(values)
        # Stacked layout (also used for the invisible base of missing segments)
        bases = level[:, None] + np.cumsum(filled, axis=1) - filled
        offsets = np.full(values.shape, self._offset(groupno))
        widths = np.full(values.shape, float(self._barwidth))
        mixed = np.zeros(n_positions, dtype=bool)

        for p in range(n_positions):
            row = values[p]
            present = np.flatnonzero(~np.isnan(row))
            if not ((row[present] > 0).any() and (row[present] < 0).any()):
                continue
            if self._mixed_signs == "error":
                raise NotImplementedError(
                    "Currently mixed signed categories in totals are not supported (yet)"
                )
            mixed[p] = True
            order = self._order_steps(present, row)
            slot = self._barwidth / len(order)
            running = level[p]
            for k, c in enumerate(order):
                bases[p, c] = running
                running += row[c]
                widths[p, c] = slot * SUBSTEP_FILL
                offsets[p, c] = self._offset(groupno) + k * slot + slot * (1 - SUBSTEP_FILL) / 2
        return bases, offsets, widths, mixed

    def _order_steps(self, present, row) -> list[int]:
        """Order of the sub-steps (category indices) within one split bar."""
        indices = list(present)
        if self._step_order == "positive_first":
            return [c for c in indices if row[c] > 0] + [c for c in indices if row[c] <= 0]
        if self._step_order == "largest_first":
            return sorted(indices, key=lambda c: -abs(row[c]))
        return indices

    def _add_net_ghost(self, fig, X, level, values, mixed, groupno, groupname):
        """Light bar behind the sub-steps of split bars, spanning the net change."""
        fig.add_bar(
            x=X[self._x].to_numpy()[mixed],
            y=np.nansum(values, axis=1)[mixed],
            base=level[mixed],
            offsetgroup=groupno,
            name="Net change",
            marker=self._net_ghost,
            legendgroup=groupname,
            showlegend=False,
            hovertemplate="Net change: %{y}<extra></extra>",
            width=self._barwidth,
            offset=self._offset(groupno),
        )

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
            marker=self._coloring.total_marker(groupname, categoryname),
            **self._legend_kwargs(),
            legendgroup=groupname,
            legendgrouptitle_text=groupname,
            width=self._barwidth,
            offset=self._offset(groupno),
        )

        self._used_directions.add("total")
        x0 = x + self._offset(groupno)
        x1 = x + 1 + self._offset(groupno) + self._barwidth
        fig.add_shape(x0=x0, x1=x1, y0=y, y1=y, line=self._connector_line)

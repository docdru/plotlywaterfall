import datetime
from collections.abc import Callable
from typing import Any, Literal, get_args

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from plotlywaterfall._coloring import Coloring
from plotlywaterfall._format import (
    NUMBER_UNITS,
    NegativeStyle,
    NumberFormat,
    NumberFormatter,
    NumberUnit,
    auto_unit,
)

DEFAULT_CONNECTOR_LINE: dict[str, Any] = {"color": "darkgrey", "width": 0.75}
TotalType = Literal["category", "sumtotal"]
MixedSigns = Literal["steps", "error"]
StepOrder = Literal["data", "positive_first", "largest_first"]
ValueLabels = Literal["bar", "segment", "both"]
TOTAL_TYPES: tuple[str, ...] = get_args(TotalType)
MIXED_SIGNS: tuple[str, ...] = get_args(MixedSigns)
STEP_ORDERS: tuple[str, ...] = get_args(StepOrder)
DEFAULT_NET_GHOST: dict[str, Any] = {
    "color": "rgba(136, 135, 128, 0.25)",
    "line": {"color": "rgb(136, 135, 128)", "width": 0.75},
}
# Share of a sub-step's slot that is filled by its bar; the rest is a small visual gap
SUBSTEP_FILL = 0.9
# helper column with each row's position in the original DataFrame (order of appearance)
ROW = "__plotlywaterfall_row__"
VALUE_LABELS: tuple[str, ...] = get_args(ValueLabels)


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
        total: bool = False,
        total_type: TotalType = "category",
        total_column_name: str = "Total",
        subtotals: dict | None = None,
        mixed_signs: MixedSigns = "steps",
        net_ghost: bool | dict = True,
        step_order: StepOrder = "data",
        color: str | None = None,
        color_discrete_map: dict | None = None,
        color_discrete_sequence: list[str] | None = None,
        pattern_shape: str | None = None,
        pattern_shape_map: dict | None = None,
        value_labels: ValueLabels | Literal[False] | None = "bar",
        number_format: NumberFormat = None,
        number_prefix: str = "",
        number_suffix: str = "",
        number_unit: NumberUnit | None = None,
        negative_style: NegativeStyle = "minus",
        title: str | None = None,
        labels: dict | None = None,
        category_orders: dict[str, list] | None = None,
        x_format: str | Callable[[Any], str] | None = None,
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
            total (bool, optional): If True, calculates the total and adds it as last x-value. Defaults to False.
            total_type (str, optional): How to calculate the total. Can be "category" or "sumtotal". Defaults to "category".
            total_column_name (str, optional): Label of the x-value for total . Defaults to "Total".
            subtotals (dict | None, optional): dict with subtotals which should be added in format {"where": "label_name"}. Defaults to None.
            mixed_signs (str, optional): What to do when the categories of one bar have
                different signs (e.g. +1 and -4 at the same x, or in a total). "steps" splits
                the bar into one narrow sub-step per category that walks from the bar's start
                level to its end level. "error" raises NotImplementedError (behaviour before
                1.0). Bars whose categories share a sign are drawn as stacked bars either way.
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
            value_labels (str | None, optional): Value labels on the bars. "bar": one label
                per bar with its change (signed, e.g. "+9") or, for totals, its value, placed
                above or below the bar. "segment": the value inside every stacked segment
                (hidden where it does not fit), "both", or None / False for no labels.
                Defaults to "bar".
            number_format (str | callable | None, optional): Format of numbers in labels and
                hover texts: a Python format spec for the absolute value (e.g. ",.1f"), or a
                callable taking the absolute value and returning text. Defaults to None:
                thousands separators and up to two decimals (1,234.5).
            number_prefix (str, optional): Text before numbers, after the sign, e.g. "$"
                gives "-$5". Defaults to "".
            number_suffix (str, optional): Text after numbers, e.g. " M€". Defaults to "".
            number_unit (str | None, optional): Show numbers in thousands ("k"), millions
                ("M") or billions ("bn"), e.g. 12500000 as "12.5M"; "auto" picks one unit for
                the whole chart from its largest value. The unit is written after the number,
                before number_suffix. Defaults to None (no scaling).
            negative_style (str, optional): "minus" ("-7", changes signed "+9") or
                "parentheses" (accounting style: "(7)", changes unsigned). Defaults to "minus".
            title (str | None, optional): Figure title. Defaults to None.
            labels (dict | None, optional): Display names for columns, as in plotly express,
                e.g. {"Y": "Cashflow [MUSD]"}. Used for the axis titles. The y-axis is titled
                with the (renamed) y column; the x-axis only gets a title if x is in labels.
                Defaults to None.
            category_orders (dict | None, optional): Order of the values of the x, group or
                category column, as in plotly express, e.g. {"X": ["Revenue", "Costs"]}.
                Listed values come first, others follow in order of appearance. Without it,
                the order of a pandas Categorical column is used, else the order of
                appearance. Defaults to None.
            x_format (str | callable | None, optional): Labels of the x-values: a strftime
                pattern for dates (e.g. "%b %Y"), or a callable taking an x-value and returning
                its label. Defaults to None: dates are shown as "Jan 2026" when they are in
                different months, else as "2026-01-31"; other values as str(value).

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
        if value_labels is False:
            value_labels = None
        if value_labels is not None and value_labels not in VALUE_LABELS:
            raise ValueError(
                f"value_labels must be one of {VALUE_LABELS}, None or False, got {value_labels!r}"
            )
        self._value_labels: str | None = value_labels
        self._title = title
        self._labels = dict(labels or {})
        if number_unit is not None and number_unit not in NUMBER_UNITS:
            raise ValueError(
                f"number_unit must be one of {NUMBER_UNITS} or None, got {number_unit!r}"
            )
        self._number_unit = number_unit
        self._fmt = NumberFormatter(
            number_format,
            number_prefix,
            number_suffix,
            negative_style=negative_style,
            unit=None if number_unit == "auto" else number_unit,
        )
        self._test_df()
        self._category_orders = dict(category_orders or {})
        dimensions = [c for c in (x, group, category) if c is not None]
        unknown = [c for c in self._category_orders if c not in dimensions]
        if unknown:
            raise ValueError(
                f"category_orders keys must be the x, group or category column; got {unknown}"
            )
        self._x_values = self._ordered_values(x)
        self._x_label = self._x_labeller(x_format)
        self._coloring = Coloring(
            df,
            group=group,
            category=category,
            color=color,
            color_discrete_map=color_discrete_map,
            color_discrete_sequence=color_discrete_sequence,
            pattern_shape=pattern_shape,
            pattern_shape_map=pattern_shape_map,
            total_name=total_column_name,
            orders={c: self._ordered_values(c) for c in (group, category) if c is not None},
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
            self._subtotals[self._x_values[-1]] = total_column_name

    def get_fig(self) -> go.Figure:
        """Creates Plotly Figure instance

        Raises:
            NotImplementedError: Certain features, such as mixed signs per x value are not (yet) supported

        Returns:
            Figure: Configured plotly.graph_objects.Figure instance
        """

        # rows in x-axis order (stable), so that running levels follow the axis in every group
        position = {value: i for i, value in enumerate(self._x_values)}
        tdf = self._df.assign(**{ROW: np.arange(len(self._df))})
        tdf = tdf.iloc[np.argsort(tdf[self._x].map(position).to_numpy(), kind="stable")]
        X = self._get_x_values(tdf)
        if self._number_unit == "auto":
            self._fmt.unit = auto_unit(self._chart_values(tdf))
        self._coloring.resolve()
        self._used_directions: set[str] = set()
        self._label_ys: dict[str, list[float]] = {"above": [], "below": []}

        fig = go.Figure()

        if self._group is None:
            self.__totalgroups = 1
            self._add_group(fig, X, 0, None, tdf)
        else:
            groups = self._groups(tdf)
            self.__totalgroups = len(groups)
            for groupno, (groupname, group) in enumerate(groups):
                self._add_group(fig, X, groupno, groupname, group)

        if self._total and (self._total_type == "sumtotal"):
            self._add_sumtotal(fig, X, tdf)
            X = pd.concat(
                [X, pd.DataFrame({self._x: X[self._x].max() + 1}, index=[self._total_column_name])]
            )

        for legend_entry in self._coloring.direction_legend(self._used_directions):
            fig.add_bar(**legend_entry)

        fig.update_layout(
            xaxis={
                "tickmode": "array",
                "tickvals": X[self._x],
                "ticktext": [
                    self._label(value, bool(total))
                    for value, total in zip(X.index, X.makeTotal.fillna(True), strict=True)
                ],
            },
            yaxis_title_text=self._labels.get(self._y, self._y),
        )
        if self._x in self._labels:
            fig.update_layout(xaxis_title_text=self._labels[self._x])
        if self._title is not None:
            fig.update_layout(title_text=self._title)
        self._make_room_for_labels(fig)
        if self._value_labels in ("segment", "both"):
            # segment labels that do not fit inside their bar are hidden instead of shrunk
            fig.update_layout(uniformtext_minsize=9, uniformtext_mode="hide")
        return fig

    def _groups(self, tdf: pd.DataFrame) -> list[tuple[Any, pd.DataFrame]]:
        """(group name, rows) pairs in display order."""
        assert self._group is not None
        return [(name, tdf[tdf[self._group] == name]) for name in self._ordered_values(self._group)]

    def _chart_values(self, tdf: pd.DataFrame) -> list[float]:
        """Bar values and running levels, to choose number_unit="auto"."""
        frames = [g for _, g in self._groups(tdf)] if self._group is not None else [tdf]
        values: list[float] = []
        for frame in frames:
            sums = frame.groupby(self._x, sort=False, observed=True)[self._y].sum()
            values += [*sums.abs(), *sums.cumsum().abs()]
        return values

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
        if x not in self._x_values:
            raise ValueError(f"Cannot find value {x!r} in data column {self._x!r}")
        self._subtotals[x] = name

    def _ordered_values(self, column: str) -> list:
        """Values of a column in display order: category_orders first, then a Categorical's
        order, else the order of appearance."""
        series = self._df[column]
        values = list(series.unique())
        if column in self._category_orders:
            present = set(values)
            given = [v for v in self._category_orders[column] if v in present]
            listed = set(given)
            return given + [v for v in values if v not in listed]
        if isinstance(series.dtype, pd.CategoricalDtype):
            present = set(values)
            return [v for v in series.cat.categories if v in present]
        return values

    def _x_labeller(self, x_format: str | Callable[[Any], str] | None) -> Callable[[Any], str]:
        """Function that turns an x-value into its axis / hover label."""
        if callable(x_format):
            return x_format
        dates = [v for v in self._x_values if isinstance(v, (datetime.date, np.datetime64))]
        if x_format is not None:
            if len(dates) != len(self._x_values):
                raise ValueError(
                    "x_format as a string is a strftime pattern for date x-values; "
                    "use a callable for other values"
                )
            pattern = x_format
        elif dates and len(dates) == len(self._x_values):
            stamps = pd.to_datetime(pd.Series(dates))
            if (stamps != stamps.dt.normalize()).any():
                pattern = "%Y-%m-%d %H:%M"
            elif stamps.dt.to_period("M").nunique() == len(stamps):
                pattern = "%b %Y"
            else:
                pattern = "%Y-%m-%d"
        else:
            return str
        return lambda value: pd.Timestamp(value).strftime(pattern)

    def _label(self, value: Any, is_total: bool) -> str:
        """Label of an x-axis position; totals and subtotals carry their name."""
        return str(value) if is_total else self._x_label(value)

    def _offset(self, groupno: int) -> float:
        """Horizontal offset of the left edge of group `groupno`'s bars from the x-value."""
        step = self._barwidth + self._gap / 2
        return -step * self.__totalgroups / 2 + step * groupno

    def _get_x_values(self, tdf: pd.DataFrame) -> pd.DataFrame:
        # Define x axis and include subtotals and totals
        labels = list(self._x_values)
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

    def _add_group(
        self, fig: go.Figure, X: pd.DataFrame, groupno: int, groupname: Any, group: pd.DataFrame
    ) -> None:
        # running level before each x-position, in x-axis order; totals start at 0
        sums = group.groupby([self._x], sort=False)[self._y].sum()
        steps = X.merge(pd.DataFrame(sums), left_index=True, right_index=True, how="left")[self._y]
        # (positions without data of this group have no bar; their base stays 0 as before)
        level = steps.fillna(0).cumsum().shift(1).fillna(0).where(steps.notna(), 0)

        # (category name, rows) pairs; a single unnamed "category" without a category column
        categories: list[tuple[Any, pd.DataFrame]]
        categories = [(None, group)] if self._category is None else self._categories(group)
        # values[p, c]: height of category c's segment at x-position p (NaN = no segment)
        values = np.column_stack([self._category_values(X, category) for _, category in categories])
        level_values = level.to_numpy(dtype=float)
        bases, offsets, widths, mixed = self._layout_segments(values, level_values, groupno)

        if mixed.any() and self._net_ghost is not None:
            self._add_net_ghost(fig, X, level_values, values, mixed, groupno, groupname)

        x = X[self._x]
        is_total = X.makeTotal.to_numpy(dtype=bool)
        net = np.nansum(values, axis=1)
        level_after = np.where(is_total, net, level_values + net)
        n_segments = (~np.isnan(values)).sum(axis=1)
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
                **self._segment_texts(
                    X, values[:, c], categoryname, groupname, is_total, net, level_after, n_segments
                ),
            )
        if self._value_labels in ("bar", "both"):
            self._add_bar_labels(fig, X, values, bases, net, is_total, groupno)
        self._track_directions(values, is_total)
        self._add_lines(fig, X, group, groupno)

    def _segment_texts(
        self,
        X: pd.DataFrame,
        values: np.ndarray,
        categoryname: Any,
        groupname: Any,
        is_total: np.ndarray,
        net: np.ndarray,
        level_after: np.ndarray,
        n_segments: np.ndarray,
    ) -> dict:
        """Hover text (and segment labels) for one trace."""
        hover = []
        texts = []
        for p, label in enumerate(X.index):
            value = values[p]
            if np.isnan(value):
                hover.append(["", ""])
                texts.append("")
                continue
            total = bool(is_total[p])
            name = categoryname if categoryname is not None else ("Total" if total else "Change")
            lines = [f"{name}: {self._fmt(value, signed=not total)}"]
            if total and n_segments[p] > 1:
                lines.append(f"{self._label(label, total)}: {self._fmt(net[p])}")
            elif not total:
                if n_segments[p] > 1:
                    lines.append(f"Step: {self._fmt(net[p], signed=True)}")
                lines.append(f"Running total: {self._fmt(level_after[p])}")
            hover.append([self._label(label, total), "<br>".join(lines)])
            texts.append(self._fmt(value, signed=not total))
        extra = "" if groupname is None else str(groupname)
        kwargs: dict = {
            "customdata": hover,
            "hovertemplate": f"<b>%{{customdata[0]}}</b><br>%{{customdata[1]}}<extra>{extra}</extra>",
        }
        if self._value_labels in ("segment", "both"):
            kwargs.update(text=texts, textposition="inside", insidetextanchor="middle", textangle=0)
        return kwargs

    def _add_bar_labels(
        self,
        fig: go.Figure,
        X: pd.DataFrame,
        values: np.ndarray,
        bases: np.ndarray,
        net: np.ndarray,
        is_total: np.ndarray,
        groupno: int,
    ) -> None:
        """One label per bar: its signed change, or its value for totals, outside the bar."""
        present = ~np.isnan(values)
        ends = np.where(present, bases + np.nan_to_num(values), np.nan)
        starts = np.where(present, bases, np.nan)
        center = self._offset(groupno) + self._barwidth / 2
        for p, position in enumerate(X[self._x]):
            if not present[p].any():
                continue
            top = np.nanmax([np.nanmax(starts[p]), np.nanmax(ends[p])])
            bottom = np.nanmin([np.nanmin(starts[p]), np.nanmin(ends[p])])
            self._add_label(
                fig, position + center, net[p], top, bottom, signed=not bool(is_total[p])
            )

    def _add_label(
        self, fig: go.Figure, x: float, value: float, top: float, bottom: float, signed: bool
    ) -> None:
        above = value >= 0
        self._label_ys["above" if above else "below"].append(top if above else bottom)
        fig.add_annotation(
            x=x,
            y=top if above else bottom,
            text=self._fmt(value, signed=signed),
            showarrow=False,
            yanchor="bottom" if above else "top",
            yshift=2 if above else -2,
        )

    def _make_room_for_labels(self, fig: go.Figure) -> None:
        """Plotly's autorange ignores annotations: extend it so labels at the outermost bars
        are not clipped (the axis still autoscales, so later changes keep working)."""
        above, below = self._label_ys["above"], self._label_ys["below"]
        if not above and not below:
            return
        span = max([*above, *below, 0]) - min([*above, *below, 0]) or 1.0
        include = []
        if above:
            include.append(max(above) + 0.08 * span)
        if below:
            include.append(min(below) - 0.08 * span)
        fig.update_layout(yaxis_autorangeoptions_include=include)

    def _legend_kwargs(self) -> dict[str, Any]:
        # Only set showlegend when hiding, so that figures stay identical to earlier versions
        return {} if self._coloring.show_trace_legend else {"showlegend": False}

    def _track_directions(self, values: np.ndarray, is_total: np.ndarray) -> None:
        """Remember which of increase / decrease / total occur, for the direction legend."""
        present = ~np.isnan(values)
        if (present & is_total[:, None]).any():
            self._used_directions.add("total")
        steps = values[present & ~is_total[:, None]]
        if (steps >= 0).any():
            self._used_directions.add("increase")
        if (steps < 0).any():
            self._used_directions.add("decrease")

    def _categories(self, group: pd.DataFrame) -> list[tuple[Any, pd.DataFrame]]:
        """(category name, rows) pairs of one group in stacking order: category_orders or a
        Categorical's order if given, else the order of appearance in the original data."""
        assert self._category is not None
        column = self._category
        explicit = column in self._category_orders or isinstance(
            self._df[column].dtype, pd.CategoricalDtype
        )
        if explicit:
            names = [v for v in self._ordered_values(column) if (group[column] == v).any()]
        else:
            names = list(group.sort_values(ROW, kind="stable")[column].unique())
        return [(name, group[group[column] == name]) for name in names]

    def _category_values(self, X: pd.DataFrame, category: pd.DataFrame) -> np.ndarray:
        """Segment heights of one category per x-position; totals hold the running sum."""
        values = category.groupby([self._x])[self._y].sum()
        y = X.merge(pd.DataFrame(values), left_index=True, right_index=True, how="left")[self._y]
        return y.fillna(0).cumsum().where(X.makeTotal, y).to_numpy(dtype=float)

    def _layout_segments(
        self, values: np.ndarray, level: np.ndarray, groupno: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
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

    def _order_steps(self, present: np.ndarray, row: np.ndarray) -> list[int]:
        """Order of the sub-steps (category indices) within one split bar."""
        indices = list(present)
        if self._step_order == "positive_first":
            return [c for c in indices if row[c] > 0] + [c for c in indices if row[c] <= 0]
        if self._step_order == "largest_first":
            return sorted(indices, key=lambda c: -abs(row[c]))
        return indices

    def _add_net_ghost(
        self,
        fig: go.Figure,
        X: pd.DataFrame,
        level: np.ndarray,
        values: np.ndarray,
        mixed: np.ndarray,
        groupno: int,
        groupname: Any,
    ) -> None:
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
            customdata=[self._fmt(v, signed=True) for v in np.nansum(values, axis=1)[mixed]],
            hovertemplate="Net change: %{customdata}<extra></extra>",
            width=self._barwidth,
            offset=self._offset(groupno),
        )

    def _add_lines(
        self, fig: go.Figure, X: pd.DataFrame, group: pd.DataFrame, groupno: int
    ) -> None:
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

    def _add_sumtotal(self, fig: go.Figure, X: pd.DataFrame, tdf: pd.DataFrame) -> None:
        x = X[self._x].max()
        if self._group is None:
            y = tdf[self._y].sum()
            self._add_total_bar_line(fig, x, y, 0, None)
        else:
            for groupno, (groupname, group) in enumerate(self._groups(tdf)):
                y = group[self._y].sum()
                self._add_total_bar_line(fig, x, y, groupno, groupname)

    def _add_total_bar_line(
        self, fig: go.Figure, x: float, y: float, groupno: int, groupname: Any
    ) -> None:
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
            customdata=[[categoryname, f"{categoryname}: {self._fmt(y)}"]],
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}"
            f"<extra>{'' if groupname is None else groupname}</extra>",
        )
        if self._value_labels in ("bar", "both"):
            center = x + 1 + self._offset(groupno) + self._barwidth / 2
            self._add_label(fig, center, y, max(y, 0), min(y, 0), signed=False)

        self._used_directions.add("total")
        x0 = x + self._offset(groupno)
        x1 = x + 1 + self._offset(groupno) + self._barwidth
        fig.add_shape(x0=x0, x1=x1, y0=y, y1=y, line=self._connector_line)


def waterfall(
    df: pd.DataFrame,
    x: str,
    y: str,
    *,
    group: str | None = None,
    category: str | None = None,
    total: bool = False,
    total_type: TotalType = "category",
    total_column_name: str = "Total",
    subtotals: dict | None = None,
    color: str | None = None,
    color_discrete_map: dict | None = None,
    color_discrete_sequence: list[str] | None = None,
    pattern_shape: str | None = None,
    pattern_shape_map: dict | None = None,
    value_labels: ValueLabels | Literal[False] | None = "bar",
    number_format: NumberFormat = None,
    number_prefix: str = "",
    number_suffix: str = "",
    number_unit: NumberUnit | None = None,
    negative_style: NegativeStyle = "minus",
    title: str | None = None,
    labels: dict | None = None,
    category_orders: dict[str, list] | None = None,
    x_format: str | Callable[[Any], str] | None = None,
    mixed_signs: MixedSigns = "steps",
    net_ghost: bool | dict = True,
    step_order: StepOrder = "data",
    barwidth: float = 0.3,
    gap: float = 0.01,
    connector_line: dict | None = None,
) -> go.Figure:
    """Create a waterfall chart in one call, like plotly express' ``px.bar``.

    ``waterfall(df, x="X", y="Y", ...)`` is the same as
    ``Waterfall(df, x="X", y="Y", ...).get_fig()``; all arguments are described in
    :class:`Waterfall`. Use the class to add subtotals step by step with ``add_subtotal``.

    Returns:
        go.Figure: the waterfall chart.
    """
    return Waterfall(
        df,
        x=x,
        y=y,
        group=group,
        category=category,
        total=total,
        total_type=total_type,
        total_column_name=total_column_name,
        subtotals=subtotals,
        color=color,
        color_discrete_map=color_discrete_map,
        color_discrete_sequence=color_discrete_sequence,
        pattern_shape=pattern_shape,
        pattern_shape_map=pattern_shape_map,
        value_labels=value_labels,
        number_format=number_format,
        number_prefix=number_prefix,
        number_suffix=number_suffix,
        number_unit=number_unit,
        negative_style=negative_style,
        title=title,
        labels=labels,
        category_orders=category_orders,
        x_format=x_format,
        mixed_signs=mixed_signs,
        net_ghost=net_ghost,
        step_order=step_order,
        barwidth=barwidth,
        gap=gap,
        connector_line=connector_line,
    ).get_fig()

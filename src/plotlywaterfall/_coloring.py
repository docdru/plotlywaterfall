"""Colour and pattern assignment for waterfall bars (plotly-express style)."""

import warnings
from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
import plotly.colors
import plotly.io as pio

DIRECTION = "direction"
DIRECTION_KINDS = ("increase", "decrease", "total")
DEFAULT_DIRECTION_COLORS: dict[str, str] = {
    "increase": "#2ca02c",
    "decrease": "#d62728",
    "total": "#7f7f7f",
}
DIRECTION_LEGEND_NAMES = {"increase": "Increase", "decrease": "Decrease", "total": "Total"}
DEFAULT_PATTERN_SHAPES = ("", "/", "\\", "x", "-", "|", "+", ".")


def _template_colorway() -> Sequence[str]:
    """Colours of the active plotly template, falling back to plotly's default palette."""
    try:
        colorway = pio.templates[pio.templates.default].layout.colorway
    except (KeyError, ValueError, AttributeError):
        colorway = None
    return colorway or plotly.colors.qualitative.Plotly


class Coloring:
    """Decides the marker (colour and pattern) of every bar of a waterfall chart.

    `color` names what drives the colour: the group column, the category column or
    "direction" (increase / decrease / total). Colours come from `color_discrete_map`
    (value -> colour, or (group, category) -> colour) and otherwise from
    `color_discrete_sequence`, assigned per value so that a category has the same colour
    in every group.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        group: str | None,
        category: str | None,
        color: str | None,
        color_discrete_map: dict | None,
        color_discrete_sequence: Sequence[str] | None,
        pattern_shape: str | None,
        pattern_shape_map: dict | None,
        total_name: str = "Total",
    ):
        self._group = group
        self._category = category
        self._total_name = total_name
        self._map = dict(color_discrete_map or {})
        self._sequence = list(color_discrete_sequence) if color_discrete_sequence else None
        self._pattern_map = dict(pattern_shape_map or {})

        dimensions = [c for c in (category, group) if c is not None]
        if color is None:
            color = dimensions[0] if dimensions else DIRECTION
        if color != DIRECTION and color not in dimensions:
            raise ValueError(
                f"color must be the group column, the category column or {DIRECTION!r}; "
                f"got {color!r} (group={group!r}, category={category!r})"
            )
        self.color = color

        if pattern_shape is not None and pattern_shape not in dimensions:
            raise ValueError(
                f"pattern_shape must be the group or the category column; got {pattern_shape!r}"
            )
        self.pattern_shape = pattern_shape

        self._color_values = [] if color == DIRECTION else list(df[color].unique())
        self._pattern_values = [] if pattern_shape is None else list(df[pattern_shape].unique())
        self._warn_unknown_keys(df)

    # ------------------------------------------------------------------ validation

    def _warn_unknown_keys(self, df: pd.DataFrame) -> None:
        if self.color == DIRECTION:
            known: set = set(DIRECTION_KINDS)
        else:
            # the sum-total bar (total_type="sumtotal") can be coloured by its name as well
            known = {*self._color_values, self._total_name}
            if self._group is not None and self._category is not None:
                pairs = df[[self._group, self._category]].drop_duplicates()
                known |= set(pairs.itertuples(index=False, name=None))
                known |= {(g, self._total_name) for g in df[self._group].unique()}
        unknown = [key for key in self._map if key not in known]
        if unknown:
            warnings.warn(
                f"color_discrete_map keys {unknown} match no value of the colour dimension "
                f"{self.color!r}; they are ignored",
                UserWarning,
                stacklevel=4,
            )
        unknown_patterns = [key for key in self._pattern_map if key not in self._pattern_values]
        if unknown_patterns:
            warnings.warn(
                f"pattern_shape_map keys {unknown_patterns} match no value of "
                f"{self.pattern_shape!r}; they are ignored",
                UserWarning,
                stacklevel=4,
            )

    # ------------------------------------------------------------------ lookups

    def resolve(self) -> None:
        """Assign colours and patterns to values (at figure time, to use the active template)."""
        sequence = self._sequence or list(_template_colorway())
        self._value_colors: dict = {}
        unmapped = [v for v in self._color_values if v not in self._map]
        for i, value in enumerate(unmapped):
            self._value_colors[value] = sequence[i % len(sequence)]
        self._value_colors.update({k: v for k, v in self._map.items() if not isinstance(k, tuple)})
        self._direction_colors = dict(DEFAULT_DIRECTION_COLORS)
        if self.color == DIRECTION:
            self._direction_colors.update(self._map)
        self._value_patterns: dict = {}
        unmapped = [v for v in self._pattern_values if v not in self._pattern_map]
        for i, value in enumerate(unmapped):
            self._value_patterns[value] = DEFAULT_PATTERN_SHAPES[i % len(DEFAULT_PATTERN_SHAPES)]
        self._value_patterns.update(self._pattern_map)

    def _pattern(self, groupname: Any, categoryname: Any) -> str | None:
        if self.pattern_shape is None:
            return None
        value = groupname if self.pattern_shape == self._group else categoryname
        return self._value_patterns.get(value, "")

    def _direction(self, values: np.ndarray, is_total: np.ndarray) -> list[str]:
        kinds = np.where(is_total, "total", np.where(values < 0, "decrease", "increase"))
        return [self._direction_colors[kind] for kind in kinds]

    def marker(
        self, groupname: Any, categoryname: Any, values: np.ndarray, is_total: np.ndarray
    ) -> dict:
        """Marker of one trace (one group/category combination over all x-positions)."""
        color: Any
        if self.color == DIRECTION:
            color = self._direction(values, is_total)
        elif (groupname, categoryname) in self._map:
            color = self._map[(groupname, categoryname)]
        else:
            value = groupname if self.color == self._group else categoryname
            color = self._value_colors.get(value)
        marker: dict = {"color": color}
        pattern = self._pattern(groupname, categoryname)
        if pattern is not None:
            marker["pattern"] = {"shape": pattern}
        return marker

    def total_marker(self, groupname: Any, total_name: str) -> dict:
        """Marker of a sum-total bar (total_type="sumtotal")."""
        color: Any
        if self.color == DIRECTION:
            color = self._direction_colors["total"]
        elif (groupname, total_name) in self._map:
            color = self._map[(groupname, total_name)]
        elif self.color == self._group:
            color = self._value_colors.get(groupname)
        else:
            color = self._map.get(total_name, self._direction_colors["total"])
        marker: dict = {"color": color}
        if self.pattern_shape is not None and self.pattern_shape == self._group:
            marker["pattern"] = {"shape": self._value_patterns.get(groupname, "")}
        return marker

    # ------------------------------------------------------------------ legend

    @property
    def show_trace_legend(self) -> bool:
        """In direction mode bars carry several colours: the legend explains the directions
        instead, plus the patterns if a pattern dimension is set."""
        return self.color != DIRECTION or self.pattern_shape is not None

    def direction_legend(self, used_kinds: set[str]) -> list[dict]:
        """Legend-only bar traces for increase / decrease / total in direction mode."""
        if self.color != DIRECTION:
            return []
        return [
            {
                "x": [None],
                "y": [None],
                "name": DIRECTION_LEGEND_NAMES[kind],
                "marker": {"color": self._direction_colors[kind]},
                "legendgroup": "direction",
                "showlegend": True,
                "hoverinfo": "skip",
            }
            for kind in DIRECTION_KINDS
            if kind in used_kinds
        ]

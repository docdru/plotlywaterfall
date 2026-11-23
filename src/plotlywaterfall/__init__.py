"""Plotly-express-style waterfall charts with groups, stacked categories and subtotals."""

from importlib.metadata import version as _version

from plotlywaterfall.waterfall import Waterfall, waterfall

__version__ = _version("plotlywaterfall")

__all__ = ["Waterfall", "__version__", "waterfall"]

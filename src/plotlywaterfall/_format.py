"""Number formatting shared by value labels and hover texts."""

from collections.abc import Callable, Iterable
from typing import Literal, get_args

NumberFormat = str | Callable[[float], str] | None
NegativeStyle = Literal["minus", "parentheses"]
NumberUnit = Literal["k", "M", "bn", "auto"]

NEGATIVE_STYLES: tuple[str, ...] = get_args(NegativeStyle)
NUMBER_UNITS: tuple[str, ...] = get_args(NumberUnit)
UNIT_DIVISORS = {"k": 1e3, "M": 1e6, "bn": 1e9}


def auto_unit(values: Iterable[float]) -> str | None:
    """The unit for a chart whose largest absolute value is max(|values|): one unit for all
    labels, so that a chart never mixes "950k" and "1.2M"."""
    largest = max((abs(v) for v in values), default=0.0)
    for unit in ("bn", "M", "k"):
        if largest >= UNIT_DIVISORS[unit]:
            return unit
    return None


class NumberFormatter:
    """Format numbers as `[sign][prefix]number[unit][suffix]`.

    `number_format` is a Python format spec applied to the absolute value (e.g. ",.1f"), a
    callable returning the text for the absolute value, or None for the default: thousands
    separators and up to two decimals without trailing zeros (9, 0.5, 1,234.57).
    The sign is written by the formatter itself, so that currency prefixes come out right
    ("-$5", not "$-5"); changes (steps) are always signed ("+9", "-7"), levels and totals only
    when negative. With negative_style="parentheses" negatives are written as in accounting,
    "(7)", and positive changes get no "+".
    `unit` ("k", "M", "bn") divides values by thousand, million or billion and writes the unit
    after the number ("12.5M").
    """

    def __init__(
        self,
        number_format: NumberFormat = None,
        prefix: str = "",
        suffix: str = "",
        negative_style: NegativeStyle = "minus",
        unit: str | None = None,
    ):
        if number_format is not None and not callable(number_format):
            try:
                format(1234.5, number_format)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid number_format {number_format!r}: {exc}") from exc
        if negative_style not in NEGATIVE_STYLES:
            raise ValueError(
                f"negative_style must be one of {NEGATIVE_STYLES}, got {negative_style!r}"
            )
        if unit is not None and unit not in UNIT_DIVISORS:
            raise ValueError(f"unit must be one of {tuple(UNIT_DIVISORS)} or None, got {unit!r}")
        self._format = number_format
        self._prefix = prefix
        self._suffix = suffix
        self._negative_style = negative_style
        self.unit = unit

    def _body(self, value: float) -> str:
        if self._format is None:
            text = f"{value:,.2f}"
            return text.rstrip("0").rstrip(".") if "." in text else text
        if callable(self._format):
            return self._format(value)
        return format(value, self._format)

    def __call__(self, value: float, signed: bool = False) -> str:
        divisor = UNIT_DIVISORS[self.unit] if self.unit else 1.0
        body = self._body(abs(value) / divisor)
        is_zero = body.strip("0.,") == ""
        number = f"{self._prefix}{body}{self.unit or ''}{self._suffix}"
        negative = value < 0 and not is_zero
        if self._negative_style == "parentheses":
            return f"({number})" if negative else number
        if negative:
            return f"-{number}"
        if signed and value > 0 and not is_zero:
            return f"+{number}"
        return number

"""Number formatting shared by value labels and hover texts."""

from collections.abc import Callable

NumberFormat = str | Callable[[float], str] | None


class NumberFormatter:
    """Format numbers as `[sign][prefix]number[suffix]`.

    `number_format` is a Python format spec applied to the absolute value (e.g. ",.1f"), a
    callable returning the text for the absolute value, or None for the default: thousands
    separators and up to two decimals without trailing zeros (9, 0.5, 1,234.57).
    The sign is written by the formatter itself, so that currency prefixes come out right
    ("-$5", not "$-5"); changes (steps) are always signed ("+9", "-7"), levels and totals only
    when negative.
    """

    def __init__(self, number_format: NumberFormat = None, prefix: str = "", suffix: str = ""):
        if number_format is not None and not callable(number_format):
            try:
                format(1234.5, number_format)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid number_format {number_format!r}: {exc}") from exc
        self._format = number_format
        self._prefix = prefix
        self._suffix = suffix

    def _body(self, value: float) -> str:
        if self._format is None:
            text = f"{value:,.2f}"
            return text.rstrip("0").rstrip(".") if "." in text else text
        if callable(self._format):
            return self._format(value)
        return format(value, self._format)

    def __call__(self, value: float, signed: bool = False) -> str:
        body = self._body(abs(value))
        is_zero = body.strip("0.,") == ""
        if value < 0 and not is_zero:
            sign = "-"
        elif signed and value > 0 and not is_zero:
            sign = "+"
        else:
            sign = ""
        return f"{sign}{self._prefix}{body}{self._suffix}"

"""Pine-compatible numeric behaviour.

**V53 computes in float64 and this implementation does the same.** Using
`Decimal` here would produce different results at the comparison boundaries
(`rng > dispMin * atr`, `ratio >= minRatr`, `adv >= 1.0`) and would therefore
not be a reproduction of the frozen artifact. The B1 contracts keep `Decimal`
for *recorded* values; the engine converts at its edges.

The formatters reproduce Pine's `str.tostring(x, "#.###")`. Verified against
all 58 recorded fills in the A2 fixtures: 0 mismatches on both the R multiple
("#.###") and the USD amount ("#.##").
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

#: Pine `na` for floats. Kept as a distinct name so intent reads clearly.
NA = float("nan")


def is_na(x: float | None) -> bool:
    """Pine `na(x)` for a float."""
    return x is None or (isinstance(x, float) and math.isnan(x))


def nz(x: float | None, replacement: float) -> float:
    """Pine `nz(x, replacement)`."""
    return replacement if is_na(x) else float(x)


def to_float(value: Any) -> float:
    """Convert a contract `Decimal` (or exact string) to the float Pine used."""
    if isinstance(value, float):
        return value
    if value is None:
        return NA
    return float(value)


def tostring(x: float, decimals: int) -> str:
    """Pine `str.tostring(x, "#.<n digits>")`.

    Rounds to `decimals` places and strips trailing zeros and a trailing point,
    which is what the `#` placeholder does. Ties round half away from zero; no
    tie occurs anywhere in the A2 fixtures, so the choice is documented rather
    than load-bearing (see the B2 audit).
    """
    if is_na(x):
        return "NaN"
    quantum = Decimal(1).scaleb(-decimals)
    value = Decimal(repr(float(x))).quantize(quantum, rounding=ROUND_HALF_UP)
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in ("", "-"):
        text = "0"
    return text


def px(x: float | None) -> str:
    """Pine `px(x)` from the artifact: `na(x) ? "-" : str.tostring(x, "#.####")`."""
    return "-" if is_na(x) else tostring(float(x), 4)

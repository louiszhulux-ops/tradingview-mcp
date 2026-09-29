"""Pine indicator equivalents: `ta.atr(14)` and `ta.pivothigh/low`.

Both are streaming and causal: they are fed one bar at a time and never look
forward. Phase 13E showed that a superficially reasonable pivot implementation
produces wrong results (180 mismatches over 20,567 bars), so the tie convention
here is transcribed from the artifact rather than reasoned about.
"""

from __future__ import annotations

from collections import deque

from bot.strategy.v53.numeric import NA, is_na


class WilderAtr:
    """`ta.atr(length)` — RMA of true range, seeded by an SMA of the first `length`.

    Pine's `ta.rma(src, n)`: `alpha = 1/n`, and
    `sum = na(sum[1]) ? ta.sma(src, n) : alpha*src + (1-alpha)*sum[1]`.
    So the value is `na` until `length` true ranges exist, then the SMA of them,
    then Wilder smoothing. True range on the first bar has no previous close and
    is therefore `high - low`.
    """

    def __init__(self, length: int) -> None:
        if length < 1:
            raise ValueError(f"atr length must be >= 1, got {length}")
        self.length = length
        self._previous_close: float | None = None
        self._seed: list[float] = []
        self._value: float = NA

    @property
    def value(self) -> float:
        """The current ATR, or NaN during warmup — Pine's `na`."""
        return self._value

    def update(self, high: float, low: float, close: float) -> float:
        if self._previous_close is None:
            true_range = high - low
        else:
            true_range = max(
                high - low,
                abs(high - self._previous_close),
                abs(low - self._previous_close),
            )
        self._previous_close = close

        if is_na(self._value):
            self._seed.append(true_range)
            if len(self._seed) == self.length:
                self._value = sum(self._seed) / self.length
        else:
            alpha = 1.0 / self.length
            self._value = alpha * true_range + (1.0 - alpha) * self._value
        return self._value


def is_pivot_high(highs, centre: int, half_width: int) -> bool:
    """`ta.pivothigh` tie convention: NON-STRICT left, STRICT right.

    `highs` is ordered oldest-first, so indices below `centre` are the left
    (older) side. A left bar equal to the centre is allowed; a right bar equal
    to the centre is not. The first of a run of equal extremes is the pivot.

    Transcribed from V53 §4a, whose own §6 verification block compared it to
    `ta.pivothigh(high, 3, 3)` with 0 mismatches over 20,567 chart bars.
    """
    centre_value = highs[centre]
    for index in range(len(highs)):
        if index < centre:              # older / left — equality allowed
            if highs[index] > centre_value:
                return False
        elif index > centre:            # newer / right — equality rejects
            if highs[index] >= centre_value:
                return False
    return True


def is_pivot_low(lows, centre: int, half_width: int) -> bool:
    """`ta.pivotlow` tie convention: NON-STRICT left, STRICT right."""
    centre_value = lows[centre]
    for index in range(len(lows)):
        if index < centre:
            if lows[index] < centre_value:
                return False
        elif index > centre:
            if lows[index] <= centre_value:
                return False
    return True


class PivotDetector:
    """Streaming `ta.pivothigh(src, n, n)` / `ta.pivotlow(src, n, n)`.

    Confirmation happens `n` bars after the pivot bar: feeding bar `i` reports a
    pivot centred on bar `i - n`. Before `2n + 1` bars exist, nothing confirms —
    matching Pine returning `na`.
    """

    def __init__(self, half_width: int) -> None:
        if half_width < 1:
            raise ValueError(f"pivot half-width must be >= 1, got {half_width}")
        self.half_width = half_width
        self._window = 2 * half_width + 1
        self._highs: deque[float] = deque(maxlen=self._window)
        self._lows: deque[float] = deque(maxlen=self._window)

    @property
    def ready(self) -> bool:
        return len(self._highs) == self._window

    def update(self, high: float, low: float) -> tuple[float, float]:
        """Push a bar; return `(pivot_high, pivot_low)`, NaN where none confirms."""
        self._highs.append(high)
        self._lows.append(low)
        if not self.ready:
            return NA, NA
        highs = list(self._highs)
        lows = list(self._lows)
        centre = self.half_width
        pivot_high = highs[centre] if is_pivot_high(highs, centre, self.half_width) else NA
        pivot_low = lows[centre] if is_pivot_low(lows, centre, self.half_width) else NA
        return pivot_high, pivot_low

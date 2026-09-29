"""V53 §"5m SWEEP ENGINE" — reference levels and sweep detection.

Everything here is 5m. The LTF stream never reaches this module.

**Two calendars, deliberately kept apart** (see `bot/U1_CME_SESSION_CALENDAR.md`):

* PDH/PDL roll on `ta.change(time("D")) != 0` — the CME **exchange-session**
  trade date, via `bot.calendar.is_trade_date_roll`.
* The Asia window is `hour(time, "UTC") < 7` — plain **UTC**, and must never be
  routed through the session calendar.

Unifying them would redefine V53 rather than reproduce it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from bot.calendar import is_trade_date_roll
from bot.contracts.enums import Direction, SweepSource
from bot.strategy.v53.constants import ASIA_END_HOUR_UTC, ATR_LENGTH, MIN_WICK, SWING_LEN
from bot.strategy.v53.indicators import PivotDetector, WilderAtr
from bot.strategy.v53.numeric import NA, is_na, nz


def utc_hour(ts_ms: int) -> int:
    """`hour(time, "UTC")` — the UTC hour of the bar's OPEN time."""
    return datetime.fromtimestamp(ts_ms / 1000, timezone.utc).hour


@dataclass
class SweepResult:
    """What one 5m bar produced. `sources` is ordered PD, AS, SW as V53 renders it."""

    sources: tuple[SweepSource, ...] = ()
    atr: float = NA

    @property
    def n_hit(self) -> int:
        return len(self.sources)

    @property
    def kind(self) -> str:
        """V53 `lSwG`: "PD", "AS", "SW", "PD+AS", "AS+SW", "PD+AS+SW"."""
        return "+".join(source.value for source in self.sources)


@dataclass
class SweepEngine:
    """Streaming reproduction of the 5m sweep engine.

    State mirrors the artifact one-for-one: `pdh`, `pdl`, `dh`, `dl`, `asiaH`,
    `asiaL`, `asiaOn`, `swH`, `swL`, plus `ta.atr(14)` and the 5m pivot detector.
    """

    direction: Direction
    previous_bar_open_ts_ms: int | None = None
    pdh: float = NA
    pdl: float = NA
    dh: float = NA
    dl: float = NA
    asia_high: float = NA
    asia_low: float = NA
    asia_on: bool = False
    swing_high: float = NA
    swing_low: float = NA
    _atr: WilderAtr = field(default_factory=lambda: WilderAtr(ATR_LENGTH))
    _pivots: PivotDetector = field(default_factory=lambda: PivotDetector(SWING_LEN))

    @property
    def atr(self) -> float:
        return self._atr.value

    def update(self, open_ts_ms: int, high: float, low: float, close: float) -> SweepResult:
        """Process one closed 5m bar in V53's own order."""
        # ---- previous-day high/low: EXCHANGE-SESSION day roll ----
        new_day = is_trade_date_roll(self.previous_bar_open_ts_ms, open_ts_ms)
        self.previous_bar_open_ts_ms = open_ts_ms
        if new_day:
            self.pdh = self.dh
            self.pdl = self.dl
            self.dh = high
            self.dl = low
        else:
            self.dh = max(nz(self.dh, high), high)
            self.dl = min(nz(self.dl, low), low)

        # ---- Asia session high/low: UTC window, NOT the session calendar ----
        in_asia = utc_hour(open_ts_ms) < ASIA_END_HOUR_UTC
        if in_asia and not self.asia_on:
            self.asia_on = True
            self.asia_high = high
            self.asia_low = low
        elif in_asia:
            self.asia_high = max(nz(self.asia_high, high), high)
            self.asia_low = min(nz(self.asia_low, low), low)
        else:
            self.asia_on = False

        # ---- 5m swing pivots, confirmed swLen bars late ----
        pivot_high, pivot_low = self._pivots.update(high, low)
        if not is_na(pivot_high):
            self.swing_high = pivot_high
        if not is_na(pivot_low):
            self.swing_low = pivot_low

        # ---- ATR(14) ----
        atr = self._atr.update(high, low, close)

        # ---- sweep test ----
        sources: list[SweepSource] = []
        if not is_na(atr) and atr > 0:
            if self.direction is Direction.LONG:
                if not is_na(self.pdl) and low < self.pdl - MIN_WICK * atr and close > self.pdl:
                    sources.append(SweepSource.PD)
                if not is_na(self.asia_low) and low < self.asia_low - MIN_WICK * atr and close > self.asia_low:
                    sources.append(SweepSource.AS)
                if not is_na(self.swing_low) and low < self.swing_low - MIN_WICK * atr and close > self.swing_low:
                    sources.append(SweepSource.SW)
            else:
                if not is_na(self.pdh) and high > self.pdh + MIN_WICK * atr and close < self.pdh:
                    sources.append(SweepSource.PD)
                if not is_na(self.asia_high) and high > self.asia_high + MIN_WICK * atr and close < self.asia_high:
                    sources.append(SweepSource.AS)
                if not is_na(self.swing_high) and high > self.swing_high + MIN_WICK * atr and close < self.swing_high:
                    sources.append(SweepSource.SW)

        return SweepResult(sources=tuple(sources), atr=atr)

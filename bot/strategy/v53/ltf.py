"""V53 §"LTF STREAM" — the 7-bar ring buffer and the 4-entry pivot register.

The LTF stream is delivered by `request.security_lower_tf` as the sub-bars of
the just-closed 5m bar, so it is an **intrabar reconstruction performed at the
parent close**, not an independent decision stream. `ltf_bars_seen` (`ltfN`)
is monotonic and never resets.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from bot.strategy.v53.constants import LTF_SWING_LEN, RING_SIZE
from bot.strategy.v53.indicators import is_pivot_high, is_pivot_low
from bot.strategy.v53.numeric import NA, is_na

#: `pvV`/`pvI`/`pvB` index layout.
LAST_PIVOT_HIGH, PREV_PIVOT_HIGH, LAST_PIVOT_LOW, PREV_PIVOT_LOW = 0, 1, 2, 3


@dataclass
class RingEntry:
    """One slot of `bH`/`bL`/`bC`/`bCB`/`bIX`/`bTM`."""

    high: float
    low: float
    close: float
    parent_bar_index: int
    ltf_index: int
    ts_ms: int


@dataclass
class LtfState:
    """Ring buffer + pivot register. Oldest at index 0, newest at `RING_SIZE - 1`."""

    ring: list[RingEntry] = field(default_factory=list)
    pivot_value: list[float] = field(default_factory=lambda: [NA] * 4)
    pivot_ltf_index: list[int] = field(default_factory=lambda: [-1] * 4)
    pivot_parent_bar: list[int] = field(default_factory=lambda: [-1] * 4)
    ltf_bars_seen: int = 0

    @property
    def ring_full(self) -> bool:
        return len(self.ring) == RING_SIZE

    def push(self, high: float, low: float, close: float,
             parent_bar_index: int, ts_ms: int) -> RingEntry:
        """Append one LTF bar, evicting the oldest past `RING_SIZE` (`array.shift`)."""
        self.ltf_bars_seen += 1
        entry = RingEntry(high, low, close, parent_bar_index, self.ltf_bars_seen, ts_ms)
        self.ring.append(entry)
        if len(self.ring) > RING_SIZE:
            self.ring.pop(0)
        return entry

    def confirm_pivots(self) -> tuple[bool, bool]:
        """§4a — confirm the ring centre as a pivot and shift the register.

        Returns `(confirmed_high, confirmed_low)`. Does nothing until the ring
        is full, matching `if array.size(bH) == RB`.
        """
        if not self.ring_full:
            return False, False

        highs = [entry.high for entry in self.ring]
        lows = [entry.low for entry in self.ring]
        centre = LTF_SWING_LEN
        centre_entry = self.ring[centre]

        confirmed_high = is_pivot_high(highs, centre, LTF_SWING_LEN)
        confirmed_low = is_pivot_low(lows, centre, LTF_SWING_LEN)

        if confirmed_high:
            self._shift(LAST_PIVOT_HIGH, PREV_PIVOT_HIGH, highs[centre], centre_entry)
        if confirmed_low:
            self._shift(LAST_PIVOT_LOW, PREV_PIVOT_LOW, lows[centre], centre_entry)
        return confirmed_high, confirmed_low

    def _shift(self, last: int, previous: int, value: float, entry: RingEntry) -> None:
        self.pivot_value[previous] = self.pivot_value[last]
        self.pivot_ltf_index[previous] = self.pivot_ltf_index[last]
        self.pivot_parent_bar[previous] = self.pivot_parent_bar[last]
        self.pivot_value[last] = value
        self.pivot_ltf_index[last] = entry.ltf_index
        self.pivot_parent_bar[last] = entry.parent_bar_index

    def opposing(self, is_long: bool) -> tuple[float, int, int, float, int]:
        """Opposing structure: pivot HIGHS for a long, pivot LOWS for a short.

        Returns `(oV, oI, oB, qV, qI)` — last opposing pivot value/LTF index/
        parent bar, then the previous opposing pivot's value and LTF index.
        """
        last = LAST_PIVOT_HIGH if is_long else LAST_PIVOT_LOW
        previous = PREV_PIVOT_HIGH if is_long else PREV_PIVOT_LOW
        return (
            self.pivot_value[last], self.pivot_ltf_index[last], self.pivot_parent_bar[last],
            self.pivot_value[previous], self.pivot_ltf_index[previous],
        )

    def newest_ts_ms(self) -> int:
        """`array.get(bTM, RB - 1)` — the newest ring entry's timestamp."""
        if not self.ring_full:
            raise IndexError("ring buffer is not full; bTM[RB-1] is out of bounds")
        return self.ring[-1].ts_ms

"""Synthetic bar construction for B2 tests.

Hand-built series that exercise one V53 rule at a time. **Not market data** —
no file is read and nothing is fetched. Timestamps sit inside the consumed
research window so the A1 pre-FE guard accepts them.
"""

from __future__ import annotations

from decimal import Decimal

from bot.contracts.enums import Timeframe
from bot.data.bars import Bar, ParentBar

#: 2026-07-01 00:00 UTC — mid-week, inside the already-consumed window.
BASE_MS = 1782864000000
FIVE_MIN = 300_000
ONE_MIN = 60_000

INSTRUMENT = "MGC1!"


def d(x: float | str) -> Decimal:
    return Decimal(str(x))


def bar(index: int, high: float, low: float, close: float, open_: float | None = None,
        tf: Timeframe = Timeframe.M5, base_ms: int = BASE_MS,
        instrument: str = INSTRUMENT) -> Bar:
    """One bar `index` periods after `base_ms`."""
    span = tf.minutes * ONE_MIN
    open_ms = base_ms + index * span
    return Bar(
        instrument=instrument, timeframe=tf,
        open_ts_ms=open_ms, close_ts_ms=open_ms + span,
        open=d(open_ if open_ is not None else close),
        high=d(high), low=d(low), close=d(close),
    )


def parent(index: int, high: float, low: float, close: float,
           subs: list[tuple[float, float, float]] | None = None,
           ltf: Timeframe = Timeframe.M1, base_ms: int = BASE_MS,
           instrument: str = INSTRUMENT) -> ParentBar:
    """A 5m bar plus its LTF sub-bars.

    `subs` is a list of `(high, low, close)`, oldest first. When omitted the
    parent carries five flat 1m sub-bars spanning its own range.
    """
    per = 5 // ltf.minutes
    if subs is None:
        subs = [(high, low, close)] * per
    parent_open_ms = base_ms + index * 5 * ONE_MIN
    sub_bars = [
        Bar(instrument=instrument, timeframe=ltf,
            open_ts_ms=parent_open_ms + i * ltf.minutes * ONE_MIN,
            close_ts_ms=parent_open_ms + (i + 1) * ltf.minutes * ONE_MIN,
            open=d(c), high=d(h), low=d(l), close=d(c))
        for i, (h, l, c) in enumerate(subs)
    ]
    return ParentBar(
        bar=bar(index, high, low, close, tf=Timeframe.M5,
                base_ms=base_ms, instrument=instrument),
        ltf_timeframe=ltf, ltf_bars=sub_bars,
    )


def flat(index: int, level: float = 100.0, half: float = 0.5, **kw) -> ParentBar:
    """A quiet 5m bar of range `2 * half` centred on `level`."""
    return parent(index, level + half, level - half, level, **kw)

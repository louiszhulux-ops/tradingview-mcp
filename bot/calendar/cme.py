"""CME Globex trade-date calendar for MGC1! (COMEX) and MNQ1! (CME).

Purpose: give B2 an exact, deterministic equivalent of TradingView's
``time("D")`` for these symbols, so PDH/PDL roll where V53 rolls them.

The rule, established in `bot/U1_CME_SESSION_CALENDAR.md`:

    A CME Globex trade date begins at 17:00 America/Chicago on the preceding
    calendar day. TradingView's ``time("D")`` returns the daily bar's open, and
    that daily bar spans one Globex session. So V53's
    ``ta.change(time("D")) != 0`` fires on the first bar at or after 17:00 CT.

**No holiday table participates in that rule.** A holiday removes bars; it does
not move the boundary. Because the market is shut from Friday 16:00 CT until
Sunday 17:00 CT, and shut for the whole of a full-closure date, every bar that
actually exists is labelled correctly by the 17:00 CT rule alone. The closure
and early-close sets below are **advisory** — for gap detection and for
expecting a short session — and are deliberately not consulted by
:func:`trade_date`.

**This module applies no pre-FE guard, on purpose.** It is a pure function of a
timestamp, not a data path: it must be able to answer "when does the session
open on 2026-11-02" in order to document the DST transition at all. Market data
is guarded where it enters, in ``Bar.__post_init__``. Nothing here reads a file,
a feed, or a clock.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

#: The session timezone for **both** products. See U1 doc §1–2.
CHICAGO = ZoneInfo("America/Chicago")
UTC = ZoneInfo("UTC")

#: A new trade date begins at this local hour, on the preceding calendar day.
TRADE_DATE_ROLL_HOUR_CT = 17

#: Nominal session close, local hour. See U1 doc §3 for the MNQ 16:15 CT caveat.
SESSION_CLOSE_HOUR_CT = 16

#: Daily maintenance break, local hours [start, end).
MAINTENANCE_BREAK_CT = (16, 17)

_MS = 1000


class SessionCalendarError(ValueError):
    """A calendar input that cannot be interpreted."""


# ---------------------------------------------------------------------------
# Advisory holiday sets. NOT used by trade_date(). See the module docstring and
# U1 doc §9 for why, and for the confidence level of these dates.
# ---------------------------------------------------------------------------

#: Dates with no Globex session at all, so no daily bar and no trade date.
CME_FULL_CLOSURES: frozenset[date] = frozenset({
    date(2026, 12, 25),  # Christmas Day (Fri)
    date(2027, 1, 1),    # New Year's Day (Fri)
    date(2027, 3, 26),   # Good Friday
})

#: Dates whose session exists but closes early. The trade date is unaffected.
CME_EARLY_CLOSES: frozenset[date] = frozenset({
    date(2026, 5, 25),   # Memorial Day (Mon)
    date(2026, 6, 19),   # Juneteenth (Fri)
    date(2026, 7, 3),    # Independence Day observed (Fri; Jul 4 is a Saturday)
    date(2026, 9, 7),    # Labor Day (Mon)
    date(2026, 11, 26),  # Thanksgiving (Thu)
    date(2026, 11, 27),  # Day after Thanksgiving (Fri)
    date(2026, 12, 24),  # Christmas Eve (Thu)
    date(2026, 12, 31),  # New Year's Eve (Thu)
    date(2027, 1, 18),   # Martin Luther King Jr. Day (Mon)
    date(2027, 2, 15),   # Presidents' Day (Mon)
})

#: The window these sets are asserted over. Outside it they are simply unknown.
CALENDAR_COVERAGE = (date(2026, 5, 1), date(2027, 5, 1))


# ---------------------------------------------------------------------------
# The contract B2 calls
# ---------------------------------------------------------------------------

def _local(ts_ms: int) -> datetime:
    if isinstance(ts_ms, bool) or not isinstance(ts_ms, int):
        raise SessionCalendarError(
            f"timestamp must be epoch milliseconds as int, got "
            f"{type(ts_ms).__name__} {ts_ms!r}"
        )
    return datetime.fromtimestamp(ts_ms / _MS, CHICAGO)


def trade_date(ts_ms: int) -> date:
    """The CME trade date a timestamp belongs to — TradingView's ``time("D")``.

    At or after 17:00 America/Chicago the timestamp belongs to the **next**
    calendar day's trade date; before 17:00 it belongs to the current one.
    DST is handled by the zone, not by an offset constant.
    """
    local = _local(ts_ms)
    if local.hour >= TRADE_DATE_ROLL_HOUR_CT:
        return local.date() + timedelta(days=1)
    return local.date()


def is_trade_date_roll(previous_ts_ms: int | None, ts_ms: int) -> bool:
    """``ta.change(time("D")) != 0`` — did the daily bar change at this bar?

    ``previous_ts_ms is None`` means this is the first bar, and returns
    ``False``: Pine's ``ta.change`` is ``na`` on bar 0 and ``if na(...)`` does
    not execute. (V53's day-high/low state happens to be identical either way on
    bar 0, but this mirrors the artifact rather than relying on that.)
    """
    if previous_ts_ms is None:
        return False
    return trade_date(previous_ts_ms) != trade_date(ts_ms)


def session_open_utc_ms(td: date) -> int:
    """Nominal open of the session carrying trade date ``td``: 17:00 CT the day before.

    Nominal: after a full closure or a weekend the *actual* first bar can be
    later. Use it to bound a search, not to assert a bar exists.
    """
    local = datetime.combine(td - timedelta(days=1), time(TRADE_DATE_ROLL_HOUR_CT), CHICAGO)
    return int(local.timestamp() * _MS)


def session_close_utc_ms(td: date) -> int:
    """Nominal close of trade date ``td``: 16:00 CT on ``td`` itself."""
    local = datetime.combine(td, time(SESSION_CLOSE_HOUR_CT), CHICAGO)
    return int(local.timestamp() * _MS)


def is_in_maintenance_break(ts_ms: int) -> bool:
    """Whether a timestamp falls in the daily 16:00–17:00 CT break."""
    start, end = MAINTENANCE_BREAK_CT
    return start <= _local(ts_ms).hour < end


def utc_offset_minutes(ts_ms: int) -> int:
    """The America/Chicago UTC offset in force: −300 (CDT) or −360 (CST)."""
    offset = _local(ts_ms).utcoffset()
    if offset is None:  # pragma: no cover — zoneinfo always supplies one
        raise SessionCalendarError("no UTC offset available")
    return int(offset.total_seconds() // 60)


def is_full_closure(td: date) -> bool:
    """Advisory: no session on this trade date. Not consulted by trade_date()."""
    return td in CME_FULL_CLOSURES


def is_early_close(td: date) -> bool:
    """Advisory: session exists but ends early. Not consulted by trade_date()."""
    return td in CME_EARLY_CLOSES

"""CME Globex session calendar — the U1 resolution.

Reproduces the *semantics* of TradingView's ``time("D")`` for CME Group futures,
which is what V53's ``newD = ta.change(time("D")) != 0`` keys PDH/PDL off.

This is a calendar, not a strategy. It contains no V53 logic.
"""

from bot.calendar.cme import (
    CHICAGO,
    CME_EARLY_CLOSES,
    CME_FULL_CLOSURES,
    MAINTENANCE_BREAK_CT,
    SESSION_CLOSE_HOUR_CT,
    TRADE_DATE_ROLL_HOUR_CT,
    SessionCalendarError,
    is_early_close,
    is_full_closure,
    is_in_maintenance_break,
    is_trade_date_roll,
    session_close_utc_ms,
    session_open_utc_ms,
    trade_date,
    utc_offset_minutes,
)

__all__ = [
    "CHICAGO", "TRADE_DATE_ROLL_HOUR_CT", "SESSION_CLOSE_HOUR_CT",
    "MAINTENANCE_BREAK_CT", "CME_FULL_CLOSURES", "CME_EARLY_CLOSES",
    "SessionCalendarError", "trade_date", "is_trade_date_roll",
    "session_open_utc_ms", "session_close_utc_ms", "is_in_maintenance_break",
    "is_full_closure", "is_early_close", "utc_offset_minutes",
]

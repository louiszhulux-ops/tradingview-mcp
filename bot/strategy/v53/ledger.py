"""V53 §1 ledger row — the exact string the artifact pushes into `LED`.

Reproducing this matters because the A2 golden fixtures *are* these rows: B3
compares text, not floats. The recorded value of a price is therefore
`str.tostring(x, "#.####")` of the float V53 held, not the float itself.

Verified against all 58 recorded fills: the R multiple and USD amount
reproduce with 0 mismatches (see the B2 audit).
"""

from __future__ import annotations

from datetime import datetime, timezone

from bot.contracts.enums import Direction, ExitReason
from bot.strategy.v53.numeric import px, tostring
from bot.strategy.v53.sequence import Outcome

_REASON_TEXT = {
    ExitReason.STOP: "stop",
    ExitReason.TARGET: "target",
    ExitReason.TIMEOUT: "timeout",
}


def format_time(ts_ms: int) -> str:
    """V53 `ft(t)`: `t == 0 ? "-" : str.format_time(t, "yyyy-MM-dd HH:mm", "UTC")`."""
    if ts_ms == 0:
        return "-"
    return datetime.fromtimestamp(ts_ms / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M")


def ledger_row(outcome: Outcome, ticker: str, direction: Direction,
               ltf_minutes: int, fold_name: str) -> str:
    """Build the pipe-delimited ledger row, field for field with the artifact."""
    slot = outcome.slot
    return "|".join([
        ticker,
        "L" if direction is Direction.LONG else "S",
        f"{ltf_minutes}m",
        fold_name,
        f"sw {format_time(slot.ledger_sweep_ts_ms)}",
        slot.ledger_sweep_kind,
        f"swX {px(slot.ledger_sweep_extreme)}",
        f"ch {format_time(slot.ledger_choch_ts_ms)}",
        f"chL {px(slot.choch_level)}",
        f"rt {format_time(slot.ledger_retest_ts_ms)}",
        f"bos {format_time(slot.ledger_bos_ts_ms)}",
        f"bosL {px(slot.ledger_bos_level)}",
        f"fvg {px(slot.ledger_fvg_low)}-{px(slot.ledger_fvg_high)}",
        f"en {format_time(slot.ledger_entry_ts_ms)}",
        f"enPx {px(slot.entry)}",
        f"stop {px(slot.stop)}",
        "WIN" if outcome.won else "LOSS",
        f"{tostring(outcome.r_net, 3)}R",
        f"${tostring(outcome.pnl_usd, 2)}",
        _REASON_TEXT[outcome.exit_reason],
        f"{outcome.bars_in_trade}bars",
    ])

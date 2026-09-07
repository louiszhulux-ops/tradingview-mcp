#!/usr/bin/env python3
"""
Trade management (§15) and the meta-strategy layer (§31).

Management is a state machine, not a single exit rule. The brief is explicit
that breakeven logic may be destroying winners, so BE is OFF by default and
must earn its place against measurement -- which it failed to do when tested
earlier in this project (BE at 1.5R: PF 1.327 -> 1.300, drawdown worse).

The meta-layer decides which setup FAMILY is live given the regime, rather than
running every setup all the time. This is the "same setup is not the same trade
in different conditions" principle applied at the portfolio-of-setups level.
"""
from dataclasses import dataclass
from enum import IntEnum
from decision_engine import Regime


class TradeState(IntEnum):
    INITIAL = 0        # full risk, original stop
    PROGRESSING = 1    # moved favourably but not yet at partial level
    PARTIAL_TAKEN = 2  # scaled out, remainder running
    TRAILING = 3       # stop is trailing structure


@dataclass
class MgmtConfig:
    partial_at_R: float = 1.0      # take some off here; 0 disables
    partial_frac: float = 0.5
    be_at_R: float = 0.0           # 0 = OFF. Measured harmful earlier.
    trail_after_R: float = 1.5     # begin trailing beyond this
    trail_atr: float = 1.5
    time_stop_bars: int = 36
    flat_before_close_min: int = 30


class TradeManager:
    """Pure function of (unrealised R, bars held) -> action. Easy to unit test."""

    def __init__(self, cfg: MgmtConfig = None):
        self.c = cfg or MgmtConfig()

    def step(self, state: TradeState, r_now: float, bars: int,
             mins_to_close: int, partial_done: bool):
        c = self.c
        if mins_to_close <= c.flat_before_close_min:
            return "FLAT_SESSION_END", state
        if bars >= c.time_stop_bars:
            return "FLAT_TIME_STOP", state
        if c.partial_at_R > 0 and not partial_done and r_now >= c.partial_at_R:
            return "TAKE_PARTIAL", TradeState.PARTIAL_TAKEN
        if c.be_at_R > 0 and r_now >= c.be_at_R and state < TradeState.TRAILING:
            return "MOVE_TO_BE", state
        if r_now >= c.trail_after_R:
            return "TRAIL", TradeState.TRAILING
        if r_now > 0:
            return "HOLD", TradeState.PROGRESSING
        return "HOLD", state


# ---------------- meta-strategy (§31) ----------------
# Which setup families are live in which regime. Grounded in V30: location
# matters in trending regimes and not in chop, and the regime ordering is
# monotonic, so chop is stand-aside rather than "trade something else".
META = {
    Regime.WITH_TREND:    ["S1 pullback", "S2 retest", "S4 followBrk"],
    Regime.COUNTER_TREND: ["S3 fadeSweep", "S6 vwapRecl"],
    Regime.RANGE:         ["S3 fadeSweep", "S5 ORB"],
    Regime.CHOP:          [],          # stand aside
}


def active_setups(regime: Regime):
    return META[regime]


if __name__ == "__main__":
    tm = TradeManager()
    print("trade management state machine (BE disabled by default)\n")
    print(f"{'R now':>7} {'bars':>5} {'min to close':>13} {'action':>20}")
    for r, b, m in [(-0.5, 5, 300), (0.4, 8, 300), (1.0, 12, 300),
                    (1.6, 20, 300), (2.5, 25, 300), (0.8, 40, 300), (1.2, 10, 20)]:
        act, _ = tm.step(TradeState.INITIAL, r, b, m, partial_done=False)
        print(f"{r:>7.1f} {b:>5} {m:>13} {act:>20}")

    print("\nmeta-strategy: which setups are live per regime")
    for reg in Regime:
        s = active_setups(reg)
        print(f"  {reg.name:>14}: {', '.join(s) if s else 'STAND ASIDE'}")

    print("\nbreakeven note: be_at_R defaults to 0 (off). When tested earlier in")
    print("this project, moving to BE at 1.5R took profit factor 1.327 -> 1.300")
    print("and made drawdown worse. It stays off until it can beat that.")

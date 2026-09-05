#!/usr/bin/env python3
"""
Conditional decision engine (brief section 9) + quality model (section 6)
+ journal and missed-trade logger (sections 36-38).

This is the reference implementation of the decision hierarchy. Pine mirrors it
bar-by-bar; keeping it here means the logic can be unit-tested and the quality
weights can be refitted without touching the chart code.

Every candidate walks the same ten steps and produces a record whether it is
taken or not. The rejection records are the point: a system that rejects
everything looks identical to a system with no opportunities unless you log the
difference.
"""
from dataclasses import dataclass, field, asdict
from enum import IntEnum


class Regime(IntEnum):
    WITH_TREND = 0
    COUNTER_TREND = 1
    RANGE = 2
    CHOP = 3


class Quality(IntEnum):
    A_PLUS = 0
    A = 1
    B = 2
    C = 3          # rejected


class Reject(IntEnum):
    NONE = 0
    REGIME = 1
    LOCATION = 2
    NO_CONFIRMATION = 3
    STOP_TOO_WIDE = 4
    STOP_TOO_TIGHT = 5
    POOR_RR = 6
    EVAL_RISK = 7
    ALREADY_EXPOSED = 8
    DAILY_TARGET_MET = 9
    DAILY_STOP = 10
    NEWS = 11
    SESSION = 12
    SIZE = 13


@dataclass
class Candidate:
    setup: str
    direction: int
    entry: float
    stop: float
    target: float
    regime: Regime
    at_level: bool
    level_name: str = ""
    confirmed: bool = False
    displacement: bool = False
    atr: float = 0.0

    @property
    def stop_dist(self):
        return abs(self.entry - self.stop)

    @property
    def rr(self):
        return abs(self.target - self.entry) / self.stop_dist if self.stop_dist else 0.0


@dataclass
class Decision:
    candidate: Candidate
    quality: Quality
    decision: str              # ENTER / WAIT / REJECT
    reject: Reject = Reject.NONE
    contracts: int = 0
    risk_usd: float = 0.0
    notes: str = ""


class QualityModel:
    """
    Scores a candidate from the effects that were actually MEASURED, not from
    invented weights:
      regime      V30: with-trend beats chop by 0.044R, monotonically
      location    V30: at a level is worth +0.043R in trending regimes,
                       and ~0 in chop -- so the bonus is regime-dependent
      confirmation displacement, as a tiebreaker
    """
    REGIME_SCORE = {Regime.WITH_TREND: 2.0, Regime.COUNTER_TREND: 1.0,
                    Regime.RANGE: 0.5, Regime.CHOP: 0.0}

    def score(self, c: Candidate) -> float:
        s = self.REGIME_SCORE[c.regime]
        # location only earns its bonus where it was measured to matter
        if c.at_level and c.regime in (Regime.WITH_TREND, Regime.COUNTER_TREND):
            s += 1.5
        elif c.at_level:
            s += 0.25
        if c.confirmed:
            s += 0.5
        if c.displacement:
            s += 0.5
        if c.rr >= 2.0:
            s += 0.5
        return s

    def grade(self, c: Candidate) -> Quality:
        s = self.score(c)
        return Quality.A_PLUS if s >= 4.0 else Quality.A if s >= 3.0 \
            else Quality.B if s >= 2.0 else Quality.C


class DecisionEngine:
    def __init__(self, acct, risk_engine, quality=None,
                 min_rr=1.2, max_stop_atr=2.5, min_stop_atr=0.2,
                 daily_target_days=3):
        self.a = acct
        self.risk = risk_engine
        self.q = quality or QualityModel()
        self.min_rr = min_rr
        self.max_stop_atr = max_stop_atr
        self.min_stop_atr = min_stop_atr
        self.daily_target_days = daily_target_days
        self.journal = []
        self.missed = []

    def evaluate(self, c: Candidate, state, day_pnl, loss_streak,
                 in_position, point_value, in_session=True, news_block=False):
        def out(dec, rej=Reject.NONE, n=0, r=0.0, note=""):
            d = Decision(c, self.q.grade(c), dec, rej, n, r, note)
            (self.journal if dec == "ENTER" else self.missed).append(d)
            return d

        # 1 session / news
        if not in_session:
            return out("REJECT", Reject.SESSION)
        if news_block:
            return out("REJECT", Reject.NEWS)
        # 2 already exposed
        if in_position:
            return out("REJECT", Reject.ALREADY_EXPOSED)
        # 3 evaluation state: daily target met -> STOP, consistency punishes overshoot
        day_target = self.a.ideal_daily_target(self.daily_target_days)
        if day_pnl >= day_target:
            return out("REJECT", Reject.DAILY_TARGET_MET,
                       note=f"day target ${day_target:,.0f} reached")
        # 4 invalidation must be sane
        if c.stop_dist <= 0:
            return out("REJECT", Reject.STOP_TOO_TIGHT)
        if c.atr > 0:
            if c.stop_dist > self.max_stop_atr * c.atr:
                return out("REJECT", Reject.STOP_TOO_WIDE)
            if c.stop_dist < self.min_stop_atr * c.atr:
                return out("REJECT", Reject.STOP_TOO_TIGHT)
        # 5 reward must justify it
        if c.rr < self.min_rr:
            return out("REJECT", Reject.POOR_RR, note=f"rr {c.rr:.2f}")
        # 6 quality
        grade = self.q.grade(c)
        if grade == Quality.C:
            return out("REJECT", Reject.REGIME if c.regime == Regime.CHOP
                       else Reject.LOCATION, note=f"score {self.q.score(c):.1f}")
        # 7 risk engine has final say
        n, r, why = self.risk.risk_for(state, int(grade), c.stop_dist,
                                       point_value, day_pnl, loss_streak)
        if n < 1:
            return out("REJECT", Reject.EVAL_RISK if "buffer" in why or "daily" in why
                       else Reject.SIZE, note=why)
        return out("ENTER", n=n, r=r, note=f"grade {grade.name}, {why}")

    def summary(self):
        from collections import Counter
        taken = len(self.journal)
        rej = Counter(d.reject.name for d in self.missed)
        return taken, dict(rej)


if __name__ == "__main__":
    from prop_rules import LUCIDFLEX, EvalState
    from risk_engine import RiskEngine

    a = LUCIDFLEX["50K"]
    st = EvalState(a)
    de = DecisionEngine(a, RiskEngine(a))

    cases = [
        ("A+ : with-trend, at PDH, confirmed", Candidate("S2 retest", 1, 4400, 4392, 4416,
            Regime.WITH_TREND, True, "PDH", True, True, atr=8)),
        ("A  : with-trend, at level, no conf", Candidate("S1 pullback", 1, 4400, 4392, 4412,
            Regime.WITH_TREND, True, "VWAP", False, False, atr=8)),
        ("B  : range, at level",               Candidate("S3 fade", -1, 4400, 4408, 4388,
            Regime.RANGE, True, "PDH", True, False, atr=8)),
        ("C  : chop, mid-range -> reject",     Candidate("S6 vwap", 1, 4400, 4392, 4412,
            Regime.CHOP, False, "", False, False, atr=8)),
        ("poor R:R -> reject",                 Candidate("S1 pullback", 1, 4400, 4392, 4404,
            Regime.WITH_TREND, True, "VWAP", True, False, atr=8)),
        ("stop too wide -> reject",            Candidate("S5 ORB", 1, 4400, 4370, 4460,
            Regime.WITH_TREND, True, "ORH", True, False, atr=8)),
    ]
    print(f"{'case':>38} {'grade':>7} {'decision':>9} {'ctr':>4} {'why':>26}")
    for lbl, c in cases:
        d = de.evaluate(c, st, day_pnl=0, loss_streak=0, in_position=False, point_value=10)
        why = d.notes if d.decision == "ENTER" else d.reject.name
        print(f"{lbl:>38} {d.quality.name:>7} {d.decision:>9} {d.contracts:>4} {why:>26}")

    print("\nevaluation-state gating:")
    d = de.evaluate(cases[0][1], st, day_pnl=1100, loss_streak=0,
                    in_position=False, point_value=10)
    print(f"  day already +$1,100 vs $1,000 target -> {d.decision} ({d.reject.name}) {d.notes}")
    d = de.evaluate(cases[0][1], st, day_pnl=-800, loss_streak=3,
                    in_position=False, point_value=10)
    print(f"  down $800 on 3 straight losses       -> {d.decision} ({d.reject.name}) {d.notes}")

    taken, rej = de.summary()
    print(f"\njournal: {taken} entered;  missed-trade log: {rej}")

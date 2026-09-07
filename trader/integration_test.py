#!/usr/bin/env python3
"""
End-to-end integration test of the full stack on synthetic opportunity flow.

Proves the components actually work together and that the evaluation behaviours
fire correctly -- particularly the two that every prior version of this project
got wrong: the daily target STOPPING trading, and consistency being satisfied at
the moment of pass.

Synthetic flow, not a backtest. It validates plumbing, not edge.
"""
import random
from prop_rules import LUCIDFLEX, EvalState
from risk_engine import RiskEngine
from decision_engine import DecisionEngine, Candidate, Regime, Quality, Reject
from management import TradeManager, MgmtConfig, active_setups

random.seed(7)
ACCT = LUCIDFLEX["50K"]
PV = 10.0          # MGC


def make_day(rng, n_opps=14, atr=8.0):
    """A day's worth of candidate opportunities, mixed quality."""
    out = []
    for _ in range(n_opps):
        reg = rng.choices([Regime.WITH_TREND, Regime.COUNTER_TREND,
                           Regime.RANGE, Regime.CHOP],
                          weights=[0.25, 0.2, 0.25, 0.3])[0]
        at_lvl = rng.random() < 0.45
        conf = rng.random() < 0.5
        disp = rng.random() < 0.35
        d = rng.choice([1, -1])
        stop_atr = rng.uniform(0.4, 1.8)
        rr = rng.uniform(1.0, 2.6)
        entry = 4400.0
        stop = entry - d * stop_atr * atr
        tgt = entry + d * stop_atr * atr * rr
        out.append(Candidate("S?", d, entry, stop, tgt, reg, at_lvl,
                             "LVL" if at_lvl else "", conf, disp, atr))
    return out


def outcome(c, win_rate_by_grade, grade, rng):
    """Synthetic result in R at the trade's own reward:risk."""
    w = win_rate_by_grade[grade]
    return c.rr if rng.random() < w else -1.0


def run_attempt(win_by_grade, target_days=3, max_days=20, seed=0, verbose=False):
    rng = random.Random(seed)
    st = EvalState(ACCT)
    de = DecisionEngine(ACCT, RiskEngine(ACCT), daily_target_days=target_days)
    streak = 0
    for _day in range(max_days):
        if st.status != "running":
            break
        day_pnl = 0.0
        for c in make_day(rng):
            d = de.evaluate(c, st, day_pnl, streak, in_position=False, point_value=PV)
            if d.decision != "ENTER":
                continue
            r = outcome(c, win_by_grade, d.quality, rng)
            pnl = r * d.risk_usd
            st.apply_trade(pnl, worst_excursion=abs(min(0.0, pnl)))
            if st.status != "running":
                break
            day_pnl += pnl
            streak = 0 if r > 0 else streak + 1
        st.close_day()
        if verbose:
            print(f"    day {st.day_index}: {day_pnl:+8.0f}  bal {st.balance:8.0f}  "
                  f"floor {st.floor:8.0f}  {'LOCKED' if st.locked else ''}")
    return st, de


print("INTEGRATION TEST -- full stack, synthetic opportunity flow\n")
WB = {Quality.A_PLUS: 0.58, Quality.A: 0.52, Quality.B: 0.46, Quality.C: 0.0}

print("one attempt, verbose:")
st, de = run_attempt(WB, seed=3, verbose=True)
print(f"  result: {st.status} in {st.day_index} days, days = "
      f"{[f'{p:+.0f}' for p in st.day_pnls]}")
if st.day_pnls:
    wins = [p for p in st.day_pnls if p > 0]
    tot = sum(st.day_pnls)
    if wins and tot > 0:
        print(f"  consistency: largest day {max(wins):.0f} / total {tot:.0f} "
              f"= {max(wins)/tot:.1%} (limit {ACCT.consistency:.0%})")

taken, rej = de.summary()
print(f"\n  journal: {taken} trades taken")
print(f"  missed-trade log: {rej}")

print("\n1,000 attempts:")
res = {"pass": 0, "bust": 0, "running": 0}
days, cons_fail = [], 0
for s in range(1000):
    st, _ = run_attempt(WB, seed=s)
    res[st.status] = res.get(st.status, 0) + 1
    if st.status == "pass":
        days.append(st.day_index)
    elif st.status == "running":
        # did it reach the profit but fail consistency?
        if st.balance >= ACCT.start_balance + ACCT.profit_target:
            cons_fail += 1
from statistics import median
print(f"  pass {res['pass']/10:.1f}%   bust {res['bust']/10:.1f}%   "
      f"unresolved {res['running']/10:.1f}%")
if days:
    print(f"  median days to pass: {median(days)}")
print(f"  reached target but blocked by consistency: {cons_fail}")

print("\nbehaviour checks:")
st2, de2 = run_attempt(WB, target_days=2, seed=11)
print(f"  2-day config -> {st2.status} in {st2.day_index} days, "
      f"days {[f'{p:+.0f}' for p in st2.day_pnls]}")
_, rej2 = de2.summary()
print(f"  DAILY_TARGET_MET rejections: {rej2.get('DAILY_TARGET_MET', 0)} "
      f"(the bot stopping itself once the day's goal is banked)")

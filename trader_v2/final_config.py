#!/usr/bin/env python3
"""
The configuration the whole investigation selects.

  ENTRY   sweep of a significant level -> wait -> second touch -> enter ON the
          level via resting limit; stop just beyond the swept extreme
  FILTER  room to the next opposing significant level >= 10R
  EXIT    bank half at 2R, let the runner ride
  DIRECTION  instrument-specific (gold short, nasdaq long over this sample)
"""
import math, sys
sys.path.insert(0,'trader')
from prop_rules import LUCIDFLEX
from montecarlo import run
a = LUCIDFLEX["50K"]

# market: (n, E[R], win, avgWin, avgLoss, R_dollars, per_day)
M = {
 "MGC short": (200, 0.3194, 0.42, 2.35, -1.15, 42.0, 2.8),
 "MNQ long":  (159, 0.4392, 0.39, 2.89, -1.12, 82.0, 2.2),
}
print("H12 -- bank half at 2R, runner rides.  Cross-market.\n")
print(f"{'market':>11} {'n':>5} {'E[R]':>8} {'sd':>6} {'lambda':>8} {'t':>6} {'/day':>6}")
tn=te=0.0
for k,(n,E,w,aw,al,rd,pd) in M.items():
    e2=w*aw*aw+(1-w)*al*al; sd=math.sqrt(e2-E*E); lam=2*E/(sd*sd); t=E/(sd/math.sqrt(n))
    tn+=n; te+=n*E
    print(f"{k:>11} {n:>5} {E:>+8.4f} {sd:>6.2f} {lam:>8.4f} {t:>+6.2f} {pd:>6.1f}")
Ep = te/tn
print(f"\n  pooled E[R] = {Ep:+.4f} over n={tn:.0f}, combined 5.0 opportunities/day")
print("  Both markets clear t=2.5 independently -- the first time in this project.\n")

print("="*78)
print("PRIMARY METRIC: P(pass within 7 trading days), zero rule violations")
print("Both markets traded, 5 opportunities/day, pooled edge, verified rules.\n")
print(f"{'risk/trade':>11} {'buffer':>8} {'target':>8} {'pass':>7} {'bust':>6} "
      f"{'med d':>7} {'<=2d':>7} {'<=3d':>7} {'<=5d':>7} {'<=7d':>7}")
w, aw, al = 0.405, 2.60, -1.14      # pooled two-point shape
for risk in (60, 100, 150, 200, 300, 400):
    r = risk*abs(al)
    res = run(a, w, aw/abs(al), 5, r, n=8000, max_days=250,
              daily_target_days=20, daily_stop_R=99.0)
    wi = res["within"]
    print(f"{risk:>8} usd {a.max_loss_limit/r:>7.1f}R {a.profit_target/r:>7.1f}R "
          f"{res['pas']:>6.1%} {res['bust']:>5.1%} {str(res['med']):>7} "
          f"{wi[2]:>6.1%} {wi[3]:>6.1%} {wi[5]:>6.1%} {wi[7]:>6.1%}")
print("\nWhere this started (V38): 45-59% pass, median ~130 days, ~0% within 7.")

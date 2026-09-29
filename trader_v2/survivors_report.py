#!/usr/bin/env python3
"""Full required reporting for the two families that pass the robustness gate."""
import math, sys
sys.path.insert(0,'trader')
from prop_rules import LUCIDFLEX
from montecarlo import run
a = LUCIDFLEX["50K"]

S = {  # E[R], win, n, perDay, PF, MFE, MAE, R_dollars(est)
 "F6 range MR": (0.134, 0.2245, 1335, 18.7, 1.15, 2.11, 2.32, 55.0),
 "F0 sweep":    (0.037, 0.1973, 1235, 17.3, 1.04, 2.05, 1.98, 55.0),
}
print("TRADING QUALITY (primary)\n")
print(f"{'family':>13} {'E[R]':>8} {'win%':>6} {'avgW':>6} {'avgL':>6} {'PF':>5} "
      f"{'MFE':>5} {'MAE':>5} {'sd':>5} {'lambda':>8} {'t':>6} {'n':>6} {'/day':>6}")
for k,(E,w,n,pd,pf,mfe,mae,rd) in S.items():
    e2 = w*25 + (1-w)*1.0; sd = math.sqrt(e2-E*E)
    print(f"{k:>13} {E:>+8.3f} {100*w:>5.1f}% {5.0:>6.1f} {-1.0:>6.1f} {pf:>5.2f} "
          f"{mfe:>5.2f} {mae:>5.2f} {sd:>5.2f} {2*E/(sd*sd):>8.4f} "
          f"{E/(sd/math.sqrt(n)):>+6.2f} {n:>6} {pd:>6.1f}")

print("\nLosing-streak distribution at a 22.5% win rate (F6):")
w = 0.2245
for L in (5,8,10,12,15,20):
    p = (1-w)**L
    print(f"   run of {L:>2} losses: p={p:.4f} per attempt, expected once per "
          f"{1/p:>7.0f} trades  (~{1/p/18.7:>5.1f} days)")

print("\n" + "="*80)
print("EVALUATION PERFORMANCE (secondary -- reported, not optimised)\n")
print("F6 range mean-reversion, 18.7 opportunities/day, R ~ $55/micro contract.")
print("Risk is chosen for QUALITY (drawdown control), not for speed.\n")
print(f"{'risk':>7} {'buffer':>8} {'pass':>7} {'bust':>6} {'med d':>7} {'p25':>5} {'p75':>5} "
      f"{'<=2d':>6} {'<=3d':>6} {'<=7d':>6}")
E, w = 0.134, 0.2245
for risk in (55, 110, 165, 220, 330):
    res = run(a, w, 5.0, 19, risk, n=8000, max_days=250,
              daily_target_days=20, daily_stop_R=99.0)
    wi = res["within"]
    print(f"{risk:>5}$ {a.max_loss_limit/risk:>7.1f}R {res['pas']:>6.1%} {res['bust']:>5.1%} "
          f"{str(res['med']):>7} {'-':>5} {'-':>5} {wi[2]:>5.1%} {wi[3]:>5.1%} {wi[7]:>5.1%}")

print("\nThe quality-first choice is the low-risk end: deep buffer, low bust,")
print("slower pass. Speed here is an OUTPUT of opportunity density, not a dial.")

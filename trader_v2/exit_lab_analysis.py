#!/usr/bin/env python3
"""
V42 exit lab. E[R] is the wrong ranking metric for a prop evaluation --
what matters is lambda = 2E/sigma^2, because the account has a hard floor.
Computes lambda and pass probability for every exit rule.
"""
import math, sys
sys.path.insert(0,'trader')
from prop_rules import LUCIDFLEX
from montecarlo import run
a = LUCIDFLEX["50K"]

# rule: (E[R], win%, avgWin, avgLoss)   MGC short, room>=10R, n=200, 2.8/day
RULES = {
 "H1 fixed 1R":     (-0.1305, 0.515, 0.83, -1.16),
 "H2 fixed 2R":     ( 0.0995, 0.420, 1.83, -1.15),
 "H3 fixed 3R":     ( 0.2195, 0.345, 2.82, -1.15),
 "H4 fixed 5R":     ( 0.3395, 0.250, 4.81, -1.15),
 "H5 destination":  ( 0.2368, 0.090,14.34, -1.16),
 "H6 trail 2R/1R":  ( 0.1764, 0.420, 2.01, -1.15),
 "H7 partial+dest": ( 0.2629, 0.420, 2.22, -1.15),
 "H8 REVERSAL":     ( 0.4172, 0.145, 9.69, -1.16),
 "H9 ride":         ( 0.5393, 0.065,24.98, -1.16),
 "H10 time 48b":    ( 0.0222, 0.100,10.62, -1.16),
}
N, TPD, RDOL = 200, 2.8, 42.0

print("Two-point approximation of each rule's R distribution.\n")
print(f"{'rule':>16} {'E[R]':>8} {'sd':>7} {'lambda':>8} {'SE':>7} {'t':>6}")
best = None
for k,(E,w,aw,al) in RULES.items():
    e2 = w*aw*aw + (1-w)*al*al
    sd = math.sqrt(max(1e-9, e2 - E*E))
    lam = 2*E/(sd*sd)
    se  = sd/math.sqrt(N)
    print(f"{k:>16} {E:>+8.4f} {sd:>7.2f} {lam:>8.4f} {se:>7.3f} {E/se:>+6.2f}")
    if best is None or lam > best[1]:
        best = (k, lam, E, w, aw, al, sd)

print(f"\n  highest lambda: {best[0]}  (lambda={best[1]:.4f}, E={best[2]:+.3f}, sd={best[6]:.2f})")
print("  Raw E[R] favours H9 'ride', but its 6.5% hit rate and 25R winners give")
print("  it enormous variance -- against a hard floor that is the wrong trade.\n")

print("="*78)
print("Pass probability, verified LucidFlex trailing-MLL rules, 4,000 runs.")
print(f"MGC short, room>=10R, {TPD}/day, R = ${RDOL:.0f} per micro contract.\n")
print(f"{'rule':>16} {'size':>7} {'buffer':>8} {'pass':>7} {'bust':>6} {'med d':>7} {'<=7d':>7}")
for k in ("H2 fixed 2R","H4 fixed 5R","H7 partial+dest","H8 REVERSAL","H9 ride"):
    E,w,aw,al = RULES[k]
    for ctr in (3,5,8):
        r = RDOL*ctr
        # model as a two-outcome bet with the empirical win rate and payoff
        res = run(a, w, aw/abs(al), max(1,int(round(TPD))), r*abs(al), n=4000,
                  max_days=250, daily_target_days=20, daily_stop_R=99.0)
        print(f"{k:>16} {ctr:>4} mic {a.max_loss_limit/(r*abs(al)):>7.1f}R "
              f"{res['pas']:>6.1%} {res['bust']:>5.1%} {str(res['med']):>7} "
              f"{res['within'][7]:>6.1%}")
    print()

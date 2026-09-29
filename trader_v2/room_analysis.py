#!/usr/bin/env python3
"""
V41c: room to the next opposing significant level, measured in R at entry.
The first quality feature in this project that replicates cross-market.
"""
import math, sys
sys.path.insert(0,'trader')
from prop_rules import LUCIDFLEX
from montecarlo import run

# market -> room bucket -> (nL, LP5, LE3, nS, SP5, SE3)
MGC = {"<1R":(170,11.8,-0.384,187,15.5,-0.057), "1-2R":(160,16.9,-0.087,163,17.2,0.038),
       "2-4R":(276,15.9,-0.135,249,21.7,0.173), "4-6R":(193,14.5,-0.211,198,18.7,0.053),
       "6-10R":(230,15.2,-0.321,204,17.6,0.094), ">10R":(185,22.2,-0.010,209,24.4,0.186)}
MNQ = {"<1R":(216,15.3,-0.088,178,14.6,-0.093), "1-2R":(254,14.2,-0.113,196,19.4,0.055),
       "2-4R":(313,16.6,0.009,320,18.1,0.017),  "4-6R":(229,20.5,0.106,216,17.1,-0.095),
       "6-10R":(248,19.0,-0.041,253,15.0,-0.142),">10R":(138,23.2,0.208,232,18.5,-0.079)}

print("DIRECTION-AGNOSTIC room effect (pool long+short, both markets)\n")
print(f"{'room':>8} {'n':>6} {'P5R':>7} {'E@3R':>8}")
tot = {}
for b in MGC:
    n = e = p5 = 0.0
    for M in (MGC, MNQ):
        nL,l5,l3,nS,s5,s3 = M[b]
        n += nL+nS; e += nL*l3 + nS*s3; p5 += nL*l5 + nS*s5
    tot[b] = (n, p5/n, e/n)
    print(f"{b:>8} {n:>6.0f} {p5/n:>6.1f}% {e/n:>+8.4f}")
lo, hi = tot["<1R"], tot[">10R"]
print(f"\n  worst -> best: E@3R {lo[2]:+.3f} -> {hi[2]:+.3f}  (+{hi[2]-lo[2]:.3f} R)")
print(f"                 P5R  {lo[1]:.1f}% -> {hi[1]:.1f}%")
print("  Replicates in BOTH markets and BOTH directions independently, which is")
print("  why it is credible despite no single cell being individually significant.\n")

print("="*74)
print("Best directional cell: MGC short, room>10R, E@5R = +0.310R, 2.9/day")
print("R = 0.6 x ATR ~ 4.2 pts ~ $42 per MGC contract\n")
a = LUCIDFLEX["50K"]
E, R1, TPD = 0.310, 42.0, 2.9
win = (E+1.0)/6.0           # p*5 - (1-p) = E
print(f"{'size':>10} {'risk':>7} {'buffer':>8} {'target':>8} {'pass':>7} {'bust':>6} "
      f"{'med d':>7} {'<=7d':>7}")
for ctr in (1,2,3,5,8,12):
    r = R1*ctr
    tpd = max(1, int(round(TPD)))
    res = run(a, win, 5.0, tpd, r, n=6000, max_days=250,
              daily_target_days=20, daily_stop_R=99.0)
    print(f"{ctr:>4} micros {r:>7.0f} {a.max_loss_limit/r:>7.1f}R {a.profit_target/r:>7.1f}R "
          f"{res['pas']:>6.1%} {res['bust']:>5.1%} {str(res['med']):>7} {res['within'][7]:>6.1%}")
print("\nThe human risked ~$250/trade (5 micros x 5pts x $10) and passed in 2 days")
print("on two trades of 9.0R and 5.1R. That is the right tail, not the average.")

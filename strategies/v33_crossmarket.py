#!/usr/bin/env python3
"""
V33 cross-market sign test on the unconditional fade.

Fade a long-side momentum trigger (go short), stop 1.5xATR(14), target 2R, 5m.
Gross mean R per trade, per market. Up to 4 concurrent trades share the slot
pool, so effective n is deflated by 4.
"""
import math
from statistics import mean, stdev

# market -> (pooled gross R_fade, n)
M = {
 "XAUUSD": (0.0930, 1946), "MNQ1!": (0.0182, 1983), "ES1!":  (0.0301, 1957),
 "CL1!":   (0.0686, 1968), "6E1!":  (0.1635, 1939), "SI1!":  (0.1240, 1967),
 "ZN1!":   (0.1688, 1422), "BTCUSD":(0.0087, 2061),
}
OVERLAP = 4.0
SD_TRADE = 1.43   # sd of a 2:1 bet at ~35% win

print(f"{'market':>9} {'n':>6} {'gross R':>9}")
for k,(r,n) in M.items():
    print(f"{k:>9} {n:>6} {r:>+9.4f}")

vals = [v[0] for v in M.values()]
N    = sum(v[1] for v in M.values())
wm   = sum(v[0]*v[1] for v in M.values())/N
pos  = sum(1 for v in vals if v > 0)

print(f"\npositive on {pos}/{len(vals)} markets"
      f"   sign test p = {0.5**len(vals):.4f}")
print(f"n-weighted pooled gross edge: {wm:+.4f} R   (total n = {N:,})")

# within-market t: pooled trades, deflated for overlap
se_w = SD_TRADE/math.sqrt(N/OVERLAP)
print(f"  pooled-trade t = {wm/se_w:+.2f}   (SE {se_w:.4f}, effective n {N/OVERLAP:,.0f})")

# across-market t: each market is ONE observation. This is the conservative
# test -- it does not assume trades within a market are independent.
m, s = mean(vals), stdev(vals)
se_m = s/math.sqrt(len(vals))
print(f"  across-market t = {m/se_m:+.2f}  (mean {m:+.4f}, sd {s:.4f}, df {len(vals)-1})")
print("  NOTE: ES/MNQ and XAU/SI are correlated pairs, so the true df is nearer")
print("        5-6 than 7 and the across-market t is optimistic.")

print(f"\ncost_R at stop = 1.5xATR(5m):")
for name, atr_pts, ptval, rt in (("MGC gold", 2.5, 10.0, 1.20),
                                 ("MNQ nasdaq", 12.0, 2.0, 1.10),
                                 ("MES s&p", 2.5, 5.0, 1.10)):
    stop = 1.5*atr_pts
    print(f"  {name:>11}: stop {stop:.2f} pts = ${stop*ptval:6.2f}/contract"
          f"   cost_R = {rt/(stop*ptval):.4f}")
print(f"\n  net edge at cost_R 0.030: {wm-0.030:+.4f} R")

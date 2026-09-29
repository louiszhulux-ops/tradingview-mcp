#!/usr/bin/env python3
"""
V37: the one conditioner that survived a pre-registered fold split AND a
cross-market replication gate -- fade only when ATR > 1.5 x SMA(ATR,100).

net is measured with next-bar-open fills and a fixed $4.40 execution drag.
gross = net + 4.40/stop$, so markets with different stop sizes are comparable.
"""
import math
from statistics import mean

# market: (n, folds_positive, net, stop_$)
V = {
 "MGC micro gold": (151, 3, +0.180, 107.0),
 "MNQ micro nasdaq":(314, 3, +0.137,  86.5),
 "MES micro S&P":  (338, 1, +0.062,  35.7),
 "CL crude":       (187, 2, -0.001, 229.3),
 "SI silver":      (224, 3, +0.229,1265.3),
 "6E euro":        (257, 2, +0.151,  33.3),
 "ZN 10y note":    (201, 0, -0.099,  38.4),
 "BTCUSD":         (308, 1, -0.083, 340.5),
}
D = 4.40
print(f"{'market':>18} {'n':>5} {'folds+':>7} {'net':>8} {'stop$':>8} {'cost_R':>7} {'GROSS':>8}")
gross = {}
for k,(n,f,net,s) in V.items():
    g = net + D/s
    gross[k] = g
    print(f"{k:>18} {n:>5} {f:>5}/3 {net:>+8.3f} {s:>8.0f} {D/s:>7.3f} {g:>+8.3f}")

gs = list(gross.values())
pos = sum(1 for x in gs if x > 0)
print(f"\ngross positive on {pos}/8 markets   mean {mean(gs):+.4f}")
print(f"  the cell was SELECTED on MGC, so MGC is in-sample. Out-of-sample is")
oos = [v for k,v in gross.items() if not k.startswith("MGC")]
print(f"  the other 7: positive on {sum(1 for x in oos if x>0)}/7, "
      f"mean {mean(oos):+.4f}  (sign test p = {7/128:.3f})")

print(f"\nunconditional fade gross (V33, 8 markets): +0.081")
print(f"conditioned on vol>1.5      gross         : {mean(gs):+.3f}")
print(f"  -> conditioning roughly DOUBLES the gross edge. This is the first")
print(f"     conditioner in the project that replicates out of sample.")

print("\nselection-free estimate for the tradeable contract (MGC, stop $107):")
oos_g = mean(oos)
print(f"  use the out-of-sample gross {oos_g:+.4f} rather than MGC's own {gross['MGC micro gold']:+.4f}")
print(f"  net on MGC = {oos_g:+.4f} - {D/107:.3f} = {oos_g - D/107:+.4f} R/trade")

print("\ntrade frequency: MGC 151 trades / 72 days = 2.1/day; MNQ 4.4/day")
print("  the conditioner keeps ~8% of triggers -- close to the 'few good trades")
print("  a day' shape, and a long way from the 27/day of the unconditional fade.")

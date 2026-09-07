#!/usr/bin/env python3
"""
Route 1 tested: does correcting the cost assumption close the gap?

The old flat 0.08R was wrong -- badly, and in an interesting direction. Real
cost in R is cost_per_contract / (stop x pointValue), which varies 5x across
instruments and moves with price level. Measured, not assumed.
"""
# per market, 15m, RR 1.0: (cost per contract $, measured costR, gross meanR)
M = {
    "MGC gold":   (2.04, 0.0213, -0.0138),
    "MNQ nasdaq": (1.54, 0.0207, -0.0295),
    "MCL crude":  (2.04, 0.0904, -0.0205),
    "6E euro":    (7.29, 0.1135, -0.0196),
}
print(f"{'market':>12} {'$/contract RT':>14} {'cost in R':>10} {'GROSS meanR':>12} {'net':>9}")
for k, (c, cr, g) in M.items():
    print(f"{k:>12} {c:>14.2f} {cr:>10.4f} {g:>+12.4f} {g - cr:>+9.4f}")

gross = sum(v[2] for v in M.values()) / len(M)
cost  = sum(v[1] for v in M.values()) / len(M)
print(f"\naverage gross expectancy across 4 markets, 10 signals: {gross:+.4f} R")
print(f"average measured cost:                                 {cost:+.4f} R")
print(f"average net:                                           {gross-cost:+.4f} R")

print("\n--- what the correction did and did not do ---")
print(f"old assumption          0.0800 R")
print(f"measured, gold 15m      0.0213 R   -> was 3.8x too high")
print(f"measured, crude 15m     0.0904 R   -> was slightly too LOW")
print(f"measured, euro 15m      0.1135 R   -> was 1.4x too low")
print()
print("So the flat number was not merely wrong, it was wrong in different")
print("directions per instrument. Cost in R is set by ATR x pointValue against")
print("a fixed dollar fee, so it varies 5x across these four markets and drifts")
print("as price level changes. Gold and Nasdaq are cheap to trade in R terms;")
print("crude and euro are 4-5x more expensive for the same nominal fee.")
print()
print("--- but the route is closed anyway ---")
print("GROSS expectancy -- before ANY costs -- is negative in all four markets.")
print("Cutting fees to zero still leaves these entries unprofitable. There is no")
print("hidden edge being eaten by costs; the entries are slightly worse than")
print("random, which is what adverse selection looks like: you enter after the")
print("move, at a worse price, and the immediate next tick is against you.")

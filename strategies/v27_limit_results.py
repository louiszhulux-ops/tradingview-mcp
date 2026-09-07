#!/usr/bin/env python3
"""
Limit orders vs market orders: does providing liquidity beat taking it?

V26 measured the one consistent effect in the project: gross expectancy of
about -0.02R across four markets and ten triggers, BEFORE any fees. Every one
of those triggers was a market order fired after a bar had already moved.
This tests the opposite class -- resting limit orders, filled only if price
comes to you.
"""
# gross mean R (costs added back), 15m, RR 1:1
mkt   = {"MGC":-0.0138, "MNQ":-0.0295, "MCL":-0.0205, "6E":-0.0196}
lim1  = {"MGC":+0.0047, "MNQ":-0.0428, "MCL":+0.0030, "6E":+0.0059}  # depth 1 ATR
lim3  = {"MGC":+0.0137, "MNQ":-0.0377, "MCL":+0.0099, "6E":+0.0092}  # depth 3 ATR

print("GROSS expectancy in R (before any costs)")
print(f"{'market':>7} {'market ord':>11} {'limit d=1':>10} {'limit d=3':>10} {'lim3 - mkt':>11}")
for k in mkt:
    print(f"{k:>7} {mkt[k]:>+11.4f} {lim1[k]:>+10.4f} {lim3[k]:>+10.4f} {lim3[k]-mkt[k]:>+11.4f}")
am = sum(mkt.values())/4; a1 = sum(lim1.values())/4; a3 = sum(lim3.values())/4
print(f"{'MEAN':>7} {am:>+11.4f} {a1:>+10.4f} {a3:>+10.4f} {a3-am:>+11.4f}")

print("\nthe SMA +/- 3xATR slot specifically, both directions (the control):")
d3 = {"MGC":(+0.0182,+0.0093), "MNQ":(-0.0387,-0.0632),
      "MCL":(-0.0696,-0.0428), "6E":(-0.0940,-0.1126)}
print(f"{'market':>7} {'long':>9} {'short':>9} {'both +?':>9}")
ok = 0
for k,(l,s) in d3.items():
    good = l > 0 and s > 0
    ok += good
    print(f"{k:>7} {l:>+9.4f} {s:>+9.4f} {str(good):>9}")
print(f"\nboth directions positive in {ok}/4 markets -- needed 3/4")

print("\n--- what is real and what is not ---")
print(f"REAL: switching from market to limit entry lifts gross expectancy by")
print(f"      {a3-am:+.4f}R on average, and turns it positive in 3 of 4 markets.")
print(f"      That is the adverse-selection penalty being removed. It is a")
print(f"      structural, direction-neutral property of the order type.")
print()
print(f"NOT REAL: the depth-3 result on gold. It peaks at depth 3 and reverses")
print(f"      at depth 5, and does not replicate on any other market.")
print()
print(f"THE PROBLEM: gross of {a3:+.4f}R still does not cover costs of")
print(f"      0.021R (gold) to 0.118R (euro). Removing adverse selection gets")
print(f"      you to approximately zero, not to profit.")

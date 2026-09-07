#!/usr/bin/env python3
"""
Setup library statistics (§30) and the cross-market validation (§33/§40).

The in-sample temptation is to keep the five setups that came out positive on
gold. That is selection, not evidence. The test is whether the SAME setups are
positive on a market they were not chosen on.
"""
# (n, win%, meanR) per setup, no-chop gate, 5m
GOLD = {
 "S1 pullback L": (373, 38.6, -0.101), "S1 pullback S": (440, 42.5, +0.009),
 "S2 retest L":   (543, 38.1, -0.129), "S2 retest S":   (674, 38.9, -0.109),
 "S3 fadeSweep L":(330, 35.8, -0.158), "S3 fadeSweep S":(351, 44.4, +0.065),
 "S4 followBrk L":(1066,38.6, -0.087), "S4 followBrk S":(1144,42.4, -0.001),
 "S5 ORB L":      (24,  54.2, +0.126), "S5 ORB S":      (28,  50.0, +0.172),
 "S6 vwapRecl L": (126, 34.9, -0.151), "S6 vwapRecl S": (118, 47.5, +0.141),
}
MNQ = {
 "S1 pullback L": (407, 38.1, -0.105), "S1 pullback S": (352, 35.2, -0.153),
 "S2 retest L":   (608, 37.8, -0.114), "S2 retest S":   (601, 39.1, -0.072),
 "S3 fadeSweep L":(342, 42.7, +0.019), "S3 fadeSweep S":(269, 39.0, -0.070),
 "S4 followBrk L":(1065,39.1, -0.074), "S4 followBrk S":(1098,39.3, -0.058),
 "S5 ORB L":      (34,  47.1, +0.109), "S5 ORB S":      (31,  48.4, +0.073),
 "S6 vwapRecl L": (149, 43.6, +0.041), "S6 vwapRecl S": (132, 41.7, +0.015),
}

def pool(d):
    n = sum(v[0] for v in d.values())
    return sum(v[0]*v[2] for v in d.values())/n, n

print("SETUP LIBRARY -- gold (selection) vs nasdaq (validation)\n")
print(f"{'setup':>16} {'gold n':>7} {'gold R':>8} {'mnq n':>7} {'mnq R':>8} {'both +?':>8}")
sel = []
for k in GOLD:
    g, m = GOLD[k], MNQ[k]
    both = g[2] > 0 and m[2] > 0
    if g[2] > 0:
        sel.append(k)
    print(f"{k:>16} {g[0]:>7} {g[2]:>+8.3f} {m[0]:>7} {m[2]:>+8.3f} {str(both):>8}")

gm, gn = pool(GOLD); mm, mn = pool(MNQ)
print(f"\nwhole library pooled: gold {gm:+.4f} (n={gn})   nasdaq {mm:+.4f} (n={mn})")

print(f"\nsetups positive on GOLD (the in-sample selection): {len(sel)}")
for k in sel:
    print(f"    {k:>16}  gold {GOLD[k][2]:+.3f}  ->  nasdaq {MNQ[k][2]:+.3f}")
sn = sum(GOLD[k][0] for k in sel)
sg = sum(GOLD[k][0]*GOLD[k][2] for k in sel)/sn
mn_ = sum(MNQ[k][0] for k in sel)
sm = sum(MNQ[k][0]*MNQ[k][2] for k in sel)/mn_
print(f"\n  those setups, in-sample on gold      : {sg:+.4f} R  (n={sn})")
print(f"  the SAME setups, out-of-sample on MNQ: {sm:+.4f} R  (n={mn_})")
print(f"  shrinkage: {sg-sm:+.4f} R  ({(1-sm/sg)*100:.0f}% of the edge disappears)")

kept = [k for k in sel if MNQ[k][2] > 0]
print(f"\n  survive on both: {len(kept)}/{len(sel)} -> {kept}")
if kept:
    kn = sum(GOLD[k][0]+MNQ[k][0] for k in kept)
    km = sum(GOLD[k][0]*GOLD[k][2]+MNQ[k][0]*MNQ[k][2] for k in kept)/kn
    print(f"  pooled over both markets: {km:+.4f} R  (n={kn})")
    print(f"\n  needed for a 7-day pass: +0.179R")
    print(f"  needed for a 5-day pass: +0.250R")
    print(f"  -> {'CLEARS' if km >= 0.179 else 'SHORT OF'} the 7-day bar")

print("\nlong/short asymmetry check (drift control):")
for lbl, d in (("gold", GOLD), ("nasdaq", MNQ)):
    ls = [(k, d[k][2]) for k in d if k.endswith(" L")]
    ss = [(k, d[k][2]) for k in d if k.endswith(" S")]
    lm = sum(v for _, v in ls)/len(ls); sm2 = sum(v for _, v in ss)/len(ss)
    print(f"  {lbl:>7}: long mean {lm:+.3f}  short mean {sm2:+.3f}  gap {sm2-lm:+.3f}")
print("  gold shorts beat longs in 6/6 pairs; nasdaq does NOT repeat that,")
print("  so gold's short bias is sample drift rather than a property of the setups.")

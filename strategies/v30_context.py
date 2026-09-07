#!/usr/bin/env python3
"""
Does CONDITIONING on regime + location change expectancy?

Trigger held constant and neutral (EMA20 cross, both directions, fires
constantly). Only the CONTEXT varies. If context carries information the cells
separate; if not, context is decoration.

4 markets, 5m. Cell = (direction, regime, at-level vs mid-range).
"""
# (n, meanR) keyed [market][dir][regime][loc]  loc 0 = @LEVEL, 1 = mid
D = {
"MGC": {"L":{"with":[(44,-0.108),(104,-0.220)], "cntr":[(101,-0.057),(119,-0.148)],
             "weak":[(174,-0.025),(222,-0.071)], "chop":[(225,-0.088),(225,-0.097)]},
        "S":{"with":[(58,+0.121),(95,+0.013)],  "cntr":[(85,+0.046),(97,-0.045)],
             "weak":[(170,-0.029),(246,+0.002)],"chop":[(219,-0.017),(250,-0.011)]}},
"MNQ": {"L":{"with":[(58,+0.066),(82,-0.189)],  "cntr":[(85,+0.125),(115,-0.077)],
             "weak":[(185,-0.076),(220,+0.033)],"chop":[(253,-0.176),(244,-0.010)]},
        "S":{"with":[(55,+0.123),(90,-0.042)],  "cntr":[(72,-0.324),(99,-0.175)],
             "weak":[(186,+0.072),(206,-0.074)],"chop":[(271,+0.002),(271,-0.054)]}},
"MES": {"L":{"with":[(60,-0.401),(89,-0.098)],  "cntr":[(76,+0.025),(102,-0.221)],
             "weak":[(214,-0.269),(215,-0.225)],"chop":[(269,-0.282),(266,-0.216)]},
        "S":{"with":[(44,-0.259),(69,+0.001)],  "cntr":[(92,-0.151),(99,-0.153)],
             "weak":[(202,-0.186),(220,-0.174)],"chop":[(275,-0.127),(262,-0.208)]}},
"MCL": {"L":{"with":[(61,-0.016),(83,-0.226)],  "cntr":[(96,-0.227),(113,-0.033)],
             "weak":[(193,-0.299),(199,-0.217)],"chop":[(258,-0.077),(198,-0.193)]},
        "S":{"with":[(67,+0.027),(85,+0.049)],  "cntr":[(85,+0.034),(99,-0.038)],
             "weak":[(167,-0.074),(197,-0.012)],"chop":[(267,-0.227),(218,-0.093)]}},
}
REG = ["with","cntr","weak","chop"]

def pooled(pairs):
    n = sum(p[0] for p in pairs)
    return (sum(p[0]*p[1] for p in pairs)/n, n) if n else (0,0)

print("=== LOCATION EFFECT (@LEVEL minus mid-range), by regime ===")
print("cost affects both sides equally and cancels in the difference\n")
print(f"{'regime':>7} " + " ".join(f"{m:>16}" for m in D) + f" {'pooled':>9}")
for r in REG:
    cells, allp_at, allp_mid = [], [], []
    for m in D:
        d = []
        for side in ("L","S"):
            at, mid = D[m][side][r]
            d.append(at[1]-mid[1])
            allp_at.append(at); allp_mid.append(mid)
        cells.append(f"L{d[0]:+.3f} S{d[1]:+.3f}".rjust(16))
    a,_ = pooled(allp_at); b,_ = pooled(allp_mid)
    print(f"{r:>7} " + " ".join(cells) + f" {a-b:>+9.3f}")

print("\n=== the with-trend @LEVEL cell, which is the discretionary core ===")
at, mid = [], []
for m in D:
    for side in ("L","S"):
        a, md = D[m]["with"][0], D[m]["with"][1]
        at.append(a); mid.append(md)
ma, na_ = pooled(at); mm, nm = pooled(mid)
print(f"  with-trend @LEVEL : {ma:+.4f} R  (n={na_})")
print(f"  with-trend mid    : {mm:+.4f} R  (n={nm})")
print(f"  difference        : {ma-mm:+.4f} R")

print("\n  per market (location effect in the with-trend regime):")
for m in D:
    a = [D[m][s]["with"][0] for s in ("L","S")]
    b = [D[m][s]["with"][1] for s in ("L","S")]
    x,_ = pooled(a); y,_ = pooled(b)
    print(f"    {m}: @LVL {x:+.3f}  mid {y:+.3f}  diff {x-y:+.3f}  {'HELPS' if x>y else 'HURTS'}")

print("\n=== chop regime: does location matter there? ===")
a = [D[m][s]["chop"][0] for m in D for s in ("L","S")]
b = [D[m][s]["chop"][1] for m in D for s in ("L","S")]
x,_ = pooled(a); y,_ = pooled(b)
print(f"  chop @LEVEL {x:+.4f}   chop mid {y:+.4f}   diff {x-y:+.4f}")
print("  (a trader would predict location matters LESS in chop -- it does)")

#!/usr/bin/env python3
"""
V34 fade-on-limit: does a resting limit recover the cost that eats the edge?

Within each market all four offsets see an IDENTICAL trigger set (the 'placed'
count is the same down every row), so the offset comparison is clean. Absolute
levels are NOT comparable to V33: V34 needs room in eight cells at once and so
skips 60-70% of triggers, against 9-26% in V33.
"""
import math
from statistics import mean, stdev

# market -> {offset: (R_fade, R_foll, fill%)},  placed
V34 = {
 "XAUUSD": (626, {0:(0.0780,-0.0925,99.5), 0.25:(0.0967,-0.0853,88.0), 0.50:(0.1391,-0.0815,73.2), 0.75:(0.1591,-0.0681,61.3)}),
 "MNQ1!":  (558, {0:(0.0951,-0.0702,99.5), 0.25:(0.1802,-0.0396,87.1), 0.50:(0.1984,-0.0703,77.2), 0.75:(0.2433,-0.0843,62.0)}),
 "ES1!":   (559, {0:(0.0294,-0.0730,99.8), 0.25:(0.0000,-0.0603,85.7), 0.50:(-0.0545,-0.0804,72.5), 0.75:(-0.0268,-0.0870,59.4)}),
 "CL1!":   (679, {0:(0.0495,-0.0391,98.7), 0.25:(0.0342,-0.0616,85.4), 0.50:(0.0188,-0.0447,72.8), 0.75:(0.0915,-0.0683,59.8)}),
 "6E1!":   (655, {0:(0.0398,-0.1089,97.4), 0.25:(0.0006,-0.0720,84.3), 0.50:(0.0305,-0.0705,72.1), 0.75:(-0.0172,-0.1012,60.9)}),
 "SI1!":   (708, {0:(0.0615,-0.1200,95.9), 0.25:(0.0635,-0.1234,83.1), 0.50:(0.0759,-0.1569,71.6), 0.75:(0.1012,-0.2153,60.3)}),
 "ZN1!":   (446, {0:(0.0757,-0.1315,98.2), 0.25:(0.1006,-0.1060,78.5), 0.50:(0.1834,-0.0691,63.0), 0.75:(0.1730,-0.0024,47.5)}),
 "BTCUSD": (773, {0:(-0.1092,0.0855,96.8), 0.25:(-0.1480,0.0373,82.5), 0.50:(-0.1054,0.0211,73.4), 0.75:(-0.1484,0.0196,62.9)}),
}
V33 = {"XAUUSD":0.0930,"MNQ1!":0.0182,"ES1!":0.0301,"CL1!":0.0686,
       "6E1!":0.1635,"SI1!":0.1240,"ZN1!":0.1688,"BTCUSD":0.0087}

print("A. DOES THE LIMIT OFFSET HELP?  (within-market, identical trigger set)\n")
print(f"{'market':>9} {'off 0':>8} {'off .25':>8} {'off .50':>8} {'off .75':>8} | "
      f"{'d(.50)':>8} {'d(.75)':>8}")
d50, d75 = [], []
for k,(pl,rows) in V34.items():
    r0 = rows[0][0]
    a,b = rows[0.50][0]-r0, rows[0.75][0]-r0
    d50.append(a); d75.append(b)
    print(f"{k:>9} {r0:>+8.4f} {rows[0.25][0]:>+8.4f} {rows[0.50][0]:>+8.4f} "
          f"{rows[0.75][0]:>+8.4f} | {a:>+8.4f} {b:>+8.4f}")
for lbl, d in (("0.50xATR", d50), ("0.75xATR", d75)):
    p = sum(1 for x in d if x > 0)
    t = mean(d)/(stdev(d)/math.sqrt(len(d)))
    print(f"\n  offset {lbl}: improves on {p}/8 markets, mean {mean(d):+.4f}, "
          f"across-market t = {t:+.2f}")
print("\n  VERDICT: the offset effect does NOT replicate. Gold, MNQ and ZN show it")
print("  strongly; ES, CL and 6E go the other way. Sign test p = 0.36 / 0.14.")
print("  Adopting 0.5xATR here would be picking the markets that agreed with me.")

print("\n\nB. THE FOLLOW CONTROL\n")
foll = [rows[0][1] for _,rows in V34.values()]
print(f"  R_follow at offset 0 is negative on {sum(1 for x in foll if x<0)}/8 "
      f"markets, mean {mean(foll):+.4f}")
print("  -> the fade thesis itself holds up; it is the limit refinement that does not.")

print("\n\nC. SAMPLE-SELECTION CHECK vs V33\n")
print(f"{'market':>9} {'V33 (mkt)':>10} {'V34 off0':>10} {'diff':>9}")
dif = []
for k,(pl,rows) in V34.items():
    d = rows[0][0]-V33[k]; dif.append(d)
    print(f"{k:>9} {V33[k]:>+10.4f} {rows[0][0]:>+10.4f} {d:>+9.4f}")
print(f"\n  V34's offset-0 is LOWER on {sum(1 for x in dif if x<0)}/8 markets "
      f"(mean {mean(dif):+.4f}).")
print("  V34 skips 60-70% of triggers to keep eight cells free, V33 only 9-26%.")
print("  So V34's ABSOLUTE levels are a selected subsample; only its within-table")
print("  offset comparison is trustworthy. V33 remains the estimate of record.")

print("\n\nD. CORRECTION TO MY EARLIER COST ARITHMETIC\n")
print("  I paired the ALL-MARKET pooled gross edge (+0.0807) with each market's")
print("  OWN cost. That is wrong: the edge has to be the edge of the market you")
print("  actually trade. Redone per market, with V26's measured costs:\n")
COST = {"XAUUSD":0.0445, "MNQ1!":0.0438, "CL1!":0.1239, "6E1!":0.1505}
print(f"{'market':>9} {'gross(V33)':>11} {'cost_R':>8} {'NET':>9} {'t (own market)':>16}")
for k,c in COST.items():
    g = V33[k]; n = 1946 if k=="XAUUSD" else 1983 if k=="MNQ1!" else 1968 if k=="CL1!" else 1939
    se = 1.43/math.sqrt(n/4)
    print(f"{k:>9} {g:>+11.4f} {c:>8.4f} {g-c:>+9.4f} {g/se:>+16.2f}")
print("\n  Only gold is positive after cost, and gold on its own is t = 1.43.")
print("  The markets with the big gross edges (6E +0.164, CL +0.069) are exactly")
print("  the ones whose cost_R (0.15, 0.12) destroys them. That inverse pairing")
print("  is the single most important fact in this whole line of work.")

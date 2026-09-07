#!/usr/bin/env python3
"""
Phase 2 -- select the ex-ante bias model on folds A+B ONLY.
Selection rule was fixed in PHASE2_PROTOCOL.md before this ran:
  most positive instrument x direction cells; tie-break pooled E[R];
  second tie-break fill count.
Fold C is not opened here.
"""
import math

BIAS = ["B0 control", "B1 4H trend", "B2 4H struct", "B3 prev-day", "B4 disp", "B5 B1&B2"]
COMPLEX = {"MGC": "metals", "SIL": "metals", "MNQ": "equity", "MCL": "energy", "6E": "FX"}

# cell -> list over B0..B5 of (armed, n, E[R], win%)
D = {
 "MGC long": [(790,130, 0.133,21.5),(151, 23, 0.359,26.1),(254, 34, 0.232,23.5),
              (182, 25,-0.450,12.0),(280, 37,-0.040,18.9),(130, 20, 0.597,30.0)],
 "MGC short":[(734,146, 0.317,24.7),(553,114, 0.469,27.2),(416, 85, 0.547,28.2),
              (242, 50,-0.304,14.0),(308, 65, 0.140,21.5),(404, 83, 0.516,27.7)],
 "SIL long": [(902,159, 0.046,18.2),(159, 29,-0.232,13.8),(325, 54,-0.500, 9.3),
              (251, 39,-0.438,10.3),(312, 47,-0.160,14.9),(140, 24,-0.312,12.5)],
 "SIL short":[(681,154,-0.192,14.3),(569,130,-0.123,15.4),(400, 84,-0.117,15.5),
              (188, 33, 0.049,18.2),(310, 71,-0.118,15.5),(388, 82,-0.095,15.9)],
 "MNQ long": [(820,122, 0.272,23.0),(373, 42, 0.443,26.2),(458, 52, 0.370,25.0),
              (254, 20,-0.550,10.0),(364, 47,-0.089,17.0),(284, 26, 0.701,30.8)],
 "MNQ short":[(975,183, 0.123,21.3),(499, 86, 0.325,24.4),(356, 70, 0.071,20.0),
              (269, 46,-0.376,13.0),(312, 59,-0.123,16.9),(277, 50, 0.190,22.0)],
 "MCL long": [(866,147, 0.055,23.8),(325, 66, 0.009,22.7),(282, 49,-0.020,22.4),
              (173, 30, 0.246,26.7),(164, 26, 0.030,23.1),(225, 43, 0.038,23.3)],
 "MCL short":[(701,120, 0.101,25.0),(474, 76, 0.070,25.0),(485, 81, 0.374,29.6),
              (255, 39, 0.179,25.6),(403, 60,-0.010,23.3),(431, 69, 0.136,26.1)],
 "6E long":  [(686,123,-0.368,13.8),(193, 35,-0.693, 8.6),(338, 72,-0.536,11.1),
              (150, 24,-0.708, 8.3),(333, 65,-0.089,18.5),(185, 33,-0.667, 9.1)],
 "6E short": [(557, 94,-0.032,19.1),(404, 73, 0.297,24.7),(295, 52, 0.076,21.2),
              (158, 29,-0.360,13.8),(183, 39, 0.675,30.8),(286, 50, 0.130,22.0)],
}
CELLS = list(D)
TGT, STOP = 5.0, -1.0

def pooled(idx, cells):
    tot = n = w = 0.0
    for c in cells:
        a_, nc, E, wp = D[c][idx]
        tot += nc * E; n += nc; w += nc * wp
    if n == 0: return 0.0, 0, 0.0, 0.0, 0.0
    E = tot / n; wp = w / n / 100.0
    var = wp*TGT*TGT + (1-wp)*STOP*STOP - E*E
    sd = math.sqrt(max(var, 1e-9))
    return E, int(n), sd, 2*E/(sd*sd), E/(sd/math.sqrt(n))

print("PHASE 2 -- ex-ante bias models, folds A+B, ten instrument x direction cells\n")
hdr = f"{'':<13}" + "".join(f"{c.replace(' short',' s').replace(' long',' l'):>10}" for c in CELLS)
print(hdr + f"{'pooled':>9}{'signs':>8}{'n':>7}{'keep%':>7}{'t':>7}")
rows = []
for i, b in enumerate(BIAS):
    line = f"{b:<13}"
    pos = 0
    for c in CELLS:
        E = D[c][i][2]
        line += f"{E:>+10.3f}"
        if E > 0: pos += 1
    E, n, sd, lam, t = pooled(i, CELLS)
    keep = 100.0*sum(D[c][i][0] for c in CELLS)/sum(D[c][0][0] for c in CELLS)
    rows.append((b, pos, E, n, keep, t, lam))
    print(line + f"{E:>+9.3f}{pos:>6}/10{n:>7}{keep:>7.1f}{t:>+7.2f}")

# complex-level cells (n-weighted within complex, per direction)
print("\nCOMPLEX x DIRECTION cells (metals pools MGC+SIL; the other three are single-instrument)")
cdirs = []
for cx in ("metals", "equity", "energy", "FX"):
    for d in ("long", "short"):
        members = [c for c in CELLS if COMPLEX[c.split()[0]] == cx and c.endswith(d)]
        cdirs.append((f"{cx} {d}", members))
hdr2 = f"{'':<13}" + "".join(f"{nm.replace('metals','met').replace('equity','eq').replace('energy','en').replace(' short',' s').replace(' long',' l'):>9}" for nm,_ in cdirs)
print(hdr2 + f"{'signs':>8}")
for i, b in enumerate(BIAS):
    line = f"{b:<13}"; pos = 0
    for nm, mem in cdirs:
        E, n, *_ = pooled(i, mem)
        line += f"{E:>+9.3f}"
        if E > 0: pos += 1
    print(line + f"{pos:>6}/8")

print("\n" + "="*100)
print("SELECTION (rule fixed in PHASE2_PROTOCOL.md before this ran):")
rows.sort(key=lambda r: (-r[1], -r[2], -r[3]))
for b, pos, E, n, keep, t, lam in rows:
    print(f"  {b:<13} cells {pos}/10   pooled E[R] {E:+.3f}   n {n:5d}   keeps {keep:5.1f}% of sweeps   t {t:+.2f}")
win = rows[0]
print(f"\n  SELECTED: {win[0]}   ({win[1]}/10 cells, pooled {win[2]:+.3f}R, n={win[3]})")

# ---------------------------------------------------------------- complement
# The honest test of a filter is not "is the kept set positive" but
# "does it separate two populations": kept vs DISCARDED.
print("\n" + "="*100)
print("DOES THE FILTER ACTUALLY SEPARATE? kept (B1) vs discarded (B0 minus B1)\n")
print(f"{'cell':>11}{'B1 kept':>10}{'n':>6}{'discarded':>12}{'n':>6}{'spread':>10}")
kn=ke=dn=de=kw=dw=0.0
seps=0
for c in CELLS:
    a0,n0,E0,w0 = D[c][0]
    a1,n1,E1,w1 = D[c][1]
    nd = n0-n1
    Ed = (n0*E0 - n1*E1)/nd if nd>0 else float('nan')
    wd = (n0*w0 - n1*w1)/nd if nd>0 else float('nan')
    print(f"{c:>11}{E1:>+10.3f}{n1:>6}{Ed:>+12.3f}{nd:>6}{E1-Ed:>+10.3f}")
    kn+=n1; ke+=n1*E1; kw+=n1*w1
    dn+=nd; de+=nd*Ed; dw+=nd*wd
    if E1 > Ed: seps += 1
Ek, Ed_ = ke/kn, de/dn
wk, wdd = kw/kn/100, dw/dn/100
sdk = math.sqrt(wk*25+(1-wk)-Ek*Ek); sdd = math.sqrt(wdd*25+(1-wdd)-Ed_*Ed_)
se = math.sqrt(sdk*sdk/kn + sdd*sdd/dn)
print(f"{'POOLED':>11}{Ek:>+10.3f}{kn:>6.0f}{Ed_:>+12.3f}{dn:>6.0f}{Ek-Ed_:>+10.3f}")
print(f"\n  kept beats discarded in {seps}/10 cells")
print(f"  difference {Ek-Ed_:+.3f}R, SE {se:.3f}, t {(Ek-Ed_)/se:+.2f}")
print(f"  90% CI on the difference: [{Ek-Ed_-1.645*se:+.3f}, {Ek-Ed_+1.645*se:+.3f}]")

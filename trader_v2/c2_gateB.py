#!/usr/bin/env python3
"""
Phase 11 C2 Gate B. Pre-registered BEFORE any expectancy was computed:
  primary  = E[R | virgin] - E[R | non-virgin], virgin = prior touches == 0
  population = prev-day + pivot levels only; Asia excluded on the Gate A
  construct-validity finding. Folds A+B. Fold C sealed.
  Gate: pooled 90% CI excludes zero AND same direction in >= 7/10 cells.
"""
import math
TGT, STOP = 5.0, -1.0

# cell -> (PDv, PDn, PVv, PVn) each (n, E, win%) ; plus asia n, cands, fills
D = {
 "MGC long": ((29,0.7840,31.0),(97,-0.4679,10.3),(215,-0.1982,15.3),(219,-0.3945,11.9), 144,774,704),
 "MGC short":((20,0.4082,25.0),(100,-0.3191,13.0),(158,-0.1356,16.5),(184,0.2500,22.8), 142,691,604),
 "SIL long": ((44,-0.6165,6.8),(151,-0.2758,12.6),(199,-0.1636,14.6),(206,-0.0761,16.0), 171,867,771),
 "SIL short":((18,-0.0310,16.7),(65,0.1625,20.0),(149,0.0852,18.8),(191,0.3086,22.5), 139,634,562),
 "MNQ long": ((30,-0.0744,16.7),(129,-0.1375,15.5),(194,-0.0427,17.5),(202,-0.1581,15.3), 170,812,725),
 "MNQ short":((32,0.2067,21.9),(133,-0.0666,17.3),(190,-0.1278,16.3),(283,-0.0882,17.0), 229,942,867),
 "MCL long": ((27,-0.1687,18.5),(118,-0.4547,13.6),(195,-0.2669,16.9),(230,-0.1576,18.7), 168,826,738),
 "MCL short":((23,-0.5796,13.0),(95,-0.1317,18.9),(162,-0.2217,17.9),(163,-0.4042,14.7), 154,692,597),
 "6E long":  ((22,1.0503,36.4),(72,-0.3115,13.9),(158,-0.0930,17.7),(181,0.0284,19.9), 162,658,595),
 "6E short": ((12,-0.5848,8.3),(61,-0.0486,18.0),(117,-0.1753,16.2),(161,0.0182,19.9), 144,558,495),
}
CELLS = list(D)
sd_of = lambda E,w: math.sqrt(max(w*TGT*TGT+(1-w)*STOP*STOP-E*E,1e-12))

def merge(parts):
    n = sum(p[0] for p in parts)
    if n == 0: return 0,0.0,0.0
    return n, sum(p[0]*p[1] for p in parts)/n, sum(p[0]*p[2] for p in parts)/n/100.0

print("=== 1. PRIMARY POPULATION / RECONCILIATION ===")
tc = sum(D[c][5] for c in CELLS); tf = sum(D[c][6] for c in CELLS)
ta_ = sum(D[c][4] for c in CELLS)
prim = sum(D[c][0][0]+D[c][1][0]+D[c][2][0]+D[c][3][0] for c in CELLS)
print(f"  candidates {tc}   fills {tf}   (matches V49/V50/V51: 7454 / 6658)")
print(f"  Asia fills excluded from the primary population: {ta_}")
print(f"  primary population (prev-day + pivot): {prim}   check {prim}+{ta_}={prim+ta_}")
print(f"  D0 and pivot-lag diagnostics were 0 in every cell (re-verified in V52)")

print("\n=== 2. VIRGIN vs NON-VIRGIN, POOLED ===")
V = merge([D[c][0] for c in CELLS] + [D[c][2] for c in CELLS])
N = merge([D[c][1] for c in CELLS] + [D[c][3] for c in CELLS])
nv,Ev,wv = V; nn,En,wn = N
sv, sn = sd_of(Ev,wv), sd_of(En,wn)
se = math.sqrt(sv*sv/nv + sn*sn/nn)
d = Ev - En
lo, hi = d-1.645*se, d+1.645*se
pfv = (wv*TGT)/((1-wv)*abs(STOP)); pfn = (wn*TGT)/((1-wn)*abs(STOP))
print(f"  virgin      n {nv:5d}   E[R] {Ev:+.4f}   win {100*wv:.1f}%   PF {pfv:.2f}")
print(f"  non-virgin  n {nn:5d}   E[R] {En:+.4f}   win {100*wn:.1f}%   PF {pfn:.2f}")
print(f"  difference  {d:+.4f}   SE {se:.4f}   90% CI [{lo:+.4f}, {hi:+.4f}]   t {d/se:+.2f}")

print("\n=== 3. TEN-CELL RESULTS ===")
print(f"{'cell':>11}{'nV':>6}{'E V':>10}{'nN':>6}{'E N':>10}{'diff':>10}{'sign':>6}")
pos = 0
for c in CELLS:
    v = merge([D[c][0], D[c][2]]); n_ = merge([D[c][1], D[c][3]])
    diff = v[1] - n_[1]
    s = "+" if diff > 0 else "-"
    if diff > 0: pos += 1
    print(f"{c:>11}{v[0]:>6}{v[1]:>+10.4f}{n_[0]:>6}{n_[1]:>+10.4f}{diff:>+10.4f}{s:>6}")
print(f"\n  virgin > non-virgin in {pos}/10 cells")

print("\n=== 4. LEVEL-TYPE DISTRIBUTIONS (descriptive) ===")
for idx,(nm,vi,ni) in enumerate((("prev-day",0,1),("pivot",2,3))):
    v = merge([D[c][vi] for c in CELLS]); n_ = merge([D[c][ni] for c in CELLS])
    tot = v[0]+n_[0]
    print(f"  {nm:>9}: n {tot:5d}   virgin {v[0]:5d} ({100*v[0]/tot:.1f}%)   "
          f"non-virgin {n_[0]:5d} ({100*n_[0]/tot:.1f}%)")
    print(f"             E[R] virgin {v[1]:+.4f}   non-virgin {n_[1]:+.4f}   diff {v[1]-n_[1]:+.4f}")

print("\n=== 5. AGE DISTRIBUTION (ageBars deciles, primary population, descriptive) ===")
AGE = {"MGC long":(5,9,12,16,21,25,35,52,128),"MGC short":(5,8,12,15,19,24,35,124,197),
       "SIL long":(5,9,14,18,25,33,43,70,153),"SIL short":(5,7,10,13,15,20,26,42,179),
       "MNQ long":(6,9,13,16,21,27,41,112,206),"MNQ short":(4,8,11,15,19,26,35,69,173),
       "MCL long":(5,8,12,16,22,29,38,86,183),"MCL short":(4,8,12,16,22,30,39,70,184),
       "6E long":(5,8,11,14,18,24,33,50,162),"6E short":(6,10,13,17,22,27,33,56,203)}
print(f"{'cell':>11}" + "".join(f"{'d'+str(i+1):>6}" for i in range(9)))
for c in CELLS:
    print(f"{c:>11}" + "".join(f"{v:>6}" for v in AGE[c]))
med = sorted(AGE[c][4] for c in CELLS)
print(f"  median-of-cells for each decile is monotone by construction; d5 (median age)"
      f" ranges {min(med)}-{max(med)} bars across cells")

print("\n=== 6. ASIA DIAGNOSTIC (excluded from the primary test) ===")
print(f"  Asia fills {ta_}   virgin 0   non-virgin {ta_}   virgin percentage 0.0%")
print("  Cause (Gate A): asiaH/asiaL are a RUNNING extreme, so bornBar lands on the")
print("  last bar that moved it and the remaining session bars count as touches.")
print("  The Asia touch counter measures the session's own formation, not later")
print("  interaction with an established level. Excluded on construct validity,")
print("  pre-registered before any expectancy was computed.")

print("\n=== 7. CONFOUNDING DIAGNOSTICS (counts only) ===")
SES = {"MGC long":((126,37,31,37,13),(120,71,72,48,5)),"MGC short":((80,32,40,22,4),(84,75,80,34,11)),
       "SIL long":((118,29,60,33,3),(172,92,57,32,4)),"SIL short":((74,25,47,18,3),(95,56,72,30,3)),
       "MNQ long":((88,52,52,29,3),(90,67,85,77,12)),"MNQ short":((83,54,51,29,5),(124,127,103,53,9)),
       "MCL long":((121,43,29,26,3),(124,85,76,52,11)),"MCL short":((62,43,54,23,3),(93,58,70,31,6)),
       "6E long":((47,56,47,22,8),(73,76,52,40,12)),"6E short":((38,27,48,9,7),(83,46,52,34,7))}
ATR = {"MGC long":(103,174,139,132),"MGC short":(67,126,108,156),"SIL long":(137,199,101,158),
       "SIL short":(88,120,77,134),"MNQ long":(90,174,130,156),"MNQ short":(87,130,133,278),
       "MCL long":(76,184,139,163),"MCL short":(103,146,78,108),"6E long":(101,141,75,111),
       "6E short":(79,110,45,111)}
sv_=[sum(SES[c][0][i] for c in CELLS) for i in range(5)]
sn_=[sum(SES[c][1][i] for c in CELLS) for i in range(5)]
lbl=("asia","london","overlap","ny","off")
print(f"  session      " + "".join(f"{l:>9}" for l in lbl))
print(f"  virgin       " + "".join(f"{v:>9}" for v in sv_))
print(f"  non-virgin   " + "".join(f"{v:>9}" for v in sn_))
print(f"  virgin share " + "".join(f"{100*sv_[i]/(sv_[i]+sn_[i]):>8.1f}%" for i in range(5)))
a=[sum(ATR[c][i] for c in CELLS) for i in range(4)]
print(f"\n  ATR above its 200-bar mean: virgin {a[0]}  non-virgin {a[1]}  "
      f"virgin share {100*a[0]/(a[0]+a[1]):.1f}%")
print(f"  ATR below its 200-bar mean: virgin {a[2]}  non-virgin {a[3]}  "
      f"virgin share {100*a[2]/(a[2]+a[3]):.1f}%")
pdv = sum(D[c][0][0] for c in CELLS); pdn = sum(D[c][1][0] for c in CELLS)
pvv = sum(D[c][2][0] for c in CELLS); pvn = sum(D[c][3][0] for c in CELLS)
print(f"\n  level type: prev-day virgin share {100*pdv/(pdv+pdn):.1f}%   "
      f"pivot virgin share {100*pvv/(pvv+pvn):.1f}%   <-- strong confound")
lv = sum(merge([D[c][0],D[c][2]])[0] for c in CELLS if c.endswith("long"))
ln = sum(merge([D[c][1],D[c][3]])[0] for c in CELLS if c.endswith("long"))
sv2 = sum(merge([D[c][0],D[c][2]])[0] for c in CELLS if c.endswith("short"))
sn2 = sum(merge([D[c][1],D[c][3]])[0] for c in CELLS if c.endswith("short"))
print(f"  direction:  long virgin share {100*lv/(lv+ln):.1f}%   short virgin share {100*sv2/(sv2+sn2):.1f}%")

print("\n=== 8. PRE-REGISTERED GATE ===")
c1 = lo*hi > 0
c2 = pos >= 7
print(f"  1. pooled 90% CI excludes zero        : {'PASS' if c1 else 'FAIL'}   [{lo:+.4f}, {hi:+.4f}]")
print(f"  2. same direction in >= 7/10 cells    : {'PASS' if c2 else 'FAIL'}   ({pos}/10)")
print(f"\n  GATE: {'PASS' if (c1 and c2) else 'FAIL'}")

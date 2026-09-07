#!/usr/bin/env python3
"""
Fold C validation of the >=10R room effect. Definition untouched, no retuning.
V48 run as committed; only the fold input changed.
"""
import math
TGT, STOP = 5.0, -1.0
DAYS = 14.5

# cell -> [(n,E,win%)] buckets <0.5,0.5-1,1-1.5,1.5-2,2-3,3-5,5-10,>=10
C = {
 "MGC long": [(3,2.909,66.7),(2,-1.042,0.0),(4,-1.045,0.0),(6,-0.077,16.7),
              (21,-0.196,14.3),(39,-0.159,15.4),(49,0.225,22.4),(33,0.310,24.2)],
 "MGC short":[(3,-1.065,0.0),(8,-0.284,12.5),(2,4.934,100.0),(8,1.175,37.5),
              (16,0.059,18.8),(38,0.026,18.4),(66,-0.747,6.1),(50,0.290,24.0)],
 "SIL long": [(6,0.949,33.3),(2,-1.012,0.0),(7,-0.176,14.3),(5,0.187,20.0),
              (22,0.062,18.2),(39,-0.110,15.4),(69,-0.432,10.1),(53,0.072,18.9)],
 "SIL short":[(7,-1.043,0.0),(2,-1.016,0.0),(6,-0.039,16.7),(5,1.386,40.0),
              (20,0.471,25.0),(35,0.160,20.0),(73,-0.060,16.4),(57,0.313,22.8)],
 "MNQ long": [(3,0.957,33.3),(5,-1.077,0.0),(3,-1.047,0.0),(7,-1.049,0.0),
              (23,-0.538,8.7),(41,0.076,19.5),(74,0.646,29.7),(34,-0.483,11.8)],
 "MNQ short":[(3,0.926,33.3),(4,0.411,25.0),(8,0.446,25.0),(6,-0.096,16.7),
              (17,0.350,23.5),(47,0.561,27.7),(80,-0.467,11.3),(60,-0.211,16.7)],
 "MCL long": [(0,0.0,0.0),(3,0.765,33.3),(6,1.872,50.0),(13,-0.687,7.7),
              (22,0.390,27.3),(42,0.732,33.3),(78,-0.059,21.8),(28,-0.817,10.7)],
 "MCL short":[(1,-1.066,0.0),(1,-1.321,0.0),(4,3.194,75.0),(3,-1.297,0.0),
              (11,-0.170,18.2),(48,-0.088,18.8),(81,0.375,28.4),(36,-0.101,22.2)],
 "6E long":  [(0,0.0,0.0),(8,-1.110,0.0),(8,-1.095,0.0),(1,-1.121,0.0),
              (17,-1.132,0.0),(41,0.151,22.0),(64,0.105,21.9),(24,0.279,25.0)],
 "6E short": [(6,0.917,33.3),(4,0.420,25.0),(7,-0.278,14.3),(12,-1.119,0.0),
              (11,-0.556,9.1),(39,0.092,20.5),(52,-0.395,13.5),(15,0.376,26.7)],
}
CELLS = list(C)
# folds A+B >=10R, for the in-sample vs out-of-sample comparison
AB10 = {"MGC long":(121,0.232,23.1),"MGC short":(146,0.354,25.3),
        "SIL long":(152,0.014,17.8),"SIL short":(140,-0.194,14.3),
        "MNQ long":(119,0.307,23.5),"MNQ short":(173,0.120,21.4),
        "MCL long":(135,-0.007,23.0),"MCL short":(117,0.077,24.8),
        "6E long":(114,-0.406,13.2),"6E short":(94,0.031,20.2)}

def agg(rows):
    n = sum(r[0] for r in rows)
    if n == 0: return 0,0.0,0.0
    return n, sum(r[0]*r[1] for r in rows)/n, sum(r[0]*r[2] for r in rows)/n/100.0

def stats(n,E,w):
    if n == 0: return 0,0,0,0,0
    sd = math.sqrt(max(w*TGT*TGT+(1-w)*STOP*STOP-E*E,1e-12)); se = sd/math.sqrt(n)
    pf = (w*TGT)/((1-w)*abs(STOP)) if w < 1 else float('inf')
    return sd, E-1.645*se, E+1.645*se, E/se, pf

print("=== 1. FOLD C VALIDATION OF >=10R (definition untouched) ===\n")
print(f"{'cell':>11}{'n':>6}{'/day':>7}{'E[R]':>9}{'win%':>7}   |  {'A+B n':>6}{'A+B E':>9}{'shift':>9}")
rows10 = [C[c][7] for c in CELLS]
for c in CELLS:
    n,E,w = C[c][7]; an,aE,aw = AB10[c]
    print(f"{c:>11}{n:>6}{n/DAYS:>7.2f}{E:>+9.3f}{w:>7.1f}   |  {an:>6}{aE:>+9.3f}{E-aE:>+9.3f}")
n,E,w = agg(rows10); sd,lo,hi,t,pf = stats(n,E,w)
pos = sum(1 for c in CELLS if C[c][7][1] > 0)
an,aE,aw = agg([AB10[c] for c in CELLS]); apos = sum(1 for c in CELLS if AB10[c][1] > 0)
print(f"\n  FOLD C  >=10R : n {n}  {n/DAYS:.1f}/day  E[R] {E:+.3f}  90% CI [{lo:+.3f},{hi:+.3f}]")
print(f"                  win {100*w:.1f}%  PF {pf:.2f}  sd {sd:.2f}  t {t:+.2f}  signs {pos}/10")
print(f"  FOLDS A+B     : n {an}  E[R] {aE:+.3f}  win {100*aw:.1f}%  signs {apos}/10")
print(f"  SHIFT         : {E-aE:+.3f}R,  sign consistency {apos}/10 -> {pos}/10")

print("\n=== FOLD C: FULL CUMULATIVE CURVE, for context ===")
FLOORS = [0.0,0.5,1.0,1.5,2.0,3.0,5.0,10.0]
print(f"{'floor':>8}{'n':>6}{'/day':>7}{'E[R]':>9}{'90% CI':>19}{'win%':>7}{'PF':>6}{'t':>7}{'signs':>8}")
for k,fl in enumerate(FLOORS):
    n,E,w = agg([C[c][i] for c in CELLS for i in range(k,8)])
    sd,lo,hi,t,pf = stats(n,E,w)
    sg = sum(1 for c in CELLS if agg([C[c][i] for i in range(k,8)])[1] > 0)
    print(f"{'>='+str(fl):>8}{n:>6}{n/DAYS:>7.2f}{E:>+9.3f}   [{lo:+.3f},{hi:+.3f}]{100*w:>7.1f}{pf:>6.2f}{t:>+7.2f}{sg:>6}/10")

print("\n=== 3a. DECOMPOSE FOLD-C >=10R BY DIRECTION AND INSTRUMENT ===")
for lbl, sel in (("long  cells", [c for c in CELLS if c.endswith('long')]),
                 ("short cells", [c for c in CELLS if c.endswith('short')])):
    n,E,w = agg([C[c][7] for c in sel]); sd,lo,hi,t,pf = stats(n,E,w)
    sg = sum(1 for c in sel if C[c][7][1] > 0)
    print(f"  {lbl}: n {n:4d}  E[R] {E:+.3f}  [{lo:+.3f},{hi:+.3f}]  win {100*w:.1f}%  t {t:+.2f}  signs {sg}/5")
print()
for inst in ("MGC","SIL","MNQ","MCL","6E"):
    sel = [c for c in CELLS if c.startswith(inst)]
    n,E,w = agg([C[c][7] for c in sel]); sd,lo,hi,t,pf = stats(n,E,w)
    print(f"  {inst:>4}: n {n:4d}  E[R] {E:+.3f}  win {100*w:.1f}%  t {t:+.2f}")

print("\n=== 3b. IS +0.059 (A+B) DRIVEN BY A SUBGROUP? leave-one-cell-out on A+B ===")
base_n, base_E, base_w = agg([AB10[c] for c in CELLS])
print(f"  all ten cells: E[R] {base_E:+.3f}  n {base_n}")
worst = None
for c in CELLS:
    sel = [x for x in CELLS if x != c]
    n,E,w = agg([AB10[x] for x in sel])
    print(f"  drop {c:>10}: E[R] {E:+.3f}  n {n}   ({E-base_E:+.3f})")

print("\n=== 5. IS THE PER-CELL RANKING STABLE ACROSS FOLDS? ===")
xs = [AB10[c][1] for c in CELLS]
ys = [C[c][7][1]  for c in CELLS]
mx, my = sum(xs)/len(xs), sum(ys)/len(ys)
sxy = sum((a-mx)*(b-my) for a,b in zip(xs,ys))
sxx = sum((a-mx)**2 for a in xs); syy = sum((b-my)**2 for b in ys)
r = sxy/math.sqrt(sxx*syy)
def rk(v):
    s = sorted(range(len(v)), key=lambda i: v[i]); out=[0]*len(v)
    for pos,i in enumerate(s): out[i]=pos
    return out
rx, ry = rk(xs), rk(ys)
mrx, mry = sum(rx)/10, sum(ry)/10
rs = sum((a-mrx)*(b-mry) for a,b in zip(rx,ry))/math.sqrt(
     sum((a-mrx)**2 for a in rx)*sum((b-mry)**2 for b in ry))
print(f"  Pearson  r(A+B E[R], fold C E[R]) across the ten cells = {r:+.3f}")
print(f"  Spearman rho                                            = {rs:+.3f}")
kept = sum(1 for a,b in zip(xs,ys) if (a>0)==(b>0))
print(f"  cells keeping their sign across folds: {kept}/10")
print(f"  mean |shift| per cell: {sum(abs(a-b) for a,b in zip(xs,ys))/10:.3f}R")

print("\n=== 2. >=10R ALONE vs >=10R + 4H BIAS (V47, both folds) ===")
V47 = {"A+B": {"room only": (1378, 0.050, 7), "room + bias": (674, 0.132, 7)},
       "C":   {"room only": (363, 0.043, 6),  "room + bias": (182,-0.074, 4)}}
for fold in ("A+B","C"):
    print(f"  fold {fold}:")
    for k,(n,E,sg) in V47[fold].items():
        print(f"    {k:<12} n {n:5d}  E[R] {E:+.3f}  cells positive {sg}/10")
print("  NOTE: V47 ran with the 2-slot engine, so both rows silently dropped ~22% of")
print("        candidates. V48 with 8 slots gives >=10R fold C = +0.008 (n 390) against")
print("        V47's +0.043 (n 363) -- the slot artefact was flattering the result.")

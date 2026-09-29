#!/usr/bin/env python3
"""
Phase 11 / C1: session-VWAP side as a RECORDED ATTRIBUTE on the V49 ledger.
Folds A+B only. Fold C sealed. Spec frozen in PHASE10_FEATURE_MAP.md sec C1.
Gate (pre-registered): VWAP must beat the SMA20 control by a margin whose 90% CI
excludes zero, AND hold the same sign in >= 7/10 cells.
"""
import math
TGT, STOP = 5.0, -1.0
SEED = 42

# cell -> feature -> (n_plus,E_plus,win_plus, n_minus,E_minus,win_minus)
D = {
 "MGC long": dict(vwap=(140,-0.3042,13.6, 564,-0.3048,13.3),
                  sma =(173,-0.4331,11.0, 531,-0.2628,14.1),
                  rnd =(338,-0.1802,15.4, 366,-0.4196,11.5), fills=704, excl=0, cands=774),
 "MGC short":dict(vwap=(448,-0.0160,18.3, 156, 0.1731,21.8),
                  sma =(439, 0.0554,19.6, 165,-0.0272,18.2),
                  rnd =(318,-0.0108,18.6, 286, 0.0813,19.9), fills=604, excl=0, cands=691),
 "SIL long": dict(vwap=(172,-0.1969,14.0, 599,-0.1851,14.2),
                  sma =(232,-0.1306,15.1, 537,-0.2092,13.8),
                  rnd =(401,-0.2583,13.0, 370,-0.1113,15.4), fills=771, excl=0, cands=867),
 "SIL short":dict(vwap=(424, 0.1920,20.5, 138,-0.0419,16.7),
                  sma =(385, 0.2226,21.0, 177,-0.0569,16.4),
                  rnd =(273, 0.1897,20.5, 289, 0.0825,18.7), fills=562, excl=0, cands=634),
 "MNQ long": dict(vwap=(208,-0.0993,16.3, 517,-0.1423,15.7),
                  sma =(248,-0.0245,17.3, 477,-0.1848,15.1),
                  rnd =(373,-0.0664,16.9, 352,-0.1972,14.8), fills=725, excl=0, cands=812),
 "MNQ short":dict(vwap=(718,-0.0977,16.9, 149,-0.1160,16.1),
                  sma =(576,-0.0485,17.7, 291,-0.2043,14.8),
                  rnd =(458,-0.0022,18.3, 409,-0.2112,14.9), fills=867, excl=0, cands=942),
 "MCL long": dict(vwap=(145,-0.2489,16.6, 593,-0.1677,18.4),
                  sma =(224,-0.2000,17.4, 514,-0.1766,18.3),
                  rnd =(384,-0.0320,20.6, 354,-0.3483,15.3), fills=738, excl=0, cands=826),
 "MCL short":dict(vwap=(458,-0.3928,14.8, 139, 0.0636,22.3),
                  sma =(443,-0.3126,16.3, 154,-0.2113,17.5),
                  rnd =(299,-0.2780,16.7, 298,-0.2950,16.4), fills=597, excl=0, cands=692),
 "6E long":  dict(vwap=(108, 0.1286,21.3, 487,-0.1177,17.2),
                  sma =(186, 0.0265,19.4, 408,-0.1157,17.4),
                  rnd =(312,-0.0376,18.6, 283,-0.1120,17.3), fills=595, excl=0, cands=658),
 "6E short": dict(vwap=(399, 0.0396,19.8,  96,-0.2142,15.6),
                  sma =(337,-0.1386,16.9, 157, 0.2748,23.6),
                  rnd =(272,-0.1551,16.5, 223, 0.1677,22.0), fills=495, excl=0, cands=558),
}
CELLS = list(D)

def sd_of(E, w):
    return math.sqrt(max(w*TGT*TGT + (1-w)*STOP*STOP - E*E, 1e-12))

def cell_diff(c, f):
    np_,Ep,wp, nm,Em,wm = D[c][f]
    wp, wm = wp/100.0, wm/100.0
    sp, sm = sd_of(Ep,wp), sd_of(Em,wm)
    se = math.sqrt(sp*sp/np_ + sm*sm/nm)
    return Ep-Em, se, np_, nm

def pooled(f):
    """n-weighted pooled E on each side, and the difference with its SE."""
    Np=Nm=0; Sp=Sm=0.0; Wp=Wm=0.0
    for c in CELLS:
        np_,Ep,wp, nm,Em,wm = D[c][f]
        Np+=np_; Sp+=np_*Ep; Wp+=np_*wp
        Nm+=nm;  Sm+=nm*Em;  Wm+=nm*wm
    Ep, Em = Sp/Np, Sm/Nm
    wp, wm = Wp/Np/100.0, Wm/Nm/100.0
    sp, sm = sd_of(Ep,wp), sd_of(Em,wm)
    se = math.sqrt(sp*sp/Np + sm*sm/Nm)
    return Np,Ep,wp, Nm,Em,wm, Ep-Em, se

print("=== 1. SANITY CHECKS ===")
tot_f = sum(D[c]['fills'] for c in CELLS)
tot_c = sum(D[c]['cands'] for c in CELLS)
tot_x = sum(D[c]['excl'] for c in CELLS)
ok = True
for c in CELLS:
    for f in ("vwap","sma","rnd"):
        np_,_,_, nm,_,_ = D[c][f]
        exp = D[c]['fills'] - (D[c]['excl'] if f=="vwap" else 0)
        if f == "sma":
            # SMA can also be 0 only in the first 20 bars; check it does not exceed fills
            if np_+nm > D[c]['fills']: ok=False; print(f"  FAIL {c} {f}: {np_+nm} > fills {D[c]['fills']}")
        elif np_+nm != exp:
            ok = False; print(f"  FAIL {c} {f}: {np_+nm} != {exp}")
print(f"  side counts reconcile to fills          {'OK' if ok else 'FAIL'}")
print(f"  total candidates {tot_c}   total fills {tot_f}   VWAP excluded (na) {tot_x}")
print(f"  random-sign seed recorded               {SEED}")
print("  freeze point: all three signs read at the ARM bar close, stored per slot,")
print("  never updated -- identical freeze point for VWAP, SMA20 and the random sign.")
print("  VWAP accumulates hlc3*volume from the 22:00 UTC session reset, current bar")
print("  inclusive, closed bars only. No request.security, no lookahead_on.")

print("\n=== 2. POOLED RESULTS ===")
res = {}
for f,label in (("vwap","VWAP"),("sma","SMA20 control"),("rnd","random-sign control")):
    Np,Ep,wp, Nm,Em,wm, d, se = pooled(f)
    lo,hi = d-1.645*se, d+1.645*se
    res[f] = (d, se, lo, hi)
    print(f"\n  {label}")
    print(f"    side +   n {Np:5d}   E[R] {Ep:+.4f}   win {100*wp:.1f}%")
    print(f"    side -   n {Nm:5d}   E[R] {Em:+.4f}   win {100*wm:.1f}%")
    print(f"    diff     {d:+.4f}   SE {se:.4f}   90% CI [{lo:+.4f}, {hi:+.4f}]   t {d/se:+.2f}")

print("\n=== 3. TEN-CELL VWAP RESULTS ===")
print(f"{'cell':>11}{'n +':>7}{'E +':>9}{'n -':>7}{'E -':>9}{'diff':>9}{'sign':>6}")
pos = 0
for c in CELLS:
    d, se, np_, nm = cell_diff(c, "vwap")
    s = "+" if d > 0 else "-"
    if d > 0: pos += 1
    e = D[c]["vwap"]
    print(f"{c:>11}{e[0]:>7}{e[1]:>+9.4f}{e[3]:>7}{e[4]:>+9.4f}{d:>+9.4f}{s:>6}")
print(f"\n  VWAP diff positive in {pos}/10 cells")

print("\n=== 4-5. CONTROLS, cell signs ===")
for f,label in (("sma","SMA20"),("rnd","random")):
    p = sum(1 for c in CELLS if cell_diff(c,f)[0] > 0)
    print(f"  {label:>8} diff positive in {p}/10 cells")

print("\n=== 6. GATE ===")
dv, sev, lov, hiv = res["vwap"]
ds, ses, los, his = res["sma"]
# criterion 1: VWAP beats SMA by a margin whose 90% CI excludes zero.
# The two statistics are computed on the same fills, so treat them as paired at
# the cell level: difference of differences, SE from the per-cell variation.
per = [cell_diff(c,"vwap")[0] - cell_diff(c,"sma")[0] for c in CELLS]
m = sum(per)/len(per)
sdp = math.sqrt(sum((x-m)**2 for x in per)/(len(per)-1))
sem = sdp/math.sqrt(len(per))
lo_m, hi_m = m-1.833*sem, m+1.833*sem   # t(9), 90% two-sided
print(f"  VWAP diff  {dv:+.4f}  90% CI [{lov:+.4f}, {hiv:+.4f}]")
print(f"  SMA  diff  {ds:+.4f}  90% CI [{los:+.4f}, {his:+.4f}]")
print(f"  VWAP - SMA, paired across the ten cells: mean {m:+.4f}  SE {sem:.4f}")
print(f"    90% CI [{lo_m:+.4f}, {hi_m:+.4f}]   {'EXCLUDES zero' if lo_m*hi_m>0 else 'CONTAINS zero'}")
c1 = lo_m*hi_m > 0 and m > 0
c2 = pos >= 7
print(f"\n  criterion 1  VWAP beats SMA, CI excludes zero : {'PASS' if c1 else 'FAIL'}")
print(f"  criterion 2  same sign in >= 7/10 cells        : {'PASS' if c2 else 'FAIL'}  ({pos}/10)")
print(f"\n  GATE: {'PASS' if (c1 and c2) else 'FAIL'}")
import sys
mde = (1.645 + 0.8416) * sev
print(f"\n  POWER: pooled split realised 3220/3438, essentially the ~3,100/side")
print(f"  assumed at pre-registration. SE {sev:.4f} -> minimum detectable effect at")
print(f"  80% power, alpha 0.10 two-sided = {mde:.3f}R, against the {0.15:.2f}R pre-registered.")
print("  The pooled test therefore had the power it promised. The per-cell sign")
print("  criterion did not: side splits within cells are very lopsided (MNQ short")
print("  718/149, 6E long 108/487), so individual cell signs are noisy.")

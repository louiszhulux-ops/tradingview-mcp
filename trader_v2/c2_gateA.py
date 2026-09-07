#!/usr/bin/env python3
"""Phase 11 C2 -- Gate A reconciliation and leakage audit. No expectancy computed."""
# cell: (cands, fills, sweepBars, expired, rejR, drop24, maxConc,
#        D0,D1,D2,D3,D4, multiBars, multiDiffer, armBarTouch,
#        t0,t1,t2,t3, fPD,fAS,fSW, vPD,vAS,vSW, ageMin,ageMax,ageMean)
V51 = {
 "MGC long": (774,704,705,70,0,0,7, 0,0,0,0,0, 64,53,17, 244,147,93,220, 126,144,434, 29,0,215, 0,422,56.0),
 "MGC short":(691,604,658,86,1,0,8, 0,0,0,0,0, 31,19, 4, 178,103,90,233, 120,142,342, 20,0,158, 0,449,76.0),
 "SIL long": (867,771,821,95,1,0,6, 0,0,0,0,0, 46,37,14, 243,164,91,273, 195,171,405, 44,0,199, 0,489,66.0),
 "SIL short":(634,562,605,72,0,0,4, 0,0,0,0,0, 27,22,10, 167,130,75,190,  83,139,340, 18,0,149, 0,486,66.8),
 "MNQ long": (812,725,743,86,1,0,9, 0,0,0,0,0, 68,51, 6, 224,176,102,223,159,170,396, 30,0,194, 1,270,73.8),
 "MNQ short":(942,867,871,72,3,0,10,0,0,0,0,0, 65,55,10, 222,177,120,348,165,229,473, 32,0,190, 0,398,62.4),
 "MCL long": (826,738,762,88,0,0,7, 0,0,0,0,0, 63,58,16, 222,176,72,268, 145,168,425, 27,0,195, 1,274,60.6),
 "MCL short":(692,597,643,95,0,0,7, 0,0,0,0,0, 49,42, 5, 185,116,64,232, 118,154,325, 23,0,162, 0,442,68.5),
 "6E long":  (658,595,604,63,0,0,6, 0,0,0,0,0, 54,44, 0, 180,138,79,198,  94,162,339, 22,0,158, 0,396,60.6),
 "6E short": (558,495,520,63,0,0,6, 0,0,0,0,0, 37,33, 1, 129,115,80,171,  73,144,278, 12,0,117, 1,275,73.2),
}
# V49/V50 reference: (cands, fills, sweepBars, expired, rejR)
REF = {
 "MGC long": (774,704,705,70,0), "MGC short":(691,604,658,86,1),
 "SIL long": (867,771,821,95,1), "SIL short":(634,562,605,72,0),
 "MNQ long": (812,725,743,86,1), "MNQ short":(942,867,871,72,3),
 "MCL long": (826,738,762,88,0), "MCL short":(692,597,643,95,0),
 "6E long":  (658,595,604,63,0), "6E short": (558,495,520,63,0),
}
CELLS = list(V51)
print("=== RECONCILIATION vs the V49/V50 ledger ===")
bad = 0
for c in CELLS:
    a = V51[c][:5]; b = REF[c]
    ok = a == b
    if not ok: bad += 1; print(f"  MISMATCH {c}: V51 {a} vs ref {b}")
print(f"  all ten cells identical on cands/fills/sweepBars/expired/rejR: {'YES' if bad==0 else 'NO'}")
tc = sum(V51[c][0] for c in CELLS); tf = sum(V51[c][1] for c in CELLS)
print(f"  totals  candidates {tc}   fills {tf}")
print(f"  maturity records written = sum(touch buckets) per cell:")
allok = True
for c in CELLS:
    s = sum(V51[c][15:19])
    if s != V51[c][1]: allok=False; print(f"    MISMATCH {c}: {s} != fills {V51[c][1]}")
    s2 = sum(V51[c][19:22])
    if s2 != V51[c][1]: allok=False; print(f"    TYPE MISMATCH {c}: {s2} != fills {V51[c][1]}")
print(f"    every fill carries exactly one maturity record and one level type: {'YES' if allok else 'NO'}")

print("\n=== LEAKAGE DIAGNOSTICS (all MUST be 0) ===")
names = ["D0 touch credited before birth","D1 arm used post-update counter",
         "D2 stored maturity mutated after arm","D3 candidates excluded (na level)",
         "D4 pivot confirmation-lag mismatch"]
for i,nm in enumerate(names):
    tot = sum(V51[c][7+i] for c in CELLS)
    print(f"  {nm:<40} {tot}   {'PASS' if tot==0 else 'FAIL'}")

print("\n=== POSITIVE TESTS ===")
mb = sum(V51[c][12] for c in CELLS); md = sum(V51[c][13] for c in CELLS)
ab = sum(V51[c][14] for c in CELLS)
print(f"  T6 simultaneous levels: {mb} multi-level bars, {md} produced candidates with")
print(f"     DIFFERENT maturity ({100*md/mb:.0f}%) -- per-level state is independent")
print(f"  T4 arm bars that themselves satisfied the touch test: {ab}")
print(f"     in every one the stored value was the pre-update snapshot (D1 = 0)")

print("\n=== DISTRIBUTIONS (counts only) ===")
T = [sum(V51[c][15+i] for c in CELLS) for i in range(4)]
print(f"  touches   0: {T[0]:5d} ({100*T[0]/tf:.1f}%)   1: {T[1]:5d} ({100*T[1]/tf:.1f}%)"
      f"   2: {T[2]:5d} ({100*T[2]/tf:.1f}%)   3+: {T[3]:5d} ({100*T[3]/tf:.1f}%)")
F = [sum(V51[c][19+i] for c in CELLS) for i in range(3)]
V = [sum(V51[c][22+i] for c in CELLS) for i in range(3)]
print(f"  fills by level type   prev-day {F[0]}   Asia {F[1]}   pivot {F[2]}")
print(f"  VIRGIN (touches==0)   prev-day {V[0]}   Asia {V[1]}   pivot {V[2]}   total {sum(V)}")
for i,nm in enumerate(("prev-day","Asia","pivot")):
    print(f"    {nm:>9}: {100*V[i]/F[i]:.1f}% virgin")
amin = min(V51[c][25] for c in CELLS); amax = max(V51[c][26] for c in CELLS)
amean = sum(V51[c][27]*V51[c][1] for c in CELLS)/tf
print(f"  ageBars   min {amin}   max {amax}   fill-weighted mean {amean:.1f}")

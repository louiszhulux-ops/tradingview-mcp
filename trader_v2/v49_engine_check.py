#!/usr/bin/env python3
"""
V49 measurement-engine fix, fold C, ten instrument x direction cells.
Strategy logic identical to V48; only the engine changed.
Each cell reports BOTH populations from the SAME run:
  ALL  = every swept level emitted independently (cascade removed)
  V48  = only the level V48's first-match cascade would have picked
"""
import math
TGT, STOP, DAYS = 5.0, -1.0, 14.5

D = {
 "MGC long": dict(all10=(36,0.352,25.0),  v4810=(33,0.310,24.2),
                  bars=179,cands=190,pd=41,asia=35,piv=114,m2=11,m3=0,
                  d24=0,w8=0,w2=51,mx=4,exp=24,rej=1,fill=165, v48fill=157),
 "MGC short":dict(all10=(52,0.352,25.0),  v4810=(50,0.290,24.0),
                  bars=214,cands=232,pd=74,asia=56,piv=102,m2=18,m3=0,
                  d24=0,w8=0,w2=95,mx=6,exp=23,rej=1,fill=208, v48fill=191),
 "SIL long": dict(all10=(54,0.051,18.5),  v4810=(53,0.072,18.9),
                  bars=232,cands=245,pd=49,asia=38,piv=158,m2=9,m3=2,
                  d24=0,w8=1,w2=81,mx=8,exp=29,rej=0,fill=216, v48fill=203),
 "SIL short":dict(all10=(57,0.313,22.8),  v4810=(57,0.313,22.8),
                  bars=230,cands=236,pd=70,asia=56,piv=110,m2=6,m3=0,
                  d24=0,w8=0,w2=71,mx=6,exp=27,rej=1,fill=208, v48fill=205),
 "MNQ long": dict(all10=(35,-0.502,11.4), v4810=(34,-0.483,11.8),
                  bars=209,cands=227,pd=49,asia=44,piv=134,m2=18,m3=0,
                  d24=0,w8=0,w2=58,mx=5,exp=24,rej=0,fill=203, v48fill=190),
 "MNQ short":dict(all10=(62,-0.241,16.1), v4810=(60,-0.211,16.7),
                  bars=257,cands=269,pd=44,asia=82,piv=143,m2=12,m3=0,
                  d24=0,w8=0,w2=91,mx=6,exp=33,rej=1,fill=235, v48fill=225),
 "MCL long": dict(all10=(30,-0.453,16.7), v4810=(28,-0.817,10.7),
                  bars=220,cands=239,pd=32,asia=71,piv=136,m2=19,m3=0,
                  d24=0,w8=1,w2=86,mx=8,exp=31,rej=0,fill=208, v48fill=192),
 "MCL short":dict(all10=(40,0.225,27.5),  v4810=(36,-0.101,22.2),
                  bars=204,cands=229,pd=49,asia=65,piv=115,m2=17,m3=4,
                  d24=0,w8=4,w2=73,mx=10,exp=20,rej=1,fill=208, v48fill=185),
 "6E long":  dict(all10=(27,0.552,29.6),  v4810=(24,0.279,25.0),
                  bars=174,cands=184,pd=50,asia=41,piv=93,m2=8,m3=1,
                  d24=0,w8=0,w2=32,mx=5,exp=15,rej=0,fill=169, v48fill=163),
 "6E short": dict(all10=(15,0.376,26.7),  v4810=(15,0.376,26.7),
                  bars=167,cands=176,pd=21,asia=69,piv=86,m2=7,m3=1,
                  d24=0,w8=0,w2=52,mx=4,exp=21,rej=3,fill=152, v48fill=146),
}
CELLS = list(D)

def agg(rows):
    n = sum(r[0] for r in rows)
    if n == 0: return 0,0.0,0.0
    return n, sum(r[0]*r[1] for r in rows)/n, sum(r[0]*r[2] for r in rows)/n/100.0
def stats(n,E,w):
    if n == 0: return 0,0,0,0,0
    sd = math.sqrt(max(w*TGT*TGT+(1-w)*STOP*STOP-E*E,1e-12)); se = sd/math.sqrt(n)
    pf = (w*TGT)/((1-w)*abs(STOP)) if w < 1 else float('inf')
    return sd, E-1.645*se, E+1.645*se, E/se, pf

S = lambda k: sum(D[c][k] for c in CELLS)
print("=== ENGINE VERIFICATION: are simultaneous sweeps now represented? ===\n")
print(f"  bars with >=1 sweep            {S('bars'):6d}")
print(f"  candidates emitted             {S('cands'):6d}")
print(f"  bars sweeping 2 levels         {S('m2'):6d}")
print(f"  bars sweeping 3 levels         {S('m3'):6d}")
chk = S('bars') + S('m2') + 2*S('m3')
print(f"  identity  bars + m2 + 2*m3 = {chk}  vs candidates {S('cands')}  "
      f"{'OK' if chk == S('cands') else 'MISMATCH'}")
print(f"  by level type: prev-day {S('pd')}  asia {S('asia')}  pivot {S('piv')}"
      f"  (sum {S('pd')+S('asia')+S('piv')})")
print(f"\n  RECOVERED CANDIDATES {S('cands')-S('bars'):+d} vs the cascade "
      f"({100*(S('cands')-S('bars'))/S('bars'):+.1f}%)")
print(f"  RECOVERED FILLS      {S('fill')-S('v48fill'):+d} "
      f"({100*(S('fill')-S('v48fill'))/S('v48fill'):+.1f}%)   {S('v48fill')} -> {S('fill')}")

print("\n=== CAPACITY: contention observable, nothing silently lost ===")
print(f"  dropped at 24 slots            {S('d24'):6d}")
print(f"  would have dropped at 8 slots  {S('w8'):6d}  ({100*S('w8')/S('cands'):.2f}%)")
print(f"  would have dropped at 2 slots  {S('w2'):6d}  ({100*S('w2')/S('cands'):.1f}%)")
print(f"  max concurrent observed        {max(D[c]['mx'] for c in CELLS):6d}  "
      f"(per cell {', '.join(str(D[c]['mx']) for c in CELLS)})")
print(f"  expired {S('exp')}   R-cap rejected {S('rej')}   filled {S('fill')}")

print("\n=== FOLD C >=10R: FIXED ENGINE vs V48-EQUIVALENT (same run, same bars) ===\n")
print(f"{'cell':>11}{'n ALL':>7}{'E ALL':>9}{'n V48':>7}{'E V48':>9}{'delta':>9}")
for c in CELLS:
    a, v = D[c]['all10'], D[c]['v4810']
    print(f"{c:>11}{a[0]:>7}{a[1]:>+9.3f}{v[0]:>7}{v[1]:>+9.3f}{a[1]-v[1]:>+9.3f}")
na,Ea,wa = agg([D[c]['all10'] for c in CELLS])
nv,Ev,wv = agg([D[c]['v4810'] for c in CELLS])
sda,loa,hia,ta,pfa = stats(na,Ea,wa)
sdv,lov,hiv,tv,pfv = stats(nv,Ev,wv)
pa = sum(1 for c in CELLS if D[c]['all10'][1] > 0)
pv = sum(1 for c in CELLS if D[c]['v4810'][1] > 0)
print(f"\n  FIXED (all levels): n {na}  {na/DAYS:.1f}/day  E[R] {Ea:+.3f}  "
      f"[{loa:+.3f},{hia:+.3f}]  win {100*wa:.1f}%  PF {pfa:.2f}  t {ta:+.2f}  signs {pa}/10")
print(f"  V48-EQUIVALENT    : n {nv}  {nv/DAYS:.1f}/day  E[R] {Ev:+.3f}  "
      f"[{lov:+.3f},{hiv:+.3f}]  win {100*wv:.1f}%  PF {pfv:.2f}  t {tv:+.2f}  signs {pv}/10")
print(f"  prior V48 run     : n 390  26.9/day  E[R] +0.008  [-0.193,+0.209]  t +0.07  signs 6/10")
print(f"\n  cascade removal moves E[R] {Ea-Ev:+.3f}R on {na-nv} extra fills")

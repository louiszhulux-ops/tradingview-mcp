#!/usr/bin/env python3
"""
V44 continuation ablation. Same event stream, one human condition per rung.
Question: is the continuation process present in the data, or did my event
definitions misclassify it?
"""
import math, sys
sys.path.insert(0,'trader')

# cell -> rung -> (armed, n, E[R], win%, PF, perDay)
D = {
 "MGC long": {"L0":(969,161, 0.147,21.7,1.16,2.25),"L1":(330, 54, 0.273,24.1,1.31,0.75),
              "L2":(181, 29,-0.362,13.8,0.65,0.41),"L3":(103,  7,-0.316,14.3,0.69,0.10),
              "L4":(103,  4, 1.750,50.0,3.65,0.06)},
 "MGC short":{"L0":(948,191, 0.317,24.6,1.37,2.67),"L1":(553,114, 0.469,27.2,1.56,1.59),
              "L2":(318, 67, 0.446,26.9,1.53,0.94),"L3":(174, 14, 0.546,28.6,1.66,0.20),
              "L4":(174,  3,-1.204, 0.0,0.00,0.04)},
 "MNQ long": {"L0":(1029,153,0.132,20.9,1.15,2.14),"L1":(495, 64, 0.248,23.4,1.28,0.90),
              "L2":(299, 36, 0.172,22.2,1.19,0.50),"L3":(149, 12, 0.374,25.0,1.44,0.17),
              "L4":(149,  1,-1.138, 0.0,0.00,0.01)},
 "MNQ short":{"L0":(1232,240,0.057,20.4,1.06,3.36),"L1":(610,110, 0.273,23.6,1.31,1.54),
              "L2":(342, 61,-0.073,18.0,0.92,0.85),"L3":(179,  6,-1.101, 0.0,0.00,0.08),
              "L4":(179,  1,-1.026, 0.0,0.00,0.01)},
}
CELLS = list(D)
print("ABLATION -- E[R] by rung, all four market x direction cells\n")
print(f"{'rung':>14} " + "".join(f"{c:>11}" for c in CELLS) + f"{'pooled':>9}{'signs':>7}{'n':>6}{'/day':>7}")
res = {}
for r in ("L0","L1","L2","L3","L4"):
    tot=n=pd=0.0; pos=0; line=f"{r:>14} "
    for c in CELLS:
        a_,nc,E,w,pf,d = D[c][r]
        line += f"{E:>+11.3f}"; tot += nc*E; n += nc; pd += d
        if E > 0: pos += 1
    Ep = tot/max(n,1); res[r]=(Ep,n,pd,pos)
    line += f"{Ep:>+9.3f}{pos:>5}/4{n:>6.0f}{pd:>7.2f}"
    print(line)

print("\nDELTA from adding each condition:")
for a,b,name in (("L0","L1","HTF bias aligned"),("L1","L2","reclaim"),("L2","L3","displacement")):
    d = [D[c][b][2]-D[c][a][2] for c in CELLS]
    up = sum(1 for x in d if x > 0)
    print(f"  {name:>18}: " + " ".join(f"{x:+.3f}" for x in d) +
          f"   improves {up}/4   mean {sum(d)/4:+.3f}")

print("\n" + "="*78)
E,n,pd,pos = res["L1"]
w = sum(D[c]["L1"][1]*D[c]["L1"][3] for c in CELLS)/n/100.0
e2 = w*25 + (1-w)*1.0; sd = math.sqrt(e2-E*E)
print(f"L1 (sweep + HTF bias aligned):  E={E:+.3f}R  n={n:.0f}  {pd:.2f}/day")
print(f"   win {100*w:.1f}%  sd {sd:.2f}  lambda {2*E/(sd*sd):.4f}  t {E/(sd/math.sqrt(n)):+.2f}  signs {pos}/4")
E6, w6, n6 = 0.134, 0.2245, 1335
sd6 = math.sqrt(w6*25+(1-w6)-E6*E6)
print(f"\nF6 range mean-reversion:        E={E6:+.3f}R  n={n6}  18.7/day")
print(f"   win {100*w6:.1f}%  sd {sd6:.2f}  lambda {2*E6/(sd6*sd6):.4f}  t {E6/(sd6/math.sqrt(n6)):+.2f}  signs 3/4")
print("\n  The bias-conditioned CONTINUATION model beats the mean-reversion")
print("  family on expectancy (2.5x), lambda (2.3x) and t -- and it is 4/4.")

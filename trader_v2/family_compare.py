#!/usr/bin/env python3
"""
V43b setup family comparison -- ranked on RISK-ADJUSTED QUALITY, with the
4-cell market x direction sign gate as the primary robustness filter.
Same engine for every family: retest entry, structural stop, room>=10R,
5R target, -1R stop, adverse excursion first, costs in R.
"""
import math, sys
sys.path.insert(0,'trader')

# family -> cell -> (n, E[R], win%, PF, MFE, MAE, perDay)
D = {
"F0 sweep":       {"MNQs":(364, 0.002,19.2,1.00,1.93,1.84,5.09),"MNQl":(246, 0.022,19.1,1.02,1.97,2.01,3.44),
                   "MGCl":(296, 0.017,19.6,1.02,2.07,2.13,4.14),"MGCs":(329, 0.104,21.0,1.11,2.21,1.93,4.60)},
"F1 brk+accept":  {"MNQs":( 58,-0.517,10.3,0.49,1.31,2.30,0.81),"MNQl":( 58,-0.292,13.8,0.70,1.82,2.06,0.81),
                   "MGCl":( 64,-0.128,17.2,0.87,1.84,2.22,0.89),"MGCs":( 79, 0.220,22.8,1.25,2.46,1.70,1.10)},
"F2 failed brk":  {"MNQs":( 35,-0.082,17.1,0.91,1.81,1.35,0.49),"MNQl":( 22,-1.084, 0.0,0.00,1.08,1.94,0.31),
                   "MGCl":( 33,-0.562, 9.1,0.44,1.69,1.68,0.46),"MGCs":( 38,-0.322,13.2,0.67,2.68,1.83,0.53)},
"F3 displace+RT": {"MNQs":(  2,-1.047, 0.0,0.00,2.47,2.43,0.03),"MNQl":(  1,-1.016, 0.0,0.00,3.34,1.07,0.01),
                   "MGCl":(  2, 1.956,50.0,4.73,4.27,1.01,0.03),"MGCs":(  2,-1.034, 0.0,0.00,0.42,1.56,0.03)},
"F4 BOS+retest":  {"MNQs":(111,-0.112,17.1,0.88,1.76,2.02,1.55),"MNQl":( 84, 0.160,21.4,1.18,2.12,1.92,1.18),
                   "MGCl":( 98,-0.365,13.3,0.64,1.61,2.18,1.37),"MGCs":(119,-0.038,18.5,0.96,2.41,1.83,1.66)},
"F5 trend pull":  {"MNQs":(400,-0.095,18.5,0.90,1.97,2.35,5.60),"MNQl":(290, 0.230,23.4,1.26,2.23,2.22,4.06),
                   "MGCl":(418,-0.169,17.5,0.83,1.87,2.30,5.84),"MGCs":(440,-0.165,17.5,0.83,1.90,2.19,6.15)},
"F6 range MR":    {"MNQs":(392, 0.114,21.7,1.12,2.04,2.19,5.49),"MNQl":(287, 0.394,26.1,1.45,2.31,2.10,4.02),
                   "MGCl":(331,-0.002,20.5,1.00,1.86,2.35,4.63),"MGCs":(325, 0.068,21.5,1.07,2.22,2.65,4.54)},
"F7 open range":  {"MNQs":( 15,-0.291,13.3,0.69,2.86,1.95,0.21),"MNQl":( 12,-0.587, 8.3,0.41,1.89,1.48,0.17),
                   "MGCl":( 14,-1.122, 0.0,0.00,1.06,2.60,0.20),"MGCs":( 20,-0.822, 5.0,0.22,1.20,1.70,0.28)},
}
CELLS = ["MNQs","MNQl","MGCl","MGCs"]

print("PRIMARY RANKING: risk-adjusted quality + 4-cell robustness gate\n")
print(f"{'family':>16} " + "".join(f"{c:>9}" for c in CELLS) +
      f"{'pooled':>9}{'signs':>7}{'n':>6}{'/day':>7}{'PF':>6}{'lambda':>8}{'t':>7}")
rows = []
for f, cells in D.items():
    tot = n = pd = pfw = 0.0; pos = 0
    line = f"{f:>16} "
    for c in CELLS:
        nc, E = cells[c][0], cells[c][1]
        line += f"{E:>+9.3f}"; tot += nc*E; n += nc; pd += cells[c][6]; pfw += nc*cells[c][3]
        if E > 0: pos += 1
    Ep = tot/max(n,1); PF = pfw/max(n,1)
    w = sum(cells[c][0]*cells[c][2] for c in CELLS)/max(n,1)/100.0
    e2 = w*25 + (1-w)*1.0
    sd = math.sqrt(max(1e-9, e2 - Ep*Ep))
    lam = 2*Ep/(sd*sd); t = Ep/(sd/math.sqrt(n))
    line += f"{Ep:>+9.3f}{pos:>5}/4{n:>6.0f}{pd:>7.1f}{PF:>6.2f}{lam:>8.4f}{t:>+7.2f}"
    print(line)
    rows.append((pos, Ep, f, n, pd, PF, lam, t))

print("\n" + "="*104)
print("Families passing the gate (positive in all four market x direction cells):\n")
for pos,Ep,f,n,pd,PF,lam,t in sorted(rows, reverse=True):
    if pos == 4:
        print(f"  {f}: E={Ep:+.3f}R  n={n:.0f}  {pd:.1f}/day  PF={PF:.2f}  lambda={lam:.4f}  t={t:+.2f}")
print("\n  3/4 (one cell flat, none negative):")
for pos,Ep,f,n,pd,PF,lam,t in sorted(rows, reverse=True):
    if pos == 3:
        worst = min(D[f][c][1] for c in CELLS)
        print(f"  {f}: E={Ep:+.3f}R  n={n:.0f}  {pd:.1f}/day  PF={PF:.2f}  "
              f"lambda={lam:.4f}  t={t:+.2f}  (worst cell {worst:+.3f})")
print("\n  FAILED the gate: " + ", ".join(f for pos,Ep,f,*_ in sorted(rows) if pos <= 2))

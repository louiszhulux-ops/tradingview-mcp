#!/usr/bin/env python3
"""
V32 target surface -- analysis against the pre-registered decision rule.

Each row: (target_a, n, win%_with, R_with, win%_against, R_against).
'with' = trade in the trigger's own direction, 'against' = the control.
edge = (R_with - R_against)/2.
"""
import math

TIGHT = {
 ("gold","LONG"):  [(0.25,1954,77.1,-0.0360,78.9,-0.0136),(0.50,1954,63.4,-0.0496,67.4,0.0110),
                    (0.75,1953,54.4,-0.0475,58.7,0.0269),(1.00,1953,47.2,-0.0558,52.6,0.0517),
                    (1.50,1953,38.2,-0.0448,43.1,0.0783),(2.00,1952,32.0,-0.0478,36.7,0.0969)],
 ("gold","SHORT"): [(0.25,2051,79.1,-0.0108,78.4,-0.0206),(0.50,2051,68.2,0.0224,66.1,-0.0083),
                    (0.75,2051,58.5,0.0230,57.1,-0.0009),(1.00,2051,50.9,0.0180,48.9,-0.0229),
                    (1.50,2049,40.8,0.0170,38.1,-0.0467),(2.00,2048,33.7,0.0040,31.6,-0.0554)],
 ("mnq","LONG"):   [(0.25,2050,80.6,0.0073,80.0,0.0006),(0.50,2050,66.4,-0.0041,67.8,0.0163),
                    (0.75,2050,56.7,-0.0080,58.0,0.0148),(1.00,2050,48.7,-0.0260,50.8,0.0163),
                    (1.50,2050,38.0,-0.0539,40.7,0.0172),(2.00,2050,31.6,-0.0691,34.1,0.0209)],
 ("mnq","SHORT"):  [(0.25,2025,79.7,-0.0043,77.8,-0.0272),(0.50,2025,67.4,0.0104,64.4,-0.0333),
                    (0.75,2025,58.2,0.0180,54.9,-0.0399),(1.00,2024,50.9,0.0192,48.1,-0.0389),
                    (1.50,2024,40.8,0.0201,38.1,-0.0511),(2.00,2024,34.6,0.0357,32.0,-0.0479)],
}
WIDE = {
 ("gold","LONG"):  [(0.5,1039,63.4,-0.0486,66.5,-0.0024),(1,1038,48.3,-0.0347,51.6,0.0328),
                    (2,1037,32.8,-0.0164,36.6,0.0983),(3,1037,24.9,-0.0048,27.2,0.0878),
                    (4,1037,19.7,-0.0265,21.5,0.0694),(6,1037,14.7,-0.0216,15.5,0.0484)],
 ("gold","SHORT"): [(0.5,1084,69.0,0.0351,67.8,0.0171),(1,1084,49.4,-0.0129,50.5,0.0092),
                    (2,1084,33.2,-0.0037,33.3,-0.0009),(3,1083,25.2,0.0083,24.8,-0.0065),
                    (4,1083,19.7,-0.0166,20.2,0.0126),(6,1081,15.3,0.0405,14.5,-0.0056)],
 ("mnq","LONG"):   [(0.5,956,66.2,-0.0068,67.2,0.0073),(1,956,47.7,-0.0460,51.9,0.0377),
                    (2,956,29.2,-0.1245,34.6,0.0387),(3,956,21.0,-0.1662,26.4,0.0524),
                    (4,956,17.9,-0.1258,22.7,0.1264),(6,956,14.2,-0.0948,16.5,0.1014)],
 ("mnq","SHORT"):  [(0.5,1059,67.0,0.0057,64.8,-0.0283),(1,1059,51.7,0.0331,47.6,-0.0482),
                    (2,1059,35.4,0.0623,30.9,-0.0737),(3,1058,26.0,0.0397,22.4,-0.1059),
                    (4,1057,20.4,0.0130,18.0,-0.1118),(6,1055,15.2,0.0366,13.8,-0.0958)],
}
OVERLAP = 4.0   # up to 4 concurrent trades share a slot pool -> deflate n

def sd(p, a, E):
    return math.sqrt(max(1e-9, p*a*a + (1-p) - E*E))

def ruin(E, s, L=5.0, U=7.5):
    """P(reach +U R before -L R), diffusion approximation."""
    lam = 2*E/(s*s)
    if abs(lam) < 1e-9:
        return L/(L+U)
    return (1-math.exp(-lam*L))/(1-math.exp(-lam*(U+L)))

def show(name, D):
    print(f"\n{'='*94}\n{name}\n{'='*94}")
    print(f"{'cell':>12} {'a':>5} {'edge':>9} {'SE':>7} {'t':>6} {'edge/a':>8} | "
          f"{'R_with':>9} {'sd':>6} {'lambda':>7} {'P(pass)':>8}")
    for key, rows in D.items():
        for (a, n, ww, rw, wa, ra) in rows:
            p_w, p_a = ww/100, wa/100
            s_w, s_a = sd(p_w, a, rw), sd(p_a, a, ra)
            edge = (rw-ra)/2
            ne = n/OVERLAP
            se = math.sqrt(s_w*s_w + s_a*s_a)/2/math.sqrt(ne)
            lam = 2*rw/(s_w*s_w)
            print(f"{key[0]+' '+key[1]:>12} {a:>5.2f} {edge:>+9.4f} {se:>7.4f} "
                  f"{edge/se:>+6.2f} {edge/a:>+8.4f} | {rw:>+9.4f} {s_w:>6.3f} "
                  f"{lam:>+7.4f} {ruin(rw,s_w):>7.1%}")

show("TIGHT GRID  (0.25R - 2R target, stop 1.5xATR)", TIGHT)
show("WIDE GRID   (0.5R - 6R target, stop 1.5xATR)",  WIDE)

print(f"\n{'='*94}\nH0 vs H1: is edge/a constant (H0) or rising as a falls (H1)?\n{'='*94}")
for label, D in (("tight", TIGHT), ("wide", WIDE)):
    for key, rows in D.items():
        ratios = [ (r[3]-r[5])/2 / r[0] for r in rows ]
        lo, hi = ratios[0], ratios[-1]
        # H1 predicts |edge/a| at the tightest target EXCEEDS it at the widest
        verdict = "H1" if abs(lo) > 1.3*abs(hi) else ("H0" if abs(lo) < 1.3*abs(hi) and abs(hi) < 1.3*abs(lo) else "H0-ish")
        print(f"  {label:>5} {key[0]+' '+key[1]:>11}: edge/a  tightest {lo:+.4f}  widest {hi:+.4f}   -> {verdict}")

print(f"\n{'='*94}\nWHAT THE ACCOUNT NEEDS, expressed scale-free\n{'='*94}")
print("Buffer L = 5R and target U = 7.5R at $400 risk on the LucidFlex 50K.")
for want in (0.60, 0.75, 0.90):
    lo, hi = 0.0, 5.0
    for _ in range(80):
        mid = (lo+hi)/2
        if (1-math.exp(-mid*5))/(1-math.exp(-mid*12.5)) < want: lo = mid
        else: hi = mid
    lam = (lo+hi)/2
    print(f"  P(pass) = {want:.0%}  needs lambda = 2E/sd^2 = {lam:.3f}"
          f"   (at a=2R, sd~1.45  ->  E = {lam*1.45**2/2:+.3f} R/trade)")
best = max(max(r[3] for r in rows) for D in (TIGHT, WIDE) for rows in D.values())
print(f"\n  best R_with measured anywhere in the surface: {best:+.4f} R  (gross, before cost)")

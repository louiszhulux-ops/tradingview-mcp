#!/usr/bin/env python3
"""V42b exit lab -- lambda ranking. MNQ long, room>=10R, n=159, 2.2/day."""
import math, sys
sys.path.insert(0,'trader')
from prop_rules import LUCIDFLEX
from montecarlo import run
a = LUCIDFLEX["50K"]

MNQ = {
 "H1 fixed 1R":     (-0.1656,0.478, 0.89,-1.13), "H2 fixed 2R":  (0.0482,0.390,1.88,-1.12),
 "H3 fixed 3R":     ( 0.0860,0.302, 2.88,-1.12), "H4 fixed 5R":  (0.1614,0.214,4.89,-1.12),
 "H5 destination":  ( 0.3949,0.101,13.95,-1.12), "H6 trail":     (0.1498,0.390,2.14,-1.12),
 "H7 partial+dest": ( 0.3220,0.390, 2.59,-1.12), "H8 REVERSAL":  (0.3725,0.145,9.18,-1.12),
 "H9 ride":         ( 0.8302,0.075,24.75,-1.12), "H10 time 48b": (0.2687,0.088,14.67,-1.12),
 "H11 half2R+rev":  ( 0.2074,0.390, 2.29,-1.12), "H12 half2R+ride":(0.4392,0.390,2.89,-1.12),
}
N = 159
print("MNQ long, room>=10R.  lambda = 2E/sd^2 is what a hard floor cares about.\n")
print(f"{'rule':>17} {'E[R]':>8} {'sd':>7} {'lambda':>8} {'t':>6}")
rows=[]
for k,(E,w,aw,al) in MNQ.items():
    e2 = w*aw*aw + (1-w)*al*al
    sd = math.sqrt(max(1e-9,e2-E*E)); lam = 2*E/(sd*sd); se = sd/math.sqrt(N)
    rows.append((lam,k,E,w,aw,al,sd,E/se))
for lam,k,E,w,aw,al,sd,t in sorted(rows, reverse=True):
    print(f"{k:>17} {E:>+8.4f} {sd:>7.2f} {lam:>8.4f} {t:>+6.2f}")

top = sorted(rows, reverse=True)[0]
print(f"\n  best lambda: {top[1]}  lambda={top[0]:.4f}  t={top[7]:+.2f}")
print("  Banking half at 2R keeps most of 'ride' expectancy at a third of its")
print("  variance -- the classic professional partial, and it wins on lambda.\n")
print("="*76)
print("Pass probability, verified LucidFlex rules, MNQ long room>=10R, 2.2/day")
print("R = $82 per MNQ micro contract.\n")
print(f"{'rule':>17} {'size':>8} {'buffer':>8} {'pass':>7} {'bust':>6} {'med d':>7} {'<=7d':>7}")
for k in ("H12 half2R+ride","H7 partial+dest","H4 fixed 5R","H8 REVERSAL"):
    E,w,aw,al = MNQ[k]
    for ctr in (2,3,5):
        r = 82.0*ctr*abs(al)
        res = run(a, w, aw/abs(al), 2, r, n=4000, max_days=250,
                  daily_target_days=20, daily_stop_R=99.0)
        print(f"{k:>17} {ctr:>4} micro {a.max_loss_limit/r:>7.1f}R {res['pas']:>6.1%} "
              f"{res['bust']:>5.1%} {str(res['med']):>7} {res['within'][7]:>6.1%}")
    print()

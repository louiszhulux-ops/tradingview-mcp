#!/usr/bin/env python3
"""
The check that matters: is the exit rule's advantage real, or was it an
artefact of choosing the direction from the sample?
All four market x direction cells, room>=10R.
"""
import math, sys
sys.path.insert(0,'trader')
from prop_rules import LUCIDFLEX
from montecarlo import run
a = LUCIDFLEX["50K"]

# cell: n, then E[R] per rule
CELLS = {                # n     H1      H2      H3      H4      H8      H12
 "MGC long":  (170, -0.2949,-0.1479, 0.0933, 0.2227,-0.3128, 0.0070),
 "MGC short": (200, -0.1305, 0.0995, 0.2195, 0.3395, 0.4172, 0.3194),
 "MNQ long":  (159, -0.1656, 0.0482, 0.0860, 0.1614, 0.3725, 0.4392),
 "MNQ short": (254, -0.3119,-0.1544,-0.0048, 0.0346,-0.2536,-0.4469),
}
RULES = ["H1 fixed 1R","H2 fixed 2R","H3 fixed 3R","H4 fixed 5R","H8 REVERSAL","H12 half+ride"]

print(f"{'rule':>14} " + " ".join(f"{c:>11}" for c in CELLS) + f" {'pooled':>9} {'signs':>6}")
pooled = {}
for j,rule in enumerate(RULES):
    tot = n = 0.0; pos = 0
    row = f"{rule:>14} "
    for c,(nc,*vals) in CELLS.items():
        v = vals[j]; row += f"{v:>+11.4f} "
        tot += nc*v; n += nc
        if v > 0: pos += 1
    p = tot/n; pooled[rule] = p
    row += f"{p:>+9.4f} {pos:>4}/4"
    print(row)

print("\n  H12 and H8 flip sign with direction. Their headline numbers required")
print("  knowing the favoured direction in advance, which I cannot do ex ante.")
print("  H4 fixed 5R is positive in ALL FOUR cells; H1 fixed 1R negative in all four.")
print("\n  => the ROBUST finding is TARGET WIDTH, not the clever exit.\n")

E = pooled["H4 fixed 5R"]; N = sum(v[0] for v in CELLS.values())
p5 = 0.224
e2 = p5*25 + (1-p5)*1.36; sd = math.sqrt(e2-E*E)
print(f"H4 direction-agnostic: E={E:+.4f}R, n={N}, sd={sd:.2f}, "
      f"t={E/(sd/math.sqrt(N)):+.2f}, lambda={2*E/(sd*sd):.4f}")
print(f"opportunities: {N/72:.1f}/day across 2 markets, both directions\n")

print("="*78)
print("PRIMARY METRIC at the direction-agnostic edge (no ex-ante direction call)")
print(f"{'risk':>8} {'buffer':>8} {'pass':>7} {'bust':>6} {'med d':>7} {'<=3d':>7} {'<=5d':>7} {'<=7d':>7}")
w = (E+1.0)/6.0
for risk in (60,100,150,200,300,400):
    res = run(a, w, 5.0, 11, risk, n=8000, max_days=250,
              daily_target_days=20, daily_stop_R=99.0)
    wi = res["within"]
    print(f"{risk:>5} usd {a.max_loss_limit/risk:>7.1f}R {res['pas']:>6.1%} {res['bust']:>5.1%} "
          f"{str(res['med']):>7} {wi[3]:>6.1%} {wi[5]:>6.1%} {wi[7]:>6.1%}")

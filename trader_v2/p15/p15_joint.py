#!/usr/bin/env python3
"""
Phase 15 JOINT analysis. Reads only committed arm run files. Changes nothing.
Reuses p15_analyze's loaders and the Phase 13G clustering identities verbatim.

Answers the eight pre-registered questions. Produces no ranking and names no winner.
"""
import sys, os, statistics
from collections import OrderedDict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p15_analyze import load, funnel, perf, clus_stats, clusters, kp, ka, pct, fold_of

ARMS = OrderedDict([
    ("BASE_pooled",                "BASELINE (frozen)"),
    ("A_sw2_pooled",               "A swLen=2"),
    ("A_sw4_pooled",               "A swLen=4"),
    ("A_sw5_pooled",               "A swLen=5"),
    ("B_d125_pooled",              "B dispMin=1.25"),
    ("B_d175_pooled",              "B dispMin=1.75"),
    ("B_d200_pooled",              "B dispMin=2.00"),
    ("C1_retest_tol_pooled",       "C1 retest band"),
    ("D1_bos_reference_pooled",    "D1 BOS reference"),
    ("E1_fvg_association_pooled",  "E1 FVG association"),
    ("F1_stop_raw_extreme_pooled", "F1 raw stop"),
    ("G1_first_choch_pooled",      "G1 CHOCH latch"),
])

DAT = OrderedDict((a, load(a)) for a in ARMS)
B_cells, B_led = DAT["BASE_pooled"]
STAGES = ["sw", "ch", "rt", "bos", "fvg", "fill"]

def line(): print("=" * 118)

# ---------------------------------------------------------------- Q1/Q2/Q3
line(); print("Q1-Q3  STRUCTURAL REACH: at which stage does each assumption first move the funnel?"); line()
print("Percent change vs frozen baseline, pooled A+B+C. '=' means bit-identical.\n")
for ltf in ("1m", "3m"):
    b = funnel(B_cells, ltf)
    print(f"  --- {ltf} ---")
    print(f"  {'arm':22s}" + "".join(f"{s:>11s}" for s in STAGES) + "   first stage moved")
    for a, lbl in ARMS.items():
        if a == "BASE_pooled":
            print(f"  {lbl:22s}" + "".join(f"{b[s]:>11d}" for s in STAGES) + "   (reference)")
            continue
        f = funnel(DAT[a][0], ltf)
        cells_txt, first = "", "none"
        for s in STAGES:
            d = f[s] - b[s]
            cells_txt += f"{'=':>11s}" if d == 0 else f"{pct(d,b[s]):>+10.1f}%"
            if d != 0 and first == "none":
                first = s
        print(f"  {lbl:22s}{cells_txt}   {first}")
    print()

# per-cell bit-identity of each stage (stronger than pooled)
print("  Per-cell bit-identity (all 8 cells identical to baseline at that stage?)\n")
print(f"  {'arm':22s}" + "".join(f"{s:>9s}" for s in STAGES))
bmap = {(c["inst"], c["d"], c["ltf"]): c for c in B_cells}
for a, lbl in ARMS.items():
    if a == "BASE_pooled": continue
    row = ""
    for s in STAGES:
        same = all(c[s] == bmap[(c["inst"], c["d"], c["ltf"])][s] for c in DAT[a][0])
        row += f"{'YES' if same else 'no':>9s}"
    print(f"  {lbl:22s}{row}")

# ---------------------------------------------------------------- Q4
print(); line(); print("Q4  1m vs 3m CONSISTENCY"); line()
print(f"  {'arm':22s}{'1m fills %':>12s}{'3m fills %':>12s}{'ratio |1m/3m|':>15s}   more sensitive")
for a, lbl in ARMS.items():
    if a == "BASE_pooled": continue
    d1 = pct(funnel(DAT[a][0],"1m")["fill"] - funnel(B_cells,"1m")["fill"], funnel(B_cells,"1m")["fill"])
    d3 = pct(funnel(DAT[a][0],"3m")["fill"] - funnel(B_cells,"3m")["fill"], funnel(B_cells,"3m")["fill"])
    r = abs(d1)/abs(d3) if d3 else float('inf')
    who = "1m" if abs(d1) > abs(d3) else ("3m" if abs(d3) > abs(d1) else "equal")
    print(f"  {lbl:22s}{d1:>+11.1f}%{d3:>+11.1f}%{r:>15.2f}   {who}")

# ---------------------------------------------------------------- Q5
print(); line(); print("Q5  FOLD CONSISTENCY  (R post-drag / fills, reconstructed from sweep timestamps)"); line()
for ltf in ("1m", "3m"):
    print(f"  --- {ltf} ---")
    print(f"  {'arm':22s}" + "".join(f"{'fold '+f:>20s}" for f in "ABC") + "   folds identical to base")
    bf = {f: perf([r for r in B_led if r["ltf"]==ltf and r["fold"]==f]) for f in "ABC"}
    for a, lbl in ARMS.items():
        led = DAT[a][1]
        pf = {f: perf([r for r in led if r["ltf"]==ltf and r["fold"]==f]) for f in "ABC"}
        txt = "".join(f"{pf[f]['Rpost']:>+13.3f}/{pf[f]['n']:<6d}" for f in "ABC")
        if a == "BASE_pooled":
            print(f"  {lbl:22s}{txt}   (reference)")
            continue
        same = [f for f in "ABC" if abs(pf[f]['Rpost']-bf[f]['Rpost'])<1e-9 and pf[f]['n']==bf[f]['n']]
        print(f"  {lbl:22s}{txt}   {','.join(same) if same else '-'}")
    print()

# ---------------------------------------------------------------- Q6/Q7
print(); line(); print("Q6-Q7  CLUSTERING: execution N vs effective event N, under BOTH identities"); line()
print(f"  {'arm':22s}{'fills':>7s}{'primary':>9s}{'altern.':>9s}{'%multi':>8s}"
      f"{'R exec':>10s}{'R/prim':>10s}{'R/alt':>10s}   sign(exec,prim,alt)")
def cluster_R(rows, fn):
    """One representative per cluster: mean R of the cluster, summed over clusters."""
    g = clusters(rows, fn)
    return sum(statistics.mean([r["R"] for r in v]) for v in g.values())
for a, lbl in ARMS.items():
    led = DAT[a][1]
    cs = clus_stats(led)
    Re = sum(r["R"] for r in led)
    Rp, Ra = cluster_R(led, kp), cluster_R(led, ka)
    sg = lambda x: "+" if x > 0 else ("-" if x < 0 else "0")
    print(f"  {lbl:22s}{len(led):>7d}{cs['primary']['clusters']:>9d}{cs['alternative']['clusters']:>9d}"
          f"{cs['alternative']['pct']:>7.1f}%{Re:>10.3f}{Rp:>10.3f}{Ra:>10.3f}   "
          f"{sg(Re)}{sg(Rp)}{sg(Ra)}")

print()
print("  Movement vs baseline, execution level vs event level (alternative identity):")
bRe = sum(r["R"] for r in B_led); bRa = cluster_R(B_led, ka); bRp = cluster_R(B_led, kp)
bn, bca = len(B_led), clus_stats(B_led)['alternative']['clusters']
print(f"  {'arm':22s}{'d fills':>9s}{'d alt events':>14s}{'d R exec':>11s}{'d R alt':>10s}"
      f"{'share of dR from':>20s}")
for a, lbl in ARMS.items():
    if a == "BASE_pooled": continue
    led = DAT[a][1]
    dn = len(led)-bn
    dca = clus_stats(led)['alternative']['clusters']-bca
    dRe = sum(r["R"] for r in led)-bRe
    dRa = cluster_R(led, ka)-bRa
    share = (dRa/dRe*100) if abs(dRe) > 1e-9 else float('nan')
    txt = f"{share:>18.0f}%" if share == share else f"{'n/a':>19s}"
    print(f"  {lbl:22s}{dn:>+9d}{dca:>+14d}{dRe:>+11.3f}{dRa:>+10.3f}{txt}")

# ---------------------------------------------------------------- Q8
print(); line(); print("Q8  EFFECTIVE INDEPENDENT N"); line()
print(f"  {'arm':22s}{'fills':>7s}{'alt events':>12s}{'wins':>6s}{'win events(alt)':>17s}"
      f"{'largest cluster':>17s}")
for a, lbl in ARMS.items():
    led = DAT[a][1]
    g = clusters(led, ka)
    wins = sum(1 for r in led if r["outcome"] == "WIN")
    winev = sum(1 for v in g.values() if any(r["outcome"] == "WIN" for r in v))
    print(f"  {lbl:22s}{len(led):>7d}{len(g):>12d}{wins:>6d}{winev:>17d}"
          f"{max((len(v) for v in g.values()), default=0):>17d}")
print()
print("  Winning events by fold (alternative identity), all arms pooled per fold:")
for a, lbl in ARMS.items():
    led = DAT[a][1]
    out = []
    for f in "ABC":
        rows = [r for r in led if r["fold"] == f]
        g = clusters(rows, ka)
        out.append(f"{f}:{sum(1 for v in g.values() if any(r['outcome']=='WIN' for r in v))}/{len(g)}")
    print(f"  {lbl:22s}" + "  ".join(f"{o:>10s}" for o in out))

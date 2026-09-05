#!/usr/bin/env python3
"""
Room-to-destination cumulative expectancy curve.

Input: V48 per-bucket counts from every instrument x direction cell.
       DATA[cell] = [(n, E[R], win%) for each of the 9 buckets]
       buckets: <0.5, 0.5-1, 1-1.5, 1.5-2, 2-3, 3-5, 5-10, >=10, no-destination
Nothing here estimates or extrapolates. If DATA is empty the script says so.
"""
import math

BUCKETS = ["<0.5R", "0.5-1R", "1-1.5R", "1.5-2R", "2-3R", "3-5R", "5-10R", ">=10R", "no dest"]
FLOORS  = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
TGT, STOP = 5.0, -1.0

DATA = {}      # filled in only from a successful V48 run
DAYS = None    # trading days in the fold, from the V48 ledger row

def agg(rows):
    """rows: list of (n, E, winpct) -> pooled (n, E, win fraction)"""
    n = sum(r[0] for r in rows)
    if n == 0:
        return 0, 0.0, 0.0
    E = sum(r[0] * r[1] for r in rows) / n
    w = sum(r[0] * r[2] for r in rows) / n / 100.0
    return n, E, w

def stats(n, E, w):
    if n == 0:
        return dict(sd=0.0, lo=0.0, hi=0.0, t=0.0, pf=0.0, med=0.0, streak=0.0)
    var = w * TGT * TGT + (1 - w) * STOP * STOP - E * E
    sd = math.sqrt(max(var, 1e-12))
    se = sd / math.sqrt(n)
    pf = (w * TGT) / ((1 - w) * abs(STOP)) if w < 1 else float('inf')
    # two-outcome payoff: the median is the loss whenever the win rate is below 50%
    med = TGT if w > 0.5 else STOP
    streak = math.log(n) / math.log(1 / (1 - w)) if 0 < w < 1 else float('nan')
    return dict(sd=sd, lo=E - 1.645 * se, hi=E + 1.645 * se, t=E / se, pf=pf,
                med=med, streak=streak)

def report():
    if not DATA:
        print("NO DATA. V48 has not been run -- the TradingView relay was unavailable.")
        print("Nothing is estimated or extrapolated here by design.")
        return
    cells = list(DATA)
    print(f"ROOM CURVE -- {len(cells)} instrument x direction cells, {DAYS:.1f} trading days\n")

    print("PER BUCKET (exclusive bands)")
    print(f"{'bucket':>10}{'n':>7}{'/day':>7}{'E[R]':>9}{'win%':>7}{'PF':>6}{'medR':>6}{'sd':>6}{'t':>7}")
    for i, b in enumerate(BUCKETS):
        n, E, w = agg([DATA[c][i] for c in cells])
        s = stats(n, E, w)
        print(f"{b:>10}{n:>7}{n/DAYS:>7.2f}{E:>+9.3f}{100*w:>7.1f}{s['pf']:>6.2f}"
              f"{s['med']:>+6.1f}{s['sd']:>6.2f}{s['t']:>+7.2f}")

    print("\nCUMULATIVE -- every trade with room >= the floor (the 'no dest' bucket is excluded)")
    print(f"{'floor':>8}{'n':>7}{'/day':>7}{'E[R]':>9}{'90% CI':>18}{'win%':>7}{'PF':>6}"
          f"{'t':>7}{'R/day':>8}{'wrstStrk':>9}")
    rows = []
    for k, fl in enumerate(FLOORS):
        n, E, w = agg([DATA[c][i] for c in cells for i in range(k, 8)])
        s = stats(n, E, w)
        rows.append((fl, n, E, w, s))
        print(f"{'>='+str(fl):>8}{n:>7}{n/DAYS:>7.2f}{E:>+9.3f}"
              f"   [{s['lo']:+.3f},{s['hi']:+.3f}]{100*w:>7.1f}{s['pf']:>6.2f}"
              f"{s['t']:>+7.2f}{E*n/DAYS:>+8.2f}{s['streak']:>9.1f}")

    print("\nINCREMENTAL COST OF EACH STEP UP (what raising the floor buys and what it costs)")
    print(f"{'step':>16}{'dE[R]':>9}{'trades lost/day':>18}{'dR/day':>9}{'verdict':>26}")
    for a in range(len(rows) - 1):
        fl0, n0, E0, w0, _ = rows[a]
        fl1, n1, E1, w1, _ = rows[a + 1]
        dE = E1 - E0
        dfreq = (n0 - n1) / DAYS
        dRday = E1 * n1 / DAYS - E0 * n0 / DAYS
        verdict = "raising the floor HELPS" if dRday > 0 else "raising the floor COSTS"
        print(f"{f'{fl0} -> {fl1}':>16}{dE:>+9.3f}{dfreq:>18.2f}{dRday:>+9.2f}{verdict:>26}")

    print("\nNOTES ON WHAT THESE COLUMNS CAN AND CANNOT SAY")
    print("  medR  every trade resolves to +5R or -1R (minus cost), so the median is")
    print("        -1R at any win rate below 50%. It is a property of the fixed-target")
    print("        design, not a finding about room.")
    print("  PF    derived from the win rate and the fixed payoff, gross of the per-trade")
    print("        cost that E[R] already carries. Treat as approximate.")
    print("  wrstStrk  expected longest losing run at that win rate over n trades.")
    print("        A stand-in for drawdown -- V48 does not record equity ordering, so")
    print("        true per-bucket drawdown is NOT available from this run.")

if __name__ == "__main__":
    report()

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

DAYS = 52.3   # trading days in folds A+B (mean across cells; 52.2-52.4)
# cell -> [(n, E[R], win%)] for buckets:
#   <0.5, 0.5-1, 1-1.5, 1.5-2, 2-3, 3-5, 5-10, >=10, no-destination
DATA = {
 "MGC long": [(18,-0.081,16.7),(14,-1.062,0.0),(20,0.134,20.0),(18,-1.075,0.0),
              (55,-0.735,5.5),(146,-0.381,11.6),(252,-0.429,11.5),(121,0.232,23.1),(0,0.0,0.0)],
 "MGC short":[(19,-0.435,10.5),(17,-0.738,5.9),(11,-0.536,9.1),(12,-1.070,0.0),
              (45,-0.408,11.1),(120,0.354,24.2),(210,-0.039,18.1),(146,0.354,25.3),(0,0.0,0.0)],
 "SIL long": [(6,-0.013,16.7),(20,-0.721,5.0),(16,0.102,18.8),(29,-0.816,3.4),
              (74,-0.214,13.5),(171,-0.187,14.0),(266,-0.227,13.5),(152,0.014,17.8),(0,0.0,0.0)],
 "SIL short":[(0,0.0,0.0),(16,-0.642,6.3),(26,0.355,23.1),(29,0.628,27.6),
              (49,0.193,20.4),(102,0.440,24.5),(176,0.113,19.3),(140,-0.194,14.3),(0,0.0,0.0)],
 "MNQ long": [(17,-0.349,11.8),(17,-0.685,5.9),(22,-0.507,9.1),(41,-0.027,17.1),
              (69,-0.621,7.2),(128,0.052,18.8),(247,-0.200,15.0),(119,0.307,23.5),(0,0.0,0.0)],
 "MNQ short":[(22,0.297,22.7),(20,0.120,20.0),(32,-0.103,15.6),(32,-0.318,12.5),
              (87,0.114,19.5),(143,-0.074,16.8),(297,-0.222,14.8),(173,0.120,21.4),(0,0.0,0.0)],
 "MCL long": [(8,-1.197,0.0),(15,-1.164,0.0),(23,-0.950,4.3),(35,-0.151,17.1),
              (68,-0.388,13.2),(159,-0.167,17.6),(241,-0.125,19.5),(135,-0.007,23.0),(0,0.0,0.0)],
 "MCL short":[(8,-1.182,0.0),(14,-0.737,7.1),(13,-1.152,0.0),(21,0.520,28.6),
              (55,-0.488,12.7),(125,-0.408,13.6),(205,-0.328,16.1),(117,0.077,24.8),(0,0.0,0.0)],
 "6E long":  [(18,-0.795,5.6),(10,0.079,20.0),(12,0.414,25.0),(21,0.583,28.6),
              (52,0.401,25.0),(119,0.040,19.3),(203,-0.200,16.3),(114,-0.406,13.2),(0,0.0,0.0)],
 "6E short": [(16,-0.342,12.5),(7,0.576,28.6),(14,-0.675,7.1),(22,-0.551,9.1),
              (35,0.085,20.0),(97,-0.139,16.5),(181,0.086,21.0),(94,0.031,20.2),(0,0.0,0.0)],
}

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
        r0, r1 = E0 * n0 / DAYS, E1 * n1 / DAYS
        if r1 > 0 >= r0:
            verdict = "turns positive"
        elif r1 > r0:
            verdict = "less negative" if r1 < 0 else "more positive"
        else:
            verdict = "worse"
        print(f"{f'{fl0} -> {fl1}':>16}{dE:>+9.3f}{dfreq:>18.2f}{dRday:>+9.2f}{verdict:>26}")


    print("\nSIGN CONSISTENCY AT EACH FLOOR -- the robustness check")
    print(f"{'floor':>8}  " + "".join(f"{c.replace(' short',' s').replace(' long',' l'):>9}" for c in cells) + f"{'signs':>8}")
    for k, fl in enumerate(FLOORS):
        line = f"{'>='+str(fl):>8}  "
        pos = 0
        for c in cells:
            n, E, w = agg([DATA[c][i] for i in range(k, 8)])
            line += f"{E:>+9.3f}"
            if E > 0:
                pos += 1
        print(line + f"{pos:>6}/10")

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

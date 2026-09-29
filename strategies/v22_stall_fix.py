#!/usr/bin/env python3
"""
The dominant outcome is STALLING, not passing or busting: the buffer shrinks
until it can no longer fund a single contract and the system stops.

That is partly an artefact of the policy "skip any trade you cannot size at the
target fraction". The alternative is "take one contract whenever the buffer can
survive it", which trades a little bust risk for escaping the stall. Worth
measuring rather than assuming.
"""
import random
random.seed(20260904)
START, TARGET, MLL, LOCK = 50000.0, 3000.0, 2000.0, 50100.0
BASE = 500.0

R, MAE, ONE = [], [], []
for ln in open("v17_mgc_trades.txt"):
    p = ln.strip().split("|")
    r_ = float(p[3]) / BASE
    R.append(r_)
    MAE.append(float(p[6]) / BASE)
    ONE.append(BASE / abs(float(p[4])))   # dollar risk of ONE contract on this setup
mu = sum(R) / len(R)
print(f"one-contract risk: min ${min(ONE):.0f}  median ${sorted(ONE)[len(ONE)//2]:.0f}  max ${max(ONE):.0f}\n")

def run(frac, shift, min1, maxtr=400):
    bal, peak, floor_ = START, START, START - MLL
    locked = False
    day, di = {}, 0
    for _ in range(maxtr):
        buf = bal - floor_
        i = random.randrange(len(R))
        r, mae, one = R[i] - shift, MAE[i] + shift, ONE[i]
        risk = buf * frac
        if risk < one:
            if not min1:
                return "stalled", bal
            risk = one                      # take the minimum size instead
        if risk * mae >= buf:               # cannot survive the excursion
            return "stalled", bal
        bal += r * risk
        di += 1
        day[di] = r * risk
        if bal < floor_:
            return "bust", bal
        if not locked:
            peak = max(peak, bal)
            floor_ = peak - MLL
            if peak >= START + MLL:
                floor_, locked = LOCK, True
        if bal >= START + TARGET:
            w = [v for v in day.values() if v > 0]
            if w and max(w) / (bal - START) <= 0.50:
                return "pass", bal
    return "stalled", bal

N = 20000
for wname, shift in [("observed edge", 0.0), ("zero edge", mu), ("negative", mu * 1.30)]:
    print(f"=== {wname} ===")
    print(f"{'frac':>6} {'min1contract':>13} {'pass%':>7} {'bust%':>7} {'stall%':>7}")
    for frac in (0.15, 0.20, 0.25, 0.30):
        for min1 in (False, True):
            res = [run(frac, shift, min1)[0] for _ in range(N)]
            print(f"{frac*100:>5.0f}% {str(min1):>13} "
                  f"{res.count('pass')/N*100:>7.2f} {res.count('bust')/N*100:>7.2f} "
                  f"{res.count('stalled')/N*100:>7.2f}")
    print()

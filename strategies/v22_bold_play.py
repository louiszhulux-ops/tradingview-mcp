#!/usr/bin/env python3
"""
If the game is subfair, grinding is the worst way to play it.

Classic result (Dubins & Savage): when the game is unfavourable and you must
reach a target, BOLD play -- the fewest, largest bets -- maximises the
probability of getting there. Timid play maximises the number of times you pay
the house edge.

Every sizing scheme in this project has been timid (small fraction of buffer,
many trades). This measures the whole spectrum against the real trade
distribution, under honest assumptions about the edge.
"""
import random
from statistics import median

random.seed(20260904)
START, TARGET, MLL, LOCK = 50000.0, 3000.0, 2000.0, 50100.0
BASE = 500.0

R, MAE = [], []
for ln in open("v17_mgc_trades.txt"):
    p = ln.strip().split("|")
    R.append(float(p[3]) / BASE)          # outcome in R multiples
    MAE.append(float(p[6]) / BASE)        # adverse excursion in R
mu = sum(R) / len(R)
print(f"{len(R)} trades   observed mean {mu:+.4f}R   "
      f"win% {sum(1 for r in R if r>0)/len(R)*100:.1f}")
print(f"worst outcome {min(R):+.2f}R   worst excursion {max(MAE):.2f}R\n")

def draw(shift):
    i = random.randrange(len(R))
    return R[i] - shift, MAE[i] + shift

def run(frac, shift, cap_frac=1.0, maxtr=400):
    """frac = fraction of remaining buffer risked per trade."""
    bal, peak, floor_ = START, START, START - MLL
    locked = False
    day, di = {}, 0
    for _ in range(maxtr):
        buf = bal - floor_
        risk = min(buf * frac, buf * cap_frac)
        if risk < 40:                      # below one contract, cannot trade
            return "stalled", bal
        r, mae = draw(shift)
        if bal - mae * risk < floor_:
            return "bust", bal
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
worlds = [("observed edge", 0.0), ("zero edge", mu), ("negative (lower CI)", mu * 1.30)]
for wname, shift in worlds:
    print(f"=== {wname} ===")
    print(f"{'risk = x of buffer':>20} {'pass%':>7} {'bust%':>7} {'stall%':>7} {'P(pass)+P(bust)':>16}")
    for frac in (0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.65, 0.80, 1.00):
        res = [run(frac, shift)[0] for _ in range(N)]
        p = res.count("pass") / N * 100
        b = res.count("bust") / N * 100
        s = res.count("stalled") / N * 100
        print(f"{frac*100:>19.0f}% {p:>7.2f} {b:>7.2f} {s:>7.2f} {p+b:>16.1f}")
    print()

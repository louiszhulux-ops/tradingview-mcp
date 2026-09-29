#!/usr/bin/env python3
"""
The 72% pass rate assumed the observed edge is the true edge. The 95% CI on
profit factor is 0.926-1.851, so that assumption is not safe. This re-runs the
evaluation under three worlds: the observed edge, no edge at all, and the lower
confidence bound.
"""
import random
from statistics import mean, median

random.seed(20260904)
START, TARGET, MLL, LOCK = 50000.0, 3000.0, 2000.0, 50100.0
BASE = 500.0

raw = []
for ln in open("v17_mgc_trades.txt"):
    p = ln.strip().split("|")
    raw.append([float(p[3]), abs(float(p[4])), float(p[6])])

obs_mean = mean(r[0] for r in raw)
BLK = 5

def make(shift, ntr):
    """shift is subtracted from every trade P&L to move expectancy."""
    out = []
    while len(out) < ntr:
        s = random.randrange(0, len(raw) - BLK)
        for pnl, n, mae in raw[s:s+BLK]:
            out.append([pnl - shift, n, mae + (shift if shift > 0 else 0)])
    return out[:ntr]

def run(seq, frac):
    bal, peak, floor_ = START, START, START - MLL
    locked = False
    day, di, c = {}, 0, 0
    for pnl, n, mae in seq:
        risk = min(750.0, (bal - floor_) * frac)
        k = int(risk * n / BASE)
        if k < 1:
            continue
        m = k / n
        if bal - mae * m < floor_:
            return "bust"
        bal += pnl * m
        c += 1
        if c >= 1:
            c = 0; di += 1
        day[di] = day.get(di, 0.0) + pnl * m
        if bal < floor_:
            return "bust"
        if not locked:
            peak = max(peak, bal)
            floor_ = peak - MLL
            if peak >= START + MLL:
                floor_, locked = LOCK, True
        if bal >= START + TARGET:
            w = [v for v in day.values() if v > 0]
            if w and max(w) / (bal - START) <= 0.50:
                return "pass"
    return "grinding"

N = 20000
worlds = [
    ("observed edge  (PF 1.33)", 0.0),
    ("lower CI bound (PF ~0.93)", obs_mean * 1.30),
    ("NO edge        (PF 1.00)", obs_mean),
]
print(f"observed mean P&L/trade ${obs_mean:.2f}\n")
print(f"{'world':>26} {'frac':>6} {'pass%':>7} {'bust%':>7} {'grind%':>8}")
for lab, shift in worlds:
    for frac in (0.15, 0.20):
        res = [run(make(shift, 400), frac) for _ in range(N)]
        print(f"{lab:>26} {frac*100:>5.0f}% {res.count('pass')/N*100:>7.2f} "
              f"{res.count('bust')/N*100:>7.2f} {res.count('grinding')/N*100:>8.2f}")

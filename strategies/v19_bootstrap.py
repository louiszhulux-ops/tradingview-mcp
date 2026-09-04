#!/usr/bin/env python3
"""
Honest bust/pass probabilities for buffer-based sizing.

The overlapping-window sweep reported 0% bust, but 159 overlapping start points
on one 11-month history are ~159 views of the SAME sequence, not 159 independent
trials. This resamples instead: a moving-block bootstrap (blocks of 5 consecutive
trades, preserving local win/loss clustering) builds many independent synthetic
histories with the same edge and the same clustering, then runs each through the
full LucidDaily rule set.
"""
import random, datetime as dt
from statistics import median

START, TARGET, MLL, LOCK = 50000.0, 3000.0, 2000.0, 50100.0
BASE = 500.0
random.seed(20260904)

raw = []
for ln in open("v17_mgc_trades.txt"):
    i, et, xt, pf, qt, ru, md = ln.strip().split("|")
    raw.append((float(pf), abs(float(qt)), float(md), int(et)))

span_days = (raw[-1][3] - raw[0][3]) / 86400000.0
rate = len(raw) / span_days                      # trades per calendar day
print(f"{len(raw)} trades over {span_days:.0f} calendar days = {rate:.3f}/day")
print(f"observed: win% {sum(1 for r in raw if r[0]>0)/len(raw)*100:.1f}  "
      f"net ${sum(r[0] for r in raw):,.0f}")

BLK = 5
def synth(ntr):
    out = []
    while len(out) < ntr:
        s = random.randrange(0, len(raw) - BLK)
        out.extend(raw[s:s+BLK])
    return out[:ntr]

def run(seq, frac, fixed, tr_per_day):
    bal, peak, floor_ = START, START, START - MLL
    locked = False
    day, dayi, cnt = {}, 0, 0
    for pnl, n, mae, _ in seq:
        risk = fixed if fixed else min(750.0, (bal - floor_) * frac)
        k = int(risk * n / BASE)
        if k < 1:
            continue
        m = k / n
        if bal - mae * m < floor_:
            return "bust", bal
        bal += pnl * m
        cnt += 1
        if cnt >= tr_per_day:
            cnt = 0; dayi += 1
        day[dayi] = day.get(dayi, 0.0) + pnl * m
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
    return "timeout", bal

N = 20000
tpd = max(1, round(1 / rate)) and max(1, round(rate)) or 1
tpd = max(1, round(rate * 1.0)) or 1
tpd = 1  # ~0.7 trades/day -> at most one per day; conservative for consistency rule

for days in (60, 90, 120):
    ntr = max(5, int(round(rate * days)))
    print(f"\n=== {days} days ~ {ntr} trades, {N:,} bootstrap runs ===")
    print(f"{'sizing':>14} {'pass%':>7} {'bust%':>7} {'time%':>7} {'medBal':>9} {'p05Bal':>9}")
    configs = [("fixed $200", None, 200.0), ("fixed $300", None, 300.0),
               ("fixed $400", None, 400.0),
               ("buffer 20%", 0.20, None), ("buffer 25%", 0.25, None),
               ("buffer 30%", 0.30, None)]
    for lab, frac, fx in configs:
        res, bals = [], []
        for _ in range(N):
            r, b = run(synth(ntr), frac, fx, tpd)
            res.append(r); bals.append(b)
        bals.sort()
        print(f"{lab:>14} {res.count('pass')/N*100:>7.2f} {res.count('bust')/N*100:>7.2f} "
              f"{res.count('timeout')/N*100:>7.2f} {median(bals):>9.0f} {bals[N//20]:>9.0f}")

# ---- the decision-relevant question ----
# LucidDaily evaluations have no hard time limit. "Timeout" therefore is not a
# failure -- it just means still trading. Run to resolution instead.
print("\n=== run to resolution (no time limit, cap 400 trades) ===")
print(f"{'sizing':>14} {'pass%':>7} {'bust%':>7} {'unres%':>7} {'med trades to pass':>20}")
for lab, frac, fx in [("fixed $200", None, 200.0), ("fixed $300", None, 300.0),
                      ("buffer 15%", 0.15, None), ("buffer 20%", 0.20, None),
                      ("buffer 25%", 0.25, None), ("buffer 30%", 0.30, None)]:
    res, ntrades = [], []
    for _ in range(N):
        seq = synth(400)
        bal, peak, floor_ = START, START, START - MLL
        locked = False
        day, dayi, cnt, k_used = {}, 0, 0, 0
        out = "unres"
        for pnl, n, mae, _t in seq:
            risk = fx if fx else min(750.0, (bal - floor_) * frac)
            k = int(risk * n / BASE)
            if k < 1:
                continue
            m = k / n
            k_used += 1
            if bal - mae * m < floor_:
                out = "bust"; break
            bal += pnl * m
            cnt += 1
            if cnt >= tpd:
                cnt = 0; dayi += 1
            day[dayi] = day.get(dayi, 0.0) + pnl * m
            if bal < floor_:
                out = "bust"; break
            if not locked:
                peak = max(peak, bal)
                floor_ = peak - MLL
                if peak >= START + MLL:
                    floor_, locked = LOCK, True
            if bal >= START + TARGET:
                w = [v for v in day.values() if v > 0]
                if w and max(w) / (bal - START) <= 0.50:
                    out = "pass"; break
        res.append(out)
        if out == "pass":
            ntrades.append(k_used)
    p = res.count("pass") / N * 100
    b = res.count("bust") / N * 100
    u = res.count("unres") / N * 100
    mt = median(ntrades) if ntrades else float("nan")
    print(f"{lab:>14} {p:>7.2f} {b:>7.2f} {u:>7.2f} {mt:>20.0f}")

# how big a single loss would it take to bust buffer sizing?
print("\n=== residual tail risk ===")
worst = max(-r[0] for r in raw)
print(f"  largest observed loss ${worst:.0f} = {worst/BASE:.2f}x intended risk")
for f in (0.15, 0.20, 0.25, 0.30):
    print(f"  buffer {f*100:.0f}%: a single trade would have to lose "
          f"{1/f:.1f}x its intended risk in one event to cross the floor")

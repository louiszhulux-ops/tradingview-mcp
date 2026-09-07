#!/usr/bin/env python3
"""
Does buffer-based (anti-martingale) sizing beat fixed sizing on the LucidDaily
50K evaluation?

Fixed sizing has one dial and it trades pass rate against bust rate roughly 1:1.
Buffer-based sizing risks a fraction of the distance to the max-loss floor, so
the position is small exactly when a loss would be fatal and grows only once a
cushion exists. Same trades, same edge -- only the execution layer changes.
"""
import datetime as dt
from statistics import median

START, TARGET, MLL, LOCK = 50000.0, 3000.0, 2000.0, 50100.0
BASE = 500.0

rows = []
for ln in open("v17_mgc_trades.txt"):
    i, et, xt, pf, qt, ru, md = ln.strip().split("|")
    rows.append(dict(et=int(et), xt=int(xt), pnl=float(pf),
                     n=abs(float(qt)), mae=float(md)))

def mult(risk, n):
    """exact MGC rescale: risk per contract = BASE/n"""
    k = int(risk * n / BASE)
    return None if k < 1 else k / n

def run(seq, days, mode, param, cap=1000.0):
    bal, peak, floor_ = START, START, START - MLL
    locked = False
    day = {}
    taken = 0
    t0 = seq[0]["et"]
    for t in seq:
        if (t["et"] - t0) / 86400000.0 > days:
            break
        risk = param if mode == "fixed" else min(cap, max(50.0, (bal - floor_) * param))
        m = mult(risk, t["n"])
        if m is None:
            continue
        taken += 1
        if bal - t["mae"] * m < floor_:
            return "bust", bal, taken
        bal += t["pnl"] * m
        d = dt.datetime.utcfromtimestamp(t["xt"] / 1000).date()
        day[d] = day.get(d, 0.0) + t["pnl"] * m
        if bal < floor_:
            return "bust", bal, taken
        if not locked:
            peak = max(peak, bal)
            floor_ = peak - MLL
            if peak >= START + MLL:
                floor_, locked = LOCK, True
        if bal >= START + TARGET:
            w = [v for v in day.values() if v > 0]
            if w and max(w) / (bal - START) <= 0.50:
                return "pass", bal, taken
    return "timeout", bal, taken

def sweep(days, mode, params, label):
    print(f"\n=== {days}-day window — {label} ===")
    print(f"{'param':>8} {'pass%':>7} {'bust%':>7} {'time%':>7} {'trades':>7} {'medBal':>9} {'edge':>7}")
    best = None
    for p in params:
        res, bals, tk = [], [], []
        for s in range(len(rows) - 3):
            r, b, t_ = run(rows[s:], days, mode, p)
            if t_ == 0:
                continue
            res.append(r); bals.append(b); tk.append(t_)
        n = len(res)
        if not n:
            continue
        pa = res.count("pass") / n * 100
        bu = res.count("bust") / n * 100
        lab = f"${p:.0f}" if mode == "fixed" else f"{p*100:.0f}%buf"
        print(f"{lab:>8} {pa:>7.1f} {bu:>7.1f} {res.count('timeout')/n*100:>7.1f} "
              f"{sum(tk)/n:>7.1f} {median(bals):>9.0f} {pa-bu:>7.1f}")
        if best is None or pa - bu > best[0]:
            best = (pa - bu, lab, pa, bu)
    if best:
        print(f"  best pass-minus-bust: {best[1]} -> {best[2]:.1f}% pass / {best[3]:.1f}% bust")

for days in (60, 90):
    sweep(days, "fixed",  [200, 250, 300, 400, 500], "fixed risk")
    sweep(days, "buffer", [0.05, 0.075, 0.10, 0.125, 0.15, 0.20, 0.25], "risk = % of buffer to floor")

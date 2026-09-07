#!/usr/bin/env python3
"""Extend the buffer-sizing sweep: higher fractions, longer windows, and a
check on WHERE the zero bust rate comes from."""
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
    k = int(risk * n / BASE)
    return None if k < 1 else k / n

def run(seq, days, frac, cap, track=None):
    bal, peak, floor_ = START, START, START - MLL
    locked = False
    day = {}
    taken = skipped = 0
    t0 = seq[0]["et"]
    for t in seq:
        if (t["et"] - t0) / 86400000.0 > days:
            break
        risk = min(cap, (bal - floor_) * frac)
        m = mult(risk, t["n"])
        if m is None:
            skipped += 1
            continue
        taken += 1
        if track is not None:
            track.append(risk)
        if bal - t["mae"] * m < floor_:
            return "bust", bal, taken, skipped
        bal += t["pnl"] * m
        d = dt.datetime.utcfromtimestamp(t["xt"] / 1000).date()
        day[d] = day.get(d, 0.0) + t["pnl"] * m
        if bal < floor_:
            return "bust", bal, taken, skipped
        if not locked:
            peak = max(peak, bal)
            floor_ = peak - MLL
            if peak >= START + MLL:
                floor_, locked = LOCK, True
        if bal >= START + TARGET:
            w = [v for v in day.values() if v > 0]
            if w and max(w) / (bal - START) <= 0.50:
                return "pass", bal, taken, skipped
    return "timeout", bal, taken, skipped

print("buffer-based sizing: risk = frac x (balance - MLL floor), capped")
for days in (60, 90, 120, 180):
    print(f"\n=== {days}-day window ===")
    print(f"{'frac':>6} {'cap':>6} {'pass%':>7} {'bust%':>7} {'time%':>7} {'trades':>7} {'skip%':>6} {'medBal':>9}")
    for frac in (0.20, 0.25, 0.30, 0.35, 0.40):
        for cap in (750.0, 1500.0):
            res, bals, tk, sk = [], [], [], []
            for s in range(len(rows) - 3):
                r, b, t_, s_ = run(rows[s:], days, frac, cap)
                if t_ == 0:
                    continue
                res.append(r); bals.append(b); tk.append(t_); sk.append(s_)
            n = len(res)
            if not n:
                continue
            print(f"{frac*100:>5.0f}% {cap:>6.0f} {res.count('pass')/n*100:>7.1f} "
                  f"{res.count('bust')/n*100:>7.1f} {res.count('timeout')/n*100:>7.1f} "
                  f"{sum(tk)/n:>7.1f} {sum(sk)/max(1,sum(sk)+sum(tk))*100:>6.1f} {median(bals):>9.0f}")

# where does the zero bust rate come from?
print("\n=== risk actually taken, frac 25% cap 750 ===")
tr = []
for s in range(len(rows) - 3):
    run(rows[s:], 90, 0.25, 750.0, track=tr)
tr.sort()
print(f"  n={len(tr)}  min ${tr[0]:.0f}  p10 ${tr[len(tr)//10]:.0f}  "
      f"median ${tr[len(tr)//2]:.0f}  p90 ${tr[9*len(tr)//10]:.0f}  max ${tr[-1]:.0f}")
print(f"  fraction of bets below $250: {sum(1 for x in tr if x<250)/len(tr)*100:.1f}%")

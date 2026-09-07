#!/usr/bin/env python3
"""
LucidDaily 50K evaluation over the V17 sweep trade sequence.

Trades are real backtest fills on COMEX_MINI:MGC1! (the actual contract the
account trades), 15m, short-only liquidity-sweep reclaims with a structural
stop capped at $12, 3R target, flat by 19:30 UTC. Commission is per-contract.

Because these are real MGC fills, contract counts are exact and rescaling risk
is exact too: risk per contract = 500/n, so at risk R the position is
floor(R*n/500) contracts.
"""
import datetime as dt
from statistics import median

START, TARGET, MLL, LOCK = 50000.0, 3000.0, 2000.0, 50100.0
BASE_RISK = 500.0

rows = []
for ln in open("v17_mgc_trades.txt"):
    i, et, xt, pf, qt, ru, md = ln.strip().split("|")
    rows.append(dict(i=int(i), et=int(et), xt=int(xt), pnl=float(pf),
                     n=abs(float(qt)), mfe=float(ru), mae=float(md)))

def scale(risk, n):
    k = int(risk * n / BASE_RISK)
    return None if k < 1 else k / n

def run(seq, risk, days, intraday=True):
    bal, peak, floor_ = START, START, START - MLL
    locked = False
    day = {}
    taken = skipped = 0
    t0 = seq[0]["et"]
    for t in seq:
        if (t["et"] - t0) / 86400000.0 > days:
            break
        m = scale(risk, t["n"])
        if m is None:
            skipped += 1
            continue
        taken += 1
        if intraday and bal - t["mae"] * m < floor_:
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
            wins = [v for v in day.values() if v > 0]
            if wins and max(wins) / (bal - START) <= 0.50:
                return "pass", bal, taken, skipped
    return "timeout", bal, taken, skipped

n_all = len(rows)
wins = [r for r in rows if r["pnl"] > 0]
print("V17 sweep on COMEX_MINI:MGC1! -- LucidDaily 50K evaluation")
print(f"trades {n_all}  win% {len(wins)/n_all*100:.1f}  "
      f"net ${sum(r['pnl'] for r in rows):,.0f}  "
      f"mean contracts {sum(r['n'] for r in rows)/n_all:.1f}")
print(f"risk per contract: ${BASE_RISK/ (sum(r['n'] for r in rows)/n_all):.0f} "
      f"(median stop ${median(BASE_RISK/r['n'] for r in rows)/10:.2f})")

for days in (30, 45, 60, 90):
    print(f"\n=== {days}-day evaluation window, all {n_all-3} start points ===")
    print(f"{'risk':>7} {'%acct':>6} {'pass%':>7} {'bust%':>7} {'time%':>7} {'trades':>7} {'medBal':>9}")
    for risk in (150, 200, 250, 300, 400, 500, 700):
        res, bals, tk = [], [], []
        for s in range(n_all - 3):
            r, b, t_, _ = run(rows[s:], risk, days)
            if t_ == 0:
                continue
            res.append(r); bals.append(b); tk.append(t_)
        n = len(res)
        if not n:
            print(f"{risk:>7}   no tradable setups")
            continue
        print(f"{risk:>7} {risk/500:>5.1f}% "
              f"{res.count('pass')/n*100:>7.1f} {res.count('bust')/n*100:>7.1f} "
              f"{res.count('timeout')/n*100:>7.1f} {sum(tk)/n:>7.1f} {median(bals):>9.0f}")

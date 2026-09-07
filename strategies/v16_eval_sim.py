#!/usr/bin/env python3
"""
LucidDaily 50K evaluation simulation over the V16 breakout trade sequence.

Every trade is a real backtest fill (XAUUSD 1H, Donchian-20 breakout, long only,
hard 3xATR stop + 3xATR trail), exported from TradingView with entry/exit time,
P&L, position size, and true per-trade MFE/MAE.

Account rules modelled:
  start 50,000 | target +3,000 | max loss limit 2,000, trailing, locks at 50,100
  once balance clears 52,000 | consistency: largest winning day <= 50% of profit
"""
import datetime as dt
from statistics import median

START, TARGET, MLL, LOCK = 50000.0, 3000.0, 2000.0, 50100.0

rows = []
for ln in open("v16_trades_raw.txt"):
    i, et, xt, pf, qt, ru, md = ln.strip().split("|")
    rows.append(dict(i=int(i), et=int(et), xt=int(xt), pnl=float(pf),
                     oz=float(qt), mfe=float(ru), mae=float(md)))

BASE_RISK = 500.0   # the risk the export was generated at

def scale_for(risk, oz):
    """MGC granularity: 1 contract = 10oz. The backtest sized in ounces at
    BASE_RISK, so stop distance ~= BASE_RISK/oz. Contracts affordable at
    `risk` = floor(risk / (stop * 10)) = floor(risk * oz / (BASE_RISK*10))."""
    n = int(risk * oz / (BASE_RISK * 10))
    if n < 1:
        return None                      # cannot take the trade: one contract
    return n * 10.0 / oz                 # P&L multiplier vs the exported fill

def run(seq, risk, days, intraday_dd=True):
    """Return 'pass' | 'bust' | 'timeout' plus stats."""
    bal, peak, floor_ = START, START, START - MLL
    locked = False
    day_pnl, taken, skipped = {}, 0, 0
    t0 = seq[0]["et"]
    for t in seq:
        if (t["et"] - t0) / 86400000.0 > days:
            break
        m = scale_for(risk, t["oz"])
        if m is None:
            skipped += 1
            continue
        taken += 1
        # intraday excursion against us while the trade is open
        if intraday_dd and bal - t["mae"] * m < floor_:
            return "bust", bal, taken, skipped, day_pnl
        bal += t["pnl"] * m
        d = dt.datetime.utcfromtimestamp(t["xt"] / 1000).date()
        day_pnl[d] = day_pnl.get(d, 0.0) + t["pnl"] * m
        if bal < floor_:
            return "bust", bal, taken, skipped, day_pnl
        if not locked:
            peak = max(peak, bal)
            floor_ = peak - MLL
            if peak >= START + MLL:
                floor_, locked = LOCK, True
        if bal >= START + TARGET:
            wins = [v for v in day_pnl.values() if v > 0]
            biggest = max(wins) if wins else 0.0
            profit = bal - START
            if biggest / profit <= 0.50:
                return "pass", bal, taken, skipped, day_pnl
            # target hit but consistency fails -> must keep trading smaller
    return "timeout", bal, taken, skipped, day_pnl

def sweep(days, label):
    print(f"\n=== {label}: {days}-day evaluation window ===")
    print(f"{'risk':>7} {'pass%':>7} {'bust%':>7} {'time%':>7} {'trades':>7} {'skip%':>7} {'medBal':>9}")
    for risk in (200, 300, 400, 500, 700, 1000, 1500):
        res, bals, tk, sk = [], [], [], []
        for s in range(len(rows) - 3):
            r, b, taken, skipped, _ = run(rows[s:], risk, days)
            if taken == 0:
                continue
            res.append(r); bals.append(b); tk.append(taken); sk.append(skipped)
        n = len(res)
        if not n:
            print(f"{risk:>7} {'-- no tradable setups at this risk --':>50}")
            continue
        p = res.count("pass") / n * 100
        b_ = res.count("bust") / n * 100
        t_ = res.count("timeout") / n * 100
        skp = sum(sk) / max(1, sum(sk) + sum(tk)) * 100
        print(f"{risk:>7} {p:>7.1f} {b_:>7.1f} {t_:>7.1f} {sum(tk)/n:>7.1f} {skp:>7.1f} {median(bals):>9.0f}")

print("V16 breakout -- LucidDaily 50K evaluation, every historical start point")
print(f"trades {len(rows)}  net ${sum(r['pnl'] for r in rows):,.0f}  "
      f"win% {sum(1 for r in rows if r['pnl']>0)/len(rows)*100:.1f}")

for days, lbl in ((30, "one month"), (60, "two months"), (90, "three months"), (180, "six months")):
    sweep(days, lbl)

# how coarse is MGC at current gold prices?
print("\n=== contract granularity ===")
recent = rows[-40:]
for risk in (300, 500, 700, 1000):
    ok = sum(1 for t in recent if scale_for(risk, t["oz"]) is not None)
    print(f"  risk ${risk}: {ok}/40 of the last 40 setups are takeable with >=1 MGC")
avg_stop = sum(BASE_RISK / t["oz"] for t in recent) / len(recent)
print(f"  mean stop distance in the last 40 setups: ${avg_stop:.0f}  "
      f"-> ${avg_stop*10:.0f} risk per MGC contract")

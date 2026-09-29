#!/usr/bin/env python3
"""
What a forward paper test can and cannot settle for V38.
MGC 5m, vol>1.5, 1 concurrent: 1.39 trades/day, sd ~1.43R per trade.
"""
import math
from statistics import NormalDist
nd = NormalDist()
SD, TPD = 1.43, 1.39
E_MEAS, E_SF = 0.1178, 0.0801

print("1. CONFIRMATION is out of reach\n")
print(f"{'if true edge is':>24} {'t=1.65':>17} {'t=2.0':>17} {'t=3.0':>17}")
for lab, E in (("measured +0.118R", E_MEAS), ("selection-free +0.080R", E_SF)):
    row = f"{lab:>24}"
    for t in (1.65, 2.0, 3.0):
        n = (t*SD/E)**2
        row += f" {n:>7.0f}tr/{n/TPD:>5.0f}d"
    print(row)
print("\n   Reaching t=2 needs 1.2-2.5 YEARS of forward trading. No forward test")
print("   on a useful horizon can confirm an edge this small.\n")

print("="*74)
print("2. DISCONFIRMATION by t-test is also weak\n")
print("   Power to reject 'edge >= +0.080R' at 95% when the truth is exactly 0:\n")
print(f"{'trades':>8} {'days':>7} {'SE':>7} {'power':>8}")
for n in (30, 60, 100, 250, 400, 800):
    se = SD/math.sqrt(n)
    print(f"{n:>8} {n/TPD:>7.0f} {se:>7.3f} {nd.cdf((E_SF-1.645*se)/se):>7.1%}")
print("\n   Only 22% at 250 trades, 30% at 400. A pure t-test forward is nearly")
print("   useless in both directions. Anything claiming otherwise is wrong.\n")

print("="*74)
print("3. What the forward test IS for\n")
print("   (a) EXECUTION VALIDATION -- ~30 trades (3 weeks), pass/fail, not")
print("       statistical. If any of these fails, the backtest is not")
print("       describing reality and the edge estimate is void:")
print("         - realised stop distance within 10% of 1.5 x ATR(14) at entry")
print("         - realised slippage <= 1 tick per side on average")
print("         - trade frequency 1.0-1.9 /day        (backtest 1.39)")
print("         - win rate 30-45%                     (backtest 37.0%)")
print("         - every trade resolves within 288 bars")
print()
print("   (b) DRAWDOWN TRIPWIRE -- the account-protecting rule, and the one")
print("       that actually binds. The worst historical drawdown was 13.5R.")
bufR = 2000/105.56
for k in (13.5, 15.0, 18.9):
    print(f"         {k:>5.1f}R = ${k*105.56:>7.0f} = {k/bufR:>4.0%} of the $2,000 buffer")
print("       STOP the forward test at 15R of drawdown. That is past the")
print("       historical worst (evidence the model is wrong) and still short")
print("       of the 18.9R that ends the account.")
print()
print("   (c) A LONG-RUN LEDGER. Every trade recorded, reviewed quarterly.")
print("       The edge either accumulates over years or it does not.\n")

print("="*74)
print("4. Pre-registered stop/continue rules, fixed now\n")
print("   CONTINUE if: execution checks pass AND drawdown < 15R")
print("   STOP if:     any execution check fails")
print("                OR drawdown reaches 15R")
print("                OR cumulative R < -8R after 100+ trades")
print("   DECLARE NOTHING either way before 400 trades (~10 months).")
print("   The strategy is NOT confirmed by a profitable first month, and it is")
print("   NOT refuted by a losing one. Both are inside one standard deviation.")

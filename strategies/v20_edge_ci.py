#!/usr/bin/env python3
"""
Is the edge real, or is PF 1.33 inside the noise band of 162 trades?

Everything downstream -- the 72% pass rate, the buffer sizing -- is conditional
on the edge existing. This bootstraps the per-trade P&L to put a confidence
interval on expectancy and profit factor before any more tuning happens.
"""
import random
from statistics import mean, stdev

random.seed(20260904)
pnl = []
for ln in open("v17_mgc_trades.txt"):
    parts = ln.strip().split("|")
    pnl.append(float(parts[3]))

n = len(pnl)
m = mean(pnl)
s = stdev(pnl)
se = s / (n ** 0.5)
gp = sum(p for p in pnl if p > 0)
gl = -sum(p for p in pnl if p < 0)

print(f"n = {n}")
print(f"mean P&L/trade  ${m:,.2f}   sd ${s:,.2f}   standard error ${se:,.2f}")
print(f"t-statistic     {m/se:.2f}")
print(f"profit factor   {gp/gl:.3f}")
print(f"net             ${sum(pnl):,.0f}")

B = 100000
means, pfs = [], []
for _ in range(B):
    samp = [pnl[random.randrange(n)] for _ in range(n)]
    means.append(mean(samp))
    g = sum(p for p in samp if p > 0)
    l = -sum(p for p in samp if p < 0)
    pfs.append(g / l if l > 0 else float("inf"))
means.sort(); pfs.sort()

def ci(v, lo=0.025, hi=0.975):
    return v[int(lo * len(v))], v[int(hi * len(v))]

ml, mh = ci(means)
pl_, ph = ci(pfs)
print(f"\n{B:,} bootstrap resamples")
print(f"  95% CI on mean P&L/trade : ${ml:,.2f} .. ${mh:,.2f}")
print(f"  95% CI on profit factor  : {pl_:.3f} .. {ph:.3f}")
print(f"  P(expectancy <= 0)       : {sum(1 for x in means if x <= 0)/B*100:.2f}%")
print(f"  P(profit factor <= 1.0)  : {sum(1 for x in pfs if x <= 1.0)/B*100:.2f}%")

# how many trades would be needed to call it at 95%?
need = (1.96 * s / m) ** 2
print(f"\n  trades needed for a 95%-significant result at this effect size: {need:,.0f}")
print(f"  at 0.48 trades/day that is {need/0.48/365:.1f} years of data")

# split-half disagreement
h = n // 2
a, b = pnl[:h], pnl[h:]
print(f"\n  first half  mean ${mean(a):,.2f}  PF {sum(p for p in a if p>0)/-sum(p for p in a if p<0):.3f}")
print(f"  second half mean ${mean(b):,.2f}  PF {sum(p for p in b if p>0)/-sum(p for p in b if p<0):.3f}")

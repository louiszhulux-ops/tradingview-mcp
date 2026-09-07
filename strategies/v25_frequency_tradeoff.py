#!/usr/bin/env python3
"""
The confluence/frequency trade-off, measured.

The plan needs 4 trades a day. Every filter that raises win rate cuts trade
count. These are the actual counts from the ICT 2022 screen on gold 15m over
11 months, so the trade-off can be priced rather than argued about.
"""
MONTHS = 11.0
DAYS   = MONTHS * 21          # trading days

funnel = [
    ("raid + MSS only",                   137),
    ("+ displacement",                    129),
    ("+ FVG retracement entry",            57),
    ("+ killzone (full published model)",  13),
    ("+ proper liquidity pool (PDL/PDH)",   9),
]

print(f"{'variant':>36} {'trades':>7} {'per month':>10} {'per day':>8} {'x short of 4/day':>17}")
for name, n in funnel:
    per_m = n / MONTHS
    per_d = n / DAYS
    print(f"{name:>36} {n:>7} {per_m:>10.1f} {per_d:>8.2f} {4/per_d:>16.0f}x")

print()
print("what 4 trades/day would require: 4 x 21 x 11 = %d trades in the same window" % (4*21*11))
print("the LOOSEST variant delivers 137, which is %.0fx short." % (924/137))
print()
print("And the loosest variant is the one with no filters -- pooled mean R of")
print("-0.110 across four markets, t = -2.74. The filters that might create an")
print("edge are precisely the ones that destroy the frequency.")
print()

# what win rate is actually needed at 4 trades/day to hit the target?
print("If 4 trades/day WERE available, here is what each win rate delivers")
print("at 1% risk ($500) on a $50,000 account, 1:1 RR, costs 0.08R:")
print(f"{'win rate':>9} {'meanR':>8} {'$/trade':>9} {'$/month (80 trades)':>21}")
for w in (0.50, 0.52, 0.55, 0.60, 0.65, 0.75):
    m = w * (1 - 0.08) - (1 - w) * (1 + 0.08)
    print(f"{w*100:>8.0f}% {m:>+8.3f} {m*500:>+9.0f} {m*500*80:>+21,.0f}")
print()
print("55% would comfortably pass the evaluation every month. The bar is not high.")
print("Nothing tested reaches it: best mechanical entry at 1:1 was 52.1%, and that")
print("was gold's uptrend leaking into a long-only signal.")

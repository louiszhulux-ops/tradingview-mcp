# V23 — testing the high-win-rate hypothesis properly

You were right that I had never tested this. Every earlier screen used a 2:1
target on a 1×ATR stop, which *structurally* produces a ~35% win rate. That
measured one corner of the space and said nothing about the corner you asked
about. This tests the whole curve: 10 signals × 4 reward:risk settings, on gold
15m, confirmed on Nasdaq.

## You were also right that win rate rises

| reward:risk | best observed win rate |
|---|---|
| 1.5 : 1 | 41.8% |
| 1 : 1 | 52.1% |
| 1 : 2 | 67.8% |
| 1 : 3 | **74.4%** |

**A 75% win rate is real and reachable.** Trend-continuation short hits 74.4%,
trend-continuation long 73.8%. So the premise holds — small, high-probability
trades genuinely do win most of the time.

## But the breakeven line rises faster

With costs at 0.08R, breakeven win rate is `(1 + 0.08) / (RR + 1)`:

| RR | need | pure chance | best observed | vs chance | vs need |
|---|---|---|---|---|---|
| 1.5 : 1 | 43.2% | 40.0% | 41.8% | +1.8 | **−1.4** |
| 1 : 1 | 54.0% | 50.0% | 52.1% | +2.1 | **−1.9** |
| 1 : 2 | 72.0% | 66.7% | 67.8% | +1.1 | **−4.2** |
| 1 : 3 | 81.2% | 75.2% | 74.4% | −0.8 | **−6.8** |

Every cell across 10 signals and 4 settings is negative. The 75% win rate is
achievable at 1:3 — where you need 81%.

## The "pure chance" column is the whole story

A driftless price with a stop at −1R and a target at +RR hits the target
`1/(RR+1)` of the time by pure chance, with no skill involved at all. At 1:1
that is 50%. At 1:3 it is 75%.

**So a 75% win rate is not evidence of a good strategy — at 1:3 it is what a coin
flip delivers.** Every signal tested lands within ±2 points of its own coin-flip
baseline. That is the finding: these entries carry essentially no information,
and the win rate is being set by where the stop and target sit, not by the entry.

## Why tightening the target makes it harder, not easier

This is the part that runs against intuition, and it is the reason the plan can't
work as specified:

    cost is a fixed fraction of the STOP, but a win only pays RR × stop

| RR | cost as % of each win | edge over chance needed |
|---|---|---|
| 1.5 : 1 | 5.3% | +3.2 pts |
| 1 : 1 | 8.0% | +4.0 pts |
| 1 : 2 | 16.0% | +5.3 pts |
| 1 : 3 | 24.2% | +6.0 pts |

Going for smaller, more frequent wins means each win is smaller while each round
trip costs the same. So you need a *bigger* edge over chance, not a smaller one,
and you pay it more often. Four trades a day at 1:1 pays the spread four times a
day for wins worth one stop each.

## What this does and does not close

**Closed:** the specific plan of "high win rate at 1:1 or 1.5:1 from a mechanical
entry". At 1:1 the best mechanical entry in this family reaches 52.1% against
54.0% needed. To make 1:1 work you need roughly **54–55% sustained**, which is
+4 points over chance. Nothing tested delivers more than +2.1, and that +2.1 is
gold's uptrend leaking into a long-only signal, not an edge.

**Not closed:** the possibility that a *better entry* clears that bar. The target
is now precisely quantified, which it never was before:

> **beat the coin-flip win rate by 4 percentage points, consistently, and 1:1 works.**

That is the number to aim at. It is a much smaller and better-defined target than
"find a profitable strategy" — 54% at 1:1, or 44% at 1.5:1.

## Honest note on your own results

Your manual trading may well clear that bar; nothing here measures it. What this
does show is that the bar is not cleared by *where you put the stop and target*.
Moving to 1:1 does not create an edge, it only changes how the same coin flip is
scored. Whatever is working in your trading is in the entry selection — which
levels, and when you decline — and that is the thing still not written down.

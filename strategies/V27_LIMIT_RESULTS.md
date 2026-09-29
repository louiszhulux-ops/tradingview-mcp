# V27 — limit orders vs market orders

V26 measured the only consistent effect in this project: gross expectancy of
about **−0.02R** across four markets and ten triggers, *before any fees*. Every
one of those triggers was a market order fired after a bar had already moved.
A breakout entry buys the top of the bar that just printed the high.

The single exception in all the testing was the ICT fair-value-gap entry (+0.12R)
— and it is the only **limit** order I ever tested. So this tests the class.

## The effect is real and direction-neutral

Gross expectancy in R, before any costs, 15m, RR 1:1:

| market | market orders | limit (1×ATR) | limit (3×ATR) | Δ limit−market |
|---|---|---|---|---|
| MGC gold | −0.0138 | +0.0047 | **+0.0137** | +0.028 |
| MNQ nasdaq | −0.0295 | −0.0428 | −0.0377 | −0.008 |
| MCL crude | −0.0205 | +0.0030 | **+0.0099** | +0.030 |
| 6E euro | −0.0196 | +0.0059 | **+0.0092** | +0.029 |
| **mean** | **−0.0209** | −0.0073 | **−0.0012** | **+0.0196** |

Switching from taking liquidity to providing it is worth about **+0.02R per
trade**, and it turns gross expectancy positive in three of four markets. Costs
were charged identically in both screens (a full tick of slippage) even though a
resting limit never crosses the spread — so the improvement is selection, not
accounting. It is a structural property of the order type, independent of any
signal, and it is roughly the same size as the entire cost of trading gold.

**This is the most useful thing found in the project so far**, because it applies
to any strategy: enter with resting limits, not with market orders on a trigger.

## What is not real

Depth appeared to help — on gold, resting at 3×ATR from the mean gave +0.018R
long and +0.009R short, the first time the both-directions control has ever
passed. It does not survive:

| market | long | short | both positive? |
|---|---|---|---|
| MGC | +0.018 | +0.009 | ✅ |
| MNQ | −0.039 | −0.063 | ❌ |
| MCL | −0.070 | −0.043 | ❌ |
| 6E | −0.094 | −0.113 | ❌ |

1 of 4, needed 3. It also peaks at depth 3 and reverses at depth 5 — a single
interior peak, which is the characteristic shape of noise.

## Why it still is not enough

Removing adverse selection moves gross expectancy from −0.021R to −0.001R. That
is a real gain of the right size, and it lands on **approximately zero**.

Costs are 0.021R on gold and 0.118R on the euro. Zero is not enough. You cannot
pay a 0.02R toll out of a 0.00R edge.

## What this narrows the problem to

The arithmetic is now completely explicit:

    net expectancy = gross edge − cost_R
    gross edge at a 1xATR horizon  ≈  0.00R   (measured, 4 markets, ~16k trades)
    cost_R = cost_per_contract / (stop × pointValue)

Both terms are now measured rather than assumed. There are exactly two ways out
and no others:

1. **Find a horizon where the gross edge is genuinely positive.** Everything in
   this project has tested a ~1×ATR stop with a 24-bar time limit — a short
   horizon. V16 found profit factor 2.1 out-of-sample using a 3×ATR stop on 1H,
   which is a far longer horizon, and it was never re-examined after the cost
   model was corrected. Documented time-series momentum literature says the edge
   lives at long horizons, not short ones.
2. **Drive cost_R down.** It falls linearly with stop width, so the same trade at
   a 4×ATR stop costs a quarter as much in R. Long horizons help here too.

Both point the same way, and both point away from the four-trades-a-day
requirement. That is the next thing to test.

# V35 — Execution test: the edge does not survive contact with the instrument

`V35_fade_prod.pine` takes the V33 fade and runs it as a real `strategy()`:
buffer-based sizing, four concurrent fades each with its own protective stop
from the bar it opens on, and the verified LucidFlex rules (trailing end-of-day
MLL, $100 lock, 50% consistency) evaluated inside the script.

Unlike the V32–V34 measurement rigs, a Pine strategy fills an order submitted on
bar *N* at the **open of bar N+1**. The rigs entered at the **close of bar N**.
That difference turns out to matter more than everything else in this project.

## What the rigs measured vs what the strategy earns

Zero commission, zero slippage in every row, so this isolates signal and fill
timing only.

| symbol | what it is | trades | net | per trade | outcome |
|---|---|---|---|---|---|
| OANDA:XAUUSD | spot gold — **not tradeable** | 1,813 | +$1,780 | +$0.98 | running |
| COMEX_MINI:MGC1! | micro gold — the real instrument | 281 | −$375 | −$1.33 | running |
| CME_MINI:MNQ1! | micro nasdaq | 198 | −$119 | −$0.60 | running |
| CBOT:ZN1! | 10y note | 149 | −$1,734 | −$11.64 | **BUST** |
| CME:6E1! | euro | 554 | +$3,063 | +$5.53 | **PASS day 54** |

Then 6E1! with its real costs put back (V26: $7.29 round turn, 1 tick = $6.25):

| symbol | cost | trades | net | per trade | outcome |
|---|---|---|---|---|---|
| CME:6E1! | zero | 554 | +$3,063 | +$5.53 | PASS day 54 |
| CME:6E1! | **real** | 138 | −$612 | −$4.44 | **BUST** |

The one market that passed, passed only because it was not paying to trade.

## Three drags, each about the size of the edge

**1. Fill timing — measured on identical data.** On XAUUSD, the same signal:

- V33 indicator rig, filled at the trigger bar's close: **+0.093R**
- V35 strategy, filled at the next bar's open: **+0.052R**

Entry timing alone costs **~0.041R**. The mean reversion the fade is capturing
has already half happened by the time the next 5-minute bar opens.

**2. Feed vs instrument.** At the same zero cost, XAUUSD spot returns +0.052R
and MGC1! futures returns **−0.040R**. A ~0.09R gap between a broker's spot
feed and the contract that is actually traded. Gold was measured on
OANDA:XAUUSD throughout V32–V34; that number was never available to trade.

**3. Transaction cost.** 0.03R on micro gold, 0.18R on 6E at these stop widths
(V26's measured figures, applied to a 1.5×ATR stop on 5m).

Any one of the three consumes the +0.081R cross-market gross edge. Together
there is nothing left, and ZN1! — which had the **largest** gross edge in the
whole V33 sample at +0.169R — busts the account.

## Why ZN inverted so violently

ZN's win rate falls from ~38% in the rig to 28.2% in the strategy. ZN trades in
1/64ths ($15.625 a tick) and its 5m ATR is small, so a 1.5×ATR stop is only a
handful of ticks wide. The close-to-next-open gap is then a large fraction of
the whole stop distance. **The tighter the stop in ticks, the more of the edge
the fill timing eats** — and it eats it in proportion to R, not in absolute
terms.

## What this retroactively says about V32–V34

The cross-market result stands as a measurement — 8/8 markets, t = 3.5 — but of
a quantity that is not tradeable at 5m with 1.5×ATR stops. I should have run
the execution test before extending the measurement to eight markets and
before computing pass probabilities from it. The Monte Carlo numbers in
`V33_V34_FADE_RESULTS.md` (81% pass at the point estimate) were built on the
rig's fill assumption and are superseded by this file.

## The bar any future signal has to clear

This is the reusable result. At 5m with a 1.5×ATR stop on these instruments the
combined drag is roughly **0.15R**: ~0.04R fill timing, ~0.03–0.18R cost, plus
whatever gap exists between the series measured and the contract traded. So a
5-minute signal needs about **+0.15R gross just to break even**, and the best
gross edge found anywhere in this project was +0.081R pooled, +0.169R in a
single market that then busted.

All three drags shrink as a fraction of R when the stop gets wider — which is
what V28 ("the edge lives at horizons the account excludes") and V32's wide
grid were both pointing at. The obstacle there is contract granularity: one
micro gold contract with a 30-point stop risks $300, which is 6.7R of a $2,000
buffer, far too coarse for buffer-based sizing on a 50K account.

## Honest status

The fade is the best-supported signal this project has produced and it does not
survive execution on the instruments the evaluation allows. I am not going to
tune it further: the failure is not in the parameters, it is that the drag is
larger than the edge on every tradeable contract tested.

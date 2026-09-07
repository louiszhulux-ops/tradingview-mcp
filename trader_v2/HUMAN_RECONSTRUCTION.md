# Human trade reconstruction — thesis-labelled, not sweep-labelled

Every manual trade recoverable from the project. Classified by **what the
trader expected price to do after entry**, not by which side of a level the
entry sat on.

| # | Source | HTF bias | Liquidity event | Immediate reaction | Entry location | **Thesis** | Destination | Outcome |
|---|---|---|---|---|---|---|---|---|
| N1 | narrative | bearish — "yesterday's drop, OB held" | sold through Asia | continued lower | 15m imbalance + 1m OB, **above** price | **CONTINUATION short** | 4H/1H unmitigated OBs | ~600p win |
| N2 | narrative | bearish — "bearish bias all week" | **swept the Asia LOW** | rallied to an OB, 1m CHOCH | OB tap **above** the swept low, on the retest of the CHOCH | **CONTINUATION short** | PDL, Monday's low | ~500p win |
| N3 | narrative | bullish — "Asia spike, liquidity broken", above VWAP | liquidity broken in Asia | held above VWAP | 5m imbalance fill, 1m inverted + 3m engulfing | **CONTINUATION long** | external liq + round 4600 | ~400p win |
| A1 | Aug 31 verified | bullish intraday — 4396 → 4449 rally | none identified | pullback to 4435 | **buy 4434**, stop 4429 (5 pts) | **CONTINUATION long** | prior high ~4464 | exit 4479, **9.0R** |
| A2 | Aug 31 verified | — rally exhausted at 4464 | swept the session high | failed to hold | **sell 4460**, stop 4468 (8 pts) | **REVERSAL short** | session low | exit 4419, **5.1R** |
| L1 | loss note | bearish | reached an unmitigated OB | "induced" the level, ran through | short at the OB | **REVERSAL short** at a level | expected a correction | stopped; thesis later right by 350+p |

**4 continuation, 2 reversal.** The process is not uniformly one or the other —
it is context-conditional, which is the point.

## The decisive case: N2

> bearish bias → **swept the Asia low** → rallied → OB tap → 1m CHOCH → **SELL**

The sweep is of a **low**, and the trade is a **short**. The sweep is *with* the
bearish bias — it is evidence the move is real — and the entry is at a supply
zone **above** the swept level, taken after a rally.

## What my F0 does with that identical event

For a low sweep, F0 sets the retest limit **at the swept level** and fills when
`low <= level`, i.e. when price comes back **down** to it.

- F0 **long** = buy at the swept level on the return → fading the sweep.
- F0 **short** = sell at the swept level as price falls into it → a breakdown.

**Neither is N2.** N2's entry is *above* the swept level, reached by a rally,
at a different structure entirely. My engine cannot generate that trade — the
limit is in the wrong place.

## The other case: the user's own worked example

> HTF bullish → pullback takes sell-side liquidity → reclaims → bullish
> displacement → retest → **long**

Here the direction *does* match F0-long. So F0-long silently contains **two
different populations**:

1. bull-bias, low-sweep, reclaim, displacement → **continuation long** (the
   trade the human takes)
2. bear-bias, low-sweep, no reclaim requirement → **counter-trend long** (a
   fade the human would not take)

F0 averages them together, which is why it lands near zero (+0.037R).

## Preliminary reading

This is consistent with **A — representation problem**, on two counts:

- F0's entry *location* cannot express the N2-style continuation trade at all.
- F0's *population* mixes bias-aligned continuation with counter-trend fading,
  with no bias, reclaim or displacement condition to separate them.

But "consistent with" is not proof. The ablation below tests whether adding
bias, reclaim and displacement to the identical event stream actually recovers
an edge — if it does not, the continuation process is not in the data at this
resolution and the answer is B or C instead.

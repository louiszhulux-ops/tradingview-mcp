# V40/V41 — opportunity engine: first results

## The correction that started this

`MANUAL_PROCESS_ANALYSIS.md` recorded, months ago, that the human uses liquidity
sweeps as **continuation** evidence aligned to a multi-day bias, while the bot
**fades** them. I then built V33–V38 as an increasingly refined sweep-fading
system — the inverse of the documented human method. That is the single largest
process error in this project.

## The human benchmark (verified trades, Aug 31)

| | entry | stop | exit | R |
|---|---|---|---|---|
| T1 BUY | 4434 | 4429 (5 pts) | 4479 | **9.0R** |
| T2 SELL | 4460 | 4468 (8 pts) | 4419 | **5.1R** |

Two trades, one session, +$4,300 on 5 micros. The bot caps every trade at 2R and
averages +0.12R. **The gap is not win rate — it is R per trade.**

## V40 — opportunities, not trades (MGC 5m, ~1,400 opportunities)

Every sweep of PDH/PDL, Asia H/L or a swing level, logged with context and the
full forward distribution. Entry at the next bar's open, stop beyond the swept
extreme, adverse excursion checked first.

- R/ATR ≈ **1.10**
- P(1R) 43–48%, P(2R) 28–31%, P(3R) 20–23%, **P(5R) 12–16%**
- E@2R negative in every cell; short beat long in every cell

**12–16% of opportunities reach 5R.** The right tail the human harvests exists
and is large. The bot's 2R cap discards all of it.

Bias conditioning (1H EMA and prior-day-range) did **not** discriminate: short
won in all six cells either way. That is the gold barrier asymmetry from V32,
not a conditional edge.

## V41 — the retest, which is what the human actually does

Human sequence: sweep → wait → price returns to the level (second touch) →
enter **on** the level → stop just beyond the sweep extreme.

Entering at the retest rather than at the next open moves the stop from ~1.1 ATR
to a wick-width:

| | V40 (enter after sweep) | V41 (enter on retest) |
|---|---|---|
| R / ATR | 1.10 | **0.65** |

Same absolute move, ~1.7× more R. This is the mechanism by which a 5-point stop
on gold becomes a 9R trade, and it is a structural difference from everything
built in V15–V38.

Best cells (MGC 5m, 1,223 filled retests):

| cell | n | L E@3R | S E@3R |
|---|---|---|---|
| Asia swept HIGH | 183 | −0.311 | **+0.323** |
| NY swept LOW | 240 | −0.312 | **+0.226** |
| NY swept HIGH | 271 | −0.071 | −0.012 |
| London swept LOW | 139 | −0.225 | +0.005 |

## What this reframes

Passing in ~2 days needs ~12R at the human's sizing ($250 risk on a $2,000
buffer). At 2.5 opportunities/day and +0.3R average that is 15 days, not 2.
**The human is not taking average trades — they are catching the right tail.**

So the open question is now precisely stated, and it is the quality model:
**can the top decile of the R-distribution be identified in advance?**

Not yet answered. Next step is to cell on setup-quality features available at
entry (sweep depth, reclaim speed, level importance, volatility state) and
measure P(5R) per cell rather than mean R.

# V19 — buffer-based sizing: the first change that beats the frontier

## Diversification was the plan, and it failed

The idea was a second uncorrelated sleeve, since combining uncorrelated streams
raises return-to-drawdown without needing a better signal. Four candidates were
built and run in isolation with identical execution discipline:

| sleeve | n | win% | PF | net |
|---|---|---|---|---|
| sweep reclaim, short (the working one) | 160 | 38.8% | **1.341** | +$16,271 |
| opening range breakout | 39 | 23.1% | 0.298 | −$9,978 |
| VWAP stretch fade | 57 | 33.3% | 0.832 | −$3,068 |
| sweep reclaim, long + trend regime | 72 | 29.2% | 0.828 | −$4,027 |
| sweep reclaim, long + counter regime | 49 | 18.4% | 0.446 | −$10,502 |

No second profitable sleeve. Correlation is irrelevant when the candidate loses
money — adding it makes the portfolio worse regardless.

The ORB failure is structurally interesting: filtering for an opening range
narrow enough to give a sub-$12 stop selects precisely the low-volatility days
on which breakouts fail. The stop-width filter and the edge are anti-correlated.

Regime does at least confirm robustness. Splitting the working sleeve by daily
trend gives PF 1.308 (HTF down, 57 trades) and PF 1.356 (HTF up, 103 trades)
against 1.341 combined — the edge does not depend on trend regime.

## What did work: size from the buffer, not from a fixed dollar amount

Fixed risk has one dial and it trades pass rate against bust rate roughly 1:1.
Risking a fixed **fraction of the distance to the max-loss floor** makes the
position small exactly when a loss would be fatal, and lets it grow only once a
cushion exists.

20,000-run moving-block bootstrap (blocks of 5 consecutive trades, preserving
win/loss clustering), run to resolution rather than to an arbitrary deadline —
LucidDaily evaluations have no hard time limit, so "didn't finish yet" is not a
failure:

| sizing | pass | bust | still grinding | median trades to target |
|---|---|---|---|---|
| fixed $200 | 72.9% | 27.1% | 0% | 47 |
| fixed $300 | 56.4% | 43.6% | 0% | 22 |
| **buffer 15%** | **78.9%** | **0.00%** | 21.1% | 50 |
| **buffer 20%** | **71.9%** | **0.00%** | 28.1% | 32 |
| buffer 25% | 64.5% | 0.00% | 35.5% | 21 |
| buffer 30% | 56.9% | 0.00% | 43.1% | 16 |

Buffer sizing **dominates** fixed sizing rather than trading against it: at 15%
it beats fixed $200 on pass rate (78.9% vs 72.9%) *and* removes 27 points of
bust risk. The failure mode changes from "account blown, pay for a reset" to
"still trying".

Earlier fixed-window results are consistent — at 60 days, buffer 25% gives 37.8%
pass / 0.0% bust against fixed $300's 39.6% pass / 32.8% bust.

## Why the zero is structural, and where the real risk actually is

After a full-size loss the buffer becomes `buffer × (1 − frac)`. That decays
geometrically and never reaches zero, so **a losing streak cannot bust the
account**. Busting requires a *single* trade losing `1/frac` times its intended
risk in one event:

| frac | single-event loss required to breach |
|---|---|
| 15% | 6.7× intended risk |
| 20% | 5.0× |
| 25% | 4.0× |
| 30% | 3.3× |

The largest loss across 162 real MGC fills is **$621 = 1.24× intended risk**,
because the stop is now genuinely enforced. So the residual risk is not a bad
run — it is a gap, halt or limit move that blows through the stop by 5×. That
risk is real and is not captured by any backtest on this data. It is the reason
to prefer 15–20% over 25–30%.

The zero also does real work through a second mechanism worth naming: when the
buffer gets small, the position rounds below one MGC contract and the trade is
**declined outright**. In the 90-day sweep that is 21% of signals. Declining a
trade you cannot size properly is legitimate, but it means part of the safety
comes from trading less, not from trading better.

## Single evaluation attempts, run in TradingView on MGC1!

`stopAtTarget` on, buffer 20%, so each run models one real attempt:

| start | outcome | trades | days | net | max DD |
|---|---|---|---|---|---|
| 2025-10-01 | **target reached** | 24 | 32 | +$3,455 | $1,543 |
| 2026-01-01 | still grinding after 8 months | 68 | — | −$139 | $1,776 |
| 2026-05-01 | target reached | 3 | 2.5 | +$3,415 | $234 |

The middle row is the honest one and matches the bootstrap's 28%: eight months of
work for nothing, but the account survives — max drawdown $1,776 against a $2,000
limit, and it never came closer than $236 of buffer.

**The third row would not actually pass.** Three trades over 2.5 days puts far
more than 50% of the profit on one day, so the consistency rule blocks it. The
Pine engine does not enforce consistency; the Python simulator does, and treats
that path as "keep trading smaller until the ratio comes in line". Any run that
reaches the target suspiciously fast should be read as a consistency failure, not
a pass.

## Where this leaves things

Recommended configuration: MGC1!, 15m, short sweep-reclaim, structural stop
capped at $12, 3R target, NY session, flat by 19:30 UTC, stop for the day at −2R,
**risk = 15–20% of the distance to the max-loss floor**, capped at $750.

Expect roughly a 72–79% chance of passing, a median of 32–50 trades (about two to
three months at 0.48 trades/day), and — conditional on stops being honoured — no
path that blows the account. Roughly a quarter of attempts stall out without
reaching the target.

That is a real answer to the original question, and it is not the answer that was
asked for: it is not $3,000 in a week. The edge is PF 1.33; nothing in this
session made it stronger. What changed is that the execution layer now converts
that modest edge into a high-probability, low-ruin outcome instead of a coin flip.

# Autonomous Day Trader — Architecture

## A. Why the old system failed

Four distinct failures, in order of how much damage they did.

**1. It optimised the wrong objective.** Every version maximised annual P&L or
profit factor. The actual objective is *probability of passing an evaluation
within a few days under a specific rule set*. Those are not the same target, and
optimising the first actively harms the second — most visibly through the
consistency rule, where a big day makes passing **harder**, not easier.

**2. It got two of the account's rules wrong.** The Max Loss Limit was modelled
as an intraday equity floor. It is an **end-of-day limit on closing balance**;
before it locks, intraday excursions do not tighten it at all. Every previous
risk calculation was therefore far too punitive, and the sizing that followed was
far too small. Separately, consistency was never modelled during the search, so
the system was tuned to produce exactly the lumpy equity curve that fails it.

**3. It tested unconditionally.** Every screen asked "does this trigger work on
average, everywhere?" A discretionary trader never claims that. The claim is
conditional: this setup, at this location, in this regime. Measuring the
unconditional average of a conditional edge dilutes it toward zero by
construction — and that is exactly the number the old system kept reporting.

**4. It confused "no evidence" with "evidence of no".** Twelve strategy families
failed, and the conclusion drawn was that no short-horizon edge exists. What was
actually shown is narrower: *no unconditional, single-timeframe, market-order
trigger has an edge.* That is a much weaker statement, and V30 disproves the
broader one.

## B. What was architecturally wrong

The old system was one Pine expression: `if signal then enter`. Everything —
context, entry, stop, size, exits — collapsed into a single conditional. That
shape makes several necessary things impossible:

| needed | why the old shape prevents it |
|---|---|
| different behaviour per regime | one condition cannot branch on market state without becoming unmaintainable |
| setup-specific statistics | with one signal there is only one number to look at |
| a quality score | binary fire/don't-fire has no room for "this is a B, take it smaller" |
| location awareness | the trigger fired wherever it fired, level or no level |
| knowing why a trade was skipped | nothing was recorded, so over-filtering was invisible |
| evaluation-aware sizing | sizing was a constant, disconnected from account state |

Most damaging: **there was no record of rejected opportunities.** The system
could have been rejecting every good trade and there was no way to see it.

## C. What the discretionary trader is doing that the bot was not

Three things, and all three are now measured rather than asserted.

**Reading context before looking for trades.** V30 measured this: the identical
trigger returns −0.075R with the trend and −0.119R in chop, with counter-trend
and range ordered monotonically in between, across ~10,000 trades. The trader's
claim that "the same setup is not the same trade in different conditions" is
correct and worth 0.044R.

**Caring where price is.** V30 also measured this: being at a previous day
high/low, VWAP, opening-range edge or prior swing is worth **+0.043R in trending
regimes and roughly zero in chop** — the interaction a trader asserts, visible in
the data. In the with-trend regime specifically it is +0.13 (gold), +0.21
(nasdaq), +0.09 (crude) and −0.29 (S&P): 3 of 4.

**Not chasing.** V27 measured this: resting a limit order rather than firing a
market order at a trigger is worth **+0.02R**, direction-neutral and
signal-independent, because a market entry buys the top of the bar that just
printed the high. That is roughly the entire cost of trading gold.

## D. New architecture

Seven components, separated so each can be measured and replaced independently.

```
MARKET DATA (multi-timeframe)
        |
   CONTEXT ENGINE ......... trend / range / expansion / volatility,
        |                   HTF bias, key levels, session, opening range
   REGIME CLASSIFIER ...... with-trend | counter-trend | range | chop
        |
   SETUP DETECTION ........ 6 named setups, each anchored to a level
        |
   QUALITY MODEL .......... A+ / A / B / C from regime x location x
        |                   confirmation; C is rejected
   RISK ENGINE ............ size from stop distance and evaluation state
        |
   EXECUTION ENGINE ....... limit / stop / market chosen per setup
        |
   TRADE MANAGEMENT ....... partials, trail, time stop, session flat
        |
   JOURNAL + MISSED LOG ... every decision AND every rejection, with the
                            forward outcome of what was skipped
```

**What lives where.** Pine can carry the context engine, regime classifier, setup
detection, quality scoring and bar-resolution execution. It cannot do
tick-accurate fills, an economic calendar, broker reconciliation, persistent
learning, or cross-instrument exposure netting — those are the external
components listed in §47 and are specified separately rather than pretended into
Pine.

**The evaluation engine is separate and authoritative** (`prop_rules.py`). It
owns the rules, all configurable, with LucidFlex 25K/50K/100K/150K as data rather
than assumptions. It exposes the two behaviours the old system lacked:
`ideal_daily_target(days)` — the per-day profit that reaches the target while
satisfying consistency — and `profit_needed_for_consistency()`, which answers
"given what I have already made, how much more do I need for the largest day to
be legal?"

**The single most important behavioural rule** falls out of that engine: the bot
targets `target / N` per day and **stops trading when it hits it**. Making $3,000
on day one does not pass the evaluation; it raises the required total to $6,000.
Every previous version of this project would have taken that trade.

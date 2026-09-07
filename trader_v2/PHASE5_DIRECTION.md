# Phase 5 / Deliverable 6 — should global HTF direction stay a filter?

**No. Remove it.** The evidence is now three independent failures, and one of
them is worse than a failure.

## 1. What was measured

| test | result |
|---|---|
| six ex-ante bias models, folds A+B, 10 cells | best (4H EMA20/50) beat the no-filter control by **+0.082R** |
| the honest test — kept vs discarded, not kept vs zero | separates in **6/10 cells**, +0.160R, **90% CI [−0.055, +0.376]** — contains zero |
| fold C, frozen spec, run once | **−0.074R**, failed all four gate criteria |
| fold C, kept vs discarded | **inverted: −0.207R.** Bias-opposed sweeps did *better* |
| prev-day structure as a bias model | **−0.249R, t = −2.11** — significantly harmful |
| HTF displacement as a bias model | +0.002R, 3/10 — indistinguishable from noise |

## 2. The structural reason, which matters more than the numbers

In **6 of 10 cells the 4H trend never changed direction across the entire 22-day
fold C.** Three cells armed nothing at all; three armed on every single sweep
(config 2 came back byte-identical to config 1). Only MNQ and MCL saw both
directions.

A 4H EMA20/50 cross flips a handful of times per quarter. **It is a regime
label, not a per-trade decision variable.** Asked "what is my bias at 09:42
today", it returns the same answer it returned for the previous three weeks. It
cannot discriminate between the trades taken on any given day, which is exactly
what a per-trade filter is for.

That is also why it is expensive: it removes **51.7% of all fills** in exchange
for a decision that carries almost no information at trade frequency.

## 3. Can direction be determined locally instead?

The engine already does this and has always done it — the point was obscured by
the bias layer sitting on top:

- **The sweep sets the direction by construction.** A sweep of a low arms a long
  at that low; a sweep of a high arms a short. No external label is consulted.
- The base sweep-rejection family is therefore **direction-agnostic as a
  policy** and **directionally determined per instance**. So is range
  mean-reversion (F6). These are the two families that survived their own tests.
- The user's own ex-ante plan works the same way: `HUMAN_TRADE_REGISTER.md` §4
  records a supply zone *and* a demand zone marked simultaneously on 2026-08-31,
  with price deciding which one traded. **Locations fixed in advance, direction
  left to the market.**

## 4. What replaces it

Nothing. Direction comes from the setup instance. The filter budget that the 4H
bias was consuming — half of all fills — is better spent on **room**, which is
direction-agnostic, asks a different question ("is there space to the next
opposing level"), and is the only component that survived fold C intact
(+0.050 → +0.043).

## 5. The caveat I am not going to bury

On fold C the bias-**opposed** population returned **+0.139R** against the
bias-aligned **−0.068R**. Read literally that says fade the 4H trend. I do not
believe that and I am not proposing it: n = 287 vs 315 on a single 22-day
window, and the CI on the difference spans zero. But it is the second time the
continuation framing has failed to survive contact with out-of-sample data, and
the correct conclusion from two failures is **stop conditioning on global trend
altogether**, not flip the sign and try again.

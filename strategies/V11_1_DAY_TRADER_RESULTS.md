# V11.1 "day trader" rebuild — what raising trade count and win rate actually costs

All runs: OANDA:XAUUSD 15m, 2025-10-01 → 2026-09-03 (~11 months), $50,000,
execution cost modelled at $0.20/oz per side (~$0.40 round-trip).

## Headline: V11.1 vs the previous V8.3

| | V8.3 | **V11.1** |
|---|---|---|
| Trades | 136 (~12/mo) | **232 (~21/mo, ~5/week)** |
| Win rate | 32.4% | **37.1%** |
| Profit factor | 1.475 | 1.352 |
| Net profit | +$6,072 (+12.1%) **at 0.75% risk** | +$5,669 (+11.3%) **at 0.50% risk** |
| Max drawdown | 3.01% | 3.81% |
| Sortino | 1.01 | **1.46** |

V11.1 makes almost the same money on **two-thirds of the risk per trade**, with
70% more trades and a better Sortino. Per unit of risk taken it is clearly the
better system. Its raw profit factor is lower because it trades more often for
smaller, more frequent wins — which is what "trade like a day trader" means.

## What produced the improvement: fixed targets, not partials

The old system aimed at distant liquidity (2.5R+), so a position occupied its
slot for a long time. A fixed 1.5R target closes faster and frees the slot.
Single-position sweep, 0.5% risk:

| Trend target | Trades | Win% | PF | Net | Max DD |
|---|---|---|---|---|---|
| 1.0R | 244 | 44.3% | 1.322 | +$4,755 | 4.60% |
| **1.5R** | **232** | **37.1%** | **1.352** | **+$5,669** | **3.81%** |
| 2.0R | 223 | 31.8% | 1.277 | +$4,621 | 4.55% |

Clean interior optimum — 1.5R is best on profit, PF *and* drawdown at once.

## Negative results (measured, not assumed)

**Partial exits are a trap for this system.** Banking 50% at 1R with the runner
moved to breakeven:

| Config | Trades | Win% | PF | Net | Max DD |
|---|---|---|---|---|---|
| No partials | 124 | 28.2% | 1.463 | +$5,430 | 3.26% |
| Partial + breakeven | 525 | **51.2%** | 1.173 | +$2,238 | 4.39% |
| Partial, no breakeven | 465 | 39.8% | 1.159 | +$2,416 | 5.19% |

Partials deliver exactly the 51% win rate asked for and **less than half the
money**, with more drawdown. Largest win collapses from $2,174 to ~$640. The
breakeven stop *helps* (4.39% DD vs 5.19%) — the partial itself is the problem.
This system's edge is entirely in letting winners reach target.

**Concurrency + fixed targets:** 4 concurrent positions, 1.5R → 308 trades but
PF 1.038 and +$679. Correlated entries stop out together; largest win $228.
Single position is strictly better here.

**5-minute timeframe:** not testable over this window. TradingView's bar limit
means the 11-month range does not exist at 5m — buy & hold over the loaded data
was $922 vs $7,854 at 15m, so the 99-trade result covers a few weeks. No
conclusion drawn.

## Honest arithmetic on the funded-evaluation goal

At 0.5% risk this system returns **~1.03%/month** with 3.81% max drawdown.
Return and drawdown both scale roughly linearly with risk per trade:

| Risk/trade | ~Monthly | ~Max DD | Time to +6% ($3,000) |
|---|---|---|---|
| 0.50% | 1.03% | 3.8% | ~5.8 months |
| 0.75% | 1.55% | 5.7% | ~3.9 months |
| 1.00% | 2.06% | 7.6% | ~2.9 months |

**$3,000 in one week is 6% in five sessions.** This system averages ~0.24% per
week at 0.5% risk. Reaching 6% in a week would need roughly 25x the risk — about
12% per trade — which puts expected drawdown near 90%. That is not a tuning
problem; no configuration of this or any honest strategy produces 6%/week
repeatably. Sized to survive, this is a 3-6 month path to an evaluation target,
not a one-week one.

## On consecutive losses

At a 37% win rate, the expected longest losing streak across 232 trades is
**~12 in a row**. That is a normal event, not a malfunction. Two things keep it
survivable:
- Risk is 0.5%/trade, so 12 straight full stops is ~6% of the account.
- The daily loss limit (default 2%) halts trading for the day once hit, so a
  bad streak cannot run past an evaluation's daily rule. Observed max drawdown
  is 3.81%, below the 6% the raw streak math implies, because the guard and the
  3-loss cooldown cut streaks short.

## Still true, still unaddressed
- **Everything here is in-sample.** Every parameter, including the 1.5R target
  chosen above, was fitted on this same 11 months of XAUUSD data.
- Limit exits are assumed to fill whenever price touches them.
- No demo forward test has been run. That remains the only honest way to find
  out whether 1.352 profit factor survives contact with a live broker.

# Testing the 1:1 / high-win-rate approach — XAUUSD 15m, 11 months, costs on

The proposal: risk 1% ($500) per trade, aim for 1:1, get ~6 net winners a week.
This is how most funded traders are taught to size, so it deserved a real test
rather than an argument. Two new levers were built to test it:

- `minConf` — a HARD confluence filter. Previously a low-confluence setup was
  merely sized down to 0.6x; it was never rejected. Now it can be.
- `rangeFixedR` — puts the range module on the same fixed R target as the trend
  module, so a *pure* 1:1 system can be measured.

## The arithmetic being tested

At 1:1, weekly net = risk x trades x (2 x winrate - 1). Six *net* winners is the
requirement, not six gross wins:

| Win rate | Trades/week for $3,000 |
|---|---|
| 50% | impossible |
| 60% | 30 |
| 70% | 15 |
| 80% | 10 |

## Result: 52.8% win rate, and that is not enough

Pure 1:1 on both modules, 0.5% risk, single position, 246 trades:

| Metric | Value |
|---|---|
| Trades | 246 |
| **Win rate** | **52.85%** |
| Profit factor | **0.998** |
| Net profit | **-$25** |
| Max drawdown | 4.98% |

**A CORRECTION.** An earlier run in this session showed 57.4% win rate over 68
trades and I reported it as encouraging. It was not real. At 1% risk the 2%
daily-loss limit halts the day after two losers, so that 68-trade sample had its
losing stretches truncated by the guard — the throttle was selecting the sample.
Dropping risk to 0.5% makes the guard non-binding, and the same code then takes
246 trades at **52.8%**. Trust 52.8%.

## Why 52.8% is not above breakeven

A nominal 1:1 does not realise as 1:1. Measured over those 246 trades:

- Largest win **$248**, largest loss **$252**. The win is capped at exactly 1R.
  The loss is not — a gap through the stop costs more than 1R.
- Costs are $2.88/trade against ~$250 of risk (1.15% of R).
- Effective reward:risk = **0.89**, not 1.00.
- Breakeven win rate at 0.89 RR = **52.90%**. Achieved: 52.85%.

So the 1:1 version lands almost exactly on its breakeven line. **This is the
structural problem with 1:1: it caps the upside at exactly 1R while leaving the
downside tail open, so the bar moves above 50% and the strategy has to clear a
bar it barely reaches.** A wider target dilutes that asymmetry.

## Compared on the metric that actually decides it

What matters is not which win rate looks better, but the **margin over the
breakeven win rate for that reward:risk**:

| Config | Win rate | Effective RR | Breakeven WR | Margin |
|---|---|---|---|---|
| Pure 1:1 | 52.85% | 0.89 | 52.90% | **-0.05 pts (none)** |
| **V11.1 @ 1.5R** | 37.07% | 2.29 | 30.35% | **+6.7 pts (22% above)** |

The 37% strategy is far healthier than the 53% one. V11.1 clears its bar by 22%;
the 1:1 build misses its bar entirely.

## The confluence filter did not rescue either config

| Config | minConf | Trades | Win% | PF | Net |
|---|---|---|---|---|---|
| 1:1 (1% risk, guard binding) | 0 | 83 | 55.4% | 1.18 | +$1,246 |
| 1:1 (1% risk, guard binding) | 1 | 68 | 57.4% | 1.25 | +$1,416 |
| 1:1 (1% risk, guard binding) | 2 | 24 | 50.0% | 1.00 | +$13 |
| **V11.1 @ 1.5R** | **0** | **232** | **37.1%** | **1.352** | **+$5,669** |
| V11.1 @ 1.5R | 1 | 198 | 37.9% | 1.211 | +$2,879 |

On the 1.5R config the filter raises win rate by 0.8 points and **halves net
profit** (PF 1.352 -> 1.211, drawdown 3.81% -> 5.71%). Rejected.

## Frequency cannot be tuned up either

Loosening the gates on the best config — 3 concurrent positions, minimum spacing
cut from 3 bars to 1 — moved trade count only 68 -> 77 over eleven months, and
cost win rate (57.4% -> 55.8%) and PF (1.250 -> 1.214). **The setups are not
being blocked; they do not exist.** This strategy finds roughly 20 valid setups
a month on XAUUSD 15m, not 20 a week.

## What the plan actually requires vs what exists

At V11.1's measured numbers (0.5% risk): +$5,669 over 11 months = **~$118/week**;
at 1% risk, ~$236/week. The target is $3,000/week — a **12-13x gap**, closable
only by 12x the trades or 12x the risk. Twelve times the risk is a ~46% expected
drawdown.

**The single instrument is the ceiling, and it is a frequency ceiling, not a
win-rate ceiling.** The honest route to more trades is more markets: the same
logic on 8 uncorrelated symbols gives ~8x the trades. If they are genuinely
uncorrelated, return scales ~8x while drawdown scales ~sqrt(8) = 2.8x — a real
improvement in return-per-drawdown, and the only lever found in this session
that increases trades without degrading edge. It requires validating the
strategy per instrument first, which has not been done.

## Status
- Everything remains in-sample on one instrument.
- No demo forward test has been run.
- V11.1 remains the recommended configuration; nothing tested here beat it.

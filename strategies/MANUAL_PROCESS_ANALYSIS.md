# Encoding the discretionary process — what transferred and what didn't

Source: three written trade breakdowns (2 shorts ~600p and ~500p, 1 long ~400p).

## 1. Structure common to all three

| Element | T1 | T2 | T3 | Encodable |
|---|---|---|---|---|
| Bias set BEFORE the day, multi-day narrative | yesterday's drop, OB held | "bearish bias all week" | Asia spike, liquidity broken | yes |
| Asia session builds the level | dropped through Asia | swept the Asia low | broke liquidity in Asia | yes |
| Execution at/after **London open** | "GB had another big sell-off" | "Coming into the GB open" | "By the time GB opened" | yes |
| Direction = **continuation** of bias | "continue selling with the trend" | "continued looking for sells" | "looking for continuations" | yes |
| VWAP as directional confirmation | — | "trending below the VWAP" | "trending above the VWAP" | yes |
| Entry = pullback into imbalance/OB | 15m imbalance + 1m OB | OB tap → 1m CHOCH | 5m imbalance fill | partly |
| Waits for a **second** touch | "price retested them" | "waited for price to retest the CHOCH" | consolidation, induced liquidity | yes |
| LTF trigger on 1m/3m | 1m OB | CHOCH → retest → BOS → imbalance retest | 1m inverted + 3m engulfing | **no** |
| Target = pre-identified HTF liquidity | 4H/1H unmitigated OBs | PDL, Monday's low | external liq + round 4600 | yes |
| Pure judgement | "understood the magnitude" | "nothing more bearish than a failed high" | "the odds were" | **no** |

## 2. The bot had the core premise inverted

Same raw event, opposite conclusion:

- **Bot** (setup 5, measured PF 0.744 standalone): sweep of a low → **BUY**, fading the sweep as a reversal.
- **T2**: sweep of the Asia low → wait for the pullback up → **SELL**, treating the sweep as *confirmation* of the existing bias.

The whole system was built to fade liquidity sweeps. The notes use sweeps as
continuation evidence. That is a genuine finding independent of anything below.

## 3. Ablation of the encodable scaffolding (MGC 15m, Oct 2025 – Apr 2026, 1:1, costs on)

| Configuration | Trades | Win% | PF | Net |
|---|---|---|---|---|
| **Full process** (bias + Asia + London + 2nd touch) | 30 | 50.0% | 0.756 | −$1,020 |
| − second touch | 30 | 50.0% | 0.756 | −$1,020 (not binding) |
| − Asia level | 30 | 50.0% | 0.756 | −$1,020 (not binding) |
| − bias (beyond prev-day range) | 110 | 49.1% | 0.939 | −$763 |

The binding constraints are the bias condition and the London window; the Asia
and second-touch filters never actually excluded a trade the others allowed.
**None of it is profitable in isolation.**

## 4. What this does and does not show

**Does show:** the mechanical scaffolding — multi-day bias, Asia level, London
window, VWAP pullback, second retest, continuation direction — does not by
itself carry an edge. The skeleton is not the edge.

**Does NOT show** that the discretionary trading has no edge. Three specific gaps:

1. **The entry trigger is proxied, badly.** The notes describe a precise
   sequence: 1m CHOCH → retest of the CHOCH → BOS → entry on the retest of the
   imbalance the BOS left behind. I substituted "price touches VWAP and rejects",
   which is far cruder. The real trigger lives on 1m, and TradingView's bar limit
   makes a 7-month 1m backtest impossible here.
2. **Zone selection is judgement.** "These zones alone were not strong enough"
   is a quality assessment across many candidate OBs/imbalances. Nothing in the
   notes makes that rule explicit.
3. **30 trades is a small sample** — too small to conclude much either way.

## 5. What I need to go further

- **Losing trades, in the same detail.** Three winners cannot separate a real
  setup from a well-told hindsight narrative. The losers are where the actual
  entry criteria get tested.
- **Stop placement.** None of the three notes says where the stop went. Without
  it there is no R, and therefore no expectancy — only a direction.
- **What "pips" means here.** 600 pips on gold is either a $6.00 or a $60.00
  move depending on convention; that is a 10x difference in R:R and it changes
  every conclusion about sizing and the consistency rule.
- **Which timeframe the entry is actually taken on**, since 1m cannot be
  validated over a long window on this platform.

## 6. Honest read

The notes contain real, encodable structure, and they corrected a genuine error
in the bot's premise. But the parts that transferred cleanly are the parts that
don't produce an edge, and the parts that might produce the edge — LTF entry
sequencing and zone-quality judgement — are exactly the parts that didn't
transfer. That is consistent with the earlier conclusion: if the discretionary
edge is real, it is not in the 15-minute OHLC scaffolding.

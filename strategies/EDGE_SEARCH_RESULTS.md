# Edge search — 9 day-trade concepts on MGC, LucidDaily-compatible shape

Goal: find a signal with the shape LucidDaily's 50% consistency rule requires —
**high win rate, modest R, several trades per session** — rather than the
rare-large-winner shape that rule structurally forbids.

Method: a setup lab where every concept runs under **identical mechanics** —
same ATR(14) stop, same fixed 1:1 target, same 2 contracts, same costs
($1.24/order, 1 tick slippage). The only variable is the entry condition. All
parameters left at textbook defaults; nothing tuned.

- **In-sample:** 2025-10-01 → 2026-04-30 (7 months) — discovery
- **Out-of-sample:** 2026-05-01 → 2026-09-03 (4 months) — held back, untouched

Breakeven win rate at 1:1 after costs, measured empirically from setup 1: **~50.9%**.

## In-sample results

| # | Setup | Trades | Win% | PF | Net |
|---|---|---|---|---|---|
| 1 | RSI(2) extreme reversion | 908 | 50.9% | 1.002 | +$186 |
| 2 | Bollinger 2σ fade | 808 | 48.0% | 0.838 | −$17,280 |
| 3 | VWAP extension fade | 723 | 49.0% | 0.945 | −$5,257 |
| **4** | **Reversal after 3 consecutive closes** | **1,434** | **54.0%** | **1.120** | **+$20,710** |
| 5 | PDH/PDL sweep reversal | 361 | 44.3% | 0.744 | −$15,481 |
| 6 | Opening-range breakout | 261 | 53.3% | 1.031 | +$1,085 |
| 7 | VWAP pullback continuation | 734 | 51.5% | 0.996 | −$404 |
| 8 | EMA20 pullback in trend | 987 | 51.9% | 1.009 | +$1,076 |
| 9 | Inside-bar breakout | 940 | 48.7% | 0.882 | −$15,611 |

Eight of nine are at or below breakeven. Setup 4 looked genuine: 1,434 trades,
Sharpe 1.38, ~10 trades/day — exactly the required shape.

## Out-of-sample: setup 4 failed

| | In-sample | Out-of-sample |
|---|---|---|
| Trades | 1,434 | 846 |
| Win rate | **54.04%** | **50.47%** |
| Profit factor | 1.120 | **0.927** |
| Net | +$20,710 | **−$6,220** |

The 3.57pp drop has z = 1.65 — entirely consistent with the in-sample result
being a lucky draw from testing nine candidates. At 50.47% it sits *below* the
~50.9% breakeven. And gross of all commissions the out-of-sample run still lost
$4,122, so this is not a cost problem. **There is no edge there.**

Note the regime differed: gold rose over the in-sample window (buy & hold
+$6,341) and fell over the out-of-sample one (−$1,098). A long-biased artifact
is a plausible explanation for the in-sample number.

## Conclusion

**I looked, and I did not find one.** Nine standard technical day-trade concepts
on MGC 15m at 1:1, tested honestly with a held-out sample, produced no
persistent edge after costs. The one candidate that passed discovery failed
validation — which is precisely why the sample was held back.

This is a real result, not an incomplete search: it says that retail-standard
chart patterns on a highly liquid gold future, at 15-minute resolution, do not
carry a 1:1 edge that survives out-of-sample. That is what market efficiency at
this level looks like.

## What this implies for the manual-vs-bot gap

The discretionary edge being described — passing evaluations in ~2 days — is
unlikely to live in these OHLC-derived patterns, because they were tested and
they are not there. If the manual edge is real, it more plausibly comes from
something not present in 15-minute bars: news and macro context, order flow /
DOM reading, session-specific judgement, or discretionary trade management.
None of those are reproducible from the data this bot consumes.

## Honest options from here

1. **Instrument the discretionary process.** Log real trades — entry/exit
   timestamps, reasoning, what was on screen. If the edge is real it will show
   up as a pattern to encode. This is the only path that starts from evidence
   that an edge exists.
2. **Change the data, not the pattern.** Order flow, footprint, COT, or
   macro/news timing are different information, not another chart indicator.
3. **Widen the search properly** — more timeframes, R multiples and filter
   combinations — but with the multiple-comparison discipline used here, and the
   expectation that most candidates will fail validation exactly as setup 4 did.

What I would not recommend is tuning setup 4 until it looks good again. That
number is already known to be noise.

## Reproduction
`SETUP_LAB.pine` (live in TradingView), setupId 1–9, window inputs switch
between the in-sample and out-of-sample ranges.

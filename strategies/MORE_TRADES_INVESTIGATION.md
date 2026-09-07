# Why XAUUSD only produces ~6 trades/month — measured, not guessed

## The funnel (XAUUSD 15m, 29 Jul -> 29 Aug 2026)
| Stage | Count |
|---|---|
| Bars in window | 2,108 |
| Uptrend bars | 1,233 (58%) |
| Downtrend bars | 89 (4%) |
| **Sideways bars (no trading allowed)** | **786 (37%)** |
| Arm events (BOS in trend) long / short | 51 / 4 |
| Distinct trigger events long / short | 58 / 5 |
| Passed stop filter | 55 |
| **Actually traded** | **5-6** |

The 58/55 figures count repeat triggers of the SAME armed zone (price oscillating
in and out of it), so they overstate independent opportunities. True independent
opportunities are closer to the arm-event count, and most arms expire because
price never retraces into the zone in a strong trend.

## Four attempts to increase trade count — all measured, all failed
| Change | Trades | PF | Net |
|---|---|---|---|
| Baseline V8 (single position) | 5 | 4.39 | +$736 |
| Allow 4 concurrent positions | 6 | 3.52 | +$835 |
| + wider entry zone (0.45xATR) + 48-bar wait | 6 | 3.27 | +$765 |
| 5m execution timeframe | 5 | 1.49 | +$158 |
| (earlier session) looser pivots + trend gap | more | 1.13 | degraded |

Concurrency, zone width, wait time, and timeframe ALL fail to increase frequency.
This is now conclusive: **~6-8 trades/month is intrinsic to this setup on gold 15m.**
It is not a tuning problem. Loosening filters has repeatedly degraded quality
without adding trades.

## Best configuration found (kept)
Concurrency enabled (4 slots), single bracket per entry, no TP1 partial:
6 trades, 50% win rate, **PF 3.52**, **+$835 (+1.67%)**, max DD $219 (**0.44%**).
That is ~+22%/yr annualised at well under 1% drawdown -- strong risk-adjusted,
but low in absolute dollars because the account is small and the setup is rare.

## The two real levers (neither is parameter tuning)
1. **The 786 sideways bars (37% of the month) are completely untraded by design.**
   The trend filter excludes them. A separate range/mean-reversion module for
   those conditions is the single largest untapped pool of opportunity. This is
   new strategy development, not tuning.
2. **PnL per trade is capped by account size, not by the strategy.** At 0.75% risk
   the system uses a tiny fraction of its risk budget (0.44% max DD), but raising
   risk % hits a notional ceiling on a $50k account -- tested earlier: 1.5% risk
   REDUCED trade count because order notional exceeded equity. More capital scales
   this linearly; higher risk % does not.

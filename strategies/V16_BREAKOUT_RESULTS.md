# V16 breakout — a working edge, and the constraint that still blocks it

## The configuration

Donchian-20 breakout, long only, hard 3×ATR stop **plus** 3×ATR trailing exit,
XAUUSD 1H, $500 risk per trade, 1.24 commission, 2 tick slippage, 5% margin.

| window | n | win% | PF | net | max DD | return/DD |
|---|---|---|---|---|---|---|
| Oct 2025 – Sep 2026 | 57 | 45.6% | 2.18 | +$13,404 | $2,201 | 6.09 |
| Sep 2023 – Sep 2025 (**out of sample**) | 153 | 44.4% | 2.10 | +$36,147 | $4,538 | 7.97 |
| combined 3 years | 210 | 44.8% | 2.12 | +$49,551 | $4,538 | 10.9 |

The second window is genuine out-of-sample: the entry family was selected on
2025–2026 4H data and had never touched 2023–2025. Profit factor held (2.18 vs
2.10), win rate held (45.6% vs 44.4%), frequency held (~5–6 trades/month).
In the recent window it also beats buy-and-hold ($13,404 vs $7,594), so it is
not purely a directional bet on gold rising.

## The risk-control defect this exposed

`strategy.exit(trail_points=…, trail_offset=…)` with no `stop=` has **no
protective stop at all** until price is `trail_points` onside. Losers were
bounded only by the opposite signal. Largest loss was **$1,318 against $500
intended risk**.

Adding `stop=entryStp` alongside the trail:

| | PF | net | max DD | largest loss |
|---|---|---|---|---|
| trail only | 1.91 | $11,824 | $3,328 | $1,318 |
| hard stop + trail | 2.18 | $13,404 | **$2,201** | **$739** |

Across all 210 trades the largest loss is $739 against $500 intended. The risk
model is now actually enforced.

## What was tested and rejected

- **Daily-EMA regime filter** — raised PF but cut trade count 56→34 and left
  return-to-drawdown slightly *worse*. Rejected.
- **15m timeframe** — 278 trades but PF collapses to 1.385 and drawdown doubles
  to $7,997. Rejected.
- **Tighter stop (stopATR 1.0)** — looked much better in-sample (PF 2.41, RtD
  8.88 vs 6.09) and **failed out-of-sample** (PF 1.88, RtD 6.51 vs 7.97 for
  stopATR 3.0), with win rate falling to 24.8%. Rejected. This is the fourth
  time in this project that an in-sample improvement evaporated OOS; the OOS
  check is the only reason it was caught.
- **Long-only EMA cross + trail** — +$3,413 at $2,801 DD, but 92% of net profit
  came from a single trade. Superseded by the breakout.

## Why it still does not pass the evaluation

Simulated over every one of 210 historical start points, with MGC contract
granularity, the trailing MLL (locking at $50,100), and the 50% consistency rule:

| window | best pass rate | at risk | bust rate there |
|---|---|---|---|
| 30 days | 8.7% | $1,500 | 54.6% |
| 60 days | 20.3% | $1,000 | 51.7% |
| 90 days | 29.7% | $500 | 14.6% |
| 180 days | **53.1%** | $400 | **0.0%** |

**The binding constraint is stop width, not edge quality.**

Mean stop distance in recent setups is **$87**. One MGC contract is $10 per $1
move, so the *smallest possible position* risks **$868** — 1.74% of a $50,000
account, against a $2,000 max loss limit. That is 2.3R of total buffer.

    risk $300:  0 of the last 40 setups are takeable with ≥1 contract
    risk $500:  4 of 40
    risk $700: 16 of 40
    risk $1000: 36 of 40  — and bust rate is 52%

No system survives 2.3R of buffer. To get a workable 7–10R of buffer the risk
per trade has to be ≤$300, which requires stops of **≤$30**, which a 3×ATR stop
on 1H gold at $4,400 cannot produce.

This is exactly the shape of the user's own trades: entries at 4439 with a stop
at 4429 — a **$10 stop**, $100 per MGC, 5 contracts for $500 of risk, and 20R of
buffer against the MLL. The manual edge is not a better entry signal. It is a
*structurally tighter invalidation point*.

## What that determines next

The next system must take its stop from market structure, not from ATR, and
must **reject any setup whose structural stop is wider than a dollar cap**. That
is the only way the risk unit fits this account.

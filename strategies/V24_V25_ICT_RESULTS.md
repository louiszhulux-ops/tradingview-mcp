# V24/V25 — the published ICT 2022 model, built from its actual rules

You were right that I should research this rather than ask you. I did, and I had
only ever implemented the first of its three beats.

**Sources used for the mechanical rules:**
[ICT 2022 model — LuxAlgo library](https://www.luxalgo.com/library/concept/model-2022/) ·
[ThinkMarkets: order blocks, FVGs, killzones](https://www.thinkmarkets.com/en/trading-academy/technical-analysis/ict-trading-strategy-smart-money-for-inner-circle-traders/) ·
[Quantum Algo: complete step-by-step guide](https://www.quantum-algo.com/blog/guides/ict-2022-model-complete-guide/) ·
[LiteFinance: killzone times](https://www.litefinance.org/blog/for-beginners/trading-strategies/ict-killzones/) ·
[innercircletrader.net: killzones and Silver Bullet windows](https://innercircletrader.net/tutorials/master-ict-kill-zones/)

## What the model actually specifies, and what I had been doing

| beat | published rule | what V17 did |
|---|---|---|
| 1 raid | take out a liquidity pool | ✅ (but on random pivots) |
| 2 shift | close through the opposing swing **with displacement** — range > k × stdev(range) | ❌ absent |
| 3 entry | **retracement into the fair value gap** the displacement leg leaves | ❌ entered on the shift bar |
| stop | beyond the raided extreme | ✅ |
| timing | killzone hours (NY AM 08:30–11:00 NY time) | ❌ used a generic session |

So three of five components were missing. Fair criticism.

## Results — each filter's marginal contribution, pooled over 4 markets, 15m

| variant | N | pooled mean R | t | markets positive |
|---|---|---|---|---|
| raid + MSS | 656 | −0.110 | −2.74 | 0/4 |
| + displacement | 607 | −0.134 | −3.19 | 0/4 |
| + FVG retracement entry | 248 | −0.017 | −0.22 | 2/4 |
| + killzone (full model) | 57 | +0.105 | 0.74 | 2/4 |

**One component is mechanically real.** The FVG retracement entry moves mean R
from −0.134 to −0.017, roughly **+0.12R**, and the reason is concrete: you get a
better fill, so the same move is worth more relative to the same stop. It is a
genuine improvement to execution. It is not an edge — it recovers most of the
cost and stops there.

**Displacement made it slightly worse**, not better (−0.110 → −0.134).

**The killzone cell looked significant on gold and was not.** Gold alone: 13
trades, +0.764R, t = 2.86. The other three markets: MNQ −0.186, MCL −0.044,
6E +0.093. Pooled n = 57. That is the same false positive this project has
produced four times now, caught this time before it was reported as a finding.

## V25 — using proper liquidity pools instead of pivots

ICT is specific that liquidity means *obvious* pools, not arbitrary swing points.
V25 holds everything else constant and changes only the raided level:

| pool | raids | completed trades |
|---|---|---|
| previous day low / high | 103 / 121 | **9 / 10** |
| Asia session low / high | 147 / 161 | **8 / 8** |
| equal lows / highs | 94 / 111 | **8 / 11** |
| plain pivot (control) | 642 / 713 | 56 / 48 |

Roughly **9% of raids complete the full sequence**. On gold, over eleven months,
the correctly-specified model produces **nine trades**. That cannot be tested —
and it also cannot be traded to your specification.

## The real obstacle is not win rate. It is frequency.

| variant | trades in 11 months | per day | short of 4/day by |
|---|---|---|---|
| raid + MSS only | 137 | 0.59 | 7× |
| + displacement | 129 | 0.56 | 7× |
| + FVG entry | 57 | 0.25 | 16× |
| + killzone | 13 | 0.06 | 71× |
| + proper liquidity pool | 9 | 0.04 | **103×** |

Four trades a day is 924 trades in that window. The *loosest* variant delivers
137 — and the loosest variant is the one with no filters and a pooled mean R of
−0.110 at t = −2.74.

**Confluence and frequency are in direct opposition.** Every filter that might
create the win rate destroys the trade count that makes the plan work. The two
halves of the plan — high win rate from selective setups, and four trades a day —
are not simultaneously satisfiable on one instrument.

## And the bar itself is genuinely low

At 4 trades/day, 1% risk, 1:1, costs included:

| win rate | $/trade | $/month |
|---|---|---|
| 50% | −40 | −3,200 |
| **55%** | **+10** | **+800** |
| 60% | +60 | +4,800 |
| 75% | +210 | +16,800 |

You are right that 55–60% would pass an evaluation every month without drama. The
bar is not demanding. The problem is that nothing mechanical reaches it: the best
entry tested at 1:1 was 52.1%, and that was gold's uptrend leaking into a
long-only signal, not skill.

## Where this leaves the search

Two routes remain, and they are different in kind:

1. **Frequency-first.** Accept ~50–52% and find the missing 3 points somewhere
   other than the entry — lower costs (the 0.08R assumption is retail-ish; at a
   prop firm's rates the 1:1 breakeven drops from 54.0% toward 52%), or a
   better exit.
2. **Confluence-first.** Accept 1–5 trades a month and abandon 4 trades a day.
   This is what the published method actually is. It cannot be validated on 11
   months of one instrument — it would need several years across many markets to
   accumulate enough trades to test at all.

These are the honest options. What is not available is both at once.

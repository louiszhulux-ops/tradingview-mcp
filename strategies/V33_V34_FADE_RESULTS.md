# V33 / V34 — The fade: the first cross-market result in this project

Protocols: `V33_FADE_PROTOCOL.md`. Analysis: `v33_crossmarket.py`, `v34_analysis.py`.
Rigs: injected via the Pine editor; V34's source is reproduced in the commit.

## Where this came from

V32 closed the payoff-ratio route and, in doing so, turned up one pattern that
held on both markets, in both target grids, on both sides of the control:
**long-side momentum triggers have negative expectancy, and the trade against
them is positive.** V33 tested that pattern properly.

## V33 — cross-market sign test

Fade a long-side momentum trigger (break-and-go, sweep-and-reclaim, trend
pullback, VWAP reclaim — pooled), stop 1.5×ATR(14), target 2R, 5m, both the
faded and the followed trade taken on the same bar as each other's control.

| market | n | gross R/trade |
|---|---|---|
| XAUUSD | 1,946 | +0.0930 |
| MNQ1! | 1,983 | +0.0182 |
| ES1! | 1,957 | +0.0301 |
| CL1! | 1,968 | +0.0686 |
| 6E1! | 1,939 | +0.1635 |
| SI1! | 1,967 | +0.1240 |
| ZN1! | 1,422 | +0.1688 |
| BTCUSD | 2,061 | +0.0087 |

**Positive on 8/8.** Sign test p = 0.0039. n-weighted pooled **+0.0807R** over
15,243 trades; pooled-trade t = +3.48, across-market t = +3.75 (df 7, and the
true df is nearer 5–6 because ES/MNQ and XAU/SI are correlated pairs).

This is the first result in the project with t > 3 and unanimous cross-market
sign. Two independent rigs agree where they overlap: V32's `R_against` at the
2R cell was +0.0969 on gold and +0.0209 on MNQ, against V33's +0.0930 and
+0.0182.

**The conditioning hypothesis was rejected.** V33's pre-registered prediction
was that fade edge decreases monotonically in ADX. Measured by ADX bucket —
gold: −0.119, +0.152, +0.063, +0.141; MNQ: −0.029, −0.007, +0.132, −0.071. The
ordering does not replicate and `edge(ADX<15) > edge(ADX>30)` fails on gold.
Rejected, and not replaced with the best-looking cell.

## V34 — fade on a resting limit: not established

V27 found limit entries starve on continuation signals. A fade is the opposite
case: the push you are fading is what fills you. Four offsets, identical
trigger set down every row (the `placed` count is the same in all four).

| market | off 0 | 0.25×ATR | 0.50×ATR | 0.75×ATR |
|---|---|---|---|---|
| XAUUSD | +0.078 | +0.097 | +0.139 | +0.159 |
| MNQ1! | +0.095 | +0.180 | +0.198 | +0.243 |
| ES1! | +0.029 | 0.000 | −0.055 | −0.027 |
| CL1! | +0.050 | +0.034 | +0.019 | +0.092 |
| 6E1! | +0.040 | +0.001 | +0.031 | −0.017 |
| SI1! | +0.062 | +0.064 | +0.076 | +0.101 |
| ZN1! | +0.076 | +0.101 | +0.183 | +0.173 |
| BTCUSD | −0.109 | −0.148 | −0.105 | −0.148 |

Gold, MNQ and ZN improve strongly. ES, CL and 6E go the other way. Improves on
**5/8** markets, across-market t = +0.89 (0.5×ATR) and +1.18 (0.75×ATR).
**Not replicated — not adopted.** Taking 0.5×ATR here would be keeping the
three markets that agreed with me.

Two things V34 did establish. The follow control is negative on 7/8 markets
(mean −0.069), so the fade thesis itself survives its own control. And V34's
absolute levels run below V33's on 7/8 markets (mean −0.044) because V34 must
keep eight cells free and skips 60–70% of triggers against V33's 9–26% — so
only V34's *within-table* comparison is trustworthy, and **V33 stays the
estimate of record.**

## The correction that matters most

I had paired the all-market pooled gross edge (+0.0807) with each market's own
cost. That is wrong — the edge must be the edge of the market actually traded.
Redone per market against V26's measured costs:

| market | gross | cost_R | **net** | t on its own |
|---|---|---|---|---|
| XAUUSD | +0.0930 | 0.0445 | **+0.0485** | +1.43 |
| MNQ1! | +0.0182 | 0.0438 | −0.0256 | +0.28 |
| CL1! | +0.0686 | 0.1239 | −0.0553 | +1.06 |
| 6E1! | +0.1635 | 0.1505 | +0.0130 | +2.52 |

**The markets with the big gross edges are the ones whose cost destroys them.**
6E has the second-largest gross edge in the sample and keeps 8% of it. Only
gold survives with anything, and gold on its own is t = 1.43.

So the cross-market t = 3.5 is real but not bankable: it pools an edge measured
in R across instruments whose R costs differ by 3.4×, and the portfolio you can
actually trade is one market, not eight.

## Where that leaves the account

MGC gold, 1 micro contract, stop 1.5×ATR(5m) = $37.50 risk. Buffer L = 53.3R,
target U = 80.0R — the small-risk lever from V32. ~27 triggers/day.

| net edge | what it is | pass | bust | median days |
|---|---|---|---|---|
| +0.1756 | 95% CI upper | 99.9% | 0.1% | 20 |
| **+0.0485** | **point estimate** | **81.2%** | 18.1% | 36 |
| +0.0250 | half the point estimate | 56.4% | 42.1% | 43 |
| +0.0100 | near the CI floor | 37.2% | 60.6% | 46 |

Gold's gross 95% CI is [−0.034, +0.220], so the net CI is [−0.079, +0.176].
**The data cannot rule out a losing system.** The point estimate gives an 81%
pass in about 36 trading days; the lower half of the interval gives a coin flip
or worse.

## Honest bottom line

This is the best-supported configuration the project has produced, and it is
still one market, one t-statistic of 1.43, and a confidence interval that
contains zero. More backtesting will not settle it — the sample is already the
full history the platform holds at 5m. What settles it is forward evidence:
running the fade on gold in paper, on the account's real rules and real fills,
and watching whether the edge shows up out of sample.

Two caveats that would lower the numbers above, both unmodeled: the Monte Carlo
treats trades as sequential and independent, whereas up to four concurrent
positions in one instrument are correlated; and the trailing MLL is modelled on
closing balances, which is correct for LucidFlex before the lock but leaves no
margin for a bad intraday sequence after it.

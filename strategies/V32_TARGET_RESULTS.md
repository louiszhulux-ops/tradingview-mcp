# V32 — Target Surface: results

Protocol and decision rule fixed in advance: `V32_TARGET_PROTOCOL.md`.
Rig: `V32_target_surface.pine`. Analysis: `v32_analysis.py`.

## What was measured

48 cells: 2 markets (XAUUSD, MNQ1!) × 2 trigger sides × 12 target multiples
(0.25R–2R and 0.5R–6R), stop fixed at 1.5×ATR(14) throughout so that cost_R is
constant and the target is the only variable. Four momentum trigger families
pooled (break-and-go, sweep-and-reclaim, trend pullback, VWAP reclaim), 5m,
~20,600 bars per market. Every trigger is taken **with** it and **against** it
on the same bar with the same stop, so `edge = (R_with − R_against)/2`.

A trigger is only taken when all twelve (side, target) cells have a free slot,
so every row of a table is measured on an **identical trigger set** — `n` is the
same to within one or two trades down every column. When both barriers are
touched inside one bar the stop is assumed to have hit first.

## Result 1 — the payoff-ratio route is closed

`edge/a` is flat. Gold long triggers: −0.045, −0.061, −0.050, −0.054, −0.041,
−0.036 across targets 0.25R→2R. MNQ long triggers: +0.013, −0.020, −0.015,
−0.021, −0.024, −0.023. The edge scales with the target, which is exactly
Wald's identity for a constant-drift process: `E[R] ≈ mu*a/sigma^2`.

Cost does **not** scale with the target — it scales with the stop, which is
fixed. So halving the target halves the edge and leaves the cost, and the
tight-target configuration is strictly worse. Pre-registered condition 2
(`edge(0.75) >= 0.80*edge(1.5)`) is met in 5 of 8 series, but condition 3 fails
everywhere by a factor of four or more, so the rule returns **do not adopt**.

This settles the "high win rate is the most important thing" question with a
measurement rather than an opinion. A 77–80% win rate **is** available — it is
what a 0.25R target produces on these triggers. It is also **below** the 80%
that a 0.25R target needs to break even. Win rate and payoff are two views of
one number; the thing that is actually scarce is `edge / target`, and no choice
of target changes it.

## Result 2 — nothing in the surface is significant

Standard errors use `n/4` because up to four trades run concurrently per cell.

| | best cell | t |
|---|---|---|
| gold long triggers | −0.0723 @ 2R (fade) | −1.59 |
| gold short triggers | +0.0319 @ 1.5R | +0.83 |
| MNQ long triggers | −0.1261 @ 4R (fade) | −1.37 |
| MNQ short triggers | +0.0728 @ 3R | +0.98 |

**All 48 |t| < 1.7.** The best tradeable expectancy anywhere in the surface is
`+0.0623R` gross (MNQ shorts at 2R, t = 1.11) — the maximum of 48 draws, so
winner's curse applies before cost of ~0.024R is subtracted.

## Result 3 — the requirement, stated scale-free

`P(pass)` depends on `lambda = 2E/sd^2` and on the buffer `L` and target `U`
expressed in R. On the LucidFlex 50K at $400 risk, `L = 5R` and `U = 7.5R`:

| P(pass) | lambda needed | E needed at 2:1 |
|---|---|---|
| 60% | 0.133 | +0.140 R |
| 75% | 0.253 | +0.266 R |
| 90% | 0.454 | +0.478 R |

Measured across the surface: `lambda` between −0.26 and +0.15, and `P(pass)`
between 10% and 62% — against a **40% baseline that a zero-edge coin achieves**
at L=5R/U=7.5R. No configuration of target, stop, trigger family, or market
materially beats blind chance.

## Result 4 — the one structural lever that does move

`lambda` is a property of the edge, but `L` and `U` are set by the **dollar risk
per trade**. Cutting the risk leaves `lambda` alone and makes the buffer and
target deeper in R, so a small positive edge compounds over more trades against
a proportionally deeper buffer. Under the verified LucidFlex rules (trailing
end-of-day MLL, 50% consistency), holding E at the surface's best cell:

| risk | L | U | trades/day | pass | bust | median days |
|---|---|---|---|---|---|---|
| $400 | 5.0R | 7.5R | 6 | 44.5% | 55.5% | 8 |
| $150 | 13.3R | 20.0R | 20 | 50.6% | 49.4% | 13 |
| $100 | 20.0R | 30.0R | 20 | 58.5% | 41.5% | 22 |
| $60 | 33.3R | 50.0R | 20 | **72.3%** | 26.6% | 37 |

That is the largest single structural improvement found in this project: +28
points of pass probability at an unchanged per-trade edge. It is bought with
time — median 37 trading days instead of 8 — and it only bites if the edge is
genuinely positive. At a defensible E of +0.030R net it gives 48%, not 72%.

## What replicated

One pattern survives on both markets, in both grids, on both sides of the
control: **long-side momentum triggers have negative expectancy, and the trade
against them is positive.** 4 of 4 market×grid cells agree in sign. Pooled at
the 2R tight-grid cell, fading long triggers is `+0.0580R` gross across n=4,002
(t = 1.31), `+0.034R` after cost. Suggestive, not significant, and it is the
opposite of every strategy built in V15–V31, all of which bought continuation.

## Honest bottom line

The payoff-ratio hypothesis was worth testing and it is now closed by
measurement, not assumption. The measurement also produced the first structural
lever in the project that is worth 28 points of pass probability. But the edge
that lever needs is still not in evidence: the best of 48 cells is 4× short of
a 75% pass and is not statistically distinguishable from zero.

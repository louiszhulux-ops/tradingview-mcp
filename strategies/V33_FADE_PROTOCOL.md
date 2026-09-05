# V33 — Conditioned fade: pre-registration

Written **before** running V33.

## The two live findings

1. **V32:** long-side momentum triggers have negative expectancy on both
   markets, in both target grids, on both sides of the with/against control.
   Fading them pools to `+0.0580R` gross (n=4,002, t=1.31), `+0.034R` net.
2. **V30:** conditioning carries real information — regime worth `+0.044R`
   with a monotone ordering across ~10k trades, location worth `+0.043R` in
   trending regimes and ~0 in chop.

They have never been combined. Every strategy in V15–V31 bought continuation,
so V30's conditioning was measured on the wrong sign of trade.

## Hypothesis (directional, not exploratory)

Fading a momentum trigger is a bet that the move does not extend. The prior
from the mean-reversion literature is specific and falsifiable:

- **H-adx:** fade edge is **monotonically decreasing in ADX**. It is largest in
  chop and smallest — plausibly negative — in a strong trend.
- **H-loc:** fade edge is larger when the trigger fires **at the day's
  extreme** (within 0.5×ATR of the running session high for a long trigger)
  than when it fires mid-range.

Both are predictions about **ordering**, made in advance. This is deliberately
not a search for the best of eight cells.

## Measurement

5m, stop 1.5×ATR(14), target 2R (the region of the V32 surface with the least
cost drag). Trigger families as V32. Cells: ADX bucket {<15, 15–22, 22–30,
>30} × location {at extreme, mid-range} = 8. Each trigger is entered **faded**
and **followed** simultaneously, so the control is per-cell. Run on both trigger
sides and both markets.

## Decision rule, fixed in advance

Adopt only if **all** hold:

1. `edge(ADX<15) > edge(ADX>30)` **independently on both markets** — the
   ordering must replicate, not just pool;
2. the pooled conditioned edge, **net of cost_R ≈ 0.024**, is positive;
3. that edge implies **≥60% pass** under the verified LucidFlex rules at a risk
   level whose median days-to-pass is ≤ 60.

If the ADX ordering does not replicate cross-market, H-adx is rejected and I
report it as rejected. I will not substitute the best-looking cell for the
prediction I made.

# V28 — the horizon sweep, and the arithmetic that closes the search

The equation was fully measured going in:

    net = gross edge − cost_R
    cost_R = cost_per_contract / (stop × pointValue)

Both terms move with holding horizon, and both move the *right* way. This holds
the signal fixed (20-bar breakout) and sweeps only the horizon — stop and target
at h×ATR, time limit scaled by h — across six markets, both directions.

## Both predictions confirmed

**Cost falls exactly linearly with stop width**, as the formula requires:

| market | h=1 | h=2 | h=4 | h=8 |
|---|---|---|---|---|
| MGC gold | 0.0223 | 0.0110 | 0.0055 | 0.0027 |
| 6E euro | 0.1124 | 0.0558 | 0.0277 | 0.0143 |

**And gross expectancy rises with horizon**, pooled over all four original markets:

| horizon | pooled gross |
|---|---|
| 1×ATR | −0.0288 |
| 2×ATR | −0.0115 |
| 4×ATR | −0.0015 |
| 8×ATR | **+0.0084** |

Monotonic, and it crosses zero between 4× and 8×. That is a real and
mechanistically sensible gradient: short-horizon entries are dominated by
adverse selection and by a fixed fee spread over a small stop; longer horizons
dilute both.

## But it fails the cross-market control

Both directions positive, six markets:

| market | h=2 | h=4 | h=8 |
|---|---|---|---|
| MGC gold | +0.024/+0.022 ✅ | +0.080/+0.064 ✅ | +0.055/+0.003 ✅ |
| MNQ nasdaq | +0.051/+0.039 ✅ | +0.016/+0.028 ✅ | −0.000/+0.042 |
| MCL crude | −0.021/−0.078 | −0.031/−0.069 | +0.058/−0.087 |
| 6E euro | −0.078/−0.050 | −0.078/−0.021 | −0.038/+0.035 |
| MES s&p | −0.001/−0.092 | +0.027/−0.029 | −0.011/−0.021 |
| 6J yen | −0.101/+0.068 | −0.130/+0.011 | −0.125/+0.139 |

**2 of 6 at best.** The bar was 3 of 4.

The failures are diagnostic. The yen at h=8 is long −0.125 / short +0.139 — the
yen fell for the entire sample. The two markets that pass are gold and Nasdaq,
the two strongest trenders in the window. An effect that appears only in markets
that trended, in whichever direction they trended, is **realised drift**. You
cannot trade it prospectively, because using it requires knowing which way the
market will go, which is the whole problem.

## And the best cell still does not pass the evaluation

Gold at h=4 is the strongest result in this entire project: net +0.066R, both
directions positive, 565 trades.

    1 MGC at a 4×ATR stop  = $220 of risk
    +0.066R × $220         = $14.50 per trade
    × 188 trades per year  = $2,730 per year
    → 13 months to make $3,000

Against an account that allows a $2,000 drawdown. One hundred and eighty-eight
trades at that expectancy swings far more than $2,000 along the way.

## The structural conclusion

This is the honest end of the search, and it is not a vague one:

- **An edge exists only at long horizons.** Measured, monotonic, and consistent
  with the published time-series-momentum literature, which finds the effect at
  1–12 *month* horizons — far beyond anything tested here.
- **The account requires short horizons.** A $2,000 max loss limit on a $50,000
  account is a 4% drawdown budget. Passing needs +6% against −4%, a
  return-to-drawdown above 1.5 realised inside weeks.
- **These two requirements do not overlap.** The horizon where the edge lives is
  excluded by the account structure, and the horizon the account permits has an
  edge of zero.

That is why eleven distinct strategy families have failed the same way. It was
never a search problem.

## What is genuinely worth keeping

Four things survived every test, and all of them are execution, not prediction:

1. **Limit orders beat market orders by ~0.02R** — direction-neutral,
   signal-independent, roughly the entire cost of trading gold.
2. **cost_R = cost / (stop × pointValue)** — varies 5× across instruments and
   falls linearly with stop width. Gold and Nasdaq are cheap; euro and yen are
   4–6× more expensive for the same nominal fee.
3. **Buffer-based sizing removes ruin** — 0% bust under every edge assumption,
   because the buffer decays geometrically and cannot be crossed.
4. **Three order-placement bugs** that silently corrupt any strategy: exits not
   armed on the entry bar, trailing exits with no protective stop, and
   `close_all()` filling at the next bar's open so a Friday flat executes Sunday.

Those make any strategy better, including a discretionary one. They do not
manufacture an edge, and nothing in this project has.

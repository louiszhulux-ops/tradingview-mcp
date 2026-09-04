# V21 cross-market signal screen — protocol, fixed before any results were seen

Written and committed BEFORE running the screen. Every previous "discovery" in
this project came from looking at results and then deciding what counted as
success. That is how PF 1.327 on 15m gold survived four rounds of checking and
then died the moment it met a genuinely independent sample.

## Why the method changes

The failure mode was statistical power, not effort. One instrument, one window,
~160 trades, expectancy $97 with standard deviation $807 — a t-statistic of 1.54.
At that effect size nothing can be concluded, and running more variants on the
same 160 trades manufactures false positives rather than evidence.

A real effect appears in many markets and many periods at modest strength. Noise
appears in one market, in one window, at impressive strength. So the screen tests
breadth instead of depth, and treats consistency as the evidence rather than
magnitude.

## Design

- **8 signals**: 4 triggers × 2 directions. Each trigger is tested *both* ways, so
  every family carries its own control — if "fade the breakout" works, "trade the
  breakout" must lose by roughly the same amount, and if both look positive the
  measurement is broken.
    0/1  trend continuation long / short   (close vs SMA50, SMA20 cross)
    2/3  20-bar range break — faded        (long on new low, short on new high)
    4/5  20-bar range break — followed     (long on new high, short on new low)
    6/7  liquidity sweep + reclaim         (the V17 setup, both directions)

- **Uniform exit for every signal**: stop at 1×ATR(14), target at 2×ATR, time
  stop at 24 bars. Results are recorded in R multiples so they are directly
  comparable across markets and price levels.

- **Costs are charged**: 0.08R per trade (commission + 2 ticks slippage, computed
  for MGC and roughly representative of liquid micros). No zero-cost results.

- **Markets** (liquid micro futures, four asset classes so they are not four views
  of the same thing): MGC gold, MNQ Nasdaq, MCL crude, M6E euro.

- **Timeframe** 1H — the longest history that fits inside the ~20k bar limit,
  giving roughly three years per market.

- **Two eras**, split at 2025-01-01: IS = 2023-09 to 2024-12, OOS = 2025-01 to
  2026-09. The OOS era is not looked at until the IS pass is complete.

## Acceptance criteria — fixed now

A signal is worth pursuing only if ALL of the following hold:

1. Positive mean R in **at least 3 of 4 markets** in the in-sample era.
2. Positive mean R in **at least 3 of 4 markets** in the out-of-sample era.
3. Pooled t-statistic across all markets and both eras **> 3.0**.
   (Not 1.96: eight signals are being tested, so the threshold is raised for
   multiplicity. 1.96 with 8 tests gives roughly a 1-in-3 chance of a false
   positive somewhere.)
4. Its mirror signal — the same trigger traded the opposite way — must be
   **negative**. A trigger that looks profitable in both directions is a bug.

If nothing clears all four, the answer is that this family contains no tradeable
edge, and I will say so rather than relaxing the criteria.

## What a pass would and would not mean

Clearing this bar means the effect is probably real and worth building on. It
does not by itself mean the evaluation can be passed — that still requires the
effect to be large enough to clear a $3,000 target against a $2,000 trailing loss
limit, which is a separate question answered by the execution layer already built.

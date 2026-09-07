# V37 — Conditioning lab with realistic fills, walk-forward validated

## Why the rig had to be rebuilt

V30 and V33 measured conditioning with entries at the **trigger bar's close**.
V35 showed that assumption is worth ~0.041R of fiction: a real order submitted
on bar N fills at the open of bar N+1. Every conditioning result in this project
was therefore measured on a quantity that cannot be traded.

V37 fills at the **next bar's open**, subtracts a **$4.40 execution drag**
converted to R at the live stop size, and reports every cell **split into three
equal time folds** so stability is visible rather than assumed.

## Hypotheses — four conditioners, chosen before looking

The ADX and day-extreme conditioners were already tested and rejected (V33).
These four are new, and each has a specific reason to matter for a *fade*:

- **C1 session.** Mean reversion is a liquidity-provision effect, so it should
  be strongest when liquidity is thin and weakest at the cash open. Six 4-hour
  UTC blocks.
- **C2 extension.** Fading a 1-bar pop and fading a 5-bar run are different
  bets. `(close − EMA20)/ATR` bucketed. This is the most natural conditioner
  for a fade and has never been tested.
- **C3 volatility regime.** `ATR / SMA(ATR,100)`. Reversion should be stronger
  when current volatility is high relative to its own recent norm.
- **C4 run length.** Consecutive bars above EMA20 before the trigger.

## Walk-forward, fixed in advance

Three equal folds by time. A cell counts as **stable** only if it is positive
in **all three** folds. Selection on folds 1–2 and confirmation on fold 3 is
reported separately, so the out-of-sample number is never the one used to pick.

## Decision rule

Adopt a conditioner only if:

1. some cell is positive in **all three folds** on MGC, **and**
2. the same cell is positive on MNQ (the second viable contract), **and**
3. the resulting net edge, applied at the measured trade frequency, clears
   **60% pass** under the verified LucidFlex trailing-MLL rules.

Anything less and I report the conditioner as not established. In particular I
will not select the best of 24 cells and present it as a finding — the whole
point of the fold split is to make that impossible to do accidentally.

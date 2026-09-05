# Pre-registration — Phases 2, 3 and 4

**Written and committed before any of it is run.** The point of committing first
is that the specification cannot be quietly adjusted after seeing the results.
Anything that changes after this commit will be recorded as a change, with the
reason, in the results document.

---

## 1. The failure mode this protocol exists to prevent

> "Do NOT simply define: *HTF bias = whichever direction happened to produce the
> profitable trade.*"

Two guards:

1. **Every bias definition is computed only from bars closed at or before the
   decision bar.** In Pine: `request.security(..., expr[1], lookahead=barmerge.lookahead_off)`.
   The model must be able to answer "at 09:42, before knowing what happens next,
   my bias is bullish."
2. **The candidate set is fixed here, in advance, and is small.** Six definitions,
   each motivated by a component the user listed, not a grid. No thresholds are
   swept. If none of the six works, that is the answer.

The +0.334R L1 result is treated as **unvalidated** from this point on. It was
measured on the whole window that generated it and does not survive as evidence
until it clears fold C below.

---

## 2. Data

Feed ends **2026-08-31 00:00 UTC** and is delayed (see `HUMAN_TRADE_REGISTER.md`
§5), so there is no fresh unseen data to wait for. The held-out period is carved
out of the available history.

### Folds (5-minute bars, UTC)

| fold | role | from | to | unix |
|---|---|---|---|---|
| **A** | develop | 2026-06-22 | 2026-07-16 | 1782086400 → 1784160000 |
| **B** | validate | 2026-07-16 | 2026-08-09 | 1784160000 → 1786233600 |
| **C** | **TEST — sealed** | 2026-08-09 | 2026-08-31 | 1786233600 → 1788134400 |

Fold C is not looked at, in any form, until the specification is frozen and
committed. It is then run **once**.

### Instruments

Ten instrument × direction cells across four complexes, so that "10 cells" is
not mistaken for ten independent observations:

| complex | instruments |
|---|---|
| metals | `COMEX_MINI:MGC1!`, `COMEX_MINI:SIL1!` |
| equity index | `CME_MINI:MNQ1!` |
| energy | `NYMEX:MCL1!` |
| FX | `CME:6E1!` |

Each run long and short.

### Robustness gate (pre-registered)

On fold C, the frozen model passes only if **all three** hold:

1. pooled E[R] > 0;
2. **≥ 7 of 10** instrument × direction cells positive;
3. **≥ 6 of 8** complex × direction cells positive (a complex cell is the
   n-weighted mean of its instruments).

All ten cells and all eight complex cells are reported whatever the outcome.

---

## 3. Phase 2 — the six candidate ex-ante bias definitions

Each returns bullish / bearish / **neutral**. Neutral means *no trade*, not
"trade anyway" — a bias model is allowed to abstain, and abstention is measured.

| id | name | definition (all inputs closed before the decision bar) |
|---|---|---|
| **B0** | control | always aligned. No directional filter. This is the null. |
| **B1** | HTF trend | 4H `EMA20 > EMA50` → bullish, else bearish. Never neutral. *(the current L1 definition)* |
| **B2** | HTF structure | 4H pivots (len 3). Bullish once a 4H close exceeds the most recent 4H pivot high; bearish once a 4H close is below the most recent 4H pivot low. Persists until flipped. Neutral before the first break. |
| **B3** | daily structure | Bullish if the previous day closed above its open **and** price is above the previous day's midpoint; bearish if the previous day closed below its open **and** price is below the midpoint; otherwise **neutral**. |
| **B4** | HTF displacement | Sign of the most recent 4H bar with range ≥ 1.5 × ATR(4H,14). Valid for 12 subsequent 4H bars, then **neutral**. |
| **B5** | composite | B1 and B2 must **agree**; otherwise **neutral**. |

Why these six: they cover trend (B1), higher-timeframe swing structure (B2),
previous-day structure (B3), displacement (B4) and confluence (B5) from the
listed components, with a control (B0). Premium/discount, session behaviour and
acceptance are deliberately **not** included here — they are location and
confirmation features, and belong to Phases 4 and 6, not to the directional
model.

### Selection rule, fixed now

Run all six on **folds A + B pooled**, on the sweep event stream, all ten cells.
Select the definition with the **most positive instrument × direction cells**;
tie-break on pooled E[R]; second tie-break on the higher fill count. Then freeze.

If **B0 wins**, the honest reading is that no ex-ante bias model in this set adds
anything, and Phase 9's answer is "no" for this feature set. That outcome will be
reported as such, not worked around.

---

## 4. Phase 4 — the ablation, defined before the outcome is seen

Run on folds A + B with the selected bias. `room` is **now an explicit,
switchable condition** — a defect in the V44 ablation, where room ≥ 10R was
silently on in every rung, so "sweep only" was never actually sweep-only.

| # | configuration |
|---|---|
| 1 | sweep only |
| 2 | sweep + HTF bias |
| 3 | sweep + room |
| 4 | sweep + HTF bias + room |
| 5 | sweep + HTF bias + displacement |
| 6 | sweep + HTF bias + reclaim |
| 7 | sweep + HTF bias + room + displacement |
| 8 | full continuation model (7 + the Phase 6 entry model) |

Every cell reports: armed count, fill count, E[R], win %, PF, MFE, MAE, R/ATR,
fills per day. **Observation counts are reported for every cell**, and any cell
with fewer than 30 fills is marked as uninterpretable rather than ranked.

Fixed machinery, unchanged from the family lab so results stay comparable:
structural stop beyond the sweep extreme + 0.20 ATR, 5R target, −1R stop,
adverse excursion checked first, R capped to [0.05, 3.00] × ATR, 144-bar timeout,
$3.00 execution drag converted to R.

---

## 5. What is explicitly forbidden in this phase

- Looking at fold C before the specification is committed as frozen.
- Re-running fold C after seeing fold C, with any change whatsoever.
- Sweeping any threshold: the 1.5× displacement multiple, the 0.25 ATR reclaim,
  the 10R room floor, the pivot lengths and the EMA periods are all **fixed at
  their existing values** and are not tuned here.
- Using the 6 human trades to fit anything. They get one agreement check, at the
  end, reported as a 6-point check.
- Any optimisation for evaluation pass speed or evaluation P&L.

## 6. What a negative result looks like

If the selected bias fails the fold-C gate, the finding is reported as: *the
ex-ante bias effect seen in-sample did not survive out-of-sample*, and the L1
result is retracted in the same document that reported it. No re-specification,
no second test window, no "close enough".

---

## 7. Amendment 1 — recorded before fold C was run

Two changes, both made after seeing **fold A+B only**. Fold C was not opened.

### 7.1 Fold A extended backwards

First run showed folds A+B give only **56 fills** on the largest cell
(MGC long, control). The window actually loaded on a 5m chart is longer than the
71.5 "288-bar days" arithmetic suggested — it reaches back to roughly mid-May —
and the original fold A start of 2026-06-22 was discarding usable development
data for no reason.

**Fold A is redefined as: all available data before 2026-07-16.** Folds B and C
are unchanged, and fold C is still sealed. This only enlarges the development
sample; it cannot leak the test period.

### 7.2 The gate is restated, with its power stated honestly

Fold C is ~22 calendar days ≈ 16 trading days, giving roughly **26 fills per
instrument × direction cell** and ~260 pooled across ten cells. That is a
low-powered test and pretending otherwise would be dishonest, so the numbers are
put on the record here, before the test is run:

| | P(one cell > 0) | P(≥7 of 10 cells > 0) |
|---|---|---|
| true E[R] = +0.30, n = 26 | 0.722 | 0.707 |
| true E[R] = +0.20, n = 26 | 0.653 | 0.521 |
| **null, E[R] = 0** | 0.500 | **0.172** |

A ≥7/10 sign count alone would fire on noise 17% of the time. So the gate adds a
pooled t requirement:

**Fold C passes only if all four hold:**

1. pooled E[R] > 0;
2. **pooled one-sided t ≥ +1.5**;
3. ≥ 7 of 10 instrument × direction cells positive;
4. ≥ 6 of 8 complex × direction cells positive.

Approximate joint characteristics at the development effect size: **power ≈ 55%,
false-positive rate ≈ 6%.** Meaning: **a failure at fold C will be genuinely
ambiguous** — roughly a coin flip between "no edge" and "real edge, too small a
sample". That is stated now so it cannot be spun later, in either direction.
Pooled E[R] will be reported with a 90% confidence interval, not as a bare
pass/fail.

No further amendments will be made once fold C is opened.

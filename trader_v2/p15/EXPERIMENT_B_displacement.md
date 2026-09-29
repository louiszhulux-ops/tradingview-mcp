# Phase 15 — Experiment B: Displacement Threshold

**Hypothesis component varied:** F-displacement — the minimum candle range, expressed as a
multiple of the 5m ATR, that a BOS candle must satisfy to count as a displacement.

**Frozen baseline value:** `dispMin = 1.50`
**Arms run:** 1.25, 1.75, 2.00 (plus the frozen 1.50 baseline as control)

**Exactly one conceptual rule changes.** `V53_ltf_sequence.pine` is untouched; the arm file
`V53_P15_B_disp.pine` is byte-identical to it (sha256 `7490766b6e3de062989a8e7f10939869cc6b679d253ce584f223064aa5797ef5`).
Only input `in_6` differs between arms. Before the first cell of each arm every other frozen
input was read back and verified against the baseline: tgtR 5, bufATR 0.20, minWick 0.10,
dispWait 12, retBars 24, minRatr 0.05, maxRatr 3.00, maxBars 144, costUSD 3.00, swLen(5m) 10,
lSw(LTF) 3.

The close-location clause of the displacement test (`close > low + 0.6·range` for longs,
`close < low + 0.4·range` for shorts) is **not** part of this experiment and was not altered.

**Run packaging:** pooled `foldSel = ALL` (A+B+C), 8 instrument × direction × LTF cells per
arm, 32 runs total. Per-fold performance is reconstructed from each ledger row's sweep
timestamp; funnel counters are pooled and are labelled as such.

---

## 1. Specification-integrity check

`dispMin` is specified to act **only** at the BOS + displacement gate, downstream of the
sweep, the CHOCH and the CHOCH retest. If the implementation honours that, the three upstream
counters must be bit-identical across all four arms. They are:

| counter | 1.25 | 1.50 (baseline) | 1.75 | 2.00 |
|---|---|---|---|---|
| sweeps | 3836 | 3836 | 3836 | 3836 |
| CHOCH 1m | 3324 | 3324 | 3324 | 3324 |
| CHOCH 3m | 1480 | 1480 | 1480 | 1480 |
| CHOCH retests 1m | 2974 | 2974 | 2974 | 2974 |
| CHOCH retests 3m | 1095 | 1095 | 1095 | 1095 |

This holds cell-by-cell, not merely in aggregate. The 5m sweep engine is confirmed untouched.

`dropped (no slot) = 0` and `ASSERTS 21-27,32 = 0/0/0/0/0/0/0/0` in all 32 cells. No assertion
was disabled.

### Read-integrity diagnostic

Two MGC short cells (`MGC S 3m`, `MGC S 1m`) returned counters identical to the 1.75 arm when
run at 2.00. To rule out a cached relay table rather than a genuine invariance, a read-only
round-trip probe was run on `MGC S 1m`: setting `in_6 = 2.50` gave BOS+disp 5 / FVG 5 / fills 4,
and restoring `in_6 = 2.00` reproduced BOS+disp 12 / FVG 11 / fills 8 exactly. The cell responds
to the input; no MGC-short displacement candle has range/ATR in the interval [1.75, 2.00).

The 2.50 probe is a **diagnostic only**. It is not a specified Experiment B arm and its numbers
are excluded from the study data.

Identical fill sets across adjacent thresholds are common in this dataset generally — the
baseline and 1.75 arms also produce the same 11 fills for `MNQ L 1m` (BOS+disp 33 → 24) and the
same 8 fills for `MGC S 1m` (BOS+disp 20 → 12). Raising `dispMin` mostly removes BOS candidates
that never converted to a fill.

---

## 2. POOLED A+B+C FUNNEL

These are pooled counters across folds A, B and C. **They are not per-fold measurements.**

### H1 — 1m LTF structure

| dispMin | sweeps | CHOCH | retest | BOS+disp | BOS/retest | FVG | FVG/BOS | fills | fill/FVG | sweep→fill |
|---|---|---|---|---|---|---|---|---|---|---|
| 1.25 | 3836 | 3324 | 2974 | 211 | 7.09% | 154 | 73.0% | 81 | 52.6% | 2.11% |
| **1.50** | 3836 | 3324 | 2974 | **107** | 3.60% | **76** | 71.0% | **41** | 53.9% | 1.07% |
| 1.75 | 3836 | 3324 | 2974 | 69 | 2.32% | 58 | 84.1% | 35 | 60.3% | 0.91% |
| 2.00 | 3836 | 3324 | 2974 | 34 | 1.14% | 29 | 85.3% | 19 | 65.5% | 0.50% |

### H2 — 3m LTF structure

| dispMin | sweeps | CHOCH | retest | BOS+disp | BOS/retest | FVG | FVG/BOS | fills | fill/FVG | sweep→fill |
|---|---|---|---|---|---|---|---|---|---|---|
| 1.25 | 3836 | 1480 | 1095 | 117 | 10.68% | 82 | 70.1% | 34 | 41.5% | 0.89% |
| **1.50** | 3836 | 1480 | 1095 | **74** | 6.76% | **50** | 67.6% | **17** | 34.0% | 0.44% |
| 1.75 | 3836 | 1480 | 1095 | 42 | 3.84% | 32 | 76.2% | 10 | 31.2% | 0.26% |
| 2.00 | 3836 | 1480 | 1095 | 31 | 2.83% | 23 | 74.2% | 10 | 43.5% | 0.26% |

### Dose–response

BOS+displacement is **monotone decreasing** in `dispMin` on both LTFs, with no reversals:

- 1m: 211 → 107 → 69 → 34 (each step roughly halves the count)
- 3m: 117 → 74 → 42 → 31

Fills are monotone decreasing on 1m (81 → 41 → 35 → 19) and monotone non-increasing on 3m
(34 → 17 → 10 → 10).

Relative to the baseline the elasticity is high and roughly symmetric in log terms: loosening by
one step (1.50 → 1.25) roughly **doubles** BOS+disp (1m +97.2%, 3m +58.1%); tightening by one
step (1.50 → 1.75) removes about a third to a half (1m −35.5%, 3m −43.2%); two steps
(1.50 → 2.00) removes about two thirds (1m −68.2%, 3m −58.1%).

`dispMin` is therefore a **strong frequency lever**, comparable in magnitude to `swLen`
(Experiment A). Unlike `swLen`, it acts at a single, late gate and leaves the whole upstream
sequence identical, which makes its effect cleanly attributable.

### Conditional conversion

The two conversion ratios downstream of the gate move in opposite directions on 1m:

- BOS+disp → FVG rises with the threshold (71.0% → 84.1% → 85.3% at 1.50/1.75/2.00), i.e.
  larger displacement candles are more likely to leave a gap. At 1.25 the ratio is 73.0%,
  slightly above baseline, so this is not monotone across the full range.
- FVG → fill also rises on 1m (53.9% → 60.3% → 65.5%), i.e. a smaller share of gaps expire
  unfilled within `retBars`.
- On 3m neither ratio is monotone (FVG/BOS 70.1/67.6/76.2/74.2; fill/FVG 41.5/34.0/31.2/43.5).

---

## 3. Per-cell record (pooled A+B+C)

| cell | 1.25 fills | 1.50 fills | 1.75 fills | 2.00 fills |
|---|---|---|---|---|
| MGC L 1m | 15 | 4 | 2 | 1 |
| MGC L 3m | 9 | 5 | 0 | 0 |
| MGC S 1m | 13 | 8 | 8 | 8 |
| MGC S 3m | 4 | 1 | 0 | 0 |
| MNQ L 1m | 20 | 11 | 11 | 7 |
| MNQ L 3m | 6 | 1 | 1 | 1 |
| MNQ S 1m | 33 | 18 | 14 | 3 |
| MNQ S 3m | 15 | 10 | 9 | 9 |

At 1.75 and 2.00 both MGC 3m cells produce **zero fills**. Cell-level counts at the tighter
thresholds are in the single digits; several are 0 or 1.

---

## 4. Performance record

Reported because the protocol requires the full record, **not** to select a value. No arm is
declared better than another and no arm is proposed as a replacement for the frozen baseline.

### H1 — 1m, pooled A+B+C

| dispMin | fills | W | L | TO | win% | R post-drag | expectancy | maxDD (R) |
|---|---|---|---|---|---|---|---|---|
| 1.25 | 81 | 15 | 66 | 6 | 18.5% | +3.992 | +0.0493 | 27.928 |
| **1.50** | **41** | **5** | **36** | **4** | **12.2%** | **−13.389** | **−0.3266** | **23.941** |
| 1.75 | 35 | 5 | 30 | 3 | 14.3% | −7.045 | −0.2013 | 16.587 |
| 2.00 | 19 | 2 | 17 | 1 | 10.5% | −8.152 | −0.4291 | 13.085 |

### H2 — 3m, pooled A+B+C

| dispMin | fills | W | L | TO | win% | R post-drag | expectancy | maxDD (R) |
|---|---|---|---|---|---|---|---|---|
| 1.25 | 34 | 6 | 28 | 3 | 17.6% | +0.808 | +0.0238 | 8.654 |
| **1.50** | **17** | **4** | **13** | **1** | **23.5%** | **+6.482** | **+0.3813** | **9.232** |
| 1.75 | 10 | 3 | 7 | 0 | 30.0% | +7.662 | +0.7662 | 4.171 |
| 2.00 | 10 | 3 | 7 | 0 | 30.0% | +7.662 | +0.7662 | 4.171 |

### Per-fold, H1 1m (R post-drag / fills)

| dispMin | fold A | fold B | fold C |
|---|---|---|---|
| 1.25 | −0.466 / 40 | −0.085 / 17 | +4.543 / 24 |
| **1.50** | −4.940 / 16 | −6.812 / 12 | −1.637 / 13 |
| 1.75 | −3.860 / 15 | −4.761 / 10 | +1.576 / 10 |
| 2.00 | −2.306 / 8 | +0.364 / 5 | −6.210 / 6 |

### Per-fold, H2 3m (R post-drag / fills)

| dispMin | fold A | fold B | fold C |
|---|---|---|---|
| 1.25 | −1.617 / 19 | +4.761 / 7 | −2.336 / 8 |
| **1.50** | −4.256 / 10 | +9.944 / 2 | +0.794 / 5 |
| 1.75 | −3.076 / 3 | +9.944 / 2 | +0.794 / 5 |
| 2.00 | −3.076 / 3 | +9.944 / 2 | +0.794 / 5 |

Sign of the pooled result is not stable across folds in any arm. The H2 3m totals at 1.50, 1.75
and 2.00 are dominated by the **same two fold-B trades** (both wins, +9.944R combined); those
two trades survive every threshold in this range, so the three arms are not independent
observations of one another. Fold B carries only 2 of the 17 baseline 3m fills.

### Event clustering (Phase 13G identities, unchanged)

| dispMin | execution N | primary clusters | alternative clusters | fills in multi-fill clusters |
|---|---|---|---|---|
| 1.25 | 115 | 86 | 76 | 63.5% |
| **1.50** | **58** | **43** | **37** | **69.0%** |
| 1.75 | 45 | 32 | 26 | 80.0% |
| 2.00 | 29 | 20 | 17 | 79.3% |

Convergence is not reduced by tightening the threshold — the share of fills sitting in
multi-fill clusters is **higher** at 1.75 and 2.00 than at the baseline. The effective number of
independent market events is well below the raw fill count in every arm. The trade counts above
must not be treated as independent observations.

---

## 5. What this experiment establishes

1. `dispMin` acts exactly where the specification says it does. All upstream counters are
   invariant across the full 1.25–2.00 range, cell by cell.
2. It is a strong, monotone frequency lever on BOS+displacement in both LTFs, of the same order
   of magnitude as `swLen` but acting at a single late gate.
3. Downstream conditional conversion (BOS→FVG, FVG→fill) increases with the threshold on 1m but
   is not monotone on 3m.
4. Sample sizes at 1.75 and 2.00 fall to a level (10 fills pooled on 3m, two cells at zero)
   where the per-cell record carries very little information.
5. Performance differences between arms are not separable from cluster structure and fold
   composition. Nothing here demonstrates an edge at any threshold.

**The frozen V53 setting (`dispMin = 1.50`) remains the official baseline regardless of these
results.** No ranking of arms is made and no winner is declared.

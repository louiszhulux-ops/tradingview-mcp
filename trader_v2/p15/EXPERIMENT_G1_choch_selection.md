# Phase 15 — Experiment G1: CHOCH Candidate Selection

**Hypothesis component varied:** F1, which eligible opposing pivot serves as the CHOCH reference.

**Frozen baseline rule:** the most recent confirmed eligible opposing pivot after the sweep,
**re-evaluated forward on every LTF bar** (the reference rolls).

**G1 rule:** the **first** confirmed eligible opposing pivot after the sweep is latched and
retained for the life of the sequence. Definition exactly as pre-registered.

---

## 0. Provenance

| | |
|---|---|
| executed baseline | `p15/executed/V53_EXECUTED_BUILD.pine`, sha256 `2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6` |
| G1 artifact | `p15/exec_arms/V53_EXEC_P15_G1_first_choch_pivot.pine`, sha256 `ef56c15f47988307e0ea47bdc2a18923d2125d712b152ffd56931c5711bf3c11` |
| derivation | 6 hunks, +14 / −8 lines against the executed baseline |
| output layer | byte-identical to the executed baseline (verified) |
| injection | `pine_set_source` (608 lines) then `pine_smart_compile`; `pineVersion` 141.0 → 142.0 |

Residue checks before injection: C1 `aA` 0, D1 0, E1 0, F1 0; the `qV` BOS fallback, the strict
single-bar FVG test and the `bufATR` stop are all present, so every other frozen rule is restored.

The **eligibility gate is untouched** — a pivot still qualifies only if its pivot bar lies in a
chart bar strictly after the sweep bar (`oB > swB`). G1 changes only *which* eligible pivot is
used, not which pivots are eligible.

---

## 1. Invariant and propagation

Unlike F1, G1 is expected to propagate through essentially the whole funnel: changing the CHOCH
reference changes the CHOCH level, hence which retests occur, hence BOS timing and reference,
hence FVG association and fills. The only hard requirement is that the 5m engine is untouched.

| counter | baseline | G1 |
|---|---|---|
| **sweeps** | **3836** | **3836** ✓ |

Sweeps are bit-identical in every cell (MGC L 884, MGC S 872, MNQ L 952, MNQ S 1128). Nothing
except the registered candidate-selection rule changed.

`ASSERTS 21-27,32 = 0/0/0/0/0/0/0/0` in all eight cells — **A21 and A32 both read 0**, exactly as
pre-registered. `dropped (no slot) = 0` everywhere.

Counter 4 changes meaning under G1 (it now counts how often a roll *would* have occurred rather
than how often one did). This build's compact funnel table does not surface counter 4, so it is
recorded here as a definitional note rather than a measured value.

Trade-level confirmation of the latch: MNQ L 1m 2026-06-25 has `ch 12:05 / chL 30151.25` where
the baseline recorded `ch 12:04 / chL 30140.5` — an earlier, higher pivot retained instead of the
rolled-forward one. MGC L 3m 2026-07-13 04:10 shows `chL 4065.7` vs baseline `4065.5`, with the
BOS reference correspondingly swapped to `4065.5`.

---

## 2. POOLED A+B+C FUNNEL

| | sweeps | CHOCH | retest | BOS+disp | FVG | fills |
|---|---|---|---|---|---|---|
| 1m baseline | 3836 | 3324 | 2974 | 107 | 76 | 41 |
| **1m G1** | 3836 | **2486** | **2266** | **88** | **63** | **35** |
| Δ 1m | +0.0% | **−25.2%** | −23.8% | −17.8% | −17.1% | −14.6% |
| 3m baseline | 3836 | 1480 | 1095 | 74 | 50 | 17 |
| **3m G1** | 3836 | **1379** | **1035** | **70** | **49** | **16** |
| Δ 3m | +0.0% | **−6.8%** | −5.5% | −5.4% | −2.0% | −5.9% |

### The effect attenuates monotonically down the funnel

On 1m the proportional loss shrinks at every stage: **−25.2% → −23.8% → −17.8% → −17.1% →
−14.6%**. Latching removes a quarter of all CHOCH events, but only about one seventh of the fills.
Sequences that survive the stricter reference convert at a *higher* rate — retest/CHOCH rises
89.5% → 91.2%, and fill/FVG rises 53.9% → 55.6%.

The counter that absorbs the loss is `expire pre-CHOCH`, which rises sharply everywhere
(MNQ L 1m 123 → 330; MNQ S 1m 161 → 392; MGC L 1m 146 → 350; MNQ L 3m 590 → 613). A latched
pivot that price never breaks simply times out at the `dispWait` deadline, where the rolling
reference would have found a later, closer pivot to break.

### Timeframe asymmetry

**1m is 3.7× more affected than 3m at the CHOCH stage** (−25.2% vs −6.8%). This is the same
direction as E1 and the opposite of A, B, C1 and D1. The mechanism is visible: on 1m many pivots
form inside the `dispWait` window, so the rolling reference has far more opportunity to advance;
on 3m fewer pivots form, so "first" and "most recent" more often coincide.

---

## 3. Per-cell record (pooled A+B+C)

| cell | baseline CHOCH | G1 CHOCH | baseline fills | G1 fills |
|---|---|---|---|---|
| MGC L 1m | 738 | 534 | 4 | 2 |
| MGC S 1m | 790 | 594 | 8 | 7 |
| MNQ L 1m | 829 | 622 | 11 | 12 |
| MNQ S 1m | 967 | 736 | 18 | 14 |
| MGC L 3m | 344 | 313 | 5 | 5 |
| MGC S 3m | 347 | 326 | 1 | 1 |
| MNQ L 3m | 362 | 339 | 1 | 1 |
| MNQ S 3m | 427 | 401 | 10 | 9 |

Every cell loses CHOCH events. Fill counts move in both directions (MNQ L 1m gains one), and
three 3m cells are unchanged at the fill level despite losing CHOCH events upstream.

---

## 4. Performance record

Reported because the protocol requires the full record. No ranking, no winner.

### Pooled A+B+C

| | fills | W | L | TO | win% | R post-drag | expectancy | maxDD (R) |
|---|---|---|---|---|---|---|---|---|
| 1m baseline | 41 | 5 | 36 | 4 | 12.2% | −13.389 | −0.3266 | 23.941 |
| **1m G1** | 35 | 4 | 31 | 4 | 11.4% | **−13.021** | −0.3720 | 23.553 |
| 3m baseline | 17 | 4 | 13 | 1 | 23.5% | +6.482 | +0.3813 | 9.232 |
| **3m G1** | 16 | 4 | 12 | 1 | 25.0% | **+7.517** | +0.4698 | 9.232 |

Removing 25% of 1m CHOCH events and 15% of 1m fills moves 1m R by **+0.368** — essentially
nothing. Total R is close to unchanged in both hypotheses while the structural funnel above it
changed substantially.

### Per fold (R post-drag / fills)

| | fold A | fold B | fold C |
|---|---|---|---|
| 1m baseline | −4.940 / 16 | −6.812 / 12 | −1.637 / 13 |
| 1m G1 | −7.797 / 13 | −5.759 / 11 | +0.535 / 11 |
| 3m baseline | −4.256 / 10 | +9.944 / 2 | +0.794 / 5 |
| 3m G1 | **−4.256 / 10** | **+9.944 / 2** | +1.829 / 4 |

On 1m all three folds move, and they move in **opposite directions** — fold A worsens by 2.857R
while fold C improves by 2.172R. On 3m folds A and B are bit-identical to the baseline despite
101 CHOCH events being removed pool-wide; only fold C changes.

### Event clustering (Phase 13G identities, unchanged) — recorded, not analysed here

| | execution N | primary | alternative | largest | fills in multi-fill clusters |
|---|---|---|---|---|---|
| baseline all | 58 | 43 | 37 | 3 | 69.0% |
| **G1 all** | 51 | 42 | 35 | 3 | **58.8%** |
| G1 1m | 35 | 30 | 23 | 3 | 62.9% |
| G1 3m | 16 | 12 | 12 | 2 | 50.0% |

G1 has the **lowest clustering share of any arm** (58.8% vs baseline 69.0%): 51 fills resolve to
42 primary and 35 alternative events, against 58 → 43/37 at baseline. Fills fell 12% but
alternative events fell only 5%. Carried into the joint analysis.

---

## 5. What this experiment establishes

1. The 5m engine is untouched: sweeps are bit-identical in every cell, and only the registered
   candidate-selection rule changed. A21 and A32 read 0 as pre-registered; `dropped` is 0.
2. G1 is the **only arm that materially moves the CHOCH stage itself** — −25.2% on 1m — and its
   effect then propagates through every subsequent stage, as expected for this rule.
3. The effect **attenuates monotonically** down the funnel (−25.2% → −14.6% on 1m). Surviving
   sequences convert at higher rates at both the retest and fill gates.
4. The loss is absorbed by `expire pre-CHOCH`: a latched pivot that price never breaks times out.
5. **1m is 3.7× more sensitive than 3m**, matching E1 and opposing A, B, C1 and D1.
6. Despite removing a quarter of 1m CHOCH events, pooled R moves +0.368 on 1m and +1.035 on 3m —
   both negligible. On 3m, folds A and B are bit-identical to the baseline.
7. Nothing here demonstrates an edge under either convention.

**The frozen V53 setting (most recent eligible opposing pivot, rolling) remains the official
baseline regardless of these results.** No ranking is made and no winner is declared.

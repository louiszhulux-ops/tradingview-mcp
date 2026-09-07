# Phase 15 — Experiment D1: BOS Reference Eligibility

**Hypothesis component varied:** F2, which opposing pivot may serve as the BOS reference.

**Frozen baseline rule:** the most recent confirmed opposing pivot after CHOCH, with the **CHOCH
pivot excluded** — when the most recent pivot *is* the CHOCH pivot, the reference falls back to
the previous opposing pivot (`qV`).

**D1 rule:** allow the CHOCH pivot to be used as the BOS reference if it is the most recent valid
opposing pivot. The fallback branch is removed. Definition exactly as pre-registered.

---

## 0. Provenance

| | |
|---|---|
| executed baseline | `p15/executed/V53_EXECUTED_BUILD.pine`, sha256 `2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6` |
| D1 artifact | `p15/exec_arms/V53_EXEC_P15_D1_bos_reference.pine`, sha256 `85861d7ed443006105f21bd43129fd3f1a5652d24684845920d08890c03ce583` |
| derivation | 2 hunks, +2 / −4 lines against the executed baseline |
| output layer | byte-identical to the executed baseline (verified) |
| injection | `pine_set_source` (600 lines) then `pine_smart_compile`; `pineVersion` 138.0 → 139.0 |

The full D1 file replaces the C1 source wholesale, so no separate baseline restore was needed.
C1's `aA` LTF-ATR field is absent from D1 (verified by grep before injection, and confirmed
behaviourally below). All fifteen inputs were read back after the compile at their frozen values.

---

## 1. Specification-integrity check

D1 acts at the BOS reference. Everything upstream — sweeps, CHOCH, CHOCH retests — must be
untouched.

| counter | baseline | D1 | change |
|---|---|---|---|
| sweeps | 3836 | 3836 | **0** |
| CHOCH 1m | 3324 | 3324 | **0** |
| CHOCH 3m | 1480 | 1480 | **0** |
| CHOCH retests 1m | 2974 | 2974 | **0** |
| CHOCH retests 3m | 1095 | 1095 | **0** |

All five hold exactly, cell by cell. **The funnel first diverges at the BOS stage**, as specified.

This also confirms C1 was fully removed: MGC L 1m retests read 664 here, the baseline value,
against C1's 677.

### Assertion A22 — expected non-zero by construction

A22 counts BOS firing on the CHOCH pivot itself, which is impossible under the baseline rule and
is exactly what D1 permits. It is retained and reported, never disabled.

| cell | A22 |
|---|---|
| MGC L 1m | 3 |
| MGC S 1m | 3 |
| MNQ L 1m | 6 |
| MNQ S 1m | 2 |
| MGC L 3m | 11 |
| MGC S 3m | 11 |
| MNQ L 3m | 15 |
| MNQ S 3m | 19 |
| **1m total** | **14** |
| **3m total** | **56** |

Every other assertion (A21, A23, A24, A25, A26, A27, A32) reads 0 in all eight cells, and
`dropped (no slot) = 0` everywhere. A22 firing 70 times total is the direct measurement of how
often the rule change actually bound.

Trade-level confirmation: MGC L 1m 2026-06-26 shows `chL 4059.3` and `bosL 4059.3` — the BOS
reference *is* the CHOCH level — where the baseline recorded `bosL 4061.2` for the same sequence,
same BOS timestamp 12:57.

---

## 2. POOLED A+B+C FUNNEL

Pooled counters across folds A, B and C. **Not per-fold measurements.**

### H1 — 1m LTF structure

| | sweeps | CHOCH | retest | BOS+disp | FVG | fills |
|---|---|---|---|---|---|---|
| baseline | 3836 | 3324 | 2974 | 107 | 76 | 41 |
| **D1** | 3836 | 3324 | 2974 | **107** | **76** | **41** |

### H2 — 3m LTF structure

| | sweeps | CHOCH | retest | BOS+disp | FVG | fills |
|---|---|---|---|---|---|---|
| baseline | 3836 | 1480 | 1095 | 74 | 50 | 17 |
| **D1** | 3836 | 1480 | 1095 | **85** (+14.9%) | **55** (+10.0%) | **19** (+11.8%) |

### Downstream propagation, recorded separately

- **1m: A22 fires 14 times and not one counter downstream moves.** BOS+disp, FVG and fills are
  bit-identical to the baseline, and so is the R total to three decimals.
- **3m: A22 fires 56 times and the funnel widens** — +11 BOS+disp, +5 FVG, +2 fills.

The 1m result is not a null change; it is a change that is absorbed. When the most recent
opposing pivot is the CHOCH pivot, the baseline still fires a BOS — against the *previous* pivot
level instead. Both levels are frequently broken by the same displacement candle, so the sequence
advances on the same bar and the FVG, which is defined by that candle, is unchanged. What D1
alters on 1m is the recorded reference level, not the event.

On 3m the same substitution more often changes *whether* the break qualifies at all, because the
two candidate levels are further apart in a coarser structure. That is where the extra 11
BOS+displacement events come from.

The BOS→FVG conversion falls on 3m (67.6% → 64.7%) while FVG→fill rises slightly (34.0% →
34.5%): the additional BOS events are somewhat less likely than average to leave a gap.

---

## 3. Per-cell record (pooled A+B+C)

| cell | baseline bos | D1 bos | baseline fvg | D1 fvg | baseline fills | D1 fills |
|---|---|---|---|---|---|---|
| MGC L 1m | 12 | 12 | 10 | 10 | 4 | 4 |
| MGC S 1m | 20 | 20 | 18 | 18 | 8 | 8 |
| MNQ L 1m | 33 | 33 | 22 | 22 | 11 | 11 |
| MNQ S 1m | 42 | 42 | 26 | 26 | 18 | 18 |
| MGC L 3m | 19 | 19 | 13 | 15 | 5 | 5 |
| MGC S 3m | 20 | 21 | 13 | 13 | 1 | 1 |
| MNQ L 3m | 14 | 18 | 6 | 8 | 1 | **3** |
| MNQ S 3m | 21 | 27 | 18 | 19 | 10 | 10 |

All four 1m cells are identical at every stage. Of the four 3m cells, three change upstream and
only one changes its fill count.

---

## 4. Performance record

Reported because the protocol requires the full record. **An increase in fills or P&L is not
evidence of improvement**, and none is claimed here.

### Pooled A+B+C

| | fills | W | L | TO | win% | R post-drag | expectancy | maxDD (R) |
|---|---|---|---|---|---|---|---|---|
| H1 1m baseline | 41 | 5 | 36 | 4 | 12.2% | −13.389 | −0.3266 | 23.941 |
| **H1 1m D1** | 41 | 5 | 36 | 4 | 12.2% | **−13.389** | −0.3266 | 23.941 |
| H2 3m baseline | 17 | 4 | 13 | 1 | 23.5% | +6.482 | +0.3813 | 9.232 |
| **H2 3m D1** | 19 | 4 | 15 | 1 | 21.1% | **+4.438** | +0.2336 | 11.276 |

On 1m the executed result is **identical to the baseline in every field**, drawdown included.

On 3m the two additional fills are both losses (MNQ L 3m, 2026-06-17, a pair sharing one
sweep cluster and entering at the same price 30477.25 on the same FVG). Wins are unchanged at 4.

### Per fold (R post-drag / fills)

| | fold A | fold B | fold C |
|---|---|---|---|
| H1 1m baseline | −4.940 / 16 | −6.812 / 12 | −1.637 / 13 |
| H1 1m D1 | −4.940 / 16 | −6.812 / 12 | −1.637 / 13 |
| H2 3m baseline | −4.256 / 10 | +9.944 / 2 | +0.794 / 5 |
| H2 3m D1 | **−6.300 / 12** | +9.944 / 2 | +0.794 / 5 |

As in C1, the entire difference sits in **fold A**; folds B and C are bit-identical to the
baseline. This is now a repeated pattern across two independent rule changes and is noted for the
joint C1–G1 analysis.

### Event clustering (Phase 13G identities, unchanged) — recorded, not yet analysed

| | execution N | primary | alternative | fills in multi-fill clusters |
|---|---|---|---|---|
| baseline all | 58 | 43 | 37 | 69.0% |
| **D1 all** | 60 | 44 | 38 | 70.0% |
| D1 1m | 41 | 31 | 25 | 73.2% |
| D1 3m | 19 | 13 | 13 | 63.2% |

Per the study plan, clustering is carried forward and analysed jointly once C1–G1 are all
complete, not interpreted arm by arm.

---

## 5. What this experiment establishes

1. D1 acts exactly where the specification says: sweeps, CHOCH and CHOCH retests are bit-identical
   to the baseline in all eight cells, and divergence begins at the BOS stage.
2. The rule change genuinely binds — A22 fires 70 times (14 on 1m, 56 on 3m) — so the null 1m
   result is absorption, not inaction.
3. **On 1m the change is completely absorbed:** 14 substitutions of the BOS reference produce
   bit-identical BOS, FVG, fill and R figures. Both candidate levels are typically cleared by the
   same displacement candle, so only the recorded level changes, not the event.
4. **On 3m the change propagates:** +14.9% BOS+displacement, +10.0% FVG, +11.8% fills, because in
   the coarser structure the two candidate levels are far enough apart to change whether the
   break qualifies.
5. The 3m/1m sensitivity asymmetry now holds for a third consecutive lever (`swLen`, retest
   tolerance, BOS reference). Whatever is fragile in this hypothesis is concentrated in the 3m
   sequence.
6. Nothing here demonstrates an edge under either rule.

**The frozen V53 setting (CHOCH pivot excluded from BOS eligibility) remains the official
baseline regardless of these results.** No ranking is made and no winner is declared. Joint
analysis of C1–G1 against the frozen baseline is deferred until G1 is complete.

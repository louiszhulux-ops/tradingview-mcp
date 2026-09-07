# Phase 15 — Experiment E1: FVG Association

**Hypothesis component varied:** F4, which fair-value gap is associated with the displacement.

**Frozen baseline rule:** exactly one test, at LTF bar `d+1`: the FVG whose **middle candle IS the
displacement candle**. No gap there → the setup is invalid immediately.

**E1 rule:** scan forward from `d+1`, testing at each LTF bar the gap whose middle candle is the
previous bar, and take the **first qualifying gap whose middle candle is at or after the
displacement candle**. Definition exactly as pre-registered.

---

## 0. Provenance

| | |
|---|---|
| executed baseline | `p15/executed/V53_EXECUTED_BUILD.pine`, sha256 `2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6` |
| E1 artifact | `p15/exec_arms/V53_EXEC_P15_E1_fvg_association.pine`, sha256 `686850a48eb9c2f8515acbbb5ccc4b6145a39eb91dacf7e2fcdd4e7ad1eec04d` |
| derivation | 2 hunks, +7 / −4 lines against the executed baseline |
| output layer | byte-identical to the executed baseline (verified) |
| injection | `pine_set_source` (605 lines) then `pine_smart_compile`; `pineVersion` 139.0 → 140.0 |

Pre-injection residue checks: C1's `aA` field absent (count 0); D1 absent — the `qV` BOS fallback
is present, so the frozen BOS reference rule is restored. All fifteen inputs read back at frozen
values after the compile, `in_7` (dispWait) = 12.

---

## 1. The dispWait scan bound — preserved, not normalized

E1's forward scan is bounded by the **existing frozen `dispWait` = 12 chart bars measured from
the sweep bar**. No new parameter was introduced and no compensation was applied.

Mechanically: section 3 of the program expires only states 1–3, so a state-4 sequence that is
scanning forward is not touched by the ordinary deadline loop. It is invalidated by the new check
`bar_index - swB > dispWait` on the first scan bar at which no qualifying gap exists past the
deadline. The consequence is that a sequence now *persists* while scanning, and which
displacement sequence gets scanned inside the 12-bar bound changes accordingly.

**That is part of E1's mechanical consequence and has been left intact.** It is not treated as an
additional experimental parameter, and nothing was added to hold the scanned set constant.

The counter that records this directly is `no FVG invalid`, which collapses because invalidation
is deferred rather than immediate:

| cell | baseline `no FVG invalid` | E1 |
|---|---|---|
| MNQ L 1m | 11 | 4 |
| MNQ S 1m | 16 | 3 |
| MGC S 1m | 2 | 0 |
| MGC L 1m | 2 | 1 |
| MNQ L 3m | 10 | 8 |
| MNQ S 3m | 8 | 2 |
| MGC S 3m | 8 | 5 |
| MGC L 3m | 4 | 2 |

`dropped (no slot) = 0` in all eight cells, so the longer slot occupancy did not exhaust the
24-slot pool anywhere. This was checked rather than assumed, since longer-lived state-4 sequences
could in principle have caused drops; had any appeared they would have been reported, not fixed.

---

## 2. Specification-integrity check

E1 must leave everything up to and including BOS detection untouched.

| counter | baseline | E1 | change |
|---|---|---|---|
| sweeps | 3836 | 3836 | **0** |
| CHOCH 1m / 3m | 3324 / 1480 | 3324 / 1480 | **0** |
| CHOCH retests 1m / 3m | 2974 / 1095 | 2974 / 1095 | **0** |
| **BOS+disp 1m / 3m** | **107 / 74** | **107 / 74** | **0** |

All four hold, and **cell by cell**: every one of the eight cells reproduces its baseline
`bos` count exactly (MGC L 1m 12, MGC S 1m 20, MNQ L 1m 33, MNQ S 1m 42, MGC L 3m 19,
MGC S 3m 20, MNQ L 3m 14, MNQ S 3m 21). **The associated-FVG selection is the only strategy
change, and the funnel first diverges at the FVG stage.**

### Assertions

`ASSERTS 21-27,32 = 0/0/0/0/0/0/0/0` in **all eight cells**. In particular **A24 reads 0**, as
pre-registered: it is evaluated only on the first scan bar, where it retains its original meaning
of "BOS bar == displacement bar". No E1 diagnostic was expected to fire and none did.

---

## 3. POOLED A+B+C FUNNEL

Pooled counters across folds A, B and C. **Not per-fold measurements.**

### H1 — 1m LTF structure

| | sweeps | CHOCH | retest | BOS+disp | FVG | FVG/BOS | fills | fill/FVG | sweep→fill |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 3836 | 3324 | 2974 | 107 | 76 | 71.0% | 41 | 53.9% | 1.07% |
| **E1** | 3836 | 3324 | 2974 | 107 | **99** (+30.3%) | **92.5%** | **56** (+36.6%) | 56.6% | 1.46% |

### H2 — 3m LTF structure

| | sweeps | CHOCH | retest | BOS+disp | FVG | FVG/BOS | fills | fill/FVG | sweep→fill |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 3836 | 1480 | 1095 | 74 | 50 | 67.6% | 17 | 34.0% | 0.44% |
| **E1** | 3836 | 1480 | 1095 | 74 | **57** (+14.0%) | **77.0%** | **21** (+23.5%) | 36.8% | 0.55% |

### Propagation, recorded separately

The change is confined to one conversion and then flows through:

- **BOS → FVG is where E1 acts**: 71.0% → 92.5% on 1m, 67.6% → 77.0% on 3m. Scanning forward
  finds a qualifying gap in almost every 1m sequence that reaches BOS.
- **FVG → fill barely moves** (53.9% → 56.6% on 1m, 34.0% → 36.8% on 3m). The gaps E1 admits
  behave, at the fill stage, much like the ones the baseline already admitted.
- Net: fills +36.6% on 1m, +23.5% on 3m.

**This is the first arm where 1m is more sensitive than 3m.** In A, B, C1 and D1 the 3m sequence
moved further; here 1m moves further at every stage past BOS (+30.3% vs +14.0% FVG, +36.6% vs
+23.5% fills). Recorded as an observation; not explained here.

---

## 4. Per-cell record (pooled A+B+C)

| cell | bos (base = E1) | baseline fvg | E1 fvg | baseline fills | E1 fills |
|---|---|---|---|---|---|
| MGC L 1m | 12 | 10 | 11 | 4 | 5 |
| MGC S 1m | 20 | 18 | 20 | 8 | 8 |
| MNQ L 1m | 33 | 22 | 29 | 11 | 16 |
| MNQ S 1m | 42 | 26 | 39 | 18 | 27 |
| MGC L 3m | 19 | 13 | 17 | 5 | 7 |
| MGC S 3m | 20 | 13 | 15 | 1 | 3 |
| MNQ L 3m | 14 | 6 | 6 | 1 | 1 |
| MNQ S 3m | 21 | 18 | 19 | 10 | 10 |

Every cell holds its baseline BOS count. Six of eight gain FVGs; five of eight gain fills.

---

## 5. Performance record

Reported because the protocol requires the full record. **An increase in fills is not evidence of
improvement, and a decrease in P&L is not evidence of harm.** No ranking against the baseline or
against C1/D1 is made.

### Pooled A+B+C

| | fills | W | L | TO | win% | R post-drag | expectancy | maxDD (R) |
|---|---|---|---|---|---|---|---|---|
| H1 1m baseline | 41 | 5 | 36 | 4 | 12.2% | −13.389 | −0.3266 | 23.941 |
| **H1 1m E1** | 56 | **5** | 51 | 5 | 8.9% | −29.015 | −0.5181 | 33.676 |
| H2 3m baseline | 17 | 4 | 13 | 1 | 23.5% | +6.482 | +0.3813 | 9.232 |
| **H2 3m E1** | 21 | **4** | 17 | 2 | 19.0% | +2.285 | +0.1088 | 12.415 |

The single most compact description of this arm: **all 19 additional fills are losses.** Wins are
unchanged at 5 on 1m and 4 on 3m, and every gap E1 newly associates that goes on to fill,
fills into a loser over this sample.

### Per fold (R post-drag / fills)

| | fold A | fold B | fold C |
|---|---|---|---|
| H1 1m baseline | −4.940 / 16 | −6.812 / 12 | −1.637 / 13 |
| H1 1m E1 | −17.477 / 28 | −8.866 / 14 | −2.672 / 14 |
| H2 3m baseline | −4.256 / 10 | +9.944 / 2 | +0.794 / 5 |
| H2 3m E1 | −7.439 / 13 | +9.944 / 2 | −0.220 / 6 |

**E1 breaks the fold pattern seen in C1 and D1.** In those arms every change sat in fold A while
folds B and C stayed bit-identical. Here all three folds move on 1m, and folds A and C move on
3m. Only 3m fold B is unchanged — the same two trades that have survived every arm so far.

### Event clustering (Phase 13G identities, unchanged) — recorded, not analysed

| | execution N | primary | alternative | largest | fills in multi-fill clusters |
|---|---|---|---|---|---|
| baseline all | 58 | 43 | 37 | 3 | 69.0% |
| **E1 all** | 77 | 57 | 51 | 4 | 62.3% |
| E1 1m | 56 | 42 | 36 | 4 | 64.3% |
| E1 3m | 21 | 15 | 15 | 2 | 57.1% |

Carried forward for the joint C1–G1 analysis; not interpreted here.

---

## 6. What this experiment establishes

1. E1 acts exactly where the specification says. Sweeps, CHOCH, CHOCH retests **and BOS+disp**
   are bit-identical to the baseline in all eight cells; the funnel first diverges at FVG
   association, and BOS detection is untouched.
2. The `dispWait` scan bound is preserved intact, with no new parameter and no compensation. Its
   signature is the collapse of `no FVG invalid` (deferred rather than immediate invalidation).
   `dropped (no slot)` remained 0 everywhere, checked rather than assumed.
3. All assertions read 0, A24 included, exactly as pre-registered.
4. E1 acts almost entirely on one conversion: BOS→FVG rises 71.0% → 92.5% on 1m and
   67.6% → 77.0% on 3m, while FVG→fill barely moves.
5. This is the **first arm in which 1m is the more sensitive timeframe**, reversing the pattern of
   A, B, C1 and D1.
6. **It also breaks the fold-A concentration** seen in C1 and D1: all three folds move on 1m.
7. All 19 additional fills are losses; wins are unchanged in both hypotheses.
8. Nothing here demonstrates an edge under either rule.

**The frozen V53 setting (unique displacement-candle FVG) remains the official baseline regardless
of these results.** No ranking is made and no winner is declared. Joint analysis of C1–G1 against
the frozen baseline is deferred until G1 is complete.

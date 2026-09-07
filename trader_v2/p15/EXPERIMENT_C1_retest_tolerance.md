# Phase 15 — Experiment C1: CHOCH Retest Tolerance

**Hypothesis component varied:** the CHOCH retest definition.

**Frozen baseline rule:** `hitR = isLong ? l <= L : h >= L` — the retest must touch the CHOCH
level exactly. Zero tolerance, a price level rather than a zone.

**C1 rule:** `hitR = isLong ? l <= L + tol : h >= L - tol`, with
`tol = 0.10 × ATR(14)` measured **on the LTF**, obtained via `request.security_lower_tf` and used
**only** for this proximity test. The FVG fill test remains exact. Definition exactly as
pre-registered; the provenance correction did not redefine it.

---

## 0. Provenance

| | |
|---|---|
| executed baseline | `p15/executed/V53_EXECUTED_BUILD.pine`, sha256 `2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6` |
| C1 artifact | `p15/exec_arms/V53_EXEC_P15_C1_retest_tol.pine`, sha256 `905ef1a9db1d9c26774e2520de424f16fd398688fd8c6cb201e5a1172bfb490a` |
| derivation | 2 hunks, +5 / −1 lines against the executed baseline |
| output layer | byte-identical to the executed baseline (verified) |
| injection | `pine_set_source` (606 lines) then `pine_smart_compile`; `pineVersion` 137.0 → 138.0 |

This is the first arm run under the corrected provenance (see `PHASE15_PROVENANCE_CORRECTION.md`).
All fifteen inputs were read back after the compile and confirmed at their frozen values:
tgtR 5, bufATR 0.20, minWick 0.10, dispMin 1.50, dispWait 12, retBars 24, minRatr 0.05,
maxRatr 3.00, maxBars 144, costUSD 3.00, swLen 10, lSw 3.

---

## 1. Specification-integrity check

The retest gate sits after the sweep and after CHOCH, and before BOS. If the implementation
honours that, sweeps and CHOCH must be untouched and retests may only **increase** — a proximity
band can add retests, never remove one.

| counter | baseline | C1 | change |
|---|---|---|---|
| sweeps | 3836 | 3836 | **0** |
| CHOCH 1m | 3324 | 3324 | **0** |
| CHOCH 3m | 1480 | 1480 | **0** |
| CHOCH retests 1m | 2974 | 3054 | +80 |
| CHOCH retests 3m | 1095 | 1163 | +68 |

Both hold, cell by cell. Retests rose in **all eight** cells and fell in none:

| cell | baseline rt | C1 rt | Δ |
|---|---|---|---|
| MGC L 1m | 664 | 677 | +13 |
| MGC S 1m | 703 | 723 | +20 |
| MNQ L 1m | 762 | 773 | +11 |
| MNQ S 1m | 845 | 881 | +36 |
| MGC L 3m | 259 | 274 | +15 |
| MGC S 3m | 262 | 273 | +11 |
| MNQ L 3m | 258 | 281 | +23 |
| MNQ S 3m | 316 | 335 | +19 |

The complementary counter moves the other way by the same amount: on MNQ L 1m,
`expire post-CHOCH` falls 67 → 56 while retests rise 762 → 773. Sequences that previously
expired waiting for an exact touch now retest instead. Nothing else is redirected.

Ledger evidence of the same thing at trade level: on the fills that survive unchanged, the
retest timestamp moves **earlier** and nothing else moves — e.g. MNQ L 1m 2026-07-16, `rt`
12:55 → 12:53, with identical CHOCH, BOS, FVG, entry, stop and outcome.

`dropped (no slot) = 0` and `ASSERTS 21-27,32 = 0/0/0/0/0/0/0/0` in all eight cells. No
assertion was disabled.

---

## 2. POOLED A+B+C FUNNEL

Pooled counters across folds A, B and C. **Not per-fold measurements.**

### H1 — 1m LTF structure

| | sweeps | CHOCH | retest | ret/CHOCH | BOS+disp | BOS/ret | FVG | FVG/BOS | fills | fill/FVG | sweep→fill |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 3836 | 3324 | 2974 | 89.5% | 107 | 3.60% | 76 | 71.0% | 41 | 53.9% | 1.07% |
| **C1** | 3836 | 3324 | 3054 | 91.9% | 112 | 3.67% | 80 | 71.4% | 41 | 51.2% | 1.07% |

### H2 — 3m LTF structure

| | sweeps | CHOCH | retest | ret/CHOCH | BOS+disp | BOS/ret | FVG | FVG/BOS | fills | fill/FVG | sweep→fill |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 3836 | 1480 | 1095 | 74.0% | 74 | 6.76% | 50 | 67.6% | 17 | 34.0% | 0.44% |
| **C1** | 3836 | 1480 | 1163 | 78.6% | 86 | 7.39% | 59 | 68.6% | 22 | 37.3% | 0.57% |

### Propagation

The band is a small, uniform loosening at one gate, and it propagates asymmetrically:

- **1m**: +2.7% retests → +4.7% BOS+disp → +5.3% FVG → **+0.0% fills**. The extra structure
  reaches the FVG stage and then stops; not one additional 5m fill results.
- **3m**: +6.2% retests → +16.2% BOS+disp → +18.0% FVG → **+29.4% fills**. Each stage amplifies.

3m is roughly 2.3× more sensitive to the retest definition than 1m at the retest gate itself, and
the gap widens downstream. This mirrors Experiment A, where 3m was 3.6× more sensitive to
`swLen`; the 3m sequence has fewer, scarcer candidates, so a loosened gate has proportionally
more room to act.

The two conditional conversions barely move (FVG/BOS 71.0 → 71.4 on 1m, 67.6 → 68.6 on 3m).
Whatever the band admits behaves, at the next gate, like what was already being admitted.

---

## 3. Per-cell record (pooled A+B+C)

| cell | baseline fills | C1 fills | Δ | baseline W | C1 W |
|---|---|---|---|---|---|
| MGC L 1m | 4 | 4 | 0 | 1 | 1 |
| MGC S 1m | 8 | 8 | 0 | 2 | 2 |
| MNQ L 1m | 11 | 11 | 0 | 0 | 0 |
| MNQ S 1m | 18 | 18 | 0 | 2 | 2 |
| MGC L 3m | 5 | **9** | +4 | 1 | **5** |
| MGC S 3m | 1 | **2** | +1 | 0 | 0 |
| MNQ L 3m | 1 | 1 | 0 | 0 | 0 |
| MNQ S 3m | 10 | 10 | 0 | 3 | 3 |

Six of eight cells produce an identical fill set. The entire change in executions comes from two
3m cells, and almost all of it from one.

---

## 4. Performance record

Reported because the protocol requires the full record, **not** to select a value. No arm is
declared better and none is proposed as a replacement for the frozen baseline.

### Pooled A+B+C

| | fills | W | L | TO | win% | R post-drag | expectancy | maxDD (R) |
|---|---|---|---|---|---|---|---|---|
| H1 1m baseline | 41 | 5 | 36 | 4 | 12.2% | −13.389 | −0.3266 | 23.941 |
| **H1 1m C1** | 41 | 5 | 36 | 4 | 12.2% | **−13.389** | −0.3266 | 21.851 |
| H2 3m baseline | 17 | 4 | 13 | 1 | 23.5% | +6.482 | +0.3813 | 9.232 |
| **H2 3m C1** | 22 | 8 | 14 | 1 | 36.4% | +25.346 | +1.1521 | 7.183 |

**On 1m the executed result is identical to the baseline** — same 41 fills, same 5 wins, same
R to three decimals. The band changed the funnel and changed nothing that was traded. (Max
drawdown differs only because the intra-sequence ordering of a few retests shifted.)

### Per fold (R post-drag / fills)

| | fold A | fold B | fold C |
|---|---|---|---|
| H1 1m baseline | −4.940 / 16 | −6.812 / 12 | −1.637 / 13 |
| H1 1m C1 | −4.940 / 16 | −6.812 / 12 | −1.637 / 13 |
| H2 3m baseline | −4.256 / 10 | +9.944 / 2 | +0.794 / 5 |
| H2 3m C1 | **+14.608 / 15** | +9.944 / 2 | +0.794 / 5 |

**The entire H2 3m difference sits in fold A.** Folds B and C are bit-identical to the baseline —
same fills, same outcomes, same R. Fold A gains 5 fills and 4 wins.

Those four extra wins are not four independent events. Three of them share one sweep cluster
(MGC 2026-05-28 05:00 / 05:05, entering at the same price 4408.8 on the same FVG as the
baseline's existing 04:50 fill) and two share another (MGC 2026-06-17 08:30 / 08:50, both
entering at 4347 on the same FVG). In cluster terms the 3m arm goes from 12 to 15 alternative
events while adding 5 fills — the added executions are largely re-entries into two market
events the baseline already traded once.

### Event clustering (Phase 13G identities, unchanged)

| | execution N | primary | alternative | fills in multi-fill clusters |
|---|---|---|---|---|
| baseline all | 58 | 43 | 37 | 69.0% |
| **C1 all** | 63 | 46 | 40 | 69.8% |
| baseline 3m | 17 | 12 | 12 | 58.8% |
| **C1 3m** | 22 | 15 | 15 | 63.6% |

---

## 5. What this experiment establishes

1. The retest tolerance acts exactly where the specification says it does: sweeps and CHOCH are
   invariant cell by cell, and retests rise in every cell and fall in none — the only direction a
   proximity band can move them.
2. It is a **weak** frequency lever at its own gate (+2.7% on 1m, +6.2% on 3m), far weaker than
   `swLen` or `dispMin`, but the 3m sequence amplifies it downstream to +29.4% fills while the 1m
   sequence absorbs it entirely.
3. On 1m the change is invisible in executions: the funnel widens through the FVG stage and
   produces exactly the same 41 fills with exactly the same outcomes.
4. On 3m the change is concentrated to a degree that forbids reading it as a general effect:
   one cell, one fold, and two sweep clusters supply almost all of it.
5. Nothing here demonstrates an edge, at either tolerance.

**The frozen V53 setting (exact-level retest, zero tolerance) remains the official baseline
regardless of these results.** No ranking is made and no winner is declared.

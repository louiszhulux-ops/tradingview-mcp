# Phase 15 — Controlled Sensitivity / Ablation Study: Final Report

**Scope.** Twelve arms (frozen baseline + 11 ablations), 8 pooled A+B+C cells each, 96 relay
runs. Every arm changes exactly one pre-registered hypothesis component. This phase was **not**
optimization: no arm is ranked, no variant is called optimal, and no parameter change is
recommended. The frozen V53 configuration remains the baseline throughout.

**Data.** `trader_v2/p15/runs/*.txt` (committed run records), analysed by `p15_analyze.py` and
`p15_joint.py`, which read only committed files. Raw joint output: `p15/P15_JOINT_DATA.txt`.

---

## 0. Execution artifact provenance correction

The initial Phase 15 manifest identified `V53_ltf_sequence.pine` as the execution baseline.
During Experiment B preparation, an audit established that TradingView had actually been
executing `p15/executed/V53_EXECUTED_BUILD.pine`. The two artifacts were compared and found to
have identical strategy-bearing logic, with only write-only diagnostic/output differences.
Therefore Experiments A and B remain valid and are not rerun. Experiments C1–G1 are re-derived
directly from the actual executed artifact to maintain single-concept experimental provenance.

| role | file | sha256 |
|---|---|---|
| canonical frozen source (did not execute) | `trader_v2/V53_ltf_sequence.pine` | `7490766b6e3de062989a8e7f10939869cc6b679d253ce584f223064aa5797ef5` |
| **execution / provenance baseline** | `trader_v2/p15/executed/V53_EXECUTED_BUILD.pine` | `2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6` |

The equivalence check compared strategy sections 1–6 with comments and blanks stripped: the only
differences are writes to `K33`, `K34`, `K35` and the `tie` local that gates `K35` — write-only
diagnostics no decision reads. All fifteen inputs are identical in the same order, preserving the
`in_0 … in_14` mapping. Full record: `p15/PHASE15_PROVENANCE_CORRECTION.md`; the stop that
raised it: `p15/PHASE15_HARD_STOP.md`. The five previously hand-edited C1–G1 files are marked
SUPERSEDED and NEVER EXECUTED, and are retained as historical evidence.

**This is an improvement to reproducibility, not a failure of the experiment.**

Every C1–G1 arm was mechanically diffed against the executed baseline before running; each shows
exactly one strategy-bearing change and a byte-identical section-7 output layer
(`p15/exec_arms/SINGLE_CONCEPT_VERIFICATION.txt`).

---

## 1. Which assumptions are structurally invariant?

**The 5m sweep engine is invariant under every single arm.** Sweeps = 3836 pooled, and
bit-identical in all 8 cells, in all 11 ablations. Nothing tested reaches it. This is the one
unconditional structural result of the phase.

Beyond that, invariance is *conditional on where the rule sits*. Per-cell bit-identity against
the baseline (YES = all 8 cells identical at that stage):

| arm | sweeps | CHOCH | retest | BOS+disp | FVG | fills |
|---|---|---|---|---|---|---|
| A swLen 2/4/5 | YES | no | no | no | no | no |
| B dispMin 1.25/1.75/2.00 | YES | YES | YES | no | no | no |
| C1 retest band | YES | YES | no | no | no | no |
| D1 BOS reference | YES | YES | YES | no | no | no |
| E1 FVG association | YES | YES | YES | **YES** | no | no |
| F1 raw stop | YES | YES | YES | YES | **YES** | no |
| G1 CHOCH latch | YES | no | no | no | no | no |

Two further invariances are worth naming because they were *measured*, not assumed:

- **D1 on 1m is fully invariant at every stage**, including fills and R to three decimals — even
  though the rule genuinely bound (assertion A22 fired 14 times on 1m). Both candidate BOS levels
  are typically cleared by the same displacement candle, so only the recorded level changes, not
  the event.
- **C1 on 1m leaves fills and R bit-identical** while widening the funnel through the FVG stage
  (+2.7% retests, +4.7% BOS, +5.3% FVG, +0.0% fills).

---

## 2. Which assumptions cause changes only downstream?

Ordering the arms by the first stage at which any counter moves gives a clean structural
hierarchy — and it matches the specification's own ordering of the rules:

| first stage moved | arms | interpretation |
|---|---|---|
| CHOCH | **A (swLen), G1 (CHOCH latch)** | reach the whole sequence |
| CHOCH retest | **C1** | everything from the retest gate down |
| BOS + displacement | **B (dispMin), D1** | late-gate only |
| FVG | **E1** | association only |
| fill | **F1** | outcome layer only |

Three arms are strictly downstream-confined:

- **F1 (stop)** — identical through FVG in every cell. Its fills delta is entirely absorbed by
  the R-band, verified by the conservation identity `FVG = fills + R-band rejects + FVG retest
  expiry`, which reconciles in all 8 cells. The stop is the R-band denominator, so a fills change
  is a mechanical consequence, not a leak.
- **E1 (FVG association)** — identical through BOS+disp in every cell; acts on one conversion
  (BOS→FVG rises 71.0% → 92.5% on 1m) and leaves FVG→fill nearly unchanged.
- **B (dispMin)** and **D1** — identical through the CHOCH retest in every cell.

---

## 3. Which assumptions materially alter the funnel?

Magnitude at the fill stage (pooled A+B+C, % vs baseline):

| arm | 1m fills | 3m fills |
|---|---|---|
| B dispMin 1.25 | **+97.6%** | **+100.0%** |
| B dispMin 2.00 | **−53.7%** | −41.2% |
| A swLen 2 | +36.6% | **+111.8%** |
| E1 FVG association | +36.6% | +23.5% |
| A swLen 5 | −31.7% | **−70.6%** |
| A swLen 4 | −26.8% | −35.3% |
| G1 CHOCH latch | −14.6% | −5.9% |
| B dispMin 1.75 | −14.6% | −41.2% |
| C1 retest band | +0.0% | +29.4% |
| F1 raw stop | +2.4% | +17.6% |
| D1 BOS reference | +0.0% | +11.8% |

**Two levers dominate: `swLen` (A) and `dispMin` (B).** Each can roughly double or halve the
trade count within its pre-registered range, and `dispMin` does so monotonically with no
reversals (BOS+disp 1m 211 → 107 → 69 → 34). These are frequency levers, not edge levers.

**G1 is the only arm that materially moves the CHOCH stage itself** (−25.2% on 1m), and its
effect *attenuates* monotonically downstream (−25.2% → −23.8% → −17.8% → −17.1% → −14.6%):
sequences surviving the stricter reference convert at higher rates at both the retest and fill
gates.

**C1, D1 and F1 are structurally minor.** Each moves the funnel by low single-digit percentages
on 1m or leaves it untouched.

---

## 4. Are effects consistent across 1m and 3m?

**No.** This is one of the phase's clearer negative results.

Of the 11 arms, **8 are more sensitive on 3m and 3 on 1m** (B dispMin 2.00, E1, G1). The
sensitivity ratio |Δ1m / Δ3m| at the fill stage ranges from **0.00** (C1 and D1: no 1m change at
all against +29.4% and +11.8% on 3m) to **2.49** (G1).

An "LTF fragility" generalization looked well supported after A, B, C1 and D1 — four consecutive
levers with greater 3m sensitivity. **E1 and G1 broke it.** The mechanism is legible: rules that
depend on *pivot density* (swLen, retest tolerance, BOS reference) bite harder on 3m, where
structure is scarce; rules that depend on *how many bars are available to search* (E1's forward
FVG scan, G1's rolling-vs-latched reference) bite harder on 1m, where many more bars fall inside
the same `dispWait` window.

So the timeframes are not two samples of one behaviour, and results from one do not transfer to
the other.

---

## 5. Are effects consistent across folds A/B/C?

**No, and the inconsistency is severe enough to be the study's main statistical caveat.**

Fold-level R (post-drag) / fills, reconstructed from sweep timestamps:

| arm | 1m A | 1m B | 1m C | 3m A | 3m B | 3m C |
|---|---|---|---|---|---|---|
| baseline | −4.940/16 | −6.812/12 | −1.637/13 | −4.256/10 | +9.944/2 | +0.794/5 |
| C1 | = | = | = | +14.608/15 | = | = |
| D1 | = | = | = | −6.300/12 | = | = |
| E1 | −17.477/28 | −8.866/14 | −2.672/14 | −7.439/13 | = | −0.220/6 |
| F1 | −1.423/18 | −5.726/11 | −1.854/13 | −6.324/12 | +9.938/2 | −0.258/6 |
| G1 | −7.797/13 | −5.759/11 | +0.535/11 | = | = | +1.829/4 |

Three things stand out.

1. **Changes concentrate in single folds.** C1's entire 3m effect (+18.9R) is in fold A; folds B
   and C are bit-identical. D1's entire 3m effect is in fold A. G1's 3m folds A *and* B are
   bit-identical to baseline.
2. **3m fold B is nearly immovable** — bit-identical in 6 of 11 arms. It contains just **2 fills,
   both wins, +9.944R**, and those two trades survive almost every rule change. They alone are
   larger than the pooled 3m result of most arms.
3. **Folds move in opposite directions within one arm.** Under G1, 1m fold A worsens by 2.857R
   while fold C improves by 2.172R. Pooling hides this.

A pooled A+B+C number for any arm is therefore not a stable summary of that arm's behaviour.

---

## 6. How much of the trade-count / P&L movement is explained by event clustering?

Collapsing executions to market events under the Phase 13G **alternative** identity:

| arm | fills | alt events | ΔR execution | ΔR event | share of ΔR surviving |
|---|---|---|---|---|---|
| A swLen 2 | 92 | 57 | −24.294 | −15.203 | 63% |
| A swLen 4 | 41 | 27 | −12.131 | −10.455 | 86% |
| A swLen 5 | 33 | 24 | −15.822 | −13.329 | 84% |
| B 1.25 | 115 | 76 | +11.707 | +12.673 | 108% |
| B 1.75 | 45 | 26 | +7.524 | +5.468 | 73% |
| B 2.00 | 29 | 17 | +6.417 | +2.951 | 46% |
| C1 | 63 | 40 | +18.864 | +8.918 | **47%** |
| D1 | 60 | 38 | −2.044 | −1.022 | 50% |
| E1 | 77 | 51 | −19.823 | −14.488 | 73% |
| F1 | 62 | 39 | +1.260 | +3.287 | **261%** |
| G1 | 51 | 35 | +1.403 | −3.860 | **−275%** |

The baseline itself has 58 fills resolving to 43 primary / 37 alternative events — **36% of the
execution count is duplication**, and 69.0% of fills sit in multi-fill clusters.

Typically **half to five-sixths** of an arm's apparent P&L movement survives collapsing to
events. Two arms are pathological: F1's event-level move is 2.6× its execution-level move, and
**G1's flips sign entirely** (+1.403R at execution level, −3.860R at event level). For those two,
the execution-level P&L figure is not a description of what happened to the underlying events.

Concrete instance: C1's +18.9R on 3m came overwhelmingly from **five extra fills in fold A**, of
which four were re-entries into just **two MGC sweep clusters** the baseline already traded once,
at the same entry price on the same FVG. The event-level gain is roughly half the execution-level
gain for exactly this reason.

---

## 7. Which conclusions survive both clustering identities?

Sign of total R at execution level, primary identity, and alternative identity:

| arm | R exec | R / primary | R / alternative | consistent? |
|---|---|---|---|---|
| baseline | −6.907 | −9.000 | −2.767 | **yes (all −)** |
| A swLen 2 | −31.201 | −25.292 | −17.971 | **yes (all −)** |
| A swLen 4 | −19.038 | −16.287 | −13.222 | **yes (all −)** |
| A swLen 5 | −22.729 | −17.112 | −16.096 | **yes (all −)** |
| B 1.25 | +4.800 | +11.513 | +9.905 | **yes (all +)** |
| B 1.75 | +0.617 | −3.532 | +2.701 | **no — sign flips** |
| B 2.00 | −0.490 | −2.889 | +0.184 | **no — sign flips** |
| C1 | +11.957 | **−0.081** | +6.151 | **no — sign flips** |
| D1 | −8.951 | −10.022 | −3.789 | **yes (all −)** |
| E1 | −26.730 | −23.487 | −17.255 | **yes (all −)** |
| F1 | −5.647 | −5.820 | +0.520 | **no — sign flips** |
| G1 | −5.504 | −10.920 | −6.627 | **yes (all −)** |

**Surviving both identities:** the baseline is negative; all three `swLen` arms are negative;
E1, D1 and G1 are negative; B dispMin 1.25 is positive. Seven of eleven arms plus the baseline
hold their sign under all three accountings.

**Not surviving:** B 1.75, B 2.00, **C1** and F1 change sign depending on which identity is used.
C1 is the sharpest case — **+11.957R at execution level, −0.081R under the primary identity**.
Any statement that C1 "improved" the result is an artifact of counting duplicate executions as
independent trades.

---

## 8. Which findings are merely descriptive because effective N is tiny?

Effective independent N is far smaller than the fill count, and the *winning* event count is
smaller still:

| arm | fills | alt events | wins | **winning events** |
|---|---|---|---|---|
| baseline | 58 | 37 | 9 | **7** |
| A swLen 2 | 92 | 57 | 11 | 8 |
| A swLen 4 | 41 | 27 | 4 | 3 |
| A swLen 5 | 33 | 24 | 2 | **2** |
| B 1.25 | 115 | 76 | 21 | 16 |
| B 1.75 | 45 | 26 | 8 | 6 |
| B 2.00 | 29 | 17 | 5 | 4 |
| C1 | 63 | 40 | 13 | 9 |
| D1 | 60 | 38 | 9 | 7 |
| E1 | 77 | 51 | 9 | 7 |
| F1 | 62 | 39 | 10 | 7 |
| G1 | 51 | 35 | 8 | 6 |

Winning events per fold (alternative identity) for the baseline: **A 3/19, B 2/8, C 2/10.**

At a 5R target the breakeven win rate is 16.67%. The baseline's entire A+B+C result rests on
**seven winning events**, and any fold-level claim rests on **two or three**. Ten of twelve arms
have fewer than ten winning events in total.

Consequently the following are **descriptive observations only**, with no inferential weight:

- every per-fold R figure in §5, and every per-fold comparison between arms;
- every arm's total R and expectancy, including the baseline's;
- the direction of any P&L difference between two arms;
- the 3m fold B result (+9.944R from **two** trades) — the single largest positive number
  anywhere in the study, and the least independent;
- C1's 3m gain and F1's and G1's sign-unstable results.

The findings that carry real weight are **structural**, because they rest on thousands of events
rather than on wins: sweep invariance (3836 sweeps × 11 arms), the per-cell bit-identity table,
the stage at which each rule first bites, the monotone dose-response of `dispMin`, the
attenuation of G1 down the funnel, and the conservation identities that confirmed each arm
changed only what it was supposed to.

---

## 9. Standing conclusions

1. The 5m sweep engine is insulated from every hypothesis component tested.
2. The rules form a clean structural hierarchy, and each arm's reach matches its position in the
   specification — evidence that the implementation does what the specification says.
3. `swLen` and `dispMin` are strong frequency levers; C1, D1 and F1 are structurally minor; G1
   is the only lever that materially moves CHOCH itself.
4. Sensitivity does **not** transfer between 1m and 3m, and does **not** transfer between folds.
5. Roughly a third of the execution count is duplication; for two arms the execution-level P&L
   movement misrepresents the event-level movement in magnitude or sign.
6. **No arm demonstrates an edge.** The baseline is negative under all three accountings, and no
   ablation produces a result that is both positive and stable across clustering identities and
   folds.

**No winner is declared, no variant is called optimal, and no parameter change is recommended.**
The frozen V53 configuration remains the baseline. Whether this hypothesis warrants further work
is a separate decision that this phase was not designed to make.

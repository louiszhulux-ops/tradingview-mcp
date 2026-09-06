
## Pooled 88-run design — progress

| arm | cells (of 8) | status |
|---|---|---|
| BASELINE swLen 3 / dispMin 1.50 | 8 | complete, verified against 13F+14 |
| A swLen=2 | 8 | **complete** |
| A swLen=4 | 0 | pending |
| A swLen=5 | 0 | pending |
| B dispMin=1.25 | 0 | pending |
| B dispMin=1.75 | 0 | pending |
| B dispMin=2.00 | 0 | pending |
| C1 retest tolerance | 0 | pending |
| D1 BOS reference | 0 | pending |
| E1 FVG association | 0 | pending |
| F1 raw stop | 0 | pending |
| G1 first-CHOCH latch | 0 | pending |

**2026-09-06 07:06 UTC — TradingView relay returned HTTP 502 (Cloudflare
origin_bad_gateway), same failure mode as the outage recorded in
`trader_v2/RELAY_OUTAGE.md`. Backing off and retrying; no strategy file, baseline
or committed result is affected.**

## Experiment B — displacement threshold (COMPLETE)
- arm 1.25: 8/8 cells, commit 15ced38
- arm 1.75: 8/8 cells, commit a47abd6
- arm 2.00: 8/8 cells
- Read-integrity diagnostic run on MGC S 1m (in_6 2.50 round-trip) to confirm the
  1.75 == 2.00 invariance on MGC short is genuine, not a cached relay table.
  Diagnostic only; 2.50 is not a study arm and is excluded from the data.
- Upstream counters (sweeps / CHOCH / CHOCH retest) identical across all four arms
  in every cell -> dispMin acts only at the BOS+displacement gate, as specified.
- Report: p15/EXPERIMENT_B_displacement.md
- Next in fixed order: C1 (CHOCH retest tolerance). C1 requires injecting
  V53_P15_C1_retest_tol.pine via pine_set_source + pine_smart_compile first.

## HARD STOP raised at the start of Experiment C1
The build executing on the chart is not V53_ltf_sequence.pine. Preserved as
p15/executed/V53_EXECUTED_BUILD.pine (sha256 2dafbafd...). Strategy logic is
identical; the differences are three write-only diagnostic counters (K33/34/35)
and the section 7 output layer. A/B results stand; C1-G1 not run.
See p15/PHASE15_HARD_STOP.md. Nothing repaired, nothing injected.

## HARD STOP RESOLVED (study owner decision)
- Provenance anchor = p15/executed/V53_EXECUTED_BUILD.pine (sha256 2dafbafd...).
- V53_ltf_sequence.pine stays canonical and unmodified (sha256 7490766b...).
- A and B are NOT rerun; results preserved unchanged.
- C1-G1 re-derived from the executed baseline into p15/exec_arms/, each verified
  as exactly one strategy-bearing change with a byte-identical output layer.
- Old p15/V53_P15_*.pine arm files: SUPERSEDED, NEVER EXECUTED, retained as history.
- See p15/PHASE15_PROVENANCE_CORRECTION.md and p15/exec_arms/SINGLE_CONCEPT_VERIFICATION.txt.
- Remaining budget: 40 pooled runs (C1, D1, E1, F1, G1). Resume at C1.

## Experiment C1 -- CHOCH retest tolerance (COMPLETE, 8/8)
- Ran p15/exec_arms/V53_EXEC_P15_C1_retest_tol.pine (sha256 905ef1a9...).
- Integrity: sweeps/CHOCH bit-identical to baseline cell by cell; retests rose in all
  8 cells and fell in none; asserts 0; dropped 0.
- 1m: funnel widens to the FVG stage but produces the IDENTICAL 41 fills / -13.389R.
- 3m: +5 fills, all in fold A, from two MGC sweep clusters.
- Report: p15/EXPERIMENT_C1_retest_tolerance.md
- NOTE: pine_smart_compile clicks "Pine Save", so the cloud script
  USER;b798deb2c9084500a1c38b14775961da now holds the C1 source at pineVersion 138.0.
  The executed baseline is preserved on disk and must be re-injected and recompiled
  after G1 to restore the cloud script.
- Next: D1 (BOS reference). Remaining budget after C1: 32 pooled runs.

## Experiment D1 -- BOS reference eligibility (COMPLETE, 8/8)
- Ran p15/exec_arms/V53_EXEC_P15_D1_bos_reference.pine (sha256 85861d7e...);
  pineVersion 138.0 -> 139.0. Full file replaced C1 wholesale (aA absent, verified).
- Integrity: sweeps, CHOCH AND CHOCH retests all bit-identical to baseline in every
  cell; divergence begins at BOS, as specified. A21/A23-A27/A32 = 0 everywhere;
  dropped = 0. A22 EXPECTED non-zero by construction: 14 on 1m, 56 on 3m, total 70.
- 1m: change fully absorbed -- BOS/FVG/fills/R bit-identical to baseline.
- 3m: BOS+disp +14.9%, FVG +10.0%, fills +11.8%; the 2 extra fills are both losses
  in one MNQ L 3m sweep cluster. All change again confined to fold A.
- Report: p15/EXPERIMENT_D1_bos_reference.md
- Clustering recorded but NOT interpreted; joint C1-G1 analysis deferred until after G1.
- Next: E1 (FVG association). Remaining budget after D1: 24 pooled runs.

## Experiment E1 -- FVG association (COMPLETE, 8/8)
- Ran p15/exec_arms/V53_EXEC_P15_E1_fvg_association.pine (sha256 686850a4...);
  pineVersion 139.0 -> 140.0. C1 residue 0, D1 residue 0 (qV fallback restored).
- Integrity: sweeps, CHOCH, CHOCH retests AND BOS+disp all bit-identical to baseline
  in every cell (1m bos 107, 3m bos 74). Divergence begins at FVG association only.
  ALL assertions 0 including A24, as pre-registered. dropped = 0 in all 8 cells.
- dispWait scan bound PRESERVED, not normalized: no new parameter, no compensation.
  Signature is the collapse of "no FVG invalid" (deferred invalidation).
- Propagation: BOS->FVG 71.0%->92.5% (1m), 67.6%->77.0% (3m); FVG->fill barely moves.
  fills +36.6% (1m), +23.5% (3m).
- FIRST arm where 1m is more sensitive than 3m, and FIRST arm to break the fold-A
  concentration: all three folds move on 1m.
- All 19 additional fills are losses; wins unchanged (5 on 1m, 4 on 3m).
- Report: p15/EXPERIMENT_E1_fvg_association.md
- Clustering recorded, NOT interpreted; joint C1-G1 analysis after G1.
- Next: F1 (stop construction), then G1. Remaining budget: 16 pooled runs.

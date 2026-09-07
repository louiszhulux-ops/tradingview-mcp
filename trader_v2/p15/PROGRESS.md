
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

## Experiment F1 -- stop construction (COMPLETE, 8/8)
- Ran p15/exec_arms/V53_EXEC_P15_F1_stop_raw_extreme.pine (sha256 4b305b21...);
  pineVersion 140.0 -> 141.0. C1/D1/E1 residue all 0.
- INVARIANT CORRECTED BEFORE THE RUN: fills cannot be part of it. The stop is the
  R-band denominator (r = |E - stp|, ratio = r/ATR, fill only if 0.05 <= ratio <= 3.00),
  so a fills change is a mechanical consequence, not an upstream leak.
  Enforced invariant: sweeps -> CHOCH -> retest -> BOS+disp -> FVG identical.
- RESULT: all five bit-identical to baseline on both LTFs AND in every individual cell
  (FVG per cell 10/18/22/26/13/13/6/18 = baseline exactly). No upstream leak.
- Conservation identity FVG = fills + rbandRej + fvgExp reconciles in all 8 cells.
  In the four 1m cells FVG expiry is unchanged and rbandRej moves exactly opposite fills.
- fills 41->42 (1m), 17->20 (3m); deltas run in BOTH directions per cell, so the R-band
  binds at both edges. ASSERTS 0, dropped 0 everywhere.
- Outcome divergence via three mechanisms: timeout->stop conversion (1m TO 4->2;
  MNQ L 1m 2 timeouts -> 0), rescaled R denominator, and a mechanically larger $3 drag
  per unit R (losses further below -1R, e.g. -1.137R -> -1.250R).
- R: 1m -13.389 -> -9.003; 3m +6.482 -> +3.356. Both drawdowns rise.
- First arm to move 3m fold B (+9.944 -> +9.938) -- via the R denominator, not trade selection.
- Report: p15/EXPERIMENT_F1_stop_construction.md
- Clustering recorded, NOT interpreted. Changed win rates are NOT evidence either stop is better.
- Next: G1 (CHOCH candidate selection), the last arm. Remaining budget: 8 pooled runs.

## Experiment G1 -- CHOCH candidate selection (COMPLETE, 8/8) -- PHASE 15 DATA COLLECTION FINISHED
- Ran p15/exec_arms/V53_EXEC_P15_G1_first_choch_pivot.pine (sha256 ef56c15f...);
  pineVersion 141.0 -> 142.0. C1/D1/E1/F1 residue all 0; eligibility gate untouched.
- Integrity: sweeps bit-identical in every cell (3836 pooled). A21 and A32 both 0 as
  pre-registered; all other asserts 0; dropped 0. Counter 4 changes meaning by design
  and is not surfaced by this build's compact table.
- Propagation (expected and legitimate for this rule): 1m CHOCH -25.2%, retest -23.8%,
  BOS -17.8%, FVG -17.1%, fills -14.6% -- attenuating monotonically down the funnel.
  3m much weaker: -6.8% / -5.5% / -5.4% / -2.0% / -5.9%.
- Loss absorbed by expire pre-CHOCH (MNQ L 1m 123 -> 330).
- 1m is 3.7x more sensitive than 3m -- matches E1, opposes A/B/C1/D1.
- R barely moves: 1m -13.389 -> -13.021, 3m +6.482 -> +7.517. On 3m folds A and B are
  bit-identical to baseline; on 1m all three folds move, in opposite directions.
- Lowest clustering share of any arm: 58.8% vs baseline 69.0%.
- Report: p15/EXPERIMENT_G1_choch_selection.md
- ALL 40 C1-G1 RUNS COMPLETE. No further experiments or probes. Next and last step:
  the joint Phase 15 analysis of all five ablations vs the frozen executed baseline.

## PHASE 15 COMPLETE
- 96 relay runs total (baseline 8, A 24, B 24, C1 8, D1 8, E1 8, F1 8, G1 8).
- Joint analysis: p15/p15_joint.py -> p15/P15_JOINT_DATA.txt
- Final report: trader_v2/PHASE15_SENSITIVITY_REPORT.md (answers all 8 questions).
- Manifest finalised; all arms marked COMPLETE.
- No winner, no optimal variant, no parameter recommendation.
- OUTSTANDING HOUSEKEEPING: the TradingView cloud script
  USER;b798deb2c9084500a1c38b14775961da currently holds the G1 source at pineVersion
  142.0. The executed baseline is preserved on disk at p15/executed/V53_EXECUTED_BUILD.pine
  and should be re-injected and recompiled to restore the cloud script when convenient.
  No data depends on this; the provenance anchor is the disk file.

# ============================================================================
# PHASE 16 -- OUT-OF-SAMPLE VALIDATION (PRE-REGISTERED, NOT YET EXECUTED)
# ============================================================================
- Authorised scope: DATA-SELECTION EXTENSION ONLY. No strategy/parameter/execution/
  outcome change of any kind.
- Phase 16 artifact: p16/executed/V53_P16_OOS_BUILD.pine
    sha256 5c21acfab1b0c832aaa562a0afc84c94e595da2318f2366dd153c1d08172b333
    derived from p15/executed/V53_EXECUTED_BUILD.pine (sha256 2dafbafd...)
    by p16/derive_p16_oos.py -- 2 lines changed, both fold-selection:
      in_1 foldSel range 0..4 -> 0..5, and a new trailing branch (time >= FE).
    Options 0-4 semantically unchanged; FB/FC/FE untouched; 15 inputs in order;
    strategy sections 1-6 and section 7 byte-identical. Audit: p16/P16_DERIVATION_AUDIT.txt
    (all PASS), reproducible via p16/verify_p16_oos.py.
- Forward window: 2026-08-31 00:00 UTC (= FE) -> 2027-04-02 00:00 UTC, 214 days,
  targeting ~80 alternative-identity events at the observed 0.3737 events/day.
- Stopping rule is a FIXED CALENDAR DATE, not an event count, so that no inspection
  is needed to know when to stop.
- H0: p = p* = 0.1751 (breakeven from the committed baseline ledger: mean win
  +4.9238R, mean loss -1.0453R). One-sided exact binomial, alpha 0.05.
  Pre-registered alternative p1 = 0.30 (large edge); power at N=80 is 0.80.
  Detecting a modest edge is infeasible: p1=0.25 needs 182 events (~1.3y),
  p1=0.214 needs 642 (~4.7y). Failure to reject means NO LARGE EDGE, not no edge.
- Power floor: realized alt events < 40 -> automatic "insufficient".
- Post-FE data is FORWARD-HELD-OUT, not "unavailable": it existed during Phase 15
  but was excluded by the pre-registered FE gate and never inspected. Latest
  timestamp in any committed Phase 13F/14/15 run: 2026-08-28 13:40.
- Pre-written invalidation rule: any change to the artifact SHA during accumulation
  invalidates the period; a new 214-day period starts from the change date.
- NO STRATEGY RUN HAS OCCURRED. Nothing injected into TradingView. The chart still
  carries the Phase 15 G1 build (pineVersion 142.0), to be replaced at the boundary.
- Protocol: p16/PHASE16_PROTOCOL.md (committed BEFORE execution).

## PHASE 16 APPROVED AND FROZEN -- 2026-09-06
- Study owner approved the protocol and provenance setup on 2026-09-06.
  Protocol was committed (3a5bf1c) BEFORE approval and before any execution.
- Frozen and verified at approval time (all three MATCH):
    P16 OOS artifact   5c21acfab1b0c832aaa562a0afc84c94e595da2318f2366dd153c1d08172b333
    P15 exec baseline  2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6
    canonical V53      7490766b6e3de062989a8e7f10939869cc6b679d253ce584f223064aa5797ef5
- Accumulation window: 2026-08-31 00:00 UTC -> 2027-04-02 00:00 UTC (214 days).
- STOPPING BOUNDARY IS THE CALENDAR DATE, NOT AN EVENT COUNT. The ~80-event figure
  was only the design input used to derive the date; realized N will be whatever the
  frozen strategy produces over the complete window. <40 alternative events ->
  automatic INSUFFICIENT. Otherwise apply the pre-registered rule unmodified
  (H0: p = p* = 0.1751, one-sided exact binomial, alpha 0.05, alternative p1 = 0.30).
- STATUS: FORWARD ACCUMULATION. No strategy run has occurred. Nothing injected into
  TradingView. The chart intentionally retains the Phase 15 G1 build (pineVersion
  142.0) for the duration; it is replaced only at the boundary.
- Standing prohibitions until 2027-04-02: no runs, no injection, no inspection of OOS
  funnel/trades/P&L/wins/losses/event counts/performance, no estimation of expected
  OOS results, no protocol or strategy changes, no date/instrument/direction/LTF/event
  -definition changes, no interim reports, no early conclusions, no optimization.
- Pre-written invalidation rule remains in force: any change to the P16 artifact SHA
  during accumulation invalidates the period; a new 214-day period starts from the
  change date. No carve-out.
- At the boundary, execute p16/PHASE16_PROTOCOL.md section 9 in order, starting with
  SHA re-verification and a full re-run of p16/verify_p16_oos.py.

## Phase 16 — pre-accumulation protocol audit and fixes (2026-09-07)

Audit of the pre-registered Phase 16 artifacts found three required fixes. All three are now
applied. **No OOS run occurred, no market data was fetched, no TradingView connection was made,
and the OOS artifact's SHA-256 is unchanged at `5c21acfa…`.**

- **B1 — verifier hardened.** `verify_p16_oos.py` previously printed both SHA-256 values without
  asserting either, so it proved only a *relative* property; a consistent edit to both the
  baseline and the derived artifact would have passed. It now asserts both pinned hashes as hard
  checks and exits non-zero with a §8 hard-stop message. Both failure modes were demonstrated on
  mutated copies in a temporary tree.
- **B2 — event outcome rule frozen.** The primary statistic was "winning alternative-identity
  events", but the protocol never said how to classify an event whose fills disagree. Two of the
  37 baseline alternative events do exactly that (MGC1! short 1m, entries 4517.7 and 4404).
  The rule is now fixed in protocol §5: **an event is a WIN only if every fill in it is a WIN**;
  any LOSS, timeout or mixture is NON-WIN. On the baseline this gives 5 winning alternative
  events rather than 7 under a permissive rule — recorded to show the direction of effect was
  known when the rule was chosen. Phase 15 results are unchanged and are not recomputed.
- **B3 — analyser pre-registered.** `p16_analyze.py` now exists and is frozen before any OOS data.
  It is mechanical, rejects out-of-window and unexpected cells, asserts the artifact hash, and
  refuses to issue a verdict for any window but the pre-registered one. 43 tests, run against
  historical Phase 13F fixtures only.

Also applied: family-wise error stated explicitly (10% across the two one-sided tests); the N<40
floor documented as deliberately foreclosing a decisive "against"; the `foldName2 = "ALL"`
capture warning moved to §9 where the capture happens; Clopper–Pearson implementation
pre-registered; `phase16_manifest.json` created with every frozen hash and boundary.

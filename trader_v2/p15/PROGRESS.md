
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

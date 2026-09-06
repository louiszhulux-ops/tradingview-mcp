
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

# Phase 15 run progress

Full specified matrix: 7 experiments, 11 variant-arms, 24 cells each
(8 instrument x direction x LTF cells x folds A/B/C) = **264 runs**.

| arm | runs required | runs completed |
|---|---|---|
| A swLen=2 | 24 | 5 |
| A swLen=4 | 24 | 0 |
| A swLen=5 | 24 | 0 |
| B dispMin=1.25 | 24 | 0 |
| B dispMin=1.75 | 24 | 0 |
| B dispMin=2.00 | 24 | 0 |
| C1 retest tolerance | 24 | 0 |
| D1 BOS reference | 24 | 0 |
| E1 FVG association | 24 | 0 |
| F1 raw stop | 24 | 0 |
| G1 first-CHOCH latch | 24 | 0 |
| **total** | **264** | **5** |

Each run is one TradingView relay round trip: set inputs, wait for recalculation,
read three tables. Observed cost is ~2.3 relay calls per run, so the remaining 259
runs need roughly 600 further relay calls.

swLen=3 and dispMin=1.50 are the frozen control arms and are NOT re-run: their
values are the committed Phase 13F and Phase 14 results.

# Phase 15 — pooled `foldSel = ALL` design verification

The run packaging changed from *one run per fold* to *one run covering A+B+C*.
Before any experiment arm was run, the pooled packaging was verified to reproduce
the committed per-fold results **exactly**, on all eight baseline cells.

Verification method: for each cell, sum the committed Phase 13F (folds A, B) and
Phase 14 (fold C) funnel counters and win counts, and compare against the single
pooled run of the same cell on the frozen V53 (`sha256 7490766b…`).

| cell | per-fold sum (sweeps, CHOCH, retests, BOS+disp, FVG, fills, wins) | pooled run | |
|---|---|---|---|
| MGC long 1m | 884, 738, 664, 12, 10, 4, 1 | identical | ✅ |
| MGC long 3m | 884, 344, 259, 19, 13, 5, 1 | identical | ✅ |
| MGC short 1m | 872, 790, 703, 20, 18, 8, 2 | identical | ✅ |
| MGC short 3m | 872, 347, 262, 20, 13, 1, 0 | identical | ✅ |
| MNQ long 1m | 952, 829, 762, 33, 22, 11, 0 | identical | ✅ |
| MNQ long 3m | 952, 362, 258, 14, 6, 1, 0 | identical | ✅ |
| MNQ short 1m | 1128, 967, 845, 42, 26, 18, 2 | identical | ✅ |
| MNQ short 3m | 1128, 427, 316, 21, 18, 10, 3 | identical | ✅ |

**PASS on all eight cells**, every counter, plus 58 fills / 9 wins / −6.907R in
total — the exact Phase 13F + Phase 14 combined baseline.

Individual ledger rows also match one-for-one. For example MGC long 1m pooled
returns exactly the four committed fills: 06-26 WIN +4.958R (fold A), 07-10 LOSS
−1.045R (fold A), 08-04 LOSS −1.029R timeout (fold B), 08-10 LOSS −1.149R (fold C).

**Why it holds.** Arming is gated by `inFold`, so pooled sweeps are the sum of the
per-fold sweeps. Downstream counters increment for live sequences irrespective of
fold, so they sum too. The only mechanism that could break the equivalence is slot
contention — a pooled run holds more sequences live near a fold boundary — and
**`dropped (no slot)` is 0 in every run**, at 24 slots against an observed maximum
concurrency of 6–9. With no drops the two packagings are behaviourally identical.

**Consequence for reporting.** Per-fold *performance* remains exactly recoverable
from the pooled ledger, because every row carries its sweep timestamp and fold
membership is decided at the arm bar. Per-fold *funnel counters* are not separable
from a pooled run and are therefore reported as **POOLED A+B+C FUNNEL**, never
presented as per-fold measurements.

This clears the Phase 15 hard-stop condition "pooled execution produces
unexplained discrepancies".

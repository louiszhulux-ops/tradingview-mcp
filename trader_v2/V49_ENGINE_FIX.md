# V49 — measurement-engine fix, verified

Strategy logic **identical to V48**. Room threshold unchanged. 4H bias still
excluded. No new filters, families or parameters. Only the measurement engine
changed.

## What changed

| | V48 | V49 |
|---|---|---|
| simultaneous sweeps | first-match cascade: prev-day → Asia → pivot, **one candidate per bar** | **every swept level emitted independently** |
| slot pool | 8 | **24** |
| contention | counted at 2 and 8 | **counted at 2, 8 and 24, plus observed max concurrency** |
| attribution | — | **every candidate flagged** for whether the cascade would have picked it, so both populations come out of one run on one set of bars |

## 1. Verification — the engine is correct

Fold C, ten instrument × direction cells:

| | count |
|---|---|
| bars with ≥1 sweep | 2,086 |
| candidates emitted | **2,227** |
| bars sweeping 2 levels | 125 |
| bars sweeping 3 levels | 8 |
| **identity: bars + m2 + 2·m3** | **2,227 = 2,227 ✓** |
| by level type | prev-day 479, Asia 557, pivot 1,191 (sum 2,227 ✓) |

Both arithmetic identities close exactly. Simultaneous sweeps are represented
independently and nothing is double-counted or lost.

**The strongest check**: the V48-equivalent column inside the V49 run reproduces
the standalone V48 fold-C result **exactly** — n 390, E[R] +0.008, 6/10 cells.
Identical to three decimal places. The strategy logic is provably unchanged.

## 2. Recovered candidates

| | V48 | V49 | recovered |
|---|---|---|---|
| candidates | 2,086 | 2,227 | **+141 (+6.8%)** |
| fills | 1,857 | 1,972 | **+115 (+6.2%)** |

The cascade was suppressing **6.8% of candidates** — smaller than the ~7.5%
estimated from the A+B ledger, and an order of magnitude smaller than the slot
bottleneck it was found alongside.

## 3. Contention is now observable

| | count | share of candidates |
|---|---|---|
| dropped at **24** slots | **0** | 0% |
| would have dropped at 8 slots | 6 | 0.27% |
| would have dropped at 2 slots | **690** | **31.0%** |
| max concurrent observed | **10** | per cell: 4, 6, 8, 6, 5, 6, 8, 10, 5, 4 |

Three things worth recording:

1. **At 24 slots the engine loses nothing.** Every candidate is either filled,
   expired, or R-cap rejected, and all three are counted.
2. **The old 2-slot engine was discarding 31% of candidates** on fold C — worse
   than the 21.8% measured on A+B, and it was doing so silently in every result
   this project produced before V48.
3. **8 slots was marginally too few.** Max concurrency reached **10** on MCL
   short, so the V48 ledger itself was lossy at the margin (6 candidates, 0.27%).
   Small, but it was invisible until now.

## 4. Fixed engine vs V48 on fold C, ≥10R

| cell | n ALL | E ALL | n V48 | E V48 | delta |
|---|---|---|---|---|---|
| MGC long | 36 | +0.352 | 33 | +0.310 | +0.042 |
| MGC short | 52 | +0.352 | 50 | +0.290 | +0.062 |
| SIL long | 54 | +0.051 | 53 | +0.072 | −0.021 |
| SIL short | 57 | +0.313 | 57 | +0.313 | 0.000 |
| MNQ long | 35 | −0.502 | 34 | −0.483 | −0.019 |
| MNQ short | 62 | −0.241 | 60 | −0.211 | −0.030 |
| MCL long | 30 | −0.453 | 28 | −0.817 | **+0.364** |
| MCL short | 40 | +0.225 | 36 | −0.101 | **+0.326** |
| 6E long | 27 | +0.552 | 24 | +0.279 | **+0.273** |
| 6E short | 15 | +0.376 | 15 | +0.376 | 0.000 |

| | n | /day | E[R] | 90% CI | win% | PF | t | signs |
|---|---|---|---|---|---|---|---|---|
| **fixed engine** | 408 | 28.1 | **+0.086** | [−0.115, +0.287] | 21.3% | 1.35 | **+0.70** | **7/10** |
| V48-equivalent | 390 | 26.9 | +0.008 | [−0.193, +0.209] | 20.0% | 1.25 | +0.07 | 6/10 |

### This is not evidence of an edge, and I am not treating it as any

The fixed engine reads +0.086R against V48's +0.008R. Before anyone reads
anything into that:

- The entire shift comes from **18 extra fills** across three cells (MCL long,
  MCL short, 6E long). Two cells moved by more than +0.3R on 2–4 extra trades
  each. That is arithmetic on tiny subgroups, not a finding.
- **The 90% CI still spans zero**, from −0.115 to +0.287. t = +0.70.
- The seven cells with 0–2 extra fills moved by −0.030 to +0.062, i.e. by nothing.

**The conclusion from the previous phase is unchanged**: ≥10R did not reproduce
out-of-sample, and a measurement fix that adds 6% more candidates does not
resurrect it. If anything this makes the point sharper — a +0.078R swing from 18
trades shows how little it takes to move this number, which is exactly why the
+0.059R in-sample figure should never have been treated as structure.

## 5. What was not re-run, and why

Folds A+B were not re-measured under V49. The validation of record is fold C, and
that is what was re-run. Re-measuring A+B would restate an in-sample number that
is already known not to reproduce, at the cost of ten more runs.

## Status

- Measurement engine: **fixed and verified.** Cascade removed, 24 slots, zero
  silent loss, contention and simultaneous sweeps both explicitly counted.
- Sweep family: **still the primary hypothesis under question.** Two
  out-of-sample tests flat, and the engine fix does not change that.
- Next phase per instruction: a fresh search for a genuinely different source of
  edge — not further optimisation of this family.

# Phase 16 — Out-of-Sample Validation: PRE-REGISTERED PROTOCOL

**Status: PRE-REGISTERED. No validation run has been executed. No OOS result has been
inspected, estimated, previewed or reported.**

This document is written and committed **before** any Phase 16 execution. Every criterion below
is fixed now. Nothing in it may be revised after results are seen; if a result would require
changing this protocol, that is a hard stop under §11.

---

## 1. Objective

Does the already-frozen V53 hypothesis produce evidence of an edge on genuinely forward
held-out data?

This is a **validation** phase. It is not a parameter search. Prohibited throughout: parameter
optimization, sensitivity testing, variant comparison, new filters, threshold changes, stop
changes, results-driven timeframe selection, rule reinterpretation, combining Phase 15 variants,
cherry-picking, and mid-run inspection followed by changes.

Phase 15 is immutable research history. It is **not** validation evidence and is not cited as
such anywhere in the Phase 16 verdict.

---

## 2. Provenance

| role | file | sha256 |
|---|---|---|
| canonical frozen source (never executed) | `trader_v2/V53_ltf_sequence.pine` | `7490766b6e3de062989a8e7f10939869cc6b679d253ce584f223064aa5797ef5` |
| Phase 15 execution baseline | `trader_v2/p15/executed/V53_EXECUTED_BUILD.pine` | `2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6` |
| **Phase 16 execution artifact** | `trader_v2/p16/executed/V53_P16_OOS_BUILD.pine` | `5c21acfab1b0c832aaa562a0afc84c94e595da2318f2366dd153c1d08172b333` |

The Phase 16 artifact is derived from the Phase 15 execution baseline by
`trader_v2/p16/derive_p16_oos.py` (fail-loud exact-string replacement; aborts unless the source
SHA matches and each anchor matches exactly once).

### The only change: a data-selection extension

Authorised scope is data-window selection only. Two lines differ, both fold-selection:

```
@@ -12 +12 @@
-foldSel  = input.int(3,  "fold 0=A 1=B 2=C 3=A+B 4=all", minval=0, maxval=4, group="Test")
+foldSel  = input.int(3,  "fold 0=A 1=B 2=C 3=A+B 4=all 5=OOS", minval=0, maxval=5, group="Test")
@@ -32 +32 @@
-inFold = ... : foldSel == 3 ? (time < FC) : (time < FE)
+inFold = ... : foldSel == 3 ? (time < FC) : foldSel == 4 ? (time < FE) : (time >= FE)
```

The former trailing `else` becomes an explicit `foldSel == 4` branch, so **options 0–4 are
semantically unchanged**; the new trailing `else` is the forward window `time >= FE`.

Verified by `trader_v2/p16/verify_p16_oos.py` → `P16_DERIVATION_AUDIT.txt` (all checks PASS):
line count unchanged at 602; `FB`/`FC`/`FE` unchanged; all five prior fold options preserved
verbatim; **all 15 inputs present in the same order** so the `in_0 … in_14` mapping is intact and
only `in_1` differs (range/label, default still 3); **every line between the fold gate and
section 7 byte-identical**; section 7 output layer byte-identical; sweep engine, pivot detector,
CHOCH, zero-tolerance CHOCH retest, BOS reference with CHOCH-pivot exclusion, displacement,
single-bar FVG association, stop, R-band, target, timeout, drag, `SP = 24`, `dispWait` deadline
and the five `request.security_lower_tf` fields all unchanged; no `request.security(`, no
lookahead, exactly five LTF fields.

**Known labelling consequence.** Keeping the diff to two lines means `foldName2` still renders
`"ALL"` for `foldSel = 5`, and `p15_analyze.fold_of()` returns `"?"` for post-FE timestamps.
Phase 16 run files are therefore identified by filename and header, and the Phase 16 analyser
must label post-FE sweeps `OOS`. This is an analysis-script matter; the artifact is not touched
to fix it.

---

## 3. Validation dataset

**Forward window: `2026-08-31 00:00 UTC` (= `FE`) → `2027-04-02 00:00 UTC`.**
214 calendar days. Selected by `foldSel = 5`.

### Why this is forward-held-out, stated precisely

The post-`FE` data **was technically available** on the chart during Phase 15 — those runs
executed on 2026-09-06. It was excluded by the `FE` boundary, which was fixed before Phase 13F,
and it was never inspected and never entered any Phase 13–15 measurement or decision. The latest
timestamp appearing anywhere in committed Phase 13F/14/15 run data is **2026-08-28 13:40**;
recorded coverage ends **2026-08-30 23:55**.

It is therefore **forward-held-out data**, not "unavailable" data. This distinction is preserved
verbatim in the final report. Do not claim it was unavailable.

At protocol time, 2026-08-31 00:00 → 2026-09-04 20:55 UTC (~4.87 days, 5 sessions) had already
elapsed. **It is not consumed now.** It is the opening segment of the accumulation period.

### Rejected candidates, recorded so they are not revisited

- **Pre-2026-05-24 history** — falls inside `inFold` for `foldSel = 4` (`time < FE`, no lower
  bound), and the 100,000-value `request.security_lower_tf` cap (~69 days of 1m) structurally
  prevents the 1m architecture from reaching it.
- **Other instruments** (MES1!, MYM1!, …) — fully available during Phases 13–15, not
  chronologically subsequent, changes the population, and post-hoc instrument selection is
  prohibited.

---

## 4. Frozen scope

| dimension | value |
|---|---|
| instruments | MGC1! (COMEX_MINI_DL), MNQ1! (CME_MINI_DL) |
| directions | long (`in_0 = 1`), short (`in_0 = -1`) |
| LTFs | 1m (`in_2 = 1`), 3m (`in_2 = 3`) |
| cells | 8 (2 × 2 × 2) |
| strategy | frozen V53 only |
| fold | `in_1 = 5` (OOS) |

Frozen inputs, verified after compile and before the first cell:
`tgtR 5.0`, `bufATR 0.20`, `minWick 0.10`, `dispMin 1.50`, `dispWait 12`, `retBars 24`,
`minRatr 0.05`, `maxRatr 3.00`, `maxBars 144`, `costUSD 3.00`, `swLen 10`, `lSw 3`.

Outcome model, unchanged: **+5R target / −1R stop, adverse-first ordering, 144-bar timeout,
$3.00 per-trade drag**, stop = sweep extreme ± 0.20 × 5m ATR, R-band 0.05–3.00 × ATR.

Architecture: 5m chart with `request.security_lower_tf` for 1m/3m. **No native 1m/3m chart
substitution. No `request.security`. No lookahead.**

**The 1m vs 3m comparison is descriptive.** No LTF is selected on the basis of results. The same
applies to instrument and direction breakdowns.

---

## 5. Event accounting

Both Phase 13G identities are carried forward verbatim.

- **Primary:** `(instrument, direction, LTF, CHOCH timestamp, CHOCH level, BOS timestamp,
  BOS level, entry timestamp, entry price)`
- **Alternative:** `(instrument, direction, LTF, BOS timestamp, BOS level, entry timestamp,
  entry price)`

Reported for the whole window and per cell: fills, primary events, alternative events, winning
fills, winning primary events, winning alternative events, largest cluster, share of fills in
multi-fill clusters.

**Clustered fills are not independent observations.** Execution-level counts are secondary
throughout. The primary unit of analysis is the **alternative-identity event** (the more
conservative of the two, since it collapses more).

---

## 6. Statistical design — fixed now

### Null hypothesis

Breakeven is derived from the frozen baseline's committed ledger (`p15/runs/BASE_pooled.txt`,
58 fills): mean win **+4.9238R**, mean loss **−1.0453R**, so

```
p* = 1.0453 / (4.9238 + 1.0453) = 0.1751
```

**H₀: p = p\* = 0.1751** (zero expectancy). **H₁: p > p\*.**

`p*` is **fixed at 0.1751** for the primary test and is *not* recomputed from OOS data — doing so
would be circular. The realized OOS payoff geometry is reported descriptively.

> Correction of record: an earlier working note framed this as 1/6 vs 1/12. That tests
> "breakeven vs half-breakeven", not "edge vs no edge", and is not used. The correct breakeven is
> 0.1751, derived above.

### Test

One-sided **exact binomial** on winning alternative-identity events, α = 0.05.

### Is the ~80-event target defensible?

**Yes, but only as a large-effect test, and the protocol says so in advance.** At N = 80:

| alternative | expectancy | power at N=80 |
|---|---|---|
| p₁ = 0.214 | +0.23R/trade | **0.18** |
| p₁ = 0.250 | +0.45R/trade | **0.44** |
| **p₁ = 0.300** | **+0.75R/trade** | **0.80** |
| p₁ = 0.333 | +0.94R/trade | 0.93 |

N = 80 delivers conventional 80% power **only against a large edge** (p₁ = 0.30). Detecting a
modest edge is infeasible at this event rate: p₁ = 0.25 needs 182 events (~1.3 years) and
p₁ = 0.214 needs 642 events (**~4.7 years**).

**Pre-registered alternative: p₁ = 0.30.** Phase 16 is powered to detect a large edge and nothing
smaller. Failure to reject H₀ therefore means **"no large edge detected"**, never "no edge".

### Stopping rule — a fixed calendar date, not an event count

The window **ends at 2027-04-02 00:00 UTC** regardless of how many events occur.

A count-based stopping rule is rejected deliberately: knowing when 80 events had accrued would
require running the strategy and reading its tables, which is inspection. The date is computed
once, now, from the Phase 15 event rate (37 alternative events / 99 days = 0.3737/day →
80 / 0.3737 ≈ 214 days) and is **never revised**.

Realized N will differ from 80. That is expected and is not a defect. All critical values are
recomputed at the **realized** N by the same fixed rule.

### Decision thresholds

At the realized N, with p* = 0.1751 and α = 0.05 one-sided:

- **Supportive** — reject H₀: k ≥ smallest k with P(X ≥ k │ p*) ≤ 0.05
- **Against** — reject p ≥ p*: k ≤ largest k with P(X ≤ k │ p*) ≤ 0.05
- **Insufficient** — otherwise

Worked values (illustrative; the realized N governs):

| N events | supportive if ≥ | against if ≤ | power vs 0.30 |
|---|---|---|---|
| 40 | 12 | 2 | 0.56 |
| 60 | 17 | 5 | 0.66 |
| **80** | **21** | **8** | **0.80** |
| 100 | 25 | 10 | 0.89 |

Power is not perfectly monotone in N (0.67 at N=50 vs 0.66 at N=60) because exact-binomial
critical values move in integer steps. This is expected, not an error.

### Power floor

**If realized alternative events < 40, the primary test is not run and the verdict is
automatically "evidence insufficient / inconclusive."** Below 40 events, power against even a
large edge is under 0.56.

### Uncertainty reporting

A **Clopper–Pearson 95% interval** on the alternative-event win rate is reported alongside the
point estimate, plus the same for the primary identity and for execution-level fills
(descriptive). Total R is reported with the caveat that it is nearly determined by the win count
given the near-two-point R distribution.

---

## 7. Decision framework

Exactly one classification, chosen by the pre-registered criteria and not by which outcome looks
attractive:

1. **Evidence supportive of an edge** — H₀ rejected at the realized N **and** realized
   N ≥ 40 **and** the result is not driven by a single cluster, instrument, direction or LTF
   (checked by reporting the breakdown, not by removing anything).
2. **Evidence insufficient / inconclusive** — realized N < 40, or H₀ not rejected in either
   direction.
3. **Evidence against an edge** — p ≥ p* rejected at the realized N.

Positive P&L alone is **not** success. A positive result with tiny effective N, severe
clustering, or instability across 1m/3m and directions **remains descriptive** and cannot be
classified as (1).

If the data are insufficient, say so. If the strategy loses, say so. If it wins but the evidence
is weak, say so. **Do not rescue the hypothesis.**

---

## 8. Forward-data integrity rules

Binding for the whole accumulation period, 2026-08-31 → 2027-04-02:

1. **No inspection of OOS outcomes before the stopping boundary.** The Phase 16 artifact is not
   sent to TradingView, not compiled onto the chart, and not run, until the boundary.
2. No parameter changes during accumulation.
3. No strategy changes during accumulation.
4. No instrument changes.
5. No timeframe changes.
6. No selective date removal.
7. No cherry-picking.
8. **No early stopping based on profitability** — the end date is fixed and is not moved in
   either direction.
9. **No restarting the accumulation period after losing periods.**
10. Data is read **once**, at the boundary, in a single pass over all 8 cells.

### Pre-written rule for artifact change during accumulation

**If the SHA-256 of `trader_v2/p16/executed/V53_P16_OOS_BUILD.pine` changes for any reason
during the accumulation period, the accumulation period is INVALIDATED.** A new period begins on
the date of the change, running 214 days from that date under the same rules, and the invalidated
segment is never analysed or reported as validation evidence.

This rule is deliberately strict and admits no carve-out — not even for changes an audit proves
are output-layer-only — because a carve-out is the obvious avenue for post-hoc rationalisation.
The rule is written now, before any result exists.

The artifact SHA is re-verified immediately before execution at the boundary and recorded in the
execution audit.

---

## 9. Execution procedure at the boundary (not before)

1. Verify `V53_P16_OOS_BUILD.pine` SHA-256 = `5c21acfab1b0c832aaa562a0afc84c94e595da2318f2366dd153c1d08172b333`.
2. Re-run `verify_p16_oos.py`; require all checks PASS.
3. Restore the chart: inject the Phase 16 artifact and compile. *(At protocol time the chart
   carries the Phase 15 G1 experimental build, `pineVersion 142.0`; it must be replaced.)*
4. Verify all 15 inputs read back at frozen values, with `in_1 = 5`.
5. Run all 8 cells in one pass. Record per cell: instrument, direction, LTF, validation period,
   sweeps, CHOCH, CHOCH retests, BOS+displacement, FVG, fills, R-band rejects, FVG retest
   expiries, timeouts, wins, losses, post-drag R, drawdown, assertions, dropped states.
6. Do not alter anything between cells.

### Integrity checks — fail loudly

The run **fails loudly** and triggers a hard stop if: the sweep engine differs; frozen inputs
differ; unexpected assertions fire (A21–A27, A32 must read 0); `dropped (no slot)` is non-zero;
the strategy code differs; LTF architecture differs; lookahead or `request.security` appears;
output-layer modifications affect strategy decisions; or the realized coverage does not match the
pre-registered window.

Where applicable, the Phase 15 conservation identity is re-applied:
`FVG = fills + R-band rejects + FVG retest expiry`.

**Note on stop mechanics.** The stop participates in the R-band denominator
(`r = |E − stp|`, `ratio = r / ATR`, fill only if `minRatr ≤ ratio ≤ maxRatr`). Fill-count
invariance is therefore **not** demanded of any stop-layer implementation. This is recorded so
the Phase 15 F1 lesson is not re-litigated.

---

## 10. Artifacts

- `trader_v2/p16/PHASE16_PROTOCOL.md` — this document, committed **before** execution
- `trader_v2/p16/executed/V53_P16_OOS_BUILD.pine` — Phase 16 execution artifact
- `trader_v2/p16/derive_p16_oos.py`, `verify_p16_oos.py`, `P16_DERIVATION_AUDIT.txt`
- `trader_v2/p16/PHASE16_EXECUTION_AUDIT.md` — after execution
- `trader_v2/p16/PHASE16_OOS_REPORT.md` — after execution, with the 15 required sections:
  provenance; validation data definition; coverage; integrity checks; funnel; execution-level
  results; primary-event results; alternative-event results; clustering; effective N;
  uncertainty; pre-registered decision criteria; final decision; limitations; exact source and
  data hashes.

Progress log: `trader_v2/p15/PROGRESS.md`.

---

## 11. Hard-stop rule

Stop immediately, report exactly what failed and why, and do not improvise, rerun or repair
silently, if at any point: the data is not genuinely forward-held-out; provenance is ambiguous;
the frozen strategy differs; the validation range is ambiguous; a required invariant fails; or a
result would require changing this protocol.

---

## 12. No optimization after results

After Phase 16 results exist, the following are prohibited: rerunning with different `swLen` or
`dispMin`; selecting 1m or 3m on performance; changing any C1/D1/E1/F1/G1 assumption; removing
clustering; changing stop construction, R target or timeout; adding filters; removing losing
trades; selecting favourable dates or instruments.

Any future optimization is a separate research phase with its own pre-registration.

---

## 13. Confirmation

**No Phase 16 strategy run has occurred. No OOS funnel, trade, P&L or performance figure has
been produced, inspected, estimated or previewed.** The only numbers in this document come from
committed Phase 15 research records and from arithmetic on them.

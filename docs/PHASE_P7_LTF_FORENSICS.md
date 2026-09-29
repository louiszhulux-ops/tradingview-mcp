# Phase P-7 — U-14 LTF Stream Forensic Investigation

**Read-only forensic pass on U-14: can the exact `request.security_lower_tf()` stream that V53
consumed be recovered, or deterministically characterised, from surviving evidence?**

Scope: no Pine executed, compiled or modified; no frozen artifact altered; no aggregator, no B-3,
no provider substitution. Investigation ran on the isolated layout `P2NtY6fg`; the frozen research
chart `2d43Iesr` was never opened or attached to.

---

## 1. Executive conclusion

## **PARTIALLY RESOLVED**

The **mechanism** is fully resolved — to the bar, for one instrument exactly and the other to
within five 1-minute bars. The **data** is not recoverable.

Specifically:

- The truncation rule is **proven**, not inferred: a trailing window of the most recent **100,000
  LTF bars per requested field**, counted back from the chart's last bar at run time, cut on a
  parent-bar boundary. For MNQ the prediction is exact (delta = 0 bars).
- The set of parent bars that received **empty** LTF arrays is **exactly recoverable** — it is the
  contiguous leading prefix of the chart, and the boundary is recorded in every run file. This
  **overturns the claim made in B-2** that the identity of those bars was unrecoverable.
- The **LTF bar values themselves are not recoverable by any route available today.** TradingView
  no longer serves 1m history before 2026-08-16 or 3m before 2026-07-02, while the research window
  opens 2026-05-24. Folds A and B are beyond reach even with Pine execution permitted.

So B-3 can reproduce *which* parent bars had LTF data, exactly. It cannot reproduce *what* that
data was.

---

## 2. Evidence inventory (P7.1)

24 independent LTF observations, all from committed run files. Every `first`/`last` timestamp is
**UTC** — proven in §3, not assumed.

| inst | dir | fold | LTF | first LTF ts (UTC) | last LTF ts (UTC) | LTFbars | foldbars | w/LTF | w/o LTF | source |
|---|---|---|---|---|---|---|---|---|---|---|
| MGC | L | A | 1m | 2026-05-27 02:15 | 2026-07-15 23:55 | 100000 | 10386 | 9813 | **573** | `trader_v2/v53_runs/MGC_L_1m_A.txt` |
| MGC | L | B | 1m | 2026-07-16 00:00 | 2026-08-07 20:55 | - | 4668 | 4668 | **0** | `trader_v2/v53_runs/MGC_L_1m_B.txt` |
| MGC | L | A | 3m | 2026-05-24 22:00 | 2026-07-15 23:55 | - | 10386 | 10386 | **0** | `trader_v2/v53_runs/MGC_L_3m_A.txt` |
| MGC | L | B | 3m | 2026-07-16 00:00 | 2026-08-07 20:55 | - | 4668 | 4668 | **0** | `trader_v2/v53_runs/MGC_L_3m_B.txt` |
| MGC | S | A | 1m | 2026-05-27 02:15 | 2026-07-15 23:55 | - | 10386 | 9813 | **573** | `trader_v2/v53_runs/MGC_S_1m_A.txt` |
| MGC | S | B | 1m | 2026-07-16 00:00 | 2026-08-07 20:55 | - | 4668 | 4668 | **0** | `trader_v2/v53_runs/MGC_S_1m_B.txt` |
| MGC | S | A | 3m | 2026-05-24 22:00 | 2026-07-15 23:55 | - | 10386 | 10386 | **0** | `trader_v2/v53_runs/MGC_S_3m_A.txt` |
| MGC | S | B | 3m | 2026-07-16 00:00 | 2026-08-07 20:55 | - | 4668 | 4668 | **0** | `trader_v2/v53_runs/MGC_S_3m_B.txt` |
| MNQ | L | A | 1m | 2026-05-27 02:20 | 2026-07-15 23:55 | - | 10368 | 9812 | **556** | `trader_v2/v53_runs/MNQ_L_1m_A.txt` |
| MNQ | L | B | 1m | 2026-07-16 00:00 | 2026-08-07 20:55 | - | 4668 | 4668 | **0** | `trader_v2/v53_runs/MNQ_L_1m_B.txt` |
| MNQ | L | A | 3m | 2026-05-24 22:00 | 2026-07-15 23:55 | - | 10368 | 10368 | **0** | `trader_v2/v53_runs/MNQ_L_3m_A.txt` |
| MNQ | L | B | 3m | 2026-07-16 00:00 | 2026-08-07 20:55 | - | 4668 | 4668 | **0** | `trader_v2/v53_runs/MNQ_L_3m_B.txt` |
| MNQ | S | A | 1m | 2026-05-27 02:20 | 2026-07-15 23:55 | - | 10368 | 9812 | **556** | `trader_v2/v53_runs/MNQ_S_1m_A.txt` |
| MNQ | S | B | 1m | 2026-07-16 00:00 | 2026-08-07 20:55 | - | 4668 | 4668 | **0** | `trader_v2/v53_runs/MNQ_S_1m_B.txt` |
| MNQ | S | A | 3m | 2026-05-24 22:00 | 2026-07-15 23:55 | - | 10368 | 10368 | **0** | `trader_v2/v53_runs/MNQ_S_3m_A.txt` |
| MNQ | S | B | 3m | 2026-07-16 00:00 | 2026-08-07 20:55 | - | 4668 | 4668 | **0** | `trader_v2/v53_runs/MNQ_S_3m_B.txt` |
| MGC | L | C | 1m | 2026-08-09 22:00 | 2026-08-30 23:55 | 100000 | 4164 | 4164 | **0** | `trader_v2/v53_runs_foldc/MGC_L_1m_C.txt` |
| MGC | L | C | 3m | 2026-08-09 22:00 | 2026-08-30 23:55 | 34269 | 4164 | 4164 | **0** | `trader_v2/v53_runs_foldc/MGC_L_3m_C.txt` |
| MGC | S | C | 1m | 2026-08-09 22:00 | 2026-08-30 23:55 | 100000 | 4164 | 4164 | **0** | `trader_v2/v53_runs_foldc/MGC_S_1m_C.txt` |
| MGC | S | C | 3m | 2026-08-09 22:00 | 2026-08-30 23:55 | 34269 | 4164 | 4164 | **0** | `trader_v2/v53_runs_foldc/MGC_S_3m_C.txt` |
| MNQ | L | C | 1m | 2026-08-09 22:00 | 2026-08-30 23:55 | 100000 | 4164 | 4164 | **0** | `trader_v2/v53_runs_foldc/MNQ_L_1m_C.txt` |
| MNQ | L | C | 3m | 2026-08-09 22:00 | 2026-08-30 23:55 | 34239 | 4164 | 4164 | **0** | `trader_v2/v53_runs_foldc/MNQ_L_3m_C.txt` |
| MNQ | S | C | 1m | 2026-08-09 22:00 | 2026-08-30 23:55 | 100000 | 4164 | 4164 | **0** | `trader_v2/v53_runs_foldc/MNQ_S_1m_C.txt` |
| MNQ | S | C | 3m | 2026-08-09 22:00 | 2026-08-30 23:55 | 34239 | 4164 | 4164 | **0** | `trader_v2/v53_runs_foldc/MNQ_S_3m_C.txt` |

`LTFbars` is blank where the captured text file did not include that table row; it is a capture
artifact of the transcription, not a difference in the runs. Where it is present it is consistent
across direction (L/S) for the same instrument/fold/LTF.

**Derived, not observed:** the "w/o LTF" column (`foldbars − w/LTF`). Everything else is direct.

---

## 3. Exact `request.security_lower_tf()` semantics established (P7.2, P7.11)

All from `trader_v2/p15/executed/V53_EXECUTED_BUILD.pine`, read only.

**The request — five separate calls, one per field** (`V53_ltf_sequence.pine:99-103`, identical in
the executed build):

```pine
aO = request.security_lower_tf(syminfo.tickerid, ltfStr, open)
aH = request.security_lower_tf(syminfo.tickerid, ltfStr, high)
aL = request.security_lower_tf(syminfo.tickerid, ltfStr, low)
aC = request.security_lower_tf(syminfo.tickerid, ltfStr, close)
aT = request.security_lower_tf(syminfo.tickerid, ltfStr, time)
```

**The counters** (`V53_EXECUTED_BUILD.pine:299-321`):

```pine
nL = array.size(aC)
if inFold
    array.set(K, 30, array.get(K, 30) + 1)          // foldbars
    if nL > 0
        array.set(K, 29, array.get(K, 29) + 1)      // fold bars w/ LTF
        if covFirst == 0
            covFirst := time
        covLast := time
...
if nL > 0 and not na(atr) and atr > 0               // NOT guarded by inFold
    for k = 0 to nL - 1
        ...
        array.set(K, 31, array.get(K, 31) + 1)      // LTF bars seen
```

| symbol | meaning | grade |
|---|---|---|
| `foldbars` = `K[30]` | parent bars with `inFold` true | **VERIFIED** from source |
| `w/LTF` = `K[29]` | in-fold parent bars where `array.size(aC) > 0` | **VERIFIED** |
| `LTFbars` = `K[31]` | **one increment per LTF array element, over ALL chart bars — not fold-scoped** — additionally gated by `not na(atr) and atr > 0` | **VERIFIED**; the `inFold` indentation ends before this block |
| `cov` first/last | `time` of the first/last in-fold parent bar with `nL > 0` | **VERIFIED** |
| `cov` timezone | **UTC** — `ft(t) => str.format_time(t, "yyyy-MM-dd HH:mm", "UTC")` (line 169) | **VERIFIED** |

`K[31]` being chart-wide, not fold-wide, is the single most load-bearing semantic finding here. It
is why fold C reports `LTFbars 100000` while showing **zero** truncated parent bars: the 100,000 is
a whole-chart total, and fold C simply sits entirely inside the surviving window.

### P7.11 — the cap applies per field, not per tuple

**VERIFIED.** Five fields are requested. If the 100,000 budget were shared across the tuple, each
field would top out near 20,000 elements. Observed instead: `aC` alone yielded **exactly 100,000**
elements at 1m, and **34,239–34,269** at 3m. A 3m count above 20,000 is by itself sufficient to
reject the shared-budget reading. The cap is **100,000 lower-timeframe bars per requested series**.

---

## 4. The 100,000 cap (P7.2, P7.5)

### Measurements

Taken on the isolated layout, read-only, over the reconstructed run-time chart extent
`[2026-05-24 22:00Z .. 2026-09-04 20:55Z]`:

| | MGC | MNQ |
|---|---|---|
| parent bars before the cut | 573 | 556 |
| parent bars from the cut to run-time end | **20,001** | **20,000** |
| implied 1m bars at 5 per parent | 100,005 | **100,000** |
| delta from the 100,000 cap | **+5** | **0** |

**MNQ matches exactly.** 20,000 parent bars × 5 one-minute bars = 100,000, ending on the last bar
before the weekend.

### 1m density is not assumed — it was measured

Over the loaded 1m range, 5-minute slots partitioned by bar count: **4,265 slots with exactly 5
bars, 1 slot with 3** (the live forming slot). The ×5 relation is therefore measured, not posited,
at least over the range TradingView still serves.

### Independent confirmation from the 3m runs

`K[31]` is chart-wide and ATR-gated, and 3m tiles a 5m parent at 5/3. Predicting the fold-C 3m
figures from the chart extent derived above:

| | total 5m bars | less ATR(14) warmup (13) | predicted 3m (×5/3) | **observed** | delta |
|---|---|---|---|---|---|
| MGC | 20,574 | 20,561 | 34,268.33 | **34,269** | 0.67 |
| MNQ | 20,556 | 20,543 | 34,238.33 | **34,239** | 0.67 |

Both within one bar, from a completely independent quantity. This simultaneously confirms the
`K[31]` semantics, the 5/3 tiling, the ATR gate, and the run-time chart extent.

### Run-time chart end recovered

**2026-09-04 20:55 UTC** — the Friday close. `PHASE16_PROTOCOL.md:81` records the Phase 15 runs
executing on **2026-09-06**, a Sunday, before the 22:00 reopen; `:89` independently records that
`2026-08-31 00:00 → 2026-09-04 20:55 UTC (~4.87 days, 5 sessions)` had elapsed at protocol time.
The count-back derivation predicted 4.91 trade days of post-FE data. The measured post-FE parent
count is **1,356** for both instruments. Three independent routes agree.

### Hypothesis discrimination (P7.5)

| hypothesis | verdict |
|---|---|
| **A — trailing 100,000-LTF-bar window per chart/request, cut at a parent boundary** | **SUPPORTED, exact for MNQ.** Adopted |
| B — 100,000 allocated independently per call | Indistinguishable from A here: all five fields share one resolution and one symbol. **Not discriminated**, and not needed |
| C — 100,000 shared across multiple LTF requests | **REJECTED** — 3m delivered 34,239 on `aC` alone; a shared budget across 5 fields would cap each near 20,000 |
| D — cap tied to visible/loaded parent bars | **REJECTED** — fold B and fold C runs loaded the same chart and show no truncation; the cut sits at a fixed calendar point regardless of fold |
| E — cap depends on LTF resolution and tuple width | **PARTIALLY REJECTED** — the cap is the same 100,000 at 1m and 3m; 3m is simply under it. No tuple-width dependence (see P7.11) |
| F — cap affected by chart resolution / paging | **NOT TESTED.** All runs were 5m-parent. Would require a differing-resolution run, which needs Pine |
| G — other | No residual evidence calls for one |

**The `+5` residual on MGC.** Under hypothesis A the cut must land exactly on the 02:15 parent
boundary, which requires MGC's window to hold exactly 100,000 1m bars rather than 100,005 — i.e.
**exactly five minutes with no trades** somewhere in `[2026-05-27 02:15, 2026-09-04 20:55]`. Gold's
overnight book is thin enough to make that unremarkable, and MNQ's exact match shows the rule
itself is not approximate. **This is INFERRED, not verified** — verifying it needs 1m history for
the window, which TradingView no longer serves (§7).

---

## 5. Parent-bar grouping and the 573 (P7.7) — **exactly recoverable**

Testing the recorded `cov`-first timestamp against the frozen parent series:

| instrument | `cov`-first (UTC) | 0-based index in frozen fold A | run-file `foldbars − w/LTF` | match |
|---|---|---|---|---|
| MGC | 2026-05-27 02:15 | **573** | **573** | **exact** |
| MNQ | 2026-05-27 02:20 | **556** | **556** | **exact** |

The index of the first LTF-bearing parent bar equals the count of LTF-less parent bars, for both
instruments. That is only possible if the LTF-less bars are a **contiguous leading prefix** — no
scattering, no interior holes.

**Therefore the set is exactly recoverable**, by a criterion that involves no estimation:

```
parent bars without LTF = { b in fold : b.timestamp < cov_first }
```

`cov_first` is recorded in the PERF line of every run file, in UTC, and the parent series is frozen
and hashed. Both inputs are committed evidence.

> **Correction to B-2.** The B-2 documentation and commit message state that "which 573 is not
> recoverable from a bar series". That is **wrong** and is withdrawn. It is recoverable — not from
> the bar series alone, but from the bar series **plus the recorded `cov` boundary**, which was
> sitting in the run files the whole time. B-2's conclusion that the LTF *values* are unavailable
> stands; its claim about the *mask* does not.

---

## 6. Fold-A boundaries and the 02:15 / 02:20 difference (P7.6)

**MGC fold A: `2026-05-27 02:15` UTC. MNQ fold A: `2026-05-27 02:20` UTC.** Both directly recorded
in four run files each (L and S); timezone proven from `ft()` in §3.

Two distinct differences must be explained, and they have different causes.

**(a) The index gap of 17 (573 vs 556) — RESOLVED.** Comparing the two frozen parent series over
the *identical* leading window `[start, 2026-05-27 02:15)`:

- MGC holds **573** parent bars; MNQ holds **555**.
- Exactly **18** timestamps are present in MGC and absent from MNQ; **zero** are present in MNQ and
  absent from MGC.
- Those 18 are contiguous: **2026-05-25 17:00 → 18:25 UTC**.

2026-05-25 was **Memorial Day**. COMEX gold traded that segment; the CME equity-index contract did
not. The 18-bar holiday-session difference shifts MGC's *index* without meaningfully shifting its
*clock time*. (The symbol record's own `corrections` string, recovered in P-6, carries a
holiday entry for that period, consistent with this.)

**(b) The 5-minute clock gap (one 5m slot) — INFERRED.** After the cut, fold A retains **9,813**
parent bars for MGC and **9,812** for MNQ — matching `w/LTF` in the run files exactly. The
one-slot offset is the residual of the 100,000-bar count-back landing marginally differently in the
two series, and it is the same `+5` residual discussed in §4. Confirming it requires 1m history
that is no longer served. **Not claimed as resolved.**

---

## 7. TradingView internal investigation (P7.3, P7.4, P7.10, P7.12)

### No lower-TF request state exists outside Pine — **VERIFIED negative**

A recursive walk of `model()` and `window.TradingViewApi` to depth 5 (2,085 objects) for property
names matching
`intrabar|lowertf|lower_tf|lowerTf|security_lower|maxIntrabar|intrabars|max_bars|maxBars|barsLimit|historyLimit|requestLimit|tupleWidth`
returned **zero hits**. The 53-key `mainSeries().symbolInfo()` record recovered in P-6 likewise
carries no intrabar or request-limit field.

This is a real negative, and it makes sense: `request.security_lower_tf` state is created by a
running Pine study. With no study on the chart, there is nothing to inspect. P-6 found
`RollDatesCalculator` because TradingView instantiates it for continuous-contract rendering; there
is no analogous always-on object for lower-timeframe requests.

| object path | searched for | result |
|---|---|---|
| `model()` (depth 5, 2,085 objects) | 13 intrabar/limit patterns | none |
| `window.TradingViewApi` (depth 5) | same | none |
| `mainSeries().symbolInfo()` (53 keys, P-6) | intrabar / request limit fields | none |
| `mainSeries()._seriesSource` prototype (P-6) | `requestMoreTickmarks`, `setFutureTickmarksMode` only | nothing LTF-related |

### Intraday history depth — **the decisive finding (P7.10)**

Measured by paging each resolution to exhaustion on `COMEX_MINI_DL:MGC1!`:

| resolution | oldest bar served | bars | covers |
|---|---|---|---|
| **5m** | 2026-05-24 22:00 | 20,700 | **the whole research window** |
| **3m** | 2026-07-02 22:00 | 21,291 | folds B and C only |
| **1m** | 2026-08-16 22:00 | 21,332 | part of fold C only |

TradingView serves roughly **21,000 intraday bars per resolution** — a **bar-count** limit, not a
time limit. The research window opens 2026-05-24 22:00.

**Consequences, stated plainly:**

1. **The 1m LTF values for folds A and B cannot be obtained from TradingView today by any route.**
   Not by chart export, not by Pine — the underlying history is no longer served at that
   resolution.
2. The 3m values for fold A are likewise unavailable; folds B and C are within reach.
3. At run time on 2026-09-06, `request.security_lower_tf` reached back to 2026-05-27 — 100,000 1m
   bars. The 1m *chart* path today reaches 21,332. Either the LTF request path carries a much
   larger history allowance than the chart path, or that history has since aged out. **Which of the
   two is UNKNOWN**, and it cannot be settled without executing Pine.
4. A raw 1m chart export was never equivalent to the LTF stream, and is now not even a superset.

### P7.12 — resolution dependence

**Not tested, deliberately.** Every frozen run used a 5m parent. Testing whether the cap moves with
chart resolution requires running a Pine study at another resolution, which is forbidden here. The
frozen chart was not touched; all paging above ran on `P2NtY6fg`.

---

## 8. Candidate reconstruction models (P7.8, P7.9)

Every model below was tested against all 24 observations, not one.

### Model 1 — availability mask from the recorded `cov` boundary

*Assumption:* none beyond the run files and the frozen parent series.
*Predicts:* LTF-less parent bars = `{ b in fold : b.timestamp < cov_first }`.
*Explains:* MGC 573 and MNQ 556 exactly; fold B and fold C zero-truncation (their `cov_first`
equals their fold start); 3m fold A zero-truncation (`cov_first` = 2026-05-24 22:00 = chart start).
All 24 observations.
*Contradicts:* nothing.
**Status: PROVEN.** This is the component B-3 may rely on.

### Model 2 — trailing 100,000-bar cap counted back from the run-time chart end

*Assumption:* the run-time chart ended at the last bar before the Sunday reopen.
*Predicts:* cut leaves exactly 100,000 LTF bars.
*Explains:* MNQ exactly (20,000 × 5 = 100,000, delta 0); MGC to +5; both 3m `LTFbars` figures to
0.67 bar; the post-FE extent (1,356 parents) against the protocol's independently recorded 4.87
days.
*Contradicts:* nothing, though MGC's +5 is unverified.
**Status: PROVEN for MNQ, INFERRED for MGC.** Useful as explanation. **B-3 does not need it** —
Model 1 supplies the mask directly, without predicting the cut.

### Model 3 — reconstruct LTF values from a 1m chart export

*Predicts:* nothing; it is a data-substitution proposal.
*Fails:* the data does not exist to export (§7). Folds A and B are unreachable. Even for fold C it
would be a different object — no cap behaviour, and per-parent grouping would have to be
manufactured by aggregation, which is forbidden and would not be evidence.
**Status: REJECTED on evidence**, not merely on scope.

### Model 4 — infer the missing set from the cap arithmetic instead of `cov`

*Predicts:* the cut position from bar counts.
*Fails:* would give MGC 20,000 parents (cut at 02:20) against the recorded 02:15 — off by one
parent bar. Model 1 gets it exactly right.
**Status: REJECTED.** A worked example of why the recorded boundary must be preferred over a
derived one.

---

## 9. Exact recoverability assessment (P7.11)

| question | answer | grade |
|---|---|---|
| Can the 573 / 556 LTF-less parent bars be identified exactly? | **YES** — leading prefix, criterion in §5 | **PROVEN** |
| Can the count of LTF bars per parent be recovered for the research window? | **NO** — needs 1m/3m history that is no longer served | **UNKNOWN** |
| Can the LTF OHLC values be recovered? | **NO** — same reason | **UNKNOWN** |
| Can the truncation rule be stated? | **YES** — §4 Model 2 | PROVEN (MNQ) / INFERRED (MGC) |
| Is the rule needed to reproduce the research? | **NO** — the boundary is recorded per run | **PROVEN** |

---

## 10. B-3 readiness (P7.12)

**NOT READY for exact LTF reproduction. READY for exact availability-mask reproduction.**

**B-3 may:**
- treat the LTF availability mask as settled and derive it from `cov_first` per run, using the
  criterion in §5, citing the run files and the frozen parent series;
- rely on `LTFbars`/`w/LTF`/`foldbars` semantics as established in §3;
- use 100,000-bars-per-field as the cap semantics;
- treat 2026-09-04 20:55 UTC as the run-time chart extent.

**B-3 may not:**
- claim to reproduce the LTF bar values for folds A or B — the data is gone from TradingView;
- synthesise, aggregate or interpolate LTF bars to fill the gap;
- substitute a 1m chart export or a provider series for the LTF stream and call it parity;
- assume every parent bar received exactly 5 (or 5/3) LTF bars in the research window — measured
  only over the range TradingView still serves;
- assume the MGC `+5` residual is explained until 1m history for the window is obtained.

**The honest framing for Gate 1:** parity against the frozen research on the 1m LTF path cannot be
demonstrated bar-for-bar, because the inputs no longer exist. What *can* be demonstrated is parity
of the parent path plus correct reproduction of LTF availability. Whether that is sufficient for
Gate 1 is a decision for the study owner, not something to be assumed away here.

---

## 11. Unknowns after P-7

| # | unknown | change |
|---|---|---|
| **U-14** | the exact LTF stream V53 consumed | **NARROWED, not closed.** The availability mask is now PROVEN recoverable; the bar values are now PROVEN *un*recoverable from TradingView (§7), which is a stronger negative than B-2 recorded |
| **U-15** | *new* — whether `request.security_lower_tf` carries a deeper history allowance than the chart path, or whether the 2026-05-27 data has simply aged out | undecidable without executing Pine |
| **U-16** | *new* — the exact per-parent LTF bar counts in the research window (the MGC `+5` residual) | needs 1m history for 2026-05-27 → 2026-08-16, which is not served |
| **U-17** | *new* — whether the 100,000 cap varies with chart resolution (hypothesis F) | untested; needs a Pine run at another parent resolution |
| U-5, U-7, U-9, U-12, U-13 | carried forward from P-6 / B-2 | unchanged |

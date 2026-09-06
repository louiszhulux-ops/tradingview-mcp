# Phase 13E — V53: first implementation of the frozen hypothesis, and its mechanical audit

Implementation plus **mechanical audit only**. No A/B/C performance test was run,
nothing was optimised, no frozen value was changed, no definition was ranked by
profitability, and no existing strategy file was modified. The word "expectancy"
does not appear in any number below; the only outputs are event counts,
conversion rates and leakage assertions.

Build: `trader_v2/V53_ltf_sequence.pine`.

---

## 1. What was built

The V49 5m sweep engine, unchanged, plus an LTF layer consulted between arming
and entry, running on the same 5m chart through `request.security_lower_tf`.

```
SWEEP -> CHOCH -> CHOCH RETEST -> BOS/DISPLACEMENT -> BOS FVG RETEST -> ENTRY
 (5m)     (LTF)       (LTF)            (LTF)              (5m)          (5m)
```

Seven-state machine per candidate: `0 free | 1 armed | 2 CHOCH | 3 retested |
4 BOS, awaiting the d+1 bar | 5 FVG found, awaiting the 5m fill | 6 in trade`.
Loop order inside the script is outcome → fill → deadline → LTF → arm, which
reproduces V49's ordering exactly (a fill on bar `t` is first judged on `t+1`,
and a sweep armed on bar `b` never sees bar `b`'s own LTF constituents).

### One implementation decision, flagged rather than buried

V49 emits up to **three** candidates on one sweep bar — previous-day, Asia and
pivot — because in V49 the *entry level is the swept level*, so the three differ.
In this hypothesis the entry is the **FVG far edge**, and the stop is the sweep
extreme, so all three would share an identical sweep bar, identical stop,
identical LTF stream, identical CHOCH, identical BOS, identical FVG and identical
entry. Running them as three candidates would emit the same trade three times.

So V53 arms **one sequence per sweep bar**. The sweep *detection* is untouched
(the same `nHit > 0` test on the same three level families); only the fan-out is
collapsed, because the thing it used to fan out over no longer varies. This is
arithmetic rather than a behavioural choice, but it is a departure from V49's
candidate count and is recorded here rather than left to be discovered.

---

## 2. The one place the implementation forced a correction

The frozen §4 method is `ta.pivothigh/low(src, swLen, swLen)`. That function
cannot be applied to an LTF array, so the rule has to be **reimplemented** for
the LTF stream — and a reimplementation that is not bit-identical to the frozen
method is a silent change to the specification.

The first build used the obvious rule, strictly greater than all neighbours on
both sides. Running it on the 5m chart series against `ta.pivothigh/low(high,3,3)`
gave **180 mismatches in 20,567 bars** — the assertion the audit exists to catch.

Rather than adjust anything, the three candidate rules were measured directly:

| rule | mismatches vs `ta.pivothigh/low(src,3,3)` |
|---|---|
| strict left, strict right | **180** (all 180 = TradingView reports a pivot, the rule does not; all 180 involve a tie) |
| strict left, non-strict right | **370** |
| **non-strict left, strict right** | **0** |

`ta.pivothigh/low` is **≥ on the left and > on the right**: the **first** bar of a
run of equal extremes is the pivot. 2,943 of 20,567 bars carry a tie somewhere in
the 7-bar window, so on this data the distinction is not academic.

The LTF detector now uses that rule and reproduces the frozen method with **0
mismatches over 20,567 chart bars and 3,912 TradingView pivots**. This is a
correctness fix that makes the reimplementation match the frozen definition — not
a parameter change, and not a choice between behaviours.

---

## 3. Mechanical audit — the eighteen required checks

Eight cells were run on folds A+B: MGC1! and MNQ1!, long and short, 1m and 3m.
Every assertion below is **0 in all eight cells**.

| # | check | how it was verified | result |
|---|---|---|---|
| 1 | sweep detection unchanged | textual diff of the 51-line sweep block against `V49_multi_level_ledger.pine`, plus all nine frozen constants compared | **byte-identical** |
| 2 | LTF pivot confirmation is causal | the same detector run on the 5m series vs `ta.pivothigh/low`; value equals `src[3]` at confirmation | **A26 = 0, A27 = 0** over 20,567 bars |
| 3 | CHOCH uses only eligible post-sweep pivots | counter fires if the reference's pivot **bar** is at or before the sweep bar | **A21 = 0** |
| 4 | CHOCH reference rolls | roll counter increments when the active reference changes | 295–1,287 rolls per cell — the reference is live, not latched |
| 5 | CHOCH requires a close through | wick-through-without-close counted separately and never fires CHOCH | 241–759 wick-only events per cell, 0 became a CHOCH |
| 6 | retest is the exact level, zero tolerance | near-miss counter: within 0.01×ATR of the level but not touching | **0–17 near misses, none counted as a retest** |
| 7 | retest occurs before BOS | assertion on `retestBar < bosBar` | **A23 = 0** |
| 8 | BOS is the displacement candle | assertion that the ring index of the BOS bar equals the recorded displacement bar | **A24 = 0** |
| 9 | BOS excludes the CHOCH pivot | assertion on `bosPivotIdx != chochPivotIdx`; falls back to the previous confirmed pivot when they coincide | **A22 = 0** |
| 10 | BOS needs break **and** §7 displacement | breaks that failed displacement counted separately | 195–3,773 per cell rejected — the conjunction binds hard (§4) |
| 11 | FVG uniquely associated with the displacement candle | evaluated exactly once, at LTF bar `d+1`, on ring indices `d−1, d, d+1` | 1 test per BOS, by construction |
| 12 | no-FVG displacement invalidates | invalidation counter | 0–14 per cell, no fallback path exists in the code |
| 13 | FVG retest uses the §12 fill condition | `low <= E` / `high >= E`, `retBars = 24` chart bars | as V49, verbatim |
| 14 | entry uses the FVG far edge | `E = high[d−1]` (bull) / `low[d−1]` (bear) | by construction |
| 15 | stop is V49 unchanged | `isLong ? low − 0.20×atr : high + 0.20×atr` at the sweep bar | line-identical to V49 |
| 16 | outcome starts the bar after the fill | outcome loop precedes the fill loop, as in V49 | **A25 = 0** |
| 17 | no lookahead / future information | grep: **no `request.security(`, no `lookahead` of any kind** in the script; only `request.security_lower_tf` | confirmed |
| 18 | 1m and 3m evaluated independently | separate runs, never pooled; coverage reported per run | see §4 |

Two further assertions were added while building and also hold everywhere:
**A32 = 0** (no CHOCH fires on a reference's own confirmation bar — geometrically
impossible, and confirmed empirically) and **D33 = D34 = D35 = 0** (the pivot
detector agrees with TradingView in both directions, including on ties).

---

## 4. The conversion funnel — folds A+B, eight cells

Counts only. No R, no win rate, no expectancy.

| cell | sweeps | CHOCH | retest | BOS+disp | FVG | **fills** | breaks rejected by displacement |
|---|---|---|---|---|---|---|---|
| MGC long 1m  | 705 | 583 | 532 | 8  | 7  | **3**  | 2,631 |
| MGC short 1m | 658 | 585 | 532 | 11 | 11 | **4**  | 3,390 |
| MGC long 3m  | 705 | 272 | 201 | 13 | 10 | **5**  | 195 |
| MGC short 3m | 658 | 253 | 203 | 19 | 12 | **1**  | 262 |
| MNQ long 1m  | 743 | 642 | 584 | 30 | 20 | **9**  | 3,773 |
| MNQ short 1m | 871 | 737 | 647 | 33 | 19 | **12** | 3,571 |
| MNQ long 3m  | 743 | 288 | 206 | 14 | 6  | **1**  | 374 |
| MNQ short 3m | 871 | 316 | 241 | 11 | 8  | **5**  | 278 |

Stage-to-stage conversion, pooled by LTF:

| step | 1m | 3m |
|---|---|---|
| sweep → CHOCH | 86% | 39% |
| CHOCH → retest | 91% | 73% |
| retest → BOS+displacement | **3.5%** | **7.0%** |
| BOS → FVG exists | 71% | 63% |
| FVG → fill | 51% | 36% |
| **sweep → fill** | **0.96%** | **0.41%** |

Capacity was never the constraint: 0 candidates dropped in any cell, observed max
concurrency 6–9 against 24 slots.

**Coverage by timestamp**, as required: on 1m, 14,480–14,481 of ~15,045 fold bars
carry LTF data (96.2%) — the 100,000-value window starts 2026-05-27 and the folds
start at the chart's own history start. On 3m, coverage is **100%** of fold bars
in every cell. No data was extended or substituted; the 1m runs are reported on
96.2% of the fold and are labelled as such.

---

## 5. What the funnel says, mechanically

**The specification implements cleanly and causally. It also produces 1 to 12
completed trades per cell over roughly ten and a half weeks.** Both facts are
findings; only the first was in doubt.

The binding constraint is unambiguous and was predicted in Phase 13D §5.1: the
§7 displacement condition applied to an **LTF** candle against the **5m** ATR.
On 1m, 3,571 structural breaks satisfied the BOS break test and failed
displacement, against 33 that passed — a **0.9%** pass rate. On 3m the same gate
passes about 4%. A 1-minute candle whose range exceeds 1.5× the 5-minute ATR is
rare by construction, which is exactly what F6 freezes.

The second constraint is the 60-minute deadline: 554–614 sequences per 1m cell
reached the CHOCH retest and then expired waiting for a displacement-qualifying
BOS. On 3m the losses move earlier — 405–555 expire before a CHOCH at all,
because `swLen = 3` on 3m consumes 7 of the available 20 bars confirming the
first pivot, as Phase 13D §5.2 anticipated.

Note the two LTFs fail in *different* places: 1m produces plenty of structure and
almost no displacement; 3m produces displacement more readily but often runs out
of clock before the structure exists. They are not a coarse and fine version of
one result, which is a further reason to keep H1 and H2 separate.

**No frozen value was touched in response to any of this**, and none should be
without a decision from you. Widening displacement, lengthening the deadline or
shrinking `swLen` would each raise the trade count, and each would be an
optimisation performed after seeing the funnel — the specific thing the
integrity rule forbids.

---

## 6. Status

Implementation complete, all eighteen mechanical checks pass, one reimplementation
defect found and corrected against ground truth before it could reach a result.

**STOPPED here, as instructed.** No A/B/C performance testing, no ranking of 1m
against 3m, no optimisation.

The one thing worth deciding before the controlled experiment on folds A+B: at
the frozen parameters the per-cell sample is 1–12 fills, which is smaller than
anything this project has previously called measurable. That is a fact about the
frozen hypothesis, not an argument for changing it — but the performance phase
should be entered knowing that its answer will be dominated by sampling noise
unless the cell set is widened (more instruments, both directions pooled) or the
sample is accepted as descriptive rather than inferential.

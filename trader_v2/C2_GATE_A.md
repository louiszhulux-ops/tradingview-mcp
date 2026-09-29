# Phase 11 C2 — Gate A: **PASS**. Gate B: **blocked on a spec ambiguity.**

V51 = V49 plus C2 maturity attributes. Entry/exit mechanics, sweep detection,
stop, retest window, R cap, 24 slots and cascade removal byte-identical to V49.
Nothing gates on maturity. `showPerf` off — **no expectancy was computed or
displayed at any point in this run.**

---

## Gate A

### Exact definitions used, taken verbatim from the frozen spec

`bornBar` = the bar the level became **known**; `ageBars = bar_index − bornBar`;
`touches` = count of **bars** since `bornBar` and **strictly before** the arm bar
where `min(|high−L|, |low−L|) ≤ 0.10 × ATR`; `virgin = (touches == 0)`.

**Touch definition — every question answered by the frozen text, none invented:**

| question | answer | where the spec settles it |
|---|---|---|
| does a wick count | **yes** | the test uses `high` and `low` |
| does a close count | **not separately** | `close` does not appear in the formula |
| does the sweep itself count | **no** | "strictly before the arm bar"; the sweep bar *is* the arm bar |
| does the retest count | **no** | the value is frozen at the arm bar; the retest is later |
| multiple touches on one bar | **once** | "count of **bars** … where" |
| simultaneous levels | **independent state per level** | "for every reference level L, maintain …" |
| equal-price touches | **counted** | the test is `≤`, so `\|high−L\| = 0` qualifies |
| closed bars only | **yes** | all bars strictly before the arm bar are closed |

**Age definition:** unit = bars; start = `bornBar`; freeze = arm bar; the arm bar
is included in the difference (a level born on the arm bar has `age = 0`); newly
created levels get `age = 0, touches = 0`; a level with unknown `bornBar` records
`na` and is excluded.

**One interpretive call, disclosed.** The spec writes `0.10 × ATR` without saying
*which* ATR. I used the ATR **at each touch bar**, because the spec's verb is
"maintain" — a running counter — and that is the causal reading. The alternative
(re-scanning history with the arm-bar ATR) would give a different count. This was
fixed before any measurement and is not a post-hoc choice.

### Temporal / leakage proof

`bornBar` for pivots is the **confirmation** bar. Proof, not assertion: at every
bar where `ta.pivotlow(low, swLen, swLen)` returns non-`na`, V51 checks that the
returned value equals `low[swLen]`. **0 mismatches in 7,454 candidates** — the
pivot value is the extreme from exactly `swLen` bars back, so confirmation lag is
exactly `swLen` and age runs from confirmation.

Per-bar ordering, which is what makes Tests 1–5 hold structurally:

1. birth detection — a changed level value resets `bornBar` and zeroes `touches`;
2. **snapshot** `snapT[k] = touches[k]` — the value "strictly before the arm bar";
3. this bar's touch test runs and may increment `touches[k]`;
4. sweep detection and arming use **`snapT[k]`**, never the live counter.

Because step 2 precedes step 3, the arm bar can never contribute to its own
candidate's count, and bars inside a pivot's formation window are counted against
the *previous* level, never the new one — the new level's counter does not exist
until its confirmation bar.

| diagnostic | total | verdict |
|---|---|---|
| D0 touch credited before birth | **0** | PASS |
| D1 arm used the post-update counter | **0** | PASS |
| D2 stored maturity mutated between arm and record | **0** | PASS |
| D3 candidates excluded (`na` level/birth) | **0** | PASS |
| D4 pivot confirmation-lag mismatch | **0** | PASS |

**Positive tests (non-vacuous):**

- **T4** — 83 arm bars *did themselves* satisfy the touch test, meaning the live
  counter was `snapshot + 1` at arm time. In all 83 the stored value was the
  snapshot (D1 = 0). The exclusion is exercised, not merely asserted.
  *Note on why only 83:* the sweep condition requires the wick to travel ≥ 0.10 ATR
  **beyond** the level, and the touch tolerance is ≤ 0.10 ATR **from** it, so a
  sweep bar usually falls outside the touch band by construction. This is a
  consequence of the two frozen constants being equal, not a defect.
- **T6** — 504 bars swept more than one level; **414 of them (82%) produced
  candidates with different maturity values.** Per-level state is genuinely
  independent, with no cross-contamination.
- **T1/T2/T3** are structural consequences of the ordering above and of D0 = 0 and
  D4 = 0, verified across 7,454 candidates rather than on a synthetic chart.
  A synthetic bar series cannot be constructed inside Pine, so the audit was run
  as invariant assertions over the real data instead. That is a weaker form of
  Tests 1–3 than a hand-built fixture and is reported as such.

### Reconciliation

| | V51 | V49/V50 reference |
|---|---|---|
| candidates | **7,454** | 7,454 |
| fills | **6,658** | 6,658 |
| sweepBars / expired / rejR, all ten cells | identical | identical |
| drop24 | 0 | 0 |

All ten cells match exactly on candidates, fills, sweep bars, expiries and R-cap
rejections. Every fill carries exactly one maturity record and exactly one level
type (touch buckets sum to fills; type counts sum to fills, in every cell). No
candidate was added or removed, no entry/exit behaviour changed, no room, bias or
VWAP logic touched.

### Distributions (counts only — required by the spec before deciding testability)

| touches | 0 | 1 | 2 | 3+ |
|---|---|---|---|---|
| fills | 1,994 (29.9%) | 1,442 (21.7%) | 866 (13.0%) | 2,356 (35.4%) |

| level type | fills | virgin | % virgin |
|---|---|---|---|
| prev-day | 1,278 | 257 | 20.1% |
| **Asia** | 1,623 | **0** | **0.0%** |
| pivot | 3,757 | 1,737 | 46.2% |

`ageBars`: min 0, max 489, fill-weighted mean 66.0.

The spec said *"`virgin` may be a small minority; count it before deciding whether
it is testable at all."* Counted: **29.9% of fills, 1,994 observations.** It is
comfortably testable.

### A definitional finding that must not be glossed

**No Asia-level candidate is ever virgin — 0 of 1,623.** This is structural, not
random. `asiaH`/`asiaL` are maintained as a *running* extreme, so `bornBar` lands
on the last bar that moved the extreme, and the remaining Asia bars sitting at or
near it are then counted as touches. For Asia levels `touches` therefore measures
**the shape of the Asia session's own extreme**, not later market interaction —
semantically a different quantity from what it measures for pivots and prev-day
levels.

It is causal and leak-free, so it does not fail Gate A. But it is precisely the
V44/V48 failure mode in miniature: a feature quietly measuring something other
than the thing it is named after. The frozen spec already requires stratification
by level type, which contains it; any Gate B design must honour that, and should
consider whether Asia levels belong in the primary comparison at all.

### **GATE A: PASS**

---

## Gate B — not run

The frozen C2 specification does **not** define a primary comparison or a gate.
Its threshold section reads, in full:

> **Thresholds** none — report the distribution of `touches` (0, 1, 2, 3+) and
> `ageBars` deciles.

C2 was scoped in Phase 10 as **descriptive**, not as a hypothesis test. The generic
gate supplied for this phase requires "a 90% CI excluding zero for the primary
comparison specified in PHASE10_FEATURE_MAP.md" — and no such comparison is
specified there.

The standing instruction covers this exactly: *"If no predefined comparison
exists, STOP before performance and report the ambiguity rather than inventing
one after seeing the data."*

So I have stopped, and **no expectancy has been computed.**

`virgin` (touches == 0) is the only *comparison* the spec names — everything else
in C2 is a distribution. It is the direct encoding of the "unmitigated" concept
C2 was built on, and it is now known to be testable at 29.9% / 1,994 fills. It is
the obvious candidate for a primary comparison. **But choosing it now, after
seeing the distributions, would be exactly the post-hoc selection this phase
exists to prevent** — so it is proposed, not adopted.

## Final status

**C2 GATE A PASSED — Gate B blocked: the frozen specification defines no primary
comparison, so no pre-registered gate can be evaluated without inventing one after
the fact.**

To proceed, one decision is needed from you, made before any expectancy is
computed: pre-register the primary comparison. The natural one is
**virgin (touches == 0) vs non-virgin**, stratified by level type, with the gate
already stated for this phase (90% CI on the difference excluding zero, and the
same directional relationship in ≥ 7/10 cells) — plus an explicit ruling on
whether Asia levels are included, given the finding above.

No further research run until that is fixed.

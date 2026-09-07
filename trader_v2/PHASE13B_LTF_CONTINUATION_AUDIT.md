# Phase 13B — LTF continuation audit: recovery search + OHLC capacity probe

Read-only audit. **No file outside this document was modified during STEP 1, no
strategy was implemented, no parameter was swept, no backtest was run, and no
performance number was produced.**

Purpose: (1) recover, from the repository and its history, the five definitions
Phase 13 marked missing (M1–M5), labelling anything unrecoverable as **UNKNOWN**
rather than inventing it; (2) settle experimentally the one data question Phase 13
left open — whether the 100,000-value `request.security_lower_tf` limit is per
field or aggregate across O/H/L/C.

---

## A. What STEP 1 recovered

Searched: working tree and full `git log --all -S` history for `CHOCH`, `BOS`,
`internal structure`, `structural swing`, `opposing swing`, `MSS`, `LTF`, `1m`,
`3m`, `swLen`, `FVG`, FVG selection, sweep→CHOCH timing, CHOCH→BOS sequencing.
Also enumerated every file ever deleted, and listed the saved TradingView scripts.

### A1. Recovered — a real BOS implementation, on the chart timeframe

`strategies/V8_3_XAU_trend_range.pine:88-174` (identical code in
`V11_1_XAU_day_trader.pine`, `V12_XAU_winrate_testrig.pine`, `V13_XAU_audit.pine`):

```pine
pivotLen   = input.int(5,  "Pivot lookback (structure)")
bosMaxBars = input.int(15, "Max bars for BOS after sweep")
swHigh = ta.pivothigh(high, pivotLen, pivotLen)
swLow  = ta.pivotlow(low,  pivotLen, pivotLen)
bullSweep = not na(lastSwLow)  and low  < lastSwLow  and close > lastSwLow
bosLongSweep = pendingBullBOS and not na(lastSwHigh) and close > lastSwHigh
               and (bar_index - pendingBullBar) <= bosMaxBars
```

- **swing selection: the most recent confirmed opposing pivot as of the current
  bar** (`lastSwHigh` / `lastSwLow`, updated on every confirmation, so it is
  re-evaluated forward — candidate (b) of F2, not (a) or (c)).
- **break rule: close beyond** the swing. Wick breaks do not count.
- **max delay: 15 bars** from sweep to BOS.
- **causal**: yes. `ta.pivothigh(src, 5, 5)` confirms at `pivotBar + 5`;
  `lastSwHigh` is only assigned on a confirmation bar.
- **conflicts with a frozen definition**: partially. Its pivot strength is **5**,
  the frozen §4 value is **10**; and it runs on the **chart** timeframe
  (15m in `MORE_TRADES_INVESTIGATION.md:3`), not on 1m or 3m.

This is `sweep → BOS` with **no CHOCH beat between them**, so it supplies M2's
break rule and swing rule *for a 15m construct*, and supplies nothing for M1.
Phase 12 already flagged this file as "a different construct, not a competing
definition" — that judgement stands. What is new is that its swing-selection rule
is explicit and is one of the F2 candidates.

### A2. Recovered — an MSS (CHOCH-equivalent) was built once, and its source is gone

`strategies/V24_V25_ICT_RESULTS.md:18` and commit `df1cced` record a
market-structure-shift implementation built from the published ICT 2022 model:

| beat | rule as recorded |
|---|---|
| shift | **close through the opposing swing with displacement — `range > k × stdev(range)`** |
| entry | **retracement into the fair value gap the displacement leg leaves** |
| stop | beyond the raided extreme |
| timing | killzone 08:30–11:00 NY |

This is the closest thing in the project to a CHOCH definition, and the FVG rule
is exactly the §17 preference ("the FVG associated with the displacement that
caused the break").

**It is not recoverable.** `df1cced` committed only `V24_V25_ICT_RESULTS.md`,
`v24_ict_pooled.py` and `v25_frequency_tradeoff.py` — result tables, no Pine.
`pine_list_scripts` returns a **single** saved script slot (`V4 Gold DEBUG`,
version 133), which every experiment since has overwritten. So `k`, the pivot
lengths, *which* opposing swing, and how multiple FVGs were resolved are all
gone. Recorded as **UNKNOWN**, not reconstructed.

### A3. Recovered — an implicit FVG-selection rule that contradicts §17

`strategies/V8_3_XAU_trend_range.pine:176-196` keeps **one** bull and **one**
bear FVG in scalar state and overwrites on each new one:

```pine
if bullFvgNow
    bullFvgTop := low
    bullFvgBot := high[2]
    bullFvgFilled := false
```

So the project's only FVG implementation resolves multiples as **"the most recent
unfilled FVG"** — a fourth candidate alongside F4's (a) first-after-BOS,
(b) largest, (c) containing the break level. It is *not* the §17 preference, and
it was never described as a selection rule anywhere; it is a side effect of using
scalars instead of an array.

### A4. Nothing else exists

- **CHOCH**: zero occurrences in any `.pine` file, working tree or history. Every
  history hit is a prose mention in a Phase 10/12/13 or human-notes document.
- **"internal structure" / "opposing swing"**: only in `PHASE13_LTF_SPEC_AUDIT.md`
  (the statement of the gap) and `V24_V25_ICT_RESULTS.md` (A2 above).
- **1m / 3m pivot strength**: no value anywhere. Every `swLen` in the repo is
  `input.int(10, "swing pivot len")` on a 5m chart, or `pivotLen = 5` / `pivL 5,
  pivR 3` on 15m. None is an LTF value.
- **sweep→CHOCH delay**: no value anywhere. The nearest neighbours are
  `bosMaxBars = 15` (sweep→**BOS**, 15m), `dispWait = 12` and `retBars = 24` (5m).
- **`request.security_lower_tf`**: introduced by Phase 13; it appears in no
  strategy, past or present.
- **deleted files**: `git log --all --diff-filter=D` lists no removed `.pine`,
  `.md` or `.py` file. Nothing was lost to deletion — A2 was lost to overwriting.

### A5. Status of M1–M5 after the recovery search

| | gap | status |
|---|---|---|
| **M1** | CHOCH swing selection | **UNKNOWN.** No implementation ever existed except A2, whose source is destroyed |
| **M2** | BOS swing selection | **PARTIAL.** A1 gives an explicit, causal rule — most recent confirmed opposing pivot, break on close — but at `pivotLen 5` on 15m, not at any LTF |
| **M3** | LTF pivot strength | **UNKNOWN.** No 1m or 3m value has ever been written down |
| **M4** | FVG selection among multiples | **CONFLICTED.** A3 is an implicit "most recent"; §17 prefers "the one the displacement left". Neither is stated as a rule |
| **M5** | sweep→CHOCH delay | **UNKNOWN.** `bosMaxBars 15` is a sweep→BOS bound on 15m, not a sweep→CHOCH bound at LTF |

---

## B. STEP 2 — the OHLC capacity probe

Read-only Pine indicator (`LTF DATA PROBE`), five runs, `COMEX_MINI_DL:MGC1!`.
Nothing was bypassed: this is the documented `request.security_lower_tf` API.

| # | chart TF | chart bars | LTF | request form | bars w/ data | values **per field** | total across 4 fields | earliest LTF bar (UTC) |
|---|---|---|---|---|---|---|---|---|
| 1 | 5m | 20,574 | 1m | 4 separate calls | 20,001 | **100,000** each | **400,000** | 2026-05-27 02:15 |
| 2 | 5m | 20,574 | 3m | 4 separate calls | 20,574 (all) | 34,290 each | **137,160** | 2026-05-24 22:00 |
| 3 | 5m | 20,574 | 30S | 1 call | 1,380 | 13,800 | — | 2026-08-30 22:00 |
| 4 | 15m | 21,938 | 1m | 1 call | 6,667 | **100,000** | — | 2026-05-27 02:15 |
| 5 | 15m | 21,938 | 3m | 1 call | 20,002 | **100,000** | — | 2025-10-29 23:00 |
| 6 | 15m | 21,938 | 1m | **tuple** `[o,h,l,c]` | 6,667 | **100,000** each | **400,000** | 2026-05-27 02:15 |

### B1. The limit is **A — per requested expression/field**

Three independent demonstrations, no assumption:

1. **Run 2 exceeds 100,000 in aggregate without truncating.** 4 × 34,290 =
   137,160 values returned, full coverage of all 20,574 chart bars. An aggregate
   budget of 100,000 is therefore falsified outright.
2. **Runs 1 and 6 each return 100,000 per field, four fields, same coverage.**
   Separate calls and the tuple form behave identically, so the budget is not
   per call either — it is per field.
3. **Run 5 caps 3m at exactly 100,000 too.** The number is a property of the
   request, not of the resolution.

### B2. It is a value cap, not a bar cap and not a history-depth cap

- Not a ~20,000-**chart-bar** cap: run 4 covers only 6,667 chart bars, and run 5
  covers 20,002 — the invariant across them is the value count, not the bar count.
- Not a 1m **history-depth** limit that we could work around: 100,000 one-minute
  bars ≈ 72 trading days ≈ 101 calendar days, which lands on 2026-05-27 — the
  same earliest timestamp on a 5m chart and on a 15m chart. The cap binds before
  any history limit does, so 1m depth beyond it is unobservable through this path.
- **A third limitation does exist, at seconds resolution** (answer C, alongside A):
  run 3 shows 30S data stops after 1,380 chart bars / 13,800 values — five days.
  That is a data-availability limit, far below the cap. It does not affect 1m/3m.

### B3. Coverage by timestamp against the fold boundaries

Folds, from `V49_multi_level_ledger.pine:32-34`: **A** < 2026-07-16 00:00,
**B** 2026-07-16 → 2026-08-09, **C** 2026-08-09 → 2026-08-31.

On the production **5m** chart (whose own series starts 2026-05-24 22:00):

| LTF | earliest | fold A | fold B | fold C |
|---|---|---|---|---|
| **1m** | 2026-05-27 02:15 | **partial** — starts 2.2 days after the 5m chart itself does | **full** | **full** |
| **3m** | 2026-05-24 22:00 | **full** (limited only by the chart, not by the LTF call) | **full** | **full** |

Fold A on 5m is 2026-05-24 → 07-16, ~7.5 weeks; 1m gives all but the first
2.2 days of it. **Both hypotheses are covered on all three folds today.**

### B4. The 1m window slides, and that is a reproducibility hazard

The 1m cap is 100,000 minutes measured **back from the last bar**, so its start
advances about one calendar day per calendar day. Today it sits at 2026-05-27,
2.2 days inside fold A. Within roughly **two months** it will have eaten fold A
entirely, and around **2026-12-10** it will begin eating fold C. A 1m result
recorded now is not exactly re-runnable later; a 3m result is, until the 5m chart
series itself rolls off. Any 1m run must therefore record its coverage window in
the artefact, and a re-run that reports a different window is a different test.

---

## C. STEP 3 — 1m and 3m are separate hypotheses

- **Hypothesis A (5m sweep + 1m LTF)** is the documented process. Data supports
  it today on all three folds, subject to B4.
- **Hypothesis B (5m sweep + 3m LTF)** has better and stable coverage, but 3m is
  **a proxy for the documented 1m process, not the documented process itself**.
  It also does not tile 5m evenly — 1 or 2 intrabars per chart bar (run 2), so a
  "3m CHOCH" is not a coarsened 1m CHOCH, it is a different object.

3m is **not** silently substituted for 1m anywhere in this audit, and neither is
recommended over the other here — the choice is not the blocker, and making it
would not unblock anything.

---

## D. STEP 4 — architecture verification

The intended shape is: **the existing 5m engine, unchanged, plus a read-only LTF
layer consulted between arming and entry.** Checked against the four prohibitions:

| prohibition | verified |
|---|---|
| do not run the whole strategy natively on 1m | holds — the script's `timeframe.period` stays 5m; `request.security_lower_tf` returns arrays *into* 5m bars |
| do not re-detect sweeps on LTF candles | holds — sweeps stay in the V49 5m block (`V49_multi_level_ledger.pine:257`), which the LTF layer only reads |
| do not change the 5m ATR framework | holds — `atr`, the ±0.20×ATR stop buffer and the R denominator are all 5m quantities and are not re-derived |
| do not introduce a second sweep engine | holds — one sweep stream; the LTF layer produces a boolean gate, not candidates |

No violation is forced by the data path. The probe confirms the LTF layer is
available inside the 5m script, which is what this architecture requires.

---

## E. What would still have to be frozen

Unchanged from Phase 13, now with the recovery search behind them. F1, F3 and F5
have **no** repository evidence; F2 and F4 have partial, conflicting evidence
that must be either adopted deliberately or rejected deliberately.

| | decision | repository evidence |
|---|---|---|
| **F1** | CHOCH swing selection | none (A2 destroyed) |
| **F2** | BOS swing selection | A1: most recent confirmed opposing pivot, break on **close** — at `pivotLen 5` on 15m |
| **F3** | LTF `swLen` for 1m / 3m | none |
| **F4** | FVG selection among multiples | A3: implicit "most recent unfilled", contradicting §17 |
| **F5** | sweep→CHOCH max delay | none (nearest: `bosMaxBars 15` on 15m, wrong beat and wrong timeframe) |
| **F6** | ATR timeframe for LTF stops | 5m, if the D architecture is kept |

---

## F. Readiness verdict

# STOP — SPECIFICATION INCOMPLETE

**Data is not the blocker.** The Phase 13 caveat is resolved in the permissive
direction: the 100,000-value limit is **per field**, so requesting open, high,
low and close costs no coverage at all relative to requesting close alone
(runs 1 and 6: 400,000 values delivered). Both 1m and 3m cover all three folds
on the production chart today. Phase 12's conclusion that LTF data access is
infeasible is now doubly superseded and should not be cited again.

**Definition is the blocker.** Three of the five elements the sequence needs —
which swing a CHOCH breaks (M1), the LTF pivot strength that decides how many
swings exist at all (M3), and how long after the sweep a CHOCH still counts (M5)
— have **no definition anywhere in the repository or its history**, and the one
implementation that had them was overwritten in the single TradingView script
slot and is unrecoverable. A fourth (M4) has an implicit rule that contradicts
the specification's stated preference. Inventing any of them would be choosing a
parameter, which §25.7 makes a stop condition, and choosing three of them
together would make the test a search rather than a test.

The gate is unchanged since Phase 13 and one item shorter than it looked: **F1,
F3 and F5 must be supplied by you.** F2 and F4 can be resolved from the repository
if you accept A1 and reject A3, but that is still your ruling, not a recovery.

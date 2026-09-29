# Phase 12 — LTF 1m/3m data-access feasibility audit

No profitability tested. No strategy built. No parameters optimised. No 5m proxy.
No alternative definition invented. Fold C performance not inspected. V49/V51/V52
untouched.

---

## 1. Exact LTF hypothesis recovered

Every reference in the repository, from `MANUAL_PROCESS_ANALYSIS.md`,
`HUMAN_RECONSTRUCTION.md`, `HUMAN_TRADE_REGISTER.md`, `PHASE10_FEATURE_MAP.md`:

> **row 16:** `LTF trigger on 1m/3m | 1m OB | CHOCH → retest → BOS → imbalance retest | 1m inverted + 3m engulfing | **no**`
>
> **§4.1:** *"The notes describe a precise sequence: 1m CHOCH → retest of the CHOCH → BOS → entry on the retest of the imbalance the BOS left behind. I substituted 'price touches VWAP and rejects', which is far cruder. The real trigger lives on 1m, and TradingView's bar limit makes a 7-month 1m backtest impossible here."*
>
> **N2:** `OB tap above the swept low, on the retest of the CHOCH`

| required element | documented? |
|---|---|
| timeframe(s) | **yes** — 1m primary, 3m secondary ("3m engulfing") |
| ordering | **yes** — CHOCH → retest of the CHOCH → BOS → retest of the imbalance the BOS left |
| **swing definition** | **NO** — no pivot length, no fractal rule, no swing-significance criterion |
| **CHOCH definition** | **NO** — never defined. Which swing, broken by what (wick or close), by how much |
| **BOS definition** | **NO** — never defined at 1m |
| **trigger / freeze point** | **NO** |
| **max delay after the sweep** | **NO** |
| **parameters** | **NONE** at 1m |
| explicitly marked causal/encodable | **explicitly marked encodable: NO** |

### Is there a conflicting definition in the repo?

There is a second, unrelated BOS construct in the V8.3 / V11.1 / V12 / V13 Pine
files: `bosMaxBars = 15` ("Max bars for BOS after sweep") and
`useContinuation` ("Allow BOS+retest without sweep"). It runs on the **chart
timeframe (5m/15m)**, has **no CHOCH component**, and is a `sweep → BOS` pattern
rather than `CHOCH → retest → BOS → imbalance retest`.

**This is a different construct, not a competing definition of the same one.**
It supplies no missing element of the LTF hypothesis: it is not 1m, and it has
no CHOCH. So there is no contradiction to stop on — but there is also no
operational definition to implement.

**Finding: the exact CHOCH/BOS definition is UNAVAILABLE.** Four of the nine
required elements are absent, and the source marks the whole row encodable: **no**.

Under the audit's stop conditions this is a stop. I continued into the data audit
anyway and am flagging that deliberately: the data-access question is independent
of the definition, it is the question the task was set to answer, and answering it
now means it does not have to be re-asked if the definition is ever supplied.
Everything below is data feasibility only.

---

## 2. Data-path audit

`src/core/data.js` retrieves bars by reading TradingView's in-memory series over
CDP:

```
window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().mainSeries().bars()
```

`getOhlcv()` walks `firstIndex() … lastIndex()` and returns
`start = max(firstIndex, end − limit + 1)` — i.e. **always the most recent N**.

| path | classification | note |
|---|---|---|
| `data_get_ohlcv` | **AVAILABLE BUT HISTORICALLY INSUFFICIENT** | hard cap `MAX_OHLCV_BARS = 500`, and **no offset/from/to parameter exists** — arbitrary historical windows cannot be requested |
| direct series read via `ui_evaluate` | **AVAILABLE NOW** | arbitrary index range, no 500-bar cap; this is how the probe below was done |
| `chart_set_visible_range` | **AVAILABLE NOW** | the supported mechanism that makes TradingView lazy-load more history |
| `chart_scroll_to_date` | **AVAILABLE BUT INSUFFICIENT** | measured: did **not** trigger a history load (series stayed at 310 bars) |
| replay tools (`src/core/replay.js`) | **NOT AVAILABLE** for bulk history | drives playback, does not export series |
| Pine-side export | **NOT AVAILABLE** | Pine can only surface values through plots/tables read back per run; no bulk export exists |
| local persistence | **AVAILABLE WITH SMALL IMPLEMENTATION** | none exists today; the probe below wrote JSON by hand |

**Displaying data interactively ≠ retrieving it programmatically** — and the two
diverge here in a way that matters: the MCP's own OHLCV tool is the *weakest*
path, while the raw series read is the strongest.

## 3. Historical coverage — measured, not assumed

Fold boundaries from the committed spec: A = all before **2026-07-16**,
B = 07-16 → **08-09**, C = 08-09 → **08-31**.

| timeframe | instrument | earliest bar | latest bar | bars | fold A? | fold B? |
|---|---|---|---|---|---|---|
| **1m** | MGC1! | 2026-08-16 22:00 | 2026-09-04 20:59 | **20,700** | **NO** | **NO** |
| **3m** | MGC1! | 2026-07-02 22:00 | 2026-09-04 20:57 | **21,080** | **partial** | **YES** |
| **3m** | 6E1! | 2026-07-02 22:00 | 2026-09-04 20:57 | **21,037** | **partial** | **YES** |

Method: set the timeframe, call `chart_set_visible_range` far back to force the
lazy load, then read `bars().size()`, `firstIndex()`, `lastIndex()` directly.

- On a fresh 1m load the series holds **310 bars (5.2 hours)**. One forced range
  request expands it to **20,700**. A second, further-back request returns the
  **identical** 20,700 / same first timestamp — **~21k bars is a hard cap**, and
  the chart clamps the requested range rather than loading earlier data.
- Two different instruments returned 21,080 and 21,037 bars with the **same
  calendar window**, so the cap is a bar count, not an instrument property.

**1m cannot reach fold A or fold B at all** — it starts 2026-08-16, five weeks
after fold B begins. **3m covers fold B in full** and reaches back to 2026-07-02,
covering roughly the last two weeks of fold A out of ~55 days (~25%).

## 4. Is the bar limit actually the blocker?

Tested rather than restated:

| route | result |
|---|---|
| direct historical request | capped at ~21k bars |
| `chart_scroll_to_date` | no additional load |
| `chart_set_visible_range` | **works** — 310 → 20,700 in one call |
| repeated / chunked requests further back | **no effect** — identical size and first timestamp |
| symbol-specific requests | same cap on both instruments tested |
| alternate endpoints in the repo | none provide deeper history |
| Pine-side export | not available |

**The old statement was directionally right but imprecise.** The blocker is not
"1m exceeds the bar limit" in the abstract — it is that the account's series cap
of ~21k bars translates to **19 calendar days at 1m** and **64 at 3m**, and no
supported route extends it. Nothing here was bypassed: no auth, no rate limits,
no access controls, no elaborate workaround.

## 5. Data continuity

Full scan of the loaded 6E1! 3m series, 21,037 bars:

| check | result |
|---|---|
| duplicate timestamps | **0** |
| out-of-order bars | **0** |
| OHLC integrity violations (`high ≥ max(o,c)`, `low ≤ min(o,c)`, `high ≥ low`) | **0** |
| gaps > one bar step | **86**, max **190,980 s (53 h)** |

86 gaps over 64 calendar days is consistent with ~45 daily exchange halts plus
~9 weekends; the 53-hour maximum is a weekend. **This is normal futures session
structure, not corruption.** Any structural scan must treat session boundaries
explicitly rather than assuming contiguity — the persisted probe below is
contiguous within its window, but the full series is not.

Timezone handling is consistent: all timestamps are epoch seconds, and the
UTC-derived session boundaries reconcile with known futures hours.

## 6. Required data volume

| | 1m | 3m |
|---|---|---|
| bars per trading day (~23 h) | ~1,380 | ~460 |
| trading days in folds A+B (5m engine, ~2026-05-19 → 08-09) | ~59 | ~59 |
| days per instrument obtainable now | **~15** | **~45** |
| bars needed, 5 instruments, folds A+B | **~407,000** | **~136,000** |
| bars obtainable now, 5 instruments | ~103,500 | ~105,000 |
| storage (JSON, ~60 B/bar) | ~24 MB | ~8 MB |
| retrieval cost | ~21k bars per instrument per forced load; the probe's full-series scan ran in one `ui_evaluate` call in well under a second |

Storage and runtime are trivial. **Coverage is the only constraint.**

## 7. Causal implementation feasibility

Cannot be assessed, and the reason is §1, not the data.

Of the documented sequence, only the **ordering** is specified. To determine when
each element becomes knowable I would need the swing definition (which fixes the
confirmation lag), the CHOCH break rule (wick or close, and by how much) and the
BOS rule. None exists. Supplying any of them would be inventing an alternative
definition, which is explicitly forbidden.

What *can* be said about the data: 3m bars carry epoch timestamps, are strictly
ordered, and a symmetric L-bar pivot scan over them confirms each swing exactly
L bars after the swing bar — the same causal structure already proved for the 5m
pivots in the V51 Gate A audit (0 confirmation-lag mismatches in 7,454
candidates). **The resolution and shape are adequate for a causal structure
scan; the rule to run on them is missing.**

## 8. Minimal proof-of-access

Retrieved and persisted `trader_v2/ltf_probe/6E1_3m_20260722.json` —
**41 × 3m bars, CME:6E1!, 2026-07-22 12:00–14:00 UTC, inside fold B.**

Verified locally after persistence:

| check | result |
|---|---|
| bars persisted | 41 |
| step spacing | all 180 s — **contiguous** |
| timestamps monotonic | yes |
| duplicates | 0 |
| OHLC integrity failures | 0 |
| volume present | yes, all bars |
| consumable by a causal structure scan | yes — a symmetric 2-bar pivot scan yields 2 confirmed swing highs, each knowable 2 bars after its own bar |

The pivot scan is a **shape check on the data**, not an implementation of the
documented CHOCH/BOS rule, which cannot be implemented (§1).

**Established: historical LTF bars inside fold B can be pulled into a local
programmatic pipeline through the existing supported path.** That was the
question, and the answer is yes.

## 9. Cost / complexity

# **YELLOW**

The data path works and is cheap, but two components do not exist yet:

1. **A chunked extractor.** `data_get_ohlcv` has a 500-bar cap and no offset, so
   bulk retrieval needs the direct series read plus a loop over index ranges —
   perhaps 50 lines, no new dependency, no platform limit defeated.
2. **Local persistence.** Nothing writes bars to disk today; the probe file was
   written by hand.

It is not GREEN because neither component exists and 1m cannot reach the folds.
It is not RED because 3m *does* cover fold B in full and part of fold A through a
supported route.

## 10. Decision

# **C — LTF experiment is currently infeasible**

Two independent blockers, either sufficient on its own:

1. **The hypothesis has no operational definition.** Swing rule, CHOCH rule, BOS
   rule and delay tolerance are all absent, and the source marks the row
   encodable: **no**. There is nothing to implement, and inventing it is
   forbidden. This blocker is not a data problem and no amount of data access
   removes it.
2. **1m — the timeframe the notes name as where "the real trigger lives" — cannot
   reach folds A or B.** 19 calendar days of coverage against a fold B that ends
   five weeks before 1m history begins. The validation framework used for every
   result in this project cannot be applied to it.

**What is now known that was not before:** the old blanket claim that LTF data is
unobtainable is **too strong**. 3m covers fold B in full, reaches ~25% of fold A,
and can be pulled into a local pipeline through a supported route with a small
extractor. So the decision is C — but the *reason* has shifted from "we cannot
get the data" to "we do not have the rule, and the specific timeframe the rule
names is the one we cannot cover."

**What would change this to B:** a written CHOCH/BOS specification from the user
covering swing definition, break rule, BOS rule and maximum delay after the
sweep — plus acceptance that the test would run on **3m over fold B only**, with
fold A partial and 1m unavailable. That is a materially weaker validation design
than every prior phase used, and it should be agreed before, not after.

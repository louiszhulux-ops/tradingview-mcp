# Controlled 3m LTF extraction — ready-to-run plan

**Status: NOT RUN. BLOCKED on TradingView availability.**

Non-frozen operator document. Written at commit
`3d333ad27eb05e0b27f5101d526f8f9c7e71c1a9`, working tree clean, no 3m candidate
files present. Nothing in this document has been executed: **TradingView was not
contacted beyond two failed connection probes, no layout was opened, switched or
modified, and no data was extracted.**

---

## 1. Current blocker

TradingView Desktop is **not reachable over CDP on port 9222**. The MCP server
itself is up and answering — it returned structured errors, not a transport
failure — but it cannot reach the desktop application:

```
tv_health_check  →  "CDP connection failed after 5 attempts: fetch failed"
                    "TradingView is not running with CDP enabled."
tab_list         →  "fetch failed"
```

Extraction cannot proceed until a **safe disposable TradingView session** is
available. `tv_launch` was deliberately **not** called: a cold launch restores
the previous session, which may place the protected chart `2d43Iesr` in the
active tab, and switching that tab to a research layout would navigate the
protected chart away — precisely the P-6 incident.

---

## 2. Existing mechanism — a reusable 3m path already exists

`docs/p9_extraction_probe.pine` already accepts `"3"`:

```pine
ltfStr = input.string("1", "lower timeframe", options=["1", "3"])
aO = request.security_lower_tf(syminfo.tickerid, ltfStr, open)
aH = request.security_lower_tf(syminfo.tickerid, ltfStr, high)
aL = request.security_lower_tf(syminfo.tickerid, ltfStr, low)
aC = request.security_lower_tf(syminfo.tickerid, ltfStr, close)
aT = request.security_lower_tf(syminfo.tickerid, ltfStr, time)
preFE = time < FE                      // FE = 1788134400000, parent-level gate
```

The probe carries **no strategy logic**: no ATR, pivots, sweep, CHOCH, BOS, FVG,
entry, stop, target, risk or P&L. It requests the arrays and republishes them as
plots; nothing is computed from them.

**One change is required.** The P-9 probe plots `t/h/l/c` only — `aO` is
requested to preserve V53's exact five-field request shape but is never plotted
(`p9_extraction_probe.pine:21`, `:77`). This task's CSV contract requires
`open`, so the probe must plot `aO` as well.

**Do not edit `docs/p9_extraction_probe.pine`.** It is the record of what P-9
actually ran. Create a sibling, e.g. `docs/p11_3m_extraction_probe.pine`,
identical except that it plots `o` alongside `t/h/l/c` and needs only three
slots (see §4).

Read-back uses the established raw-CDP path, not `data_get_study_values` — that
returns only the *current* bar's values, and the extraction needs the full
series. The pattern is the one `src/core/data.js` already uses:

```js
var chart  = window.TradingViewApi._activeChartWidgetWV.value()._chartWidget;
var model  = chart.model();
var srcs   = model.model().dataSources();   // find the study by metaInfo().description
// then walk the study's own series: firstIndex() / lastIndex() / valueAt(i)
```

`getOhlcv` (`src/core/data.js:137-155`) shows the equivalent walk over
`mainSeries` bars and is the template for indexing and extraction.

---

## 3. Safe start procedure

Run in order. **Any STOP is final for the session** — do not improvise around it.

1. `tv_health_check` — confirm CDP on 9222 responds.
2. `tab_list` — inspect every open tab **before doing anything else**.
3. Determine the active tab's chart id.
   * **If the active tab is `2d43Iesr` → STOP.** Do not switch it, do not
     navigate it, do not read it, do not open a new tab to escape it.
4. Confirm a disposable research layout is reachable **without** touching the
   protected chart. `P2NtY6fg` ("B1 ROLL INVESTIGATION") is the layout P-9 used.
5. **Do not call `tab_new`.** In P-6 it navigated the tab showing `2d43Iesr`
   away from it. P-9 deliberately reused the existing disposable layout instead,
   and accepted that deviation to protect the chart.
6. Carry a hard `location.href` abort guard on `2d43Iesr` inside **every**
   `ui_evaluate`, as P-9 did. It never fired there; it must be present anyway.
7. **Do not call `pine_smart_compile`.** In P-9 it clicked *Pine Save* and
   overwrote the unrelated saved script `V4 Gold DEBUG` as version 143
   (`docs/PHASE_P9_LTF_EXTRACTION.md` §16). Create a fresh script with
   `pine_new` and compile without any path that can press Save.
8. If a disposable layout cannot be established without touching the protected
   chart → **STOP**.
9. Record the protected chart's CDP target id at start and at end, and confirm
   they match. Note that this check alone cannot detect a study version
   re-binding (P-10B) — so also avoid every operation that could cause one.
10. Remove the extraction study from the disposable layout when finished.

---

## 4. Extraction scope

| | |
|---|---|
| instruments | `MGC1!`, `MNQ1!` — no substitutes, no dated contracts, no `_DL` requested (note: P-9 requested non-`_DL` and TradingView resolved to `_DL`; record whatever is actually served) |
| lower timeframe | **3 minute** |
| parent timeframe | 5m, matching the frozen Phase-C parent grid |
| window start | `2026-05-24T22:00:00Z` — the Phase-C parent coverage start |
| window end | `FE = 2026-08-31T00:00:00Z` = `1788134400000` |

**FE rules — exclusive on the open instant:**

* accept `open_ts < FE_MS`
* accept only if `close_ts <= FE_MS`
* reject any bar opening at or after FE
* reject any bar closing after FE
* **no post-FE padding**, including to fill the 100,000-element cap

**Slot count.** 3 does not divide 5, so a 5m parent holds **1 or 2** 3m sub-bars
(aggregate ratio 1.6662 ≈ 5/3, `bot/contracts/UNRESOLVED.md` U3). Plot slots
0–2: two for the expected maximum and a third purely as an overflow detector,
which should never be non-`na`. Report it if it ever is.

---

## 5. Extraction restrictions

Candidate data only. No V53 execution, no parity adjudication, no strategy
calculation of any kind. No stitching, no pagination, no cap bypass, no chart-
history manipulation intended to defeat the LTF limit. No synthetic bars, no
interpolation, no inferred OHLC. No modification of any frozen artifact or
fixture. No Phase-16 activity. Preserve exactly what TradingView returns; if the
full range cannot be served, **record the limitation** rather than working
around it.

---

## 6. Expected output

| artifact | notes |
|---|---|
| `data/phase_c_ltf/MGC1__3m.csv` | new file; must not exist beforehand |
| `data/phase_c_ltf/MNQ1__3m.csv` | new file; must not exist beforehand |
| `data/phase_c_ltf/3m_candidate_manifest.json` | **separate** manifest — do **not** modify `data/phase_c_manifest.json` or `data/phase_c_ltf_manifest.json` |

CSV contract: `timestamp,open,high,low,close`. Timestamps are raw UTC seconds,
matching the frozen 5m and candidate 1m convention. Values preserved exactly as
returned; **no rounding for convenience**.

Per-row validation, checked **before** writing:

* timestamp valid, strictly increasing, no duplicates
* timestamp strictly before FE
* bar attributable to a Phase-C 5m parent
* `high >= max(open, close)` and `low <= min(open, close)`

**Do not silently repair an invalid row.** Fail the extraction and report.

Measure and report, per instrument: requested parent start; requested FE; first
and last returned 3m timestamp; total rows; unique timestamps; duplicate count;
first/last parent represented; parents with ≥1 returned bar; parents with zero;
whether the 100,000-per-field cap was reached; whether the stream is
head-truncated; whether it reaches the whole pre-FE window; post-FE rows
observed; malformed/out-of-order/duplicate rows observed.

**Cap semantics — measure, do not assume.** P-9 established that the *1m* stream
was capped at 100,000 elements. Do **not** assume 3m reaches the beginning, that
it reaches FE, that it has one-third of the 1m limitation, or that the cap is
the only limiting factor. The 3m fold-C fixtures record `ltf_bars` of 34,269
(MGC) / 34,239 (MNQ) — below the cap — but that was a *different chart* at a
*different date*, and it is evidence about the past, not a prediction. Record
observed evidence only, and never infer completeness from the absence of an
explicit TradingView error.

**Parent mapping.** A 3m bar may straddle a 5m boundary. Do not assume one-to-one
containment, do not discard a bar because the relationship is nontrivial, and do
not fabricate a mapping. Document the exact observed relationship between the
returned 3m timestamps and the existing 5m parent grid.

**Status is `CANDIDATE`.** Never `AUTHORITATIVE`. Under the ratified G1 rule
(`bot/GATE1_ACCEPTANCE.md` §1.1a) a cell is authoritative only if *every*
required dataset is explicitly and unqualifiedly authoritative — and the 5m
parent manifest still reads `PARTIAL`. A successful 3m extraction therefore
moves 12 cells from `NO-DATA` to at best `PROVISIONAL`. It cannot produce a
Gate 1 pass.

---

## 7. Protected material — byte-for-byte unchanged, before and after

* `trader_v2/` (all of it, including Phase-15 and Phase-16 artifacts and
  `p16/PHASE16_PROTOCOL.md`)
* `bot/fixtures/` — all 25 golden fixture files
* `data/phase_c/` — `MGC1__5m.csv`, `MNQ1__5m.csv`
* `data/phase_c_manifest.json`
* `data/phase_c_ltf/MGC1__1m.csv`, `data/phase_c_ltf/MNQ1__1m.csv`
* `data/phase_c_ltf_manifest.json`
* `data/roll_calendar.json`
* frozen V53 artifacts — `V53_ltf_sequence.pine` `7490766b…`,
  `p15/executed/V53_EXECUTED_BUILD.pine` `2dafbafd…`,
  `p16/executed/V53_P16_OOS_BUILD.pine` `5c21acfa…`
* the registered OOS boundary `FE = 1788134400000` and the fold definitions

If any protected path changes unexpectedly: **STOP, do not revert blindly**,
report the exact modification, and do not commit.

---

## 8. Resume condition

All four must hold:

1. TradingView Desktop is running with CDP on 9222;
2. the active tab has been inspected and is **not** `2d43Iesr`;
3. disposable layout access is confirmed;
4. the protected chart will not be navigated away from or modified.

---

## 9. Post-extraction

Run the full test suite; run `bot/tools/check_guards.py`; verify all frozen
hashes; verify every protected path in §7; verify no post-FE data entered any
file; inspect the complete diff and confirm only intended files changed.

**Do not adjudicate Gate 1 in the extraction task**, and do not alter the
standing verdict on the strength of new candidate data. Do not push.

---

## 10. What this cannot fix

The fold-C divergence is a **proven data-horizon deficit**: V53 gates only
arming on `inFold`, so a sequence armed in-fold keeps producing counted events
on later bars, and the Phase-14 runs continued past FE while our replay
correctly stops there (`bot/GATE1_ACCEPTANCE.md` §4.7). **A 3m extraction
cannot repair that**, in fold C or anywhere else, and must not be attempted as a
remedy for it. The purpose here is solely to measure whether a usable 3m stream
is still recoverable for the 12 cells that currently hold `NO-DATA`.

# Phase P-8 — U-15: Historical LTF Depth Investigation

**Does `request.security_lower_tf()` reach historical lower-timeframe data that the ordinary
intraday chart series cannot, or is it bounded by the same depth limit?**

Read-only. No Pine executed or compiled, no chart symbol/resolution/study altered, no data
recovered, no provider substituted, no frozen artifact touched. All inspection ran on the isolated
layout `P2NtY6fg`; the protected chart `2d43Iesr` was **never opened, attached to, or read**.

---

## 1. Executive conclusion

## **RESOLVED — DEEPER PATH**

The lower-timeframe request path is **not** bounded by the same-resolution chart-series limit. It
is bounded by the **parent series' range** and the 100,000-per-field cap.

The decisive evidence is a controlled same-resolution comparison, needing no assumption about the
1m cap at all:

| 3-minute data, same symbol, same account | reach |
|---|---|
| via the ordinary **3m chart series** (measured P-7) | back to **2026-07-02 22:00** — 63 days |
| via **`request.security_lower_tf(..., "3", ...)`** (frozen run files) | back to **2026-05-24 22:00** — 102 days |

The 3m LTF request reached the **first bar of the 5m parent series** — `cov 2026-05-24 22:00` with
`w/LTF 10386 == foldbars 10386` for MGC and `10368 == 10368` for MNQ, i.e. *every* parent bar was
served, uncapped. The 3m chart series stops 39 days short of that.

Two paths, one resolution, one session, one auth token — different depth. That is a deeper path,
and it is shown by measurement rather than inferred from "Pine returned old values".

**This corrects P-7.** P-7 concluded the LTF values were "proven unrecoverable from TradingView"
because the 1m chart series only reaches 2026-08-16. That inference was **wrong**: the LTF path is
not bounded by the 1m series limit, so the 1m series limit never implied the values were gone. See
§10.

---

## 2. What U-15 asked

> Does the `request.security_lower_tf()` path used by V53 have access to deeper historical LTF data
> than the ordinary TradingView intraday chart series, or is it subject to the same historical
> depth boundary?

Deliberately **not** asked here, and kept separate throughout (P8.6):

| | question | status |
|---|---|---|
| Q1 | Did the original Pine execution reach the deeper data? | **YES** — established before P-8; the run files contain it |
| Q2 | Does a non-Pine interface currently expose it? | **NO** — §9 |
| Q3 | Is it retained but reachable only during Pine execution? | **Probable, not proven** — §8 |
| Q4 | Has it aged out entirely? | **Not established either way** — §8 |

U-15 is the *architecture* question. Q3/Q4 are retention questions, and §8 says exactly how far the
evidence carries.

---

## 3. Known historical evidence (P8.5)

From the frozen run files — direct, not derived:

| observation | value | source |
|---|---|---|
| 1m LTF first coverage, MGC fold A | 2026-05-27 02:15 UTC | `MGC_{L,S}_1m_A.txt` |
| 1m LTF first coverage, MNQ fold A | 2026-05-27 02:20 UTC | `MNQ_{L,S}_1m_A.txt` |
| **3m LTF first coverage, both instruments** | **2026-05-24 22:00 UTC** | `{MGC,MNQ}_{L,S}_3m_A.txt` |
| 3m fold-A parent bars served | **all of them** (`w/LTF == foldbars`) | same |
| first bar of the frozen 5m parent dataset | **2026-05-24 22:00 UTC** | `data/phase_c/*_5m.csv` |
| run-time chart end | 2026-09-04 20:55 UTC | recovered in P-7, three ways |

**No artifact anywhere in the repository records *where* that data came from** — no endpoint, no
data-source identifier, no request metadata. The run files record outputs only. Architecture had to
come from the platform (§5–§7).

---

## 4. Current chart depth (P8.7, P8.10)

Measured in P-7 by paging each resolution to exhaustion on `COMEX_MINI_DL:MGC1!`:

| resolution | oldest bar served | bars | days before run end |
|---|---|---|---|
| 5m | 2026-05-24 22:00 | 20,700 | 102 |
| 3m | 2026-07-02 22:00 | 21,291 | 63 |
| 1m | 2026-08-16 22:00 | 21,332 | 18 |

**The boundary is server-declared, not a client artifact — VERIFIED.** With the 3m series sitting
at its limit, `mainSeries()._requestMoreDataAvailable.value()` reads **`false`**, and TradingView
instantiates an `_endOfDataPaneView` for it. The client stopped paging because the server said
there is no more, not because the bridge gave up.

**Recorded relationship, not promoted to a rule.** The three depths are ≈21,000 bars each, which
looks like a bar-count limit. But one observation cuts against a simple rolling window: the 5m
series began at **2026-05-24 22:00** at run time (2026-09-06) and begins at **2026-05-24 22:00**
today (2026-09-07). A rolling ~20,700-bar window would have advanced that start by roughly a day.
It did not move. **Whether the limit is a fixed calendar boundary, a slowly-updated bar-count
window, or an entitlement-tier rule is UNKNOWN**, and one day of observation cannot settle it.
Resolving it would need repeated measurement over time, or a resolution experiment this phase
forbids.

---

## 5. Architecture: chart series vs Pine request (P8.1, P8.2)

Both paths run over **one WebSocket, one session, one auth token**.

`mainSeries()._seriesSource._gateway` and `_chartApi._sessions['cs_r61XhbgePIHS']` are the **same
object** (identical own-property sets), and its prototype carries both families:

```
series : resolveSymbol  requestFirstBarTime  createSeries  modifySeries  removeSeries  requestMoreData
study  : canCreateStudy getStudyCounter getChildStudyCounter createStudy modifyStudy notifyStudy removeStudy
```

`_chartApi._wsBackendConnection` is a single socket; `set_auth_token` was sent exactly once.

**So the two paths share transport, session and entitlement context — but they are distinct request
families with distinct server-side semantics.** Notably there is **no `request_more_data` analogue
for studies**: a study is created *inside* the chart session that owns the series, and its data
extent follows from that, not from a separate paging loop.

### Protocol traffic actually observed (P8.4 — passive, no request replayed)

Read from `_chartApi.sentMethodsCounters()` / `receivedMethodsCounters()`, which the client
maintains for its own telemetry. Nothing was sent to obtain this.

| sent | count | | received | count |
|---|---|---|---|---|
| `create_series` | 1 | | `series_loading` | 59 |
| `modify_series` | 22 | | `series_completed` | 59 |
| **`request_more_data`** | **36** | | `timescale_update` | 144 |
| `resolve_symbol` | 13 | | `data_update` | 21,255 |
| **`create_study`** | **7** | | **`study_loading`** | **255** |
| `remove_study` | 1 | | **`study_completed`** | **233** |
| `request_more_tickmarks` | 1 | | `study_error` | 1 |

The client sends a **study specification** and receives **computed study outputs**
(`study_loading` → `study_completed`). It never receives raw lower-timeframe bars for a study.
**Pine — including `request.security_lower_tf` — is evaluated server-side**, and the LTF
constituents never reach the browser. That is why P-7's depth-5 walk found no LTF state: there is
none to find client-side, by construction.

### The mechanism this implies

`request.security_lower_tf` is resolved server-side over the **parent series' bar range**. Its
depth is therefore bounded by:

1. the parent series' extent — 5m, reaching 2026-05-24 22:00, and
2. the 100,000-bars-per-field cap established in P-7.

It is **not** bounded by the same-resolution chart-series limit. The observations fit exactly:

- **3m** — 34,269 values, under the cap, so it reached the full parent range: 2026-05-24 22:00.
- **1m** — would have needed ~102,805 values, so the cap bit first and it stopped at
  2026-05-27 02:15, **just inside** the parent range.

The 1m LTF cut is caused by the cap, not by data availability. Had the cap been larger, the parent
range was there to be read.

---

## 6. TradingView objects inspected (P8.3)

| object path | type | what it shows | distinguishes chart vs Pine history? |
|---|---|---|---|
| `mainSeries()._requestMoreDataAvailable` | observable → `false` | the depth boundary is **server-declared** | no, but proves the limit is server-side |
| `mainSeries()._endOfDataPaneView` | pane view `k` | TradingView renders an explicit end-of-data marker | corroborates the above |
| `mainSeries()._seriesSource._gateway` | `o` | one object exposing **both** series and study methods | **yes** — shared session, distinct request families |
| `_chartApi` (`ce`) | transport | `_wsBackendConnection`, single socket, one auth token | yes — shared entitlement context |
| `_chartApi.sentMethodsCounters()` / `receivedMethodsCounters()` | Maps | `create_study`/`study_completed` vs `create_series`/`request_more_data`/`data_update` | **yes — the primary architecture evidence** |
| `_chartApi._sessions['cs_…']` | `o` | identical to the gateway; studies are created **within** the series session | yes |
| `_chartApi._studySpecs` | Map, **empty** | no study running on this layout | explains P-7's null result |
| `gateway._lastSymbolResolveInfoMap` | Map, 25 entries | carries only `pro_name` | no depth metadata |
| `mainSeries().symbolInfo()` (53 keys, P-6) | record | no intrabar/limit field | no |

### P8.8 — Pine-specific depth metadata: **not observable**

No client-side object exposes a maximum-intrabars figure, a per-request historical depth, or a
Pine-specific retention setting. `_studySpecs` is empty because no study runs here. Since Pine
executes server-side, such limits are enforced there and are not surfaced to the client. **Stated
as not observable — not inferred from `LTFbars = 100000`**, which P8.9 correctly separates as a
different question.

### P8.9 — the cap does not by itself prove deeper retention

The invalid inference — "Pine returned 100,000 intrabars, therefore TradingView retains more than
21,000" — is **not** used here. The cap is an output limit on a request; it says nothing on its own
about what the store holds. The DEEPER PATH conclusion rests instead on the **3m comparison**
(§1), where the LTF request reached 102 days at a resolution whose chart series reaches 63, and
where the cap was never binding.

---

## 7. Why the frozen chart was not used

`2d43Iesr` carries a live `V53 LTF SEQUENCE` study — the only running instance of
`request.security_lower_tf` available, and in principle the most direct evidence for U-15.

**It was deliberately not read.** Its FUNNEL table would report coverage recomputed over *current*
data, which extends past `FE = 2026-08-31`. Reading it would mean inspecting a V53 computation
spanning held-out Phase 16 data, which `PHASE16_PROTOCOL.md` forbids before the boundary. The
protocol constraint binds independently of P-8's own read-only rule, so the route is closed on
principle, not merely on caution.

The chart was not opened, attached to, or switched to at any point in P-8.

---

## 8. Historical retention — what can and cannot be established (P8.6)

**Established:** at run time (2026-09-06, chart ending 2026-09-04 20:55) the server served, into a
study, 1m constituents back to 2026-05-27 and 3m constituents back to 2026-05-24. The data existed
server-side then, at a moment when the 1m chart series reached ~18 days and the 3m series ~63.

**Not established:** whether it is still served today. The only interface that reaches it is the
LTF request, and exercising that requires executing Pine — prohibited here.

A one-day-apart caveat applies to every comparison in this document: the chart depths were measured
2026-09-07, the LTF reaches are from 2026-09-06. For the 3m comparison the gap is 63 vs 102 days,
so a single day cannot account for it.

---

## 9. Current accessibility (P8.11)

**Can the old LTF values be obtained through a permitted non-Pine interface today? NO.**

- 1m chart series: reaches 2026-08-16 — short of folds A and B.
- 3m chart series: reaches 2026-07-02 — short of fold A.
- No client-side cache, loader or data-source object holds lower-timeframe history (§6).
- `requestFirstBarTime` exists on the gateway but was **not called**: it issues a network request,
  and P-8 is architecture, not extraction.

**Potential historical LTF source identified; extraction deliberately not performed under P-8
scope.** The `request.security_lower_tf` path is the route, and §5 shows why it reaches where the
chart series does not. Whether it still does is untested, and testing it means running Pine — a
decision for the study owner, under an authorisation P-8 does not have.

---

## 10. U-15 conclusion, and the correction it forces on U-14 (P8.12, P8.13)

### U-15: **RESOLVED — DEEPER PATH**

`request.security_lower_tf()` is bounded by the parent series' range and the 100,000-per-field cap,
not by the same-resolution chart-series limit. Demonstrated by the 3m comparison: 102 days via the
LTF request against 63 days via the 3m chart series, same symbol, same account, one day apart.

### Correction to P-7's U-14 wording

P-7 recorded that the LTF **values** are "proven unrecoverable from TradingView", reasoning from
the 1m chart series reaching only 2026-08-16. **That reasoning does not hold** — the LTF path was
never bounded by the 1m series limit. The claim is withdrawn and replaced:

> The LTF values are **not obtainable through any permitted non-Pine interface**. Whether they
> remain obtainable through the Pine lower-timeframe request path is **UNKNOWN**, and on the P-8
> architecture evidence it is **plausible that they are**. Settling it requires a Pine execution
> that is currently prohibited.

That is a weaker negative than P-7 stated, and the difference matters: P-7 implied the data was
gone; P-8 shows it may simply be behind an interface this phase may not use.

### Status of the U-14 components

| component | status |
|---|---|
| 100,000-bar per-field cap | **PROVEN** (P-7) |
| exact parent availability mask | **PROVEN** (P-7) |
| LTF values existed at run time | **PROVEN** (run files) |
| current ordinary 1m chart depth | **PROVEN** — 2026-08-16 |
| did the original request use a deeper source than the chart series? | **PROVEN — YES** (P-8) |
| does that source still hold the data? | **UNKNOWN** |
| can a non-Pine interface reach it? | **PROVEN — NO** |

---

## 11. Impact on B-3

**B-3 remains NOT READY for exact LTF value reproduction, and should proceed with exact
availability-mask reproduction only.**

Unchanged from P-7 in what B-3 may do; changed in *why*, and in what may become possible:

- **May:** reproduce the LTF availability mask exactly, from `cov_first` and the frozen parent
  series (P-7 §5); rely on the cap and counter semantics as established.
- **May not:** synthesise, aggregate or interpolate LTF bars; substitute a chart export or a
  provider series; assume the data is retrievable; assume it is gone.
- **New:** the honest blocker is no longer "the data is gone" but "the only interface that reaches
  it is Pine, and running Pine is not authorised". If the study owner wants exact LTF parity, the
  question to put to them is whether to authorise a **read-only Pine LTF extraction run** — scoped
  to dump LTF timestamps and OHLC without evaluating strategy logic, and bounded to pre-FE data so
  Phase 16 stays intact. **P-8 does not request that authorisation and did not perform it.**

---

## 12. Remaining unknowns

| # | unknown | status after P-8 |
|---|---|---|
| U-14 | the exact LTF stream | **re-scoped, not closed** — mask PROVEN recoverable; values not reachable by any permitted non-Pine interface; reachability via Pine UNKNOWN (§10) |
| **U-15** | LTF path depth vs chart-series depth | ✅ **RESOLVED — DEEPER PATH** |
| U-16 | exact per-parent LTF counts (the MGC `+5` residual) | unchanged — needs 1m history for 2026-05-27 → 2026-08-16 |
| U-17 | whether the 100,000 cap varies with chart resolution | unchanged — needs a Pine run at another parent resolution |
| **U-18** | *new* — whether the ~21,000-bar chart-series depth is a fixed calendar boundary, a rolling bar-count window, or an entitlement rule | **UNKNOWN** — the 5m start did not move over one day (§4) |
| **U-19** | *new* — whether the LTF path still reaches 2026-05-24/27 today | **UNKNOWN** — testable only by the prohibited Pine experiment |
| U-5 | B-ADJ during the 13F/14/15 runs | unchanged — STRONGLY INFERRED off |
| U-7 | `_DL` vs non-`_DL` historical roll parity | unchanged — UNKNOWN, non-`_DL` unreachable |
| U-9 | retroactive roll-rule revision | unchanged — calendar frozen in-repo as mitigation |
| U-12 | `settlementAsClose` effect on 5m/LTF bars | unchanged |
| U-13 | roll dates at intraday resolutions | unchanged |

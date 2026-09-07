# Phase B-1 — Continuous-Futures Roll Calendar

**Audit only. No production code was created or modified. V53, Phase 16, the protocol, the
analyser, the aggregator and the provider adapter are all untouched. No OOS analysis was run, no
TradingView connection was made, and nothing was deployed. This document is the only file
created.**

Audited at HEAD `7e1f1c1`, branch `claude/tradingview-paper-trading-auto-76ojnw`, working tree
clean before and after.

> ## Verdict up front
>
> **B-1 is BLOCKED at the evidence boundary. The roll calendar cannot be frozen from the
> repository, and no roll dates are asserted in this document.**
>
> The repository contains **zero** contract-rollover, expiry, back-adjustment or symbol-resolution
> information of any kind. The research records only the continuous tickers `MGC1!` and `MNQ1!`.
> The underlying contracts, the roll dates and the back-adjustment setting in force during the
> frozen runs are all **unrecorded and unrecoverable from committed artifacts**.
>
> A specific, bounded data pull will resolve it. It is defined in §6.

---

## 1. Current Repository State

Every claim here was verified by search against the working tree; counts exclude my own two
Phase B documents so that pre-existing knowledge is not confused with this investigation's output.

### 1.1 What the repository knows about MGC and MNQ

| dimension | state | evidence |
|---|---|---|
| instrument identity | a **bare string** — `instrument: str` | `bot/data/bars.py:56`, `bot/contracts/events.py:60` |
| symbols used in research | `MGC1!`, `MNQ1!` — continuous tickers only | 94 / 164 mentions; every run file and fixture |
| exchange prefix | **ambiguous — see 1.3** | conflicting artifacts |
| concrete contract | **absent everywhere** | no fixture, run file, manifest or ledger field carries it |
| expiry | **absent** | see 1.2 |
| roll / rollover | **absent** | see 1.2 |
| back-adjustment | **absent** | see 1.2 |
| contract resolution logic | **absent** | no root-symbol, month-code or resolver code exists |
| point value | derived, not configured — MGC $10/pt, MNQ $2/pt | A2 derived these from the committed ledger and verified them against every stop and target exit |
| tick size | **absent, and not required by the strategy** | V53 has no `syminfo.mintick` reference |

### 1.2 The vocabulary search — a negative result, stated precisely

Repo-wide, case-insensitive, all source and documentation:

| term | raw hits | **hits that actually concern futures contract rollover** |
|---|---|---|
| `roll` / `rollover` | 198 | **0** — all are V53's *rolling reference* (`pRef`/`L_choch`/`L_bos` advancing per bar) or the CME *session day roll* |
| `expiry` / `expiration` | 51 (excl. my docs) | **0** — all are V53's `FVG retest expiry` counter or TradingView **alert** expiration (`src/core/alerts.js:45`) |
| `continuous` | ~10 (excl. my docs) | **0** — `replay_autoplay` "continuous play", "continuously-updating feed", "HTTP 502 continuously" |
| `back-adjust` / `adjustment` | 2 (excl. my docs) | **0** — a drawdown-advice line in a skill, and an unrelated Phase 13F note |
| `open interest` | 1 | **0** |
| `front-month` | 2 | **0** — both in my own Phase B spec |

**Conclusion: the repository has never modelled contract rollover.** This is not a gap in
documentation; the concept is absent from the codebase.

### 1.3 A correction to my own Phase B specification

`trader_v2/PHASE_B_MARKET_DATA_SPEC.md:274` states that the research ran on
`COMEX_MINI_DL:MGC1!` and `CME_MINI_DL:MNQ1!`. **That was overstated and is corrected here.**

What the evidence actually supports:

| artifact | prefix recorded | scope of that claim |
|---|---|---|
| `p16/PHASE16_PROTOCOL.md:107` | `MGC1! (COMEX_MINI_DL)`, `MNQ1! (CME_MINI_DL)` | **Phase 16 only** — a forward-looking scope table |
| `PHASE13B_LTF_CONTINUATION_AUDIT.md:125` | `COMEX_MINI_DL:MGC1!` | a Phase 13B **LTF probe**, not a V53 run |
| `HUMAN_TRADE_REGISTER.md:188` | `COMEX_MINI_DL:MGC1!` | an environment note about feed delay |
| earlier generations (`V38_DEPLOYMENT.md`, `V35_EXECUTION_RESULTS.md`, `PHASE2_PROTOCOL.md`, `STATE_OF_PLAY.md`) | `COMEX_MINI:MGC1!`, `CME_MINI:MNQ1!` — **non-`_DL`** | the superseded V11–V38 line |
| **the frozen Phase 13F / 14 / 15 run files** | **none** | `syminfo.ticker` strips the exchange, so every ledger row reads `MGC1!` |

**The exchange prefix used by the frozen V53 runs is therefore UNKNOWN.** Both `_DL` and non-`_DL`
appear in the corpus, for different phases.

*Assessed risk: low but non-zero.* A delayed entitlement is a delivery-latency property, and the
historical bars for a symbol should be identical either way. But TradingView maintains distinct
symbol records for delayed feeds, and it is not established that both carry the same continuous
roll rule. **This must be confirmed by the pull, not assumed.**

### 1.4 Existing symbol-handling capability

There is no stored metadata, but there is an *extraction* capability worth naming, because it is
the mechanism §6 depends on:

- `src/core/chart.js:257 symbolInfo()` calls `chart.symbolExt()` and returns
  `symbol, full_name, exchange, description, type, pro_name, typespecs, resolution, chart_type`.
  **It returns no expiry, no root, no contract month and no adjustment flag** — but it demonstrates
  that TradingView's in-page symbol object is reachable, and the current extraction is a *subset*
  of what that object holds.
- `src/core/chart.js:40 setSymbol()`, `chart.js:25 chart_get_state` — symbol as an opaque string.
- `src/core/chart.js:185` pages history via `requestMoreData(1000)`.
- `src/tools/ui.js:88 ui_evaluate` — arbitrary JS in the page context, i.e. the general-purpose
  route to any chart-model field the typed tools do not expose.

### 1.5 Tests concerning instruments, timestamps or datasets

| test | what it asserts about instruments | roll-aware? |
|---|---|---|
| `bot/tests/test_v53_engine.py` | engine rejects a bar whose `instrument` differs from config; `point_value` must be explicit and positive | no |
| `bot/tests/test_contracts.py` | `instrument` is a non-empty string; nothing more | no |
| `bot/tests/test_golden_fixtures.py` | fixture matrix is exactly 2 × 2 × 2 × 3 | no |
| `trader_v2/p16/test_p16_analyze.py` | instrument ∈ {`MGC1!`, `MNQ1!`}; anything else raises | no |
| `bot/tests/test_calendar.py` | CME **session** semantics — not contract semantics | no |

**No test anywhere is aware of contract rollover.** A roll could occur mid-dataset today and no
test would notice.

---

## 2. TradingView Semantics

Direct fetch of `tradingview.com` is **blocked by this environment's egress proxy**, exactly as
`cmegroup.com` was during U1. The statements below come from search-index summaries of
TradingView's own support and blog pages — *secondary retrieval of primary sources*, not verbatim
primary quotes. They are graded accordingly, and none is treated as settled where it matters.

### VERIFIED (consistent across independent TradingView sources)

| # | statement |
|---|---|
| V-1 | `1!` is the **front / nearest-expiration** continuous contract; `2!` is the second. |
| V-2 | The switching date is set from a **fixed per-symbol rule derived from average volume statistics** — e.g. "switch N business days before expiration" — and **that rule is then applied throughout the symbol's history**. It is *not* a live volume or open-interest crossover evaluated bar by bar. |
| V-3 | Because the rule is an average, TradingView acknowledges the continuous may switch while the old contract still has higher volume, and vice versa. The rule wins; observed volume does not override it. |
| V-4 | **Back-adjustment is DISABLED by default.** |
| V-5 | Back-adjustment is a **chart/display setting**, not intrinsic series data — the `B-ADJ` ("Adjust for contracts changes") button or settings checkbox. |
| V-6 | When enabled, the adjustment is **additive (difference-based)**: the coefficient is the *difference* between the Close of the new and old contracts on the nearest daily bar to the switching point. Not a ratio. |
| V-7 | **Roll dates are surfaced on the continuous chart** — on `ES1!` they are marked by a purple symbol on the date axis. This establishes that roll-date information exists inside the chart and is in principle extractable. |

### INFERRED (reasoned, not directly stated for these symbols)

| # | inference | basis | risk if wrong |
|---|---|---|---|
| I-1 | The frozen V53 research used **unadjusted (raw) prices with roll gaps**, because B-ADJ defaults off and the repository records no instruction to enable it. | V-4, V-5 + absence of any repo mention | **High.** If B-ADJ was on, every historical price in the research is shifted, and a provider's raw series will not reproduce it. |
| I-2 | The `1!` roll rule is applied identically to the `_DL` and non-`_DL` symbol records. | they are the same instrument, differing in entitlement | Low–moderate. |
| I-3 | Both MGC and MNQ rolled at least once inside the research window 2026-05-24 → 2026-08-30. | MNQ M26 expires 2026-06-19 (§3.2) and MGC lists a June contract, both inside the window; V-2's rule rolls *before* expiry | Moderate — if wrong, parity is easier, not harder. |

### UNKNOWN (must not be guessed)

| # | unknown |
|---|---|
| U-1 | **The value of N** in "switch N business days before expiration" for `MGC1!`. |
| U-2 | **The value of N** for `MNQ1!`. TradingView publishes an *illustrative* figure for `ES1!` (~8 days / second Thursday of the expiration month); **`ES1!` is not `MNQ1!`** and that figure must not be transferred. |
| U-3 | The **actual roll dates** for `MGC1!` and `MNQ1!` in the research window. |
| U-4 | The **concrete underlying contract** in force for any bar of the frozen dataset. |
| U-5 | Whether **B-ADJ was on or off** during the Phase 13F/14/15 runs. |
| U-6 | Whether TradingView's rule uses calendar days or business days, and how it treats holidays. |
| U-7 | Whether the `_DL` and non-`_DL` records share a roll rule (I-2 unverified). |
| U-8 | Which exchange prefix the frozen runs actually used (§1.3). |
| U-9 | Whether TradingView's roll rule has ever been revised, and whether a revision would retroactively alter historical bars. |

**U-9 deserves emphasis.** V-2 says the rule is applied throughout history. If TradingView ever
revises a symbol's rule, the *historical* continuous series changes retroactively. That would mean
the frozen research dataset is not reproducible from TradingView at a later date — which is an
argument for exporting and hashing it soon, independent of everything else in Phase B.

---

## 3. Historical Roll Calendar

### 3.1 Status: **UNRESOLVED — no roll dates are asserted**

The calendar cannot be constructed from available evidence. Constructing it would require either
U-1/U-2 (the rule) or U-3 (the observed dates), and neither is obtainable from the repository or
from the public documentation reachable in this environment.

**In accordance with the brief, no roll dates are invented.** The table below is the required
schema with every row unresolved.

| instrument root | TV continuous symbol | underlying concrete contract | effective range (UTC) | roll boundary | source / evidence | status |
|---|---|---|---|---|---|---|
| MGC | `MGC1!` | **UNRESOLVED** | **UNRESOLVED** | **UNRESOLVED** | — | ⛔ blocked on U-1 / U-3 |
| MGC | `MGC1!` | **UNRESOLVED** | **UNRESOLVED** | **UNRESOLVED** | — | ⛔ blocked on U-1 / U-3 |
| MNQ | `MNQ1!` | **UNRESOLVED** | **UNRESOLVED** | **UNRESOLVED** | — | ⛔ blocked on U-2 / U-3 |
| MNQ | `MNQ1!` | **UNRESOLVED** | **UNRESOLVED** | **UNRESOLVED** | — | ⛔ blocked on U-2 / U-3 |

Row count is itself unresolved: the number of transitions inside the window depends on the roll
rule and on MGC's listing behaviour.

### 3.2 Candidate contract universe — **this is NOT a roll calendar**

> **Read this heading literally.** What follows is the set of contracts that *existed* during the
> window, from CME listing conventions. It says nothing about which was *active* in TradingView's
> continuous series on any date. It is included solely so the §6 pull knows what to look for.
> **Substituting CME expiration dates for TradingView roll dates is exactly the error this phase
> exists to prevent.**

**MNQ — Micro E-mini Nasdaq-100 (CME).** CME states the contract is listed on the customary US
equity index quarterly cycle and expires **against the opening index value on the third Friday of
March, June, September and December**.

| contract | third Friday | inside window 2026-05-24 → 2026-08-30? |
|---|---|---|
| `MNQH2026` | 2026-03-20 | before |
| `MNQM2026` | **2026-06-19** | **yes** |
| `MNQU2026` | 2026-09-18 | after |
| `MNQZ2026` | 2026-12-18 | after |

**MGC — Micro Gold (COMEX).** CME states trading is conducted for delivery in **February, April,
June, August, October and December** across the most current 24-month period. Month codes: `G` Feb,
`J` Apr, `M` Jun, `Q` Aug, `V` Oct, `Z` Dec.

| contract | delivery month | expiry date |
|---|---|---|
| `MGCJ2026` | April 2026 | **NOT ASSERTED — termination rule not sourced in this session** |
| `MGCM2026` | June 2026 | **NOT ASSERTED** |
| `MGCQ2026` | August 2026 | **NOT ASSERTED** |
| `MGCV2026` | October 2026 | **NOT ASSERTED** |

The MGC termination rule (commonly the third-last business day of the delivery month for COMEX
gold) was **not verified from a CME source in this session**, so it is deliberately left blank
rather than stated from memory.

### 3.3 What this means for the frozen dataset

Fold A spans **2026-05-24 22:00 → 2026-07-15 23:55**. `MNQM2026` expires 2026-06-19, inside that
span, and under V-2 the continuous rolls *before* expiry. **A roll almost certainly falls inside
fold A for MNQ, and probably for MGC.** Under I-1 (unadjusted), that roll appears in the data as a
price discontinuity.

Why this matters more for V53 than for most strategies — restating from the Phase B spec because
it is the reason B-1 exists: V53 keys off **absolute price levels**. PDH/PDL, 5m swing pivots via
`ta.pivot*(10,10)`, CHOCH and BOS levels, FVG edges, and a stop at the sweep extreme
± 0.20 × ATR(14). A roll gap can manufacture a sweep, orphan a level that no longer exists on the
new contract, and distort ATR for 14 bars afterwards.

**None of this is a defect to fix. It is behaviour to reproduce.** Whatever Pine saw is what Phase
C must feed the Python engine.

---

## 4. Adjustment Mode

| aspect | finding | grade |
|---|---|---|
| default state | **disabled** | **VERIFIED** (V-4) |
| where it lives | a **chart/display setting** (`B-ADJ` button or settings checkbox), not series data | **VERIFIED** (V-5) |
| method when enabled | **additive/difference** — Close(new) − Close(old) on the nearest daily bar to the switch | **VERIFIED** (V-6) |
| **mode used by the frozen research** | **UNKNOWN** (U-5) | ⛔ |
| **whether exported research OHLC is adjusted or raw** | **UNKNOWN** — follows directly from U-5 | ⛔ |
| most likely | **raw / unadjusted**, since the default is off and the repo records no instruction to change it | **INFERRED** (I-1) |

**Required for parity: whichever mode the frozen runs used.** Do not pick on theoretical merit.
The wider trading literature prefers back-adjusted series for continuity, and TradingView community
material argues `B_ADJ` should be ON — **that argument is irrelevant here.** Phase C's job is to
reproduce Pine, not to improve on it. If the research was raw, the parity dataset must be raw.

A useful property of V-6: because the adjustment is *additive*, an adjusted and an unadjusted
series differ by a constant offset within each inter-roll segment. That makes the two empirically
distinguishable — a segment-wise constant difference between a TradingView export and a raw
provider series is the signature of back-adjustment, and its absence is the signature of raw data.
**This is a concrete test, and it means U-5 can be resolved from data alone.**

---

## 5. Concrete-Contract Mapping

Two distinct invariants. They are frequently conflated, and conflating them is how a bot sends an
order to a symbol that does not exist.

### 5.1 Historical (research, replay, Phase C)

```
        MGC1!  /  MNQ1!                 continuous historical symbol
               │
               ▼
   frozen roll calendar (committed)     ← the artifact B-1 must produce
               │
               ▼
   MGCM2026 / MGCQ2026 / MNQM2026 …     concrete CME contract per bar
```

Invariant: **every historical bar in the Phase C dataset must resolve to exactly one concrete
contract**, and that resolution must be reproducible from a committed, version-controlled calendar
— never recomputed at read time from a live source.

### 5.2 Live (execution)

```
   "trade the MGC front month"          live continuous intent
               │
               ▼
   current-contract resolver            ← queries the venue for the active contract
               │
               ▼
   e.g. MGCZ2026                        concrete executable contract
```

### 5.3 The rule that must never be violated

> **`MGC1!` and `MNQ1!` must never be submitted to an execution venue.**
>
> They are TradingView charting constructs. No exchange, broker or clearing house accepts them.
> Every order must name a concrete contract with a real expiry.

Two engineering consequences, recorded now so they are not rediscovered late:

1. **The execution layer needs a contract resolver** with its own roll policy — which may
   legitimately differ from TradingView's charting roll. It is an execution concern, and belongs
   in Phase G, not here.
2. **The `instrument` field is currently a bare string** (`bot/data/bars.py:56`). It carries no
   concrete contract, and nothing validates that it is executable. `ClosedBar.contract` was
   proposed in the Phase B spec for exactly this; B-1 confirms the need but does not implement it.

---

## 6. Required Data Pull

Everything below is **read-only**, touches no strategy artifact, and produces no OOS result. None
of it has been performed — this section defines the work, it does not do it.

### 6.1 From TradingView (primary route — it is the parity oracle)

| # | item | how | resolves |
|---|---|---|---|
| **P-1** | Roll-date markers for `MGC1!` and `MNQ1!` across ≥ 2026-04-01 → 2026-09-01 | V-7 establishes the markers exist on the chart. Extract from the chart model via the CDP bridge (`ui_evaluate`, or a purpose-built read-only extractor) | **U-3** |
| **P-2** | The full `chart.symbolExt()` object for each symbol | `symbolInfo()` today returns a subset (§1.4); dump the whole object and inspect for root, expiry, contract and adjustment fields | **U-4**, partly **U-1/U-2** |
| **P-3** | Current B-ADJ state, and whether it is persisted per layout | read the chart settings model | **U-5** |
| **P-4** | Which exchange prefix the frozen runs used, and whether `_DL` and non-`_DL` roll identically | compare roll markers on `COMEX_MINI:MGC1!` vs `COMEX_MINI_DL:MGC1!` | **U-7**, **U-8** |
| **P-5** | A daily-bar export of `MGC1!`/`MNQ1!` over the window, once with B-ADJ off and once on | the segment-wise constant-offset signature (§4) identifies the mode empirically | **U-5** independently of P-3 |

**Constraint on P-1…P-5:** the chart currently carries the Phase 15 G1 build, and Phase 16
forbids compiling the P16 artifact before the boundary. **This pull must not load, compile or run
any V53 or P16 Pine artifact.** It reads symbol and chart metadata only. Changing the chart symbol
to `MGC1!`/`MNQ1!` for a metadata read is not a strategy run — but it does mutate shared chart
state, so it needs explicit authorisation before it is done.

### 6.2 From CME (secondary — context only, never a substitute)

| # | item | resolves |
|---|---|---|
| **P-6** | The MGC termination rule and the actual last-trade dates for `MGCM2026`, `MGCQ2026`, `MGCV2026` | fills the blanks in §3.2 |
| **P-7** | Confirmation of MNQ third-Friday expiries against the CME calendar | corroborates §3.2 |

**These bound the search; they do not answer it.** A CME expiry is not a TradingView roll date.

### 6.3 From a provider (deferred — Phase B-9, not B-1)

| # | item | resolves |
|---|---|---|
| **P-8** | The provider's available continuous roll rules and their roll dates over the same window | whether any provider rule reproduces TradingView's (Phase B spec Acceptance Test 12) |

### 6.4 The decision gate

If **P-1 and P-3 succeed**, the calendar can be frozen directly from observation, and U-1/U-2
(the rule) become merely explanatory rather than load-bearing.

If **P-1 fails** — the markers are not machine-readable — then the fallback is inference from
data: export daily bars for `MGC1!` alongside each candidate concrete contract
(`MGCM2026`, `MGCQ2026`, …), and identify the date on which the continuous series stops matching
one contract and starts matching the next. **That is observational, not fabricated**, and it is
the honest fallback. It requires the concrete contract symbols to be available on TradingView.

---

## 7. Acceptance Criteria for B-1

| # | criterion | status |
|---|---|---|
| 1 | MGC roll calendar frozen | ⛔ **BLOCKED** — U-1 / U-3 |
| 2 | MNQ roll calendar frozen | ⛔ **BLOCKED** — U-2 / U-3 |
| 3 | Every relevant historical bar can eventually resolve to a concrete contract | ⛔ **BLOCKED** — depends on 1 and 2 |
| 4 | Adjustment semantics documented | 🟡 **PARTIAL** — mechanism and default VERIFIED (§4); the mode actually used is UNKNOWN (U-5) |
| 5 | Unresolved assumptions explicitly identified | ✅ **DONE** — U-1…U-9, I-1…I-3 |
| 6 | No fabricated roll dates | ✅ **DONE** — none asserted anywhere in this document |
| 7 | Calendar committed to the repository | ⛔ **BLOCKED** — nothing to commit yet |
| 8 | Calendar deterministic / version-controlled | 🟡 **schema defined** (§3.1), unpopulated |
| 9 | Phase 16 untouched | ✅ **DONE** — verified by hash, §8 |
| 10 | Repository state audited, not assumed | ✅ **DONE** — §1, including a correction to my own prior spec (§1.3) |
| 11 | TradingView semantics graded VERIFIED / INFERRED / UNKNOWN | ✅ **DONE** — §2 |
| 12 | Concrete-contract mapping invariant defined, both directions | ✅ **DONE** — §5 |
| 13 | Required data pull specified precisely | ✅ **DONE** — §6 |

**7 of 13 complete, 2 partial, 4 blocked. B-1 is NOT complete.** The four blocked criteria all
reduce to a single missing input: the observed roll dates, obtainable via P-1 (or the P-5 fallback).

---

## 8. Verification

| check | result |
|---|---|
| files changed | **1 created**: `docs/PHASE_B1_ROLL_CALENDAR.md`. Zero modified, zero deleted |
| Phase 16 artifacts | untouched — `V53_P16_OOS_BUILD.pine` `5c21acfa…`, protocol, analyser, manifest all unchanged |
| strategy logic | unchanged — `V53_ltf_sequence.pine` `7490766b…`, `V53_EXECUTED_BUILD.pine` `2dafbafd…` |
| live execution code | **none introduced** |
| OOS analysis | **none performed**; no post-FE data inspected |
| TradingView connection | **none made** |
| provider adapter / aggregator (B-2…B-11) | **not started** |

---

## 9. Recommendation

**Authorise a read-only TradingView metadata pull (P-1 through P-5), scoped explicitly to exclude
loading, compiling or running any Pine artifact.** That is the whole of the remaining B-1 work.

Two points worth weighing before B-2:

1. **Export the Phase C dataset soon.** U-9 raises a real possibility that TradingView's continuous
   series is not stable retroactively. The research dataset's reproducibility from TradingView is
   not guaranteed indefinitely, and it is the only source that is *by construction* the series
   Pine ran on.
2. **If P-1 and P-5 both fail**, B-1's honest outcome is a documented inability to establish the
   roll calendar. Phase C would then have to scope Gate 1 parity to a **roll-free sub-window**,
   with the divergence recorded — a smaller Gate 1, but an honest one. That fallback should be
   decided deliberately, not drifted into.

---

## 10. P-1…P-5 READ-ONLY TRADINGVIEW INVESTIGATION

**Authorised:** read-only chart-metadata pull, P-1 through P-5, scoped to exclude loading,
compiling or running any Pine artifact, and to exclude mutating chart state.

> **This section supersedes commit `713a160`.** That commit recorded P-1…P-5 as *blocked on
> infrastructure* after 11 consecutive HTTP 502s at the MCP relay. The relay then recovered under a
> new server binding and the investigation ran. The retry log is retained in §10.9 because it is
> the honest record of what happened, but **the "BLOCKED, nothing retrieved" conclusion in
> `713a160` is wrong and is withdrawn.** Substantial evidence was retrieved; it is below.

### 10.0 Outcome

| P | question | outcome |
|---|---|---|
| **P-1** | roll-date markers for `MGC1!` / `MNQ1!` | 🟡 **PARTIAL** — the switch *mechanism* is now VERIFIED present and enabled on this chart; the switch *dates* are not exposed in the reachable client model. **No roll date is asserted.** |
| **P-2** | full `chart.symbolExt()` | ✅ **RESOLVED** — and it is a **negative** result. A richer object was then found elsewhere and dumped in full. |
| **P-3** | current B-ADJ state | ✅ **RESOLVED** for the live chart — `backAdjustment: false` |
| **P-4** | `_DL` vs non-`_DL` | 🟡 **PARTIAL** — the two are VERIFIED to be one instrument record under two entitlements; identical *roll behaviour* is still inferred, not observed |
| **P-5** | daily-bar export, B-ADJ off vs on | ⛔ **BLOCKED, and now known to be blocked for a new and harder reason** — see U-10 in §10.5 |

**No roll date is asserted anywhere in this section. No CME expiration date has been substituted
for a TradingView roll date.**

### 10.1 Exact symbols

| role | symbol | status |
|---|---|---|
| chart under investigation | **`CME_MINI_DL:MNQ1!`**, resolution `5`, chart type 1 | **VERIFIED** — read, not set. This is the symbol the chart already carried |
| its non-delayed record | `CME_MINI:MNQ1!` | **VERIFIED** to exist as this symbol's `pro_name` / `base_name` |
| gold continuous | `COMEX_MINI:MGC1!` | **VERIFIED** to exist; queried out-of-chart only (§10.4) |

The chart carried three studies: `V53 LTF SEQUENCE` (`0f0OTQ`), `V8.3 XAU - Trend + Range
(cost-hardened)` (`gNx1DZ`), `Volume` (`V8L5rU`). **None was loaded, compiled, run, read or
modified by this investigation** — the study list is a by-product of `chart_get_state`.

**The chart symbol was never changed.** That constrained the whole investigation and is the direct
cause of most of what remains unknown: `MGC1!`'s full symbol record, the roll markers, and P-5 all
require the symbol or the visible range to be changed, which the authorisation excludes.

**U-8 — which prefix the frozen runs used — remains UNKNOWN.** A fresh local re-check confirms the
negative result in §1.1: a sweep for `(COMEX|CME|NYMEX|CBOT)(_MINI)?(_DL)?:` across every file in
`trader_v2/v53_runs/`, `v53_runs_foldc/` and `p15/runs/` returns **zero matches**, because
`syminfo.ticker` strips the prefix. That the live chart sits on the `_DL` record today is a new
data point, and it is **not** proof of what the frozen runs used — the symbol has been changed many
times since.

### 10.2 Metadata discovered

#### 10.2a P-2: `chart.symbolExt()` — a definitive negative

**VERIFIED.** The object has exactly **8** keys:

```
symbol, full_name, exchange, description, type, pro_name, typespecs, delay
```

The only field beyond the 9 that `symbolInfo()` already exposes (§1.4) is `delay: 600`. **There is
no root, expiry, contract-month, front-contract or adjustment field.** M-4 in the earlier draft of
this work asked whether `symbolExt()` carried more than the bridge surfaces; **the answer is no.**
`symbolExt()` cannot answer U-4, and P-2 as originally specified was aimed at the wrong object.

#### 10.2b The right object: `model().mainSeries().symbolInfo()`

**VERIFIED.** This is a different, far richer record — **53 keys** — reached at
`window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().mainSeries().symbolInfo()`.
Values below are for `CME_MINI_DL:MNQ1!` as at 2026-09-07, read verbatim:

| field | value | significance |
|---|---|---|
| `root` | `"MNQ"` | the contract root, **not** previously available |
| `front_contract` | **`"MNQU2026"`** | the concrete contract in force **today** |
| `continuous_order` | `1` | confirms `1!` = front, **VERIFIED** for this symbol (V-1 was documentation) |
| `base_name` | `["CME_MINI:MNQ1!"]` | the non-delayed record |
| `legs` | `["CME_MINI_DL:MNQ1!"]` | single leg — not a spread |
| `has_backadjustment` | `true` | back-adjustment is *supported* |
| `has_adjustment` | `false` | |
| `allowed_adjustment` | `"none"` | **this is the corporate-action (splits/dividends) axis, not futures back-adjustment** — do not confuse the two |
| `bar_source` / `bar_transform` / `bar_fillgaps` | `"trade"` / `"none"` / `false` | bars are trade-based, untransformed, gaps not filled |
| `has_settlement` | `true` | |
| `pointvalue` | **`2`** | |
| `minmov` / `minmove2` / `pricescale` | `25` / `0` / `100` | ⇒ **mintick = 0.25** |
| `session` / `session_display` | **`"1700-1600"`** | |
| `timezone` | **`"America/Chicago"`** | |
| `subsession_id` | `"regular"` | |
| `currency_code` | `"USD"` | |
| `delay` | `600` | 10-minute delayed feed — confirms `_DL` |
| `provider_id` / `source_id` / `listed_exchange` / `pro_perm` | `"ice"` / `"CME_MINI"` / `"CME_MINI"` / `"cme_mini"` | |
| `corrections` | a long holiday / early-close string, quoted in §10.2d | |

**Three findings here are worth more than the roll question they were sought for.**

**(i) `session: "1700-1600"`, `timezone: "America/Chicago"` independently confirms U1.**
`bot/U1_CME_SESSION_CALENDAR.md` established from exchange trade-date rules that the CME trade date
begins **17:00 America/Chicago**, and `bot/calendar/cme.py` encodes exactly that
(`TRADE_DATE_ROLL_HOUR_CT = 17`, `CHICAGO = ZoneInfo("America/Chicago")`). **TradingView's own
symbol record states the identical session and the identical timezone.** U1 was resolved by
reasoning from exchange documentation; it is now corroborated by the platform the frozen research
actually ran on. **VERIFIED.**

**(ii) `pointvalue: 2` resolves B1's U-4 for MNQ.** `bot/contracts/UNRESOLVED.md` carried U-4 as an
open question about `syminfo.pointvalue`. TradingView reports **2** for MNQ, which matches
`POINT_VALUE["MNQ1!"] = Decimal("2")` in `bot/tools/extract_golden.py`. **VERIFIED for MNQ.**
**MGC's `pointvalue` was NOT obtained** (§10.4) — the A2 fixture value of `10` for MGC remains
uncorroborated by TradingView and stays UNKNOWN.

**(iii) `mintick = minmov / pricescale = 25/100 = 0.25` for MNQ.** V53 never reads `syminfo.mintick`
(established in the Phase B spec), so this changes nothing about the strategy — but it is a
required input for the execution layer and it is now evidenced rather than assumed.

#### 10.2c P-3: back-adjustment and related series properties

**VERIFIED**, read from `mainSeries().properties().state()`:

| property | value | meaning |
|---|---|---|
| **`backAdjustment`** | **`false`** | **B-ADJ is OFF on this chart right now** |
| `settlementAsClose` | **`true`** | **new, previously unrecorded**: the daily close is the *settlement* price, not the last trade |
| `sessionId` | `"regular"` | the `1700-1600` session, not extended hours |
| `dividendsAdjustment` | present as a **separate** property | confirms the two adjustment axes are independent |
| `showContinuousContractSwitches` | **`true`** | the roll markers are **enabled** on this chart |
| `showContinuousContractSwitchesBreaks` | `false` | the *breaks* rendering is off |
| `showFuturesContractExpiration` | `true` | |
| `isBackAdjustmentForbiddenProperty()` | `false` | back-adjustment is permitted for this symbol |
| `symbolParams` | `{"symbol":"CME_MINI_DL:MNQ1!","currency":"USD","unit":null,"metric":null,"interval":"5","style":1,"session":"regular"}` | |
| resolved symbol string | `={"adjustment":"splits","currency-id":"USD","session":"regular","symbol":"CME_MINI_DL:MNQ1!"}` | the `"splits"` here is the **corporate-action** axis; it is *not* futures back-adjustment |

**`settlementAsClose: true` is a genuinely new finding and it is not a footnote.** If a provider's
daily bars use last-trade rather than settlement as the close, they will not reproduce TradingView's
daily closes even with the roll calendar solved and back-adjustment matched. This is a new
acceptance requirement for Phase B-9 provider parity that was not in the Phase B spec. Its effect on
the frozen V53 research is **UNKNOWN** — V53 runs on 5m/LTF intrabar data, where the property may
not apply, but that has not been established.

**Grading `backAdjustment: false` correctly.** What is VERIFIED is the state of this chart **now**,
2026-09-07. That the same value held during the Phase 13F/14/15 runs is **INFERRED**, not verified.
The inference is now considerably stronger than I-1 was — it rests on a direct reading of the very
chart (`tradingview.com/chart/2d43Iesr/`) the research ran on, agreeing with V-4's documented
default — but the property is user-toggleable and layout-persisted, and **no history of its value
exists**. **U-5 is therefore downgraded from UNKNOWN to STRONGLY INFERRED, not to VERIFIED.**

#### 10.2d The `corrections` string — an evidenced holiday and early-close calendar

**VERIFIED**, verbatim from the symbol record. This encodes CME/CBOT holiday sessions as
`session-spec:YYYYMMDD,YYYYMMDD;…`. Entries relevant to the research and Phase 16 windows:

| session spec | meaning | dates in/near scope |
|---|---|---|
| `1700-1215` | early close 12:15 CT | `20260703`, `20261224` |
| `1700F2-1200F1,1700-1215` | Thanksgiving pattern | `20261127` |
| `1700F2-1200F1,1700-1600` | full-day holiday closure pattern | `20260120`, `20260217`, **`20260526`**, **`20260908`** |
| `1700F4-1200F3,1700-1600` | | **`20260622`**, **`20260706`** |
| `1700-0815` | | `20260403` |

**This is a directly evidenced replacement for the advisory `CME_FULL_CLOSURES` / `CME_EARLY_CLOSES`
tables in `bot/calendar/cme.py`**, which were marked advisory precisely because they had no
authoritative source. It is quoted here as evidence only; **`bot/calendar/cme.py` was not modified**
— that is B-2 work and is out of scope.

### 10.3 Roll evidence (P-1, P-4)

**NO ROLL DATE IS ASSERTED. U-3 REMAINS UNKNOWN.**

What was established:

| # | finding | grade |
|---|---|---|
| R-1 | This chart has `showContinuousContractSwitches: true`. TradingView models continuous-contract switches as first-class, renderable objects, on **this** symbol — not merely on `ES1!` per documentation | **VERIFIED**. V-7 is upgraded from documentation to observation |
| R-2 | `MNQ1!` resolves to `front_contract: "MNQU2026"` as at 2026-09-07 | **VERIFIED** |
| R-3 | Therefore the MNQ `M2026 → U2026` roll occurred at some point **before 2026-09-07** | **VERIFIED** as a bound — and it is a nearly worthless bound, since it is 9 weeks wide and everyone already believed it. It is recorded because it is the only thing about a *historical* roll that this pass actually evidenced |
| R-4 | The switch **dates** are not present in the reachable client model | **VERIFIED** to the depth searched — see below |
| R-5 | The loaded bar history spans **2026-08-18T04:40Z → 2026-09-07T05:55Z**, 3,880 5m bars, 20.05 days, and contains no roll | **VERIFIED** |

**On R-4, the honest statement of what was searched.** Bars are plain 6-tuples `[time, o, h, l, c,
v]` with no contract field. `timeScale().marks()` returned 31 entries, all of which are time-axis
*labels* (`"17:00"`, `"17:15"`, …) — not switches. A recursive walk of the chart widget to depth 4–5
for property names matching `tickmark|timescalemark|contractswitch|continuouscontract` found only
**settings flags**, never a data store; a walk for `marks|tickMarks|switches|contractSwitches` found
nothing. The series source exposes `requestMoreTickmarks()` and `setFutureTickmarksMode()`, which
implies switch data is **fetched on demand for the visible range**. **R-4 is therefore bounded:
"not reachable at depth 5 with the current 20-day visible range", not "does not exist".** Calling
`requestMoreTickmarks()` or widening the range would change chart state and was not done.

**On P-4.** `pro_name: "CME_MINI:MNQ1!"` and `base_name: ["CME_MINI:MNQ1!"]` on the `_DL` symbol are
**VERIFIED**: TradingView treats `CME_MINI_DL:MNQ1!` as the delayed entitlement view of one
underlying record, with `delay: 600` as the only distinguishing field. That materially strengthens
I-2. It does **not** discharge U-7: identical roll dates were never *observed*, because observing
them requires loading both symbols.

**The critical evidence rule, restated and honoured.** V-2 — that TradingView rolls `1!` on a fixed
per-symbol rule derived from average volume statistics — remains a *rule*. Nothing in this section
converts it into a calendar. `front_contract` is a snapshot, not a history. I-3 (that a roll fell
inside the research window) remains an **inference**.

### 10.4 Adjustment evidence, and the MGC gap

P-3 is answered for the live chart (§10.2c). **P-5 was not performed and is now known to be
harder than blocked-on-permission.** See U-10 below.

`MGC1!` could not be read from the chart without changing the symbol. It was queried out-of-chart
via TradingView's scanner API, which returns only a thin projection:

| field | `COMEX_MINI:MGC1!` | grade |
|---|---|---|
| `root` | `"COMEX_MINI:MGC"` | **VERIFIED** |
| `minmov` / `pricescale` | `1` / `10` ⇒ **mintick 0.1** | **VERIFIED** |
| `timezone` | **`"America/New_York"`** | **VERIFIED** |
| `typespecs` | `["continuous","micro","synthetic"]` | **VERIFIED** |
| `front_contract`, `pointvalue`, `session`, `has_backadjustment`, `allowed_adjustment` | **all returned `null`** — the scanner does not serve them | **UNKNOWN** |

**MGC is stamped `America/New_York`, MNQ `America/Chicago`.** This looks alarming for U1 and is not.
New York and Chicago differ by exactly one hour year-round — both observe US DST on the same dates —
so a COMEX session written `1800-1700` in New York time denotes the **same UTC instants** as
`1700-1600` in Chicago time. `bot/calendar/cme.py`'s single 17:00-CT roll instant therefore remains
correct for both instruments. **However, MGC's actual `session` string was NOT read**, so this
equivalence is **INFERRED** for MGC and **VERIFIED** only for MNQ. Reading MGC's session string
requires loading the symbol.

### 10.5 Unresolved questions after P-1…P-5

| # | unknown | status |
|---|---|---|
| U-1 | roll-rule N for `MGC1!` | **UNKNOWN** — unchanged |
| U-2 | roll-rule N for `MNQ1!` | **UNKNOWN** — unchanged |
| U-3 | **actual roll dates in the research window** | **UNKNOWN** — unchanged. Still the single load-bearing gap |
| U-4 | concrete contract per bar | **UNKNOWN** for history; the **current** front contract is VERIFIED for MNQ (`MNQU2026`) |
| U-5 | B-ADJ during 13F/14/15 | **STRONGLY INFERRED off** — upgraded from UNKNOWN; the live chart reads `backAdjustment: false` |
| U-6 | calendar vs business days, holidays | **partly advanced** — the `corrections` string (§10.2d) gives the evidenced holiday calendar, but not the roll rule's day convention |
| U-7 | `_DL` vs non-`_DL` roll rule | **STRONGLY INFERRED identical** — one record, two entitlements; not observed |
| U-8 | prefix used by the frozen runs | **UNKNOWN** — unchanged, and unanswerable from the run files (§10.1) |
| U-9 | retroactive revision of the roll rule | **UNKNOWN** — unchanged |
| **U-10** | **can the concrete contracts of the research window still be loaded?** | **RESOLVED — and the answer is bad.** See below |
| **U-11** | **MCP relay availability** | **UNKNOWN** — 11 consecutive 502s (§10.9) before recovery under a new binding; three outages now on record |
| **U-12** | **does `settlementAsClose: true` affect the 5m/LTF bars V53 consumed?** | **NEW, UNKNOWN** — §10.2c |

#### U-10 — the P-5 fallback is very likely gone

**VERIFIED**, from TradingView's own contract lists:

- `CME_MINI:MNQ` offers: `MNQ1!`, `MNQ2!`, **`MNQU2026` (Sep 2026)**, `MNQZ2026`, `MNQH2027`,
  `MNQM2027`, `MNQU2027`, `MNQZ2027`. Cycle **H, M, U, Z** (quarterly).
- `COMEX_MINI:MGC` offers: `MGC1!`, `MGC2!`, **`MGCV2026` (Oct 2026)**, `MGCZ2026`, `MGCG2027`,
  `MGCJ2027`, `MGCM2027`, `MGCQ2027`, `MGCV2027`, `MGCZ2027`, `MGCG2028`, `MGCJ2028`, `MGCM2028`.
  Cycle **G, J, M, Q, V, Z** (bi-monthly).
- Direct searches for **`MNQM2026`** and **`MGCQ2026`** return **zero symbols**.

**The contracts that were front-month during the research window 2026-05-24 → 2026-08-30 are no
longer in TradingView's catalog.** §3.2's candidate universe is corrected by this: MGC's cycle is
G/J/M/Q/V/Z as listed above, and the June and August 2026 gold contracts, along with the June 2026
Nasdaq contract, are delisted.

**Grade this precisely.** VERIFIED: those symbols are absent from the search catalog. **UNKNOWN:**
whether the history endpoint still resolves them if requested directly by name — platforms commonly
retain expired-contract data that search no longer surfaces. Testing that requires setting the chart
symbol. **So E-3 is not proven impossible; it is proven not-discoverable-by-search, which is a
weaker but still serious result.** If direct resolution also fails, the observational fallback for
U-3 is gone permanently and §9's roll-free-sub-window recommendation becomes the live option.

This sharpens §9's export-the-dataset-soon recommendation into something closer to urgent: the
concrete contracts underlying the frozen research have **already** aged out of the catalog in the
seven days since FE.

### 10.6 Updated B-1 acceptance checklist

| # | criterion | before | after |
|---|---|---|---|
| 1 | MGC roll calendar frozen | ⛔ BLOCKED | ⛔ **BLOCKED** — no roll date evidenced |
| 2 | MNQ roll calendar frozen | ⛔ BLOCKED | ⛔ **BLOCKED** — only the bound "before 2026-09-07" (R-3) |
| 3 | Every relevant bar resolves to a concrete contract | ⛔ BLOCKED | ⛔ **BLOCKED** — downstream of 1 and 2 |
| 4 | Adjustment semantics documented | 🟡 PARTIAL | ✅ **DONE** — mechanism VERIFIED, live state VERIFIED (`backAdjustment: false`), historical state strongly inferred, and the separate `settlementAsClose` axis newly documented |
| 5 | Unresolved assumptions identified | ✅ DONE | ✅ **DONE** — extended with U-10, U-11, U-12 |
| 6 | No fabricated roll dates | ✅ DONE | ✅ **DONE** — none asserted; no CME expiry substituted |
| 7 | Calendar committed | ⛔ BLOCKED | ⛔ **BLOCKED** — nothing to commit |
| 8 | Calendar deterministic / version-controlled | 🟡 schema defined | 🟡 **unchanged**, unpopulated |
| 9 | Phase 16 untouched | ✅ DONE | ✅ **DONE** — hashes re-verified, §10.8 |
| 10 | Repository state audited | ✅ DONE | ✅ **DONE** — prefix sweep re-run |
| 11 | Semantics graded | ✅ DONE | ✅ **DONE** — applied throughout §10 |
| 12 | Contract-mapping invariant defined | ✅ DONE | ✅ **DONE** |
| 13 | Required data pull specified | ✅ DONE | ✅ **DONE** — rewritten as §10.7 against observed platform behaviour |

**8 of 13 complete, 1 partial, 4 blocked** (was 7 / 2 / 4). Criterion 4 moved to complete. **The
four roll-calendar criteria are unchanged, and B-1 is still not complete.**

The honest summary: this pass resolved the *adjustment* half of B-1, corroborated U1 from the
platform itself, resolved B1's U-4 for MNQ, produced an evidenced holiday calendar, surfaced a new
provider-parity requirement (`settlementAsClose`), and discovered that the observational fallback for
the roll calendar is disappearing. It did **not** move the roll calendar itself one day closer to
being frozen.

### 10.7 Exact evidence still required

Every remaining item needs **one narrow authorisation the current one withholds: permission to
change the chart's symbol, resolution and visible range**, and to restore them afterward. That is
the whole gate. Nothing below needs a Pine artifact loaded, compiled or run.

| # | required evidence | closes | acceptance test |
|---|---|---|---|
| **E-1′** | With `MGC1!` loaded: the full `mainSeries().symbolInfo()` dump, as §10.2b for MNQ | MGC's `session`, `pointvalue`, `front_contract`, `root`, `corrections` | the 53-key object quoted verbatim |
| **E-2′** | Set resolution to `D`, widen the visible range to cover ≥ 2026-03-01 → 2026-09-01, call `requestMoreTickmarks()`, then re-walk the model for switch marks | **U-3**, if the marks are client-readable | each switch as an extracted timestamp **plus the model path it came from**. A screenshot is **not** sufficient |
| **E-3′** | *If E-2′ fails:* attempt to load `CME_MINI:MNQM2026` and `COMEX_MINI:MGCQ2026` **by direct symbol entry** | **U-10** definitively | either bars return (and E-3 below is live), or an explicit resolve error |
| **E-3** | *If E-3′ succeeds:* daily bars for `MGC1!`/`MNQ1!` and each concrete contract over 2026-03-01 → 2026-08-30, **forming bar dropped** | **U-3** observationally | the date the continuous stops matching contract *k* and starts matching *k+1*, shown bar-by-bar for ≥ 3 bars either side |
| **E-5** | Toggle `backAdjustment` on, re-read daily bars across a **known** roll, toggle back off | **U-5** independently of the current-state read | a segment-wise **constant additive** offset in exactly one series (§4) |
| **E-6** | Load `COMEX_MINI:MGC1!` and `COMEX_MINI_DL:MGC1!`, extract switch marks on both, diff | **U-7**; makes U-8 moot **only if identical** | both mark sets extracted and diffed |
| **E-7** | Compare 5m bars against daily bars around a session close on the same instrument | **U-12** — whether `settlementAsClose` touches intraday data | whether the 5m close at 16:00 CT equals the daily close for that trade date |

**A caution about E-5 that applies to all of these.** Toggling `backAdjustment` mutates a
layout-persisted property on the chart that carries the V53 studies. It must be restored, and the
restoration must be **verified by re-reading the property**, not assumed. The safest sequencing is
to do all of E-1′…E-7 on a **separate layout or tab**, leaving `2d43Iesr` untouched.

**Two things this must never become.** A CME expiration date is not a TradingView roll date, and
E-3 remains the only sanctioned substitute for E-2′. If E-2′, E-3′ and E-3 all fail, the honest
outcome is §9's second recommendation — scope Phase C Gate 1 parity to a **roll-free sub-window**
and record the reduction explicitly. That is the user's decision to take deliberately.

### 10.8 Verification of this investigation

| check | result |
|---|---|
| chart symbol changed | **no** — read at `CME_MINI_DL:MNQ1!`, left there |
| chart resolution / visible range / settings changed | **no** |
| Pine artifact loaded, compiled, run or read | **none** — no `pine_*` tool was invoked, and no `pine_*` schema was loaded into this session |
| studies on the chart | untouched; listed only as a by-product of `chart_get_state` |
| write-capable tools invoked | **none** — only `tv_health_check`, `chart_get_state`, `symbol_info`, `symbol_search`, `ui_evaluate` |
| `ui_evaluate` side effects | five temporary `window.__b1*` variables held fetch results; **all deleted, deletion verified** (`leftover: []`). No chart-model object was written to |
| network reads initiated | TradingView's own public `symbol-search` and `scanner` endpoints, from the page's origin. Read-only GETs |
| post-FE data | the live chart necessarily exposed current prices (the last 5m bar, 2026-09-07). **No post-FE price data was collected, stored, or analysed; no strategy evaluation or OOS analysis of any kind was performed** |
| roll date asserted | **none** |
| CME expiry substituted for a roll date | **no** |
| Phase 16 artifacts | unchanged — `sha256sum -c` OK: `V53_P16_OOS_BUILD.pine` `5c21acfa…`, `PHASE16_PROTOCOL.md` `c5b6c853…`, `p16_analyze.py` `588eb9d0…` |
| V53 artifacts | unchanged — `V53_ltf_sequence.pine` `7490766b…`, `V53_EXECUTED_BUILD.pine` `2dafbafd…` |
| strategy / execution / data-architecture code | **not modified** |
| `bot/calendar/cme.py` | **not modified**, though §10.2d supplies evidence that would improve it — that is B-2 work |
| Databento / provider adapter / aggregator | **not started** |
| files changed | **1**: `docs/PHASE_B1_ROLL_CALENDAR.md` |

### 10.9 Relay retry log (retained)

Before recovery, the MCP relay returned Cloudflare **HTTP 502 `origin_bad_gateway`**, zone
`api.anthropic.com` — the **relay**, not TradingView. 11 attempts, 2 distinct tools, ~21 minutes.

| # | time (UTC) | wait | tool | ray id |
|---|---|---|---|---|
| 1 | 05:35:21 | — | `tv_health_check` | `a373597be9aa72e5` |
| 2 | 05:35:40 | 19s | `tv_health_check` | `a37359f1cf7e9991` |
| 3 | 05:36:03 | 23s | `tv_health_check` | `a3735a83a8ee2234` |
| 4 | 05:36:43 | 40s | `tv_health_check` | `a3735b7d9c6d98b8` |
| 5 | 05:39:57 | 194s | `tv_health_check` | `a37360386c02866c` |
| 6 | 05:41:19 | 82s | `tv_health_check` | `a373623bec60dc1f` |
| 7 | 05:46:25 | 306s | `tv_health_check` | `a37369b52df83457` |
| 8 | 05:46:30 | 5s | **`symbol_search`** | `a37369d22a02c0f3` |
| 9 | 05:54:23 | 473s | `tv_health_check` | `a373755da866b002` |
| 10 | 05:55:41 | 78s | `tv_health_check` | `a37377455c6f226a` |
| 11 | 05:56:37 | 56s | `tv_health_check` | `a37378a2dce9508f` |

Recovery came from the MCP server being re-bound (server `f` disconnected; server `r` connected),
**not** from further waiting — matching `trader_v2/RELAY_OUTAGE.md`'s conclusion that this failure
mode needs the connector re-established rather than more backoff. That is U-11: with three outages
now on record and TradingView acting as the Phase C parity oracle, **oracle availability is itself a
project risk**, and it is a second independent argument for exporting and hashing the research
dataset promptly.

---

## P-6 / E-1′…E-7′ HISTORICAL ROLL-EVIDENCE INVESTIGATION

**Authorised:** controlled read-only TradingView navigation — symbol, resolution, visible range,
history requests, model inspection — **on a separate investigation layout only**.

> **This section resolves the roll calendar.** §3.1 previously stated "no roll dates are asserted".
> That is now superseded: the roll dates below are **observed**, by two independent methods that
> agree exactly. §10.5's pessimistic reading of U-10 is also **withdrawn** — see E-4′.

### P-6.0 Isolation — how the frozen chart was protected, and one thing that did happen

| step | action | evidence |
|---|---|---|
| 1 | Recorded the frozen chart's state **before** anything: `CME_MINI_DL:MNQ1!`, resolution `5`, chartType `1`, studies `V53 LTF SEQUENCE` (`0f0OTQ`), `V8.3 XAU - Trend + Range (cost-hardened)` (`gNx1DZ`), `Volume` (`V8L5rU`) | `chart_get_state` |
| 2 | Created a **new layout in a new tab**: `B1 ROLL INVESTIGATION`, chart id **`P2NtY6fg`** | `tab_new{layout:"new"}` → `{chart_id:"P2NtY6fg"}` |
| 3 | Confirmed the CDP target re-pinned to `P2NtY6fg` | `tv_health_check` → `target_url: .../chart/P2NtY6fg/` |
| 4 | **Every** subsequent evaluation opened with a hard guard: `if (location.href.indexOf('2d43Iesr') !== -1) return {ABORT:1}` | present in every `ui_evaluate` below; it never fired |
| 5 | All symbol/resolution/property writes ran against `P2NtY6fg`, each returning its own href | e.g. `set backAdjustment=true on https://www.tradingview.com/chart/P2NtY6fg/` |

**What did happen, stated plainly.** Creating the new layout **navigated the tab that was showing
`2d43Iesr` away from it** — after `tab_new`, `tab_list` no longer showed a `2d43Iesr` target. This
was not intended and is worth recording rather than glossing. It is a *navigation*, not an edit: no
mutating call was ever issued while the bridge was pinned to that chart.

**It was then verified recoverable and unchanged.** `2d43Iesr` was reopened in its own tab and read
back:

| property | at session start | after the investigation |
|---|---|---|
| symbol | `CME_MINI_DL:MNQ1!` | `CME_MINI_DL:MNQ1!` |
| resolution / `interval` | `5` | `5` |
| chartType | `1` | `1` |
| studies (name + entity id) | `0f0OTQ`, `gNx1DZ`, `V8L5rU` | `0f0OTQ`, `gNx1DZ`, `V8L5rU` — **identical ids** |
| `backAdjustment` | `false` | `false` |
| `settlementAsClose` | `true` | `true` |
| `sessionId` | `regular` | `regular` |

**VERIFIED: the frozen chart is intact, down to identical study entity IDs.** No Pine artifact was
loaded, compiled, executed or read on it; no study added or removed; no setting changed.

**A caution for the next session.** The bridge's fallback target selector picks the *first*
`tradingview.com/chart` target it finds, which can be `2d43Iesr`. If the MCP server restarts, the
pin is lost and the next call may land on the frozen chart. The `location.href` guard used
throughout this section is the mitigation and should be kept in any future navigation work.

### E-1′ — Historical switch-marker accessibility

**Method.** On `P2NtY6fg`: set resolution `D` (loading 300 daily bars, 2025-06-30 → 2026-09-06,
covering the whole research window), then enumerate the chart model's data sources rather than
walking the object graph blindly.

**Exact object inspected.**
`window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().dataSources()`

**Observation.** The daily chart carries a source list that includes two futures-specific entries
that the 5m chart's property flags only hinted at:

```
cd|Crosshair            Is|MNQ1! · CME, 1D      O|Ideas on chart       o|Vol (false)
oe|Dividends            ae|Splits               le|Earnings
B|RollDatesCalculator (now)      H|FuturesContractExpiration
X|LatestUpdatesSource   te|Chart Events
```

**`RollDatesCalculator` is the object §10.3 could not find.** Its output lives in `_data`, a
standard bar-series container whose rows are:

```
[ unix_seconds , old_contract_YYYYMM , new_contract_YYYYMM , trade_date_YYYYMMDD , …nulls… , 0 ]
```

**Evidence.** `src._data.each(...)` returned **34 rows for MNQ** (2019-06 → 2027-09) and **88 rows
for MGC** (2010-12 → 2028-03). Raw sample, verbatim:

```
-1000123|1560808800|201906|201909|20190618
       241|1781474400|202606|202609|20260615
       304|1789423200|202609|202612|20260915
```

**Status: VERIFIED.** Switch markers are machine-readable, exposed as a first-class chart data
source, and available for the **entire** history — not merely the visible window. §10.3's R-4
("not reachable at depth 5") was correct only because the 5m chart's 20-day range and the object-graph
walk both missed a source that is enumerable directly.

**Implication for B-1.** This is the primary input criteria 1–3 were blocked on.

### E-2′ — MGC historical roll evidence

**Method.** Set symbol to `COMEX_MINI:MGC1!` on `P2NtY6fg`; re-read `symbolInfo()` and the
`RollDatesCalculator`.

**Exact objects inspected.** `mainSeries().symbolInfo()`; `RollDatesCalculator._data` (88 rows).

**Observation — MGC symbol record (the §10.4 gap, now closed):**

| field | value | note |
|---|---|---|
| `full_name` / `pro_name` | `COMEX_MINI_DL:MGC1!` / `COMEX_MINI:MGC1!` | |
| `root` | `MGC` | |
| `front_contract` | **`MGCZ2026`** | |
| **`pointvalue`** | **`10`** | **E-5′ — see below** |
| `minmov` / `pricescale` | `1` / `10` ⇒ **mintick 0.1** | |
| **`session`** | **`1800-1700`** | |
| `timezone` | `America/New_York` | |
| `has_backadjustment` / `allowed_adjustment` | `true` / `none` | as MNQ |
| `backAdjustment` / `settlementAsClose` | `false` / `true` | as MNQ |

**§10.4's inference is now VERIFIED.** MGC's session is `1800-1700` **America/New_York**, which is
the *same instants* as MNQ's `1700-1600` **America/Chicago**. The two instruments share one
trade-date boundary, and `bot/calendar/cme.py`'s single 17:00-CT roll instant is correct for both.
This was INFERRED in §10.4; it is now observed.

**Observation — MGC roll calendar (rolls from 2025-01, trade dates):**

| effective (UTC) | effective (CT) | trade date | from | to |
|---|---|---|---|---|
| 2025-01-29 23:00Z | 2025-01-29 17:00 CST | 2025-01-30 | `MGCG2025` | `MGCJ2025` |
| 2025-03-27 22:00Z | 2025-03-27 17:00 CDT | 2025-03-28 | `MGCJ2025` | `MGCM2025` |
| 2025-05-28 22:00Z | 2025-05-28 17:00 CDT | 2025-05-29 | `MGCM2025` | `MGCQ2025` |
| 2025-07-29 22:00Z | 2025-07-29 17:00 CDT | 2025-07-30 | `MGCQ2025` | `MGCZ2025` |
| 2025-11-25 23:00Z | 2025-11-25 17:00 CST | 2025-11-26 | `MGCZ2025` | `MGCG2026` |
| 2026-01-28 23:00Z | 2026-01-28 17:00 CST | 2026-01-29 | `MGCG2026` | `MGCJ2026` |
| 2026-03-29 22:00Z | 2026-03-29 17:00 CDT | 2026-03-30 | `MGCJ2026` | `MGCM2026` |
| **2026-05-27 22:00Z** | **2026-05-27 17:00 CDT** | **2026-05-28** | **`MGCM2026`** | **`MGCQ2026`** |
| **2026-07-29 22:00Z** | **2026-07-29 17:00 CDT** | **2026-07-30** | **`MGCQ2026`** | **`MGCZ2026`** |
| 2026-11-25 23:00Z | 2026-11-25 17:00 CST | 2026-11-27 | `MGCZ2026` | `MGCG2027` |

**Two structural findings.**

1. **MGC's continuous cycle is G, J, M, Q, Z — five rolls a year, and it SKIPS V (October).**
   Both 2025 and 2026 go `Q → Z` directly. §3.2 listed `MGCV2026` as a candidate front contract;
   **it is never the front month of `MGC1!`**, even though it is a listed contract. That correction
   matters: a provider rule that includes October would not reproduce TradingView's series.
2. **The last row is a holiday cross-check.** `2026-11-25 17:00 CST` carries trade date
   **`20261127`**, not `20261126`, because 2026-11-26 is Thanksgiving — and `20261127` appears in
   the symbol record's own `corrections` string (§10.2d). The field is a genuine exchange trade
   date, holiday-aware, not a naive calendar offset. **This independently validates the semantics
   of the whole table.**

**Status: VERIFIED.** Fold A is covered, and so is the entire research window.

### E-3′ — MNQ historical roll evidence

**Method.** As E-2′, on `CME_MINI:MNQ1!`.

**Observation — MNQ roll calendar (rolls from 2025-03, trade dates):**

| effective (UTC) | effective (CT) | trade date | from | to |
|---|---|---|---|---|
| 2025-03-17 22:00Z | 2025-03-17 17:00 CDT | 2025-03-18 | `MNQH2025` | `MNQM2025` |
| 2025-06-15 22:00Z | 2025-06-15 17:00 CDT | 2025-06-16 | `MNQM2025` | `MNQU2025` |
| 2025-09-15 22:00Z | 2025-09-15 17:00 CDT | 2025-09-16 | `MNQU2025` | `MNQZ2025` |
| 2025-12-15 23:00Z | 2025-12-15 17:00 CST | 2025-12-16 | `MNQZ2025` | `MNQH2026` |
| 2026-03-16 22:00Z | 2026-03-16 17:00 CDT | 2026-03-17 | `MNQH2026` | `MNQM2026` |
| **2026-06-14 22:00Z** | **2026-06-14 17:00 CDT** | **2026-06-15** | **`MNQM2026`** | **`MNQU2026`** |
| 2026-09-14 22:00Z | 2026-09-14 17:00 CDT | 2026-09-15 | `MNQU2026` | `MNQZ2026` |
| 2026-12-14 23:00Z | 2026-12-14 17:00 CST | 2026-12-15 | `MNQZ2026` | `MNQH2027` |

**MNQ's cycle is H, M, U, Z — quarterly, no skips.**

**The instruction not to reason from `front_contract` was correct, and the table honours it.** The
2026-09-15 row is *in the future* and says `MNQU2026 → MNQZ2026`, which is exactly why
`front_contract` reads `MNQU2026` today (2026-09-07). That is a **consistency check on the table**,
not the source of the historical date. The historical M→U date comes from the table and from the
price identity in E-3′b — never from the current front contract.

#### E-3′b — Independent confirmation by bar-level price identity

This is the `continuous → old contract → new contract → exact switch date` chain, closed
observationally. Daily bars, `backAdjustment = false`. Bar timestamps are session-open instants
(22:00Z = 17:00 CT), so the bar stamped `2026-05-27T22:00` **is** trade date 2026-05-28.

**MGC, around the predicted 2026-05-28 switch:**

| bar (UTC) | `MGC1!` OHLC | matches |
|---|---|---|
| 2026-05-24 22:00 | `O4530.2 H4583.2 L4480.1 C4502.3` | **`MGCM2026` exactly** |
| 2026-05-26 22:00 | `O4504 H4527.9 L4398.4 C4448.4` | **`MGCM2026` exactly** |
| **2026-05-27 22:00** | `O4487.7 H4547.4 L4395.8 C4532.4` | **`MGCQ2026` exactly** ← switch |
| 2026-05-28 22:00 | `O4527.7 H4627.3 L4519.1 C4593` | **`MGCQ2026` exactly** |

For contrast, `MGCM2026`'s own 2026-05-27 bar is `O4453.1 H4511.5 L4364 C4499.3` — the two
contracts differ by roughly 34 points, so the match is unambiguous.

**MNQ, around the predicted 2026-06-15 switch:**

| bar (UTC) | `MNQ1!` OHLC | `MNQM2026` | `MNQU2026` |
|---|---|---|---|
| 2026-06-11 22:00 | `O29450 H29759.25 L29231.25 C29662` | **identical** | differs (`C29954.75`) |
| **2026-06-14 22:00** | `O30100 H30918.5 L30100 C30864.25` | differs (`O29826.25 C30559.25`) | **identical** ← switch |
| 2026-06-17 22:00 | `O30146 H30783.25 L30092.25 C30719.75` | differs | **identical** |

**Status: VERIFIED, by two independent methods that agree exactly.** The `RollDatesCalculator`
timestamps and the bar-level price identity give the same switch dates for both instruments. Note
also that the pre-roll continuous bars equal the **old contract's raw prices** — no offset — which is
a behavioural confirmation that back-adjustment is off (see E-7′).

#### Rolls inside the frozen research window

Research window 2026-05-24 → 2026-08-30; folds per the frozen definitions.

| fold | span | rolls inside |
|---|---|---|
| **A** | 2026-05-24 → 2026-07-15 | **MGC `MGCM2026 → MGCQ2026` on 2026-05-28**; **MNQ `MNQM2026 → MNQU2026` on 2026-06-15** |
| **B** | 2026-07-16 → 2026-08-07 | **MGC `MGCQ2026 → MGCZ2026` on 2026-07-30** |
| **C** | 2026-08-09 → 2026-08-30 | **none** |

**I-3 is now VERIFIED** — rolls did occur inside the research window; there are **three** of them,
and the first lands only four days after Fold A opens. Fold C is roll-free.

### E-4′ — Direct historical-contract resolution

**Method.** Set the symbol directly, by name, to contracts that returned **zero results** from
search in §10.5.

**Observation.**

| symbol | resolved? | resolved name | `expiration` | `typespecs` | daily bars |
|---|---|---|---|---|---|
| `CME_MINI:MNQM2026` | **yes** | `CME_MINI_DL:MNQM2026` | `20260618` | `["micro","expired","dynamic"]` | 300, 2025-04-09 → **2026-06-17** |
| `COMEX_MINI:MGCQ2026` | **yes** | `COMEX_MINI_DL:MGCQ2026` | `20260827` | `["micro","expired","dynamic"]` | 300, 2025-06-17 → **2026-08-26** |
| `COMEX_MINI:MGCM2026` | **yes** | `COMEX_MINI_DL:MGCM2026` | `20260626` | — | to **2026-06-25** |
| `CME_MINI:MNQU2026` | **yes** | `CME_MINI_DL:MNQU2026` | `20260918` | `["micro","dynamic"]` (no `expired`) | live |

**Status: VERIFIED — and §10.5's U-10 conclusion is WITHDRAWN.** Expired contracts resolve fully,
carry complete history, and expose an **`expiration`** field that the continuous symbol does not.
Search-catalog absence did **not** mean symbol absence. §10.5 graded this correctly as UNKNOWN
rather than asserting impossibility; that caution was warranted, and the pessimistic framing
("the fallback is disappearing") was wrong.

**Implication for B-1.** The observational fallback is fully available, which is why E-3′b could be
run at all — it is now corroboration rather than fallback.

### E-5′ — MGC pointvalue

**Method.** Read `mainSeries().symbolInfo().pointvalue` with `MGC1!` actually loaded — not from the
scanner projection that returned `null` in §10.4, and not from a fixture constant.

**Observation.** **`pointvalue = 10`** for `COMEX_MINI_DL:MGC1!`; also `10` on the concrete
`MGCQ2026` and `MGCM2026`. MNQ remains `2`.

**Status: VERIFIED.** This matches `POINT_VALUE = {"MGC1!": Decimal("10"), "MNQ1!": Decimal("2")}`
in `bot/tools/extract_golden.py`. The fixture constants are now corroborated by the platform for
**both** instruments; **B1's U-4 is fully resolved.**

### E-6′ — `_DL` parity

**Method.** Request the non-delayed record explicitly and compare.

**Observation.** **Every** non-`_DL` request silently resolved to the `_DL` record:

| requested | resolved (`full_name`) |
|---|---|
| `CME_MINI:MNQ1!` | `CME_MINI_DL:MNQ1!` |
| `COMEX_MINI:MGC1!` | `COMEX_MINI_DL:MGC1!` |
| `CME_MINI:MNQM2026` | `CME_MINI_DL:MNQM2026` |
| `COMEX_MINI:MGCQ2026` | `COMEX_MINI_DL:MGCQ2026` |

`pro_name` keeps the non-`_DL` name, `pro_perm` is `cme_mini`, `delay` is `600`. The account lacks
the real-time entitlement, so the platform substitutes the delayed record.

**Status: split, deliberately.**

- **VERIFIED:** this account **cannot obtain a distinct non-`_DL` series at all**. The two views
  cannot be compared, because only one of them is reachable.
- **UNKNOWN — and it stays UNKNOWN:** whether `_DL` and non-`_DL` have identical *historical* roll
  behaviour. It was never observed, and identical underlying records do **not** license the
  inference. §10.3's "STRONGLY INFERRED identical" was over-graded and is **downgraded to UNKNOWN**.

**Implication for U-8, which is the point.** If the account can only ever resolve `_DL`, the frozen
13F/14/15 runs necessarily ran on `_DL`, whatever prefix was typed — `syminfo.ticker` stripped it,
which is why the run files are silent. **U-8 is therefore STRONGLY INFERRED as `_DL`**, resting on a
verified entitlement constraint rather than on a guess. It is not VERIFIED, because entitlements can
change and no record of the entitlement at run time exists.

### E-7′ — Adjustment / historical-series evidence

**Method.** On `P2NtY6fg` only, with `MNQ1!` daily: read bars, set
`mainSeries().properties().childs().backAdjustment.setValue(true)`, re-read the same bars, restore
`false`, re-read again to confirm restoration. **The frozen chart's setting was never touched.**

**Observation.**

| bar (UTC) | `backAdjustment = false` | `backAdjustment = true` | delta |
|---|---|---|---|
| 2026-06-09 22:00 | `O29102 … C28554` | `O29394.75 … C28846.75` | **+292.75** |
| 2026-06-10 22:00 | `O28458 … C29464.75` | `O28750.75 … C29757.5` | **+292.75** |
| 2026-06-11 22:00 | `O29450 … C29662` | `O29742.75 … C29954.75` | **+292.75** |
| **2026-06-14 22:00** (roll) | `O30100 H30918.5 L30100 C30864.25` | **identical** | **0** |
| 2026-06-17 22:00 | `O30146 … C30719.75` | **identical** | **0** |

**Four things are now VERIFIED rather than documented:**

1. Back-adjustment is **additive**, not multiplicative — a constant **+292.75** across O, H, L and C.
2. The offset is applied to **pre-roll** bars only; post-roll bars are untouched.
3. The offset equals the **contract spread at the switch**: `MNQU2026` close 29954.75 −
   `MNQM2026` close 29662 on 2026-06-11 = **292.75** exactly. V-6's stated rule is confirmed
   empirically.
4. With `backAdjustment = false`, the continuous bars equal the **old contract's raw prices**
   (E-3′b). **The series the research consumed is raw, with roll gaps intact.**

**Adjustment state is per-chart and persisted.** It lives in `mainSeries().properties()`, part of
the saved layout — a **brand-new** layout (`P2NtY6fg`, created empty in this session) also defaults
to `backAdjustment: false`, `settlementAsClose: true`. That the frozen chart carries the same values
is therefore the platform default, not a deliberate historical toggle.

**Restoration verified, not assumed.** After restoring, `backAdjustment = false` and the
2026-06-11 close read back as **29662** — the raw value.

**Status on U-5: STRONGLY INFERRED — deliberately NOT upgraded to VERIFIED.** Three independent
observations now support "the frozen research ran unadjusted": the platform default, the frozen
chart's current state, and the new layout's default. But **the historical state of the property
during the 13F/14/15 runs is not exposed anywhere**, and no amount of present-tense evidence can
establish a past setting. It stays STRONGLY INFERRED.

**No evidence was found that adjustment state differs by symbol** — MGC and MNQ both read `false`
with `has_backadjustment: true` and `allowed_adjustment: "none"`.

### P-6.1 Newly VERIFIED facts

1. `RollDatesCalculator` is an enumerable chart data source exposing the **complete** roll history
   (MNQ 34 rows from 2019-06; MGC 88 rows from 2010-12).
2. **MNQ roll `MNQM2026 → MNQU2026`, trade date 2026-06-15**, effective 2026-06-14 22:00Z.
3. **MGC roll `MGCM2026 → MGCQ2026`, trade date 2026-05-28**, effective 2026-05-27 22:00Z.
4. **MGC roll `MGCQ2026 → MGCZ2026`, trade date 2026-07-30**, effective 2026-07-29 22:00Z.
5. Both confirmed independently by **bar-level price identity** against the concrete contracts.
6. **Every** roll instant is exactly **17:00 America/Chicago** — a third independent confirmation
   of U1's trade-date boundary.
7. MGC continuous cycle **G, J, M, Q, Z** — **October (V) is skipped**. MNQ cycle **H, M, U, Z**.
8. **MGC `pointvalue = 10`**; MNQ `pointvalue = 2`. B1's U-4 fully resolved.
9. MGC `session = 1800-1700`, `timezone = America/New_York` — the same instants as MNQ's
   `1700-1600` America/Chicago.
10. MGC `minmov/pricescale = 1/10` ⇒ **mintick 0.1**; MNQ `25/100` ⇒ **0.25**.
11. Expired contracts **resolve directly** with full history and expose an `expiration` field
    (`MNQM2026` 20260618, `MGCM2026` 20260626, `MGCQ2026` 20260827, `MNQU2026` 20260918).
12. Back-adjustment is **additive**, pre-roll only, offset = contract spread at the switch
    (**+292.75** for the MNQ M→U roll).
13. `backAdjustment: false` and `settlementAsClose: true` are **platform defaults** on a
    brand-new layout.
14. This account cannot resolve any non-`_DL` record; all requests fall back to `_DL`.
15. Fold C (2026-08-09 → 2026-08-30) is **roll-free**.
16. The roll table's trade dates are **holiday-aware** (the 2026-11-27 Thanksgiving row agrees with
    the symbol record's own `corrections` string).

### P-6.2 Remaining UNKNOWNs

| # | unknown | why it stays unknown |
|---|---|---|
| U-1 / U-2 | the roll **rule** (the N in "N days before expiry") | never needed now — the observed calendar supersedes it. Deriving N from 122 observed rolls would be *inference from* the answer, not evidence, and is not attempted here |
| U-5 | B-ADJ **during** the 13F/14/15 runs | historical property state is not exposed. **STRONGLY INFERRED off** |
| U-6 | calendar vs business days, holiday convention **of the rule** | moot for the calendar; the observed dates are holiday-aware |
| U-7 | `_DL` vs non-`_DL` historical roll parity | **UNKNOWN — downgraded from §10.3.** The non-`_DL` series is unreachable, so it cannot be observed |
| U-8 | prefix used by the frozen runs | **STRONGLY INFERRED `_DL`** via the entitlement constraint (E-6′); not verifiable |
| U-9 | whether TradingView ever revised the rule retroactively | not exposed. The calendar should be **frozen into the repository** rather than re-read later |
| U-12 | whether `settlementAsClose` affects the 5m/LTF bars V53 consumed | not tested — it needs an intraday-vs-daily close comparison, which is E-7 in §10.7 and was not part of P-6 |
| U-13 | **NEW** — whether TradingView's roll dates are identical on the `1!` series at **intraday** resolutions | the entire investigation ran on daily bars. The roll instant is a session boundary, so agreement is expected, but it was not observed |

### P-6.3 Updated B-1 acceptance matrix

| # | criterion | after P-1…P-5 | **after P-6** |
|---|---|---|---|
| 1 | MGC roll calendar frozen | ⛔ BLOCKED | ✅ **DONE** — observed, dual-method, holiday-aware |
| 2 | MNQ roll calendar frozen | ⛔ BLOCKED | ✅ **DONE** — observed, dual-method |
| 3 | Every relevant bar resolves to a concrete contract | ⛔ BLOCKED | ✅ **DONE** — the tables map every bar of the research window to a named contract |
| 4 | Adjustment semantics documented | ✅ DONE | ✅ **DONE** — now demonstrated empirically (additive, +292.75) |
| 5 | Unresolved assumptions identified | ✅ DONE | ✅ **DONE** — U-13 added; U-7 downgraded; U-10 withdrawn |
| 6 | No fabricated roll dates | ✅ DONE | ✅ **DONE** — every date observed; no CME expiry substituted anywhere |
| 7 | Calendar committed to the repository | ⛔ BLOCKED | 🟡 **PARTIAL** — the calendar is committed **as this document**; a machine-readable artifact is B-2 work and is deliberately not created here |
| 8 | Calendar deterministic / version-controlled | 🟡 schema only | 🟡 **PARTIAL** — same reason as 7 |
| 9 | Phase 16 untouched | ✅ DONE | ✅ **DONE** — hashes re-verified |
| 10 | Repository state audited | ✅ DONE | ✅ **DONE** |
| 11 | Semantics graded | ✅ DONE | ✅ **DONE** |
| 12 | Contract-mapping invariant defined | ✅ DONE | ✅ **DONE** |
| 13 | Required data pull specified | ✅ DONE | ✅ **DONE** — executed |

**11 of 13 complete, 2 partial, 0 blocked** (was 8 / 1 / 4).

**B-1's substantive question is answered: the roll calendar exists, is observed, and is recorded.**
Criteria 7 and 8 remain partial for one reason only — writing the machine-readable calendar file is
implementation, and this task's scope forbids creating implementation files. That is a **one-file
B-2 task with no remaining unknowns**, not a blocker.

### P-6.4 Verification of this investigation

| check | result |
|---|---|
| investigation layout | `B1 ROLL INVESTIGATION`, chart `P2NtY6fg`, created this session |
| frozen chart `2d43Iesr` | **navigated away from by `tab_new`, reopened, and verified byte-for-byte unchanged** — symbol, resolution, chartType, all three study entity IDs, `backAdjustment`, `settlementAsClose`, `sessionId` (P-6.0) |
| mutating call on the frozen chart | **none** — every evaluation carried an abort guard on `2d43Iesr`; it never fired |
| Pine artifact loaded / compiled / executed / read | **none** — no `pine_*` tool invoked, no `pine_*` schema loaded |
| studies added or removed | **none**, on either chart |
| `backAdjustment` toggled | **on `P2NtY6fg` only**; restored to `false` and **re-read to confirm** |
| post-FE data | daily bars for 2026-09-01…09-07 were necessarily present in loaded ranges. **Nothing post-FE was collected, stored, analysed, or used**; every quoted bar is pre-FE. No strategy evaluation or OOS analysis was performed |
| roll date asserted without evidence | **none** — every date is dual-sourced |
| CME expiry substituted for a roll date | **no**. `expiration` values are recorded in E-4′ as metadata only and are **not** used to derive any roll date |
| Phase 16 artifacts | unchanged — `V53_P16_OOS_BUILD.pine` `5c21acfa…`, `PHASE16_PROTOCOL.md` `c5b6c853…`, `p16_analyze.py` `588eb9d0…` |
| V53 artifacts | unchanged — `V53_ltf_sequence.pine` `7490766b…`, `V53_EXECUTED_BUILD.pine` `2dafbafd…` |
| strategy / execution / data-architecture code | **not modified** |
| `bot/calendar/cme.py` | **not modified** |
| Databento / provider adapter / aggregator | **not started** |
| files changed | **1**: `docs/PHASE_B1_ROLL_CALENDAR.md` |

---

## B-2 — FROZEN ROLL CALENDAR + PHASE C DATASET EXPORT

**Status: 🟡 PARTIAL / BLOCKED on one component.** The roll calendar is frozen and validated. The
parent 5m dataset is exported and verified against the frozen run files. **The LTF (1m/3m) stream
is BLOCKED and was not exported** — see B-2.E. Per the task's own rule, one unsatisfiable criterion
means B-2 is reported BLOCKED rather than improvised around.

### B-2.A Artifacts frozen

| path | kind | rows | bytes | SHA-256 |
|---|---|---|---|---|
| `data/roll_calendar.json` | roll calendar | 122 rolls | 40,215 | `8d025df3fa600d1d3d8abf40811d2ecc12947f90892fed9fc997fd99b8edfe29` |
| `data/phase_c/MGC1__5m.csv` | parent bars | 19,218 | 602,265 | `1c5c5ebaaa3fb740d7a388330ab5080a6a53445fd7d86205e424514131f0888f` |
| `data/phase_c/MNQ1__5m.csv` | parent bars | 19,200 | 667,838 | `63e9d0ac33f29d2d27172ae0129d4ba57f10cd143b51baa8a87b720ac77ee665` |
| `data/phase_c_manifest.json` | manifest | — | — | (records the three above) |
| `bot/tests/test_roll_calendar.py` | validator | 24 tests | — | — |

### B-2.B The roll calendar (B-2.1, B-2.2) — **FROZEN**

`data/roll_calendar.json` carries **122 roll entries**: 88 for MGC (from 2010-12) and 34 for MNQ
(from 2019-06), exactly the rows TradingView's `RollDatesCalculator` exposed in P-6. Nothing was
reconstructed, extrapolated or inferred; the historical rows were captured during the P-6 session
and are transcribed verbatim.

Per-roll fields: `old_contract`, `new_contract`, `trade_date`, `roll_timestamp`,
`roll_timestamp_utc`, `roll_timezone`, `status`. Instrument-level fields hold the values that are
constant across every roll — `root`, `continuous_symbol`, `resolved_symbol`, `session`,
`session_timezone`, `pointvalue`, `minmov`, `pricescale`, `mintick`, `contract_cycle`,
`adjustment_mode`, `roll_count`.

**One stated interpretation.** The brief listed `session` and `pointvalue` among the per-entry
fields *and* forbade unnecessary duplication. Repeating two instrument constants across 122 rows is
duplication, so they live at instrument level, where each roll inherits them unambiguously. This is
recorded rather than silently applied.

`status` is `historical` for rolls at or before the 2026-09-07 observation date and `scheduled` for
the future switches TradingView already publishes (e.g. MNQ `MNQU2026 → MNQZ2026` on 2026-09-15).
Both are equally *observed*; only their relation to today differs.

**Determinism.** Serialised with `indent=2`, `ensure_ascii=False`, insertion-ordered keys, trailing
newline, and no generation timestamp, hostname, path or random id. `test_deterministic_round_trip`
re-serialises the parsed file and asserts byte equality.

**Validation** — `bot/tests/test_roll_calendar.py`, 24 tests, all passing. It covers every check the
brief listed, plus three that fell out of the data:
- no duplicate roll boundary or trade date; chronological ordering; `old != new`
- **contract chaining** — each roll's `new_contract` is the next roll's `old_contract`, unbroken
  across all 122 rows
- timestamps valid, and `roll_timestamp_utc` agrees with `roll_timestamp`
- **every roll instant is exactly 17:00 America/Chicago** (asserted, not assumed)
- the roll timestamp precedes its trade date by 1–4 days, the wider gaps being holiday/weekend rows
- `contract_cycle` is **derived from the contracts actually present** and asserted equal to MGC
  `GJMQZ` / MNQ `HMUZ` — so the cycle is a computed property of the evidence, not a hardcoded claim
- pointvalue MGC 10 / MNQ 2; continuous symbols correct
- **no contract is a `!` continuous alias** — every leg matches `^[A-Z]{2,4}[FGHJKMNQUVXZ]\d{4}$`
- the three research-window rolls are present with their exact timestamps
- **fold C contains no roll**

### B-2.C The parent dataset (B-2.3) — **EXPORTED AND VERIFIED**

Exported on the investigation layout `P2NtY6fg`. **The frozen chart `2d43Iesr` was not opened,
attached to, or modified**; every evaluation carried the `location.href` abort guard from P-6.

Fields are exactly the frozen V53 requirement — **`timestamp,high,low,close`**. Open and volume were
deliberately excluded: V53's 5m engine never reads them, and including them would extend the
dataset beyond what the research consumed.

| | MGC1! | MNQ1! |
|---|---|---|
| rows (pre-FE) | **19,218** | **19,200** |
| fold A | **10,386** | **10,368** |
| fold B | **4,668** | **4,668** |
| fold C | 4,164 | 4,164 |
| post-FE rows | **0** | **0** |
| span | 2026-05-24T22:00Z → 2026-08-30T23:55Z | same |

**The fold counts and spans match the frozen run files exactly.** `MGC_L_3m_A` records
`foldbars 10386` and `cov 2026-05-24 22:00 -> 2026-07-15 23:55`; `MNQ_L_3m_A` records
`foldbars 10368` with the same span; every `_B` run records `foldbars 4668` and
`cov 2026-07-16 00:00 -> 2026-08-07 20:55`. This is an independent reproduction, not a target that
was fitted to.

**Why the start date is not a chosen cutoff.** `requestMoreData()` paging stalled at
**2026-05-24T22:00Z** for *both* instruments — that is TradingView's 5m history limit for these
symbols. It is the same instant the frozen research saw. The window start was never a research
decision; it is a platform boundary, and it has not moved.

**The end boundary** is `FE = 1788134400` (2026-08-31T00:00:00Z), applied as `timestamp < FE`.
`test_no_post_fe_data` asserts it on every row of both files.

**Nothing was repaired.** No gap filling, no interpolation, no timestamp normalisation — timestamps
are the raw unix seconds TradingView reports. No bar was added because TradingView can now supply
it: everything from 2026-08-31 onward was dropped at export.

### B-2.D Reproducibility (B-2.5)

| parameter | value |
|---|---|
| requested symbols | `COMEX_MINI:MGC1!`, `CME_MINI:MNQ1!` |
| resolved symbols | `COMEX_MINI_DL:MGC1!`, `CME_MINI_DL:MNQ1!` — **delayed feed**; non-`_DL` requests resolve to `_DL` on this account |
| resolution | `5` |
| `backAdjustment` | `false` |
| `settlementAsClose` | `true` |
| `sessionId` | `regular` |
| timestamps | raw unix seconds, UTC, bar-open instant; no normalisation |
| export mechanism | `model().mainSeries().bars()` read over CDP after `requestMoreData()` paging to the history limit |
| layout | `B1 ROLL INVESTIGATION` (`P2NtY6fg`) — **not** `2d43Iesr` |
| roll-calendar version | `data/roll_calendar.json` sha256 `8d025df3…` |

No TradingView setting was changed to improve the data. `backAdjustment` was left at its platform
default of `false`, which is what makes the exported bars the **raw** old-contract prices across a
roll, matching what the research consumed.

### B-2.E **BLOCKED: the LTF (1m/3m) stream cannot be exported**

This is the pre-registered stop condition, and it applies to exactly this component.

**What blocks it.** V53 obtains its LTF stream from
`request.security_lower_tf(syminfo.tickerid, ltfStr, high/low/close/time)` — a **Pine-runtime**
construct (`V53_ltf_sequence.pine:99-103`). The data has three properties that exist only inside
that call:

1. **The 100,000-value cap.** Every 1m run file reports exactly `LTFbars 100000`. The cap truncates
   the *earliest* history, and where it bites depends on the run's end point.
2. **Per-parent-bar grouping.** The call returns an array per chart bar. `MGC_L_1m_A` reports
   `foldbars 10386 | w/LTF 9813` — **573 parent bars received an empty array**. Which 573 is part
   of the information set, and it is not recoverable from a bar series.
3. **Run-specific truncation points.** Fold-A 1m coverage starts `2026-05-27 02:15` for MGC and
   `02:20` for MNQ; the 3m runs are untruncated (`w/LTF 10386` = `foldbars`), and fold B is
   untruncated for both. The boundary differs per instrument, per LTF and per fold.

**Why the workarounds are all forbidden or wrong.**

- Running the Pine artifact would reproduce it exactly — **explicitly forbidden** ("do not rerun
  Pine", "no Pine artifact loaded/compiled/executed").
- Exporting the 1m/3m *chart* series is not the same object: it would carry no 100k truncation and
  no parent grouping, and would hand fold A **more** LTF history than the research had — which the
  brief forbids ("do not backfill missing LTF history", "do not add bars merely because TradingView
  can now provide them").
- Truncating a chart export at the recorded `cov` start and grouping it to parent bars would be
  **implementing 1m/3m/5m aggregation** — forbidden in B-2 — and would be reconstruction from a
  summary line, not reproduction of the stream.

**Nothing was substituted.** No provider, no Databento, no reconstructed or interpolated LTF data.
The Fold-A truncation is preserved by *not touching it*: the parent dataset is exported as observed,
and the LTF boundary remains exactly as the frozen run files record it. Reproducing the truncation
algorithm is B-3 work, as the brief states.

### B-2.F Acceptance

| criterion | status |
|---|---|
| canonical machine-readable roll calendar exists | ✅ `data/roll_calendar.json` |
| calendar contains only evidenced TradingView roll information | ✅ 122 verbatim `RollDatesCalculator` rows |
| calendar deterministic | ✅ byte-stable round trip asserted |
| calendar version-controlled | ✅ committed |
| calendar validator passes | ✅ 24/24 |
| exact Phase C TradingView dataset exported | ⛔ **parent 5m only; LTF blocked (B-2.E)** |
| dataset boundaries documented | ✅ B-2.C / manifest |
| no post-FE data included | ✅ asserted per row, both files |
| no Fold-A LTF truncation repaired | ✅ untouched |
| no synthetic/backfilled bars | ✅ none |
| dataset manifest exists | ✅ `data/phase_c_manifest.json` |
| SHA-256 hashes recorded | ✅ |
| frozen pre-existing hashes unchanged | ✅ all five re-verified |
| dataset reproducible | ✅ fold counts and spans match the frozen runs independently |
| Phase 16 untouched | ✅ |
| V53 untouched | ✅ |
| no provider/execution code changed | ✅ |
| no Pine artifact loaded/compiled/executed | ✅ |
| existing guards/tests pass | ✅ guards PASS, 299 bot tests, 43 analyser tests, `verify_p16_oos.py` PASS |

**17 of 18 satisfied. One is not, so B-2 is reported BLOCKED on the LTF component.**

### B-2.G UNKNOWN after B-2

| # | unknown | note |
|---|---|---|
| U-5 | B-ADJ during the 13F/14/15 runs | **STRONGLY INFERRED off**, not upgraded |
| U-7 | `_DL` vs non-`_DL` historical roll parity | **UNKNOWN** — the non-`_DL` series is unreachable |
| U-9 | whether TradingView ever revised a roll rule retroactively | not exposed; the calendar is now frozen in-repo precisely so a later re-read cannot silently replace it |
| U-12 | whether `settlementAsClose` affects the 5m/LTF bars V53 consumed | untested; recorded, not acted on |
| U-13 | whether roll dates hold identically at intraday resolutions | the calendar was read on daily bars |
| **U-14** | **the exact LTF stream the frozen research consumed** | **NEW.** Not exportable without running Pine (B-2.E). B-3 must reproduce the truncation algorithm rather than recover the data |

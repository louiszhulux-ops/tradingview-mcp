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
compiling or running any Pine artifact.

### 10.0 Outcome: ⛔ **BLOCKED ON INFRASTRUCTURE. No TradingView call succeeded.**

**No roll date is asserted. No adjustment mode is asserted. Nothing was inferred to fill the gap.**

The four blocked B-1 criteria (§7 rows 1, 2, 3, 7) remain blocked, for the same reason as before
and with no new evidence either way. What changed is only that the *route* to the evidence has now
been tried and has failed for a reason that is external to this repository.

#### The failure

Every `mcp__f__*` call returned Cloudflare **HTTP 502 `origin_bad_gateway`**, zone
`api.anthropic.com`. **VERIFIED:** the failing origin is the **MCP relay**, not TradingView. The
error body names the zone explicitly, and no request reached TradingView Desktop or the CDP bridge
on port 9222. This is not a TradingView outage, a symbol-permission problem, or a chart-state
problem, and it says nothing about whether the data sought by P-1…P-5 exists.

**Retry log — 9 attempts, 2 distinct tools, ~19 minutes elapsed, 2026-09-07 UTC:**

| # | time | wait before | tool | ray id | result |
|---|---|---|---|---|---|
| 1 | 05:35:21 | — | `tv_health_check` | `a373597be9aa72e5` | 502 `origin_bad_gateway` |
| 2 | 05:35:40 | 19s | `tv_health_check` | `a37359f1cf7e9991` | 502 |
| 3 | 05:36:03 | 23s | `tv_health_check` | `a3735a83a8ee2234` | 502 |
| 4 | 05:36:43 | 40s | `tv_health_check` | `a3735b7d9c6d98b8` | 502 |
| 5 | 05:39:57 | 194s | `tv_health_check` | `a37360386c02866c` | 502 |
| 6 | 05:41:19 | 82s | `tv_health_check` | `a373623bec60dc1f` | 502 |
| 7 | 05:46:25 | 306s | `tv_health_check` | `a37369b52df83457` | 502 |
| 8 | 05:46:30 | 5s | **`symbol_search`** | `a37369d22a02c0f3` | 502 — *different tool, identical failure* |
| 9 | 05:54:23 | 473s | `tv_health_check` | `a373755da866b002` | 502 |

Attempt 8 is the informative one: a **different** read-only tool fails identically and immediately.
**VERIFIED:** the failure is relay-wide at the transport layer, not specific to `tv_health_check`
and not a property of any particular chart operation.

Backoff followed the gateway's own `retry_after: 60` guidance and then escalated. The failure was
stationary — identical `error_name`, identical zone, no degradation and no partial success.

**Precedent.** `trader_v2/RELAY_OUTAGE.md` records the same failure signature on 2026-09-05
(18:05–18:55, 18 attempts), where it degraded from 502 to `MCP server "f" is not connected` and
then to a hard 404 on the session's MCP route. That outage was resolved by re-establishing the
connector on the user's side, not by further waiting. `trader_v2/FREQUENCY_REPORT.md:94` records a
third instance. **INFERRED (moderate confidence):** this is a recurring environmental condition of
this session type, not a one-off.

### 10.1 Exact symbols targeted

These are the symbols the pull was to address. **None of them was loaded, queried or resolved** —
this table records intent and the basis for it, not observation.

| role | symbol | status | basis |
|---|---|---|---|
| continuous, gold | `MGC1!` | **not queried** | the ticker recorded by every frozen run file (§1.1) |
| continuous, Nasdaq | `MNQ1!` | **not queried** | as above |
| prefix candidate A | `COMEX_MINI:MGC1!` / `CME_MINI:MNQ1!` | **not queried** | non-delayed records; used by earlier generations (§1.3) |
| prefix candidate B | `COMEX_MINI_DL:MGC1!` / `CME_MINI_DL:MNQ1!` | **not queried** | pinned by `p16/PHASE16_PROTOCOL.md:107`, **for Phase 16 only** |
| concrete, gold | `COMEX_MINI:MGCM2026`, `MGCQ2026`, `MGCV2026` | **not queried**, **existence unverified** | §3.2 candidate universe |
| concrete, Nasdaq | `CME_MINI:MNQM2026`, `MNQU2026` | **not queried**, **existence unverified** | §3.2 candidate universe |

**UNKNOWN:** whether the concrete-contract symbols above exist on TradingView at all, and whether
this account is entitled to them. The P-5 fallback depends entirely on that, and it was not
established. It must not be assumed.

**U-8 is unchanged and remains UNKNOWN.** The prefix actually used by the frozen 13F/14/15 runs
is still not determined. A fresh local re-check during this attempt confirms the negative result
already recorded in §1.1: a regex sweep for `(COMEX|CME|NYMEX|CBOT)(_MINI)?(_DL)?:` across every
file in `trader_v2/v53_runs/`, `trader_v2/v53_runs_foldc/` and `trader_v2/p15/runs/` returns **zero
matches**. `syminfo.ticker` strips the prefix, so the runs cannot testify to it. **This is a
permanent property of the frozen artifacts, not a gap that P-4 could have closed retroactively** —
P-4 could only have shown whether the two records *roll identically*, which would make the
question moot; it could never have shown which one was used.

### 10.2 Metadata discovered

**None.** Zero bytes of TradingView chart metadata were retrieved.

What is recorded below is the **capability inventory**, established by reading this repository's
own bridge source — it is VERIFIED about the bridge, and says nothing about TradingView's data.

| # | finding | grade | evidence |
|---|---|---|---|
| M-1 | `symbolInfo()` returns exactly 9 fields — `symbol`, `full_name`, `exchange`, `description`, `type`, `pro_name`, `typespecs`, `resolution`, `chart_type` | **VERIFIED** | `src/core/chart.js:257` |
| M-2 | None of those 9 fields carries expiry, root, contract month, or adjustment state | **VERIFIED** | same |
| M-3 | Therefore `symbol_info` **cannot** answer P-2, P-3 or P-4 as it stands; `ui_evaluate` against the chart model is the only available route | **VERIFIED** (follows from M-1/M-2 and the tool list) | — |
| M-4 | `chart.symbolExt()` is the underlying object `symbolInfo()` projects from, so it may carry more fields than the 9 exposed | **INFERRED** | `symbolInfo()` reads `chart.symbolExt()` and discards the remainder; whether a richer field set exists there is **UNKNOWN** until dumped |
| M-5 | History paging exists (`requestMoreData(1000)`, `src/core/chart.js:185`) and `getOhlcv` is capped at 500 bars (`MAX_OHLCV_BARS`, `src/core/data.js`) | **VERIFIED** | cited files |
| M-6 | `getOhlcv` includes the **forming** bar (`end = bars.lastIndex()`, inclusive loop, `src/core/data.js:137-155`) | **VERIFIED** | cited file; already logged in the production-readiness audit |

M-6 matters for P-5: a daily-bar export used for the segment-offset signature must **drop the last
bar**, or a partial bar will be differenced against a complete one and manufacture a false offset.
That is a design note for the next attempt, not a finding about rolls.

### 10.3 Roll evidence (P-1, P-4)

**NONE. UNKNOWN. No roll date is asserted for either instrument.**

- No chart-model read was performed, so V-7's purple date-axis markers were **not** located, not
  enumerated, and not confirmed to be machine-readable. V-7 remains what it was: a statement from
  TradingView's documentation that such markers exist on `ES1!`, **not** an observation on `MGC1!`
  or `MNQ1!`.
- No `MGC1!`-vs-concrete-contract comparison was performed, so the P-5 fallback produced nothing.
- **U-1, U-2, U-3, U-6, U-7, U-9 are all unchanged and remain UNKNOWN.**

**The critical evidence rule holds and is restated:** V-2 ("TradingView rolls `1!` on a fixed
per-symbol rule derived from average volume statistics") is a *rule*, and a rule is not a calendar.
Nothing in this section converts it into one. No CME expiration date has been substituted for a
TradingView roll date anywhere in this document, and I-3 (that a roll occurred inside the research
window) remains an **inference**, not an observation, notwithstanding that it is very likely true.

### 10.4 Adjustment evidence (P-3, P-5)

**NONE. UNKNOWN.**

- The chart settings model was not read, so the live `B-ADJ` state is unobserved and it is unknown
  whether the setting persists per layout.
- No dual daily-bar export was taken, so the segment-wise constant-offset signature (§4) was not
  computed.
- **U-5 is unchanged and remains UNKNOWN.** I-1 (that the frozen research ran unadjusted) remains
  an inference resting on V-4 (adjustment defaults off) plus the absence of any repository
  instruction to enable it. **That is an argument from silence and is explicitly not evidence.**
  Its stated risk-if-wrong is High and that assessment is unchanged.

### 10.5 Unresolved questions after P-1…P-5

Every unknown carried into this investigation survives it. Nothing was resolved, and — the point
worth stating plainly — **nothing was downgraded from UNKNOWN to INFERRED merely because the
evidence could not be obtained.**

| # | unknown | status after P-1…P-5 |
|---|---|---|
| U-1 | roll-rule N for `MGC1!` | **UNKNOWN** — unchanged |
| U-2 | roll-rule N for `MNQ1!` | **UNKNOWN** — unchanged |
| U-3 | actual roll dates in the research window | **UNKNOWN** — unchanged; this is the single load-bearing gap |
| U-4 | concrete contract per bar | **UNKNOWN** — unchanged; downstream of U-3 |
| U-5 | B-ADJ on or off during 13F/14/15 | **UNKNOWN** — unchanged |
| U-6 | calendar vs business days, holiday handling | **UNKNOWN** — unchanged |
| U-7 | `_DL` vs non-`_DL` share a roll rule | **UNKNOWN** — unchanged |
| U-8 | prefix used by the frozen runs | **UNKNOWN** — unchanged; re-confirmed unanswerable from the run files themselves (§10.1) |
| U-9 | whether the roll rule was ever revised retroactively | **UNKNOWN** — unchanged |
| **U-10** | **whether the concrete monthly contracts (`MGCM2026` etc.) exist on TradingView and are entitled to this account** | **NEW, UNKNOWN** — the P-5 fallback is conditional on this and it has never been checked |
| **U-11** | **whether the MCP relay will be available at all during Phase B** | **NEW, UNKNOWN** — three recorded outages (§10.0); if TradingView is the parity oracle for Phase C Gate 1, oracle availability is itself a project risk |

U-11 is not a data question, but it belongs here. §9's recommendation to export and hash the Phase C
dataset **soon** was written against U-9 (retroactive revision). This attempt supplies a second,
independent reason for the same recommendation: the export route is intermittently unavailable, and
the window in which it can be taken is not under this project's control.

### 10.6 Updated B-1 acceptance checklist

| # | criterion | status before P-1…P-5 | status after |
|---|---|---|---|
| 1 | MGC roll calendar frozen | ⛔ BLOCKED | ⛔ **BLOCKED** — no change; blocker reclassified data-unavailable → **infrastructure-unavailable** |
| 2 | MNQ roll calendar frozen | ⛔ BLOCKED | ⛔ **BLOCKED** — as above |
| 3 | Every relevant bar resolves to a concrete contract | ⛔ BLOCKED | ⛔ **BLOCKED** — downstream of 1 and 2 |
| 4 | Adjustment semantics documented | 🟡 PARTIAL | 🟡 **PARTIAL** — unchanged; mechanism VERIFIED, mode in force still UNKNOWN (U-5) |
| 5 | Unresolved assumptions explicitly identified | ✅ DONE | ✅ **DONE** — extended with U-10, U-11 |
| 6 | No fabricated roll dates | ✅ DONE | ✅ **DONE** — still none asserted anywhere |
| 7 | Calendar committed to the repository | ⛔ BLOCKED | ⛔ **BLOCKED** — nothing to commit |
| 8 | Calendar deterministic / version-controlled | 🟡 schema defined | 🟡 **unchanged**, unpopulated |
| 9 | Phase 16 untouched | ✅ DONE | ✅ **DONE** — re-verified by hash after every relay attempt (§10.7) |
| 10 | Repository state audited, not assumed | ✅ DONE | ✅ **DONE** — §10.1 re-ran the prefix sweep |
| 11 | Semantics graded VERIFIED / INFERRED / UNKNOWN | ✅ DONE | ✅ **DONE** — grading applied throughout §10 |
| 12 | Concrete-contract mapping invariant defined | ✅ DONE | ✅ **DONE** — unchanged |
| 13 | Required data pull specified precisely | ✅ DONE | ✅ **DONE** — sharpened by §10.7 |

**7 of 13 complete, 2 partial, 4 blocked — numerically identical to before.** B-1 is not complete
and is not closer to complete. The honest summary is that this attempt eliminated a *hypothesis
about why* B-1 was blocked (it is not blocked because the metadata route is wrong — that route was
never reached) without eliminating the blockage.

### 10.7 Exact evidence required to unblock

Each item below is the *minimum sufficient* observation. Anything less does not close the criterion.

| for | required evidence | closes | acceptance test |
|---|---|---|---|
| **E-1** | A dump of `chart.symbolExt()` on `MGC1!` and `MNQ1!` via `ui_evaluate`, verbatim, all keys | U-4 partly, U-1/U-2 if a roll or expiry field is present | the raw object is pasted into this document; absent fields are recorded as absent |
| **E-2** | The chart-model roll markers (V-7) enumerated as timestamps for both symbols over ≥ 2026-04-01 → 2026-09-01 | **U-3** — the load-bearing gap | each marker is an extracted timestamp with the model path it came from; a screenshot alone is **not** sufficient |
| **E-3** | *If E-2 is unavailable:* daily bars for `MGC1!` and each candidate concrete contract over the same window, forming bar dropped (M-6) | **U-3** observationally | the date on which the continuous series stops matching contract *k* and starts matching *k+1*, shown bar-by-bar for ≥ 3 bars either side |
| **E-4** | Existence and entitlement check for `MGCM2026`/`MGCQ2026`/`MGCV2026`/`MNQM2026`/`MNQU2026` | **U-10** | `symbol_search` result, or an explicit "no such symbol" |
| **E-5** | The chart settings model's `B-ADJ` field, read directly | **U-5** partly | the field name and value, quoted |
| **E-6** | Daily-bar export of one instrument across a **known** roll date, once B-ADJ off and once on | **U-5** independently | a segment-wise constant additive offset appears in exactly one of the two series (§4) |
| **E-7** | Roll markers on `COMEX_MINI:MGC1!` and `COMEX_MINI_DL:MGC1!` compared | **U-7**; makes U-8 moot **only if identical** | both marker sets extracted and diffed |

**Precondition for all of E-1…E-7: a working MCP relay.** That is the entire remaining blocker and
it is not resolvable from inside this session. It requires the connector re-established or the
session restarted, on the user's side.

**Two things E-1…E-7 must not become.** First, a CME expiration date is not a TradingView roll
date, and E-3's observational fallback is the *only* sanctioned substitute for E-2 — not a CME
calendar. Second, if both E-2 and E-3 prove permanently unavailable, the honest outcome is §9's
second recommendation: scope Phase C Gate 1 parity to a **roll-free sub-window** and record the
reduction explicitly. That should be a deliberate decision by the user, not a drift.

### 10.8 Verification of this attempt

| check | result |
|---|---|
| TradingView reached | **no** — zero successful calls; 9 × HTTP 502 at the relay across 2 distinct tools |
| Pine artifact loaded / compiled / executed | **none** — `pine_*` tools were never invoked, and no schema for them was even loaded |
| chart symbol / timeframe / settings mutated | **none** — no write-capable tool was invoked |
| OOS or post-FE data inspected | **none** |
| roll date asserted | **none** |
| adjustment mode asserted | **none** |
| Phase 16 artifacts | unchanged — re-verified by `sha256sum -c` after every attempt: `V53_P16_OOS_BUILD.pine` `5c21acfa…`, `PHASE16_PROTOCOL.md` `c5b6c853…`, `p16_analyze.py` `588eb9d0…` all OK |
| V53 artifacts | unchanged — `V53_ltf_sequence.pine` `7490766b…`, `V53_EXECUTED_BUILD.pine` `2dafbafd…` OK |
| strategy / execution / data-architecture code | **not modified** |
| Databento / provider adapter / aggregator | **not started** |
| files changed by this section | **1 modified**: `docs/PHASE_B1_ROLL_CALENDAR.md`. Zero created, zero deleted |

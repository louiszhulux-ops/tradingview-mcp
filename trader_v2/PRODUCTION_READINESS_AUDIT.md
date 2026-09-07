# Production Readiness Audit

**Audit only. No source file, script, Pine artifact, protocol, test or configuration was modified.
Phase 16 was not run, not deployed, and its OOS results were not inspected. This document is the
only file created.**

Audited at HEAD `f547165`, 2026-09-07. 202 commits. Working tree clean.

Frozen artifacts verified unchanged during the audit:
`V53_ltf_sequence.pine` `7490766b…` · `V53_EXECUTED_BUILD.pine` `2dafbafd…` ·
`V53_P16_OOS_BUILD.pine` `5c21acfa…`

---

## Executive Summary

**This repository is roughly 15% of an automated trading bot, and 0% of a *live* one.**

What exists is genuinely good, but it is three things, none of which is a trading system:

1. **A mature research instrument** — 6,265 LOC of Node that drives a GUI copy of TradingView
   Desktop over a Chrome debug port, plus ~5,700 LOC of Python research analysis and 24 Pine
   artifacts. It is well-tested for what it does.
2. **A rigorous validation apparatus** — Phase 16 pre-registration, hash-pinned provenance,
   a frozen analyser, 43 tests. This is stronger than most professional shops manage.
3. **The beginnings of a real system** — `bot/`, 5,992 LOC added over the last five commits:
   contamination guards, golden fixtures, typed contracts, a session calendar, and a faithful
   Python V53 engine. **318 Python tests pass.**

What does not exist, at all:

> **no broker integration · no order management · no position management · no execution engine ·
> no risk engine wired to anything · no persistence · no reconciliation · no scheduler ·
> no process supervision · no deployment · no monitoring · no alerting · no paper broker ·
> no runtime entrypoint of any kind**

Evidence, not impression: a repo-wide search for broker/order/execution identifiers
(`broker`, `submit_order`, `place_order`, `client_order_id`, and 20 named venues) returns
**2 hits, both of which are a test asserting those words are *absent***. Searches for
`sqlite|postgres|redis|mongo|CREATE TABLE` return **0**. There is no `Dockerfile`, no
`docker-compose`, no `Makefile`, no systemd unit. `package.json` has exactly two runtime
dependencies: the MCP SDK and `chrome-remote-interface`.

The V53 Python engine — the single most valuable new asset — **has no consumer**. Every import of
`bot.strategy.v53` outside the package is a test. There is no `__main__` anywhere in `bot/`
except the two tools and the test modules.

**Answer to "how close is this to a real bot?": the strategy specification is finished and the
strategy engine is written; the *system* around it has not been started.** The distance is not
"add a broker adapter" — it is "build the trading system", with this repo supplying an unusually
good specification, a verification oracle, and a research harness.

**One thing must be said plainly and separately from all engineering judgements:** Phase 15
concluded *"No arm demonstrates an edge. The baseline is negative under all three accountings."*
Phase 16 is the only thing that can change that, and it is sealed until 2027-04-02. **A working
bot is not a reason to trade this strategy.** Build the system because the harness outlives the
hypothesis, not because the hypothesis is validated.

---

## Current Architecture

Traced from code, not assumed. The real flow today:

```
TradingView Desktop (Electron GUI, logged-in session)
        │  Chrome DevTools Protocol, 127.0.0.1:9222
        ▼
src/connection.js ── CDP client, 5 retries, 500ms base backoff
        │            Runtime.evaluate() of JS strings against the page
        ▼
src/core/*.js (17 modules) ── scrape the chart widget's in-memory objects
        │   data.js      : window.TradingViewApi…mainSeries().bars()
        │   pine.js      : inject/compile/save Pine source
        │   stream.js    : poll-and-diff, 300–2000 ms
        ▼
src/tools/*.js (15 modules) → src/server.js ── 84 MCP tools over stdio
        ▼
   an LLM or a human operator reads the numbers
        ▼
   Pine tables read by eye  →  hand-copied into trader_v2/**/runs/*.txt
        ▼
trader_v2/*.py (31 scripts) ── regex-parse those text files, compute statistics
        ▼
   markdown research reports
```

And, entirely disconnected from the above:

```
bot/  (offline, no runtime)
   guards.py ─ pre-FE contamination guard (fails closed)
   calendar/ ─ CME trade-date rule
   contracts/ ─ typed Signal/state/event schemas
   data/bars.py ─ Bar / ParentBar, Decimal prices
   strategy/v53/ ─ faithful Python V53  ←── consumed only by its own tests
   fixtures/golden/ ─ 24 golden fixtures + manifest
```

**Boundaries that exist:** CDP↔core, core↔tools, tools↔MCP stdio, contracts↔engine (declared in
`bot/contracts/engine.py`, which imports no broker/OMS/risk and has a test asserting it).

**Boundaries that do not exist:** strategy→risk, risk→execution, execution→broker,
broker→reconciliation, anything→persistence. **The pipeline terminates at "a human reads a
table."**

The architecture the request sketched — data → sweep → sequence → validation → risk → order →
broker → position → ledger → monitoring — **exists only as far as the third box, and only
offline.**

---

## Repository Map

| tree | size | what it is | consumed by | tested | production-safe |
|---|---|---|---|---|---|
| `src/` | 52 js, 6,265 LOC | MCP bridge: 17 core + 15 tools + 17 CLI modules, 84 tools | MCP clients, CLI | yes (see Testing) | **NO — research only** |
| `bot/` | 36 py, 5,992 LOC | new system: guards, contracts, calendar, V53 engine, fixtures | **only its own tests** | 275 tests | partial — no runtime |
| `trader_v2/` | 31 py + 24 pine + 36 md | V53 research, Phases 10–16 | humans | p16 only (43 tests) | research only |
| `trader/` | 8 py, 992 LOC | v1 prop/risk/decision skeleton, targets **V38 not V53** | **nothing** | 1 self-contained script | **NO — dead code** |
| `strategies/` | 88 files | superseded V11–V38 generation | nothing | no | historical |
| `tests/` | 9 js, 3,223 LOC, 191 blocks | Node tests; `e2e.test.js` (79) needs live TradingView | CI (subset) | — | — |
| `scripts/` | 2 js + launchers | pine push/pull, TV launchers (bat/vbs/sh) | manual | no | dev only |
| `.github/` | 1 workflow | Node lint+unit+audit; `phase16-guards` job | CI | — | adequate |

**Dead / duplicate / unfinished, with evidence:**

- `trader/` — 992 LOC, complete-looking, **zero external importers**, and aimed at V38.
- **Six independent re-implementations of the same V53 ledger parser**: `g_cluster.py` (227),
  `p14_foldc.py` (143), `p15/p15_analyze.py` (176), `p16/p16_analyze.py` (716),
  `bot/tools/extract_golden.py` (535), plus test-local parsers. Same 21-field format, six
  decodings. Divergence risk is real; `g_cluster.py` is the de-facto reference.
- **Exactly one TODO** in the whole codebase: `src/core/pine.js:516`, inside a template string.
  Genuinely trivial.
- **Stray zero-byte file `=` at repo root — and it is committed** (commit `ebca186`), not merely
  untracked. A shell-redirection accident.
- `STATE_OF_PLAY.md` still describes V38 as "live", which predates the whole V53 line.

**Environment surface — complete list:** `TV_CDP_HOST`, `TV_CDP_PORT` (aliases `CDP_HOST`,
`CDP_PORT`), plus OS paths `HOME`, `LOCALAPPDATA`, `PROGRAMFILES`. **That is all.** No broker
credential, no account id, no webhook secret, no database URL — because none of those subsystems
exists.

---

## Subsystem Scorecard

| Subsystem | Status | Evidence | Main gap |
|---|---|---|---|
| MCP/CDP bridge | **COMPLETE (research)** / **UNSAFE (trading)** | 6,265 LOC, 84 tools, retry+backoff, `safeString`/`requireFinite` | GUI-dependent; not a production data path |
| Strategy specification | **COMPLETE** | frozen Pine, hash-pinned, 12 frozen inputs, assertion battery reads 0 | none |
| Python V53 engine | **MOSTLY COMPLETE** | `bot/strategy/v53/`, 1,414 LOC, 69 tests, all 58 recorded ledger rows reproduce char-for-char | **never parity-tested on real bars (B3 blocked, no OHLCV in repo)** |
| Contracts / schemas | **COMPLETE** | `bot/contracts/`, 1,007 LOC, 86 tests, Decimal-only, deterministic serialisation | no consumer yet |
| Session calendar | **COMPLETE** | `bot/calendar/`, 40 tests, 3-link derivation, cross-checked against committed records | CST half unverified in-repo |
| Contamination guards | **COMPLETE** | `bot/guards.py` fails closed; 4 static checks in CI; 42 tests | none |
| Golden fixtures | **COMPLETE** | 24 + manifest, deterministic, provenance-hashed, 38 tests | results only, **no bars** |
| Market data | **UNSAFE** | scrapes chart memory; **reads through `lastIndex()` = the forming bar**; 0 hits for gap/stale/complete handling | everything |
| Execution | **MISSING** | 0 broker/order identifiers in code | everything |
| Risk engine | **PROTOTYPE / UNSAFE** | `trader/risk_engine.py`, unwired, unit-ambiguous, has an over-risk path | wiring + units + tick model |
| Position / lifecycle | **MISSING** | no state store, no order state machine | everything |
| Reconciliation | **MISSING** | no broker truth concept | everything |
| Persistence | **MISSING** | 0 hits for any database | everything |
| Observability | **MISSING** | no structured logging, no correlation ids, no metrics | everything |
| Deployment / ops | **MISSING** | no Dockerfile/compose/Makefile/service | everything |
| Research framework | **COMPLETE** | Phases 10–16, provenance, ablations, clustering, pre-registration | execution realism (below) |
| Phase 16 apparatus | **COMPLETE** | hash-pinned verifier (54 checks), frozen analyser, 43 tests, manifest | none |
| Testing | **PARTIAL** | 318 Python pass; Node 191 blocks but 79 need live TV | no execution/risk/recovery tests — because no such code |
| Security | **GOOD, with one caveat** | **0 secrets in working tree AND 0 in full git history** | `ui_evaluate` arbitrary JS eval |

---

## Critical P0 Blockers — cannot safely trade

**P0-1 · No execution layer whatsoever.** MISSING. A valid signal cannot become an order.

**P0-2 · No position or order state, and no persistence.** MISSING. Nothing survives a restart.
V53 carries ~30 parallel arrays of live state; Pine recomputes from bar 1 on every reload — a bot
cannot, and nothing here persists it.

**P0-3 · No reconciliation against broker truth.** MISSING. The classic route to unmanaged
positions.

**P0-4 · Market data reads the forming bar.** UNSAFE, and this one is concrete:
`src/core/data.js:137` `getOhlcv` iterates `start … end` where `end = bars.lastIndex()`, which
**includes the currently-forming bar**. A repo-wide search for `closed bar|complete|partial
bar|forming|unclosed` in `src/` returns **0 hits**. Any live loop on this path repaints. V53 is a
bar-close strategy; feeding it a partial bar produces signals that vanish.

**P0-5 · No data-integrity checks.** UNSAFE. Searches for `gap|stale|out-of-order|missing bar|
monotonic` in `src/` return 2 hits, **both about screenshot rendering**. No staleness detection,
no gap detection, no duplicate/out-of-order rejection anywhere in the live path.

**P0-6 · No kill switch, no emergency flatten, no risk limits in force.** MISSING.

**P0-7 · Strategy parity is unproven.** The Python V53 reproduces all 58 recorded ledger rows
exactly — a real result — but **bar-for-bar parity has never been run**, because the repo contains
no OHLCV and fetching it is out of scope. Until B3 passes, "faithful" is an argued claim, not a
measured one.

**P0-8 · TradingView is a single point of failure with no SLA.** UNSAFE. Requires a logged-in
desktop GUI, an Electron debug port, and breaks on app update.

---

## P1 Requirements — before serious paper trading

- Deterministic bar loader + replay driver (blocked on obtaining OHLCV).
- B3 parity harness — the Gate-1 oracle.
- Paper broker with an **explicit, switchable fill model** (see Research audit).
- Risk engine rebuilt and wired, with units fixed (see Risk audit).
- Idempotent order construction (`client_order_id` design exists on paper only).
- SQLite persistence + rehydration.
- Structured logging with correlation ids.
- Process supervision and a documented runbook.

## P2 Requirements — before production

Production market-data feed (non-GUI); broker/prop adapter; reconciliation loop; chaos/restart
test suite; health endpoint and alerting; backup/restore; deployment and rollback procedure;
config validation; secrets management.

## P3 Improvements

Consolidate the six ledger parsers; delete the committed `=` file; correct `STATE_OF_PLAY.md`;
Python linting in CI; resolve the single TODO; multi-instrument scaling; second-strategy
portability.

---

## Strategy Engine Audit

**Can the production implementation reproduce every V53 stage?** Yes — all thirteen stages are
implemented in `bot/strategy/v53/` and individually tested: 5m sweep, pivot confirmation, CHOCH
candidate selection, CHOCH retest, BOS, displacement, associated FVG, FVG retest, entry, stop,
target, timeout, outcome.

**Causality.** No lookahead in the implemented path. The engine consumes one closed `ParentBar` at
a time; `ParentBar` refuses a non-5m parent; the pivot detectors confirm `n` bars late by
construction; `PivotDetector` returns nothing until its window is full. Section order is asserted
by test, and two lookahead-adjacent consequences are separately pinned: §1 runs before §2 (a fill
on bar *t* is first judged on *t+1*) and §5 runs after §4 (a sequence armed on bar *t* is not
served by that bar's own sub-bars). **The lookahead risk is not in the engine — it is upstream, in
the forming-bar problem (P0-4).**

**State machine.** Yes, and explicit: `SequenceMachine` with 24 slots, `SlotState` 0–6, a 7-entry
ring buffer, a 4-entry pivot register, and a 15-member `TransitionReason` vocabulary each mapped
to its V53 counter index. This closes what would otherwise have been the largest gap.

**Parity — how many implementations exist?** Three, and this is the central engineering risk:

| implementation | status | can diverge? |
|---|---|---|
| `V53_ltf_sequence.pine` (`7490766b…`) | canonical, **never executed** | — |
| `V53_EXECUTED_BUILD.pine` (`2dafbafd…`) | produced all Phase 13F/14/15 data | reference |
| `V53_P16_OOS_BUILD.pine` (`5c21acfa…`) | +2 lines, data-gate only, 54-check verifier | proven equal |
| `bot/strategy/v53/` (Python) | **parity unproven on bars** | **YES** |

Do **not** assume parity from naming. What is actually established: all 58 recorded ledger rows
reproduce character-for-character through the real §1 loop and the Pine formatter — which
validates the outcome arithmetic, the point values, the cost model and the formatter. What is
**not** established: the funnel counters, the sequence detection, or any non-filling path.

A documentation defect was found and correctly left uncorrected: the artifact's pivot comment says
*"the FIRST of a run of equal extremes is the pivot"*, but its code allows equality on the older
side and rejects it on the newer, making the **most recent** member the pivot. Both Pine blocks
agree with each other and disagree with the prose; the code is authoritative (0 mismatches over
20,567 bars). The Python transcribes the code.

---

## Market Data Audit

> **Can the bot reliably reconstruct the exact bars V53 requires in real time? No.**

| concern | reality |
|---|---|
| source | TradingView Desktop chart's in-memory bar array, scraped over CDP |
| transport | `Runtime.evaluate()` of JS strings; **poll-and-diff, 300–2000 ms** — not a feed |
| bar construction | none — bars are taken as the GUI has them |
| **forming bar** | **included** (`lastIndex()`), no completeness flag anywhere — **P0-4** |
| tick handling | none, and none needed: V53 is bar-close |
| 1m / 3m | `request.security_lower_tf`, **capped at 100,000 values per field** ≈ 69 days of 1m |
| 5m | the chart's own resolution |
| timestamps | epoch ms; V53's are **bar OPEN** times |
| timezone | two calendars, correctly separated: PDH/PDL on the CME session day (17:00 America/Chicago), Asia on UTC `hour < 7`. Resolved and documented in `bot/U1_CME_SESSION_CALENDAR.md` |
| sessions / rollover | continuous contracts (`MGC1!`, `MNQ1!`); **rollover behaviour unaudited — UNKNOWN** |
| missing / duplicate / out-of-order bars | **no detection** — 0 hits in `src/` |
| stale data | **no detection** |
| reconnection | CDP reconnects (5 retries), but **data integrity across a reconnect is not considered** |
| validation | none in `src/`; strong in `bot/data/bars.py`, which nothing feeds |
| persistence | none |
| replay | `src/core/replay.js` drives TradingView's own replay **UI** — it is not a strategy backtester |

**Why not, precisely:** the live path has no notion of a closed bar, no gap detection, no
staleness bound, and a 100k-value LTF ceiling; and the only validated bar model (`bot/data/bars.py`)
is not connected to any source.

---

## TradingView / MCP Audit

**Classification: (A) research/debugging dependency today — and it must never become (B) or (C).**

Connection: `chrome-remote-interface` to `127.0.0.1:9222` (IPv4 deliberately, per an in-code note
about Windows resolving `localhost` to `::1`). 5 retries, 500 ms base backoff, liveness probe
before reuse. Auth: **none of its own** — it rides the desktop app's logged-in session.

There is **no HTTP server, no WebSocket server, no Cloudflare tunnel, no ngrok** anywhere in this
repository. Searches for `express|fastify|createServer|websocket|webhook|cloudflare|tunnel`
return only false positives on the word "expression". MCP transport is **stdio**.

Script deployment: `pine.js` (619 LOC) injects/compiles/saves. Verification of *what is deployed*
is possible via `pine_get_source` + hashing — the strongest available evidence, and the method the
Phase 16 protocol relies on.

Quality: for a research tool this is well-built — input sanitisation via `safeString`
(`JSON.stringify` escaping), `requireFinite` guarding values that persist to TradingView cloud
state, structured error handling, 84 tools.

**FRAGILE for live trading, flagged explicitly:** requires a GUI desktop app with a logged-in
session and a debug port open; no SLA; breaks on TradingView app update; poll-based with a
300–2000 ms floor; no data-integrity guarantees. **Using it as a live signal-generation or
execution dependency would be the single most dangerous architectural choice available.**

---

## Execution Audit

> **If the bot generated a valid signal right now, can it safely turn that into a real trade and
> know with certainty what happened?**
>
> **No. Not one component of the path exists.**

Every item below is **MISSING**, evidenced by a repo-wide identifier search returning 2 hits, both
in a test asserting absence:

broker integration · prop-firm integration · order creation · market/limit/stop orders ·
SL/TP placement · partial fills · rejected orders · cancelled orders · duplicate-order protection ·
order ids · idempotency · acknowledgement · execution confirmation · slippage model ·
latency handling · retry policy · network-failure handling · broker disconnect handling ·
position reconciliation · startup reconciliation · orphan order/position detection ·
manual intervention · emergency flatten · kill switch.

The only design work that exists is prose: `BOT_IMPLEMENTATION_AUDIT.md` §8 specifies a
`client_order_id` derived from immutable signal fields, and `bot/contracts/engine.py` declares the
boundary. **Neither is implemented.**

---

## Risk Audit

`trader/risk_engine.py` (113 LOC) + `trader/prop_rules.py` (162 LOC) exist. **Neither is imported
by anything** — 0 external importers. Both target the V38 strategy and a LucidFlex prop account.

What is right: sizing derives from stop distance (`per_contract = stop_distance * point_value`),
never a fixed contract count; martingale and size-up-on-wins are explicitly excluded; risk scales
down with losing streaks and near targets; a daily stop exists.

**Three findings, verified by executing the code:**

**R-1 · Unit ambiguity (dangerous).** `risk_for(..., stop_distance, point_value, ...)` has no unit
in its signature; the module docstring says *"Stop distances in dollars"* and the demo column is
labelled `stop$` — but the demo passes `8.0` with `point_value=10.0`, i.e. **8 price points**, not
$8. The math is right; the documentation contradicts it. A caller who believes the docstring and
passes dollars would mis-size by the multiplier — **10× for MGC, 2× for MNQ**.

**R-2 · The minimum-size override can exceed the risk budget.** Verified numerically on a
LucidFlex 50K account (buffer $2,000, intended per-trade risk $300):

| stop | per-contract risk | contracts taken | actual risk |
|---|---|---|---|
| 8 pt | $80 | 3 | $240 ✓ |
| **40 pt** | **$400** | **1** | **$400 — 33% over budget** |
| 150 pt | $1,500 | 0 | blocked ✓ |

The clause `if n < 1: if buffer_ > per_contract * 3.0: n = 1` deliberately takes one contract when
the budget cannot afford it. It is bounded (never more than a third of the buffer), so not
catastrophic — but it silently violates the stated per-trade risk.

**R-3 · No tick model at all.** There is no `tick_size` parameter anywhere. Stop distances are
never snapped to a tick, and no instrument specification table exists. `point_value` is passed in
by the caller with no validation.

**Missing entirely:** live account balance/equity, margin/leverage, maximum exposure, concurrent-
trade cap wired to anything, per-symbol limits, correlated exposure (MGC and MNQ traded together,
never considered), session restrictions, news restrictions, emergency shutdown.

Note: A2 independently **derived and verified** the correct point values from the committed ledger
— MGC $10/pt, MNQ $2/pt, $3.00 round-trip cost — and `bot/strategy/v53/engine.py` now *requires*
an explicit positive `point_value`, refusing V53's silent `1.0` fallback. That is the right
pattern; it just is not connected to a risk engine.

---

## Position / Reconciliation Audit

Every transition below is **MISSING**. There is no store, no identifier, no recovery:

| transition | state stored | identity | survives restart | reconciled |
|---|---|---|---|---|
| Signal → Candidate | MISSING | MISSING | MISSING | MISSING |
| Candidate → Risk approval | MISSING | — | — | — |
| → Order submitted | MISSING | MISSING | MISSING | MISSING |
| → Acknowledged | MISSING | — | — | — |
| → Filled | MISSING | — | — | — |
| → Position opened | MISSING | — | — | — |
| → SL/TP active | MISSING | — | — | — |
| → Modified | MISSING | — | — | — |
| → Closed | MISSING | — | — | — |
| → Result recorded | Pine table, **40-row cap**, read by eye | — | no | no |

Crash mid-flight, network death, fill-while-offline, broker-says-filled-vs-local-pending: **none
is handled, because no process exists to crash.** The one identity work that exists is analytical
— the Phase 13G primary/alternative event keys — and the contracts correctly document that these
are *analysis* identities and must never be used as order idempotency keys.

The Pine ledger's 40-row cap is worth flagging: it silently truncates. It never bit in Phase 15
(largest cell: 10 fills) and A2 detects it, but it is a live truncation risk for any longer run.

---

## Research / Backtesting Audit

The strongest part of the repository, and it must be judged on three separate axes.

**Strategy validity — GOOD.** Deterministic runs, frozen inputs, hash-pinned provenance, an
explicit provenance correction when canonical ≠ executed, train/test separation (folds A/B/C),
pre-registered OOS, parameter ablations (Phase 15 A–G), event clustering under two identities,
execution-level *and* event-level accounting, exact binomial tests, Clopper–Pearson intervals,
a pre-registered power analysis honest enough to state that N=80 detects only a *large* edge.

**Execution realism — POOR, and known.** Two optimistic assumptions are baked in and were
correctly identified rather than hidden:

1. **Touch ⇒ fill.** §2 fills on `low <= E`. A resting limit merely touched may not fill.
2. **The fill bar is never judged.** `bIn = 0` at fill, `b = bIn + 1` in §1, so the bar on which
   the fill occurs is never checked for an adverse excursion. Assertion K25 cannot catch this —
   it is 0 *by construction*, not by validation.

Both flatter every result in Phases 13F/14/15. Also absent: slippage, spread, latency, partial
fills, rejected orders, missed trades, queue position. Costs are a flat $3.00 round trip.

**Production reliability — NOT ADDRESSED.** The research framework never models a disconnect, a
restart, or a broker. Monte Carlo exists (`trader/montecarlo.py`) but for prop-pass probability
on V38, not for this.

**Do not confuse these three.** A strategy that is valid in research can still be unprofitable
live purely through (2), and can still be untradeable through (3).

---

## Testing Audit

| class | present | notes |
|---|---|---|
| unit | **YES** | 318 Python tests pass (275 `bot/`, 43 `p16/`); Node 191 blocks |
| integration | PARTIAL | `tests/e2e.test.js`, 79 blocks — **requires a live TradingView Desktop**, excluded from CI |
| regression / golden fixture | **YES** | 24 golden fixtures, deterministic extraction asserted in CI |
| strategy parity | **NO** | B3 not started; blocked on OHLCV |
| data integrity | PARTIAL | strong in `bot/data/bars.py`; **absent in the live path** |
| execution | **NONE** | no code to test |
| risk | **NONE** | `trader/` has one self-contained demo, no assertions |
| failure recovery | **NONE** | |
| end-to-end | **NONE** | |

**Correction of a false alarm, stated because it would otherwise mislead:** `npm run test:unit`
currently reports **21 of 43 failing** in this container. Every failure is
`ERR_MODULE_NOT_FOUND: chrome-remote-interface` — `node_modules` was never installed here. CI runs
`npm ci` first, so **CI is not red on this basis.** I am not claiming the Node suite is green; I
am saying this container cannot determine it.

**Where tests give false confidence:** `e2e.test.js` is 1,590 LOC and 79 blocks — it *looks* like
substantial coverage and is not automated coverage at all. And the 318 passing Python tests cover
contracts, guards, fixtures and the strategy engine — **none of which is in a live path**.

**Concrete missing-test list:** bar-close/forming-bar rejection · gap/stale/duplicate/out-of-order
rejection · strategy bar-for-bar parity (all 24 cells) · sizing determinism and limit enforcement ·
unit-mismatch regression for R-1 · order idempotency under replay/restart/duplicate delivery ·
partial fill · rejected order · rejected *stop* (unprotected position) · broker disconnect
mid-submission · `kill -9` at each lifecycle point · reconciliation divergence detection ·
kill-switch latch across restart · clock skew · disk full · paper-trading end-to-end.

---

## Reliability / Failure Modes

| failure | classification | evidence |
|---|---|---|
| Internet outage | **unhandled** | no live path exists |
| TradingView outage | **dangerous** | sole data source; no fallback |
| MCP failure | partially handled | CDP retries 5×; no data-integrity recovery |
| Cloudflare/tunnel failure | **N/A** | no tunnel in this repository |
| Broker API failure | **N/A** | no broker |
| WebSocket disconnect | **N/A** | polling, not sockets |
| Stale market data | **dangerous** | no staleness detection at all |
| Missing candle | **dangerous** | no gap detection |
| Malformed data | partially handled | `requireFinite` at the CDP edge only |
| Duplicate candle | **unhandled** | no detection |
| Clock drift | **unhandled** | no NTP check; bar clock is load-bearing |
| Process crash | **unhandled** | no persistence, no supervision |
| Machine reboot | **unhandled** | no service unit, no autostart |
| Python exception | **unhandled** | no runtime to catch it |
| Node process crash | **unhandled** | no supervisor |
| Database failure | **N/A** | no database |
| Corrupted state | **N/A** | no state |
| Rejected order / partial fill / unexpected position or balance | **N/A** | no execution |
| API rate limit / auth expiry | **unhandled** | rides the desktop session; expiry not detected |

---

## Security Audit

**Clean, and verified two ways.** A working-tree scan for credential-shaped assignments returns
**0**. A scan of the **entire git history** (`git log --all -p`) for high-entropy secret
assignments returns **0**, and no `.env`, `.pem`, `.key`, `.p12`, `credential` or `id_rsa` file has
**ever** been committed. No secret appears in this report because none was found.

Configuration surface is minimal: `TV_CDP_HOST`/`TV_CDP_PORT` and OS paths. `.gitignore` already
covers `.env`, `*.key`, `*.pem`, `secrets/`, `bot/var/` and SQLite files — added ahead of need.

**Findings:**

- **S-1 (medium) · `ui_evaluate` is an arbitrary-JS-execution MCP tool.** `src/tools/ui.js:88`
  exposes `Execute JavaScript code in the TradingView page context`. Anything holding the MCP
  channel gets full page context on an authenticated TradingView session — read/modify charts,
  scripts, alerts, account UI. Appropriate for a local research tool; **must not be exposed on any
  trading host**, and never over a network transport.
- **S-2 (medium) · CDP port 9222 is unauthenticated by design.** Any local process can drive the
  logged-in session. Fine on a trusted workstation; unacceptable on a shared or cloud host.
- **S-3 (informational) · No auth on the MCP server.** It is stdio-only, so exposure is inherited
  from whoever runs it. This changes the moment anyone puts it behind a network transport.
- **S-4 (future) · No secrets management exists** because no secrets exist. Broker keys, account
  ids and any webhook secret will need real handling before P1.

---

## Observability Audit

The operator cannot answer the required questions. Assessed literally:

| question | answerable today? |
|---|---|
| Why did it trade? | **No** — no decision journal |
| Why didn't it trade? | **No** — funnel counters exist in a Pine table, read by eye |
| What order did it send? | **No** — no orders |
| What happened to that order? | **No** |
| What position does the broker have? | **No** |
| What does the bot think the position is? | **No** — no position model |
| Are those consistent? | **No** — no reconciliation |

Missing: structured logs, correlation/trade/sequence ids in logs, health endpoint, heartbeat,
latency metrics, data-freshness metrics, connectivity monitoring, risk-state exposure, alerting,
dashboards, notifications.

Present: `src/core/health.js` (447 LOC) — a *research* health check (CDP reachable, chart loaded,
UI buttons present, git update available). Useful; not operational monitoring.

---

## Deployment / Operations Audit

> **If the computer reboots at 03:00 while a trade is open, what happens?**
>
> **Nothing restarts, and there is no trade to lose — because nothing can open one.** Traced
> concretely: there is no service unit, no supervisor, no autostart, no persisted state, and no
> reconciliation. If such a bot existed on this codebase today, a reboot would orphan the position
> at the broker with zero local record, and nothing would notice.

No OS target, no process manager, no Docker, no service startup, no auto-restart, no crash
recovery, no log rotation, no backups, no database, no monitoring, no deployment procedure, no
rollback, no config validation. Launch is manual: `scripts/launch_tv_debug.{bat,vbs,sh}` starts
TradingView with a debug port, then `npm start` runs the MCP server in the foreground.

---

## Performance / Latency Audit

Bottlenecks measured from code, not guessed:

| stage | latency | matters for V53? |
|---|---|---|
| market data (poll) | **300–2000 ms** floor, per `src/core/stream.js` | **No** |
| CDP `Runtime.evaluate` round trip | ~ms–tens of ms | No |
| bar processing (Python engine) | µs — 275 tests in 0.3 s | No |
| signal generation | one pass per 5m bar close | No |
| order submission | **N/A** | — |
| broker acknowledgement | **N/A** | — |

**V53 is a 5m bar-close strategy with entries resting as limit orders at a pre-computed FVG edge.**
Latency is genuinely not the constraint — a 2-second poll is irrelevant against a 300-second bar.
**Do not optimise any of this.** The real bottleneck is correctness and reliability, not speed.
The one timing property that *does* matter is detecting the bar close accurately, which is P0-4.

---

## Configuration / Environment Audit

There is **no single authoritative configuration**. What exists:

- **Env**: `TV_CDP_HOST`/`TV_CDP_PORT` (+ aliases). That is the entire runtime config surface.
- **Hard-coded in Pine**: all 12 frozen strategy inputs — correct and intentional.
- **Hard-coded in Python**: frozen constants duplicated in `bot/strategy/v53/constants.py` and
  `trader_v2/p16/p16_analyze.py`; both pin the same values, and tests assert them against the
  artifact — acceptable, but it is duplication.
- **Hard-coded account model**: `trader/prop_rules.py` embeds four LucidFlex tiers.
- **Manual/undocumented**: which symbol and timeframe the chart must be on; which Pine build is
  loaded; instrument point values (derived, not configured).
- **Research vs production inconsistency**: research configures by *editing Pine inputs in a GUI*;
  the Python engine configures by `V53Config`. There is no shared config source.

---

## Production Parity Matrix

| Component | Research | Backtest | Paper | Live | Same logic? | Status |
|---|---|---|---|---|---|---|
| market data | TV chart scrape | same | — | — | n/a | **RESEARCH ONLY** |
| bar construction | TV internal | TV internal | — | — | n/a | **MISSING outside TV** |
| sweep | Pine | Python | — | — | **unproven** | PARITY UNPROVEN |
| pivot | Pine | Python | — | — | **unproven** | PARITY UNPROVEN |
| CHOCH | Pine | Python | — | — | **unproven** | PARITY UNPROVEN |
| retest | Pine | Python | — | — | **unproven** | PARITY UNPROVEN |
| BOS | Pine | Python | — | — | **unproven** | PARITY UNPROVEN |
| displacement | Pine | Python | — | — | **unproven** | PARITY UNPROVEN |
| FVG | Pine | Python | — | — | **unproven** | PARITY UNPROVEN |
| entry | Pine | Python | — | — | **unproven** | PARITY UNPROVEN |
| stop | Pine | Python | — | — | **unproven** | PARITY UNPROVEN |
| target | Pine | Python | — | — | **verified** (58/58 rows) | OK |
| timeout | Pine | Python | — | — | **verified** (58/58 rows) | OK |
| sizing | `trader/` (V38) | — | — | — | **different strategy** | **MISSING** |
| slippage | none | none | — | — | — | **MISSING** |
| order execution | — | — | — | — | — | **MISSING** |
| position management | — | — | — | — | — | **MISSING** |
| trade ledger | Pine table (40-cap) | Python ledger row | — | — | **verified** | PARTIAL |

**Paper and Live columns are empty for every row.** That is the audit's central fact.

---

## Hypothetical Trade Trace

*A valid MGC long V53 setup occurs at 14:32:17.*

| # | step | status |
|---|---|---|
| 1 | market data arrives | **UNSAFE** — only if a human has TradingView open; poll-based; would read the forming bar |
| 2 | 5m state updated | **MISSING in production** — `SweepEngine` exists offline with no feed |
| 3 | 1m/3m sequence detected | **MISSING in production** — `SequenceMachine` exists offline with no feed |
| 4 | signal represented | **PARTIAL** — `StrategySignal` contract exists; nothing emits it into a runtime |
| 5 | risk calculated | **MISSING** — `trader/risk_engine.py` unwired, targets V38, unit-ambiguous |
| 6 | order size calculated | **UNSAFE** — see R-1/R-2/R-3 |
| 7 | order constructed | **MISSING** |
| 8 | order sent | **MISSING** |
| 9 | acknowledgement received | **MISSING** |
| 10 | fill state recorded | **MISSING** |
| 11 | SL/TP handled | **MISSING** — modelled in Pine only |
| 12 | position monitored | **MISSING** |
| 13 | position closed | **MISSING** |
| 14 | result recorded | **PARTIAL** — a Pine table row, 40-row cap, read by eye |
| 15 | crash recovery | **MISSING** at every step |

**Nothing happens.** The setup would appear as a row in a chart table if a human were watching.
Steps 5–15 have no code.

---

## Decisions Required

**D-1 · Is TradingView a data source for live trading, or research only?**
Options: (a) research only + a real vendor feed; (b) TradingView as the live feed via CDP.
Repo state: (b) is all that exists, and it reads the forming bar.
**Recommend (a), firmly.** (b) requires a GUI, a logged-in session and a debug port, has no SLA,
breaks on app update, and polls. Everything in Phases B/D depends on this.

**D-2 · Where does the strategy run in production — Python or Pine?**
Options: (a) Python engine is authoritative, Pine is the research oracle; (b) Pine on TradingView
emits alerts, a bot executes them.
Repo state: the Python engine exists and is untested against bars; (b) has no webhook receiver.
**Recommend (a).** (b) makes a GUI a hard execution dependency and cannot be unit-tested.
Blocks: B3, the entire execution layer.

**D-3 · Which broker / prop firm?**
Repo state: none integrated; `prop_rules.py` assumes LucidFlex.
Unresolved and blocking: order model, idempotency semantics, reconciliation API, sandbox
availability. **Nothing in the execution phase can be specified until this is chosen.**

**D-4 · Execution language: Python or Node?**
Repo state: Node is the MCP bridge with no execution role; all new work is Python.
**Recommend Python throughout.** Do not split the bot across two languages.

**D-5 · Persistence.**
Options: SQLite (WAL, one file) / Postgres / files.
**Recommend SQLite.** A handful of rows per 5m bar; relational; crash-safe; a server DB adds an
operational failure mode for no benefit. `.gitignore` already anticipates it.

**D-6 · Where does the OHLCV for B3 parity come from?**
**This is the immediate blocker.** Golden fixtures record *results*, not bars. Options: export
from TradingView; buy/obtain a vendor history; capture forward. Each has provenance implications
for Gate 1. **Nothing in Phase C can complete until this is answered.**

**D-7 · Convergent-signal policy.**
Phase 13G established the frozen spec *permits* convergence with **no deduplication rule** (69% of
baseline fills in multi-fill clusters, largest 3). Strategy-level dedup would be a rule change.
**Recommend: no strategy dedup; an explicit, off-by-default, separately-reported concurrency cap
in the risk engine.** Decide before the execution layer, not after.

**D-8 · Deployment target.** Single trusted host vs cloud. Determines secrets management
(`.env` vs a secret manager) and the whole of Phase K.

---

## Complete Implementation Roadmap

Phases in dependency order. This supersedes nothing in `BOT_IMPLEMENTATION_ROADMAP.md`; it
re-grounds it in what now exists.

### Phase A — Foundations · **DONE** (`ade51b3`, `acdb8e1`, `649cd17`, `c308dea`)
Guards, golden fixtures, contracts, session calendar. 318 tests. No action.

### Phase B — Data Acquisition · **P1, and the current critical path**
*Objective:* obtain and freeze the OHLCV that B3 needs.
*Why:* without bars, strategy parity cannot be measured and every downstream gate is unearned.
*Exists:* `bot/data/bars.py`, `bot/fixtures/loader.py`, the pre-FE guard.
*Missing:* the bars themselves; a loader; a provenance record for them.
*Depends on:* **D-6**.
*Tasks:* choose a source; export 5m + 1m/3m for 8 cells over folds A/B/C; hash and freeze; write
a guarded loader; record provenance.
*Acceptance:* **"A frozen, hash-recorded bar set exists for all 24 cells, every timestamp is
pre-FE, and re-loading it is byte-identical."**

### Phase C — Strategy Parity (Gate 1) · **P1**
*Objective:* prove the Python V53 is bar-for-bar V53.
*Exists:* the engine (1,414 LOC, 69 tests), golden fixtures, the comparator design.
*Missing:* the B3 harness.
*Depends on:* Phase B.
*Acceptance:* **"Given identical historical bars, Python reproduces all 17 funnel counters and
every ledger row for all 24 cells, with zero mismatches and no tolerance parameter."**
Until this passes, **treat the Python engine as unverified.**

### Phase D — Real-Time Data Engine · **P1**
*Objective:* a feed that never hands the strategy a bad bar.
*Missing:* everything — bar-close detection, gap/staleness/duplicate/out-of-order rejection,
reconnect semantics, a non-GUI source.
*Depends on:* D-1.
*Acceptance:* **"Disconnect the feed and the bot refuses to trade on stale data; inject a gap, a
duplicate and an out-of-order bar and each is rejected, never repaired; a forming bar never
reaches the strategy."**

### Phase E — Runtime & Persistence · **P1**
*Objective:* a 5m bar-close event loop whose state survives a restart.
*Exists:* `StrategyState`/`SequenceSlot` contracts.
*Missing:* the loop, SQLite schema, snapshot/rehydrate.
*Acceptance:* **"Snapshot at ≥20 random bars per cell, including inside every slot state 1–6,
restart from the snapshot, and the resulting ledger is identical to an uninterrupted run."**

### Phase F — Risk Engine · **P1**
*Objective:* an independent veto that sizes from the stop and enforces every limit.
*Exists:* `trader/prop_rules.py` as **design input only** — re-implement with tests, do not import.
*Missing:* instrument spec table (tick size, tick value, multiplier), unit-safe sizing, live
equity, exposure caps, correlated exposure, kill switch.
*Must fix:* R-1 (units), R-2 (over-risk override), R-3 (no tick model).
*Acceptance:* **"Given equity X and stop distance Y, sizing is deterministic, unit-tested against
a table of instruments, never exceeds the per-trade budget, and every limit provably blocks;
the kill switch latches across a restart."**

### Phase G — Execution Engine · **P1**
*Objective:* turn a signal into exactly one intended order and know its terminal state.
*Depends on:* **D-3**.
*Missing:* everything.
*Acceptance:* **"Every submitted order reaches a terminal known state or is reconciled from broker
state; a replayed signal, a restart mid-submission and a duplicated message all produce the same
`client_order_id` and exactly one broker order."**

### Phase H — Reconciliation · **P1**
*Acceptance:* **"An injected divergence — unknown position, unknown order, quantity or price
mismatch — is detected within one cycle, halts the engine, and latches the kill switch. It is
never auto-corrected."**

### Phase I — Paper Broker & Fill Realism · **P1**
*Objective:* measure the two optimistic assumptions instead of inheriting them.
*Acceptance:* **"Two fill models exist and are selected by config: `research_parity` reproduces
the Gate-1 ledger exactly; `conservative` requires trade-through and evaluates the entry bar. The
difference between them is reported as a software measurement and never as evidence about V53."**

### Phase J — Observability · **P1**
*Acceptance:* **"For any bar, the logs alone answer: why it traded, why it didn't, what order was
sent, what happened to it, what the broker holds, what the bot believes, and whether those agree."**

### Phase K — Failure Testing & Operations · **P2**
*Acceptance:* **"`kill -9` at each of six lifecycle points, a rejected stop, a partial fill then
disconnect, a 3-bar feed stall, a duplicate delivery and a full disk each end with no duplicate
order, no orphan position and no silent resumption."** Plus supervision, restart-storm limiting,
backup/restore, and a runbook.

### Phase L — Paper Soak · **P1/P2**
*Acceptance:* **"≥30 unattended sessions with zero unexplained discrepancies and clean
reconciliation every cycle."**
**Constraint:** before 2027-04-02 this must run on pre-FE replay or a **non-V53** strategy.
Running V53 forward *is* consuming the held-out window.

### Phase M — Live Gate · **P1**
*Acceptance:* **"Gates 0–L have committed evidence artifacts, AND Phase 16 has returned a
supportive verdict."** A working bot is not a reason to trade. `live_enabled` defaults false.

### Phase N — Hygiene · **P3**
Consolidate the six ledger parsers behind one tested module; remove the committed `=` file;
correct `STATE_OF_PLAY.md`; Python lint in CI; resolve the one TODO.

**Critical path:** B → C → E → G → H → K → L → M. **Phase B is the immediate blocker**, and it is
a data-sourcing decision (D-6), not an engineering task.

**Parallelisable from today:** Risk (F) needs only the contracts; Execution interface + paper
broker (G/I front half) need only the `Signal` schema; Observability (J) and Persistence (E back
half) are independent. Four tracks can run concurrently. **Do not parallelise inside Phase C** —
the state machine is one coupled artifact.

---

## Acceptance Criteria — consolidated

| subsystem | "done" means |
|---|---|
| **Data acquisition** | frozen, hash-recorded bar set for 24 cells; all pre-FE; byte-identical reload |
| **Signal engine** | identical historical bars → Python and Pine produce identical funnel counters and ledger rows, all 24 cells, zero mismatches |
| **Real-time data** | feed disconnect → refuses to trade; gap/duplicate/out-of-order/forming bar each rejected, never repaired |
| **Runtime/persistence** | kill at any bar, rehydrate, ledger identical to uninterrupted run |
| **Risk engine** | equity X + stop Y → deterministic size, unit-tested per instrument, never over budget, every limit blocks, kill switch latches across restart |
| **Execution** | every order reaches a terminal known state or is reconciled; replay/restart/duplicate → same id, one broker order |
| **Reconciliation** | injected divergence detected within one cycle, halts, latches; never auto-corrected |
| **Paper broker** | `research_parity` reproduces Gate 1 exactly; `conservative` differs measurably and the difference is reported as software, not edge |
| **Observability** | logs alone answer all seven operator questions |
| **Recovery** | kill −9 with an open position, restart, exact state reconstructed, no duplicate orders |
| **Live gate** | all gates evidenced **and** Phase 16 supportive |

---

## Definition of Production Ready

All of the following, simultaneously:

1. Gate 1 parity passes on all 24 cells with zero mismatches.
2. The live path never sees a forming, stale, duplicated, gapped or out-of-order bar.
3. State survives `kill -9` at any point and rehydrates exactly.
4. Every order has a deterministic idempotency key and a terminal known state.
5. Broker truth is reconciled every cycle; divergence halts and latches.
6. Sizing is unit-tested per instrument and provably cannot exceed its budget.
7. A latching kill switch and an emergency flatten exist and are tested.
8. The logs alone answer all seven operator questions.
9. ≥30 unattended paper sessions with zero unexplained discrepancies.
10. Secrets are managed, never logged, never committed.
11. The process is supervised, restarts safely, and has a tested backup/restore.
12. **Phase 16 has returned a supportive verdict.**

---

## Separation of Concerns — do not cross these

- **Strategy research** — V53 is frozen. Nothing in this audit is a reason to change it. Every
  optimistic assumption found (touch⇒fill, entry-bar blindness) is to be *measured in the
  execution layer*, never "fixed" in the strategy.
- **Engineering** — everything in the roadmap. None of it requires a strategy change.
- **Execution** — fill realism, slippage, latency. Belongs to the paper broker, not the strategy.
- **Operations** — supervision, deployment, monitoring.
- **Risk** — sizing and limits. A *policy* layer; it never alters a level.
- **Validation** — Phase 16, sealed until 2027-04-02. Bot results are never evidence about V53's
  edge, and Phase 16 results never justify architecture changes.

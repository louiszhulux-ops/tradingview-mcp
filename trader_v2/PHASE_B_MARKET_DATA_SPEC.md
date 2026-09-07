# Phase B — Market Data Architecture & Specification

**Design and investigation only. No production code was created or modified. `getOhlcv()`, the
V53 engine, Pine, Phase 16, the protocol, the analyser, strategy parameters, risk and execution
logic are all untouched. No dependency was added, nothing was deployed, no broker was contacted,
and no Phase 16 OOS result was run or inspected. This document is the only file created.**

Written at HEAD `f8b6167`, 2026-09-07. Every claim below was verified against the code, not
inherited from the audit.

---

## Executive Summary

The production market-data layer does not exist, and the research path that stands in for it
**cannot** be promoted to production. Three findings settle the architecture, and two of them are
decisive on their own.

1. **The forming-bar defect is real and worse than "an off-by-one".** `src/core/data.js:145-149`
   sets `end = bars.lastIndex()` and iterates `i <= end`. `lastIndex()` on TradingView's main
   series **is the currently-forming bar**. A repo-wide search for bar-completeness handling in
   `src/` returns **zero hits**. There is no `complete` flag, no close-time check, nothing.

2. **The feed reachable from this environment is delayed, and the repository already says so.**
   `trader_v2/HUMAN_TRADE_REGISTER.md` §5 records that `COMEX_MINI_DL:MGC1!` returns a delayed
   feed — the `_DL` suffix is TradingView's delayed-exchange marker — and that it was at one point
   **five days behind**. `PHASE16_PROTOCOL.md:107` names the instruments as
   `MGC1! (COMEX_MINI_DL)` and `MNQ1! (CME_MINI_DL)`. **A delayed feed cannot generate live
   signals.** This is not a judgement call about GUI fragility; it is an entitlement fact.

3. **V53 needs far less data than assumed, and that widens the provider field.** Traced from the
   frozen artifact: V53 references `volume` **zero** times, and the 5m `open` price **is never
   used** — the single textual match is the `open` argument on the LTF request line. The fetched
   LTF open (`aO`, line 97) is **assigned and never read again**. There is no `syminfo.mintick`
   dependency. The strategy's true requirement is **(timestamp, high, low, close)** at 5m and at
   the LTF, plus `syminfo.pointvalue` for USD conversion only.

**Recommendation: Option A — a direct licensed CME feed (Databento `GLBX.MDP3`, `ohlcv-1m`),
1-minute native, with 3m and 5m aggregated in-house under a tested rule. TradingView is demoted
to research and cross-validation only, and is removed from the production data path entirely.**

The one genuinely hard problem this creates is **continuous-contract parity**: TradingView's `1!`
rolls on a fixed per-symbol calendar rule applied uniformly through history, while a provider's
continuous symbology rolls on calendar, open interest or volume. These are not the same series.
That must be pinned before Phase C, and §7 and §21 specify how.

A second, previously unrecorded finding materially changes Phase C: **the fold A 1-minute runs
were themselves LTF-truncated**. `foldbars 10386` against `w/LTF 9813` means **573 parent bars
(MGC) and 556 (MNQ) had no LTF data at all**, because `request.security_lower_tf` caps at 100,000
values per field. Pine did not see complete 1m data for the start of fold A. **Supplying complete
1m data for that window would produce more sequences than the golden fixtures record and would
fail parity for reasons that have nothing to do with the strategy.**

---

## Current Data Architecture

Traced from code. This is what exists, not what was intended.

```
TradingView Desktop (Electron GUI, logged-in, DELAYED entitlement for MGC1!/MNQ1!)
        │
        │  Chrome DevTools Protocol, 127.0.0.1:9222, unauthenticated
        │  src/connection.js — 5 retries, 500 ms base backoff, liveness probe
        ▼
  Runtime.evaluate() of JS source strings against the page
        │
        │  window.TradingViewApi._activeChartWidgetWV.value()
        │        ._chartWidget.model().mainSeries().bars()
        ▼
src/core/data.js::getOhlcv        ← reads bars.firstIndex()..bars.lastIndex() INCLUSIVE
src/core/stream.js::pollLoop      ← 300–2000 ms poll-and-diff, dedupe on change
        ▼
src/tools/*.js → src/server.js — 84 MCP tools over stdio
        ▼
  a human or an LLM reads the numbers
        ▼
  Pine tables read by eye → hand-copied into trader_v2/**/runs/*.txt
        ▼
  trader_v2/*.py — regex parsers → markdown research reports
```

Component-by-component:

| component | source | protocol | format | timestamps | hist/live | bars complete? | late data | duplicates | out-of-order | reconnect | gaps detected | survives restart |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TradingView chart buffer | TV servers | proprietary | in-memory JS array | epoch, bar **open** | both | **NO** | possible | possible | unknown | app-level | **NO** | n/a |
| `connection.js` | CDP | WebSocket/CDP | JS eval | — | — | — | — | — | — | **yes**, 5×backoff | — | no |
| `getOhlcv` | chart buffer | — | `{time,open,high,low,close,volume}` | as provided | both | **NO — includes forming bar** | — | **not checked** | **not checked** | — | **NO** | no |
| `stream.js` | `getOhlcv`/quote | poll | JSON lines to stdout | — | live | **NO** | — | dedupe-on-change only | **not checked** | inherits | **NO** | no |
| hand-copy to `runs/*.txt` | human | — | Pine table text | UTC "YYYY-MM-DD HH:MM" | historical | n/a | n/a | n/a | n/a | n/a | n/a | files persist |
| `bot/data/bars.py` | **nothing** | — | `Bar`/`ParentBar` | epoch ms, open+close | — | **validated** | — | **rejected** | **rejected** | — | **partially** | n/a |

**There is no normalization layer, no bar construction, no storage, and no strategy consumer in
the live path.** `bot/data/bars.py` is the only component with real validation and **nothing feeds
it** — every external import of `bot.strategy.v53` in the repository is a test.

**Export ceiling:** `MAX_OHLCV_BARS = 500` per call (`src/core/data.js:7`). History paging exists
via `requestMoreData(1000)` (`src/core/chart.js:185`), so a bulk export is possible but would take
~21 calls for fold A's 10,386 5m bars and ~200 calls for 100,000 1m bars, against a lazy-loading
GUI.

---

## Verified Current Problems

Each independently verified against source.

**B-1 · The forming bar reaches every consumer.** `src/core/data.js`:

```js
var end = bars.lastIndex();
var start = Math.max(bars.firstIndex(), end - LIMIT + 1);
for (var i = start; i <= end; i++) { ... }     //  <= end  ⇒ includes the forming bar
```

*Where it enters:* `bars()` is the live main-series array; its last element mutates on every tick
until the bar closes. *Who sees it:* every caller of `getOhlcv` — the MCP tool `data_get_ohlcv`,
the CLI, and `stream.js::streamBars` (which explicitly fetches the **last** bar every 500 ms).
*Does the code distinguish forming from closed?* No — `grep -rniE "closed bar|complete|partial
bar|forming|unclosed" src/` returns **0**. *Does V53 require closed bars?* Yes, absolutely: every
decision resolves at a 5m close, `request.security_lower_tf` hands the whole LTF array at the
parent close, and §1/§2/§3 all run on closed 5m bars.

**Exact failure mode.** A poll at 14:32:17 returns a 14:30 bar whose `high`, `low` and `close` are
the running values, not the final ones. If a strategy consumed it: (a) a sweep can appear and then
vanish when the low retraces — a repaint; (b) an FVG fill can register on a wick that the close
erases; (c) the same 14:30 bar is processed on **every poll** — up to 600 times in five minutes —
so any stateful engine double-counts unless it dedupes, and `stream.js` dedupes only on *value
change*, which a forming bar does constantly. **Yes, a bar can change after the strategy has
consumed it, and yes, a bar can be processed more than once.** Both are disqualifying.

**B-2 · No data-integrity checks whatsoever in the live path.** `grep -rniE "gap|stale|
out.of.order|missing.*bar|monotonic" src/` returns 2 hits, **both about screenshot rendering**.
No staleness bound, no gap detection, no duplicate rejection, no ordering guarantee.

**B-3 · The feed is delayed.** Recorded in `HUMAN_TRADE_REGISTER.md` §5 and in the frozen Phase 16
protocol's own scope table. `_DL` = delayed exchange feed.

**B-4 · The LTF stream is capped at 100,000 values per field.** Evidenced directly: every 1m run
file reports exactly `LTFbars 100000`, while 3m reports 34,239–34,269 (= 5/3 × 20,567 chart bars,
i.e. untruncated). ≈ 69 days of continuous 1m, or ~101 calendar days at CME's 23 h × 5 d week.

**B-5 · Fold A 1m runs were truncated, and the fixtures prove it.** `foldbars 10386` vs
`w/LTF 9813` (MGC), `10368` vs `9812` (MNQ). The coverage start differs by LTF for exactly this
reason — 3m fold A starts `2026-05-24 22:00`, 1m fold A starts `2026-05-27 02:15` (MGC) /
`02:20` (MNQ), because `covFirst` is set on the first bar with `nL > 0`.

---

## V53 Data Requirements

Derived from the frozen artifact `V53_EXECUTED_BUILD.pine` (`2dafbafd…`) and from
`bot/strategy/v53/engine.py`, not assumed.

**Field census in the Pine source** (word-boundary counts): `low` 24, `high` 22, `time` 15,
`close` 7, `open` **1**, `volume` **0**.

The single `open` is the argument on line 97:
`aO = request.security_lower_tf(syminfo.tickerid, ltfStr, open)`. Every line mentioning `aO` is
line 97 plus four `asiaOn` substring matches. **`aO` is fetched and never read.**

The Python engine agrees: `engine.py:155` reads `bar.high, bar.low, bar.close` and `bar.open_ts_ms`;
`engine.py:197-198` reads `sub.high, sub.low, sub.close` and `sub.open_ts_ms`. It reads neither
`open` nor `volume` nor `close_ts_ms` for computation.

| requirement | 5m | LTF (1m/3m) | notes |
|---|---|---|---|
| timestamp | **required** | **required** | Pine `time` = bar **OPEN**; fold gate, day roll, Asia window and every ledger field key off it |
| high | **required** | **required** | sweeps, pivots, ATR, displacement, FVG, outcomes |
| low | **required** | **required** | as above |
| close | **required** | **required** | sweep close-back-inside, CHOCH/BOS break-on-close, ATR |
| open | **not used** | **not used** | supply it (the `Bar` contract validates OHLC coherence) but its value cannot affect V53 |
| volume | **not used** | **not used** | zero references |
| session info | derived | — | PDH/PDL roll on the CME session day; Asia window on UTC. Both resolved in `bot/U1_CME_SESSION_CALENDAR.md` |
| tick size | **not used** | — | no `mintick` reference. Needed by *execution*, never by the strategy |
| point value | **required** | — | `syminfo.pointvalue`; USD only, does not alter R. MGC $10/pt, MNQ $2/pt — derived and verified in A2 |
| contract multiplier | = point value | — | same quantity |
| trading hours | **required** | — | 17:00 → 16:00 America/Chicago, break 16:00–17:00 |
| timezone | **required** | — | two calendars, deliberately different (see §Time) |

**Consequence for provider selection:** an OHLCV-1m schema is more than sufficient; a full order
book or tick feed is unnecessary. Open and volume may be present and are simply ignored.

**Scope:** instruments MGC1!, MNQ1!; directions long and short; timeframes 5m primary with 1m and
3m as alternative LTFs — 8 cells (2 × 2 × 2). Direction is a strategy input, not a data axis: it
does not change the data requirement.

---

## Data Source Investigation

Only genuinely viable sources are listed. Evaluated against the actual requirement above.

| criterion | **A. Databento GLBX.MDP3** | **B. Broker feed (TBD)** | **C. TradingView / CDP (current)** |
|---|---|---|---|
| MGC availability | yes — dedicated catalog entry | depends on D-3 | yes, **delayed (`_DL`)** |
| MNQ availability | yes — dedicated catalog entry | depends on D-3 | yes, **delayed (`_DL`)** |
| 1m bars | native `ohlcv-1m` schema | typically yes | via `security_lower_tf`, **100k cap** |
| 3m bars | aggregate from 1m | usually aggregate | via `security_lower_tf` |
| 5m bars | aggregate from 1m (or `ohlcv-1h`/`-1d` for others) | usually native | native chart resolution |
| historical depth | full MDP 3.0 history | usually shallow | GUI lazy-load, 500/call |
| real-time feed | yes, live API | yes | **delayed for these symbols** |
| bar-close semantics | explicit, schema-defined | broker-defined | **none — forming bar exposed** |
| latency | sub-second | broker-dependent | **300–2000 ms poll + feed delay** |
| reliability | licensed CME distributor | broker SLA | **no SLA; GUI + debug port** |
| reconnect | documented client | broker client | CDP retry only; **no data-integrity recovery** |
| rate limits | documented, per-plan | broker-specific | none, but GUI-bound |
| API stability | versioned public API | broker-specific | **undocumented internals; breaks on app update** |
| cost | paid; free signup credit | usually bundled | already paid (TV subscription) |
| futures contract handling | native, per-expiry + continuous | broker-native | continuous only |
| continuous contracts | `.c.0` symbology, selectable roll rule | broker-defined | `1!`, fixed calendar rule |
| timestamp quality | exchange-sourced | broker-sourced | TradingView-normalised |
| **production suitability** | **YES** | **conditional on D-3** | **NO** |

**A — Databento `GLBX.MDP3`.** Officially licensed CME distributor covering CME/CBOT/NYMEX/COMEX.
Provides an `ohlcv-1m` schema and continuous-contract symbology with selectable roll rules, and
its live APIs support continuous symbology. Direct catalog entries exist for both MGC and MNQ.
This is the only investigated option that satisfies every hard requirement.

**B — Broker feed.** Cannot be evaluated: no broker is chosen (**D-3**, still open from the
production audit). Worth keeping open, because a broker feed removes one vendor and guarantees
that the data used for signals matches the venue used for execution. Its historical depth is
usually inadequate for Phase C, so it is likely a *complement*, not a replacement.

**C — TradingView via CDP.** Excellent research instrument, **not a production data source**, for
five independently sufficient reasons: the entitlement is delayed; the forming bar is exposed with
no completeness concept; the LTF path is capped at 100k values; the transport is an unauthenticated
debug port into a GUI that breaks on app update; and there is no gap, staleness or ordering
guarantee anywhere in the path.

Sources considered and rejected as not viable here: free/scraped endpoints (no CME licence, no
reliability), exchange direct connectivity (cost and complexity far beyond a single-strategy bot),
and equity-oriented APIs without CME futures coverage.

---

## TradingView Assessment

**Verdict: A — research-only. Remove it from the production data path.**

This is not a rejection of a GUI-based tool on principle. The bridge is genuinely well built:
6,265 LOC, 84 tools, retry/backoff, `safeString` injection-proofing, `requireFinite` guarding
values that persist to TradingView cloud state, and 191 test blocks. It is the right tool for
driving Pine research, and it should keep doing exactly that.

| consequence | A. research-only *(recommended)* | B. production market data | C. production signal generation |
|---|---|---|---|
| GUI dependency | acceptable — operator-driven | **fatal** — a desktop app must run 24/7 | **fatal** |
| browser/Electron dependency | acceptable | breaks on app update, no version pinning | breaks silently |
| chart state | operator sets it | **hidden global state**: symbol, timeframe, loaded history all mutate the answer | worse — indicator inputs too |
| session state | operator logs in | login expiry halts trading, undetected | same |
| Cloudflare tunnel | **not present in this repo** | would have to be built | would have to be built |
| MCP transport | stdio, local | stdio is not a service transport | same |
| authentication | rides the desktop session | **none of its own**; port 9222 is open to any local process | same |
| latency | irrelevant for research | **delayed feed** + 300–2000 ms poll | disqualifying |
| reliability | good enough | no SLA | no SLA |
| reconnects | handled | handled at CDP level only, not for data integrity | same |
| hidden state | tolerable | **`lastIndex()` mutates under you** | same |
| data completeness | tolerable | **no completeness concept at all** | same |
| automation fragility | tolerable | GUI automation as a trading dependency | same |

**What TradingView keeps doing after Phase B:** running frozen Pine for research, executing the
Phase 16 boundary procedure, and — valuably — acting as an **independent cross-validation oracle**
for the new feed. Comparing provider bars against TradingView bars over the parity window is a
real test, and §Acceptance-Test-11 requires it.

---

## Continuous Futures Assessment

**This is the largest unresolved parity risk in Phase B, and it must be closed before Phase C.**

What the repository assumes today: the research ran on `COMEX_MINI_DL:MGC1!` and
`CME_MINI_DL:MNQ1!` — TradingView continuous front-month series. **Nothing in the repository
records the roll dates, the roll rule, or whether back-adjustment was enabled.** No code reads a
contract expiry; the symbol is a string.

What TradingView actually does: `1!` is the front/nearest-expiration continuous contract, and the
switching date is set from a **fixed per-symbol rule derived once from average volume statistics**
— e.g. "switch N business days before expiration" — then applied uniformly across the whole
history. It is **not** a live volume or open-interest crossover. Back-adjustment is a **chart
setting** (`B_ADJ`), not the default, so the default series carries raw roll gaps.

Why this matters more for V53 than for most strategies: V53 keys off **absolute price levels** —
PDH/PDL, 5m swing pivots, CHOCH/BOS levels, FVG edges, and a stop placed at the sweep extreme
± 0.20 × ATR. A roll discontinuity injects a synthetic gap that can manufacture a sweep, invalidate
a level, or distort ATR for 14 bars.

**Rolls fall inside the research window.** MGC (COMEX gold) trades Feb/Apr/Jun/Aug/Oct/Dec, so a
Jun→Aug roll lands in late May–June; MNQ is quarterly Mar/Jun/Sep/Dec, so a Jun→Sep roll lands
around mid-June. Fold A spans 2026-05-24 → 2026-07-15. **Both instruments almost certainly rolled
inside fold A.**

> **Can production safely use the same instrument representation for research and live trading?**
>
> **Not yet — and this cannot be assumed either way from the repository.** A translation layer is
> required, and its specification depends on an empirical answer to two questions that only a data
> pull can settle:
>
> 1. On what exact dates did `MGC1!` and `MNQ1!` roll during 2026-05-24 → 2026-08-30?
> 2. Was the research series back-adjusted or raw?

**Required translation layer (specified, not built):**

- A `ContinuousSeriesSpec` recording, per instrument: the roll rule (rule name + parameters), the
  back-adjustment mode (`none` | `ratio` | `difference`), the exact roll dates within any dataset,
  and the underlying contract in force per date range.
- A **frozen roll calendar** committed alongside the dataset, so replay is reproducible and the
  live feed can be configured to the *same* rule.
- Live trading must resolve the continuous symbol to a **concrete expiry** before order placement.
  A continuous symbol is a charting construct; **you cannot send an order to `MGC1!`**. This is an
  execution-layer requirement created by the data layer, and it belongs in Phase G.

**Recommended stance:** configure the provider's continuous symbology to the roll rule that
reproduces TradingView's dates over the parity window, and **verify empirically** — do not assume
`.c.0` equals `1!`. If no provider rule reproduces it, fall back to per-expiry contracts stitched
under our own frozen, committed calendar, which is deterministic and testable even if it differs
from TradingView. In that case Phase C parity must be scoped to a window with no roll, and the
divergence documented.

---

## Time / Session Model

The strategy's time semantics are already resolved and must not change. Restating them because the
data layer must honour them exactly.

| concern | canonical rule | source |
|---|---|---|
| **internal representation** | **UTC epoch milliseconds, integer** | `bot/data/bars.py`, `bot/guards.py` |
| bar timestamp semantics | **bar OPEN time** — Pine `time` is the open | verified: fold B coverage begins exactly at `FB` |
| bar close time | carried explicitly as `close_ts_ms = open + period` | `Bar.__post_init__` asserts the span |
| PDH/PDL day roll | **CME exchange-session day**, 17:00 America/Chicago | `bot/U1_CME_SESSION_CALENDAR.md`, `bot/calendar/cme.py` |
| Asia window | **UTC**, `hour(time,"UTC") < 7` | `V53_EXECUTED_BUILD.pine:57` |
| session | 17:00 CT → 16:00 CT; maintenance break 16:00–17:00 CT | U1, cross-checked against committed run coverage |
| weekend | dark Friday 16:00 CT → Sunday 17:00 CT | U1, verified: 0 of 290 event timestamps on a Saturday CT |
| DST | handled by `zoneinfo("America/Chicago")`; never a fixed offset | U1 — CDT open 22:00 UTC, CST open 23:00 UTC |
| holidays | advisory only; they remove bars, they do not move the boundary | U1 §5 |
| local machine time | **never used** — no wall-clock read in the decision path | `bot/contracts/engine.py` |
| TradingView time | boundary conversion only; never internal | — |

**Rule: UTC epoch-ms internally, everywhere. Convert only at the provider boundary and at the
human-readable edges.** The two strategy calendars stay separate — merging them redefines V53.

---

## Bar Completeness Model

`now >= bar_end` is **not** sufficient, and the reasons are concrete:

- a provider may emit a bar's final update *after* its end time (settlement, late prints);
- a delayed feed satisfies `now >= bar_end` while the bar has not been received at all;
- clock drift on the host makes `now` untrustworthy as a sole gate;
- an exchange may correct a bar after publication;
- a bar that never trades may not be emitted at all, so waiting for it blocks forever.

**Canonical rule — a bar is eligible for strategy consumption when all four hold:**

1. **Provider-attested close.** The source explicitly marks the bar final — a completed OHLCV
   record from the historical/aggregation endpoint, or a live message flagged as the bar's final
   state. *Never* infer closure from the array position of a mutable buffer.
2. **Successor evidence OR a bounded grace period.** Either a bar with a strictly greater
   `open_ts_ms` has been received, or `receive_clock ≥ bar_close_ts + GRACE` where `GRACE` is a
   configured constant (proposed: 2 s live, 0 in replay). Successor evidence is preferred because
   it does not depend on local time.
3. **Structural validity.** `low ≤ min(open, close) ≤ max(open, close) ≤ high`, positive finite
   prices, `close_ts − open_ts` exactly equals the timeframe period, and `open_ts` on a minute
   boundary. Already enforced by `bot/data/bars.py`.
4. **Sequence validity.** `open_ts` is strictly greater than the last emitted bar's for that
   (instrument, timeframe), and does not overlap it.

Once emitted, a bar is **immutable**. A late correction to an already-emitted bar is **not**
applied silently — see Data Quality below.

The rule is **deterministic** (no dependence on wall-clock in replay, where condition 2 reduces to
successor evidence), **testable** (each clause is a unit test), **restart-safe** (the last emitted
`open_ts` is the only state needed), **timezone-safe** (epoch-ms only), and **explicit**.

---

## Data Quality Model

| condition | detect | action | log | alert | halt trading? |
|---|---|---|---|---|---|
| **duplicate bar** (same `open_ts`, same content) | last-emitted `open_ts` per (instrument, tf) | **drop silently at the boundary**; never re-enter the engine | debug, counter | no | no |
| **duplicate with different content** | same `open_ts`, different OHLC | **quarantine, do not emit** | error | yes | **yes** — the source is inconsistent |
| **out-of-order** (`open_ts` ≤ last emitted) | ordering check | **reject**; never reorder in place | error | yes | **yes** until resynchronised |
| **missing bar** — genuine gap | expected next `open_ts` (from the session calendar) not received, and the session is open | **reject the stream**, trigger backfill | error | yes | **yes** until the gap is filled or explained |
| **missing bar** — legitimate absence | the calendar says the session is closed, or the instrument simply did not trade that minute | **normal**; record `ltf_count` honestly | debug | no | no |
| **corrupt** (`high < low`, close outside range, non-finite, non-positive, bad timestamp) | `Bar.__post_init__` | **reject, never repair** | error | yes | **yes** |
| **stale** (no new closed bar within `period + tolerance` while the session is open) | receive clock vs last bar | enter `STALE`; **refuse to trade** | error | yes | **yes** |
| **partial / forming bar** | absence of provider-attested close | **never emitted** — the boundary rejects it | debug | no | no |
| **late correction** to an already-emitted bar | content hash per emitted bar | **halt and quarantine**; a bar the strategy has consumed must never change under it | error | yes | **yes** — requires operator decision |
| **post-FE timestamp in a dev/replay path** | `bot/guards.py::assert_pre_fe` | raise `HeldOutDataError` | error | yes | **yes, fail closed** |

Two principles, both already embodied in `bot/data/bars.py` and to be preserved: **reject, never
repair**, and **a legitimate session gap is not an error** — the validator asserts strict ordering
and non-overlap, not a contiguous grid.

---

## Multi-Timeframe Architecture

**Recommendation: Architecture B — 1-minute native, with 3m and 5m aggregated in-house.**

```
Provider ohlcv-1m  ──►  validated 1m ClosedBar stream
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            5m aggregator        3m aggregator      (deterministic, tested, same code in
                    │                   │            research, replay, paper and live)
                    └────────┬──────────┘
                             ▼
                    ParentBar(5m) + nested LTF sub-bars  ──►  V53 engine
```

Why B over A (native per-timeframe from the provider):

- **One aggregation rule, used identically in replay and live.** With A, the provider's 5m
  aggregation is a black box that could differ between its historical and live endpoints — an
  invisible parity break.
- **The 5m ↔ LTF nesting is exactly what V53 needs.** `ParentBar` already models "one closed 5m
  bar plus the sub-bars it contains", which is the `request.security_lower_tf` equivalent.
  Building it from a single 1m stream makes the nesting trivially consistent; assembling it from
  two independent provider streams requires cross-stream reconciliation.
- **It resolves UNRESOLVED U3.** 3 does not divide 5, so a 5m parent holds 1 or 2 three-minute
  sub-bars, averaging 5/3 (verified: 34,269 / 20,567 = 1.6662 ≈ 5/3). Owning the aggregator means
  owning that assignment rule explicitly instead of inheriting an undocumented one.
- **Fewer entitlements and one reconnect path.**

The cost of B, stated plainly: **our aggregation must reproduce TradingView's, or Phase C parity
fails for reasons unrelated to the strategy.** That is a *testable* cost — see Acceptance Test 11 —
and it is far better than an untestable one.

Aggregation rule (to be implemented in Phase B, specified here): bars are bucketed by
`floor(open_ts_ms / period_ms) * period_ms` on the **UTC epoch grid**; `open` = first sub-bar's
open, `high` = max, `low` = min, `close` = last sub-bar's close, `volume` = sum (carried, unused);
a bucket with no 1m bars produces **no** parent bar; a partial bucket is emitted only when the next
bucket opens or the session closes. Each 3m/5m bar records the exact `open_ts` list of the 1m bars
that composed it, so any parity mismatch is diagnosable to the minute.

---

## Historical Data Requirements

**Warm-up, derived from the code — not "enough bars".**

| driver | requirement | source |
|---|---|---|
| `ta.atr(14)` on 5m | **14** 5m bars before any sweep can arm (`not na(atr) and atr > 0` gates §5) | line 34 |
| 5m swing pivot `ta.pivot*(high, 10, 10)` | **21** 5m bars — pivot at bar 10, confirmed at bar 20 | lines 71–72 |
| LTF ring buffer, `lSw = 3` | **7** LTF bars before the first LTF pivot confirms | `RB = 2·lSw+1` |
| PDH/PDL | **2 complete session rolls** — the first roll copies a partial day into `pdh`/`pdl` | lines 42–52 |
| Asia H/L | one **complete, closed** Asia window (`hUTC < 7` then ≥ 7) | lines 57–69 |
| max sequence lifetime | `dispWait 12 + retBars 24 + maxBars 144` = **180** 5m bars = **15 h** | lines 20/21/24 |

A CME session is 23 h = **276** 5m bars. Two complete rolls ≈ 552 bars; adding a full sequence tail
gives ≈ 732.

> **Live warm-up requirement: 3 full sessions = 828 closed 5m bars (~69 h), plus the matching 1m
> or 3m sub-bars.** The bot must refuse to trade until warm-up completes, and must say so.

**Phase C parity dataset — the exact requirement.**

| fold | window (UTC) | 5m bars | 1m LTF availability | 3m LTF availability |
|---|---|---|---|---|
| A | 2026-05-24 22:00 → 2026-07-15 23:55 | 10,386 (MGC) / 10,368 (MNQ) | **from 2026-05-27 02:15 (MGC) / 02:20 (MNQ) only** — 573/556 earlier parent bars had **none** | full |
| B | 2026-07-16 00:00 → 2026-08-07 20:55 | 4,668 | full | full |
| C | 2026-08-09 22:00 → 2026-08-30 23:55 | 4,164 | full | full |

**The fold A truncation must be reproduced, not repaired.** Pine ran with an empty LTF array for
those parent bars because of the 100,000-value cap; a dataset that supplies complete 1m data there
will generate sequences Pine never saw. The truncation boundary is recoverable exactly from the
fixtures, because `covFirst` is set on the first bar with `nL > 0`.

Plus warm-up **before** each fold's start (the strategy state is not reset at a fold boundary — the
fold gate only controls arming and the coverage counters), and a tail after fold C's end for
sequences that resolve late.

**Future backtesting:** the same shape, unbounded in length — which is precisely what the 100k cap
prevents today and what a direct provider removes.

---

## Restart / Recovery Requirements

The data layer must survive process restart, machine restart, reconnect, transient internet
outage, and provider outage. **Requirements only; the storage design is Phase E.**

State that must persist:

| item | why |
|---|---|
| last emitted `open_ts_ms` per (instrument, timeframe) | the sole ordering/duplicate authority; makes restart deterministic |
| provider cursor / subscription position | resume without re-reading or skipping |
| content hash of the last N emitted bars | detect a late correction to a bar already consumed |
| current data-layer state (below) and the reason for it | a `HALTED` layer must not silently resume as `LIVE` |
| warm-up completion marker and its window | avoid re-warming, and avoid trading un-warmed |
| the frozen roll calendar in force | a restart must not silently change the series |

Required capabilities: **gap-aware backfill** (on reconnect, request from `last_emitted_open_ts`
forward and validate contiguity against the session calendar before resuming live); **idempotent
re-emission** (a bar already emitted is dropped, never re-delivered to the engine); **fail closed**
(unknown or unrecoverable state ⇒ do not trade).

Note the interaction with the strategy: V53 carries ~30 parallel arrays of live sequence state
across up to 180 bars. **Data-layer recovery alone is not enough** — the engine's state must be
persisted and rehydrated too. That is Phase E; Phase B must not pretend to solve it.

---

## Latency Requirements

Derived from the strategy, not from ambition.

- A 5m bar closes on the 5-minute UTC grid. Every V53 decision resolves **at that close**.
- `request.security_lower_tf` hands the whole LTF array **at the parent close** — the LTF is an
  intrabar reconstruction, not an independent decision stream. No LTF information is actionable
  before the parent closes.
- The earliest a signal can be known is therefore **the 5m close itself**.
- Entries are **resting limit orders** at a pre-computed FVG edge, and §2 fills them on a *later*
  5m bar (earliest `emit_bar + 1`). The order can be placed any time before that next close.

| budget | requirement | rationale |
|---|---|---|
| bar delivery after close | **< 2 s** | leaves the rest of the interval for everything else |
| bar validation + strategy step | **< 500 ms** | measured: 275 Python tests run in ~0.3 s; a single bar step is microseconds |
| risk + order construction | **< 1 s** | not yet built |
| order submission → ack | **< 2 s** | broker-dependent |
| **total signal → resting order** | **< 10 s against a 300 s bar** | ~3% of the interval |

**Do not optimise for low latency.** A 2-second budget against a 5-minute bar is ample. The timing
property that actually matters is **detecting the close correctly**, which is the completeness
model — not speed. The current 300–2000 ms poll would be adequate *if* it delivered closed bars;
it is disqualified because it does not, and because the feed is delayed.

---

## Security Requirements

No secret is created, connected or exposed by this document. For reference, the repository is
currently **clean**: 0 credential matches in the working tree and 0 across the entire git history.

| requirement | specification |
|---|---|
| credentials needed | one provider API key (and, if the live and historical APIs differ, one per surface) |
| where they live | environment variables loaded from an un-committed `.env`; `.gitignore` already covers `.env`, `*.key`, `*.pem`, `secrets/` |
| are env vars sufficient? | **yes for a single trusted host** — the current deployment assumption. A shared or cloud host requires a secret manager (**D-8**) |
| rotation | required on any suspected exposure and on every operator change; the design must tolerate rotation without a code change |
| IP restrictions | to be confirmed with the provider at signup; if offered, **enable them** |
| logging | the key must never appear in a log line, an error message, a stack trace or a request echo. A redaction test asserting the configured secret is absent from a full session capture is **mandatory**, mirroring the pattern already specified for the bot |
| startup validation | fail fast and loudly if a required variable is missing; never fall back to an anonymous or delayed mode silently |

Note the contrast worth preserving: the current TradingView path needs **no** credential because it
rides a logged-in GUI session — which is exactly why it has no authentication boundary and why
port 9222 is open to any local process.

---

## Cost / Operating Model

Indicative categories only. **Exact pricing must be confirmed with the vendor at procurement time
— it is not stated here because it was not verified.**

| category | Option A (direct feed) | Option B (broker feed) | Option C (TradingView) |
|---|---|---|---|
| historical data | one-off or subscription for the parity window + backtest depth | usually unavailable at depth | already paid, but **capped and slow to export** |
| real-time data | monthly subscription | usually bundled with the account | already paid, but **delayed for these symbols** |
| API access | included | included | none (GUI automation) |
| exchange fees | CME licence fees may apply per-user | usually passed through | included in the TV plan |
| infrastructure | one small always-on host | same | **a desktop GUI must run 24/7** |
| storage | modest — 1m OHLCV for 2 instruments is small | same | n/a |
| monitoring | to be built (Phase J) | to be built | to be built |

Ranking, given this strategy and this repository:

1. **Best production choice — Option A (direct licensed feed).** The only one that satisfies
   entitlement, completeness, depth and reliability simultaneously.
2. **Best low-cost choice — Option B**, *if* the chosen broker's feed proves adequate. It removes
   a vendor and guarantees signal/execution data alignment. Blocked on **D-3**.
3. **Best development/testing choice — a frozen local dataset**, exported once and committed by
   hash. Zero recurring cost, perfectly reproducible, and it is exactly what Phase C needs.

These differ, and the difference is worth exploiting: **buy history once for Phase C, subscribe to
real-time only when paper trading actually starts.**

---

## Architecture Options

### Option A — Direct licensed feed → normalized bars → V53 *(recommended)*

```
Databento GLBX.MDP3 (ohlcv-1m, live + historical)
        ▼
  Provider adapter  ── normalizes to UTC epoch-ms, Decimal prices
        ▼
  Completeness gate ── provider-attested close + successor/grace + validity + ordering
        ▼
  Validator         ── duplicate / out-of-order / gap / corrupt / stale
        ▼
  Aggregator        ── 1m → 3m, 1m → 5m, deterministic, tested
        ▼
  ParentBar(5m + nested LTF)  ──►  V53 engine  ──►  risk ──► execution
```

*Advantages:* real-time entitlement; explicit bar-close semantics; unbounded history; no GUI; one
tested aggregation rule shared by replay and live; testable against TradingView as an oracle.
*Disadvantages:* new vendor, new cost, new credential; continuous-contract roll must be matched.
*Failure modes:* provider outage (→ `STALE`, fail closed), credential expiry (→ startup failure),
roll-rule mismatch (→ caught by Acceptance Test 11 before it matters).
*Parity implications:* the aggregation and the roll calendar are the two things to verify; both are
testable. *Complexity:* moderate. *Production suitability:* **high**.

### Option B — Broker feed → normalized bars → V53

Same pipeline, provider swapped. *Advantages:* one fewer vendor; signal data and execution venue
are identical, which removes a whole class of discrepancy. *Disadvantages:* historical depth is
usually insufficient for Phase C; quality varies enormously; **blocked on D-3**.
*Suitability:* **conditional** — likely the best *live* feed and a poor *historical* one, so
probably a complement to A rather than a replacement.

### Option C — TradingView extraction layer → V53

```
TradingView Desktop GUI ──CDP──► extraction ──► completeness shim ──► V53
```

*Advantages:* already built and paid for; identical to the research series by construction, which
makes parity trivial. *Disadvantages:* **delayed entitlement**, forming bar with no completeness
concept, 100k LTF cap, GUI/session/chart hidden state, no SLA, breaks on app update, 500-bar
export ceiling. *Failure modes:* silent login expiry, silent app update, silent chart-state change,
stale data indistinguishable from a quiet market. *Suitability:* **research only.**

**Hybrid worth noting:** Option C is the right way to *export the Phase C dataset* if buying
history is undesirable — it produces exactly the series Pine ran on. It remains unsuitable as a
live feed. Options A and C are not mutually exclusive; C is the oracle, A is the feed.

---

## Recommended Architecture

**Option A — a direct licensed CME feed (Databento `GLBX.MDP3`, `ohlcv-1m`), 1-minute native with
3m and 5m aggregated in-house, TradingView retained solely as a research tool and cross-validation
oracle.**

**Why.** Only Option A clears every hard requirement at once: a real-time entitlement (C is
delayed — the disqualifying fact, recorded in the repo itself), explicit bar-close semantics
(C has none), history beyond 100,000 LTF values (C is capped), and a transport that is not a GUI
debug port. The strategy's narrow field requirement — timestamp, high, low, close, no volume, no
open, no tick size — means a plain `ohlcv-1m` schema is sufficient, so no exotic or expensive
product is needed.

**What it replaces.** The `getOhlcv` → `lastIndex()` path as a *trading* input. That function is
not deleted and not modified in Phase B; it simply stops being on the production path.

**What it preserves.** Everything already built: `bot/data/bars.py` becomes the normalized type the
adapter produces; `ParentBar` is unchanged; the V53 engine is unchanged; `bot/calendar` supplies
session semantics; `bot/guards.py` continues to fail closed on held-out data; the whole MCP bridge
keeps its research role untouched.

**Risks that remain.** (1) **Continuous-contract roll mismatch** — the biggest one; mitigated by
pinning the roll calendar and by Acceptance Test 11. (2) **Aggregation mismatch** with TradingView
— mitigated by the same test, and diagnosable to the minute because each aggregate records its
constituent 1m timestamps. (3) **Fold A LTF truncation** — must be reproduced deliberately; the
boundary is recoverable from the fixtures. (4) **Vendor dependency** — mitigated by keeping the
adapter behind an interface so a second provider is a drop-in. (5) **Cost** — mitigated by buying
history once and subscribing to real-time only at paper-trading time.

**What needs to be built.** A provider adapter, a completeness gate, a validator, an aggregator, a
backfill/reconnect path, the data-layer state machine, the frozen dataset with a reproducible hash,
and the roll calendar. Sequence in the Implementation Plan below.

---

## Proposed Data Interface

Derived from the code, not from a template. The engine already consumes `ParentBar`; this
formalises what must reach it and what the layer guarantees.

```
ClosedBar                       # the atomic unit the layer emits
    instrument      str         # canonical internal id, e.g. "MGC1!"
    timeframe       Timeframe   # M1 | M3 | M5
    open_ts_ms      int         # UTC epoch ms, bar OPEN — the strategy's time
    close_ts_ms     int         # == open_ts_ms + period; asserted, not assumed
    open            Decimal     # required by the contract, UNUSED by V53
    high            Decimal     # required
    low             Decimal     # required
    close           Decimal     # required
    volume          Decimal?    # optional, UNUSED by V53
    # provenance — not consumed by the strategy, required for audit
    source          str         # provider id
    contract        str?        # concrete expiry in force, for continuous series
    composed_of     tuple[int]? # 1m open_ts values, for aggregates

ParentBar                       # what the V53 engine consumes  (already exists)
    bar             ClosedBar   # must be M5
    ltf_timeframe   Timeframe   # M1 | M3
    ltf_bars        tuple[ClosedBar, ...]   # oldest first; MAY be empty or short
```

**Guarantees the layer makes to the engine:**

| guarantee | statement |
|---|---|
| **completeness** | every emitted bar satisfies all four clauses of the completeness rule; a forming bar is never emitted |
| **ordering** | strictly increasing `open_ts_ms` per (instrument, timeframe); never reordered in place |
| **uniqueness** | an `open_ts_ms` is emitted at most once per (instrument, timeframe) |
| **immutability** | an emitted bar never changes; a late correction halts the layer rather than mutating history |
| **gaps** | a legitimate session gap is normal and is *represented*; an unexplained gap halts the layer. `ltf_bars` may be empty or short and that fact is reported, never repaired |
| **errors** | a validation failure raises and fails closed. The layer never returns a "best-effort" bar |
| **time** | UTC epoch-ms only; `open_ts_ms` is the bar OPEN, matching Pine's `time` |
| **provider opacity** | the engine cannot tell which provider produced a bar; `source` is provenance, never a branch condition |

The engine already refuses a non-5m parent and a 5m "LTF", so "an LTF stream substitutes for the
5m stream" is unrepresentable. That property must be preserved.

---

## Data-Layer State Machine

```
                 ┌──────────────┐
                 │ INITIALISING │  config validated, credentials present
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │  CONNECTING  │  ◄─────────────┐
                 └──────┬───────┘                │
                        ▼                        │
                 ┌──────────────┐                │
                 │ BACKFILLING  │  fetch from last_emitted_open_ts forward
                 └──────┬───────┘                │
                        ▼                        │
                 ┌──────────────┐                │
                 │  WARMING_UP  │  828 closed 5m bars + matching LTF
                 └──────┬───────┘                │
                        ▼                        │
                 ┌──────────────┐                │
                 │ SYNCHRONIZED │  contiguity verified against the session calendar
                 └──────┬───────┘                │
                        ▼                        │
                 ┌──────────────┐                │
             ┌──►│     LIVE     │  emitting closed bars in order
             │   └──┬────────┬──┘                │
             │      │        │                   │
             │      ▼        ▼                   │
             │  ┌───────┐ ┌──────────────┐       │
             │  │ STALE │ │ DISCONNECTED │───────┘
             │  └───┬───┘ └──────────────┘
             │      │
             │      ▼
             │  ┌────────────┐
             └──│ RECOVERING │  (via BACKFILLING → SYNCHRONIZED)
                └────────────┘

   any state ──► ┌────────┐   corrupt bar · late correction · unexplained gap ·
                 │ HALTED │   duplicate-with-different-content · out-of-order
                 └────────┘   LATCHED — requires an explicit operator action
```

**Trading eligibility — the safety contract:**

| state | may the strategy consume bars? | may the bot open a position? | may it manage an open position? |
|---|---|---|---|
| INITIALISING / CONNECTING / BACKFILLING | no | no | no — but existing positions must still be protected by resting broker stops |
| WARMING_UP | **yes** (state building) | **no** | no |
| SYNCHRONIZED | yes | **no** — one clean live bar required first | yes |
| **LIVE** | yes | **yes** | yes |
| STALE | no | **no** | yes — and consider flattening after a configured bound |
| DISCONNECTED | no | **no** | escalate to the operator |
| RECOVERING | no | **no** | yes |
| **HALTED** | **no** | **no** | **operator only** |

Two non-negotiables: **fail closed** — any state that is not `LIVE` forbids opening a position;
and **`HALTED` latches** — it never clears itself, and a restart does not clear it.

---

## Phase B Acceptance Tests

| # | test | criterion |
|---|---|---|
| 1 | **Closed-bar integrity** | Feed a provider stream containing an explicitly non-final bar; the layer emits nothing for it. **No forming bar can reach V53** under any input. |
| 2 | **Ordering** | For any input permutation, emitted `open_ts_ms` is strictly increasing per (instrument, timeframe). |
| 3 | **Duplicate handling** | Re-deliver an identical bar → dropped, engine step count unchanged. Re-deliver the same `open_ts` with **different** content → `HALTED`, nothing emitted. |
| 4 | **Gap detection** | Remove one bar inside an open session → detected, `HALTED`/backfill, never silently skipped. Remove bars across a weekend or holiday → **not** flagged. |
| 5 | **Reconnect** | Disconnect mid-stream and reconnect → no duplicate and no missing bar across the seam; emitted sequence identical to an uninterrupted run. |
| 6 | **Restart** | Kill the process at 20 random points and restart → the emitted sequence is identical to an uninterrupted run, with no re-emission. |
| 7 | **MTF integrity** | For every emitted 5m bar: `high` = max of its 1m constituents, `low` = min, `close` = last, and `composed_of` lists exactly the 1m bars in `[open_ts, close_ts)`. Same for 3m. Every `ParentBar`'s `ltf_bars` lie inside its parent and are contiguous. |
| 8 | **Historical replay** | The same frozen dataset produces byte-identical output across runs and across machines. |
| 9 | **Timestamp integrity** | Every bar: UTC epoch-ms, `open_ts` on a minute boundary, `close_ts − open_ts` exactly the period, `open_ts` is the OPEN. No local-time conversion anywhere in the path. |
| 10 | **Provider failure fails closed** | Kill the provider connection → the layer reaches `STALE`/`DISCONNECTED` and the bot **refuses to open a position**. Never a silent stall. |
| 11 | **Cross-source equivalence** ⟵ *the parity-critical one* | For a sampled window, bars aggregated from provider 1m must equal TradingView's 5m and 3m bars for `high`, `low`, `close` and `open_ts`. **Any mismatch is a Phase C blocker and must be explained before proceeding.** |
| 12 | **Continuous-contract roll** | The roll dates in the frozen calendar reproduce the research series' rolls over the parity window; each bar's `contract` is recorded; a roll never appears as a price gap without being flagged. |
| 13 | **Fold A truncation reproduction** | For fold A 1m, parent bars before `2026-05-27 02:15` (MGC) / `02:20` (MNQ) carry **empty** `ltf_bars`, and the resulting `fold_bars_with_ltf` equals 9,813 (MGC) / 9,812 (MNQ). |
| 14 | **Held-out guard** | Any dev/replay path receiving a bar at or after `FE = 1788134400000` raises `HeldOutDataError`. Fail closed. |
| 15 | **Warm-up enforcement** | With fewer than 828 closed 5m bars the layer reports `WARMING_UP` and the bot refuses to open a position. |
| 16 | **Secret redaction** | A full session capture contains no configured credential value. |

---

## Phase C Handoff Requirements

Phase C is Gate 1: V53 Python parity against authoritative raw OHLCV. It needs exactly this from
Phase B.

| requirement | specification |
|---|---|
| **dataset format** | one file per (instrument, timeframe), 1m/3m/5m; columns `open_ts_ms, open, high, low, close, volume?, contract`; exact decimal text, never float repr; sorted by `open_ts_ms` |
| **symbol mapping** | `MGC1!` → provider continuous symbol + the frozen roll calendar; same for `MNQ1!`; the mapping is committed, not inferred |
| **timeframe representation** | `M1`, `M3`, `M5` as in `bot/contracts/enums.py`; 3m and 5m produced by **our** aggregator, with `composed_of` retained |
| **timestamps** | UTC epoch-ms, bar **OPEN**; `close_ts` derived and asserted |
| **session handling** | `bot/calendar/cme.py` unchanged; gaps at session boundaries are legitimate and must not be filled |
| **continuous contracts** | frozen roll calendar committed alongside; each bar tagged with the concrete `contract` |
| **warm-up** | ≥ 828 closed 5m bars **before** each fold start, plus a tail after fold C for late-resolving sequences |
| **bar-close semantics** | every bar in the dataset is closed by construction; no forming bar exists in a frozen file |
| **reproducible dataset hash** | sha256 per file plus a manifest recording provider, query parameters, extraction date, roll calendar hash and row counts — the same pattern already proven by A2 |
| **fold A LTF truncation** | reproduced exactly (Acceptance Test 13) |

**Can Phase B provide all of this? Yes — with two caveats that must be closed first.**

1. **The roll calendar cannot be produced without a data pull.** Until the actual roll dates for
   `MGC1!`/`MNQ1!` over 2026-05-24 → 2026-08-30 are known, and it is known whether the research
   series was back-adjusted, the mapping is unspecified. **This is the gating unknown for Phase C.**
2. **If Acceptance Test 11 fails**, the provider series is not the research series, and Phase C
   must either use a TradingView-exported dataset (Option C as an export mechanism only) or accept
   a documented divergence and scope parity to a roll-free window.

---

## Decisions Required

**D-B1 · Data provider.** Options: (a) Databento `GLBX.MDP3`; (b) broker feed; (c) TradingView
export. **Recommend (a) for live, with (c) as the export fallback for the Phase C dataset if
purchasing history is undesirable.** Blocks: everything in the implementation plan.

**D-B2 · Continuous-contract representation.** Options: (a) provider continuous symbology
configured to match TradingView's roll; (b) per-expiry contracts stitched under our own frozen
calendar. **Recommend (a) if Acceptance Test 12 passes, else (b).** *This cannot be decided from
the repository — it needs a data pull.* Blocks: Phase C dataset, and the execution layer's
symbol resolution.

**D-B3 · Back-adjustment.** Options: none (raw, with roll gaps) / difference / ratio.
**Recommend: match whatever the research series used**, which must be determined empirically. Do
not choose on theoretical merit — parity governs.

**D-B4 · Where the Phase C dataset comes from.** Buy history, or export from TradingView.
**Recommend: export from TradingView first** — it is free, it is *by construction* the series Pine
ran on, and it de-risks Gate 1 — then buy provider history for live and for future backtesting,
validating one against the other via Test 11. This inverts the obvious order deliberately: parity
is the priority, and TradingView is the ground truth *for parity specifically*.

**D-B5 · Live/historical provider split.** One vendor for both, or a broker feed live plus a
vendor for history. **Recommend deciding after D-3 (broker) is settled**; keep the adapter
interface provider-agnostic so this stays reversible.

**D-B6 · Aggregation ownership.** In-house (Architecture B) vs provider-native (A).
**Recommend in-house**, per the Multi-Timeframe section. Reversible if Test 11 reveals an
irreconcilable difference.

---

## Implementation Plan

Ordered by dependency. **No task below is started in Phase B; this is the plan, not the work.**

| # | task | depends on | output |
|---|---|---|---|
| **B-1** | Determine the actual roll dates and back-adjustment mode of `MGC1!`/`MNQ1!` over the research window | D-B4 | the frozen roll calendar; closes **D-B2**, **D-B3** |
| **B-2** | Export the Phase C dataset (5m + 1m + 3m, all three folds, plus warm-up and tail), hash it, and commit a manifest | B-1 | the Phase C dataset — **unblocks Phase C** |
| **B-3** | Reproduce the fold A LTF truncation in the dataset and assert it (Test 13) | B-2 | parity-correct fixtures |
| **B-4** | Define `ClosedBar` provenance fields and the `MarketDataSource` protocol | — | the provider-agnostic interface |
| **B-5** | Build the deterministic aggregator (1m → 3m, 1m → 5m) with `composed_of` | B-4 | Tests 7, 8 |
| **B-6** | Run cross-source equivalence against TradingView (Test 11) | B-2, B-5 | go/no-go on the aggregation rule |
| **B-7** | Build the completeness gate and validator | B-4 | Tests 1, 2, 3, 4, 9 |
| **B-8** | Build the offline/replay source over the frozen dataset | B-2, B-7 | deterministic replay; **the only source Phase C needs** |
| **B-9** | Build the provider adapter (live + historical) | D-B1, B-4 | live capability |
| **B-10** | Build the data-layer state machine, backfill and reconnect | B-7, B-9 | Tests 5, 6, 10, 15 |
| **B-11** | Wire the guard and secret redaction; add all 16 tests to CI | all | Tests 14, 16 |

**Critical path to Phase C: B-1 → B-2 → B-3.** Everything else can proceed in parallel and is not
required for Gate 1. Phase C needs only a frozen dataset and an offline reader — **not** a live
feed. That is worth exploiting: **Phase C can start as soon as B-3 completes**, while the live
plumbing (B-9, B-10) is still being built.

---

## Strategy Remains Frozen

Nothing in this specification changes sweep logic, CHOCH, BOS, FVG, stops, targets, displacement,
`swLen`, ATR, `dispWait`, or any frozen V53 input. Where the strategy is unusual — the unused
`open`, the unused `volume`, the fold A LTF truncation, the 100k cap's effect on what Pine saw —
the specification **reproduces** the behaviour rather than correcting it. The two optimistic
execution assumptions (touch⇒fill, entry-bar blindness) are execution-layer concerns and are not
touched here.

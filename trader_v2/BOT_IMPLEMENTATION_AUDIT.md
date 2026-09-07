# Bot Implementation Audit — frozen V53 → paper/production trading

**Audit only. Nothing was implemented, no strategy was run, TradingView was not touched, and no
forward/OOS data was inspected or consumed.**

Audit date: 2026-09-06. Repository HEAD at audit time: `806110a`.
Branch: `claude/tradingview-paper-trading-auto-76ojnw`. 195 commits, 2026-03-16 → 2026-09-06.

---

## 0. Headline finding

**This repository contains no trading system.** It contains a research instrument.

There is a mature 6,265-LOC Node MCP bridge that drives a *GUI copy of TradingView Desktop over a
Chrome debug port*, a large body of Pine research, and ~15k LOC of Python that *parses text tables
copied out of chart runs*. There is **no broker integration, no order management, no position
management, no execution engine, no webhook receiver, no persistence, no scheduler, no risk
engine wired to anything, and no implementation of V53 outside Pine.**

The distance from here to a paper-trading bot is therefore not "add a broker adapter". It is
"build the trading system", with the existing repo supplying the strategy specification, a
verification oracle, and some good design documents.

Second headline finding: **V53's only executable form is Pine running inside a desktop GUI.**
Any production bot must re-implement it, and the central engineering risk of this whole programme
is proving that re-implementation is bar-for-bar identical to the frozen artifact.

---

## 1. Repository inventory

### 1.1 Strategy

| item | location | LOC | status |
|---|---|---|---|
| **frozen canonical V53** | `trader_v2/V53_ltf_sequence.pine` | 665 | FROZEN — sha `7490766b…` — never executed |
| **frozen executed baseline** | `trader_v2/p15/executed/V53_EXECUTED_BUILD.pine` | 602 | FROZEN — sha `2dafbafd…` — produced all Phase 13F/14/15 data |
| **Phase 16 OOS artifact** | `trader_v2/p16/executed/V53_P16_OOS_BUILD.pine` | 602 | FROZEN — sha `5c21acfa…` — data-selection extension only, **not yet run** |
| Phase 15 experimental arms | `trader_v2/p15/exec_arms/*.pine` (5) | ~3k | historical, executed |
| superseded arms | `trader_v2/p15/V53_P15_*.pine` (7) | ~4k | SUPERSEDED / NEVER EXECUTED — retained as evidence |
| V42–V49 research rigs | `trader_v2/V4*.pine` (7) | ~86k chars | historical research |
| V11–V38 line | `strategies/*.pine` (~24) | 6,156 (incl. .py) | superseded strategy generation |

**Strategy constants (frozen, all 15 inputs):** `dirMode`, `foldSel`, `ltfSel`, `tgtR 5.0`,
`bufATR 0.20`, `minWick 0.10`, `dispMin 1.50`, `dispWait 12`, `retBars 24`, `minRatr 0.05`,
`maxRatr 3.00`, `maxBars 144`, `costUSD 3.00`, `swLen 10`, `lSw 3`.

**State machine (V53 §"SEQUENCE SLOTS"):** `SP = 24` concurrent slots,
`st ∈ {0 free, 1 armed, 2 CHOCH, 3 retested, 4 BOS awaiting FVG bar, 5 FVG found awaiting fill,
6 in trade}`, with parallel arrays for `swB, stp, aRf, cLvl, pRef, cPvI, cBar, rBar, dBar, ent,
rr, wt, bIn, mfe, mae, flg` plus ten ledger-only arrays.

**Signal output:** there is none in the machine-readable sense. V53 emits three Pine `table`s
(funnel counters, performance summary, trade ledger capped at 40 rows) that a human or an LLM
reads via `data_get_pine_tables`. **There is no alert, no webhook, no JSON, no file output.**

**Diagnostic output:** assertion counters `K21–K27, K32` (all must read 0), `dropped (no slot)`,
funnel counters, and — in the canonical build only — the `K33/K34/K35` pivot-tie diagnostics that
the executed build omits.

### 1.2 Data

| concern | current state |
|---|---|
| historical source | TradingView Desktop chart buffer, read over CDP |
| formats | Pine `table` text → hand-copied into `trader_v2/**/runs/*.txt`; also `data_get_ohlcv` JSON |
| loaders | `trader_v2/p15/p15_analyze.py` (regex over committed run text), `p14_foldc.py`, `g_cluster.py` |
| replay/backtest infra | **none for V53.** `src/core/replay.js` drives TradingView's *own* replay UI; it is not a strategy backtester |
| timestamps | UTC throughout; fold constants are epoch-ms (`FB/FC/FE`) |
| session handling | inside Pine only (`hUTC < 7` Asia window, `ta.change(time("D"))` day roll) |
| missing data | `request.security_lower_tf` silently returns a shorter array; V53 counts `fold bars w/ LTF` vs `fold bars` and no more |

**Critical data constraint:** `request.security_lower_tf` is capped at **100,000 values per
requested field** — ≈69 days of 1m history from the chart's last bar. Any replay or re-derivation
that needs 1m beyond that window cannot use this architecture.

### 1.3 TradingView layer

| component | location | status |
|---|---|---|
| MCP server (84 tools) | `src/server.js` + `src/tools/*` (15 modules) | **production-quality for its purpose** |
| core logic | `src/core/*` (17 modules) | mature |
| CDP connection | `src/connection.js` — retry/backoff, `safeString`, `requireFinite` | mature |
| CLI | `src/cli/*` (17 files) | mature |
| launchers | `scripts/launch_tv_debug.{bat,vbs,sh}` | Windows/Mac/Linux |
| Pine push/pull | `scripts/pine_{push,pull}.js` | working |
| streaming | `src/core/stream.js` — **500 ms poll-and-diff, not a tick feed** |
| alerts | `src/core/alerts.js` — TradingView pricealerts REST via the desktop session |
| **webhook / signal infra** | **none** |
| auth | none of its own; rides the desktop app's authenticated session |
| deployment state | local dev only; requires a GUI TradingView Desktop with `--remote-debugging-port=9222` |

### 1.4 Bot

**Effectively absent.** `trader/` (992 LOC Python) is a v1 design skeleton for a *different*
strategy:

| file | LOC | what it is | wired to anything? |
|---|---|---|---|
| `prop_rules.py` | 162 | LucidFlex 25K/50K/100K/150K rule engine; end-of-day MLL, consistency | no |
| `risk_engine.py` | 113 | sizing from stop distance × evaluation state | no |
| `management.py` | 93 | trade-management state machine, meta-layer | no |
| `decision_engine.py` | 219 | 10-step decision hierarchy + journal + missed-trade log | no |
| `montecarlo.py` | 139 | pass-probability simulator | no |
| `setup_stats.py` | 72 | setup library stats | no |
| `feasibility.py` | 74 | required-expectancy arithmetic | no |
| `integration_test.py` | 120 | synthetic-flow plumbing test | self-contained |

These target the **V38 fade-vol** strategy documented in `STATE_OF_PLAY.md`, not V53. They are
useful as *design input* — `prop_rules.py` especially — but none of them consume a V53 signal, and
none of them touch a broker.

Absent entirely: execution code, broker/prop adapters, order management, position management,
order-state reconciliation, logging framework, persistence, configuration system, monitoring,
strategy tests.

### 1.5 Infrastructure

| item | status |
|---|---|
| Docker | none |
| env vars | only `TV_CDP_HOST` / `TV_CDP_PORT` (+ `CDP_HOST`/`CDP_PORT`, `HOME`, `LOCALAPPDATA`, `PROGRAMFILES`) |
| secrets | **none committed** (see §14) |
| cloud deployment | none |
| process supervision | none |
| database | none |
| queues | none |
| cron/scheduler | none |
| CI | `.github/workflows/ci.yml` — Node 20/22, eslint, `test:unit`, `npm audit` (non-blocking). **No Python in CI. No Pine validation.** |

### 1.6 Existing unfinished work

Nothing here is to be deleted.

- **Stray empty file `=` at repo root** — a shell redirection accident (0 bytes, 2026-09-05). Harmless, untracked-looking clutter.
- **Exactly one TODO** in the entire codebase: `src/core/pine.js:516`, inside a Pine library template string. Genuinely trivial.
- **`trader/` is dead code relative to V53** — complete-looking, never integrated, and aimed at a superseded strategy.
- **`strategies/`** — a full superseded strategy generation (V11→V38) plus its analysis. `STATE_OF_PLAY.md` documents V38 as "live" on a forward test; that claim predates the V53 line and is **not** the current research position.
- **Duplicated analysis logic** — `p15_analyze.py`, `p15_joint.py`, `p14_foldc.py`, `g_cluster.py`, `foldC_test.py`, `v49_engine_check.py` each re-implement ledger parsing and clustering. Divergence risk if reused for the bot.
- **`trader_v2/alert_history.json`** — hand-annotated human alert records; research evidence, not infrastructure.
- **`e2e.test.js` (79 blocks) requires a live TradingView Desktop** and is excluded from CI. Looks like coverage; is not automated coverage.
- **Looks complete but is NOT production-safe:** the MCP bridge. It is excellent at what it does — driving a GUI for research — and is structurally unsuitable as a trading data path (§2, §5).

---

## 2. End-to-end signal trace

Legend: **IMPL** implemented · **PART** partial · **MISS** missing · **UNSAFE** exists but unsafe for live.

| # | stage | where | status | notes |
|---|---|---|---|---|
| 1 | market data | TradingView Desktop chart buffer via CDP | **UNSAFE** | GUI-dependent, poll-based, no gap detection, no staleness check, no reconnect semantics for data integrity |
| 2 | 5m sweep detection | V53 §"5m SWEEP ENGINE" | **IMPL (Pine only)** | deterministic, causal; PDH/PDL, Asia H/L, `ta.pivot*(10,10)` swings |
| 3 | LTF extraction | `request.security_lower_tf` ×5 fields | **IMPL (Pine only)** | 100k/field cap; no equivalent outside Pine |
| 4 | LTF pivot detection | V53 §4a ring buffer, `lSw=3` | **IMPL (Pine only)** | non-strict-left / strict-right; verified 0 mismatches over 20,567 bars |
| 5 | CHOCH | V53 §4b `s==1` | **IMPL (Pine only)** | break-on-close vs most-recent eligible opposing pivot |
| 6 | CHOCH retest | V53 §4b `s==2` | **IMPL (Pine only)** | exact level, zero tolerance |
| 7 | BOS / displacement | V53 §4b `s==3` | **IMPL (Pine only)** | CHOCH pivot excluded; `rng > 1.50×ATR` + close-location clause |
| 8 | associated FVG | V53 §4b `s==4` | **IMPL (Pine only)** | single test at LTF bar `d+1`; middle candle **is** the displacement candle |
| 9 | FVG retest / fill | V53 §2 | **UNSAFE** | assumes **touch ⇒ fill** on a resting limit. Optimistic; unvalidated |
| 10 | entry signal | implicit — `st` 5→6 | **MISS** | never leaves Pine as a machine-readable event |
| 11 | risk calculation | `r = \|E − stp\|`, R-band 0.05–3.00×ATR | **PART** | R is computed; **position sizing does not exist** |
| 12 | order | — | **MISS** | |
| 13 | fill | — | **MISS** | |
| 14 | stop / target | +5R / −1R modelled in Pine | **UNSAFE** | never placed with a broker; adverse-first is an assumption, not an exchange guarantee |
| 15 | exit | V53 §1 outcome loop | **UNSAFE** | see the entry-bar gap in §5.4 |
| 16 | trade ledger | Pine `table`, 40-row cap | **PART** | human/LLM-read, not persisted programmatically; **silently truncates above 40 fills** |

### 2.1 The questions asked of every stage

For stages 2–9 (the strategy core, Pine):

- **Deterministic?** Yes. Pure functions of the bar series, no randomness, no wall-clock.
- **Causal?** Yes, and it was *audited* to be — Phase 13E verified assertion `A21` (CHOCH on
  ineligible pivot), `A23` (retest not before BOS), `A24` (BOS bar ≠ displacement bar) all read 0
  across every run.
- **Data required?** 5m OHLC + `ta.atr(14)`; 1m or 3m OHLC + timestamps for the same 5m window.
- **Timestamp used?** The **5m bar close**. LTF sub-bars carry their own `time` for the ledger
  only; every decision materialises at the parent 5m close.
- **State that must persist?** The 24 slot arrays, the 4-pivot register, the 7-bar LTF ring
  buffer, `ltfN`, and daily/Asia levels. **Non-trivial: roughly 30 parallel arrays.**
- **After restart?** Pine recomputes from bar 1 every reload. **A bot cannot** — this state must
  be persisted and rehydrated, and that is a first-class engineering task, not an afterthought.
- **Missing data?** Pine silently shortens the LTF array. A bot must detect and refuse to trade.
- **Order rejected / network down / duplicate signal?** Not modelled anywhere. All MISS.

For stages 10–16: every question is MISS or UNSAFE because the components do not exist.

---

## 3. Strategy / execution boundary

This is the most important design decision in the programme, and the repo currently has no
boundary at all because it has no execution side.

### 3.1 The boundary

**Strategy engine — a faithful re-implementation of frozen V53. Nothing else.**
Owns: sweep detection, LTF ingest, pivot detection, CHOCH, CHOCH retest, BOS + displacement, FVG
association, the FVG fill *predicate*, R computation, target/stop *levels*, timeout counting, the
24-slot state machine, and event identity.
Emits: immutable `Signal` events. Consumes: bars. Knows nothing about accounts, brokers,
positions, money, or whether a signal will be traded.

**Execution engine — everything about turning a signal into a position.**
Owns: order construction, submission, acknowledgement, fills, partials, cancels, replaces,
broker reconciliation, position truth, idempotency, retries, disconnects.
**Must never re-derive or reinterpret a level.** If the execution engine ever computes a price
from bars, the boundary has been violated.

**Risk engine — a veto between them.** Strategy says *"valid signal"*; risk says *"allowed?"*;
execution says *"here is how"*. Sizing lives in risk, not strategy: V53 defines R as a price
distance, never a contract count.

### 3.2 Canonical immutable Signal schema (recommended)

Every field below already exists in the V53 ledger row, so this is a transcription of the frozen
research record, not a new invention.

```
Signal {
  # identity
  signal_id            uuid            # execution-layer, generated once
  event_key_primary    string          # Phase 13G primary identity, see below
  event_key_alt        string          # Phase 13G alternative identity
  slot_index           int             # V53 slot 0..23, for state provenance

  # provenance — MANDATORY
  strategy_id          "V53"
  strategy_sha256      string          # hash of the strategy artifact that produced this
  schema_version       int

  # scope
  instrument           string          # "MGC1!" | "MNQ1!"
  direction            "long"|"short"
  ltf                  "1m"|"3m"

  # the frozen sequence, one field per stage
  sweep_ts             utc_ms          # 5m bar close that armed the slot
  sweep_kind           set{"PD","AS","SW"}
  sweep_extreme        decimal         # swX — low (long) / high (short)
  choch_ts             utc_ms          # LTF bar time
  choch_level          decimal
  choch_pivot_index    int             # cPvI, needed for BOS eligibility
  retest_ts            utc_ms
  bos_ts               utc_ms
  bos_level            decimal
  displacement_ltf_idx int             # dBar
  fvg_low              decimal
  fvg_high             decimal

  # execution instructions — computed by strategy, NOT re-derived downstream
  entry_price          decimal         # FVG far edge
  stop_price           decimal         # sweep extreme ∓ 0.20 × ATR(5m at arm)
  target_price         decimal         # entry ± 5R
  r_distance           decimal         # |entry − stop|
  atr_at_arm           decimal
  r_atr_ratio          decimal         # must be in [0.05, 3.00]

  # lifecycle
  emitted_at           utc_ms          # 5m bar close at which FVG was found
  expires_after_bars   24              # retBars
  timeout_bars         144             # maxBars
}
```

Use `Decimal`, never float, for every price. Tick-round only at the broker adapter.

**Event keys, carried forward verbatim from Phase 13G:**
- primary: `(instrument, direction, ltf, choch_ts, choch_level, bos_ts, bos_level, entry_ts, entry_price)`
- alternative: `(instrument, direction, ltf, bos_ts, bos_level, entry_ts, entry_price)`

These are **analysis** identities. They are *not* the execution idempotency key (§8).

### 3.3 Boundary violations to guard against

1. Execution "improving" the entry (mid-FVG, offset ticks) — that is a strategy change.
2. Risk widening a stop to fit a size — sizing must adapt to the stop, never the reverse.
3. Execution deduplicating convergent signals — Phase 13G established that the frozen spec
   *permits* convergence with **no deduplication rule**. Suppressing at strategy level is a rule
   change; see §8.
4. Re-deriving ATR downstream — `atr_at_arm` is carried in the signal.

---

## 4. Live-time / bar-close semantics

### 4.1 The favourable finding

**Every V53 decision resolves at a 5m bar close.** `request.security_lower_tf` hands the whole
LTF array for the current 5m bar at that bar's close, so the LTF loop is an *intrabar
reconstruction* performed at the parent close — not a stream of independent LTF decisions.

Consequences: the bot is a **5m bar-close event loop**. It needs no tick handling for signal
generation, and the 1m/3m feeds only need to be complete-and-correct for the just-closed 5m bar.

### 4.2 Earliest real-world knowledge time, per decision

| decision | earliest knowable | driver |
|---|---|---|
| ATR(14) 5m | 14 × 5m = 70 min after data start | warmup |
| PDH / PDL | first 5m close of the new UTC day | `ta.change(time("D"))` |
| Asia H/L | rolling, final at the first close with `hUTC ≥ 7` | session window |
| **5m swing level** | **close of bar +10 after the pivot bar = +50 min** | `ta.pivot*(high,10,10)` |
| sweep armed | close of the sweeping 5m bar | |
| LTF pivot | close of the 5m bar containing LTF bar +3 | `lSw=3`, resolved intrabar |
| CHOCH / retest / BOS / FVG | close of the 5m bar containing the LTF bar | all within §4 loop |
| FVG fill | close of a **later** 5m bar (§2 runs before §4) | earliest = emit bar + 1 |
| outcome | close of the bar **after** the fill bar | `bIn` starts at 0 |

**A swing-sourced sweep cannot be known until 50 minutes after the swing formed.** That is correct
and causal, but it means the bot must retain ≥ 21 bars of 5m history to reproduce `swH`/`swL`.

### 4.3 Where the backtest knows more than a live system could

**None in the signal path.** Phase 13E's assertion battery was built precisely to catch lookahead,
and `A21`, `A23`, `A24`, `A32` read 0 across all 96 Phase 15 runs. Section 5 arms sweeps *after*
the LTF loop specifically so a bar's own LTF sub-bars cannot serve the sequence armed on that bar.

### 4.4 Two optimistic assumptions in the *execution* model — flag both

**(a) Touch ⇒ fill.** §2 fills when `low <= E` (long). A resting limit that is merely touched may
not fill; you need to be through the level or first in queue. `trader/EXTERNAL_COMPONENTS.md`
already calls this "the single most optimistic assumption in the whole system". It flatters every
result in Phases 13F/14/15. **Live fill-rate must be measured in paper trading before any R figure
is trusted.**

**(b) The entry bar is never evaluated for stop or target.** §2 sets `bIn = 0` on fill; §1 runs
first on subsequent bars with `b = bIn + 1`. The 5m bar on which the fill occurs is therefore
never checked for an adverse excursion. In live trading price can touch the FVG edge and reach the
stop inside the same 5m bar.

Assertion `K25` (`b < 1`) cannot detect this — it is 0 **by construction**, not by validation. A
live bot will experience same-bar stop-outs the research model never counted, and this biases
research results **optimistically**. This must be measured, not assumed away, and it is a reason
to expect live results to underperform the ledger even if the edge is real.

---

## 5. Biggest technical risks

| # | risk | severity | why |
|---|---|---|---|
| R1 | **Re-implementation drift** — a Python/Node V53 that is subtly not V53 | **critical** | 30 parallel arrays, a 7-bar ring buffer, non-strict-left/strict-right pivots, §-ordering that is load-bearing. Phase 13E already caught one pivot-rule defect (180/20,567 mismatches). Without golden tests this silently invalidates everything |
| R2 | **GUI-dependent data path** | **critical** | TradingView Desktop + CDP is not a production feed. No SLA, no gap detection, breaks on app update, needs a logged-in desktop session |
| R3 | **Touch ⇒ fill** | **high** | unvalidated, flatters all research, directly inflates R |
| R4 | **Entry-bar stop blindness** | **high** | structural optimism the assertions cannot catch |
| R5 | **No persistence** | **high** | ~30 arrays of live state; a restart mid-sequence currently loses everything |
| R6 | **No reconciliation** | **high** | no concept of broker truth; the classic way bots produce unmanaged positions |
| R7 | **Convergent sequences** | **medium** | Phase 13G: 69% of baseline fills sit in multi-fill clusters, largest 3. Naive execution fires 3 orders into one market event |
| R8 | **40-row ledger cap** | **medium** | silent truncation; the research pipeline reads tables |
| R9 | **Analysis-code duplication** | **medium** | 6 divergent ledger parsers; reuse invites inconsistency |
| R10 | **Phase 16 contamination** | **medium** | any bot test that pulls "recent data" touches the held-out window |
| R11 | **No edge established** | **informational** | Phase 15: *no arm demonstrates an edge*; baseline negative under all three accountings. Bot readiness ≠ strategy validity |

---

## 6. Proposed architecture

```
        ┌────────────────────────── research/ (immutable) ──────────────────────────┐
        │  trader_v2/**  ·  strategies/**  ·  trader/**  ·  p15/  ·  p16/           │
        │  frozen artifacts · ledgers · phase reports · Phase 16 held-out window    │
        └───────────────────────────────┬───────────────────────────────────────────┘
                                        │ read-only, one direction, at build time only
                                        ▼
   bars ──▶ DATA ENGINE ──▶ STRATEGY ENGINE ──▶ RISK ENGINE ──▶ EXECUTION IFACE ──▶ ┬─ PaperBroker
            gap/staleness    faithful V53         veto only        idempotent        └─ LiveBroker
            5m + 1m/3m       Signal events        sizing           orders
                 │                 │                  │                 │
                 └────────── PERSISTENCE  ·  OBSERVABILITY  ·  RECONCILER ──────────┘
```

Non-negotiables: one code path from data to execution, with only the final adapter differing;
strategy state persisted and rehydrated; risk as an independent veto; every live decision
reconstructable from logs.

### Recommended stack

**Python 3.11+.** The research analysis, the golden fixtures and `prop_rules.py` are already
Python; the Node side is an MCP bridge with no execution role. Do not split the bot across two
languages.

**Persistence: SQLite (WAL), single file.** Rationale: the write rate is a handful of rows per 5m
bar; the state is relational (signals → orders → fills → positions); crash-safe durability is
mandatory; and a server database adds an operational failure mode for zero benefit at this scale.
Explicitly **not** Postgres, not Redis, not Kafka.

---

## 7. Phase 16 contamination safeguards

Phase 16 accumulates forward-held-out data from 2026-08-31 00:00 UTC to 2027-04-02 00:00 UTC. The
protocol forbids inspecting OOS outcomes before the boundary. Bot development runs in parallel and
**must not touch that window**.

Mandatory controls:

1. **Hard date guard in every fixture loader.** Any bar with `time >= FE (1788134400000)` raises
   in test/dev code paths. Fail closed.
2. **Golden fixtures are frozen files**, extracted only from already-consumed Phase 13F/14/15
   ledgers (`v53_runs/`, `v53_runs_foldc/`, `p15/runs/`) — never from a live chart pull.
3. **No live chart reads for development.** Development uses committed fixtures or synthetic bars.
4. **`p16/` is read-only to the bot.** No bot module imports from `trader_v2/p16/`. Add a CI check.
5. **Paper trading before 2027-04-02 must run on a non-V53 dummy strategy** or on
   pre-`FE` replay — never live V53 on the accumulating window. A paper bot silently running V53
   forward *is* consuming the held-out data.
6. Bot results are never cited as Phase 16 evidence, and Phase 16 results never justify
   architecture changes.

---

## 8. Idempotency (not deduplication)

Phase 13G established: *the frozen specification permits multiple independently armed sweep
sequences to converge on the same downstream market event, and no deduplication rule exists.*
Baseline: 58 fills → 43 primary / 37 alternative events; 69.0% of fills in multi-fill clusters;
largest cluster 3.

**Do not add strategy-level dedup.** That is a rule change and it would invalidate comparability
with all prior phases.

Instead, protect at the execution layer with a deterministic idempotency key:

```
client_order_id = sha256(
    strategy_sha256 ‖ instrument ‖ direction ‖ ltf ‖
    slot_index ‖ sweep_ts ‖ choch_ts ‖ bos_ts ‖ entry_price ‖ intent_seq
)[:32]
```

Properties: derived only from immutable signal fields, so a replayed webhook, a duplicated MCP
message, a re-processed bar or a restart mid-submission all regenerate the *same* id; the broker
rejects the duplicate, or the local store already holds it. `intent_seq` distinguishes
entry/stop/target/amend for the same signal.

Convergent sequences remain **separate signals with separate ids** — the strategy's behaviour is
unchanged. Whether the *risk engine* caps concurrent exposure on one market event is a **risk
policy decision**, made explicitly, logged, and reported separately from strategy results.

---

## 9. Configuration and secrets

**Scan result: no secrets are committed.** The only credential-shaped grep hits are
`SECURITY.md:17` (prose) and three `scripts/launch_tv_debug.bat` lines using the `tokens=*`
`for /f` option. No `.env`, `.pem`, keystore or credential file exists anywhere in the tree.

Environment surface today is minimal: `TV_CDP_HOST`, `TV_CDP_PORT` (aliases `CDP_HOST`,
`CDP_PORT`), plus OS paths.

For the bot, the following will be introduced and **must never be committed**: broker API key,
secret and account id; prop-firm account identifiers; webhook shared secret; any tunnel URL;
database path if outside the repo.

Recommendations: `.env` loaded via `python-dotenv`, `.env.example` committed with placeholder keys
only; add `.env`, `*.key`, `*.pem`, `secrets/`, `bot/data/` to `.gitignore`; a startup assertion
that required vars are present and that no value appears in any log line; rotation on any
suspected exposure and after every operator change; OS keychain or a secret manager only if the
bot ever leaves a single trusted host.

---

## 10. Live safety gates

Adopted as written, with acceptance evidence required at each:

| gate | requirement | evidence |
|---|---|---|
| **0** | code tests pass | unit + property suites green in CI |
| **1** | historical replay reproduces V53 | bar-for-bar equality with committed ledgers on **all 8 cells**, zero mismatches |
| **2** | paper trading works | end-to-end signal → paper fill → ledger, on pre-`FE` replay |
| **3** | survives reconnect/restart | kill −9 at each of 6 lifecycle points; state rehydrates; no duplicate orders |
| **4** | broker reconciliation passes | injected divergence detected and halts within one cycle |
| **5** | risk limits tested | every limit provably blocks; kill switch latches |
| **6** | extended soak | ≥ 30 sessions unattended, zero unexplained discrepancies |
| **7** | live capital | **requires Phase 16 to have returned a supportive verdict — a working bot is not a reason to trade** |

`trader/EXTERNAL_COMPONENTS.md` §48 already specifies the live-safety layer in detail. It is a
good specification and should be implemented rather than rewritten.

---

## 11. Research edge vs software readiness

These are orthogonal and must stay that way.

- Phase 15: **no arm demonstrates an edge**; the frozen baseline is negative under execution,
  primary-event and alternative-event accountings.
- Phase 16 is the only thing that can produce a verdict, and it is powered only against a *large*
  edge (p₁ = 0.30, 0.80 power at N = 80); failure to reject means "no large edge", not "no edge".
- The bot can and should be built regardless. A correct, observable, safe bot is worth having even
  if V53 is ultimately retired — the same harness will test the next hypothesis.
- **Bot testing results are never evidence about V53's edge. Phase 16 results never justify
  architecture changes.**

---

## 12. Confirmations

- `trader_v2/V53_ltf_sequence.pine` — **not modified**, sha `7490766b…` unchanged.
- `trader_v2/p15/executed/V53_EXECUTED_BUILD.pine` — **not modified**, sha `2dafbafd…` unchanged.
- `trader_v2/p16/**` — **not modified**; sha `5c21acfa…` unchanged; protocol untouched.
- **No strategy was run.** No Pine was injected, compiled or executed. TradingView was not
  contacted during this audit.
- **No forward/OOS data was inspected or consumed.** No chart data was read at all; every figure
  in this document comes from committed research records and from static file inspection.

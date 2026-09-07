# Bot Implementation Roadmap — frozen V53 → paper → production

**Companion to `trader_v2/BOT_IMPLEMENTATION_AUDIT.md`. Roadmap only — nothing in this document has
been implemented. No strategy was run, TradingView was not contacted, Phase 16 was not touched.**

Roadmap date: 2026-09-06. Branch `claude/tradingview-paper-trading-auto-76ojnw`.

---

## 0. How to read this document

Every task carries the same nine fields:

| field | meaning |
|---|---|
| **Objective** | the single outcome that makes the task done |
| **Affects** | files / components created or modified |
| **Depends on** | task ids that must be complete first |
| **Acceptance** | exact, checkable criteria — not "works correctly" |
| **Tests** | the test artifacts the task must ship with |
| **Phase-16-safe** | YES = can be built and verified without touching the held-out window or the p16 artifacts |
| **Touches frozen V53** | YES = modifies a frozen `.pine` artifact. **Every task in this roadmap is NO. Any future task that would be YES is prohibited without an explicit new authorization and a new phase record.** |
| **Risk** | low / medium / high / critical — chance the task silently produces a wrong system |
| **Complexity** | S ≤ 1 day · M 2–4 days · L 1–2 weeks · XL > 2 weeks (single engineer) |

Priority classes:

- **P0** — required before paper trading can begin at all.
- **P1** — required before live capital.
- **P2** — important, can follow live-readiness work.
- **P3** — optional / future.

---

## 1. Ordering: proposed vs. adopted

The ordering suggested in the request is sound in outline. The audit forces **three changes**:

1. **Historical replay / golden parity moves from #12 to #4** — immediately after the strategy
   adapter, before *any* runtime, broker or infrastructure work. R1 (re-implementation drift) is
   the critical risk of the entire programme. Every component downstream of an unverified strategy
   engine is built on sand, and the cost of discovering drift late is a rewrite of the state model.
   Nothing else in the roadmap may start consuming strategy output until Gate 1 passes.
2. **Golden-fixture extraction moves to the front (A2)** — the parity harness needs frozen
   fixtures, and extracting them is also the only Phase-16-safe way to obtain data. This is a
   prerequisite, not a testing detail.
3. **The paper broker and risk engine move earlier and run in parallel** — they depend only on the
   `Signal` schema and the execution interface, not on the strategy engine's internals. Building
   them concurrently with B2/B3 is the largest available schedule win.

Everything else keeps the requested sequence.

---

## 2. Phase map

```
A. FOUNDATIONS ────────────────────────────────────────────────────────── P0
   A1 boundaries/guardrails   A2 golden fixtures   A3 Signal schema
                       │              │                  │
B. STRATEGY CORRECTNESS ◀── critical path ─────────────────────────────── P0
   B1 bar model + offline loader
   B2 V53 strategy adapter (faithful re-implementation)
   B3 golden-parity replay harness ......................... ★ GATE 1
   B4 assertion battery + property tests
                       │
C. RUNTIME ────────────────────────────────────────────────────────────── P0
   C1 persistence   C2 event/state engine   C3 observability
   C4 execution interface + idempotency   C5 paper broker   C6 risk engine
                       │
D. REAL-TIME DATA ─────────────────────────────────────────────────────── P0/P1
   D1 data-engine contract + gap/staleness   D2 CDP adapter   D3 production feed
                       │
E. ROBUSTNESS ─────────────────────────────────────────────────────────── P1
   E1 reconciliation   E2 failure testing   E3 fill-model calibration
   E4 deployment/supervision
                       │
F. OPERATING ──────────────────────────────────────────────────────────── P1
   F1 paper-trading soak ..................... ★ GATES 2,3,4,5,6
   F2 live deployment gate ................... ★ GATE 7 (blocked on Phase 16)

G. HYGIENE / FUTURE ───────────────────────────────────────────────────── P2/P3
```

---

## 3. Phase A — Foundations

### A1 · Repository boundaries and research guardrails — **P0**

- **Objective.** Create `bot/` as the only writable code tree for the trading system, and make it
  structurally impossible for bot code to read the Phase 16 held-out window or the `p16/` artifacts.
- **Affects.** new `bot/` package skeleton; `bot/guards.py`; `.gitignore`; `.github/workflows/ci.yml`;
  `pyproject.toml`; `README` section. Deletes nothing. `trader_v2/`, `trader/`, `strategies/`,
  `src/` become read-only-by-convention *research* trees.
- **Depends on.** none. **This is the first task.**
- **Acceptance.**
  1. `bot/` exists, imports nothing from `trader_v2/p16/**` — enforced by a CI grep that fails the
     build on any `p16` import or path literal in `bot/**`.
  2. `bot/guards.py` exports `FE_MS = 1788134400000` and `assert_pre_fe(ts_ms)` which **raises**
     `HeldOutDataError` for `ts_ms >= FE_MS`. Every fixture loader and every dev/test data path
     calls it. Fail closed: unknown or missing timestamp also raises.
  3. A deliberate test bar at `FE_MS` and at `FE_MS + 1` raises; `FE_MS - 1` passes.
  4. `.gitignore` covers `.env`, `*.key`, `*.pem`, `secrets/`, `bot/data/`, `*.sqlite*`.
  5. CI runs Python (lint + unit) in addition to the existing Node job.
- **Tests.** `bot/tests/test_guards.py` — boundary cases above; CI job `python-unit`; CI check
  `no-p16-imports`.
- **Phase-16-safe.** YES — it is the safeguard itself.
- **Touches frozen V53.** NO.
- **Risk.** low. **Complexity.** S.

### A2 · Golden fixture extraction — **P0**

- **Objective.** Convert already-consumed Phase 13F/14 run records into frozen, machine-readable
  golden fixtures: for each of the 8 cells (MGC/MNQ × long/short × 1m/3m) and folds A, B, C, the
  full funnel counters, assertion counters and trade ledger exactly as V53 reported them.
- **Affects.** new `bot/fixtures/golden/*.json`; `bot/tools/extract_golden.py`. Reads
  `trader_v2/v53_runs/*.txt` (folds A, B), `trader_v2/v53_runs_foldc/*.txt` (fold C). Does **not**
  modify them.
- **Depends on.** A1.
- **Acceptance.**
  1. 24 fixture files (8 cells × 3 folds), each carrying: source file path, source file sha256,
     `strategy_sha256 = 2dafbafd…` (the executed build), funnel counters, `K21–K27/K32`, and every
     ledger row with all fields.
  2. Re-running the extractor is byte-identical (deterministic, sorted keys, fixed float format).
  3. Every extracted bar/ledger timestamp is `< FE_MS`; the extractor calls `assert_pre_fe`.
  4. Totals reconcile against `trader_v2/PHASE15_SENSITIVITY_REPORT.md` and the committed
     Phase 13G cluster counts (58 baseline fills → 43 primary / 37 alternative events).
  5. **Known limitation recorded in the fixture header:** the Pine ledger table caps at 40 rows
     (R8), so any cell exceeding 40 fills is truncated at source. The extractor must detect a
     truncated cell (row count == 40 and funnel fills > 40) and mark it `truncated: true`;
     truncated cells are excluded from strict-equality parity and used for counter parity only.
- **Tests.** `test_extract_golden.py` — determinism (extract twice, compare bytes), reconciliation
  against the committed report figures, truncation detection on a synthetic 40-row input.
- **Phase-16-safe.** YES — sources are already-consumed folds A/B/C, all pre-`FE`.
- **Touches frozen V53.** NO.
- **Risk.** medium — a wrong fixture makes Gate 1 meaningless in either direction.
- **Complexity.** M.

### A3 · Canonical `Signal` schema and event keys — **P0**

- **Objective.** Implement the immutable signal record from audit §3.2 as the single contract
  between strategy, risk and execution.
- **Affects.** new `bot/contracts/signal.py`, `bot/contracts/keys.py`, `bot/contracts/enums.py`.
- **Depends on.** A1.
- **Acceptance.**
  1. `Signal` is frozen/immutable; every price field is `Decimal`; no float anywhere in the type.
  2. All fields of audit §3.2 present, including `strategy_id`, `strategy_sha256`,
     `schema_version`, `slot_index`, and the full frozen-sequence provenance
     (`sweep_*`, `choch_*`, `retest_ts`, `bos_*`, `displacement_ltf_idx`, `fvg_low/high`).
  3. `event_key_primary` and `event_key_alt` computed exactly as Phase 13G defines them, and
     **documented in code as analysis identities that must never be used for order idempotency.**
  4. Round-trip `Signal → JSON → Signal` is exact for all `Decimal` values (string encoding).
  5. Constructing a `Signal` whose `r_atr_ratio` falls outside `[0.05, 3.00]`, or whose
     `target_price` is not `entry ± 5 × r_distance`, raises — the schema is self-validating.
  6. `schema_version` is stamped and any change to the field set bumps it.
- **Tests.** `test_signal_schema.py` — immutability, Decimal round-trip, validator rejections,
  event-key vectors derived from three committed Phase 13G ledger rows (hand-checked).
- **Phase-16-safe.** YES. **Touches frozen V53.** NO.
- **Risk.** medium — schema churn later is expensive. **Complexity.** M.

---

## 4. Phase B — Strategy correctness (critical path)

> **Nothing in Phase C, D, E or F may consume strategy output until B3 passes.**

### B1 · Bar model and deterministic offline bar loader — **P0**

- **Objective.** A single `Bar` type and an offline loader producing the exact 5m + LTF series V53
  consumed, so the strategy adapter can be driven without TradingView.
- **Affects.** new `bot/data/bar.py`, `bot/data/offline_loader.py`, `bot/fixtures/bars/`.
- **Depends on.** A1, A2.
- **Acceptance.**
  1. `Bar` carries `ts_open_ms`, `ts_close_ms`, OHLC as `Decimal`, volume, `tf`, `instrument`, and
     a `complete` flag. Incomplete bars are never handed to the strategy.
  2. The loader emits 5m bars each carrying the ordered list of contained LTF sub-bars — the exact
     shape `request.security_lower_tf` produces — with an explicit `ltf_count` so a short array is
     visible rather than silent.
  3. `assert_pre_fe` is called on every bar; any `>= FE_MS` bar raises.
  4. A bar series with a missing 5m bar, an out-of-order timestamp, or a duplicate timestamp is
     **rejected**, not repaired.
  5. Cells whose LTF coverage is short reproduce V53's `fold bars w/ LTF` vs `fold bars` counters
     within the loader itself.
- **Tests.** `test_bar_model.py`, `test_offline_loader.py` — gap/duplicate/out-of-order rejection,
  LTF nesting, pre-`FE` guard, counter reproduction.
- **Phase-16-safe.** YES. **Touches frozen V53.** NO.
- **Risk.** medium. **Complexity.** M.

### B2 · V53 strategy adapter — faithful re-implementation — **P0 · critical path**

- **Objective.** A pure Python implementation of frozen V53 that, given the same bars, produces the
  same sweeps, sequences, fills and outcomes as `V53_EXECUTED_BUILD.pine` (sha `2dafbafd…`).
- **Affects.** new `bot/strategy/v53/` — `constants.py`, `levels.py` (PDH/PDL, Asia, `pivot(10,10)`),
  `ltf.py` (ring buffer, `lSw=3` pivots), `sequence.py` (24-slot state machine `st 0..6`),
  `outcome.py` (§1 loop), `fills.py` (§2), `engine.py`. Emits `Signal`.
- **Depends on.** A3, B1.
- **Acceptance.**
  1. All 15 inputs are constants sourced from one module, values exactly as frozen; a test asserts
     each numeric value against the value parsed out of the frozen `.pine` text.
  2. `strategy_sha256` embedded in every emitted `Signal` is the sha of the frozen artifact the
     implementation claims to reproduce, and a startup check re-hashes that file.
  3. **Section ordering is preserved and asserted**: §1 outcomes → §2 fills → §4 sequence → §5 arm.
     A test that reorders them must fail. This ordering is load-bearing (it is what makes
     `emit_bar + 1` the earliest fill and prevents a bar's own LTF sub-bars serving a sequence
     armed on that bar).
  4. Pivot detection is **non-strict on the left (≥), strict on the right (>)** at both `swLen=10`
     and `lSw=3`, with a dedicated test over the Phase 13E tie cases (the rule that produced
     0 mismatches over 20,567 bars; the two rejected variants must fail the same test).
  5. `bIn = 0` at fill and `b = bIn + 1` in §1 are reproduced **exactly as in the frozen build**,
     with an explicit code comment naming this as audit finding §4.4(b) — an optimistic model,
     reproduced deliberately, not repaired. **Do not "fix" it here**; measuring it is E3.
  6. Touch⇒fill (`low <= E` long / `high >= E` short) is reproduced exactly, likewise commented as
     §4.4(a) and likewise not repaired here.
  7. No dedup: convergent sequences emit separate `Signal`s (audit §8).
  8. Pure and side-effect free — no I/O, no clock, no randomness. A test asserts the engine
     produces identical output when run twice on the same bars in the same process.
- **Tests.** unit tests per module; a mutation check (flip the pivot strictness, reorder the
  sections, change one constant → parity in B3 must fail).
- **Phase-16-safe.** YES — developed entirely against pre-`FE` fixtures.
- **Touches frozen V53.** NO — it *reads* the frozen file to hash and to extract constants.
- **Risk.** **critical** (R1). **Complexity.** XL.

### B3 · Golden-parity replay harness — **P0 · ★ GATE 1**

- **Objective.** Prove B2 is bar-for-bar V53 across all 24 golden cells, or fail loudly.
- **Affects.** new `bot/replay/harness.py`, `bot/replay/compare.py`, `bot/reports/gate1.md`
  (generated), CI job `gate1`.
- **Depends on.** A2, B1, B2.
- **Acceptance.**
  1. For all 8 cells × folds A, B, C: **zero** mismatches in funnel counters
     (sweeps, CHOCH, retests, BOS, FVG, fills, R-band rejects, expiries, `dropped (no slot)`).
  2. For every non-truncated cell: the trade ledger matches row-for-row — entry ts, entry price,
     stop, target, outcome, bars-in-trade, MFE/MAE — with exact `Decimal` equality on prices.
  3. Assertion counters `K21–K27`, `K32` all read 0 in the Python engine, as in the frozen runs.
  4. The conservation identity `FVG = fills + R-band rejects + FVG retest expiry` holds in the
     Python engine for every cell.
  5. Any mismatch produces a **diff report naming the first divergent bar and slot**, and the CI
     job fails. There is no tolerance parameter and no "close enough" mode.
  6. Truncated cells (A2 §5) are compared on counters only, and the report states which cells were
     downgraded and why.
- **Tests.** the harness *is* the test; plus `test_compare.py` proving the comparator detects an
  injected one-tick price change, an injected extra ledger row, and a missing row.
- **Phase-16-safe.** YES.
- **Touches frozen V53.** NO.
- **Risk.** **critical** — this gate is the only thing standing between the programme and a
  plausible-looking wrong strategy.
- **Complexity.** L.

### B4 · Assertion battery and property tests — **P0**

- **Objective.** Port the Phase 13E causality assertions into the Python engine as runtime
  invariants, and add the properties the frozen assertions cannot express.
- **Affects.** `bot/strategy/v53/asserts.py`; `bot/tests/test_properties.py`.
- **Depends on.** B2.
- **Acceptance.**
  1. `A21` (CHOCH on ineligible pivot), `A23` (retest before BOS), `A24` (BOS bar == displacement
     bar), `A32` implemented as live assertions that **halt the engine**, not counters.
  2. Property tests over generated bar series: no signal references a bar later than its emit bar;
     `stop` is always on the correct side of `entry`; `target = entry ± 5R` to the tick;
     `r_atr_ratio ∈ [0.05, 3.00]` for every emitted signal; a swing-sourced sweep is never armed
     earlier than 10 bars after the pivot bar (audit §4.2, the 50-minute rule).
  3. **A test that documents, rather than fixes, the entry-bar gap**: a synthetic bar where price
     touches the FVG edge and the stop within the same 5m bar produces *no* stop-out in the engine,
     and the test asserts that outcome with a comment naming §4.4(b). If someone later "fixes" the
     engine, this test fails and forces a phase decision.
- **Tests.** as above; property tests use a seeded generator with the seed recorded on failure.
- **Phase-16-safe.** YES. **Touches frozen V53.** NO.
- **Risk.** medium. **Complexity.** M.

---

## 5. Phase C — Runtime

> C1–C6 are largely parallel. C4, C5 and C6 depend only on A3, not on B2 — start them alongside B2.

### C1 · Persistence — **P0**

- **Objective.** Durable, crash-safe storage of strategy state, signals, orders, fills, positions
  and the decision journal.
- **Affects.** new `bot/store/` — `schema.sql`, `db.py`, `repositories.py`, `migrations/`.
- **Depends on.** A3.
- **Acceptance.**
  1. **SQLite in WAL mode, one file** (audit §6). Not Postgres, not Redis, not a queue.
  2. Tables: `strategy_state` (serialised slot arrays + pivot register + ring buffer + `ltfN` +
     daily/Asia levels, keyed by instrument/direction/ltf and last processed bar), `signals`,
     `orders`, `fills`, `positions`, `journal`, `runs`, `schema_version`.
  3. Prices stored as strings or scaled integers — **never** SQLite `REAL`. A test writes and reads
     `Decimal("2401.15")` and asserts exact equality.
  4. Every write is in a transaction; `synchronous=FULL`; a `kill -9` during a write leaves the DB
     openable with the last committed state intact.
  5. Forward-only numbered migrations; startup refuses to run against a newer schema than the code.
  6. `client_order_id` has a UNIQUE constraint — the database is the last line of idempotency defence.
- **Tests.** `test_store.py` — Decimal fidelity, UNIQUE violation on duplicate `client_order_id`,
  migration up from empty, crash simulation (subprocess killed mid-transaction).
- **Phase-16-safe.** YES. **Touches frozen V53.** NO.
- **Risk.** medium. **Complexity.** M.

### C2 · Event / state engine — **P0**

- **Objective.** The 5m bar-close event loop that drives the strategy, persists its state, and
  rehydrates identically after restart.
- **Affects.** new `bot/runtime/loop.py`, `bot/runtime/state.py`, `bot/runtime/lifecycle.py`.
- **Depends on.** B3 (gate), C1.
- **Acceptance.**
  1. One event type drives everything: **5m bar close** (audit §4.1). No tick handling in the
     signal path.
  2. `serialise(state) → store → rehydrate` is **exactly** round-trip: a test replays fold A to
     bar N, snapshots, restarts from the snapshot, replays to the end, and gets a ledger identical
     to the uninterrupted run. This must hold at ≥ 20 randomly chosen N per cell, **including N
     inside every slot state 1–6**.
  3. Warmup is explicit and refuses to emit before ATR(14) and the 21-bar swing history are
     satisfied (audit §4.2).
  4. A bar arriving out of order or duplicating a processed bar is rejected and journalled; the
     engine does not advance.
  5. The loop is a pure function of (persisted state, next bar) — no wall-clock reads inside the
     strategy path.
- **Tests.** `test_rehydration.py` (the snapshot/restart matrix above), `test_loop_ordering.py`.
- **Phase-16-safe.** YES — driven by fixtures.
- **Touches frozen V53.** NO.
- **Risk.** **high** (R5). **Complexity.** L.

### C3 · Observability — **P0**

- **Objective.** Every live decision reconstructable from logs, with no secret ever printed.
- **Affects.** new `bot/obs/log.py`, `bot/obs/journal.py`, `bot/obs/metrics.py`, `bot/obs/health.py`.
- **Depends on.** A3, C1.
- **Acceptance.**
  1. Structured JSON logs, one event per line, every line carrying `run_id`, `bar_ts`,
     `strategy_sha256`, and where applicable `signal_id` / `client_order_id`.
  2. A **decision journal** row for every slot transition (`st` change), every risk veto with its
     reason code, and every order intent — sufficient to answer "why did/didn't it trade" without
     re-running.
  3. Counters mirroring the Pine funnel (sweeps → CHOCH → retest → BOS → FVG → fills) plus
     order/fill/reject/reconcile-divergence counters, exposed on a local health endpoint.
  4. A log-redaction test: every configured secret value is asserted absent from a full capture of
     a simulated session's log output.
  5. Health endpoint reports: last bar processed, data staleness, broker connectivity, kill-switch
     state, open positions, and whether the engine is halted and why.
- **Tests.** `test_logging_redaction.py`, `test_journal_completeness.py` (every emitted signal has a
  full transition chain in the journal).
- **Phase-16-safe.** YES. **Touches frozen V53.** NO.
- **Risk.** low. **Complexity.** M.

### C4 · Execution interface and idempotency — **P0**

- **Objective.** A broker-agnostic execution port with deterministic idempotency, so paper and live
  differ only in the final adapter.
- **Affects.** new `bot/exec/interface.py` (`Broker` protocol), `bot/exec/idempotency.py`,
  `bot/exec/order.py`, `bot/exec/oms.py`.
- **Depends on.** A3, C1.
- **Acceptance.**
  1. `Broker` protocol: `submit`, `cancel`, `replace`, `get_orders`, `get_positions`,
     `get_account`. Paper and live implement the same protocol; the OMS has **no** branch on which
     one is attached.
  2. `client_order_id = sha256(strategy_sha256 ‖ instrument ‖ direction ‖ ltf ‖ slot_index ‖
     sweep_ts ‖ choch_ts ‖ bos_ts ‖ entry_price ‖ intent_seq)[:32]` — derived only from immutable
     signal fields (audit §8).
  3. Replaying the same signal, restarting mid-submission, or double-delivering a message produces
     the **same** `client_order_id`; the second submit is a no-op resolved against the store, and a
     test proves no second order reaches the broker.
  4. **No strategy-level deduplication.** Convergent signals (R7) keep separate ids and both reach
     the OMS. A test asserts a Phase-13G-shaped 3-signal cluster produces 3 distinct ids.
  5. The execution layer **never computes a price** — a test greps the module for arithmetic on bar
     fields, and the OMS receives prices only from `Signal` (audit §3.3).
  6. Order state machine: `intent → submitted → acked → (partial)* → filled | rejected | cancelled`,
     with every transition persisted before the next action.
- **Tests.** `test_idempotency.py` (replay, restart, duplicate delivery, convergent cluster),
  `test_oms_states.py`, `test_no_price_derivation.py`.
- **Phase-16-safe.** YES. **Touches frozen V53.** NO.
- **Risk.** **high** (R6). **Complexity.** L.

### C5 · Paper broker — **P0**

- **Objective.** A deterministic simulated broker implementing the same `Broker` protocol, with an
  **explicit, switchable fill model** so the audit's optimistic assumptions become measurable
  choices rather than hidden defaults.
- **Affects.** new `bot/exec/paper/broker.py`, `bot/exec/paper/fills.py`,
  `bot/exec/paper/accounting.py`.
- **Depends on.** C4.
- **Acceptance.**
  1. Two fill models, both implemented, selected by config, both logged in every run header:
     - `research_parity` — touch⇒fill, entry bar not evaluated for stop/target. Reproduces V53.
     - `conservative` — requires trade-through (`low < E` long / `high > E` short) **and**
       evaluates the entry bar for stop and target, adverse-first.
  2. Running the paper broker in `research_parity` over a golden cell reproduces the B3 ledger
     exactly — the paper broker is proven not to add drift.
  3. Commission `costUSD = 3.00` per round trip applied exactly as V53 applies it.
  4. Slippage model configurable and defaulting to **non-zero** in `conservative`; a run with
     slippage 0 is labelled as such in the report.
  5. Partial fills, rejects and cancels are simulable on demand (needed by E2).
  6. Deterministic: same inputs and same config → byte-identical fills. No randomness without a
     recorded seed.
- **Tests.** `test_paper_broker.py`, plus a parity test asserting `research_parity` == B3 ledger and
  a test asserting `conservative` differs on at least the constructed same-bar-stop case from B4.
- **Phase-16-safe.** YES. **Touches frozen V53.** NO.
- **Risk.** medium. **Complexity.** L.

### C6 · Risk engine — **P0**

- **Objective.** An independent veto layer that sizes positions from the stop distance and enforces
  account and prop-firm limits. It never changes a level.
- **Affects.** new `bot/risk/engine.py`, `bot/risk/sizing.py`, `bot/risk/limits.py`,
  `bot/risk/prop.py` (ported from `trader/prop_rules.py`), `bot/risk/killswitch.py`.
  `trader/prop_rules.py` itself is **not modified** — it is read as design input and re-implemented
  with tests.
- **Depends on.** A3, C1, C3.
- **Acceptance.**
  1. Sizing derives contracts from `r_distance`, tick value and per-trade risk budget, rounding
     **down**; a zero-contract result is a veto, never a widened stop (audit §3.3).
  2. Every veto emits a reason code and a journal row. Reason codes are a closed enum.
  3. Limits implemented and individually provable: max concurrent positions, max daily loss,
     max drawdown / MLL, per-instrument exposure cap, consistency rule, session windows,
     max orders per bar, max orders per day.
  4. Optional, explicit, **off by default**, and reported separately: a concurrent-exposure cap on
     convergent signals sharing an `event_key_alt` (R7). Turning it on is a *risk policy* decision,
     logged, and its effect on results reported separately from strategy results.
  5. Kill switch **latches**: once tripped only a deliberate operator action clears it; a restart
     does not clear it (state persisted).
  6. The risk engine cannot emit or alter a price, and cannot create a signal. Enforced by test.
- **Tests.** `test_sizing.py` (rounding, zero-size veto), `test_limits.py` (one test per limit
  proving it blocks), `test_killswitch_latch.py` (trip → restart → still tripped),
  `test_prop_rules_port.py` (ported behaviour matches `trader/prop_rules.py` on shared cases).
- **Phase-16-safe.** YES. **Touches frozen V53.** NO.
- **Risk.** high. **Complexity.** L.

---

## 6. Phase D — Real-time data

### D1 · Data-engine contract, gap and staleness detection — **P0**

- **Objective.** One data contract with mandatory integrity checks, so the strategy never runs on
  incomplete or stale bars.
- **Affects.** new `bot/data/feed.py` (protocol), `bot/data/integrity.py`, `bot/data/clock.py`.
- **Depends on.** B1.
- **Acceptance.**
  1. A bar is delivered to the engine only when `complete == True` and its LTF sub-bar count is
     consistent with the timeframe (5 for 1m, 1–2 for 3m per V53's own handling); a short LTF array
     is surfaced as a counted, journalled condition — **never silently accepted** (audit §1.2).
  2. Staleness: if no closed 5m bar arrives within `bar_period + tolerance`, the engine enters
     `HALTED_STALE`, stops emitting, and does **not** self-resume without a fresh complete bar.
  3. A detected gap in the 5m series halts the engine and requires an explicit backfill-and-replay
     action; the engine never interpolates.
  4. Time is UTC end-to-end; a test asserts no local-time conversion anywhere in the data path and
     that DST transitions do not shift bar boundaries.
  5. `assert_pre_fe` is **not** applied to the live feed (live is allowed to be recent) — but the
     live feed is unreachable from any test or fixture path, enforced by config separation.
- **Tests.** `test_integrity.py` (gap, duplicate, out-of-order, short LTF, stale), `test_clock.py`.
- **Phase-16-safe.** YES for the contract and tests. See note under D2/F1 about *running* it forward.
- **Touches frozen V53.** NO.
- **Risk.** high (R2). **Complexity.** M.

### D2 · TradingView/CDP data adapter — **P1**

- **Objective.** A feed adapter over the existing MCP bridge, explicitly labelled research-grade.
- **Affects.** new `bot/data/adapters/tv_cdp.py`; reads `src/**` over the existing MCP/CLI surface.
  `src/**` is not modified.
- **Depends on.** D1.
- **Acceptance.**
  1. Implements the D1 feed protocol including gap/staleness, on top of the 500 ms poll-and-diff
     stream (`src/core/stream.js`).
  2. Reconnect: a dropped CDP session halts the engine, reconnects, refuses to resume until a
     complete bar is verified, and never fabricates the missed bar.
  3. Startup refuses if TradingView Desktop is not on the expected symbol/timeframe, or if the chart
     buffer is shorter than the warmup requirement.
  4. **The module docstring states plainly that this adapter is not a production data path** — no
     SLA, GUI-dependent, breaks on app update (audit R2) — and the live-trading config refuses to
     select it (hard error at startup, not a warning).
  5. **Phase 16 interlock:** this adapter is inert unless `strategy_id != "V53"` or
     `mode == replay_pre_fe`, until 2027-04-02. Attempting to run live V53 through it before that
     date raises `HeldOutDataError`. Running V53 forward on the accumulating window *is* consuming
     the held-out data (audit §7.5).
- **Tests.** `test_tv_cdp_adapter.py` against a recorded CDP transcript (no live app in CI);
  `test_p16_interlock.py` proving the refusal.
- **Phase-16-safe.** YES **only with the interlock in acceptance criterion 5.** Without it, NO.
- **Touches frozen V53.** NO.
- **Risk.** high. **Complexity.** L.

### D3 · Production data feed adapter — **P1**

- **Objective.** A non-GUI market-data source suitable for live trading.
- **Affects.** new `bot/data/adapters/<vendor>.py`; config; `.env.example`.
- **Depends on.** D1; vendor/broker selection (an open decision — see §10).
- **Acceptance.**
  1. Implements the D1 protocol with the same integrity guarantees.
  2. Bar boundaries provably identical to TradingView's for the traded instruments over a sampled
     pre-`FE` window — any systematic boundary or timestamp offset is a blocker, documented, not
     absorbed.
  3. Survives a 60-second disconnect with a correct backfill-and-verify, or halts.
  4. Credentials from environment only; nothing committed.
- **Tests.** `test_vendor_adapter.py` against recorded responses; a boundary-comparison report.
- **Phase-16-safe.** YES if the comparison window is pre-`FE`. **The comparison window must be
  pre-`FE`.**
- **Touches frozen V53.** NO.
- **Risk.** high. **Complexity.** L.

---

## 7. Phase E — Robustness

### E1 · Broker reconciliation — **P1**

- **Objective.** Broker truth, not local belief, defines positions and orders.
- **Affects.** new `bot/exec/reconcile.py`; `bot/runtime/lifecycle.py`.
- **Depends on.** C4, C5.
- **Acceptance.**
  1. On every startup and on a fixed cadence (≤ 1 bar), fetch broker orders/positions/account and
     diff against the store.
  2. Any divergence — unknown position, unknown order, quantity mismatch, price mismatch — **halts
     the engine and latches the kill switch**. It never auto-corrects silently.
  3. An injected divergence is detected within one cycle; test proves it.
  4. Orphan detection: an order at the broker with no local record, and a local record with no
     broker order, are both detected.
  5. Reconciliation results are journalled every cycle, including the clean ones.
- **Tests.** `test_reconcile.py` with a fault-injecting paper broker covering all five divergence
  shapes.
- **Phase-16-safe.** YES. **Touches frozen V53.** NO.
- **Risk.** **high** (R6). **Complexity.** M.

### E2 · Failure and chaos testing — **P1 · ★ GATES 3, 4**

- **Objective.** Prove the system fails safe under the failures that actually occur.
- **Affects.** new `bot/tests/chaos/`; `bot/tools/faultinject.py`.
- **Depends on.** C2, C4, C5, E1.
- **Acceptance.** Each scenario ends with **no duplicate order, no orphan position, no silent
  resumption**, and a journal that explains what happened:
  1. `kill -9` at six lifecycle points: after signal emit / before submit; after submit / before ack;
     after ack / before fill; after fill / before persist; mid-reconcile; mid-bar-processing.
  2. Broker rejects the entry; broker rejects the stop (**must halt — an unprotected position is a
     kill-switch event**); broker accepts entry but never acks the stop.
  3. Partial fill, then disconnect.
  4. Data feed stalls for 3 bars, then resumes with a gap.
  5. Duplicate signal delivery; duplicate bar delivery.
  6. Clock skew: a bar timestamped in the future.
  7. Disk full on the SQLite write path.
- **Tests.** the scenarios above as automated tests, each asserting the store's final state and the
  absence of duplicate `client_order_id`s.
- **Phase-16-safe.** YES — all synthetic. **Touches frozen V53.** NO.
- **Risk.** high. **Complexity.** L.

### E3 · Fill-model calibration — **P1**

- **Objective.** Measure, rather than assume, the two optimistic assumptions in audit §4.4.
- **Affects.** new `bot/analysis/fill_calibration.py`; `bot/reports/fill_model.md` (generated).
- **Depends on.** B3, C5, F1 (partially — needs paper fills).
- **Acceptance.**
  1. Quantifies, over pre-`FE` replay and over paper sessions: the fraction of `research_parity`
     fills that would **not** have filled under `conservative` (touch⇒fill exposure, R3), and the
     fraction of fills that would have been stopped on the entry bar (R4).
  2. Reports the resulting R-distribution shift **as a software-model measurement**, with an
     explicit statement in the report that it is **not** evidence about V53's edge and does **not**
     alter Phase 16 (audit §11).
  3. Uses **no** data at or after `FE_MS`; the report header asserts the window used.
  4. Produces a recommended default fill model for paper trading, with the recommendation stated as
     a *conservatism* choice, not an optimisation.
- **Tests.** `test_fill_calibration.py` on synthetic cases with known answers.
- **Phase-16-safe.** YES, given criterion 3. **Touches frozen V53.** NO.
- **Risk.** medium. **Complexity.** M.

### E4 · Deployment and process supervision — **P1**

- **Objective.** A single reproducible way to run the bot unattended.
- **Affects.** new `deploy/` — `Dockerfile`, `compose.yaml`, `systemd/bot.service`,
  `bot/cli/main.py`, `bot/config/`, `.env.example`, `deploy/RUNBOOK.md`.
- **Depends on.** C1, C2, C3, C6, D3.
- **Acceptance.**
  1. One command starts the bot; pinned dependency versions; the image records the git sha and the
     `strategy_sha256`.
  2. Auto-restart on crash, with a **restart storm limit** — more than N restarts in M minutes
     latches the kill switch rather than looping.
  3. Config is layered `defaults → file → env`, fully logged at startup **with secrets redacted**;
     startup fails fast if any required var is missing.
  4. `bot/var/` (the SQLite file) is a mounted volume and survives container replacement; a
     documented, tested backup/restore procedure exists.
  5. `RUNBOOK.md` covers: start, stop, flatten-and-halt, clear kill switch, restore from backup,
     what to do on each halt reason code.
  6. Time sync verified at startup (NTP offset within tolerance) — the bar clock is load-bearing.
- **Tests.** a smoke test that boots the container, processes a fixture session, and exits clean;
  a restart-storm test; a backup/restore test.
- **Phase-16-safe.** YES. **Touches frozen V53.** NO.
- **Risk.** medium. **Complexity.** M.

---

## 8. Phase F — Operating

### F1 · Paper-trading soak — **P1 · ★ GATES 2, 3, 4, 5, 6**

- **Objective.** Run the complete system end to end, unattended, long enough to trust it.
- **Affects.** no new components — operating the built ones. Produces `bot/reports/soak/*.md`.
- **Depends on.** C1–C6, D1, D2 or D3, E1, E2, E4.
- **Acceptance.**
  1. **Before 2027-04-02 the soak runs in one of exactly two modes** (audit §7.5):
     (a) pre-`FE` historical replay driven through the *live* code path, or
     (b) forward paper trading on a **non-V53 dummy strategy**.
     Running live V53 forward before the boundary is prohibited — it consumes the held-out window.
     The D2 interlock enforces this in code, not by discipline.
  2. ≥ 30 sessions with zero unexplained discrepancies; every discrepancy either explained in the
     journal or treated as a defect and fixed.
  3. Every signal traceable end to end: journal → signal → order intent → `client_order_id` →
     fill → position → exit, reconstructable from logs alone.
  4. Reconciliation clean on every cycle, or halted with cause.
  5. At least one deliberate restart and one deliberate kill-switch trip during the soak, recovered
     per the runbook.
  6. A soak report per session and a summary report; **the summary contains no claim about V53's
     edge** — it is a software-reliability report.
- **Tests.** the soak is the test; automated post-session assertions on log completeness and
  reconciliation cleanliness.
- **Phase-16-safe.** YES **only under criterion 1.** This is the single most likely place for
  accidental Phase 16 contamination.
- **Touches frozen V53.** NO.
- **Risk.** high. **Complexity.** L (mostly elapsed time).

### F2 · Live deployment gate — **P1 · ★ GATE 7**

- **Objective.** A deliberate, evidenced, blocked-by-default decision to risk capital.
- **Affects.** `deploy/GO_LIVE_CHECKLIST.md`; config flag `live_enabled` (default false).
- **Depends on.** every P0 and P1 task; **and Phase 16 returning a supportive verdict on or after
  2027-04-02 00:00 UTC.**
- **Acceptance.**
  1. Gates 0–6 all have written evidence artifacts committed.
  2. **Phase 16 has reached its pre-registered boundary and returned a supportive verdict.** A
     working bot is not a reason to trade (audit §11). An INSUFFICIENT or against verdict blocks
     this gate; the correct response is a new hypothesis, not a lower bar.
  3. Live enablement requires an explicit operator action plus a second confirmation; it cannot be
     the default in any config file.
  4. First live period runs at minimum size with a hard daily loss limit and a scheduled review.
  5. A written rollback plan: how to flatten, halt, and revert to paper within one bar.
- **Tests.** checklist review; a test asserting `live_enabled` defaults to false in every committed
  config.
- **Phase-16-safe.** YES (it *depends* on Phase 16 but does not touch its data).
- **Touches frozen V53.** NO.
- **Risk.** critical (capital). **Complexity.** S — the work is evidence, not code.

---

## 9. Phase G — Hygiene and future

| id | task | objective | affects | depends | acceptance | tests | P16-safe | frozen V53 | risk | cx | pri |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G1 | Consolidate ledger parsers | one parser instead of six (R9) | new `bot/analysis/ledger.py`; `trader_v2/**` scripts left in place | A2 | new parser reproduces each existing script's output on its own inputs, byte-identical; old scripts untouched as historical evidence | golden comparison per script | YES | NO | low | M | **P2** |
| G2 | Python in CI | the research and bot Python is linted and tested in CI | `.github/workflows/ci.yml` | A1 | Python job green; `gate1` job green; `no-p16-imports` green | — | YES | NO | low | S | **P2** |
| G3 | Repo hygiene | remove the stray 0-byte `=` file; resolve the single TODO at `src/core/pine.js:516`; document `strategies/` and `trader/` as superseded | root, `src/core/pine.js`, `STATE_OF_PLAY.md` note | — | `=` gone; `STATE_OF_PLAY.md` carries a header stating the V38 "live" claim predates V53 and is not the current position; nothing deleted from `trader/` or `strategies/` | CI | YES | NO | low | S | **P2** |
| G4 | Ledger-cap remediation *for future research builds only* | remove the 40-row truncation (R8) so future runs are not silently capped | **a future, separately authorized research build — NOT the frozen artifacts** | new phase authorization | not schedulable under current authorizations | — | YES | **would be YES — therefore prohibited under the current phase rules** | — | — | **P3, blocked** |
| G5 | Strategy portability | make the harness accept a second strategy so the next hypothesis reuses it | `bot/strategy/` interface | B3, F1 | a trivial second strategy runs end to end through the same runtime with no runtime changes | integration test | YES | NO | low | M | **P3** |
| G6 | Multi-instrument / multi-account scaling | run MGC and MNQ concurrently with independent state and shared risk | `bot/runtime/`, `bot/risk/` | C2, C6 | two instruments run concurrently with isolated strategy state and a single shared risk ledger; parity unaffected | integration test | YES | NO | medium | M | **P3** |

---

## 10. Priority summary

| priority | tasks |
|---|---|
| **P0 — before paper trading** | A1, A2, A3, B1, B2, B3, B4, C1, C2, C3, C4, C5, C6, D1 |
| **P1 — before live capital** | D2, D3, E1, E2, E3, E4, F1, F2 |
| **P2 — important, can follow** | G1, G2, G3 |
| **P3 — optional / future** | G4 (blocked), G5, G6 |

---

## 11. Critical path

```
A1 ─▶ A2 ─▶ B1 ─▶ B2 ─▶ B3 ★GATE1 ─▶ C2 ─▶ E1 ─▶ E2 ★G3,G4 ─▶ F1 ★G2,G5,G6 ─▶ F2 ★G7
      A3 ─▶ B2                                                        ▲
                                                          D1 ─▶ D2/D3 ┘
```

The critical path is **A1 → A2/A3 → B1 → B2 → B3 → C2 → E1 → E2 → F1 → F2**.

**B2 → B3 is the dominant cost and the dominant risk.** It is XL + L, it is the only task rated
critical for correctness, and every downstream component is worthless if it is wrong. Resourcing
should reflect that: if only one thing gets careful review, it is the parity harness.

**F1 is the dominant elapsed time** — ≥ 30 sessions cannot be compressed.

**F2 is calendar-blocked** on Phase 16 (2027-04-02 00:00 UTC) regardless of engineering progress.
This is a feature: it guarantees a long runway, so there is no schedule pressure to cut corners on
B2/B3, and no engineering reason to touch the held-out window.

---

## 12. Parallelizable work

Four tracks can run simultaneously from day two (after A1).

| track | tasks | depends on | notes |
|---|---|---|---|
| **1 — Strategy (critical path)** | A2 → B1 → B2 → B3 → B4 | A1 | one engineer, uninterrupted; this is where the risk lives |
| **2 — Execution** | A3 → C4 → C5 → E1 | A1 | needs only the `Signal` schema — **never blocked on B2** |
| **3 — Platform** | C1 → C3 → E4 → G2 → G3 | A1 | persistence, logging, deployment, CI |
| **4 — Risk** | C6 (port of `trader/prop_rules.py`) | A3 | fully independent; testable against synthetic signals |

Join points:

- **C2** requires track 1 (through B3) **and** track 3 (C1). It is the first real convergence.
- **E2** requires tracks 1, 2, 3.
- **F1** requires everything.
- **D1** can start any time after B1; **D2/D3** any time after D1, independently of tracks 1–4.
- **E3** needs both B3 and paper fills from F1 — schedule it as a mid-soak deliverable.

Anti-parallel warnings:

- **Do not parallelise inside B2.** The 24-slot machine, the ring buffer and the section ordering
  are one coupled artifact; splitting it across engineers is how drift enters.
- **Do not start C5 tuning before B3 passes.** A "better" fill model layered on a wrong strategy
  produces confident nonsense.
- **Do not let track 2 or 4 invent prices.** Both are structurally tempted to; C4 acceptance
  criterion 5 and C6 criterion 6 exist to catch it.

---

## 13. Open decisions that block specific tasks

These are genuinely the operator's, not the implementer's. None blocks the critical path before C4.

1. **Broker / prop firm.** Blocks D3, and the live half of C4. The prop-rule port (C6) targets
   LucidFlex per `trader/prop_rules.py`; confirm that is still the target.
2. **Production data vendor.** Blocks D3. Must produce bar boundaries matching TradingView's.
3. **Host.** Blocks E4 detail. A single trusted host justifies `.env`; anything else needs a secret
   manager.
4. **Per-trade risk budget and account size.** Blocks C6 defaults. Not a strategy parameter — a
   risk-policy input, and choosing it from research results would be optimisation.
5. **Paper mode before 2027-04-02.** F1 criterion 1: pre-`FE` replay, or a dummy forward strategy?
   Both are permitted; replay is the stronger correctness test, dummy-forward is the stronger
   infrastructure test. Recommendation: do both — replay first, dummy-forward during the soak.

---

## 14. Explicitly NOT in this roadmap

- Any modification to `trader_v2/V53_ltf_sequence.pine`, `trader_v2/p15/executed/`,
  `trader_v2/p15/exec_arms/`, or `trader_v2/p16/**`.
- Any change to the Phase 16 protocol, its window, its statistic, or its stopping boundary.
- Any run of V53 — Pine or Python — against data at or after `FE = 1788134400000`.
- Any parameter change, filter addition, threshold change, or "improvement" to V53. Fixing the
  entry-bar gap (§4.4b) or the touch⇒fill assumption (§4.4a) **inside the strategy** is a strategy
  change and is prohibited; both are reproduced faithfully and measured in the *execution* layer.
- Any strategy-level deduplication of convergent sequences.
- Combining Phase 15 variants, or promoting any arm.
- Live capital before F2.

---

## 15. The honest summary

The engineering is large but ordinary: roughly one XL task, six L tasks, and a tail of M/S work —
call it 3–5 months for one engineer to reach a defensible paper-trading soak, with F2 calendar-
blocked until April 2027 regardless.

The uncomfortable part is not the schedule. It is that **Phase 15 found no edge**, the baseline is
negative under all three accountings, and Phase 16 is powered only against a large effect. This
roadmap is worth executing anyway — the harness outlives the hypothesis, and every gate here is
reusable — but it should be executed with clear eyes: **a correct bot is not a reason to trade V53,
and no result produced by this bot is evidence about V53's edge.**

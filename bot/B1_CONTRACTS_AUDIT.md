# B1 — Strategy and data contracts: audit

Roadmap task B1. **No V53 strategy logic was implemented, no research artifact
was modified, no market data was obtained, no TradingView connection was made,
and no Phase 16 or post-FE data was inspected or consumed.**

Date: 2026-09-06. Preceded by A1 (`ade51b3`) and A2 (`acdb8e1`).

---

## 1. What was built

| artifact | lines | what it is |
|---|---|---|
| `bot/contracts/enums.py` | 165 | closed vocabularies, each mapped to its V53 counter |
| `bot/data/bars.py` | 226 | market-data contract |
| `bot/contracts/state.py` | 325 | strategy-state contract |
| `bot/contracts/events.py` | 334 | event and signal contract |
| `bot/contracts/engine.py` | 108 | the output boundary |
| `bot/contracts/serialize.py` | 62 | deterministic serialisation |
| `bot/contracts/SCHEMA.md` | 128 | the format |
| `bot/contracts/UNRESOLVED.md` | 158 | what could not be settled |
| `bot/tests/test_contracts.py` | 446 | 67 contract tests |
| `bot/tests/test_contract_fixture_compat.py` | 242 | 19 A2 compatibility tests |

Everything is a container or a vocabulary. Nothing detects a sweep, selects a
CHOCH, qualifies a displacement, tests a fill or decides an outcome.

---

## 2. Two design decisions worth stating

**No trading rule is enforced by a schema.** The contracts do not validate that
a target sits 5R from entry, that `r_atr_ratio` falls inside V53's
[0.05, 3.00] band, or that a stop lies on a particular side of entry. This
**supersedes the validator sketch in `BOT_IMPLEMENTATION_AUDIT.md` §3.2**, which
proposed exactly those checks.

Two reasons. First, a schema that re-states V53's rules becomes a second, silent
implementation of the strategy — and B3 could never catch it diverging, because
both sides would encode the same assumption. Second, it would be *wrong today*:
two of the 58 A2 fills carry a stop on the near side of entry (the FVG far edge
can lie beyond the sweep extreme), and a side check would reject real recorded
V53 output.

**`SequenceRef.slot_index` is optional.** V53's ledger never emits the slot
index, so every signal reconstructed from an A2 fixture has none. Rather than
invent a value to satisfy a `0..23` constraint, the contract represents the
absence. This was found by building the A2 compatibility test, not by guessing.

---

## 3. State represented

All sixteen strategy arrays and all ten ledger arrays, under readable names,
with the V53 name in the docstring of each. Nothing collapsed:
`cBar`/`rBar`/`dBar` are three distinct load-bearing LTF indices;
`mfe`/`mae` are kept although neither reaches the ledger; `pRef` is kept although
it only feeds a diagnostic counter.

Also represented: the 24-slot array (ordered, index-checked), the 7-bar LTF ring
buffer (size-capped), the 4-entry pivot register (last/prev high, last/prev low),
the 5m sweep-engine levels, `ltfN`, and the parent bar index.

`SequenceSlot.LEDGER_FIELDS` preserves V53's own split between strategy state
and "measurement only; no strategy state" — the distinction that decides what
B3 may treat as behaviour and what merely records.

---

## 4. Unresolved semantics

Five, all in `bot/contracts/UNRESOLVED.md`, all marked rather than guessed:

| id | what | severity |
|---|---|---|
| **U1** | PDH/PDL roll on `ta.change(time("D"))` — the **exchange session day**, not UTC midnight, while the Asia window is explicitly UTC. B2 needs the CME session calendar. | **blocking** |
| **U2** | The LTF timestamp fallback: when `aT` is shorter than the OHLC arrays, V53 substitutes the 5m bar time. Whether this ever fired is unknowable from the records. | needs a decision |
| **U3** | 3m sub-bars do not tile a 5m parent. The *aggregate* is settled (34,269/20,567 = 1.6662 ≈ 5/3, exactly as tiling predicts); the *per-parent* alignment is not. | structural |
| **U4** | `syminfo.pointvalue` is environment data, not a frozen constant. A2 derived MGC 10 / MNQ 2, but the fallback to `1.0` must not reach the bot. | correctness |
| **U5** | `ta.atr(14)` warmup is TradingView's RMA seeding, not the artifact's. It sets the stop buffer, displacement threshold, wick minimum and R-band denominator. | precision |

Eight further items are recorded as **resolved but easy to get wrong** —
including that V53's timestamps are bar *open* times (proved by fold B's
coverage beginning exactly at `FB`), that `dispWait` counts chart bars not
minutes, that displacement compares an LTF range against the 5m ATR, and that a
stop can legitimately sit on the near side of entry.

One correction made during this task: an early draft of U3 computed the 3m
sub-bar ratio against *fold* bars rather than *chart* bars and concluded there
was an unexplained 8.2× discrepancy. Recomputed against all 20,567 chart bars
the ratio is 1.6662, i.e. exactly 5/3. The aggregate is fully explained; only
the per-parent alignment remains open.

---

## 5. A2 compatibility

All **58 recorded fills across all 24 fixtures** map into `StrategySignal`
without loss and without invention:

- every price, timestamp, sweep kind, outcome, R multiple, P&L and bar count
  survives exactly;
- all five recorded sweep kinds (`SW`, `AS`, `PD`, `AS+SW`, `PD+AS`) are covered
  by the enum;
- the six zero-fill cells correctly produce no signals;
- unrecorded fields stay `None`/`-1`, and a test asserts the fixtures declare
  those same gaps in `not_captured`;
- all 58 `signal_id`s are unique and reproducible.

**Identity agrees with Phase 13G.** The contract renders event keys from
epoch-ms and `Decimal`, while A2 renders them from UTC text — different strings
for the same identity. The test therefore compares the **partitions** they
induce, not the strings, and both the primary and alternative partitions match
exactly. Convergence survives: MNQ L 1m B is still 7 fills over 3 alternative
events.

---

## 6. Determinism

`serialize.encode` **raises on any float**, emits `Decimal` as exact text, sorts
mapping keys and preserves sequence order. No contract value can contain a wall
clock read, a random id, or a filesystem path. `signal_id` is a content hash
computed excluding the outcome, so it is stable from fill through resolution —
verified by test.

---

## 7. Tests

166 in the suite (67 B1 contract + 19 B1 compatibility + 42 A1 + 38 A2), all
passing, stdlib `unittest` only.

The B1 tests test **contracts, not V53**. None asserts that a sweep is detected,
a CHOCH selected, or an outcome correct. The compatibility test is
transcription: it maps recorded fields into contract types and checks nothing
was lost.

The A1 guard earned its keep during this task: it failed the build on a
hard-coded FE literal in a B1 test, which was fixed by importing `FE_MS` rather
than by adding an exemption.

---

## 8. Scope

Not done, deliberately: B2 (the strategy engine), B3 (the parity harness),
execution, risk, paper trading, broker connectivity, persistence, observability.

`bot/contracts/engine.py` imports no broker, OMS, risk engine, paper broker,
TradingView client or live feed, and a test asserts it.

Unchanged: `V53_ltf_sequence.pine` `7490766b…`,
`p15/executed/V53_EXECUTED_BUILD.pine` `2dafbafd…`,
`p16/executed/V53_P16_OOS_BUILD.pine` `5c21acfa…`, every file under
`trader_v2/`, `trader/`, `strategies/` and `src/`, and all 25 A2 fixture files.

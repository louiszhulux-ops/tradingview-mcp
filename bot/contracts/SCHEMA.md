# B1 contracts — schema

The typed boundary between V53's data, its state, and its consumers.
**Contracts only**: nothing here detects, selects, qualifies or decides anything.
B2 implements the behaviour; B3 compares its output to the A2 fixtures.

Transcribed from `trader_v2/p15/executed/V53_EXECUTED_BUILD.pine`
(sha256 `2dafbafd…`), the Phase 15 provenance anchor. What could not be settled
from the artifacts is in **`UNRESOLVED.md`**, not guessed at here.

## Modules

| module | contains |
|---|---|
| `bot/contracts/enums.py` | `Direction`, `Timeframe`, `SlotState`, `SweepSource`, `ExitReason`, `Outcome`, `TransitionReason` |
| `bot/data/bars.py` | `Bar`, `ParentBar`, `validate_series` |
| `bot/contracts/state.py` | `StrategyState`, `SequenceSlot`, `LtfRingEntry`, `PivotRecord`, `SweepEngineState`, `SlotTransition` |
| `bot/contracts/events.py` | `SequenceRef`, the seven stage events, `StrategySignal` |
| `bot/contracts/engine.py` | `StrategyEngine` protocol, `BarResult`, `ReplayResult` |
| `bot/contracts/serialize.py` | `encode`, `dumps`, `canonical` |

## Market data

`Bar` is immutable, prices are `Decimal` (a float raises), and both timestamps
pass the A1 pre-FE guard. Validation is data integrity only — OHLC coherence,
exact bar span, minute-aligned open. No trading rule.

`ParentBar` is the unit B2 consumes: one closed **5m** bar plus the LTF sub-bars
it contains, oldest first. It refuses a non-5m parent and a 5m "LTF", so **an
LTF stream cannot substitute for the 5m stream** — the sweep engine, ATR(14),
the fill test and both bar-count deadlines are all defined on 5m bars.

A short LTF array is *represented, not repaired*: `ltf_count` and `ltf_complete`
expose it. `ltf_complete` is meaningful for 1m only (see UNRESOLVED U3).

`validate_series` rejects duplicates, disorder and overlap. It does **not**
require a contiguous grid — weekends, holidays and halts are real.

## Strategy state

`StrategyState` is everything V53 carries between 5m bars, and the object C1
must persist and C2 rehydrate:

- `slots` — exactly 24 `SequenceSlot`, ordered by index (V53 `SP = 24`)
- `ltf_ring` — up to 7 `LtfRingEntry` (`RB = 2 × lSw + 1`), oldest first
- `pivots` — exactly 4 `PivotRecord`: last/prev pivot high, last/prev pivot low
- `sweep_engine` — PDH/PDL, day H/L, Asia H/L, swing H/L, ATR
- `ltf_bars_seen` (`ltfN`, monotonic), `parent_bar_index`

`SequenceSlot` carries **all sixteen** V53 strategy arrays plus **all ten**
ledger arrays, under readable names. Nothing was collapsed for looking
redundant: `choch_ltf_index`, `retest_ltf_index` and `displacement_ltf_index`
(`cBar`/`rBar`/`dBar`) are three separate load-bearing values, and
`max_favourable_r`/`max_adverse_r` are state even though neither reaches the
ledger. `LEDGER_FIELDS` names the ten V53 marks "measurement only".

| contract name | V53 | contract name | V53 |
|---|---|---|---|
| `state` | `st` | `entry` | `ent` |
| `sweep_bar_index` | `swB` | `r_distance` | `rr` |
| `stop` | `stp` | `fvg_wait_bars` | `wt` |
| `atr_at_arm` | `aRf` | `bars_in_trade` | `bIn` |
| `choch_level` | `cLvl` | `max_favourable_r` | `mfe` |
| `pivot_ref` | `pRef` | `max_adverse_r` | `mae` |
| `choch_pivot_index` | `cPvI` | `target_reached` | `flg` |
| `choch_ltf_index` | `cBar` | `retest_ltf_index` | `rBar` |
| `displacement_ltf_index` | `dBar` | `ledger_*` | `lSwT … lEnT` |

## Events and signals

One type per stage: `SweepEvent`, `ChochEvent`, `RetestEvent`, `BosEvent`,
`FvgEvent`, `FillEvent`, `OutcomeEvent`; `StrategySignal` binds a full sequence.

Every stage carries two timestamps, and the difference matters:

- `ts_ms` — the **recorded** time, a bar *open* (see UNRESOLVED R1): a 5m open
  for sweep and fill, an LTF open for CHOCH, retest and BOS.
- `bar_close_ts_ms` — the 5m close at which the stage became knowable, i.e. the
  earliest a live system could act.

Identity:

- `event_key_primary` / `event_key_alternative` — the Phase 13G clustering
  identities. **Analysis identities, never order idempotency keys.**
- `signal_id` — a deterministic content hash, computed *excluding* the outcome
  so it is stable from fill through resolution. Never random.
- `SequenceRef.slot_index` is `None` when not recorded. V53's ledger never emits
  it, so every signal rebuilt from an A2 fixture has none.

### No rule is enforced by a schema

The contracts deliberately do **not** check that `target` sits 5R from `entry`,
that `r_atr_ratio` falls in [0.05, 3.00], or that `stop` lies on a given side of
`entry`. Those are V53's rules; encoding them would make the schema a second,
silent copy of the strategy that B3 could never catch diverging — and two real
A2 fills have a stop on the near side of entry, which such a check would wrongly
reject. This supersedes the validator sketch in `BOT_IMPLEMENTATION_AUDIT.md`
§3.2.

## Transition vocabulary

`TransitionReason` names all 15 ways a slot can change state, each mapped to its
V53 counter via `.k_index`, with `.frees_slot` marking the seven that return a
slot to `FREE`. `SlotTransition` records one change — descriptive only;
constructing one performs nothing.

`SlotState`: `FREE 0`, `ARMED 1`, `CHOCH 2`, `RETESTED 3`, `BOS_AWAIT_FVG 4`,
`FVG_AWAIT_FILL 5`, `IN_TRADE 6` — V53's frozen integer encoding.

## The output boundary

```
ParentBar  →  StrategyEngine.on_bar()  →  BarResult(transitions, signals, resolved)
```

`StrategyEngine` also requires `state`, `snapshot()` and `rehydrate()`.
Implementations must be pure with respect to their inputs: no wall clock, no
randomness, no I/O in the decision path.

Not connected to a broker, OMS, risk engine, paper broker, TradingView or live
feed — and must not be. A test asserts the module imports none of them.

## Determinism

`serialize.encode` refuses floats, emits `Decimal` as exact text, sorts mapping
keys, and preserves sequence order. `dumps` is canonical JSON; `canonical` is
the compact form used for hashing. No wall clock, no random id, no filesystem
path enters a contract value.

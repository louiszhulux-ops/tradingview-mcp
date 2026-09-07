# `bot/` — trading-system implementation tree

Status: **roadmap task A1 only.** This tree currently contains the Phase 16
contamination guard and its static checker. There is no strategy, data loader,
execution, risk or persistence code yet. See
`trader_v2/BOT_IMPLEMENTATION_ROADMAP.md`.

## Boundaries

`bot/` is the only writable code tree for the trading system. Everything else
is **research and is read-only**:

| tree | contents | rule |
|---|---|---|
| `trader_v2/` | V53, Phases 13–16, analysis | read-only. `trader_v2/p16/**` is **forbidden entirely** |
| `trader/` | v1 Python skeleton (targets V38) | read-only design input; re-implement with tests, never import |
| `strategies/` | superseded V11–V38 line | read-only history |
| `src/` | Node MCP/CDP bridge | read-only; not a production data path |

Roadmap task A2 will read the already-consumed fold A/B/C run files under
`trader_v2/v53_runs/` and `trader_v2/v53_runs_foldc/`. That is permitted — those
folds are spent. `trader_v2/p16/**` is not, and never will be during development.

## The Phase 16 guard

Phase 16 is a pre-registered out-of-sample validation. It accumulates
forward-held-out data from **FE = 2026-08-31 00:00 UTC (1788134400000 ms)** until
**2027-04-02 00:00 UTC**. Reading that window during development — in a test, a
fixture, a backtest, a debugging session, or a forward paper run of V53 —
consumes the held-out data and invalidates the study.

`bot/guards.py` holds the single authoritative definition of `FE_MS` and the
`assert_pre_fe()` guard. It **fails closed**: a timestamp is accepted only when
it is provably a valid, positive, pre-FE epoch-millisecond `int`. `None`, a
float, a string, a bool and a non-positive value are all rejected rather than
coerced, because a timestamp that cannot be checked cannot be shown to be safe.

```python
from bot.guards import assert_pre_fe, assert_all_pre_fe, HeldOutDataError
```

Catch `HeldOutDataError` only to stop. It is never a recoverable condition.

## Static enforcement

```
python3 bot/tools/check_guards.py          # checks bot/
python3 -m unittest discover -s bot/tests -t .
```

Four checks, all run in CI:

1. **No Phase 16 dependency** — nothing under `bot/` may reference the Phase 16
   tree, its protocol/derivation/audit files, or its out-of-sample build.
2. **Single FE definition** — the boundary literal may appear only in
   `bot/guards.py`.
3. **Loaders require the guard** — every module under `bot/data/` and
   `bot/fixtures/` must import from `bot.guards`, so no data path can be written
   that silently accepts a post-FE timestamp.
4. **No live TradingView data in development code** — files under `bot/tests/`
   and `bot/fixtures/` may not reference the MCP/CDP chart surface. Live chart
   reads return *recent* bars, which are inside the held-out window. The check is
   scoped to development paths; a production adapter (roadmap D2) is governed by
   its own Phase 16 interlock instead.

A line carrying `GUARD-ALLOW` is exempt from checks 1, 2 and 4. Every exemption
is printed by the checker on every run, so exemptions are visible rather than
silent. They are legitimate only for the checker's own pattern definitions,
negative-test fixtures, and the authoritative-value assertion in
`bot/tests/test_guards.py`. A test asserts this.

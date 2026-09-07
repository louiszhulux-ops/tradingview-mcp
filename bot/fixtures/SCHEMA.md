# Golden fixture schema — v1

24 fixtures at `bot/fixtures/golden/v53-{INST}-{DIR}-{LTF}-{FOLD}.json`, plus
`manifest.json`. Produced by `bot/tools/extract_golden.py` from the committed
Phase 13F / Phase 14 run records. Read them through `bot/fixtures/loader.py`,
which re-applies the A1 pre-FE guard to every timestamp.

**These are expected results, not inputs.** B2 (the Python V53) computes its own
results from bars; B3 compares them to these. Never feed a fixture into the
strategy engine.

## Numeric convention

Every price, R multiple and dollar amount is a **JSON string** carrying the exact
text of the recorded value (`"4055.7894"`). Parse with `Decimal`, never `float`.
Counters and bar counts are JSON integers. Timestamps are integer epoch
milliseconds UTC, alongside the source's `"YYYY-MM-DD HH:MM"` text.

## Top level

| key | type | meaning |
|---|---|---|
| `schema_version` | int | 1 |
| `fixture_id` | str | `v53-MGC-L-1m-A` — unique, stable |
| `cell` | obj | `instrument` (`MGC1!`), `instrument_short`, `direction` (`L`/`S`), `ltf` (`1m`/`3m`), `fold` (`A`/`B`/`C`) |
| `provenance` | obj | see below |
| `coverage` | obj | `start_utc`/`start_ms`, `end_utc`/`end_ms` — the run's bar coverage |
| `funnel` | obj | 17 counters, verbatim |
| `asserts` | obj | `raw`, `all_zero`, `values` (null when the source collapsed them to "all 0") |
| `performance` | obj | `fills`, `zero_trades`, and when traded: `wins`, `losses_stop`, `timeouts`, `wr`, `rpre`, `rpost`, `avg`, `med`, `exp`, `max_consec_losses`, `dd_r`, `dd_usd`, `total_usd` |
| `fills_truncated_at_source` | bool | true if the Pine 40-row ledger cap bit. **False for all 24** — the largest cell has 10 fills |
| `fills` | list | one entry per fill, see below |
| `source_notes` | list | research annotations from the run file, verbatim |
| `not_captured` | list | what the source records cannot supply — read this before writing a B3 assertion |

### `provenance`

`source_file`, `source_sha256`, `research_phase` (`13F` or `14`), `strategy_id`
(`V53`), `executed_artifact` + `executed_artifact_sha256`, `canonical_artifact` +
`canonical_artifact_sha256`, `attribution_note`, `extractor`,
`extractor_version`.

The `attribution_note` matters. The canonical `V53_ltf_sequence.pine`
(`7490766b…`) **never executed** — that is the Phase 15 provenance correction.
The executed artifact (`2dafbafd…`) is the earliest hashed build of the program
that produced this data, and it reproduced the committed Phase 13F/14 per-cell
results exactly under pooled packaging. No hash was captured at Phase 13F/14 run
time, so this is **attribution by reproduction, not a contemporaneous record.**

### `funnel`

`fold_bars`, `fold_bars_with_ltf`, `ltf_bars` (nullable — only some runs report
it), `sweeps`, `choch`, `retests`, `bos_displacement`, `fvg`, `fills`,
`break_no_displacement`, `no_fvg`, `r_band_rejects`, `fvg_retest_expiry`,
`expire_pre_choch`, `expire_post_choch`, `expire_post_retest`, `dropped_no_slot`.

The conservation identity `fvg = fills + r_band_rejects + fvg_retest_expiry`
holds in all 24 fixtures and is asserted by the test suite.

### `fills[]`

```
{ "index": 0, "recorded": {...}, "derived": {...}, "event_keys": {...} }
```

**`recorded`** — verbatim from the ledger row, the authoritative expectation:

| stage | fields |
|---|---|
| 1 sweep | `sweep_ts_utc`, `sweep_ts_ms`, `sweep_kind` (`PD`/`AS`/`SW`, or a `+` combination), `sweep_extreme` |
| 2 CHOCH | `choch_ts_utc`, `choch_ts_ms`, `choch_level` |
| 3 CHOCH retest | `retest_ts_utc`, `retest_ts_ms` |
| 4 BOS | `bos_ts_utc`, `bos_ts_ms`, `bos_level` |
| 5 FVG | `fvg_low`, `fvg_high` |
| 6 entry/fill | `entry_ts_utc`, `entry_ts_ms`, `entry_price` |
| 7 stop | `stop_price` |
| 8 outcome | `outcome` (`WIN`/`LOSS`), `r_multiple`, `pnl_usd`, `exit_reason` (`target`/`stop`/`timeout`), `bars_in_trade` |

Plus `instrument`, `direction`, `ltf`, `fold` for self-identification.

**`derived`** — arithmetic on recorded fields, **not** recorded expectations:

| field | how |
|---|---|
| `r_distance` | `abs(entry_price − stop_price)` |
| `target_price` | `entry ± 5 × r_distance` (frozen `tgtR = 5.0`). V53 emits no target price |
| `point_value_usd` | MGC 10, MNQ 2 — derived from the ledger and verified on every stop and target exit |
| `stop_inverted` | stop on the near side of entry for the direction |
| `checks.pnl_reconciled` | true when recorded P&L equals the arithmetic (all stop and target exits; false for the 5 timeouts, which record no exit price) |
| `checks.r_reconciled` | `pnl_usd / (r_distance × point_value)` equals `r_multiple` — true for all 58 |

`stop_inverted` is true for exactly two fills. It is a **real recorded V53
outcome**, not an error: the FVG far edge can sit beyond the sweep extreme.
B2 must reproduce it, not correct it.

**`event_keys`** — the Phase 13G clustering identities, pipe-joined:

- `primary` — instrument, direction, ltf, CHOCH ts + level, BOS ts + level, entry ts + price (9 parts)
- `alternative` — the same without the CHOCH pair (7 parts)

These are **analysis** identities. They are not execution idempotency keys — see
`BOT_IMPLEMENTATION_AUDIT.md` §8.

## What is deliberately absent

The source records one row per **fill**. They contain no per-event record of
pivot confirmation, displacement qualification, slot index, non-filling
sequences, per-bar transitions, timeout exit prices, or ATR at arm. Those are in
every fixture's `not_captured` list. Recovering them would require re-running or
re-implementing V53; the first is forbidden and the second is exactly what these
fixtures exist to verify. See `bot/A2_FIXTURE_AUDIT.md` §4.

## Regenerating

```
python3 bot/tools/extract_golden.py            # rewrite fixtures
python3 bot/tools/extract_golden.py --check    # verify on-disk == fresh extraction
python3 -m unittest discover -s bot/tests -t .
```

Extraction is deterministic: sorted keys, two-space indent, exact decimal text,
no wall-clock, no random ids, no absolute paths. Running it twice is
byte-identical, and CI asserts it.

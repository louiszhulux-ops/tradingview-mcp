# A2 — Golden fixture extraction: audit

Roadmap task A2. **No research artifact was modified, no strategy was run, no
TradingView connection was made, and no Phase 16 or post-FE data was inspected
or consumed.**

Date: 2026-09-06. Preceded by A1 (`ade51b3`).

---

## 1. What was built

| artifact | what it is |
|---|---|
| `bot/fixtures/golden/*.json` | 24 fixtures + `manifest.json` — the expected results |
| `bot/fixtures/loader.py` | the only supported read path; re-guards every timestamp |
| `bot/fixtures/SCHEMA.md` | the format |
| `bot/tools/extract_golden.py` | deterministic extractor, also `--check` |
| `bot/tests/test_golden_fixtures.py` | 38 validation tests |

---

## 2. The matrix

The roadmap's "24 fixtures (8 cells × 3 folds)" resolves against the source
material exactly, with no ambiguity and nothing invented: the committed run
records are 16 files in `trader_v2/v53_runs/` (folds A and B) and 8 in
`trader_v2/v53_runs_foldc/` (fold C) — one per
`instrument × direction × LTF × fold`.

| | 1m A | 1m B | 1m C | 3m A | 3m B | 3m C |
|---|---|---|---|---|---|---|
| **MGC long** | 2 | 1 | 1 | 5 | 0 | 0 |
| **MGC short** | 2 | 2 | 4 | 1 | 0 | 0 |
| **MNQ long** | 2 | 7 | 2 | 1 | 0 | 0 |
| **MNQ short** | 10 | 2 | 6 | 3 | 2 | 5 |

Cell values are fill counts. 24 fixtures, 58 fills, 18 cells with fills and
6 zero-fill cells. Zero-fill cells are kept: a cell that must produce *no* trade
is as much a test of B2 as one that must produce five.

---

## 3. Source artifacts

**Extracted from** (read-only, unmodified — hashes recorded in every fixture):

- `trader_v2/v53_runs/{MGC,MNQ}_{L,S}_{1m,3m}_{A,B}.txt` — 16 files, Phase 13F
- `trader_v2/v53_runs_foldc/{MGC,MNQ}_{L,S}_{1m,3m}_C.txt` — 8 files, Phase 14

**Cross-checked against** (read, never extracted — independent records):

- `trader_v2/p15/POOLED_DESIGN_VERIFICATION.md` — 58 fills / 9 wins total
- `trader_v2/p15/runs/BASE_pooled.txt` — per-cell pooled A+B+C run
- `trader_v2/v53_runs/PHASE13G_raw_output.txt` — folds A+B: 40 fills / 6 wins
- `trader_v2/v53_runs_foldc/PHASE14_raw_output.txt` — fold C: 18 fills / 3 wins

**Field decoding** follows `trader_v2/g_cluster.py`, the Phase 13G reference
parser. That script is untouched and remains the reference; the extractor
reproduces its control totals rather than replacing it.

**Deliberately not used:** `trader_v2/p15/runs/{A,B,C1,D1,E1,F1,G1}_*` — those
are Phase 15 *experimental arms*, i.e. modified strategies. They are not V53 and
must never become golden expectations for V53. Only the `BASE_pooled.txt`
baseline was read, and only as a cross-check.

---

## 4. What the fixtures can and cannot pin — read this before writing B3

The request asked for twelve checkpoint types. Nine are present. **Three are not
in the source material at all**, and no amount of extraction effort will produce
them:

| # | checkpoint | status |
|---|---|---|
| 1 | sweep detection | ✅ ts, kind, extreme |
| 2 | **pivot confirmation** | ❌ never emitted per event |
| 3 | CHOCH selection | ✅ ts, level |
| 4 | CHOCH retest | ✅ ts |
| 5 | BOS candidate/reference | ✅ ts, level |
| 6 | **displacement qualification** | ❌ aggregate `bos_displacement` counter only |
| 7 | associated FVG | ✅ low, high |
| 8 | entry/fill | ✅ ts, price |
| 9 | stop | ✅ price |
| 10 | target | ⚠️ derived (`entry ± 5R`), cross-validated, **not recorded** |
| 11 | **sequence state / slot identity** | ❌ slot index never emitted; Phase 13G event keys substituted |
| 12 | final outcome | ✅ outcome, R, USD, reason, bars |

Also absent: every sequence that armed but never filled (only aggregate funnel
counters), per-bar state transitions, exit prices for the 5 timeout exits, and
ATR at arm — so `r_atr_ratio` cannot be checked per fill.

**Why this is not fixable.** V53's ledger emits one row per fill, at fill time.
Recovering per-bar or per-sequence state would require re-running V53 (forbidden:
no new research runs, no TradingView) or re-implementing it to generate the
expectations (forbidden, and self-defeating — an unverified second implementation
cannot be the oracle for the implementation it is meant to verify). **This is
reported as a dependency, not worked around.** Every fixture carries the gap in
its `not_captured` field so B3 cannot assume coverage it does not have.

**Consequence for B3.** Gate 1 can assert, exactly and per cell: all 17 funnel
counters, all-zero assertions, the conservation identity, and every field of
every fill. It **cannot** assert intermediate state for non-filling sequences.
That is a real weakening of Gate 1 versus what the roadmap implied, and it should
be stated in the B3 report rather than discovered later. The mitigation available
without new research runs is B4's property tests plus the aggregate counters,
which do constrain the non-filling paths in total even though not individually.

---

## 5. Integrity findings

**Every fill reconciles arithmetically.** For all 58 fills, recorded
`r_multiple` equals `pnl_usd / (|entry − stop| × point_value)`. For all 53 stop
and target exits, recorded `pnl_usd` equals the arithmetic to the cent. The
5 timeout exits record no exit price and are unreconcilable by construction.

This also **derives and verifies the contract point values** — MGC $10/point,
MNQ $2/point, `costUSD` $3.00 per round trip — from the committed ledger rather
than from an assumption. A wrong value fails extraction.

**Two fills carry a stop on the near side of entry** (`v53-MNQ-S-1m-A`
2026-05-29 19:25 and `v53-MNQ-S-1m-B` 2026-07-20 12:30): short entries whose FVG
far edge sits above the sweep extreme, so the stop lands below the entry. The
P&L still reconciles, because V53 computes `r = |E − stp|` regardless of side.
This is **a real recorded property of the frozen strategy, flagged and preserved**
— `derived.stop_inverted`. A B2 that "fixes" the sign will fail Gate 1, correctly.

**No cell is truncated.** The roadmap flagged the Pine 40-row ledger cap (R8) as
a risk. The largest cell has 10 fills, so the cap never bit and all 24 fixtures
are eligible for strict row-for-row parity. The truncation flag and its detection
logic remain in place for future extractions.

**Provenance is honest about its limit.** The canonical `V53_ltf_sequence.pine`
never executed. The executed build `2dafbafd…` is attributed by reproduction —
it reproduced the committed Phase 13F/14 per-cell results exactly under pooled
packaging — not by a contemporaneous hash capture, because none was taken at
Phase 13F/14 run time. Every fixture says so in `provenance.attribution_note`.

---

## 6. Validation results

All 11 required checks, as automated tests:

| # | check | result |
|---|---|---|
| 1 | all expected fixtures exist | PASS — 24 + manifest |
| 2 | schema valid | PASS — keys, types, prices as strings |
| 3 | all timestamps pass `assert_pre_fe()` | PASS — 338 timestamps |
| 4 | no post-FE data | PASS — max timestamp 2026-08-30 23:55 UTC, FE is 2026-08-31 00:00 |
| 5 | no Phase 16 reference | PASS — regex scan of all 25 files |
| 6 | matrix coverage | PASS — 2×2×2×3, each exactly once |
| 7 | ids unique | PASS |
| 8 | ordering deterministic | PASS — manifest order, dense fill indices, sorted JSON keys |
| 9 | extraction reproducible | PASS — two extractions byte-identical; on-disk matches fresh |
| 10 | provenance valid | PASS — 11 required fields, sha256 format, artifacts hash-verified |
| 11 | sources unmodified | PASS — every recorded `source_sha256` matches the file today |

Plus cross-checks against the independent research records: 58/9 total, 40/6 for
A+B, 18/3 for C, and all 7 counters on all 8 cells versus the pooled baseline
run.

---

## 7. Scope discipline

Not done, deliberately: no B1 bar model, no B2 strategy code, no B3 harness, no
execution, no risk, no paper trading. The extractor contains **no strategy
logic** — it parses recorded text and does documented arithmetic on recorded
fields. It never detects a sweep, selects a CHOCH, qualifies a displacement, or
decides an outcome.

Unchanged: `V53_ltf_sequence.pine` `7490766b…`,
`p15/executed/V53_EXECUTED_BUILD.pine` `2dafbafd…`,
`p16/executed/V53_P16_OOS_BUILD.pine` `5c21acfa…`, and every file under
`trader_v2/`, `trader/`, `strategies/` and `src/`.

# B2 — Python V53 implementation: audit

Deterministic Python reproduction of `trader_v2/p15/executed/V53_EXECUTED_BUILD.pine`
(sha256 `2dafbafd…`), the Phase 15 provenance anchor.

**No V53 or Phase 16 artifact was modified, no TradingView connection was made,
no market data was fetched, and no post-FE data was inspected or consumed.**
B3 has not been started.

Date: 2026-09-06. Preceded by A1 `ade51b3`, A2 `acdb8e1`, B1 `649cd17`, U1 `c308dea`.

---

## 1. Pine → Python map

Audit line by line against the artifact using this table.

| Pine section (line) | Python | Notes |
|---|---|---|
| inputs, "Frozen" group (11–27) | `v53/constants.py` | all 12 frozen values + `SP`, `RB`, ATR length |
| `FB`/`FC`/`FE`, `inFold` (29–32) | `v53/engine.py::in_fold` | evaluated on the bar **open**, as Pine's `time` is |
| `atr = ta.atr(14)` (34) | `v53/indicators.py::WilderAtr` | RMA seeded by SMA of the first 14 TRs |
| 5m SWEEP ENGINE (39–92) | `v53/levels.py::SweepEngine` | PDH/PDL, Asia, swings, sweep test |
| ├ `newD = ta.change(time("D"))` (42) | `bot.calendar.is_trade_date_roll` | **exchange session**, U1 |
| ├ `hUTC`, `inAsia` (57–58) | `levels.py::utc_hour` | **UTC**, deliberately not the session |
| ├ `ta.pivothigh/low(_, swLen, swLen)` (70–71) | `indicators.py::PivotDetector` | confirms `swLen` bars late |
| └ `hitPD`/`hitAS`/`hitSW` (79–92) | `SweepEngine.update` | wick ≥ `minWick × ATR`, close back inside |
| LTF STREAM, ring, pivot register (94–116) | `v53/ltf.py::LtfState` | 7-slot ring, 4-entry register, `ltfN` |
| SEQUENCE SLOTS (118–150) | `v53/sequence.py::Slot` | all 16 strategy + 10 ledger fields |
| `K` counters (162) | `sequence.py::Counters` | same indices, named views on top |
| §1 OUTCOME LOOP (172–252) | `SequenceMachine.section1_outcomes` | adverse first; `b = bIn + 1` |
| §2 FVG RETEST / FILL (255–285) | `SequenceMachine.section2_fills` | touch ⇒ fill; R band; `retBars` |
| §3 DEADLINE (287–296) | `SequenceMachine.section3_deadline` | `bar_index − swB > dispWait` |
| §4 LTF LOOP (297–470) | `V53Engine.on_bar` + `section4_advance` | see below |
| ├ 4a pivot confirmation (336–370) | `LtfState.confirm_pivots` | tie rule transcribed |
| ├ 4b `s == 1` CHOCH (383–406) | `section4_advance` | `oB > swB`; break on close |
| ├ 4b `s == 2` retest (407–418) | `section4_advance` | exact level, zero tolerance |
| ├ 4b `s == 3` BOS (419–443) | `section4_advance` | excludes the CHOCH pivot; displacement |
| └ 4b `s == 4` FVG (444–470) | `section4_advance` | single test at `dBar + 1` |
| §5 ARM NEW SWEEPS (473–505) | `SequenceMachine.section5_arm` | lowest free slot; `stp`, `aRf` |
| §6 DETECTOR VERIFICATION (508–537) | — | K26/K27; not reproduced, see §6 below |
| §7 OUTPUT ledger row (222–247) | `v53/ledger.py::ledger_row` | 21 fields, `str.tostring` semantics |

---

## 2. State variables

`Slot` carries every V53 parallel array under a readable name, with the Pine
name in a trailing comment: `st`, `swB`, `stp`, `aRf`, `cLvl`, `pRef`, `cPvI`,
`cBar`, `rBar`, `dBar`, `ent`, `rr`, `wt`, `bIn`, `mfe`, `mae`, `flg`, plus the
ten `l*` ledger fields. Nothing was collapsed for looking redundant.

Engine-level state: `SweepEngine` (10 fields + ATR + pivot detector),
`LtfState` (7-slot ring, 4-entry pivot register, `ltfN`), `Counters` (`K[36]`),
`bar_index`, `ledger`, coverage timestamps.

---

## 3. Timeframe ownership

| owned by | timeframe |
|---|---|
| sweep engine, ATR(14), 5m swing pivots | **5m** |
| §1 outcomes, §2 fills, §3 deadline, §5 arming | **5m** |
| ring buffer, LTF pivots, CHOCH, retest, BOS, FVG | **1m or 3m** |

`ParentBar` keeps the boundary explicit: one closed 5m bar plus the LTF
sub-bars it contains. The architecture is **not** collapsed to one timeframe —
`V53Engine.on_bar` consumes a 5m bar and iterates its sub-bars, which is the
`request.security_lower_tf` equivalent. A native 1m/3m chart implementation is
not possible through this interface: `ParentBar` refuses a non-5m parent.

---

## 4. Calendar ownership

**Two calendars, never merged** (`bot/U1_CME_SESSION_CALENDAR.md`):

| what | calendar | code |
|---|---|---|
| PDH/PDL roll | CME exchange-session trade date, 17:00 America/Chicago | `bot.calendar.is_trade_date_roll(prev_open, open)` |
| Asia H/L window | UTC, `hour < 7` | `levels.utc_hour` |

First bar: `is_trade_date_roll(None, ts)` returns `False`, mirroring Pine's
`ta.change` being `na` on bar 0. Tests assert both directions — that a session
roll fires PDH/PDL and that UTC midnight inside a session does **not**.

---

## 5. Causal ordering

`SECTION_ORDER = ("outcomes", "fills", "deadline", "ltf_loop", "arm")`, asserted
by test. Two consequences are load-bearing and separately tested:

1. **§1 before §2** — a fill on bar *t* is first judged on *t+1*. A bar that
   both fills and reaches the stop does **not** stop out.
2. **§5 after §4** — a sequence armed on bar *t* is not served by bar *t*'s own
   LTF sub-bars.

Also preserved: `nLive` is snapshotted **before** the LTF loop and never
recomputed inside it; every section walks slots in index order, since slot order
decides which slot wins a contested transition; `mfe` updates only on the branch
where the adverse excursion is below 1.0R, so it is not updated on the bar that
stops out.

---

## 6. Deliberate faithfulness — things that look wrong and are not

- **Touch ⇒ fill.** §2 fills on `low <= E`. Optimistic, reproduced, not fixed.
- **The fill bar is never judged.** `bIn = 0` at fill, `b = bIn + 1` in §1.
  Structural optimism; `K25` is 0 *by construction*, not by validation.
- **A stop can sit on the near side of entry.** The FVG far edge can lie beyond
  the sweep extreme. `r = |E − stp|` regardless. Two recorded fills do this and
  both reproduce exactly.
- **A timeout is a LOSS**, even if price ended above entry: `won = flg >= 1`.
- **Adverse before favourable.** A bar reaching both resolves as a stop.
- **`dispWait` counts chart bars**, not minutes — across a weekend, 12 bars
  spans two days.
- **Displacement compares an LTF bar range against the 5m ATR.**
- **An AS sweep cannot fire inside the Asia window.** The running Asia low is
  updated before the sweep test, so `low < asiaL − minWick × atr` can never hold
  while the window is open. AS sweeps only occur once it closes. Confirmed as
  V53's own behaviour and covered by a test.
- **`float64`, not `Decimal`.** V53 computes in float64; `Decimal` would give
  different results at `rng > dispMin * atr`, `ratio >= minRatr` and
  `adv >= 1.0`. B1's contracts keep `Decimal` for *recorded* values; the engine
  converts at its edges and formats output through the Pine formatter.

---

## 7. Discrepancies found

**The artifact's pivot comment contradicts its own code.** V53 §4a says:

> `ta.pivothigh/low` is NON-STRICT on the left and STRICT on the right: the
> FIRST of a run of equal extremes is the pivot.

The code rejects an older neighbour only when it is *strictly greater*
(equality allowed) and a newer neighbour when it is *greater or equal*
(equality rejects). A member of a run therefore qualifies only if nothing
equal-or-higher follows it — i.e. the **most recent** member, not the first.
§6's own verification block uses the same comparison in `high[j]` indexing, so
both blocks agree with each other and disagree with the prose.

**Resolution: the code is authoritative.** It was verified against
`ta.pivothigh(src, 3, 3)` with 0 mismatches over 20,567 chart bars, and the
K26/K27 detector-verification counters read 0 in every committed run. This
implementation transcribes the code. Four tests pin the behaviour, including two
that show a strict-both-sides and a non-strict-both-sides rule each disagreeing.

The prose is a documentation defect in a frozen artifact, so it is **recorded,
not corrected** — the file is not modified.

---

## 8. Limitations

**The engine cannot be fixture-validated end to end in this repository.** The
A2 fixtures record *results*, not bars, and the repo contains no OHLCV. Full
funnel and ledger parity across the 24 cells needs 5m + 1m/3m bars for MGC1! and
MNQ1! over folds A/B/C, which must not be fetched here. **That is B3's
dependency, and it is a real blocker for Gate 1**, not a gap in B2.

What was validated against the fixtures is the layer that does not need bars:
driving the real §1 loop with each recorded entry, stop and exit reason
reproduces **all 58 ledger rows exactly, character for character** — R multiple,
USD, WIN/LOSS, exit reason, bar count, and every price through
`str.tostring(x, "#.####")`.

Not reproduced: §6 (detector verification, K26/K27) — it exists to compare V53's
hand-rolled pivot against Pine's built-in, and there is no built-in here. K26/K27
therefore stay 0 and are reported as not-applicable rather than as passing.

Carried forward from `bot/contracts/UNRESOLVED.md`: **U2** (LTF timestamp
fallback — reproduced as given), **U3** (3m per-parent alignment — the engine
consumes whatever sub-bars it is handed and never assumes a count), **U4**
(`point_value` is required and explicit; the silent 1.0 fallback is refused),
**U5** (ATR warmup — implemented as Wilder RMA seeded by SMA; only B3 can
confirm it against Pine).

---

## 9. Test coverage

**275 tests pass** (69 B2 + 206 earlier). B2 breakdown, all stdlib `unittest`:

| area | tests |
|---|---|
| ATR warmup, seeding, Wilder smoothing | 4 |
| pivot tie convention + rejected variants | 6 |
| pivot confirmation timing (LTF and 5m) | 3 |
| sweep detection, wick depth, close-inside, both directions | 6 |
| the two calendars, kept separate | 5 |
| instrument abstraction, explicit point value | 3 |
| CHOCH selection and retest semantics | 4 |
| displacement thresholds and close-location clause | 3 |
| FVG creation, association, invalidation, conservation | 4 |
| entry, stop, fill, R band, retest expiry | 5 |
| outcome: next-bar start, target, stop, adverse-first, timeout | 6 |
| section ordering, slots/ring, deadline, assertions, bar order | 6 |
| fold gate | 3 |
| determinism and isolation | 3 |
| **A2: all 58 recorded ledger rows** | 7 |

---

## 10. Determinism

No wall clock, no randomness, no network, no I/O in the decision path, no
module-level mutable state. Everything is explicit config: bars, timestamps,
timeframe, instrument, point value, cost, fold. Two identical runs produce
identical ledgers, funnels and counter arrays; a fresh engine starts from a
zeroed state. All three are asserted.

---

## 11. Not implemented, by scope

B3 parity harness, live execution, broker API, TradingView connection, order
placement, risk sizing, persistence/rehydration, paper trading, optimisation,
parameter search, strategy improvements, Phase 16 validation.

# Gate 1 acceptance model — the repaired B3

**Status: NON-FROZEN operator document.** Amendable by a normal change with a
dated note. It modifies no frozen artifact; the eight frozen hashes are
untouched by everything described here.

Date: 2026-09-13. Implements the nine-item repair set from the B3 Specification
Repair Audit, which closes defects D1–D5 found by the B3 Feasibility Audit.

**This document is prose. `bot/replay/verdicts.py` is the only executable
definition, and the two must agree.** Where they disagree, that is a bug in one
of them, not a licence to choose.

---

## 0. What this repairs, and why it was broken

B3 as originally written could not be adjudicated. Five defects:

| id | defect |
|---|---|
| **D1** | Criterion 2 demanded exact parity on `target`, `MFE` and `MAE` — three values V53 never emitted. |
| **D2** | Criterion 6's only downgrade was for source truncation, and no cell is truncated, so the clause was inert. |
| **D3** | 12 of 24 cells have no input dataset at all, and the gate had no state for that. |
| **D4** | B1 assumed the exact series V53 consumed is recoverable. For 1m fold A it is permanently not. |
| **D5** | Criterion 3 required `K26`/`K27` to read 0, but those counters have no Python analogue at all. |

The root cause under all five: **B3 had two verdicts for a situation with at
least seven states**, and it could not distinguish a defect in the engine from a
hole in the data. A gate that cannot tell those apart either slanders a correct
engine or launders a real divergence into a pass.

---

## 1. Dataset provenance — a mandatory gate input

Every cell declares, before it runs:

| field | meaning |
|---|---|
| `cell_id` | e.g. `v53-MNQ-S-1m-B` |
| `instrument` | `MGC1!` / `MNQ1!` |
| `fold` | `A` / `B` / `C` |
| `ltf_timeframe` | `1m` / `3m` |
| dataset file paths | every required input series, repo-relative |
| `sha256` per file | the recorded hash, re-verifiable against disk |
| manifest `status` | `AUTHORITATIVE` or `CANDIDATE` |
| capture/provenance | how the series was obtained |

**The loader reads status. It never manufactures one and never upgrades one.**
`bot/replay/datasets.py::parse_status` is deliberately asymmetric:

* `AUTHORITATIVE` is accepted only from the bare, unqualified token. A qualifier
  can only weaken a claim, so `AUTHORITATIVE -- pending` is refused, not trimmed.
* `CANDIDATE` is accepted from any string whose first token is `CANDIDATE`,
  because recognising it can only ever *downgrade* a cell's weight.
* Anything else raises. `PARTIAL` — the status the frozen 5m manifest carries —
  is **not** recognised: it describes that export's completeness, not a Gate 1
  status, and inferring one from it would be the exact silent upgrade this
  function exists to prevent.

There is no code path from an unrecognised status to a gate-passing verdict.

### 1.1 `AUTHORITATIVE` is an evidentiary standard, not proof of identity

A dataset is `AUTHORITATIVE` for a cell only when **all** of:

1. it reproduces that cell's fixture coverage counters exactly;
2. it is frozen, with a recorded hash and a manifest entry;
3. its provenance is a single non-paginated capture through the same mechanism
   V53 consumed.

State this plainly wherever the word is used:

> **Exact coverage-counter reproduction is necessary but not sufficient.**
> No historical LTF value artifact was ever recorded. The values V53 consumed in
> 2026 were never written down, so **absolute historical value identity cannot
> be proven for any dataset**, and `AUTHORITATIVE` never asserts it.
> **No future rerun may manufacture that missing ground truth.** A rerun today
> produces today's values; calling them history would be fabrication.

### 1.2 The P-9 candidate stays `CANDIDATE`

`data/phase_c_ltf/*.csv` reproduce the fixture coverage counters exactly for
folds B and C on both instruments, and provably fail fold A:

| | `fold_bars` | `fold_bars_with_ltf` expected | actual | |
|---|---|---|---|---|
| MGC 1m A | 10386 ✓ | 9813 | 9677 | short 136 |
| MGC 1m B | 4668 ✓ | 4668 | 4668 | exact |
| MGC 1m C | 4164 ✓ | 4164 | 4164 | exact |
| MNQ 1m A | 10368 ✓ | 9812 | 9675 | short 137 |
| MNQ 1m B | 4668 ✓ | 4668 | 4668 | exact |
| MNQ 1m C | 4164 ✓ | 4164 | 4164 | exact |

**The B/C match does not promote them.** Condition 1 of §1.1 is satisfied;
conditions 2 and 3 are a separate, human decision. The files and their manifest
are not to be edited to make a cell pass — that would be changing the evidence
to fit the verdict.

---

## 2. Cell verdicts

Seven states. Closed vocabulary. Exactly one per cell.

| verdict | condition | engine runs? | counts toward Gate 1 PASS? |
|---|---|---|---|
| `NO-DATA` | a required input series is absent | no | no |
| `PRECONDITION-FAIL` | inputs exist, coverage counters differ | **no** | no |
| `SOURCE-TRUNCATED` | A2 §5 source truncation, compared clean on counters | yes, counters only | **yes** |
| `PROVISIONAL-PASS` | clean comparison on `CANDIDATE` data | yes | no |
| `PROVISIONAL-FAIL` | divergence on `CANDIDATE` data | yes | no |
| `PASS` | clean comparison on `AUTHORITATIVE` data | yes | **yes** |
| `FAIL` | divergence on `AUTHORITATIVE` data | yes | no |

### 2.1 Precedence

```
NO-DATA → PRECONDITION-FAIL → SOURCE-TRUNCATED → PROVISIONAL / PASS / FAIL
```

A cell is classified at the earliest tier whose condition holds, so an absent
dataset is never reported as a strategy divergence, and a coverage shortfall
never reaches the engine at all.

Two refinements, **both of which tighten the gate and neither of which may be
relaxed**:

* **A divergence outranks truncation.** A2 §5 downgrades a truncated cell to
  counters-only comparison; it does not excuse a counter mismatch. Classifying
  truncation ahead of the comparison result would let a real divergence on a
  truncated cell be laundered into a gate-passing verdict.
* **Candidate status outranks truncation.** `SOURCE-TRUNCATED` counts toward a
  pass, so it is reachable only from an `AUTHORITATIVE` dataset. A truncated
  cell on candidate data is `PROVISIONAL-PASS`.

`decide_cell_verdict` implements exactly this, and `CellResult` refuses at
construction to hold a gate-passing verdict against a non-authoritative dataset.

### 2.2 `NO-DATA` is not a truncation downgrade

Truncation means **the source recorded a capped subset of a run that happened**
(the Pine ledger table caps at 40 rows; A2 §5). No-data means **the run cannot
be attempted at all**. They are not degrees of the same thing, and the
counters-only comparison that is lawful for the first is meaningless for the
second: there is nothing to count.

All 24 fixtures carry `fills_truncated_at_source = false` — the largest cell has
10 fills — so `SOURCE-TRUNCATED` is currently unreachable. The clause is
retained anyway, correct and inert, so that it is never stretched to cover the
12 cells that have no 3m data.

---

## 3. Gate aggregation

> **Gate 1 = PASS if and only if all 24 cells are `PASS` or `SOURCE-TRUNCATED`.**

No other combination passes, under any argument, in any report. A short census
cannot pass either: a cell that was never evaluated is *missing* evidence, not
*satisfied* evidence.

Otherwise, exactly one of:

| result | when |
|---|---|
| `GATE 1: FAIL` | any cell is `FAIL` — the engine diverged on authoritative data |
| `GATE 1: NOT ADJUDICABLE — DIVERGENCE ON CANDIDATE DATA` | any cell is `PROVISIONAL-FAIL` (and none is `FAIL`) |
| `GATE 1: NOT ADJUDICABLE — INSUFFICIENT EVIDENCE` | no failures, but not every cell reached a passing verdict |

`FAIL` outranks `PROVISIONAL-FAIL`, which outranks insufficiency. A
`PROVISIONAL-FAIL` names no defendant — engine or data, unknown — so it is a
loud state requiring a written disposition naming the first divergent bar and
slot. **It may not be closed by re-running.**

### 3.1 Partial validation unblocks nothing

The roadmap rule at `BOT_IMPLEMENTATION_ROADMAP.md:166` stands unchanged:

> Nothing in Phase C, D, E or F may consume strategy output until B3 passes.

"Passes" means `GATE 1: PASS` as defined above. A partial result is never a
pass, is never described as "Gate 1 passed for the cells we could run", and
never unblocks a downstream phase. This holds in reports, commit messages and
conversation alike.

The full strategy/parity proof remains **one coupled correctness artifact with
one verdict** (`PRODUCTION_READINESS_AUDIT.md:706`). The repair adds resolution
*inside* the report — you can now see which cells are blocked and why — without
creating a second, weaker gate that anything downstream could cite.

---

## 4. What is compared

### 4.1 Behaviour counters — parity, zero tolerance (14)

`sweeps`, `choch`, `retests`, `bos_displacement`, `break_no_displacement`,
`fvg`, `no_fvg`, `fills`, `r_band_rejects`, `fvg_retest_expiry`,
`expire_pre_choch`, `expire_post_choch`, `expire_post_retest`,
`dropped_no_slot`.

### 4.2 Coverage counters — precondition, not parity (2)

`fold_bars`, `fold_bars_with_ltf`. Computed by the loader **before the engine
runs**. On mismatch the cell is `PRECONDITION-FAIL`, the engine is not started,
and the report names instrument, fold, timeframe, expected and actual values for
both counters, and the first differing parent timestamp where determinable.

No reconstruction from a higher timeframe. No interpolation. No synthetic bars.
No external substitution.

### 4.3 Excluded — informational (1)

`ltf_bars` (K31) is counted chart-wide rather than in-fold, and is null in most
fixtures. Reported with its reason, never compared.

### 4.4 Ledger — the 18 fields V53 emitted

`sweep_ts`, `sweep_kind`, `sweep_extreme`, `choch_ts`, `choch_level`,
`retest_ts`, `bos_ts`, `bos_level`, `fvg_low`, `fvg_high`, `entry_ts`,
`entry_price`, `stop_price`, `outcome`, `r_multiple`, `pnl_usd`, `exit_reason`,
`bars_in_trade`.

Row count exact. Row order exact. Exact `Decimal` equality on prices; a float on
either side is refused outright rather than compared. A missing row and an extra
row are each a failure. The first divergent row and field are named.

### 4.5 Assertion counters

`K21`, `K22`, `K23`, `K24`, `K25`, `K32` must read **0**; non-zero is a failure.

`K26` and `K27` are reported **`NOT APPLICABLE`**, never as a passing zero.
V53 §6 exists solely to cross-check its hand-rolled pivot against Pine's
`ta.pivothigh` / `ta.pivotlow`. Python has no built-in comparand, so the check
has no analogue here (`bot/B2_V53_IMPLEMENTATION_AUDIT.md:171-174`).
**A structurally absent check is not a passing check**, and K26/K27 contribute
nothing to any verdict in either direction.

### 4.6 Derived diagnostics — `DERIVED — NO GOLDEN COMPARAND`

`target_price`, `MFE`, `MAE`.

The engine computes all three and serialises them into the Gate 1 report under
that label. **They are excluded from parity and may never be added to it.**

V53 maintains `mfe`/`mae` internally (`V53_ltf_sequence.pine:140-141, 199-208`)
and emits neither; it emits no target price either
(`bot/fixtures/SCHEMA.md:86`). No golden comparand exists. Recomputing them from
the 5m bars and comparing to our own recomputation would test the engine against
itself, and a fresh run would manufacture a comparand and call it history.
Neither is permitted.

A determinism baseline over these values — run-to-run byte equality — is an
**implementation regression guard on our own code**. It is not historical
TradingView parity, may never be cited as such, and no Gate 1 verdict may depend
on it.

Exit price for timeout exits is likewise never compared: the source recorded
none (five such rows across the 58).

---

## 5. Implementation map

| concern | module |
|---|---|
| verdicts, precedence, aggregation | `bot/replay/verdicts.py` |
| dataset status and provenance | `bot/replay/datasets.py` |
| coverage precondition | `bot/replay/coverage.py` |
| comparator | `bot/replay/compare.py` |
| optional bar fields | `bot/data/bars.py` |
| incomplete-bar rejection | `bot/strategy/v53/engine.py` |

Not built, deliberately: the harness that would drive the engine over real
cells. Building the judge is in scope; running Gate 1 is not.

---

## 6. Standing today

Gate 1 has **not** been run and no cell has been adjudicated. On the evidence
currently in the repository, a run would return:

```
GATE 1: NOT ADJUDICABLE — INSUFFICIENT EVIDENCE
  NO-DATA             12   all 3m cells; no 3m series exists in the repository
  PRECONDITION-FAIL    4   1m fold A; 9677/9813 (MGC), 9675/9812 (MNQ)
  PROVISIONAL          8   1m folds B/C; coverage exact, dataset status CANDIDATE
  PASS                 0
  FAIL                 0
```

That is the correct outcome, not a setback. It is also a projection from
coverage arithmetic and dataset status — **not a result**, because the engine
has not been run against any cell.

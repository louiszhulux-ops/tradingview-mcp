# Phase 11 C3 — session-phase viability audit

Audit only. **No expectancy, win rate, PF or backtest was computed. Fold C not
touched.** All counts below come from ledgers already produced in earlier runs.

---

## 1. Evidence audit

**One artefact of seven mentions session at all.**

| artefact | mentions London / GB |
|---|---|
| `MANUAL_PROCESS_ANALYSIS.md` | **yes — 4** |
| `LOSS_NOTE_ANALYSIS.md` | no |
| `TRADE_VERIFICATION_AUG31.md` | no |
| `TRADE_VERIFICATION_TWO_TRADES.md` | no |
| `HUMAN_RECONSTRUCTION.md` | no |
| `HUMAN_TRADE_REGISTER.md` | no |
| `alert_history.json` | no |

What it actually says — the entire evidence base, one table row:

> | Execution at/after **London open** | "GB had another big sell-off" | "Coming into the GB open" | "By the time GB opened" | yes |

**Is the evidence consistent about a phase?** Yes — all three narratives place
execution at or after the London open.

**Does it establish session as a decision variable?** **No.** Every one of the
three quotes is a *description of when the trade happened*. None says the trader
chose London because it is better, none compares London to another session, and
none rejects a setup for occurring outside it. This is exactly the inference the
audit brief warns against: three trades occurring during London does not make
London a cause.

A material counterweight sits in the same document. Its ablation of the encodable
scaffolding lists the **London window as one of only two binding constraints**,
and the configuration containing it returned:

| configuration | trades | win% | PF | net |
|---|---|---|---|---|
| full process (bias + Asia + **London** + 2nd touch) | 30 | 50.0% | **0.756** | **−$1,020** |

The London window's *marginal* contribution was never isolated — there is no
"− London" row — so this is not a clean negative on session itself. But the one
document that supplies all the positive evidence also reports that the process
containing it lost money.

## 2. Prior session research audit

### V37 — session conditioner (`V37_RESULTS.md`)

- **What was tested:** does the UTC session block condition expectancy? Six
  4-hour blocks, pre-registered as conditioner C1 before looking.
- **Definition:** 0–4, 4–8, 8–12, 12–16, 16–20, 20–24 UTC.
- **Population:** MGC 5m, fade/level family, n = 244–354 per block, fills at the
  next bar's open with a $4.40 drag, split into **three walk-forward folds**.
- **Result:**

| session | n | fold 1 | fold 2 | fold 3 | ALL |
|---|---|---|---|---|---|
| 0–4 UTC | 352 | +0.272 | +0.036 | −0.012 | +0.094 |
| 4–8 | 343 | +0.051 | −0.136 | −0.170 | −0.094 |
| **8–12 (London)** | 333 | +0.090 | +0.120 | **−0.062** | +0.050 |
| **12–16 (overlap)** | 354 | +0.057 | +0.299 | **−0.061** | +0.084 |
| **16–20 (NY)** | 252 | +0.535 | +0.161 | **−0.174** | +0.154 |
| 20–24 | 244 | −0.239 | −0.109 | −0.034 | −0.120 |

> **"Every cell negative in the most recent third."**

Session did **not** reach V37's cross-market survivor table. The variable that
did was **volatility > 1.5**, which held 3/3 folds on MGC *and* 3/3 on MNQ.

- **Classification: SAME HYPOTHESIS**, different binning (six 4-hour blocks vs
  five named bands) and a different setup family (V33/V35 fade vs the V49 sweep
  engine). The question asked — *does UTC session phase condition expectancy of
  a level-interaction setup on the same instruments and timeframe* — is the same
  question C3 asks, and it was tested with walk-forward validation that the
  planned C3 test would not exceed.

### V11.1 — `sessMult` session filter (`AUDIT_REPORT.md`)

- **What was tested:** a binary in/out of 07:00–16:00 UTC used to **halve
  position size**, not to condition expectancy.
- **Result:** trades **outside** 07:00–16:00 scored **+0.293** against **+0.242**
  inside — the filter ran backwards, and the direction is opposite to what the
  human narrative would imply.
- **Contamination:** that population is the 232 of 420 signals admitted by the
  zero-leverage margin bug, i.e. a bug-selected subset. The number cannot be
  taken at face value.
- **Classification: RELATED HYPOTHESIS.** Same variable, different use (sizing,
  not conditioning), on a compromised population. Weak evidence either way, but
  it points against the narrative rather than for it.

### `MANUAL_PROCESS_ANALYSIS.md` — London as an entry gate

- **Classification: RELATED HYPOTHESIS.** London inside a multi-condition
  process, never isolated. PF 0.756 on 30 trades.

**No prior test is dismissed for being imperfect.** V11.1 is discounted for a
specific, documented contamination; V37 is not discounted at all.

## 3. Distinctness audit

The stated concern — that session is a proxy for volatility or liquidity — is
not hypothetical here. **V37 ran session and volatility as competing
pre-registered conditioners on the same population, and volatility survived
cross-market while session did not.** That is direct evidence that on this family
the volatility variable already carries what session might have carried.

Relationship to variables already tested, from existing ledgers (counts only):

| variable | relationship to session | source |
|---|---|---|
| level maturity | **weak** — virgin share by session 34.6% / 39.0% / 36.5% / 39.4% / 44.2% | C2 confounding table |
| direction | weak — long 40.9% vs short 38.0% virgin share | C2 |
| ATR regime | weak on maturity — 38.2% vs 40.5% virgin share | C2 |
| **ATR level itself** | **not measured per session** | — |
| room, VWAP, 4H bias, sweep timing | not cross-tabbed against session | — |

**Gap:** ATR percentile by session has never been computed. The frozen C3 spec
requires exactly that control ("Report ATR percentile and candidate count per
session, or a 'session effect' is indistinguishable from a volatility effect").
It is a distribution, not a performance statistic, so it *could* be produced
without breaching this audit — but it has not been, and until it is, the
proxy concern is open rather than addressed.

## 4. Definition / leakage audit

| requirement | status |
|---|---|
| exact UTC boundaries | **specified** — Asia 22:00–07:00, London 07:00–12:00, Overlap 12:00–16:00, NY 16:00–20:00, Off 20:00–22:00 |
| exact freeze point | **specified** — "Known / frozen at the arm bar" |
| no lookahead | **specified and true** — the hour is known at bar open |
| known at arm time | **yes** |
| can the phase change after the candidate is created | **no** — a scalar read once at arm |
| sessions crossing midnight | **implied** by the 22:00–07:00 notation, not stated as a rule |
| **treatment of boundary bars** | **GAP** — the spec never says whether a bar's **open** or **close** time assigns its band. A 5m bar opening 06:55 UTC closes at 07:00 |
| **treatment of weekends / holidays** | **GAP** — not mentioned. Futures reopen Sunday ~22:00 UTC and close Friday ~21:00; the "Off 20:00–22:00" band straddles the Friday close |
| **treatment of missing / inactive periods** | **GAP** — the daily exchange halt (~21:00–22:00 UTC) is not addressed, and it falls inside the "Off" band |
| DST | **specified as a known imprecision**, explicitly not to be corrected by fitting |

Three gaps. Per the audit rules I have **not** filled them.

## 5. Sample adequacy

Counts already in the ledger (V52, folds A+B, ten cells, prev-day + pivot
population, n = 5,035). **No expectancy attached.**

| band | fills | per cell | fold C projection (~22%) |
|---|---|---|---|
| Asia | 1,895 | ~190 | ~42 |
| London | 1,151 | ~115 | ~25 |
| Overlap | 1,178 | ~118 | ~26 |
| NY | 679 | ~68 | ~15 |
| **Off** | **132** | **~13** | **~3** |

- **The "Off" band is not testable.** 13 fills per cell in A+B and ~3 in fold C.
  A ≥7/10 cell-consistency criterion cannot be meaningfully evaluated on it.
- **NY is marginal** at ~68 per cell.
- Pooled, London n = 1,151 against 3,884 elsewhere gives SE ≈ 0.075 on the
  difference, so the minimum detectable effect at 80% power is roughly **0.19R** —
  larger than the pre-registered detectable effect of the C1 test that already
  failed, and far larger than any effect this project has produced.
- The spec's "~1/5 each" expectation does not hold: the realised split is
  38 / 23 / 23 / 13 / 3 percent.

## 6. Decision

# **C — CLOSE C3**

## 7. Justification

Four independent reasons, any two of which would be sufficient:

1. **The evidence is descriptive, not causal, and it is one artefact of seven.**
   Three quotes recording *when* trades happened. No comparison, no rejection of
   a non-London setup, no statement that session drove selection. The brief's own
   warning covers this case exactly, and it is the entire positive evidence base.

2. **The same hypothesis has already been tested, more rigorously than the
   planned C3 test, and failed.** V37 pre-registered session as conditioner C1 on
   MGC 5m with realistic fills and three walk-forward folds, and found *every*
   session block negative in the most recent fold. Session did not reach the
   cross-market survivor table. A C3 run would be a lower-powered repeat of a
   test already conducted with walk-forward validation.

3. **The volatility-proxy concern is not merely plausible — it has been
   adjudicated.** In V37 session and volatility competed as pre-registered
   conditioners on the same population; **volatility survived cross-market,
   session did not.** The most likely outcome of C3 is measuring, at lower power,
   a variable already shown to lose to its own confound.

4. **The frozen definition has three unfilled gaps and one untestable band.**
   Boundary-bar convention, weekends/holidays and the exchange halt are all
   unspecified, and the "Off" band has ~13 fills per cell falling to ~3 in fold C.
   Under option B I would have to propose clarifications for all three — but
   fixing the definition does not touch reasons 1–3, which are the substantive
   ones.

**Why not B.** B is for a worthwhile hypothesis blocked by a fixable ambiguity.
The ambiguities here are fixable, but the hypothesis is not sufficiently
supported: fixing the boundary convention would not create causal evidence that
does not exist, nor unmake V37's walk-forward result.

**Why not A.** A requires the human evidence to be sufficiently specific, C3 to
be genuinely distinct from already-failed variables, and prior negative evidence
not to answer the same question. None of the three holds.

**What would reopen it.** New human evidence that treats session as a *selection*
criterion rather than a timestamp — e.g. a trade log showing setups declined for
occurring outside London, or the user stating that session is a filter they
apply. That is evidence only the user can supply; it cannot be mined from price
data or from the existing artefacts.

---

## Status after this audit

All three Phase 10 candidates are now resolved:

| candidate | outcome |
|---|---|
| C1 session VWAP | **CLOSED** — failed pre-registered gate; a seeded coin flip partitioned the same fills better |
| C2 level maturity | **CLOSED** — Gate A passed, Gate B failed both criteria (+0.0059R, CI [−0.101, +0.112], 6/10) |
| C3 session phase | **CLOSED** — viability audit; evidence descriptive, hypothesis already tested and failed in V37 |

The Phase 10 map's own top-ranked gap remains unaddressed and was excluded on
feasibility rather than merit: **LTF structure shift (1m/3m CHOCH → BOS)**, which
`MANUAL_PROCESS_ANALYSIS.md` names as *the* trigger and marks encodable: **no**,
because 1m data over a multi-month window exceeds TradingView's bar limit. That
is the largest known gap between the human process and anything the engine can
represent, and it is a data-access problem rather than a research-design one.

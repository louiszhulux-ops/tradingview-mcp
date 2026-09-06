# Phase 11 C2 Gate B — **FAIL**. C2 closed.

Pre-registered before any expectancy was computed: primary comparison
`E[R | virgin] − E[R | non-virgin]`, virgin = prior touches == 0, population =
prev-day and pivot levels only, Asia excluded on the Gate A construct-validity
finding. Folds A+B. Fold C never touched.

---

## 1. Primary population / reconciliation

| | |
|---|---|
| candidates | **7,454** (matches V49 / V50 / V51) |
| fills | **6,658** (matches) |
| Asia fills excluded | 1,623 |
| **primary population** | **5,035** — and 5,035 + 1,623 = 6,658 exactly |
| D0, pivot-lag diagnostics | 0 in every cell, re-verified in V52 |

Entry, exit, room, ATR, sweep detection, slot handling and candidate generation
all unchanged. Maturity remained an observational ledger attribute throughout.

## 2. Virgin vs non-virgin, pooled

| | n | E[R] | win% | PF |
|---|---|---|---|---|
| **virgin** | 1,994 | **−0.1173** | 17.0% | 1.02 |
| **non-virgin** | 3,041 | **−0.1232** | 16.8% | 1.01 |

| difference | SE | 90% CI | t |
|---|---|---|---|
| **+0.0059** | 0.0647 | **[−0.1006, +0.1124]** | **+0.09** |

The two populations are, to three decimal places, the same. A difference of
+0.006R on 5,035 fills is not a small effect — it is no effect.

## 3. Ten-cell results

| cell | n virgin | E virgin | n non-virgin | E non-virgin | diff | sign |
|---|---|---|---|---|---|---|
| MGC long | 244 | −0.0815 | 316 | −0.4170 | **+0.3356** | + |
| MGC short | 178 | −0.0745 | 284 | +0.0496 | −0.1241 | − |
| SIL long | 243 | −0.2456 | 357 | −0.1606 | −0.0850 | − |
| SIL short | 167 | +0.0727 | 256 | +0.2715 | −0.1988 | − |
| MNQ long | 224 | −0.0469 | 331 | −0.1501 | +0.1031 | + |
| MNQ short | 222 | −0.0796 | 416 | −0.0813 | +0.0017 | + |
| MCL long | 222 | −0.2550 | 348 | −0.2583 | +0.0034 | + |
| MCL short | 185 | −0.2662 | 258 | −0.3039 | +0.0377 | + |
| 6E long | 180 | +0.0467 | 253 | −0.0683 | +0.1151 | + |
| 6E short | 129 | −0.2134 | 222 | −0.0002 | −0.2132 | − |

**Virgin > non-virgin in 6/10 cells.** Three of the six "positive" cells are
+0.0017, +0.0034 and +0.0377 — indistinguishable from zero. The sign count is
carried by near-ties.

## 4. Level-type distributions (descriptive)

| level type | n | virgin | non-virgin | E virgin | E non-virgin | diff |
|---|---|---|---|---|---|---|
| prev-day | 1,278 | 257 (20.1%) | 1,021 (79.9%) | +0.0226 | −0.2219 | **+0.2444** |
| pivot | 3,757 | 1,737 (46.2%) | 2,020 (53.8%) | −0.1380 | −0.0733 | **−0.0646** |

The two level types point in **opposite directions**, and they cancel. This is
reported because the frozen spec required stratification by level type — not as
a rescue. The prev-day virgin cell is n = 257 across ten instrument × direction
cells, roughly 26 per cell, and the sign disagreement between types is exactly
what a null looks like when a population is split on something irrelevant.

**No subgroup is promoted to a result.** The pre-registered primary comparison is
the pooled one, and it failed.

## 5. Age distribution — `ageBars` deciles, primary population, descriptive only

| cell | d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 | d9 |
|---|---|---|---|---|---|---|---|---|---|
| MGC long | 5 | 9 | 12 | 16 | 21 | 25 | 35 | 52 | 128 |
| MGC short | 5 | 8 | 12 | 15 | 19 | 24 | 35 | 124 | 197 |
| SIL long | 5 | 9 | 14 | 18 | 25 | 33 | 43 | 70 | 153 |
| SIL short | 5 | 7 | 10 | 13 | 15 | 20 | 26 | 42 | 179 |
| MNQ long | 6 | 9 | 13 | 16 | 21 | 27 | 41 | 112 | 206 |
| MNQ short | 4 | 8 | 11 | 15 | 19 | 26 | 35 | 69 | 173 |
| MCL long | 5 | 8 | 12 | 16 | 22 | 29 | 38 | 86 | 183 |
| MCL short | 4 | 8 | 12 | 16 | 22 | 30 | 39 | 70 | 184 |
| 6E long | 5 | 8 | 11 | 14 | 18 | 24 | 33 | 50 | 162 |
| 6E short | 6 | 10 | 13 | 17 | 22 | 27 | 33 | 56 | 203 |

Median level age at arm is 15–25 bars (75–125 minutes). **No expectancy was
computed for any age bin**, per the instruction.

## 6. Asia diagnostic (excluded from the primary test)

Asia fills **1,623**, virgin **0**, virgin percentage **0.0%**.

Cause, established in Gate A: `asiaH`/`asiaL` are a *running* extreme, so
`bornBar` lands on the last bar that moved it and the remaining session bars
count as touches. The Asia touch counter measures the session's own formation,
not later interaction with an established level. Causal and leak-free, but a
different construct — excluded on that basis, pre-registered before any
expectancy was seen.

## 7. Confounding diagnostics (counts only)

| session | Asia | London | overlap | NY | off |
|---|---|---|---|---|---|
| virgin | 837 | 398 | 459 | 248 | 52 |
| non-virgin | 1,058 | 753 | 719 | 431 | 80 |
| **virgin share** | 44.2% | 34.6% | 39.0% | 36.5% | 39.4% |

| ATR regime | virgin | non-virgin | virgin share |
|---|---|---|---|
| above 200-bar mean | 931 | 1,504 | 38.2% |
| below 200-bar mean | 1,025 | 1,507 | 40.5% |

| | virgin share |
|---|---|
| prev-day levels | **20.1%** |
| pivot levels | **46.2%** |
| long cells | 40.9% |
| short cells | 38.0% |

Session, ATR regime and direction are all close to flat — virgin status is not a
disguised session or volatility variable. **Level type is a strong confound**
(20.1% vs 46.2%), which is why the spec mandated stratifying by it, and §4 shows
the stratification does not rescue anything.

## 8. Gate

| criterion | result |
|---|---|
| 1. pooled 90% CI excludes zero | **FAIL** — [−0.1006, +0.1124] |
| 2. same direction in ≥ 7/10 cells | **FAIL** — 6/10 |

### **GATE: FAIL — both criteria**

## 9. Exact next action

**C2 CLOSED — A+B performance failure.** Fold C is not run and was never
inspected.

No alternative maturity comparison will be tried: not age, not 2+ touches, not
level-type-specific thresholds, not Asia added back, not maturity combined with
anything else. Per the standing rule, a failed pre-registered result is not
rescued.

Phase 10's map leaves **C3 (session phase)** as the last unrun candidate. It was
ranked third and carries prior negative evidence — V11.1's session filter was
measured running backwards, and V37's session conditioning did not survive. The
confounding table above adds a fresh reason for pessimism: virgin share barely
moves across sessions, and neither did anything else this phase has tested.

Two of three Phase 10 candidates have now failed pre-registered gates on the same
candidate population. That is worth weighing before spending a run on the third.

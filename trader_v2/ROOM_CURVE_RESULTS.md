# Room-to-destination curve — measured

V48 run unchanged, folds A+B, **52.3 trading days**, ten instrument × direction
cells (MGC, SIL, MNQ, MCL, 6E long/short), **6,219 fills**. No parameters were
touched, no filters added, nothing inferred from earlier work.

---

## The curve

### Per bucket (exclusive bands)

| bucket | n | /day | E[R] | win% | PF | median R | sd | t |
|---|---|---|---|---|---|---|---|---|
| <0.5R | 132 | 2.52 | −0.364 | 12.1% | 0.69 | −1.0 | 1.94 | −2.15 |
| 0.5–1R | 150 | 2.87 | −0.562 | 8.7% | 0.47 | −1.0 | 1.66 | −4.14 |
| 1–1.5R | 189 | 3.61 | −0.255 | 13.8% | 0.80 | −1.0 | 2.06 | −1.70 |
| 1.5–2R | 260 | 4.97 | −0.166 | 15.4% | 0.91 | −1.0 | 2.16 | −1.24 |
| 2–3R | 589 | 11.26 | −0.216 | 14.6% | 0.85 | −1.0 | 2.11 | −2.49 |
| 3–5R | 1,310 | 25.05 | −0.069 | 17.3% | 1.05 | −1.0 | 2.27 | −1.10 |
| 5–10R | 2,278 | 43.56 | −0.173 | 16.2% | 0.97 | −1.0 | 2.20 | −3.75 |
| **≥10R** | **1,311** | **25.07** | **+0.059** | **20.7%** | **1.30** | −1.0 | 2.44 | **+0.87** |
| no destination | 0 | — | — | — | — | — | — | — |

### Cumulative — every trade with room ≥ the floor

| floor | n | /day | E[R] | 90% CI | win% | PF | t | R/day | worst streak |
|---|---|---|---|---|---|---|---|---|---|
| ≥0 (no filter) | 6,219 | 118.9 | −0.122 | [−0.169, −0.075] | 16.8% | 1.01 | −4.29 | −14.52 | 47 |
| ≥0.5R | 6,087 | 116.4 | −0.117 | [−0.164, −0.069] | 17.0% | 1.02 | −4.06 | −13.60 | 47 |
| ≥1R | 5,937 | 113.5 | −0.106 | [−0.154, −0.057] | 17.2% | 1.04 | −3.60 | −11.99 | 46 |
| ≥1.5R | 5,748 | 109.9 | −0.101 | [−0.150, −0.052] | 17.3% | 1.04 | −3.37 | −11.07 | 46 |
| ≥2R | 5,488 | 104.9 | −0.098 | [−0.148, −0.047] | 17.4% | 1.05 | −3.18 | −10.24 | 45 |
| ≥3R | 4,899 | 93.7 | −0.083 | [−0.137, −0.030] | 17.7% | 1.08 | −2.55 | −7.81 | 44 |
| ≥5R | 3,589 | 68.6 | −0.089 | [−0.152, −0.026] | 17.8% | 1.09 | −2.31 | −6.08 | 42 |
| **≥10R** | **1,311** | **25.1** | **+0.059** | **[−0.052, +0.169]** | **20.7%** | **1.30** | **+0.87** | **+1.47** | 31 |

### Incremental cost of each step up

| step | ΔE[R] | trades lost/day | ΔR/day | effect |
|---|---|---|---|---|
| 0 → 0.5R | +0.005 | 2.5 | +0.92 | less negative |
| 0.5 → 1R | +0.011 | 2.9 | +1.61 | less negative |
| 1 → 1.5R | +0.005 | 3.6 | +0.92 | less negative |
| 1.5 → 2R | +0.003 | 5.0 | +0.83 | less negative |
| 2 → 3R | +0.014 | 11.3 | +2.44 | less negative |
| 3 → 5R | −0.005 | 25.1 | +1.73 | less negative |
| **5 → 10R** | **+0.147** | **43.6** | **+7.54** | **turns positive** |

### Sign consistency across the ten cells

| floor | MGC l | MGC s | SIL l | SIL s | MNQ l | MNQ s | MCL l | MCL s | 6E l | 6E s | signs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ≥0 | −0.325 | +0.048 | −0.194 | +0.119 | −0.120 | −0.063 | −0.202 | −0.287 | −0.105 | −0.032 | **2/10** |
| ≥1.5R | −0.330 | +0.103 | −0.187 | +0.132 | −0.083 | −0.077 | −0.140 | −0.239 | −0.096 | −0.010 | **2/10** |
| ≥3R | −0.261 | +0.181 | −0.153 | +0.090 | −0.013 | −0.091 | −0.108 | −0.244 | −0.188 | +0.013 | **3/10** |
| ≥5R | −0.215 | +0.122 | −0.139 | −0.023 | −0.035 | −0.096 | −0.083 | −0.181 | −0.274 | +0.067 | **2/10** |
| **≥10R** | **+0.232** | **+0.354** | **+0.014** | **−0.194** | **+0.307** | **+0.120** | **−0.007** | **+0.077** | **−0.406** | **+0.031** | **7/10** |

---

## The five questions, answered

### 1. Does 10R actually add meaningful expectancy?

**It is the only threshold that produces a positive number at all — and it is
still not statistically significant.**

Every floor from 0 to 5R is negative with a 90% CI that **excludes zero**
(t between −4.29 and −2.31). This setup **loses money at any room floor below
10R**, and that is a well-powered result: 3,589–6,219 fills.

At ≥10R it flips to +0.059R, but the CI is **[−0.052, +0.169]** — it contains
zero, t = +0.87. So the honest statement is: 10R is the only floor that isn't
demonstrably losing, and it is not demonstrably winning either.

### 2. Is there a plateau at 1.5R–3R?

**No.** The cumulative curve is essentially flat across the entire 0–5R range:
−0.122, −0.117, −0.106, −0.101, −0.098, −0.083, −0.089. Total movement across
ten-fold changes in the threshold is **0.039R**, and every point is negative.
The individual 1.5–2R bucket looked promising in three cells (SIL s +0.628,
6E l +0.583, MCL s +0.520) but pools to **−0.166R** across all ten. That is
three cells out of ten, which is what noise looks like.

### 3. How much frequency does lowering the threshold gain?

**A great deal — and all of it is loss-making.** Dropping from 10R to no filter
takes 25.1 → 118.9 fills/day, a **4.7× increase**, and takes R/day from
**+1.47 to −14.52**. Every trade added below 10R has negative expectancy in
aggregate. This is the clearest possible answer to "are we filtering out good
opportunities": **no — the discarded 75% are the losing ones.**

### 4. Is there a clear knee?

**Yes, and it is at 10R, not in the 1.5–3R region.** Six of the seven steps up
move expectancy by +0.003 to +0.014R. The 5R → 10R step moves it by **+0.147R**
— an order of magnitude larger — and is the only step that changes the sign.
The curve is flat-negative then steps up once, sharply, at the far end.

### 5. Is the room effect robust or sampling noise?

**Partly robust, and weaker than the pooled number suggests.**

- Sign consistency jumps from **2–3 of 10 cells** at every floor below 10R to
  **7 of 10** at ≥10R. That jump is real and is the strongest evidence here.
- But the three failures at ≥10R are severe: 6E long **−0.406**, SIL short
  **−0.194**, MCL long −0.007. 6E long is the second-largest magnitude in the
  entire ≥10R row, pointing the wrong way.
- The pooled +0.059R has a CI spanning zero, so the effect **is not established
  at conventional confidence** even at its best threshold.

**Verdict: 10R survives, 1.5–3R does not.** The room floor is doing real work,
and the work it does is removing losers rather than finding winners.

---

## What the ledger also showed

| | pooled across 10 cells |
|---|---|
| sweep events detected | 6,932 |
| filled | 6,219 (89.7%) |
| expired (no retest in 24 bars) | 710 |
| rejected by the R cap | 2 |
| **dropped for lack of a slot at 8 slots** | **1** |
| **would have been dropped at 2 slots** | **1,511 (21.8%)** |
| simultaneous sweeps suppressed by the first-match cascade | 522 |
| candidates with **no destination** | **0** |

Three previously invisible things are now measured:

1. **The 2-slot limit was silently discarding 21.8% of all candidates** in every
   result this project has produced. At 8 slots it costs 1 candidate in 6,932.
   This was an engine artefact acting as an unmeasured filter.
2. **The R cap rejects almost nothing** — 2 of 6,221. It is not a bottleneck.
3. **The detector cascade suppresses 522 simultaneous sweeps** (7.5% more
   candidates available if all swept levels were emitted).
4. **"No destination" never occurs** — every fill had an opposing level. The
   inconsistency flagged in the audit (na room allowed when the filter is off,
   rejected when on) turns out to be moot in practice.

---

## Limits of this measurement, stated plainly

- **Median R is uninformative by construction.** Every trade resolves to +5R or
  −1R minus cost, so the median is −1R at any win rate below 50% — which is every
  bucket. It says nothing about room.
- **True per-bucket drawdown is not available.** V48 records no equity ordering.
  The "worst streak" column is the expected longest losing run at that win rate,
  a labelled proxy, not a drawdown measurement.
- **PF is derived** from win rate and the fixed payoff, gross of the per-trade
  cost that E[R] already carries. Approximate.
- **This is folds A+B only.** Fold C remains sealed. Nothing here has been
  validated out-of-sample.

---

## Stopping here

Per instruction, no strategy change follows from this. The one thing the data
clearly does **not** support is lowering the room threshold: doing so would add
94 trades a day at an aggregate expectancy of roughly −0.16R each.

The open question this raises — and it is a bigger one than the threshold — is
that **even the best cell of the best threshold is not significantly positive.**
The sweep family may simply not have an edge at any room setting, which fold C
already hinted at. That is the next thing worth testing, not a looser filter.

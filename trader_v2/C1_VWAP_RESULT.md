# Phase 11 — C1 session-VWAP test: **FAIL**

V50 = V49 plus three recorded attributes. Entry/exit mechanics, sweep detection,
stop, retest window, R cap, slot pool and cascade removal are unchanged and
nothing gates on the attributes. Folds A+B, ten instrument × direction cells,
**6,658 fills** from 7,454 candidates.

---

## 1. Implementation and sanity checks

| check | result |
|---|---|
| side counts reconcile to fill counts, every cell, every feature | **OK** |
| candidates / fills match the V49 ledger | **OK** — spot-checked 6E short: cands 176, fills 152, sweepBars 167, expired 21, rejR 3, identical to V49 |
| VWAP uses only closed-bar information | **OK** — cumulative `hlc3 × volume` from the 22:00 UTC reset, current bar inclusive; no `request.security`, no `lookahead_on`, never the session's final value |
| session reset per spec (22:00 UTC, CME boundary) | **OK** |
| missing VWAP handled as specified | **OK** — 0 excluded; every session on all five instruments had volume |
| SMA20 uses the same freeze point | **OK** — both read at the arm bar close and stored per slot |
| random-sign seed fixed and recorded | **42** |
| no entry/exit logic changed | **OK** |
| no candidate added or removed because of VWAP | **OK** — attributes are written after the arm decision |

### Disclosure — a fold-C read

The V50 study inherited `foldSel = 2` from the previous V49 run. Before I set it
to A+B I read **one fold-C cell (6E short)** and saw its VWAP/SMA/random numbers.
I switched to A+B immediately and used nothing from it.

This does not affect the result below — the specification and the gate were both
frozen and committed before this run, so there was nothing for the reading to
influence. But **fold C is no longer fully sealed for 6E short**, and if C1 had
passed, the honest correction would have been to validate on the nine clean cells
and mark that one contaminated. C1 failed, so the point is moot, but it is on the
record.

---

## 2. Pooled result

| partition | side | n | E[R] | win% | difference | 90% CI | t |
|---|---|---|---|---|---|---|---|
| **VWAP** | + | 3,220 | −0.0867 | 17.4% | **+0.0648** | **[−0.0258, +0.1553]** | +1.18 |
| | − | 3,438 | −0.1515 | 16.3% | | | |
| **SMA20 control** | + | 3,243 | −0.0784 | 17.6% | **+0.0803** | [−0.0103, +0.1709] | +1.46 |
| | − | 3,411 | −0.1587 | 16.2% | | | |
| **random-sign control** | + | 3,428 | −0.0850 | 17.4% | **+0.0726** | [−0.0178, +0.1630] | +1.32 |
| | − | 3,230 | −0.1576 | 16.2% | | | |

**All three partitions produce the same thing.** A coin flip seeded with 42
separates this population by +0.073R; VWAP separates it by +0.065R. VWAP is
*below* the random control. Every CI contains zero.

## 3. Ten-cell VWAP results

| cell | n + | E + | n − | E − | diff | sign |
|---|---|---|---|---|---|---|
| MGC long | 140 | −0.3042 | 564 | −0.3048 | +0.0006 | + |
| MGC short | 448 | −0.0160 | 156 | +0.1731 | −0.1891 | − |
| SIL long | 172 | −0.1969 | 599 | −0.1851 | −0.0118 | − |
| SIL short | 424 | +0.1920 | 138 | −0.0419 | +0.2339 | + |
| MNQ long | 208 | −0.0993 | 517 | −0.1423 | +0.0430 | + |
| MNQ short | 718 | −0.0977 | 149 | −0.1160 | +0.0183 | + |
| MCL long | 145 | −0.2489 | 593 | −0.1677 | −0.0812 | − |
| MCL short | 458 | −0.3928 | 139 | +0.0636 | −0.4564 | − |
| 6E long | 108 | +0.1286 | 487 | −0.1177 | +0.2463 | + |
| 6E short | 399 | +0.0396 | 96 | −0.2142 | +0.2538 | + |

**VWAP positive in 6/10 cells.**

## 4. SMA20 control

Diff **+0.0803**, 90% CI [−0.0103, +0.1709], positive in **6/10** cells.
Identical sign count to VWAP and a *larger* pooled difference.

## 5. Random-sign control (seed 42)

Diff **+0.0726**, 90% CI [−0.0178, +0.1630], positive in **7/10** cells.
**The random control beats VWAP on both gate criteria.**

## 6. Gate

| criterion | result |
|---|---|
| 1. VWAP beats SMA20 by a margin whose 90% CI excludes zero | **FAIL** — paired across the ten cells the difference is **−0.0133**, 90% CI [−0.1784, +0.1517]. VWAP is *worse* than the control, and the CI contains zero |
| 2. same sign in ≥ 7/10 cells | **FAIL** — 6/10 |

### **GATE: FAIL**

### Power, honestly

The pooled split realised **3,220 / 3,438**, essentially the ~3,100 per side
assumed at pre-registration. With SE 0.0551 the minimum detectable effect at 80%
power (α = 0.10, two-sided) is **0.137R**, against the 0.15R pre-registered — so
**the pooled test had the power it promised.** A true VWAP effect smaller than
~0.14R would not have been found, and this result is not evidence that such an
effect is zero.

But that caveat does not rescue anything here, because the failure is not
"too small to see". It is that **a seeded coin flip partitioned the same fills
slightly better than VWAP did.** Whatever the ~+0.07R common to all three splits
is, it is a property of the population's noise at this sample size, not of any of
the three signals.

The per-cell criterion was weaker than the pooled one: within-cell side splits
are very lopsided (MNQ short 718/149, 6E long 108/487), so individual cell signs
carry less information than a balanced split would.

## 7. Exact next action

**Stop C1.** Recorded as failed on folds A+B. Fold C is not run for C1.

No further VWAP work: no other anchor, session, band, distance decile, moving
average, threshold or combination. Per the standing instruction, a failed result
is not rescued.

C1 is closed. C2 (level maturity — age and prior touches) and C3 (session phase)
remain unrun candidates from the Phase 10 map, in that order of priority. Neither
is started in this run.

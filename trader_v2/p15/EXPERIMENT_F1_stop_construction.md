# Phase 15 — Experiment F1: Stop Construction

**Hypothesis component varied:** §14 / F5, the stop definition.

**Frozen baseline rule:** long stop = sweep low − 0.20 × ATR(5m); short stop = sweep high +
0.20 × ATR(5m).

**F1 rule:** long stop = sweep low; short stop = sweep high. No buffer. Definition exactly as
pre-registered.

This experiment tests the **sensitivity of the hypothesis to the stop convention**. It is not a
search for a profitable stop, and nothing below is offered as evidence that either convention is
better.

---

## 0. Provenance

| | |
|---|---|
| executed baseline | `p15/executed/V53_EXECUTED_BUILD.pine`, sha256 `2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6` |
| F1 artifact | `p15/exec_arms/V53_EXEC_P15_F1_stop_raw_extreme.pine`, sha256 `4b305b21e3a2470575585945e79e94f91cb8a36d9f4524e70c72a4f620424af9` |
| derivation | 1 hunk, +1 / −1 line against the executed baseline |
| output layer | byte-identical to the executed baseline (verified) |
| injection | `pine_set_source` (602 lines) then `pine_smart_compile`; `pineVersion` 140.0 → 141.0 |

Residue checks before injection: C1 `aA` 0, D1 marker 0, E1 marker 0; the `qV` BOS fallback and
the strict single-bar FVG test are both present, so the frozen BOS and FVG rules are restored.
`bufATR` remains an input at 0.20 but is no longer referenced by the stop assignment.

---

## 1. Correction to the stated invariant, made before the run

The pre-run brief proposed the invariant *sweeps → CHOCH → retest → BOS+disp → FVG → **fills** =
baseline*, with any change a hard stop.

**Fills cannot be part of that invariant.** The stop sits inside the fill gate. Section 2 computes

```
r     = |E - stp|
ratio = r / ATR(5m at arm time)
fill only if  minRatr (0.05) <= ratio <= maxRatr (3.00)
```

Changing the stop changes `r`, so it can move a candidate across either edge of the R-band. A
fills change is therefore a **necessary mechanical consequence of the stop definition**, not an
upstream leak.

The invariant actually enforced was **sweeps → CHOCH → retest → BOS+disp → FVG identical**, with
any fills delta required to be fully absorbed by the R-band reject counter. The audit is the
conservation identity

```
FVG = fills + R-band rejects + FVG retest expiry
```

which holds exactly on baseline data (e.g. MNQ L 1m: 22 = 11 + 5 + 6).

---

## 2. Specification-integrity check — passed at every stage through FVG

| counter | baseline | F1 | change |
|---|---|---|---|
| sweeps | 3836 | 3836 | **0** |
| CHOCH 1m / 3m | 3324 / 1480 | 3324 / 1480 | **0** |
| CHOCH retests 1m / 3m | 2974 / 1095 | 2974 / 1095 | **0** |
| BOS+disp 1m / 3m | 107 / 74 | 107 / 74 | **0** |
| **FVG 1m / 3m** | **76 / 50** | **76 / 50** | **0** |

And **cell by cell**, every cell reproduces its baseline FVG count exactly:

| cell | baseline fvg | F1 fvg |
|---|---|---|
| MGC L 1m | 10 | 10 |
| MGC S 1m | 18 | 18 |
| MNQ L 1m | 22 | 22 |
| MNQ S 1m | 26 | 26 |
| MGC L 3m | 13 | 13 |
| MGC S 3m | 13 | 13 |
| MNQ L 3m | 6 | 6 |
| MNQ S 3m | 18 | 18 |

**F1 leaks nowhere upstream.** Everything through entry generation is bit-identical; divergence
begins exactly at the fill gate and the outcome layer.

### Conservation audit — all eight cells reconcile

| cell | FVG | = fills | + R-band rej | + FVG exp |
|---|---|---|---|---|
| MGC L 1m | 10 | 5 | 2 | 3 |
| MGC L 3m | 13 | 6 | 3 | 4 |
| MGC S 3m | 13 | 2 | 5 | 6 |
| MGC S 1m | 18 | 7 | 5 | 6 |
| MNQ S 1m | 26 | 18 | 6 | 2 |
| MNQ S 3m | 18 | 11 | 5 | 2 |
| MNQ L 3m | 6 | 1 | 1 | 4 |
| MNQ L 1m | 22 | 12 | 4 | 6 |

In the four 1m cells where the baseline split is on record, **FVG retest expiry is unchanged in
every one** and the R-band reject count moves exactly opposite to fills:

| cell | fills base → F1 | R-band rej base → F1 | FVG exp |
|---|---|---|---|
| MGC L 1m | 4 → 5 | 3 → 2 | 3 → 3 |
| MGC S 1m | 8 → 7 | 4 → 5 | 6 → 6 |
| MNQ L 1m | 11 → 12 | 5 → 4 | 6 → 6 |
| MNQ S 1m | 18 → 18 | 6 → 6 | 2 → 2 |

The entire fills delta is confined to the R-band, i.e. to the stop layer.

`ASSERTS 21-27,32 = 0/0/0/0/0/0/0/0` and `dropped (no slot) = 0` in all eight cells.

Ledger confirmation that the rule is live: every F1 row has `stop` exactly equal to `swX`
(e.g. MGC L 1m `swX 4484.3 … stop 4484.3`).

---

## 3. Recorded separately, as required

### Fill count

| | baseline | F1 | Δ |
|---|---|---|---|
| 1m | 41 | 42 | +1 (+2.4%) |
| 3m | 17 | 20 | +3 (+17.6%) |

Per cell the delta runs in **both directions** — +1 (MGC L 1m), −1 (MGC S 1m), +1 (MNQ L 1m),
0 (MNQ S 1m), +1 (MGC L 3m), +1 (MGC S 3m), 0 (MNQ L 3m), +1 (MNQ S 3m). A smaller `r` can push a
candidate below `minRatr` (losing a fill) or back under `maxRatr` (gaining one); both occur, so
the R-band is binding at both edges in this dataset.

### Win / loss / timeout counts

| | fills | W | L | TO |
|---|---|---|---|---|
| 1m baseline | 41 | 5 | 36 | 4 |
| **1m F1** | 42 | 6 | 36 | **2** |
| 3m baseline | 17 | 4 | 13 | 1 |
| **3m F1** | 20 | 4 | 16 | **2** |

### R and drawdown

| | R post-drag | expectancy | maxDD (R) |
|---|---|---|---|
| 1m baseline | −13.389 | −0.3266 | 23.941 |
| **1m F1** | −9.003 | −0.2144 | 24.417 |
| 3m baseline | +6.482 | +0.3813 | 9.232 |
| **3m F1** | +3.356 | +0.1678 | 11.298 |

The two hypotheses move in opposite directions. Drawdown rises in both.

### Outcome divergence

Three distinct mechanisms are visible, all inside the stop/outcome layer:

1. **Timeouts convert to stops.** A tighter stop is reached sooner, so trades that previously ran
   to the 144-bar limit now terminate early. MNQ L 1m is the clearest case: baseline 11 fills,
   0W / 9 stops / 2 timeouts → F1 12 fills, 0W / **12 stops / 0 timeouts**. Pooled 1m timeouts
   fall 4 → 2.
2. **Same trade, different R denominator.** Identical entries produce different R and $ because
   `r` shrank — e.g. MGC L 1m 2026-06-26 WIN 4.958R / $357.53 → 4.952R / $312.
3. **The fixed $3 drag becomes a larger fraction of R.** Since `cR = costUSD / (r × pointvalue)`
   and `r` is smaller, every loss is further below −1R: MNQ S 1m 2026-06-17 12:30 goes
   −1.137R → **−1.250R**. This is a systematic, mechanical penalty of the tighter stop, not a
   market effect.

Per fold (R post-drag / fills):

| | fold A | fold B | fold C |
|---|---|---|---|
| 1m baseline | −4.940 / 16 | −6.812 / 12 | −1.637 / 13 |
| 1m F1 | −1.423 / 18 | −5.726 / 11 | −1.854 / 13 |
| 3m baseline | −4.256 / 10 | +9.944 / 2 | +0.794 / 5 |
| 3m F1 | −6.324 / 12 | +9.938 / 2 | −0.258 / 6 |

All folds move. Even 3m fold B — bit-identical in C1, D1 and E1 — shifts here, from +9.944 to
+9.938: the same two trades with a fractionally larger cost drag. This is the first arm to touch
it, and it does so through the R denominator rather than by changing which trades occur.

### Event clustering (Phase 13G identities, unchanged) — recorded, not analysed

| | execution N | primary | alternative | largest | fills in multi-fill clusters |
|---|---|---|---|---|---|
| baseline all | 58 | 43 | 37 | 3 | 69.0% |
| **F1 all** | 62 | 45 | 39 | 3 | 69.4% |
| F1 1m | 42 | 33 | 27 | 3 | 66.7% |
| F1 3m | 20 | 12 | 12 | 3 | 75.0% |

Carried forward for the joint C1–G1 analysis; not interpreted here.

---

## 4. What this experiment establishes

1. **The strongest invariant of the study holds exactly.** Sweeps, CHOCH, retests, BOS+disp and
   FVG are all bit-identical to baseline on both LTFs and in every individual cell. F1 does not
   leak upstream at all.
2. Fills are *not* invariant, and could not have been: the stop is the R-band denominator. The
   delta is fully absorbed by R-band rejects, verified by a conservation identity that reconciles
   in all eight cells.
3. The R-band binds at **both** edges — removing the buffer gains fills in six cells and loses
   one in another — so the frozen ±0.20 × ATR buffer is not simply "loosening" or "tightening"
   the filter; it moves candidates across two boundaries at once.
4. The stop convention changes outcomes through three separable mechanisms: timeout→stop
   conversion, a rescaled R denominator, and a mechanically larger cost drag per unit R.
5. The hypothesis is **not** insensitive to the stop convention: 1m R moves +4.386 and 3m R moves
   −3.126 on a change that alters no structural event whatsoever. The same 76 and 50 fair-value
   gaps produce materially different results depending only on where the stop is placed.
6. Nothing here demonstrates an edge under either convention, and the changed win rates
   (12.2% → 14.3% on 1m, 23.5% → 20.0% on 3m) are **not** evidence that one stop is better.

**The frozen V53 setting (sweep extreme ± 0.20 × 5m ATR) remains the official baseline regardless
of these results.** No ranking is made and no winner is declared. Joint analysis of C1–G1 against
the frozen executed baseline is deferred until G1 is complete.

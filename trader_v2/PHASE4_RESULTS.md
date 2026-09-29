# Phases 2 & 4 — development results, and the frozen specification

Folds A + B only. Fold C has not been opened at the time of writing. Ten
instrument × direction cells across four complexes (metals: MGC, SIL; equity:
MNQ; energy: MCL; FX: 6E).

---

## 1. Phase 2 — the ex-ante bias model

Six candidates, all `lookahead_off`, all permitted to abstain. Selection rule
was fixed in `PHASE2_PROTOCOL.md` before the run.

| model | cells | pooled E[R] | n | keeps | t |
|---|---|---|---|---|---|
| **B1 4H trend** (EMA20/50) | **7/10** | **+0.132** | 674 | 48.0% | +1.37 |
| B5 B1 ∧ B2 agree | 7/10 | +0.131 | 480 | 35.7% | +1.14 |
| B0 control (no filter) | 7/10 | +0.050 | 1,378 | 100% | +0.76 |
| B2 4H structure | 6/10 | +0.058 | 633 | 46.8% | +0.59 |
| B4 HTF displacement | 3/10 | +0.002 | 516 | 38.5% | +0.02 |
| B3 previous-day structure | 3/10 | **−0.249** | 335 | 27.5% | **−2.11** |

**B1 is selected.** Its margin over B5 (+0.132 vs +0.131) is meaningless and is
reported as a tie; the pre-registered tie-break picked B1 and that is all it did.

Two clean negatives worth keeping: **B3 previous-day structure is significantly
harmful** (t = −2.11), and **B4 displacement is exactly a coin flip** (+0.002R,
3/10) — the second independent time displacement has measured as worthless.

### The honest test of a filter: kept vs discarded

"Is the kept set positive" is the wrong question; "does the filter separate two
populations" is the right one. B1 kept vs B0 \ B1 discarded:

| | E[R] | n |
|---|---|---|
| kept (bias aligned) | +0.132 | 674 |
| discarded (bias opposed) | −0.028 | 704 |
| **difference** | **+0.160** | t = **+1.22** |

Separates in **6 of 10 cells**. 90% CI on the difference **[−0.055, +0.376]** —
**it contains zero.**

**This materially downgrades the earlier +0.334R / 4-of-4 result.** That was
measured on MGC and MNQ alone — the two instruments this project has been
developed on all along. Adding silver, crude and euro roughly halves the effect
and breaks the sign consistency. The HTF bias effect is directionally positive
and **not established**.

---

## 2. Phase 4 — the ablation, with room as an explicit switch

The V44 defect mattered. Room ≥ 10R was silently on in every V44 rung, so "sweep
only" was never sweep-only and every gain was attributed to bias by default.
With room switchable:

| config | pooled E[R] | cells | n | t |
|---|---|---|---|---|
| 1 sweep only | **−0.100** | 2/10 | 5,479 | **−3.27** |
| 2 + bias | −0.031 | 5/10 | 2,645 | −0.69 |
| 3 + room | +0.050 | 7/10 | 1,378 | +0.76 |
| **4 + bias + room** | **+0.132** | **7/10** | 674 | +1.37 |
| 5 + bias + displacement | **−0.366** | 1/10 | 803 | **−5.24** |
| 6 + bias + reclaim | −0.021 | 4/10 | 2,001 | −0.40 |
| 7 + bias + room + displacement | −0.528 | 3/10 | **97** | — |
| 8 full | −0.498 | 3/10 | **84** | — |

Configs 7 and 8 have **2–20 fills per cell**. They are not ranked and nothing is
concluded from them in either direction.

### Marginal effect of each condition, same event stream

| condition | improves | mean |
|---|---|---|
| **ROOM**, without bias | **8/10** | **+0.142** |
| **ROOM**, with bias | 7/10 | **+0.155** |
| BIAS, without room | 7/10 | +0.034 |
| BIAS, with room | 6/10 | +0.047 |
| RECLAIM, on bias | 5/10 | −0.004 |
| **DISPLACEMENT**, on bias | **0/10** | **−0.322** |

### Three findings that change the emphasis

1. **The unconditioned sweep loses money, significantly.** −0.100R over 5,479
   fills, t = −3.27, positive in only 2 of 10 cells. Trading liquidity sweeps
   with no filter is not a neutral base rate — it is a losing setup.

2. **Room, not bias, is what carries this system.** Room is worth ~3–4× what
   bias is worth and is more consistent (8/10 vs 7/10). It takes the setup from
   −0.100R to +0.050R on its own; bias then adds +0.047R on top. The V44 write-up
   credited bias for work room was already doing.

3. **Displacement is actively destructive**, at 0/10 cells and t = −5.24 on
   803 fills. This is now the strongest single negative result in the project.
   Combined with room it also nearly empties the sample (97 fills from 10 cells),
   reproducing the F3 and L4 finding: after a displacement bar, price does not
   come back.

**Reclaim is a null** — 5/10, mean −0.004. Not harmful, not useful.

---

## 3. Frozen specification, declared before fold C is opened

**Primary model for the fold-C test: config 4 — sweep + HTF bias (B1) + room ≥ 10R.**

Everything else in the fold-C run is secondary and exploratory. Declaring this
now is the point: the Pine reports all eight configs from a single pass, so
without this declaration I could pick whichever config happened to survive and
call it the result. **Config 4 is the result. The other seven are context.**

Frozen parameters, none of them tuned in this phase: 4H EMA 20/50; room ≥ 10R to
the nearest opposing level; structural stop beyond the sweep extreme + 0.20 ATR;
5R target, −1R stop; adverse excursion checked first; R ∈ [0.05, 3.00] × ATR;
24-bar retest window; 144-bar timeout; $3.00 execution drag in R; sweep = 0.10
ATR beyond a previous-day / Asia-session / 10-bar-pivot level.

Gate, from Amendment 1: pooled E[R] > 0 **and** pooled one-sided t ≥ +1.5 **and**
≥ 7/10 instrument cells **and** ≥ 6/8 complex cells. Expected ~26 fills per cell.
Power ≈ 55%, false-positive ≈ 6% — **a failure will be genuinely ambiguous**, and
that was put on the record before the test, not after.

Fold C is run once. No re-specification afterwards.

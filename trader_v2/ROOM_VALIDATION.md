# ≥10R validation — fold C is inconclusive, and the per-cell effect does not persist

Run on the committed V48, definition untouched, no retuning. Only the fold input
changed. Fold C = 2026-08-09 → 08-31, 14.5 trading days, ten instrument ×
direction cells.

---

## 1. Fold C validation of ≥10R

| | n | /day | E[R] | 90% CI | win% | PF | t | signs |
|---|---|---|---|---|---|---|---|---|
| **folds A+B** | 1,311 | 25.1 | **+0.059** | [−0.052, +0.169] | 20.7% | 1.30 | +0.87 | **7/10** |
| **fold C** | 390 | 26.9 | **+0.008** | **[−0.193, +0.209]** | 20.0% | 1.25 | **+0.07** | **6/10** |

**The ≥10R effect did not survive. It did not invert — it went to zero.**
t = +0.07 is as close to nothing as a number gets, and the CI is wide enough to
contain both a strong edge and a strong anti-edge.

### The whole curve is flat on fold C

| floor | n | /day | E[R] | 90% CI | t | signs |
|---|---|---|---|---|---|---|
| ≥0 (no filter) | 1,857 | 128.1 | −0.004 | [−0.094, +0.086] | −0.07 | 5/10 |
| ≥1.5R | 1,731 | 119.4 | −0.012 | [−0.106, +0.081] | −0.21 | 5/10 |
| ≥3R | 1,485 | 102.4 | +0.010 | [−0.092, +0.112] | +0.16 | 6/10 |
| ≥5R | 1,076 | 74.2 | −0.044 | [−0.162, +0.075] | −0.61 | 5/10 |
| ≥10R | 390 | 26.9 | +0.008 | [−0.193, +0.209] | +0.07 | 6/10 |

On folds A+B the ≥10R floor was worth **+0.181R** over no filter. On fold C it is
worth **+0.012R**. The advantage is 15× smaller and inside the noise.

**The 5→10R knee also shrank**: +0.147R on A+B, **+0.052R** on fold C. The
structural transition the A+B curve showed is not visible out-of-sample at
anything like the same magnitude.

## 2. The per-cell effect has no cross-fold persistence — this is the decisive number

| cell | A+B E[R] | fold C E[R] | shift |
|---|---|---|---|
| MGC long | +0.232 | +0.310 | +0.078 |
| MGC short | +0.354 | +0.290 | −0.064 |
| SIL long | +0.014 | +0.072 | +0.058 |
| SIL short | −0.194 | +0.313 | **+0.507** |
| MNQ long | +0.307 | −0.483 | **−0.790** |
| MNQ short | +0.120 | −0.211 | −0.331 |
| MCL long | −0.007 | −0.817 | **−0.810** |
| MCL short | +0.077 | −0.101 | −0.178 |
| 6E long | **−0.406** | **+0.279** | **+0.685** |
| 6E short | +0.031 | +0.376 | +0.345 |

| statistic | value |
|---|---|
| Pearson r (A+B vs C, ten cells) | **−0.198** |
| Spearman ρ | **−0.103** |
| cells keeping their sign | **5/10** |
| mean absolute shift per cell | **0.385R** |

**A correlation of −0.20 across folds means the A+B per-cell ordering carried no
information about fold C — if anything it pointed the wrong way.** The two cells
that looked best on A+B (MNQ long +0.307, MGC short +0.354) went to −0.483 and
+0.290; the worst (6E long −0.406) became the third best (+0.279). Five of ten
cells flipped sign, and the average cell moved 0.385R — six times the size of the
pooled effect being tested.

That is what sampling noise looks like. It is not what a stable setup-quality
signal looks like.

## 3. Is the room effect independent of the failed 4H bias filter?

| fold | ≥10R alone | ≥10R + 4H bias |
|---|---|---|
| A+B | +0.050R, n 1,378, 7/10 | +0.132R, n 674, 7/10 |
| **C** | **+0.043R, n 363, 6/10** | **−0.074R, n 182, 4/10** |

**Yes — room is independent of the bias filter, and adding bias makes it worse
out-of-sample.** Room alone holds its (small, non-significant) value across
folds; room + bias inverts. This confirms the earlier finding that the 4H
directional filter should not be reinstated, and it means the room result is not
a disguised bias result.

**Caveat that cuts against the room number**: these V47 rows ran on the **2-slot**
engine, which silently discarded ~22% of candidates. Measured properly at 8
slots, fold-C ≥10R is **+0.008 (n 390)**, not V47's +0.043 (n 363). **Fixing the
slot artefact removed most of what little fold-C room advantage there appeared to
be.** The artefact was flattering the result.

## 4. Decomposition of ≥10R — is it broad or one subgroup?

**On folds A+B it is broad, not subgroup-driven.** Leave-one-cell-out on the
+0.059R pooled figure moves it between +0.021 and +0.103. No single cell carries
it; dropping the worst cell (6E long) only lifts it to +0.103, still
non-significant.

**On fold C the decomposition splits along lines that contradict A+B:**

| split | n | E[R] | 90% CI | t | signs |
|---|---|---|---|---|---|
| long cells | 172 | −0.108 | [−0.397, +0.181] | −0.61 | 3/5 |
| short cells | 218 | +0.099 | [−0.177, +0.376] | +0.59 | 3/5 |

| instrument | n | E[R] | win% | t |
|---|---|---|---|---|
| MGC | 83 | +0.298 | 24.1% | +1.05 |
| SIL | 110 | +0.197 | 20.9% | +0.84 |
| MNQ | 94 | −0.309 | 14.9% | −1.42 |
| MCL | 64 | −0.414 | 17.2% | −1.49 |
| 6E | 39 | +0.316 | 25.7% | +0.74 |

Metals positive, equity index and energy negative, FX positive on 39 trades. Not
one of these reaches significance, and the pattern does not match A+B (where 6E
long was the worst cell by a distance and is now positive). **Splitting a null
result into subgroups produces subgroups that differ by chance.** I am not going
to read a metals-only strategy out of this.

**Not measured**: session and setup-family decomposition. Both require adding
labels to the measurement engine, which V48 does not carry. Given fold C came
back flat, decomposing it further would be looking for structure that the
top-line test has already failed to find.

## 5. Fine-graining the 5R–20R transition — not run, and why

The point of fine-graining was to locate a stable structural transition. Fold C
has already answered the prerequisite question: **the 5→10R step is +0.147R
in-sample and +0.052R out-of-sample, and the ≥10R level itself is +0.008R with
t = +0.07.** Sampling nine thresholds on folds A+B would produce a "best" one,
and fold C gives no reason to believe any of them. That is the historical-maximum
trap the instruction warned about, so I have not run it.

If it is run later, it should be run on **both folds simultaneously** and judged
on whether the transition appears in the same place in each — not on which
threshold maximises A+B.

---

## FINAL ANSWER

> **Is ≥10R room a reproducible, direction-independent setup-quality signal, or is
> the +0.059R result likely sample-specific?**

**Likely sample-specific.** Stated precisely:

1. **Fold C is inconclusive, leaning null.** +0.008R, n 390, 90% CI
   [−0.193, +0.209], t = +0.07, 6/10 cells. It neither confirms nor refutes an
   edge; it fails to detect one.
2. **The in-sample structure did not reproduce.** The ≥10R advantage over no
   filter fell from +0.181R to +0.012R. The knee fell from +0.147R to +0.052R.
3. **The per-cell effect has no cross-fold persistence at all** — Pearson
   −0.198, Spearman −0.103, 5/10 signs kept, mean shift 0.385R. This is the
   strongest single piece of evidence and it points one way.
4. **It is direction-independent**, which was the one thing that held: room does
   not depend on the 4H bias filter, and adding that filter makes it worse OOS.
5. **Part of the original signal was an engine artefact.** The 2-slot bottleneck
   was discarding 22% of candidates; removing it cut fold-C ≥10R from +0.043 to
   +0.008.

**No edge is declared.** The correct reading of A+B's 7/10 and +0.059R is that a
non-significant in-sample pattern failed to reproduce out-of-sample, and the
per-cell correlation says the pattern was never carrying information.

**What ≥10R still is:** the only threshold that is not *demonstrably negative* on
folds A+B, where every floor from 0 to 5R had a CI excluding zero. That is a real
asymmetry and it is why the threshold should stay at 10R rather than be lowered.
But "not demonstrably losing" is not an edge, and it should not be built on.

The honest next question is the one fold C keeps pointing at: **does the sweep
family have an edge at all?** Two out-of-sample tests have now come back flat.
That is worth settling before any further conditioning of it.

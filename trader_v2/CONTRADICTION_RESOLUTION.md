# Resolving the contradiction: continuation process vs mean-reversion measurements

**Question posed:** the statistical engine keeps selecting mean-reversion / fade
behaviour, while the described discretionary process is continuation-flavoured.
Which is it?

**Answer: A — representation problem.** Detail, evidence and limits below. No
setup is selected as a winner here; that decision is deliberately not taken in
this document.

---

## 1. What was actually tested

Four independent pieces of work, all on MGC and MNQ 5m, long and short —
the standing 4-cell sign gate — over one 72-day window:

| # | artefact | what it does |
|---|---|---|
| 1 | `HUMAN_RECONSTRUCTION.md` | every recoverable manual trade re-labelled by **thesis** (what the trader expected after entry), from their own words |
| 2 | `confusion_matrix.py` | human label vs what the bot generates **at the same event** |
| 3 | `V44_continuation_ablation.pine` + `ablation_result.py` | one shared sweep event stream, one human condition added per rung — an ex-ante continuation model |
| 4 | `V45_overlap_lab.pine` + `overlap_analysis.py` | how much F0 and F6 actually overlap, and a tag census of what is true when each fires |

---

## 2. The human trades are 4 continuation / 2 reversal

Six trades are recoverable in enough detail to label (`HUMAN_RECONSTRUCTION.md`).
Labelling is by stated thesis, not by which side of a level the entry sat on:

- **Continuation (4):** N1, N2, N3 (narratives — "continue selling with the
  trend", "continued looking for sells", "looking for continuations"), A1
  (Aug 31 verified buy 4434 inside a rally).
- **Reversal (2):** A2 (Aug 31 verified sell 4460 into a swept session high),
  L1 (the loss note — short into an unmitigated OB expecting a correction).

The process is **mixed and context-conditional**, majority continuation.

## 3. The bot agrees on 2/2 reversals and 0/4 continuations

|  | SAME | SAME but from a rejected family | OPPOSITE | NO EVENT |
|---|---|---|---|---|
| human **CONTINUATION** | 0 | 1 | 2 | 1 |
| human **REVERSAL** | **2** | 0 | 0 | 0 |

The disagreement is not about *which bars are interesting* — both sides look at
the same liquidity events. It is about **direction and arming**:

- **N2 is the decisive case.** Bearish bias → sweep of the Asia **low** → rally
  → sell at a supply zone **above** the swept level. F0 places its limit **at**
  the swept level and fills when price comes back **down** to it. F0 is a fade
  by construction, whatever the context, so at this identical event it produces
  a **long**. The engine cannot express the human's trade: the limit is in the
  wrong place and the direction is inverted.
- **N1 arms nothing at all** — a trend leg with no sweep and no range extreme.
- **A1 is directionally right** but only via F5 trend-pullback, the family the
  setup comparison rejected at 1/4 signs.

## 4. The continuation process IS in the data

`V44` holds the event stream, stop convention, room filter and 5R exit fixed
and adds one human condition per rung.

| rung | MGC l | MGC s | MNQ l | MNQ s | pooled | signs | n | /day |
|---|---|---|---|---|---|---|---|---|
| L0 sweep only (= F0) | +0.147 | +0.317 | +0.132 | +0.057 | +0.159 | 4/4 | 745 | 10.4 |
| **L1 + HTF bias aligned** | **+0.273** | **+0.469** | **+0.248** | **+0.273** | **+0.334** | **4/4** | **342** | 4.8 |
| L2 + reclaim | −0.362 | +0.446 | +0.172 | −0.073 | +0.109 | 2/4 | 193 | 2.7 |
| L3 + displacement | −0.316 | +0.546 | +0.374 | −1.101 | +0.085 | 2/4 | 39 | 0.6 |
| L4 entry at displacement 50% | +1.750 | −1.204 | −1.138 | −1.026 | — | 1/4 | **9** | 0.1 |

Marginal effect of each condition on the identical event stream:

| condition added | MGC l | MGC s | MNQ l | MNQ s | improves | mean |
|---|---|---|---|---|---|---|
| **HTF bias aligned** | +0.126 | +0.152 | +0.116 | +0.216 | **4/4** | **+0.153** |
| reclaim (my encoding) | −0.635 | −0.023 | −0.076 | −0.346 | 0/4 | −0.270 |
| displacement | +0.046 | +0.100 | +0.202 | −1.028 | 3/4 | −0.170 |

**One condition — trade only in the direction of the 4H trend — improves the
same sweep events in 4 of 4 cells with a consistent effect size.** That is the
continuation premise, and it is present in the data.

Head to head against the family the statistics had been selecting:

| | E[R] | win% | sd | λ = 2E/σ² | t | signs | n |
|---|---|---|---|---|---|---|---|
| **L1 bias-aligned sweep (continuation)** | **+0.334** | 24.8% | 2.62 | **0.097** | **+2.36** | **4/4** | 342 |
| F6 range mean-reversion | +0.134 | 22.4% | 2.52 | 0.042 | +1.94 | 3/4 | 1,335 |

2.5× the expectancy, 2.3× the λ, a better t on a quarter of the sample, and it
is 4/4 rather than 3/4.

## 5. F0 was averaging two opposite populations

The tag census on every sweep arm (`V45`, n = 4,178 arms pooled):

| | MGC l | MGC s | MNQ l | MNQ s |
|---|---|---|---|---|
| HTF-aligned when the sweep fires | 34.1% | 58.3% | 48.1% | 49.5% |

Roughly **half** of F0's arms are bias-aligned (the continuation trade the human
takes) and half are bias-opposed (a counter-trend fade the human would not
take). F0 pools them, which is why it lands at +0.037R in the family comparison
and near zero everywhere: it is the average of two different trades.

## 6. F0 and F6 are not the same effect — the other open question, now closed

`SETUP_FAMILIES.md` flagged: *"F0 and F6 may be the same effect… overlap that I
have not measured."* Measured now:

| | F0 arms | of which also F6 | F6 arms | of which also F0 |
|---|---|---|---|---|
| pooled, 4 cells | 4,178 | **11.9%** | 3,384 | **14.7%** |

**Jaccard = 497 / 7,065 = 0.070.** Only 11.9% of sweep arms are also
range-regime arms, and only 14.7% of range arms are also sweeps. And each survives with
the other removed:

| bucket | pooled E[R] | signs | n | λ | t |
|---|---|---|---|---|---|
| F0 with every F6 condition absent | +0.124 | 4/4 | 668 | 0.041 | +1.30 |
| F6 with no sweep present | +0.206 | 4/4 | 810 | 0.062 | **+2.27** |
| F0 ∩ F6, entry at the swept level | +0.438 | 4/4 | 78 | 0.120 | +1.43 |
| F6 ∩ F0, entry at the range extreme | +0.262 | 3/4 | 111 | 0.077 | +1.06 |

Neither family is an artefact of the other. The intersection looks like the best
cell in the table but n = 78 and n = 111 — not enough to act on, and not acted on.

**Caveat on this section.** The original family-lab Pine was never saved to
disk, so V45's F6 is a *reconstruction* (20-bar range extreme, ADX < 20), not
the identical code. It is tighter than the original — 12.8 fills/day pooled
against 18.7 — and it comes out 4/4 rather than 3/4. The overlap and
decomposition results are robust to that (they are about set membership, and
a tighter F6 can only understate the overlap of the looser one by at most the
difference in arm counts), but the F6 expectancies here should not be quoted
against the family table as if they were the same measurement.

---

> ## RETRACTION — added after the fold-C test
>
> **The statistical half of the evidence below did not survive out-of-sample and
> is retracted.** `FOLD_C_RESULTS.md` records the test in full. In short:
>
> - The +0.334R / 4-of-4 L1 result was measured on MGC and MNQ only — the two
>   instruments this project was developed on. On ten instrument × direction
>   cells across four complexes it falls to +0.132R, and the honest kept-vs-
>   discarded test separates in 6/10 cells with a 90% CI containing zero.
> - On the sealed test period (2026-08-09 → 08-31) the frozen model returned
>   **−0.074R**, failed every pre-registered gate criterion, and the bias
>   filter's kept-vs-discarded spread **inverted** to −0.207R.
> - §4 below ("adding HTF bias alignment improves the identical event stream
>   4/4") is therefore **withdrawn as evidence of edge**, as is the §4 comparison
>   claiming L1 beats F6.
> - A further defect: room ≥ 10R was silently on in every V44 rung, so "sweep
>   only" was never sweep-only. With room switchable, room is worth 3–4× what
>   bias is worth (`PHASE4_RESULTS.md` §2).
>
> **Conclusion A still stands, on structural grounds, not statistical ones.**
> The confusion matrix in §3, the fact that F0's limit at the swept level makes
> every fill a fade by construction, F0's mixed arm composition (§5) and the
> F0/F6 disjointness (§6) are all descriptive facts about the engine and the
> event stream. None of them depended on the bias edge being real. What is gone
> is the claim that conditioning on bias *recovers* an edge — it does not.

## 7. Conclusion: **A — representation problem**

The human's continuation process is real, is the majority of their stated
process, and **is present in the data as a positive, 4/4-consistent edge**. My
event definitions could not express it:

1. **Wrong entry location.** F0's limit sits *at* the swept level, so it fills
   on the return to it. Every F0 fill is mechanically a fade. The human's
   continuation entry is at a *different* structure — a zone on the far side,
   reached by the retracement *away* from the sweep. The engine has no way to
   place that order.
2. **No directional conditioning.** F0 armed on both sides of the HTF trend and
   averaged a continuation trade with its own opposite. Adding the single
   condition the human states first in every narrative — "bias set before the
   day" — recovers +0.153R in 4/4 cells.
3. **Missing arming case.** A pure trend leg with no sweep (N1) arms nothing.

So the earlier reading — "fade-at-extreme families work, continuation families
do not" — was a statement about **my encodings**, not about the market. The
continuation families I built (F1 breakout, F2 failed breakout, F3 displacement
retest, F5 trend pullback, F7 opening range) all failed; a continuation model
built the way the human describes it (bias first, then the event) does not.

### Why not B

B would require the human's process to be genuinely different from the
strongest statistical edge available. It is not: conditioning the *identical*
event stream on the human's own first filter produces the strongest,
most sign-consistent result measured in this project so far (+0.334R, λ 0.097,
t +2.36, 4/4), ahead of the mean-reversion family that had been winning.

### Why not C

C would require the human's own process to be mostly mean-reversion. Their
written narratives say the opposite in their own words, 4 of 6 trades are
continuation by stated thesis, and the two reversal trades are exactly the two
the bot already reproduces. C is contradicted by the primary source.

---

## 8. What is NOT established — read this before using any of it

- **One window, two instruments.** 72 days, MGC and MNQ 5m. No temporal
  out-of-sample, no walk-forward, no parameter perturbation on L1 yet. The 4-cell
  sign gate is a robustness check, not a substitute for out-of-sample.
- **L1 was tested on the data that generated the hypothesis.** t = +2.36 on
  n = 342 in-sample is suggestive, not established. This is exactly where
  winner's curse lives.
- **The human's literal entry does not fill.** L4 places the limit at the
  displacement 50% — the location the human describes — and gets **9 fills from
  605 arms (~1.5%)**. Whatever the human is doing to get filled there, a resting
  limit at the midpoint is not it. This part of the representation is still wrong.
- **My encodings of "reclaim" and "displacement" carry no edge** (0/4 and 3/4 with
  a negative mean). Either the conditions do not matter or I have encoded them
  badly; the ablation cannot distinguish those, and L3/L4 are too thin (39 and 9
  fills) to conclude anything.
- **The human sample is 6 trades and survivorship-skewed** — five winners and one
  loss. If their *losing* trades are disproportionately continuation, the realised
  process is closer to mean-reversion than the narratives suggest. I have exactly
  one loss note and it is a reversal. This is the single biggest weakness in the
  A/B/C determination and it cannot be fixed without more losing trades.
- **No winner selected.** L1 and F6 are ~90% disjoint and both survive; that is a
  reason to evaluate them together later, not a reason to declare either now.

# Fold C — the sealed test. The frozen model failed.

Test period **2026-08-09 → 2026-08-31**, run once, on the specification frozen
and committed in `PHASE4_RESULTS.md` §3 before the period was opened. No
re-specification followed.

---

## 1. Primary result

**Config 4 — sweep + B1 (4H EMA20/50) bias + room ≥ 10R.**

| | |
|---|---|
| pooled E[R] | **−0.074R** |
| n | 182 |
| t | −0.43 |
| 90% CI | **[−0.360, +0.211]** |
| cells positive | 4 of 7 populated |
| cells that never armed | **3 of 10** |

| gate criterion (Amendment 1) | |
|---|---|
| pooled E[R] > 0 | **FAIL** |
| pooled one-sided t ≥ +1.5 | **FAIL** |
| ≥ 7 of 10 instrument cells positive | **FAIL** |
| ≥ 6 of 8 complex cells positive | **FAIL** |

**The model failed on every criterion.**

Per the protocol's stated consequence: *the ex-ante bias effect seen in-sample
did not survive out-of-sample.* The +0.334R / 4-of-4 L1 result is retracted, and
the retraction has been written into `CONTRADICTION_RESOLUTION.md`, the document
that reported it.

## 2. All eight configs, for completeness

| config | pooled | cells + / populated | n | t |
|---|---|---|---|---|
| 1 sweep only | +0.024 | 5/10 | 1,417 | +0.37 |
| 2 + bias | −0.010 | 3/7 | 726 | −0.12 |
| 3 + room | +0.043 | 6/10 | 363 | +0.33 |
| **4 + bias + room (primary)** | **−0.074** | **4/7** | **182** | **−0.43** |
| 5 + bias + displacement | −0.243 | 1/7 | 211 | −1.67 |
| 6 + bias + reclaim | −0.024 | 3/7 | 557 | −0.24 |
| 7 + bias + room + displacement | −0.141 | 2/6 | 28 | — |
| 8 full | −0.060 | 2/5 | 26 | — |

### Development vs test

| config | A+B | C | change |
|---|---|---|---|
| 1 sweep only | −0.100 | +0.024 | +0.124 |
| 3 + room | +0.050 | +0.043 | **−0.007** |
| 4 + bias + room | **+0.132** | **−0.074** | **−0.206** |

Two things to read here, and they point in different directions:

- **The bias effect inverted.** +0.132 → −0.074. It did not merely shrink.
- **Room was the only component that held.** +0.050 → +0.043, essentially
  unchanged. But its t was +0.76 in development and +0.33 in test — **stable and
  never significant.** Stability is not the same as edge, and I am not going to
  present it as one.
- The in-sample −0.100R on the raw sweep also did not persist (+0.024). So the
  *negative* finding was window-specific too. The honest summary is that on a
  22-day out-of-sample window, **none of these conditions demonstrates anything.**

## 3. Did the bias filter separate out-of-sample?

The kept-vs-discarded test, run only on cells where both populations exist:

| cell | kept | n | discarded | n | spread |
|---|---|---|---|---|---|
| MNQ long | +0.082 | 84 | −0.200 | 67 | +0.282 |
| MNQ short | +0.060 | 72 | −0.051 | 92 | +0.111 |
| MCL long | −0.069 | 102 | +0.481 | 39 | −0.550 |
| MCL short | −0.447 | 57 | +0.440 | 89 | −0.887 |
| **pooled** | **−0.068** | 315 | **+0.139** | 287 | **−0.207** |

**Separates in 2 of 4 testable cells, and the pooled spread is negative**:
−0.207R, SE 0.200, t −1.03, 90% CI [−0.536, +0.122]. The bias-aligned population
did *worse* than the bias-opposed one out-of-sample. The CI still spans zero, so
this is not evidence that the filter is harmful — it is evidence that **it does
nothing measurable.**

## 4. The structural problem the test exposed, which matters more than the number

**In 6 of 10 cells the 4H trend never changed direction across the whole 22-day
period.** Three cells armed nothing at all (MGC short, SIL short, 6E short) and
three armed on every single sweep (MGC long, SIL long, 6E long — where config 2
is byte-identical to config 1). Only MNQ and MCL saw both directions.

That is not a sampling accident, it is what the feature *is*: a 4H EMA20/50
cross flips a handful of times per quarter. **It is a regime label, not a
per-trade decision variable.** A model built on it cannot answer "what is my
bias at 09:42 today" with anything that varies at the frequency trades are
taken — for weeks at a time it just says "long" and nothing else.

This also means the pre-registered gate was **unachievable as designed**: "≥ 7 of
10 cells positive" cannot be met when only 7 cells exist. That is a flaw in my
test design, not a property of the market, and it is mine to own. A directional
filter needs cells where both directions occur, which needs either a longer test
window or instruments chosen for having changed trend within it.

## 5. Phase 5 — reclaim and displacement, before judging the features

The instruction was not to conclude these are useless until their definitions are
checked against the actual process. Where that stands:

- **Displacement**: harmful in development (0/10 cells, −0.322R, t = −5.24 on
  803 fills) and still negative in test (−0.243, 1/7). It also nearly empties the
  sample when combined with room — 97 fills across 10 development cells,
  28 in test — reproducing the F3 and L4 finding that after a ≥1.5× ATR bar,
  price does not return to the level.
- **Reclaim**: a null in both — 5/10 and −0.004R in development, 3/7 and −0.024
  in test. Not harmful, not useful.

**I cannot complete the representation check.** It requires human-labelled
instances of "this was a reclaim / this was displacement" to compare against the
machine labels, and the human sample is 6 trades with no such annotations
(`HUMAN_TRADE_REGISTER.md`). Making up labels would be exactly the fabrication
the brief prohibits.

One piece of real evidence does exist and points the same way: the user's own
ex-ante plan of 2026-08-31 (three hand-written alerts) specifies **two price
zones and a direction for one of them, and mentions no confirmation event at
all** — no displacement, no reclaim, no structure break. It is location-first.
That is weak evidence (one plan), but it is evidence, and it is consistent with
room-to-destination mattering and confirmation events not.

## 6. Phase 9 — can the system determine direction before the trade?

The question was: *using only information available at time t, can the system
establish a directional thesis reliably enough to distinguish continuation from
reversal?*

**On this feature set, no.**

- Six ex-ante directional models were specified in advance and measured. The best
  of them (4H trend) beat the no-filter control by +0.082R in development, did
  not separate kept from discarded at any conventional confidence (t = +1.22,
  90% CI containing zero), and **inverted out-of-sample** (−0.207R spread,
  t = −1.03).
- Two of the six are measurably worse than useless: previous-day structure
  (−0.249R, t = −2.11) and HTF displacement (+0.002R, 3/10 — pure noise).
- The one that ranked best is **too slow-moving to be a trade-level decision**
  (§4). It labels regimes, not trades.

So the answer to the fork the brief set is the second branch: **direction should
remain conditional, and the work moves to whether setup selection can compensate.**
There is a concrete reason to think it can, from evidence that is not affected by
this failure:

- **Room-to-destination is the only component that survived out-of-sample intact**
  (+0.050 → +0.043), and it is direction-agnostic — it asks "is there space to
  the next opposing level", not "which way is the market going".
- **The human's own ex-ante plan works the same way**: mark the locations, let
  price choose the direction (`HUMAN_TRADE_REGISTER.md` §4).
- **F0 and F6 are 93% disjoint** and both survived their own tests, which is what
  a regime → family structure would look like.

That is Phase 8's hypothesis, and it is now the best-supported direction. It is
**not** established — nothing here is — and I am not going to build on it until
it is tested the same way this was.

## 7. What I am not doing

Not re-specifying the bias model and re-running fold C. Not searching for a
config that survives. Not presenting room's +0.043R as a result — it is a
non-significant number that happened not to move. Not presenting configs 7 and 8
(26–28 fills) as anything at all.

The pre-registered outcome for this test was failure or success, and it failed.

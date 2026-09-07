# Phase 13C — can F1, F3 and M5 be recovered without using performance?

Specification research only. **No implementation, no backtest, no optimisation,
no parameter sweep, no P&L, no ranking of any definition by profitability.** No
existing strategy file was modified. Nothing below was chosen because it looked
like it would work; the only tools used are the project's own wording, its frozen
definitions, and internal consistency.

---

## 0. Correction carried in from Phase 13B

Phase 13B's summary table listed **F5 as "sweep→CHOCH delay"**. That was a
transcription error on my part: in Phase 13 §3, **F5 is the stop buffer** and the
delay is **M5**. The owner's correction is adopted and the mapping is restored:

- **F5 — stop = sweep extreme ± 0.20 × ATR** (V49), preserved. §14's literal
  wording is the bare sweep extreme; V49's ±0.20×ATR is a strict superset that
  only widens the stop, so there is no direct contradiction requiring separate
  clarification, and none is raised here.
- **F6 — ATR = the existing 5m ATR framework**, preserved.
- **M5** is the sweep→CHOCH timing question, addressed in §3 below.

---

## 1. F1 — CHOCH swing selection

### 1.1 Every source that speaks to it

| # | source | exact wording | type |
|---|---|---|---|
| S1 | owner's §5 (Phase 13 specification) | close beyond "the relevant opposing **internal structure**" | authoritative spec |
| S2 | trade note T2, via `MANUAL_PROCESS_ANALYSIS.md:16` | "CHOCH → retest → BOS → imbalance retest" | primary narrative |
| S3 | trade note T2, via `MANUAL_PROCESS_ANALYSIS.md:15` | "waited for price to **retest the CHOCH**" | primary narrative |
| S4 | `HUMAN_TRADE_REGISTER.md:41` | "sweep → rally → OB tap → **1m CHOCH**" | reconstruction of T2 |
| S5 | `HUMAN_RECONSTRUCTION.md:10` | "swept the Asia LOW → rallied to an OB, **1m CHOCH** → CONTINUATION short" | reconstruction of T2 |
| S6 | `V24_V25_ICT_RESULTS.md:18` | "close through the **opposing swing** with displacement" | third-party model, source code destroyed (13B §A2) |

`internal structure` appears nowhere in the repository except in my own Phase 13
restatement of S1. There is no project glossary defining it, and no code has ever
implemented a CHOCH (13B §A4). **The corpus above is complete.**

### 1.2 What the sources do establish

- The CHOCH is a **price level that can be retested** (S3). Whatever swing it
  breaks, that swing's price is carried forward and price returns to it.
- In the one narrated instance (S4/S5) the order is: **sweep of a low → rally →
  CHOCH**, and the trade is a short. So the swing the CHOCH breaks is a swing
  **low**, and it is broken **downward**, ending the rally.

### 1.3 Conceptual evaluation of the three Phase 13 candidates

No performance was computed for any of these. They are judged on whether they are
internally coherent with the already-frozen §1 sweep definition and with S3–S5.

**C1a — the most recent confirmed opposing swing existing at the sweep bar.**

| | |
|---|---|
| mechanical rule | at the sweep bar, take the most recent confirmed opposing pivot; CHOCH = first causal close beyond it |
| causal | yes — the pivot is confirmed at `pivotBar + swLen`, before the sweep bar |
| eligible pivot | one, fixed at the sweep bar |
| eligible from | the sweep bar |
| matches the stated hypothesis | **no** |
| new assumption | none needed, but it is incoherent (below) |

**Eliminated on construct validity, not performance.** In the bias-aligned case
that the whole hypothesis is about (S5: bearish bias, sweep of a *low*, short),
the "opposing" structure for a bearish CHOCH is a swing **low**. Price has just
traded *below* the swept level. Any pre-existing swing low near it has already
been taken out by the sweep itself, so "closing below it" is not a change of
character — it is a restatement of the sweep. C1a makes CHOCH a near-tautology of
the event that precedes it.

**C1b — the most recent confirmed opposing swing as of each bar, re-evaluated
forward.**

| | |
|---|---|
| mechanical rule | on every bar after the sweep, the reference is the most recent opposing pivot confirmed so far; CHOCH = first causal close beyond the current reference |
| causal | yes, provided only pivots confirmed strictly before the break bar are eligible |
| eligible pivot | rolling; in practice the last swing low of the counter-rally |
| eligible from | `pivotBar + swLen` of that pivot |
| matches the stated hypothesis | **yes** — this is the swing the rally in S4/S5 creates, and its price is a level that can be retested (S3) |
| new assumption | **yes, one**: that eligibility is restricted to pivots whose pivot bar falls **after** the sweep bar |

**C1c — the extreme opposing swing formed between the sweep and now.**

| | |
|---|---|
| mechanical rule | reference = the lowest confirmed swing low (bull case: highest swing high) formed since the sweep; CHOCH = close beyond it |
| causal | yes |
| eligible pivot | one, the extreme |
| eligible from | its confirmation bar |
| matches the stated hypothesis | **no** |
| new assumption | none needed, but it degenerates (below) |

**Eliminated on construct validity.** After a low sweep, the lowest swing low
formed since the sweep sits at or immediately above the sweep extreme. Requiring
a close beyond it means requiring price to give back the entire counter-rally and
return to the sweep extreme. That is a full retrace, not a change of character,
and it would fire *after* the entry the process describes rather than before it.

### 1.4 Verdict on F1

Two of the three candidates are eliminated by internal consistency with the
frozen sweep definition — an argument available without any P&L — leaving
**C1b (restricted to post-sweep pivots)** as the only coherent reading of S1–S5.

That is a narrowing, **not a recovery**. C1b is an interpretation of a two-clause
narrative sentence; nobody ever wrote the rule down, and the one implementation
that contained something like it was overwritten and is unrecoverable (13B §A2).
Three sub-decisions inside C1b are still open and cannot be read off any source:
whether eligibility starts at the sweep bar or at the sweep's extreme bar;
whether the reference resets after each new confirmed pivot or latches to the
first one; and whether a wick beyond the reference invalidates the pending CHOCH.

## **F1 = UNKNOWN**

Adopting C1b would be an **explicit project decision**, and it stays inert until
F3 exists, because "the most recent confirmed pivot" has no referent until a
pivot strength is fixed.

---

## 2. F3 — LTF pivot strength

### 2.1 Everything the project contains

| source | value | timeframe |
|---|---|---|
| `V46`–`V52` (`swLen`) | **10** | 5m |
| `V8_3`/`V11_1`/`V12`/`V13` (`pivotLen`) | **5** | 15m |
| `V17_XAU_sweep.pine:36-37` (`pivL`/`pivR`) | **5 / 3** | 15m |
| V24/V25 MSS | unrecorded — source destroyed | 15m |
| trade notes | "1m OB", "1m CHOCH", "1m inverted + 3m engulfing" — **no swing length, no fractal degree** | 1m/3m |
| ICT/SMC terminology used in the project | "internal structure", "opposing swing", "unmitigated OB" — none of which carries a number | — |
| commit history, comments, experiment notes | nothing (13B §A4) | — |

**No LTF pivot strength has ever been written down in this project.** There is
also no scaling convention to extend, because the two documented values disagree
in wall-clock terms: `swLen 10` on 5m is 50 minutes of one-sided lookback,
`pivotLen 5` on 15m is 75. Extending "the project convention" to 1m would give
50, or 75, depending which file you extend — which is not a convention.

### 2.2 What *can* be established without inventing a number

Two bounds, both derived from already-frozen constants:

1. **Degree bound.** The LTF structure must be finer than the 5m structure the
   sweep engine already uses, or the "LTF" layer is not lower-timeframe in any
   meaningful sense: `swLen_LTF × LTF_minutes < 50`. That is `swLen < 50` on 1m
   and `swLen < 17` on 3m.
2. **Feasibility bound.** Under §3 below, the whole sweep→CHOCH leg must fit in
   60 minutes. A pivot costs `swLen` bars to confirm, the counter-move must build
   it, and the break must then occur — so roughly `2 × swLen` bars of the window
   are consumed before a CHOCH is even possible. That puts 1m at `swLen ≲ 25` and
   3m at `swLen ≲ 8`.

These narrow the range. **They select nothing.** Every value inside them is
equally supported by the documentation, which is to say: not at all.

## **F3 = UNKNOWN**

No value is invented here, and none is preferred. This is the single parameter
Phase 13 §3 flagged as "most likely to be mistaken for optimisation later", so it
must be fixed in writing by the owner before any run, not discovered by one.

---

## 3. M5 — sweep → CHOCH timing

### 3.1 Is there an authoritative rule?

No. No source states a sweep→CHOCH bound (13B §A4). The nearest neighbour,
`bosMaxBars = 15`, is a sweep→**BOS** bound on a **15m** chart in a construct
with no CHOCH beat at all, and Phase 12 already ruled it a different construct.

### 3.2 But an existing frozen limit already governs it

The frozen sequence is strictly ordered:

```
SWEEP → LTF CHOCH → DISPLACEMENT → BOS → FVG → RETEST → ENTRY
```

and the frozen §10/§7 constants, verified in `V44_continuation_ablation.pine:118-124`:

```pine
rng = high - low
dispNow  = rng > dispMin * atr and (isLong ? close > low + 0.6*rng : close < low + 0.4*rng)
freshSweep = not na(swpLvl) and (bar_index - swpBar) <= dispWait   // dispWait = 12
dispFire = dispNow and freshSweep and swpRec
```

`dispWait = 12` caps **sweep → displacement** at 12 bars of 5m = **60 minutes**.
Because CHOCH precedes displacement in the sequence:

> sweep → CHOCH  ≤  sweep → displacement  ≤  60 minutes

So the sweep→CHOCH interval is **already bounded, by a constant that is already
frozen**, at 60 LTF minutes = 60 bars on 1m, 20 bars on 3m. No new number is
required, and inventing one would only tighten a bound the architecture already
enforces.

Two conditions this rests on, both of which are already the frozen spec: the
sequence is enforced **in order**, and displacement is **mandatory** rather than
optional. If either is relaxed later, the bound disappears with it.

The other two constants do **not** govern this leg: `retBars = 24` is the retest
window after the FVG forms, and `maxBars = 144` is the outcome timeout — both sit
downstream of the CHOCH.

## **M5 = RECOVERED (derived, not newly specified)**

Governing rule: the existing `dispWait = 12` (5m) already caps sweep→CHOCH at
60 minutes. Whether the owner additionally wants a *tighter, independent* cap is
a decision, not a gap — the specification is complete without one.

---

## 4. F4 — FVG selection

### 4.1 The three things that must not be conflated

**A. Documented intended rule** — owner's §17: *"prefer the FVG directly
associated with the displacement that caused the structural break."* This is the
owner's own specification, so it is authoritative. `V24_V25_ICT_RESULTS.md:18`
independently records the same rule from the published ICT model ("retracement
into the fair value gap **the displacement leg leaves**"), which corroborates the
intent even though that implementation is destroyed.

**B. Existing implementation behaviour** — `V8_3_XAU_trend_range.pine:176-196`
selects, in effect, the **most recent unfilled** FVG.

**C. Accidental implementation artifact** — B *is* C. V8.3 holds one bull and one
bear FVG in scalars (`bullFvgTop`/`bullFvgBot`) and overwrites them on every new
gap. Nothing selects; the last write wins. It was never described as a rule
anywhere. Per the owner's ruling it is rejected as an artifact and is **not** the
project's FVG-selection rule.

### 4.2 §17 is mechanically determinate under the already-frozen definitions

Phase 13 recorded M4 on the premise that "if the displacement leg spans three
bars it can create two or three FVGs". **That premise does not hold against the
frozen §7.** As the code above shows, displacement is evaluated on a **single
bar** — `rng = high - low` of the current bar — so `dispFire` identifies exactly
one bar, not a leg.

The frozen §11 FVG is a three-candle pattern evaluated at bar `t`
(`bullFvgNow = low > high[2]`), spanning `t-2 … t` with **middle candle `t-1`**.
"The FVG directly associated with the displacement" therefore resolves to:

> **the FVG whose middle candle is the displacement bar** — i.e. the gap tested
> at `dispBar + 1`, with zone `[high[dispBar-1], low[dispBar+1]]` for a bull and
> `[high[dispBar+1], low[dispBar-1]]` for a bear.

That object is **unique by construction**: at most one bull FVG and one bear FVG
can have a given bar as their middle candle. The multiplicity problem M4 assumed
does not arise. Nothing was chosen here — the rule falls out of §7 + §11 + §17.

## **F4 = RECOVERED (derived from frozen §7, §11 and §17)**

One residual decision, and it is not a selection rule: a large-range bar does not
have to leave a gap, so the displacement bar may have **no** associated FVG. The
coherent reading is that the setup simply does not complete and no entry occurs.
Any *fallback* to a different FVG would reintroduce exactly the selection problem
§17 was written to avoid, so a fallback should be adopted only deliberately. This
derivation is also conditional on §7 remaining a single-bar condition; if
displacement is ever redefined as a multi-bar leg, F4 reopens.

---

## 5. Facts and assumptions

| Item | Status | Definition | Source | Fact or assumption |
|---|---|---|---|---|
| §1 sweep | DOCUMENTED | wick ≥ 0.10×ATR beyond PDH/PDL, Asia H/L or 10-bar pivot, close back inside | V49 | fact |
| §4 pivot method | DOCUMENTED | `ta.pivothigh/low(src, swLen, swLen)`, confirmed at `pivotBar + swLen` | V49 / V51 Gate A (0 lag mismatches, 7,454 candidates) | fact |
| §7 displacement | DOCUMENTED | single bar: `range > 1.50×ATR` and `close > low + 0.6×range` (bull) / `close < low + 0.4×range` (bear) | `V44_continuation_ablation.pine:121-122` | fact |
| §10 delays | DOCUMENTED | `dispWait 12`, `retBars 24`, `maxBars 144`, all 5m | V44–V52 | fact |
| §11 FVG | DOCUMENTED | `low > high[2]` / `high < low[2]`; zone `[high[2], low]` / `[high, low[2]]` | `V8_3:176-194` | fact |
| §12 retest / fill | DOCUMENTED | `low <= bullFvgBot` marks the bull FVG filled | `V8_3:189` | fact |
| §15 outcome | DOCUMENTED | 5R target, −1R stop, adverse excursion first, 144-bar timeout, $3.00 drag | V47–V52 | fact |
| **F5** stop buffer | DOCUMENTED | sweep extreme ± 0.20 × ATR | V49; reaffirmed by owner, Phase 13C brief | fact |
| **F6** ATR frame | EXPLICIT PROJECT DECISION | the existing **5m** ATR framework | owner, Phase 13C brief | decision |
| **F2** BOS swing | EXPLICIT PROJECT DECISION | most recent confirmed opposing pivot available at that point; causal close beyond it; the CHOCH pivot is **excluded** from BOS eligibility | owner, Phase 13C brief; shape corroborated by `V8_3:88-174` (A1) | decision |
| **M5** sweep→CHOCH | RECOVERED | already bounded at **60 minutes** by the frozen `dispWait = 12` (5m), because CHOCH precedes displacement in the ordered sequence | derived from §7/§10 + the §-sequence; code at `V44:118-124` | fact (derived) — conditional on the sequence staying ordered and displacement staying mandatory |
| **F4** FVG selection | RECOVERED | the FVG whose **middle candle is the displacement bar**; unique by construction | derived from §7 + §11 + §17 | fact (derived) — conditional on §7 staying single-bar; behaviour when no such FVG exists is still a decision |
| **M2** BOS swing rule shape | RECOVERED | most recent confirmed opposing pivot, break on **close**, causal | `V8_3_XAU_trend_range.pine:88-174` — but at `pivotLen 5` on **15m**, not at any LTF | fact about the 15m construct; its transfer to LTF is F2's decision |
| **F1** CHOCH swing | **UNKNOWN** | narrowed to C1b (most recent confirmed opposing pivot, restricted to pivots formed after the sweep, re-evaluated forward) by eliminating C1a and C1c on construct validity; three sub-decisions remain open | S1–S5; elimination argument in §1.3 | **assumption** if adopted — no source states it |
| **F3** LTF pivot strength | **UNKNOWN** | no value exists; bounded only to `swLen ≲ 25` on 1m and `≲ 8` on 3m by the degree and feasibility arguments in §2.2 | bounds derived from `swLen 10`/5m and `dispWait 12` | **assumption** if chosen — no source states it |
| V8.3 "most recent unfilled FVG" | *(not a status — rejected)* | scalar-overwrite behaviour | `V8_3:176-196` | **implementation artifact**, rejected by owner; must not be cited as the documented rule |
| V24/V25 MSS rule and its `k` | **UNKNOWN** | "close through the opposing swing with displacement, `range > k × stdev(range)`" | `V24_V25_ICT_RESULTS.md:18`; Pine source overwritten in the single saved script slot | **unrecoverable** — recorded, never reconstructed |

### One discrepancy to record, not to resolve here

The primary narrative (S2) reads **"CHOCH → retest of the CHOCH → BOS → entry on
the retest of the imbalance the BOS left behind"**, and S3 says the trader
"waited for price to **retest the CHOCH**". The frozen §-sequence has no
retest-of-the-CHOCH beat: it goes CHOCH → displacement → BOS → FVG → retest. The
two are not the same process — the narrative contains an extra confirmation step,
and its entry reference is described relative to the BOS's imbalance. This is
flagged as a fidelity question for the owner. It is **not** treated as a gap, and
nothing here assumes an answer.

---

## 6. Final decision

# STILL INCOMPLETE

Phase 13C closed two of the five gaps without inventing anything: **M5** turned
out to be already governed by a frozen constant, and **F4** turned out to be
mechanically determinate once §7's single-bar displacement is taken literally.
With F2, F5 and F6 frozen by the owner, the specification is complete except for:

**Unresolved decisions required from the strategy owner — two:**

1. **F1 — CHOCH swing selection.** Adopt C1b (most recent confirmed opposing
   pivot, eligibility restricted to pivots formed after the sweep, re-evaluated
   forward), or supply a different rule. If C1b is adopted, three sub-decisions
   come with it: (i) eligibility starts at the sweep bar or at the sweep's
   extreme bar; (ii) the reference rolls to each newly confirmed pivot or latches
   to the first one; (iii) a wick beyond the reference does or does not
   invalidate a pending CHOCH.
2. **F3 — LTF pivot strength.** One integer, applied to both 1m and 3m, fixed in
   writing before any run. Nothing in the project selects it; the bounds in §2.2
   are the most that can be said honestly.

Two smaller items travel with them and need a yes/no rather than a value:
whether a displacement bar with **no** associated FVG voids the setup (§4.2), and
whether the narrative's **retest-of-the-CHOCH** beat belongs in the sequence (§5).

No implementation, no backtest, no optimisation, and no definition ranked by
profitability. F1 and F3 remain UNKNOWN and are not filled in here.

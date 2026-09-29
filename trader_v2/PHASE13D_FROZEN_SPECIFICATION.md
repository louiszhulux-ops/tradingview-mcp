# Phase 13D — frozen specification and final mechanical validation

Validation only. **Nothing implemented, no backtest, no optimisation, no
parameter sweep, no performance number, and no existing strategy file changed.**
The single question answered here is whether every step of the frozen sequence
can be expressed mechanically and causally with no remaining ambiguity.

---

## 1. Status labels — recorded as instructed

| item | status | one-line content |
|---|---|---|
| **F1** CHOCH swing selection | **EXPERIMENTAL HYPOTHESIS** | C1b, post-sweep pivots only, rolling reference, close-through required |
| **F2** BOS swing | **EXPLICIT PROJECT DECISION** | most recent confirmed opposing pivot available after CHOCH, CHOCH pivot excluded, causal close |
| **F3** LTF pivot strength | **EXPERIMENTAL HYPOTHESIS** | `swLen = 3` on both 1m and 3m; `ta.pivothigh/low(src, 3, 3)`, confirmed at `pivotBar + 3` |
| **F4** FVG selection | **RECOVERED / DERIVED** | the three-candle FVG whose middle candle is the displacement candle; no fallback |
| **M5** sweep→CHOCH timing | **RECOVERED / DERIVED** | governed by the existing `dispWait = 12` 5m bars; 60 bars on 1m, 20 on 3m |
| **F5** stop | **DOCUMENTED V49** | long: sweep low − 0.20×ATR; short: sweep high + 0.20×ATR |
| **F6** ATR | **DOCUMENTED EXISTING ARCHITECTURE** | the 5m ATR(14) framework; the LTF layer computes no ATR of its own |

**F1 and F3 are not described as recovered anywhere in this document.** Both are
hypotheses chosen to be tested, and they are frozen before the first run so that
whatever comes back is reported as-is.

---

## 2. The frozen sequence, expressed mechanically

Notation: the sweep is a 5m event on chart bar `s`. LTF bars are the
`request.security_lower_tf` constituents of chart bars, `L` denotes an active
reference price, `swLen = 3`, and `isLong` follows V49 (`dirMode`).

**Direction pairing is already fixed by F5 and V49** and is not re-opened here:
`isLong` ⇔ the swept level is a **low**, stop below it; short ⇔ a swept **high**,
stop above it. Consequently the "opposing" structure is **pivot highs for a long**
(the counter-structure to an up-move) and **pivot lows for a short**.

| # | beat | mechanical rule | causal? |
|---|---|---|---|
| 1 | **sweep arms** | unchanged V49 §1: wick ≥ 0.10×ATR beyond PDH/PDL, Asia H/L or the 10-bar 5m pivot, close back inside. Stop `sp = isLong ? low − 0.20×atr : high + 0.20×atr` fixed at bar `s` | yes — decided at the close of bar `s` |
| 2 | **CHOCH eligibility opens** | eligible references are LTF pivots (`ta.pivothigh/low(src,3,3)`) whose **pivot bar** lies in the LTF constituents of chart bars `s+1 …`; a pivot becomes usable only at its confirmation bar, `pivotBar + 3` | yes — pivot value equals `src[3]` at confirmation (V51 Gate A, 0 mismatches in 7,454 candidates) |
| 3 | **active CHOCH reference** | `L_choch` = the most recent **confirmed eligible** opposing pivot as of the current LTF bar; it rolls forward each time a newer eligible opposing pivot confirms | yes — only pivots confirmed strictly before the current bar are eligible |
| 4 | **CHOCH fires** | first LTF bar whose **close** is beyond `L_choch` (long: `close > L_choch`; short: `close < L_choch`). A wick beyond without such a close does nothing. On firing, `L_choch` **freezes** and is excluded from BOS eligibility | yes — uses only the current bar's close |
| 5 | **CHOCH retest** | on LTF bars strictly after the CHOCH bar: `retested = isLong ? low <= L_choch : high >= L_choch` — V49's own fill test, verbatim, same polarity, zero tolerance | yes |
| 6 | **BOS reference** | `L_bos` = the most recent confirmed opposing pivot as of the current LTF bar, **excluding the frozen CHOCH pivot**; rolls forward on each new confirmation | yes |
| 7 | **BOS fires** | first LTF bar **after the CHOCH retest** that both (a) closes beyond `L_bos` in the trade direction and (b) satisfies §7 displacement on that same candle: `rng = high − low`, `rng > 1.50 × ATR₅ₘ` and `isLong ? close > low + 0.6×rng : close < low + 0.4×rng` | yes — current bar only |
| 8 | **deadline** | the BOS/displacement candle must fall within `dispWait = 12` chart bars of `s` (M5). Everything in beats 2–7 is therefore inside **60 minutes** — 60 LTF bars on 1m, 20 on 3m. If the deadline passes, the candidate expires | yes |
| 9 | **FVG identified** | the three-candle FVG whose **middle candle is the BOS/displacement candle** `d`: bull `low[d+1] > high[d−1]`, zone `[high[d−1], low[d+1]]`; bear `high[d+1] < low[d−1]`, zone `[high[d+1], low[d−1]]`. If that gap does not exist, the setup is **INVALID**, with no fallback | yes — known one LTF bar after `d` |
| 10 | **entry** | entry level `E` = the **far edge** of that FVG (§12: bull fills at `low <= bullFvgBot = high[d−1]`; bear at `high >= bearFvgTop = low[d−1]`). Fill test and the `retBars = 24` expiry run on **5m bars**, exactly as V49 | yes |
| 11 | **validity band** | unchanged V49: `r = |E − sp|`, fill accepted only if `0.05 ≤ r/ATR₅ₘ ≤ 3.00`; otherwise the candidate is discarded | yes |
| 12 | **outcome** | unchanged §15: +5R target, −1R stop, **adverse excursion checked first**, `maxBars = 144` timeout, $3.00 drag as `cR = costUSD/(r × ptv)`. Evaluation starts on the bar **after** the fill bar, as V49's loop order already enforces | yes |

---

## 3. The eight questions that could have been ambiguities, and the frozen rule that settles each

Nothing below introduces a tolerance, a penetration rule, a timeout or a
parameter. Each item names the already-frozen rule that determines it.

**3.1 CHOCH-retest tolerance — settled by V49's own retest machinery.**
`V49_multi_level_ledger.pine:198-200` is a level-based touch test:

```pine
hit = isLong ? low <= L : high >= L
```

It is a **price level**, not a zone, and it carries **zero tolerance**. It
transfers to the CHOCH level verbatim, and — this is the part worth checking —
*with the same polarity*. For a long the CHOCH breaks a pivot **high** upward, so
its retest is price coming back **down**: `low <= L`, which is exactly V49's long
branch. For a short it is `high >= L`. No new rule, not even a sign flip.

The 0.10×ATR proximity test from C2 Gate A is **not** used: it was built to count
level *maturity* touches, C2 is closed, and it is not part of the frozen sequence.
Using it would have been importing a tolerance the specification forbids.

**3.2 CHOCH-retest timeout — already bounded, so none is added.**
The retest sits between CHOCH and BOS, and BOS is the displacement candle, which
M5 caps at `dispWait = 12` chart bars from the sweep. The retest is therefore
bounded at **60 minutes** by a constant that is already frozen. Binding
`retBars = 24` to this beat would have been attaching a documented number to an
undocumented beat — a new parameter wearing an old name. It is not done.

**3.3 Is the BOS candle the displacement candle? — entailed by F4's own wording.**
F4 says "the displacement condition identifies exactly one displacement candle"
and "if **that** displacement candle does not produce the required FVG, the setup
is INVALID". Invalidity is attached to *a candle*, not to a window expiring. Under
any reading where displacement is scanned for separately after the BOS, failure
would be a timeout rather than an invalidation, and step 6's "the BOS displacement
candle" would have no referent. So the BOS candle must itself satisfy §7. This
also keeps M5's derivation intact: displacement stays mandatory and stays ordered
after CHOCH.

Note the consequence, which is a real narrowing and is stated rather than
softened: a BOS close that does **not** meet the displacement threshold is not a
BOS for this experiment; the candidate simply continues to look for one until the
deadline.

**3.4 FVG entry price — settled by §12.**
§12's frozen fill trigger is the **far** edge (`low <= bullFvgBot`, where
`bullFvgBot = high[2]`; symmetrically `high >= bearFvgTop = low[2]`). The entry
level is that same far edge, so entry price and fill test are one object. No
choice between near edge, far edge and midpoint is being made here — §12 already
made it.

**3.5 FVG-retest window — `retBars = 24` needs no conversion.**
The FVG retest can be evaluated on **5m** bars with no loss, because a 5m bar's
low is the minimum of its LTF constituents' lows and its high the maximum: the
touch test `low <= E` gives the identical answer on either clock. So `retBars`
stays 24 **chart** bars exactly as V49 defines it, and the wall-clock conversion
question never arises. (The CHOCH retest at 3.1 is different and *must* be
evaluated on LTF bars, because its ordering relative to the BOS matters and both
can fall inside one 5m bar.)

**3.6 No penetration rule and no re-arm — by omission, deliberately.**
Nothing invalidates the setup if price passes back through `L_choch` after the
retest; the brief forbids inventing such a rule and none is added. Likewise the
**first** qualifying close is the CHOCH, the reference then freezes, and there is
no second attempt within the same sweep. Both readings add no machinery; the
alternatives would.

**3.7 "After the sweep bar" — expressible exactly under the data path.**
`request.security_lower_tf` delivers LTF values grouped by chart bar, so
"LTF bars belonging to chart bars `s+1` onward" is directly representable, with no
timestamp arithmetic and no partial-bar edge case. Eligibility therefore excludes
the sweep bar's own LTF constituents, as F1 requires.

**3.8 Outcome evaluation — unchanged, including its start bar.**
V49 runs the outcome loop (`st == 2`, line 175) **before** the fill loop
(`st == 1`, line 196), so a candidate filled on bar `t` is first evaluated on
`t+1`. That behaviour is preserved rather than re-derived, and it is the
conservative direction: same-bar stop-and-target races are not adjudicated.

---

## 4. Causality — checked step by step

Every beat consumes only information available at or before the bar on which it
fires:

- **Pivots.** `ta.pivothigh/low(src, 3, 3)` returns non-`na` at `pivotBar + 3`,
  and the value equals `src[3]` at that bar. This is the identical mechanism V51
  Gate A verified on 5m with **0 lag mismatches across 7,454 candidates**; only
  the timeframe and the length change, not the mechanism. Both the CHOCH and BOS
  references use confirmed pivots only, so neither can reference a swing the
  market has not yet finished forming.
- **Rolling references.** "Most recent confirmed" is evaluated per bar from
  already-confirmed pivots. There is no forward scan and no `lookahead_on`
  anywhere in the sequence.
- **Closes.** CHOCH (beat 4) and BOS (beat 7) both test the **current bar's
  close**, decided at that bar's close.
- **Touches.** Beats 5 and 10 test the current bar's high/low.
- **Displacement.** `rng` and the close-position clause are current-bar
  quantities; `ATR₅ₘ` is `ta.atr(14)` on completed chart bars.
- **FVG.** The gap whose middle candle is `d` is fully determined at `d+1`, one
  bar after the displacement — it is never known at `d`.
- **Outcome.** Starts the bar after the fill, adverse excursion first.

The known leakage trap for this family — counting a level's history from its
pivot bar instead of its confirmation bar — cannot occur here, because
eligibility is defined at `pivotBar + 3` throughout. The D0–D7 harness from V51
Gate A remains applicable and should be re-run against the LTF layer during
implementation.

---

## 5. Two consequences to measure, not to fix

Neither is an ambiguity and neither justifies changing a frozen value. Both are
recorded now so that if the event count comes back small, it is understood as a
predicted property of the frozen specification rather than a bug or a reason to
loosen anything.

1. **Displacement is measured against a 5m ATR (F6).** Beat 7 requires an LTF
   candle whose range exceeds `1.50 × ATR₅ₘ`. A 1m bar clearing 1.5× the 5-minute
   ATR is a genuine but uncommon event; on 3m it is less uncommon. This is the
   frozen combination of §7 and F6 and it stays exactly as frozen.
2. **The 60-minute deadline is tight against `swLen = 3`.** The earliest possible
   confirmed post-sweep pivot arrives at LTF bar 7 (pivot at bar 4, confirmed
   three bars later). That leaves 53 of 60 bars on 1m, but only **13 of 20 on 3m**,
   for CHOCH → retest → BOS. The 3m hypothesis is materially more constrained than
   the 1m one, which is a further reason to keep them reported as separate
   hypotheses rather than pooled.

The right response to either, if it bites, is to report the conversion rates from
the mechanical audit — not to widen a threshold.

---

## 6. Fidelity note recorded, not acted on

The CHOCH-retest beat is restored from narrative **T2/N2**, whose geometry is
*sweep of a **low** → rally → CHOCH → retest → **short***. The frozen direction
pairing (F5, V49) is the opposite: a swept **low** arms a **long**. So the beat is
being tested inside the pairing of the owner's other worked example — *HTF bullish
→ pullback takes sell-side liquidity → reclaims → displacement → retest → long* —
rather than inside N2's own pairing.

This is recorded as a scope fact, not raised as a blocker: F5 is frozen, the
sequence is fully specified under it, and re-opening the pairing would change the
experiment rather than validate it. It is the one thing worth remembering when
the results are interpreted.

---

## 7. Verdict

Every beat of the sequence maps to a current-bar test on confirmed inputs. Each
of the eight potential ambiguities is settled by a rule that was already frozen —
V49's level-touch fill for the CHOCH retest, the `dispWait` deadline for its
timeout, F4's own invalidity clause for the displacement/BOS identity, §12 for the
entry edge, V49's loop order for outcome timing — and no tolerance, penetration
rule, timeout, or parameter has been introduced. F1 and F3 remain labelled
experimental hypotheses and are frozen at C1b and `swLen = 3` before any run.

# READY FOR IMPLEMENTATION

Not implemented in this phase. No backtest, no optimisation, no strategy file
touched.

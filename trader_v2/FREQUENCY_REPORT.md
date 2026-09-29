# Frequency phase — consolidated deliverables

Companion documents: `PIPELINE_AUDIT.md` (Phase 1), `PHASE2_FAMILIES.md`
(Phase 2), `PHASE5_DIRECTION.md` (Phase 5), `V48_candidate_ledger.pine`
(Phases 3/4/8 instrumentation, **written but not yet run** — see §5).

---

## 1. Current bot pipeline

```
5m bar
  |
  v
LEVEL MAINTENANCE ........ prev-day H/L | Asia-session H/L | 10-bar pivots
  |
  v
SETUP DETECTION .......... wick >= 0.10 x ATR beyond a level
                           AND close back on the original side
  |                        ................................. 7,712 events / 57d
  v
TRIGGER .................. limit AT the swept level, 24-bar window
  |                        stop = sweep extreme -/+ 0.20 x ATR
  |                        ................................. 5,479 fills (71%)
  v
QUALITY FILTERS .......... R in [0.05, 3.00] x ATR
  |                        room >= 10R            removes 74.8%
  |                        4H bias aligned        removes 51.7%
  |                        (displacement 85.3%, reclaim 63.5% -- both rejected)
  |                        ................................. 674-1,378 fills
  v
ENTRY .................... at the level, limit fill
  |
  v
EXIT ..................... -1R stop | +5R target | 144-bar timeout
                           adverse excursion checked first | $3 drag in R
```

Direction is set by the setup instance, not by a label: a swept low arms a long,
a swept high arms a short.

## 2. Frequency bottlenecks, ranked

**The headline is that there is no frequency shortage.** The current engine
produces **96 fills/day across ten instrument × direction cells** before quality
filters, and **24/day** after the strictest one. The "242 trades/year" premise
belongs to V11.1, a bot that was retired ten versions ago and whose result was
invalidated by a margin bug (`PIPELINE_AUDIT.md` §0).

Ranked by measured fills removed per 57 days, all cells:

| rank | cause | fills removed | % of fills | verdict |
|---|---|---|---|---|
| 1 | **room ≥ 10R** (filter D) | 4,101 | **74.8%** | the threshold is arbitrary and **2–20× outside the range the user thinks in**. Highest-value thing to re-measure |
| 2 | **4H bias** (filter E) | 2,834 | 51.7% | **remove.** Failed fold C, costs half the fills for a near-information-free decision |
| 3 | **retest expiry + R-cap + slot loss** (B, J, K) | 2,233 | 29.0% of events | **not separated.** Slot contention is invisible because `arm()` counts before checking for a slot |
| 4 | **detector cascade** (I) | unknown | unknown | first-match only: a bar sweeping both a prev-day low and an Asia low generates **one** candidate, never two |
| 5 | **displacement confirmation** (C) | 4,676 | 85.3% | already rejected on expectancy grounds (0/10, t −5.24), not a frequency question |

Against the user's list: **A (too few raw setups) is false** — 7,712 events in
57 days. **B (detection too restrictive) is unproven and cheap to test.**
**D (room) is the dominant suppressor. E (HTF bias) is the second and should go.
F (prev-day structure) is not in the current engine.
G (session filters) do not exist. H (cooldowns) do not exist.
I and J are real but unmeasured.**

## 3. Setup families

See `PHASE2_FAMILIES.md`. Nine families exist in the code; six measure negative,
two significantly so. **Low trade count is not caused by having too few
families**, and adding more of this kind would add trades and subtract money.
The two families that survived their own tests — raw sweep-rejection and range
mean-reversion — are both **direction-agnostic** and **93% disjoint**.

## 4. Filter audit

Full table in `PIPELINE_AUDIT.md` §2. Summary of what to keep:

| filter | keep? | reason |
|---|---|---|
| sweep detection | keep, **and test a looser variant** | it is the event; no alternative has ever been measured |
| retest limit entry | **keep** | R/ATR falls 1.10 → 0.65, so the same move is worth ~1.7× more R |
| R cap | keep | caught a real bug once; cost unmeasured |
| **room** | **keep the concept, re-derive the threshold** | only component to survive fold C (+0.050 → +0.043), but never significant, and 10R was never justified |
| **4H bias** | **remove** | see `PHASE5_DIRECTION.md` |
| displacement | **remove** | 0/10 cells, t −5.24 |
| reclaim | **remove** | null in both folds; it costs 63.5% of fills for nothing |
| 2-slot limit | **raise to 8 and measure** | an engine artefact silently acting as a filter |
| session / cooldown | none exist | V11.1's session filter was measured **backwards**; do not reintroduce one untested |

## 5. Room analysis — NOT YET MEASURED

This is the central experiment of the phase and **it has not run.** The
TradingView MCP relay returned HTTP 502 continuously while V48 was being
injected, so no room-bucket data exists yet. I am not going to estimate it.

What V48 will produce, per instrument × direction cell:

- fills bucketed by available room at entry: `<0.5R, 0.5–1, 1–1.5, 1.5–2, 2–3,
  3–5, 5–10, ≥10R`, plus a **"no destination"** bucket for candidates where no
  opposing level exists (currently *allowed* when the filter is off and
  *rejected* when it is on — an inconsistency worth surfacing);
- per bucket: n, E[R], win%, fills/day, mean MAE;
- **cumulative E[R] for every threshold upward**, which is what actually
  identifies the minimum useful floor rather than assuming one;
- the ledger: sweeps, extra levels suppressed by the cascade, drops at 8 slots,
  would-have-dropped at 2 slots, expiries, R-cap rejections, fills.

The question it answers: **is 10R doing real work, or is 1.5R enough?** If the
cumulative curve is flat from ~1.5R upward, the floor can drop and frequency
rises ~4× at no cost to expectancy. If it rises monotonically to 10R, the
current floor is right and the frequency ceiling is real.

**I will not recommend lowering the threshold before this runs.** That would be
exactly the "loosen filters to get more trades" the brief prohibits.

## 6. Direction analysis

See `PHASE5_DIRECTION.md`. **Remove the global HTF filter.** Direction is
already determined locally by which side was swept.

## 7. Recommended architecture

```
DETECT   all levels swept on this bar (not first-match) -> N candidates
   |
CLASSIFY family (sweep-rejection | range-extreme | ...) and direction
   |     from the instance itself. No global label.
   |
MEASURE  entry, structural stop, nearest opposing destination,
   |     room in R, R/ATR, session, ATR regime
   |
FILTER   R in range; room >= T  (T to be derived, not assumed)
   |
RANK     score the surviving candidates; take the best k
   |
EXECUTE  limit at the level; -1R stop
   |
MANAGE   exit AT THE DESTINATION room was measured to -- not a fixed 5R
```

Three deliberate changes from the current engine:

1. **Detection emits every swept level**, not the first match.
2. **No global directional filter.**
3. **The exit uses the destination that room was measured to.** Today the engine
   measures room to a structural level and then exits at a fixed 5R — an
   inconsistency named in `PIPELINE_AUDIT.md` §3 item 12. Ranking and exiting on
   the same object is the natural fix, and it is testable.

The ranking step is what makes higher frequency safe: with 96 candidates a day
the bot should be **choosing among them**, not taking all of them — which is
Phase 7 of the earlier brief and the one part of that brief still unbuilt.

## 8. Implementation plan, in order

1. **Run V48.** Room buckets + ledger, folds A+B, all ten cells. *(blocked on
   the relay)*
2. **Derive the room threshold** from the cumulative curve. Pre-register it
   before touching fold C.
3. **Remove bias, displacement and reclaim** from the engine. Each is already
   measured; no new test needed to drop them.
4. **Raise slots to 8** permanently and report the contention that was hidden.
5. **Emit all swept levels** and measure what the cascade was costing.
6. **Exit at the destination**, benchmarked against fixed 5R on the same
   candidate set.
7. **Build the ranking layer** — only after 1–6, because ranking is meaningless
   until the candidate set is correct.
8. Evaluation modelling (Phase 10) last, against the verified LucidFlex rules
   already in `trader/prop_rules.py`, with no invented limits.

## 9. Test plan

Every change above goes through the same gate that just failed the bias model,
because that gate worked:

- develop on folds A+B; **fold C stays sealed** until the spec is frozen and
  committed;
- ten instrument × direction cells across four complexes, reported in full;
- report for each change: **change / baseline / new / delta / n / OOS / sign
  consistency / frequency effect / drawdown effect**;
- **a change that fails OOS is discarded**, not re-specified;
- state the test's power *before* running it, as Amendment 1 did.

One fix to the gate itself: the "≥ 7 of 10 cells" criterion was unachievable
when only 7 cells were populated. Future gates must require a **minimum
populated-cell count** first, or use a longer test window.

## 10. Stop condition

If the room-bucket curve shows no threshold that improves risk-adjusted
expectancy, **the room filter is kept at whatever value the evidence supports
and frequency stays where it is.** Trade count is not a goal. Nothing in this
phase will be shipped because it produces more trades; it ships if and only if
it survives fold C on expectancy, sign consistency and drawdown.

And if the honest end state is "this setup family has no demonstrated edge at
any room threshold" — which fold C leaves genuinely open — then that is the
finding, and the next move is a different family, not a looser version of this
one.

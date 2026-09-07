# Phase 1 — pipeline audit, and a correction to the premise

## 0. The premise needs correcting before anything else

> "The bot's backtest produced approximately 242 trades over one year with only
> around $5k PnL."

That number is real, but it does not describe the current bot, and it was
already retracted in this project.

- It is **V11.1**, from `strategies/V11_1_DAY_TRADER_RESULTS.md`: 232 trades,
  37.1% win, PF 1.352, **+$5,669**.
- `strategies/AUDIT_REPORT.md` invalidated it. The strategy ran with
  `margin_long = margin_short = 100` — zero leverage — so on $4,400 gold a
  correctly-sized position exceeded the account's notional and **TradingView
  silently rejected the order**. Same code, same signals:

  | margin | trades executed | net | PF |
  |---|---|---|---|
  | 100% (as configured) | **232** | **+$5,669** | 1.35 |
  | 20% (5:1) | 416 | −$366 | 0.990 |
  | 5% (20:1) | 420 | −$1,006 | 0.974 |

  **188 of 420 signals — 45% — were never executed.** With any realistic
  leverage there was no edge. The +$5,669 came from the bug preferentially
  admitting the good trades, which is luck, not selection.

So the honest reading of the original symptom is the opposite of the premise:
**"242 trades/year" was never a frequency problem — 420 signals existed and 45%
were silently discarded by an execution defect.** That report said so at the
time: *"Frequency (232/yr) was never the real problem."*

**And the current engine is not that bot.** V11.1 was replaced ten versions ago.
Measured on the current V47 engine, folds A+B, ten instrument × direction cells
over ~57 trading days:

| stage | fills | per day, all 10 cells |
|---|---|---|
| sweep only | 5,479 | **96.1/day** |
| + room ≥ 10R | 1,378 | **24.2/day** |
| + room + 4H bias | 674 | 11.8/day |

Even at its most restrictive the current pipeline produces **~12 opportunities a
day**, not 242 a year. The frequency question is therefore not "why so few
trades" — it is **"which of these thousands of candidates are worth taking, and
is the 10R room floor throwing away good ones?"** That reframing is what the rest
of this audit is about, and I think it is a better question than the one in the
premise.

---

## 1. The current pipeline

```
                     5m bar
                       |
        [1] LEVEL MAINTENANCE   prev-day H/L, Asia-session H/L, 10-bar pivots
                       |
        [2] SETUP DETECTION     sweep = wick >= 0.10 x ATR beyond a level
                                AND close back on the original side
                       |                                    7,712 events
        [3] ARM                 place a limit AT the swept level
                                stop = sweep extreme -/+ 0.20 x ATR
                       |
        [4] TRIGGER             price returns to the level within 24 bars
                       |                          (2,233 lost here + at [5])
        [5] QUALITY FILTERS     R in [0.05, 3.00] x ATR
                                room >= 10R to nearest opposing level   <-- 75%
                                4H EMA20/50 bias aligned (optional)     <-- 52%
                       |                                    674-5,479 fills
        [6] MANAGEMENT          -1R stop, +5R target, adverse checked first,
                                144-bar timeout, $3 drag charged in R
```

## 2. Bottleneck table

Counts are measured over folds A+B, 10 cells, ~57 trading days, from the V47
runs already in `ablation_phase4.py`. Where I do not have a count I say so
rather than estimate one.

| filter / condition | purpose | threshold | setups removed | evidence it helps | evidence it hurts |
|---|---|---|---|---|---|
| **sweep detection** | find the event | wick ≥ 0.10×ATR beyond level, close back inside | — (defines the 7,712) | it is the event, not a filter | **untested**: no measurement of what a looser or different detector would find |
| **retest trigger** (limit at the level, 24-bar window) | get a tight entry | 24 bars | part of 2,233 (29%) | earlier work: R/ATR falls 1.10 → 0.65, so the same move is worth ~1.7× more R | **the split between expiry, R-cap and slot contention is not measured** — see §4 |
| **R cap** | reject unusable stops | R ∈ [0.05, 3.00]×ATR | part of the same 2,233 | caught a real F5 bug once (3,266 of 3,269 arms rejected) | not separately measured here |
| **room ≥ 10R** | trade only where there is space | 10R | **4,101 of 5,479 fills = 74.8%** | biggest marginal effect measured: 8/10 cells, +0.142R; **the only component that survived fold C** (+0.050 → +0.043) | **never significant** (t +0.76 dev, +0.33 test); **10R is far outside the range the user thinks in** — their own bucket list stops at "5R+" |
| **4H EMA bias** | directional filter | EMA20 vs EMA50 | 2,834 of 5,479 = 51.7% | 7/10 cells in development, +0.034R marginal | **failed fold C**: −0.074R, kept-vs-discarded spread **inverted** to −0.207R; flips a few times a quarter, so it is a regime label not a trade decision |
| **displacement** | confirmation | bar range ≥ 1.5×ATR within 12 bars | 4,676 of 5,479 = **85.3%** | none | **0/10 cells, −0.322R, t −5.24.** Strongest negative in the project |
| **reclaim** | confirmation | close 0.25×ATR beyond the level within 12 bars | 3,478 of 5,479 = 63.5% | none | null: 5/10, −0.004R dev; 3/7, −0.024R test |
| **prev-day structure** | direction | prev-day close vs open + midpoint | not run as a filter | none | −0.249R, t −2.11 as a bias model |
| **slot limit (2 per group)** | engine bookkeeping | 2 concurrent | **unknown — arms are silently dropped when both slots are busy** | none — this is an artefact, not a design choice | **unmeasured suppressor.** `arm()` increments the counter before checking for a free slot, so dropped arms are invisible in every result so far |
| session filter | — | **none in the current engine** | 0 | — | earlier V11.1 work found its session filter was **backwards** (outside 07:00–16:00 UTC scored +0.293 vs +0.242 inside, yet outside trades were halved in size) |
| cooldown / one-per-day | — | **none** | 0 | — | — |

## 3. Answers to the specific audit questions

| # | question | answer |
|---|---|---|
| 1 | how is a setup detected | wick ≥ 0.10×ATR beyond prev-day H/L, Asia H/L or a 10-bar pivot, with the close back on the original side |
| 2 | what arms it | detection alone; the limit goes in immediately at the swept level |
| 3 | what is required for entry | price returns to the level within 24 bars, R within [0.05, 3.00]×ATR, plus whichever quality filters are switched on |
| 4 | what rejects valid setups | room (75%), bias (52%), displacement (85%), reclaim (64%), R-cap, retest expiry, and silently the 2-slot limit |
| 5 | which are directional | 4H bias only. Sweep direction already sets the trade direction by construction |
| 6 | volatility / session based | **none.** ATR is used to scale thresholds, never as a regime gate. No session filter exists |
| 7 | HTF-structure dependent | 4H bias only |
| 8 | prev-day dependent | prev-day H/L as a sweep *level* (kept); prev-day structure as a *bias* was tested and is harmful |
| 9 | sweep/reclaim/displacement | sweep is the detector; reclaim and displacement are optional confirmations, both measured worthless-to-harmful |
| 10 | room calculation | `\|nearest opposing level − entry\| / R`, where the opposing set is prev-day H/L, Asia H/L and the last 10-bar pivot on that side. If no level exists on that side, room is `na` and the trade is **allowed** when the filter is off, **rejected** when it is on |
| 11 | stop | structural: the sweep extreme ± 0.20×ATR |
| 12 | target | fixed 5R. **Not** the destination that room is measured to — this is an inconsistency worth naming: the engine measures room to a structural level and then ignores that level when exiting |
| 13 | do min/max R constraints block trades | yes, but the count is folded into the 2,233 and not separately measured |
| 14 | cooldowns / one-per-day | none |
| 15 | one active setup at a time | no — but only **2** per group, and overflow is dropped invisibly |
| 16 | mutually exclusive families | the sweep detector is a **first-match cascade** (prev-day → Asia → pivot). If price sweeps a prev-day low and an Asia low on the same bar, only the prev-day one is generated. **This is a real suppressor and it has never been counted** |
| 17 | lookback windows too tight | 24-bar retest and 12-bar confirmation windows are untested at any other value; the 10-bar pivot length likewise |
| 18 | is confirmation making entries too late | yes, demonstrably — displacement removes 85% of fills and turns expectancy sharply negative, which is the signature of entering after the move |

## 4. What this audit cannot answer, and why

Three suppressors are real and **completely unmeasured**, because the current
engine counts arms before it checks whether it can accept them:

1. **Slot contention** — `arm()` increments `cArm` and only then looks for a free
   slot. Every arm dropped for lack of a slot is invisible in every number in
   this project.
2. **The detector cascade** — the first matching level wins; simultaneous sweeps
   of a second level are never generated.
3. **The 2,233 arms that never became fills** are one lump. Expiry (price never
   came back), R-cap rejection, and slot loss are not separated.

I am not going to estimate these. The next step is to instrument them, which is
Phase 8's candidate ledger, and it is the only honest way to answer the question
this whole phase is built around:

> Are we failing to find opportunities because the market doesn't provide them,
> or because our code is filtering them out?

For the current engine the first-order answer is already clear and it is neither:
**the code finds ~96 opportunities a day and then discards 75% of them on a
threshold I chose arbitrarily.** Whether that threshold is right is Phase 4, and
it is the next thing to measure.

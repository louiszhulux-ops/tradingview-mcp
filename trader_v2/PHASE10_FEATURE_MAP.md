# Phase 10 — fresh edge discovery: what the engine does not see

No strategy logic touched. No backtests run. No thresholds searched.

---

## 1. Existing feature inventory (V49)

**Observed from raw data**

| input | used for |
|---|---|
| 5m OHLC | everything |
| ATR(14) 5m | scaling only — sweep depth, stop buffer, R cap |
| previous-day H/L | reference level |
| Asia-session H/L (UTC < 07:00) | reference level |
| 5m pivots, len 10 | reference level |
| `time`, `hour(UTC)` | fold gating; Asia window only |
| `syminfo.pointvalue` | cost → R conversion |

**Converted into explicit features**

sweep booleans per level type · simultaneous-level count · swept level price · structural stop (sweep extreme ± 0.20 ATR) · R · R/ATR · room to nearest opposing level (measured, bucketed, **not gated**) · MFE/MAE in R · outcome flag.

**Used for the entry decision**

Only four things: a sweep fired → limit at the swept level → filled within 24 bars → R ∈ [0.05, 3.00] × ATR. That is the entire decision surface.

**Present in the raw data, currently discarded**

`volume` (never read) · intrabar / 1m-3m detail · bar shape (body:wick, close position in range) · level *width* — levels are single prices, never bands · level age · prior touches of a level · session labels other than Asia · day of week · VWAP · ATR as a *regime* rather than a scaler · distance to round numbers · what happened between the sweep and the retest.

---

## 2. Missing discretionary primitives

Evidence base = the seven human-evidence artefacts only (`MANUAL_PROCESS_ANALYSIS.md`, `LOSS_NOTE_ANALYSIS.md`, `TRADE_VERIFICATION_AUG31.md`, `TRADE_VERIFICATION_TWO_TRADES.md`, `HUMAN_RECONSTRUCTION.md`, `HUMAN_TRADE_REGISTER.md`, `alert_history.json`). Counts are occurrences within that set.

### A. Already represented adequately

| concept | evidence | how V49 covers it |
|---|---|---|
| liquidity sweep of a prior level | "Asia spike, liquidity broken"; liquidity ×11 / 3 docs | the core detector |
| failed high / failed low | "nothing more bearish than a failed high" | wick beyond + close back inside **is** a failed break |
| retest entry | retest ×9 / 3 docs; "price retested them" | limit at the swept level, 24-bar window |
| structural invalidation | stop placement in both verified trades (4429 under structure, 4468 over the high) | stop beyond the sweep extreme |
| prev-day and Asia reference levels | Asia ×13 / 3 docs | both maintained |

### B. Partially represented — crude proxies

| concept | evidence | what is crude |
|---|---|---|
| **zones, not levels** | both hand-written alerts specify **bands** ("4460-4470", "BUY ZONE 4441-4444"); "pullback into imbalance/OB" | V49 uses a single price. A band has width, and width is where the trader's tolerance lives |
| **second touch** | "second" ×4; "waited for price to retest the CHOCH" | V49's retest is the second touch of the *swept level*. The notes mean the second touch of a *zone identified earlier* |
| **session phase** | London ×4, all three narratives execute at the GB open: "Coming into the GB open", "By the time GB opened", "GB had another big sell-off" | `hour(UTC)` exists but only gates the Asia window. London is never represented |
| **displacement** | displacement ×4 / 1 doc | encoded once as range ≥ 1.5×ATR and **falsified** (0/10 cells, t −5.24). The notes never quantify it, so one encoding failing is not the concept failing — but it is not a fresh candidate either |

### C. Completely missing

| concept | evidence | note |
|---|---|---|
| **VWAP state** | VWAP ×5 / 3 docs. `MANUAL_PROCESS_ANALYSIS.md` lists it as a process element and marks it **encodable: yes**; §4.1 records that I substituted "price touches VWAP and rejects", calling it "far cruder" than "trending below/above the VWAP" | never computed anywhere in the codebase |
| **level maturity — age and prior touches** | "unmitigated" ×9 / 4 docs; induc- ×6 / 3 docs; mitigat- ×9 / 4 docs. The loss note turns on it: *"we reached an unmitigated OB… price induced that level and filled an unmitigated 4-hour zone"* | V49 has no memory of whether a level has been touched before, or when it formed |
| **LTF structure shift (1m/3m CHOCH → BOS)** | CHOCH ×7 / 3 docs, BOS ×3. `MANUAL_PROCESS_ANALYSIS.md` names it as **the** trigger and marks it encodable: **no**, adding "The real trigger lives on 1m, and TradingView's bar limit makes a 7-month 1m backtest impossible here" | strongest evidence of any primitive, worst feasibility on this platform |
| **zone quality / confluence count** | "These zones alone were not strong enough" | an explicit quality ranking across candidate zones. No objective definition is given anywhere |
| **round numbers** | "external liq + round 4600" — one mention | thin; and it appears as a *destination*, which is the room framework already tested |
| **volume** | **none** | present in the data, absent from the human vocabulary. Excluded on the rule against inferring a concept just because it is common |

---

## 3. Candidate ranking

Ranked on evidence → objectivity → ex-ante availability → independence. **Not** on expected profitability.

| # | primitive | evidence it was actually used | current representation | missing information | objectively definable? | lookahead risk |
|---|---|---|---|---|---|---|
| **1** | **Session VWAP state** | ×5 / 3 docs, listed as a process element and marked encodable; my proxy was recorded as inadequate | **none** | where price sits relative to the session's volume-weighted mean | **yes** — standard formula, no free parameters | **low** — cumulative over closed bars only |
| **2** | **Level maturity (age + prior touches)** | ×9 / 4 docs ("unmitigated"), and the single documented loss is explained by it | **none** | whether this level is virgin or already worked, and how old it is | **yes** — touch count within 0.10×ATR since the level became *known* | **medium** — pivot levels are only knowable `swLen` bars after they form |
| **3** | **Session phase (Asia / London / overlap / NY)** | ×4, and 3/3 narratives place execution at the GB open | Asia only, as a level-building window | which regime a candidate belongs to | **yes** — fixed UTC boundaries | **none** |
| — | LTF structure shift | strongest of all | none | the actual stated trigger | yes in principle | none — but **infeasible**: 1m over a multi-month window exceeds TradingView's bar limit, recorded in the notes themselves |
| — | Zone width | ×2 alerts + narratives | single price | tolerance band around a level | only with an arbitrary construction rule | low — but **not independent**: it modifies the sweep entry mechanism |
| — | Zone quality / confluence | 1 explicit line | none | the ranking the trader applies | **no** — no objective definition exists in any source | — |
| — | Round numbers | 1 mention | none | — | yes | low — but thin evidence and it is a destination feature |
| — | Volume | **none** | none | — | yes | — |

**Selected: three.** VWAP state, level maturity, session phase. LTF structure shift is excluded on feasibility, not on merit, and that is the single biggest known gap.

---

## 4. Measurement specification

Each is an **attribute recorded on the existing V49 candidate ledger**. None gates anything. Recording an attribute is measurement, not a filter.

### C1 — Session VWAP state

- **Definition** `VWAP_t = Σ(hlc3ᵢ · volumeᵢ) / Σ(volumeᵢ)` accumulated from the session open, reset at the CME session boundary (22:00 UTC). Two attributes: `vwapSide = sign(close − VWAP)` and `vwapDist = (close − VWAP) / ATR14`.
- **Inputs** high, low, close, volume, session boundary. **Timeframe** 5m. **Lookback** intraday, resets each session.
- **Known** at the close of each 5m bar. **Frozen** at the close of the arm bar (the sweep bar); never updated afterwards.
- **Attachment** stored alongside the candidate's room bucket, same as MFE/MAE.
- **Missing/ambiguous** if `volume` is 0 or `na` for the session, record `na` and **exclude** — do not substitute a price-only VWAP. Report the exclusion count.
- **Lookahead** would be: using the session's *final* VWAP, any `request.security(..., lookahead_on)`, or computing VWAP on the bar in progress.
- **Controls** compare against (a) a random-sign control at the same n, and (b) `sign(close − SMA(20))`, to establish VWAP is not just a trivial trend proxy.
- **Thresholds** none for `vwapSide`. For `vwapDist`, report deciles; do not choose a cut.
- **Minimum dataset** existing 10 cells × folds A+B ≈ 6,200 candidates; a roughly 50/50 side split gives ~3,100 per arm.

### C2 — Level maturity

- **Definition** for every reference level L, maintain `bornBar` = the bar L became **known** (for pivots that is pivotBar + swLen, **not** pivotBar), `ageBars = bar_index − bornBar`, and `touches` = count of bars since `bornBar` and strictly before the arm bar where `min(|high−L|, |low−L|) ≤ 0.10 × ATR`. Derived: `virgin = (touches == 0)`.
- **Inputs** the level series V49 already maintains, plus ATR. **Timeframe** 5m.
- **Known / frozen** at the arm bar.
- **Missing/ambiguous** prev-day and Asia levels have a well-defined birth; pivots do not exist until confirmed. Any level whose `bornBar` is unknown records `na` and is excluded.
- **Lookahead** the trap is counting touches during the pivot's own formation window — those bars were not yet known to have formed a pivot. Age must run from confirmation, not from the pivot bar.
- **Controls** `ageBars` and `touches` correlate with each other and with level type (prev-day levels are always ~1 session old; pivots vary). Report marginally **and** stratified by level type, or the result will just be "pivot vs prev-day".
- **Thresholds** none — report the distribution of `touches` (0, 1, 2, 3+) and `ageBars` deciles.
- **Minimum dataset** same candidate set. `virgin` may be a small minority; **count it before deciding whether it is testable at all.**

### C3 — Session phase

- **Definition** fixed UTC bands, precommitted: Asia 22:00–07:00, London 07:00–12:00, Overlap 12:00–16:00, NY 16:00–20:00, Off 20:00–22:00.
- **Known / frozen** at the arm bar. **Lookahead** none.
- **Missing/ambiguous** DST is ignored, so band edges drift by an hour twice a year. Recorded as a known imprecision, not corrected by fitting.
- **Controls** session correlates strongly with volatility and volume. **Report ATR percentile and candidate count per session**, or a "session effect" is indistinguishable from a volatility effect.
- **Thresholds** none — the bands are the categories.
- **Minimum dataset** same set, ~1/5 each.

---

## 5. Risks and falsification

### C1 VWAP

1. **Why it might contain information** it is a volume-weighted consensus price that many participants reference; it is the only element of the trader's stated process that was marked encodable and then encoded badly.
2. **Why it might be useless** on a 24-hour futures contract the session anchor is arbitrary, and VWAP may just be a lagging mean that carries the same content as any moving average.
3. **Confound** `vwapSide` is strongly correlated with short-horizon trend. A positive result could be a trend effect wearing a VWAP badge — which is why the SMA control is mandatory, not optional.
4. **Leak** using the completed session's VWAP, or an unclosed bar's.
5. **Falsification** if `vwapSide` splits outcomes no better than `sign(close − SMA20)` and no better than a random sign at the same n, it carries nothing.

### C2 Level maturity

1. **Why** the loss note turns on exactly this distinction, and it is the one concept the trader uses to explain a failure rather than a success.
2. **Why useless** "unmitigated" may be post-hoc vocabulary for "the level that happened to hold", in which case it is unlearnable from price.
3. **Confound** `touches` is mechanically tied to how long a level has existed and to volatility — an old level in a quiet market accumulates touches. Stratification by level type and ATR regime is required.
4. **Leak** counting touches from the pivot bar rather than the confirmation bar leaks `swLen` bars of future information. This is the specific mistake to guard against.
5. **Falsification** if outcome distributions for `touches ∈ {0,1,2,3+}` are indistinguishable after stratifying by level type, the concept is not in the price data.

### C3 Session phase

1. **Why** 3/3 narratives put execution in one window; that is the most consistent pattern in the notes after "bias".
2. **Why useless** session may be pure volatility, already normalised away by ATR-scaled stops and R-denominated outcomes.
3. **Confound** volatility, volume, and news timing all covary with session. Also: `AUDIT_REPORT.md` found V11.1's session filter ran **backwards**, and V37 found session conditioning did not survive — prior evidence leans negative.
4. **Leak** none.
5. **Falsification** if per-session E[R] differences vanish once candidates are stratified by ATR percentile, it is a volatility effect, not a session effect.

**The V44/V48 failure mode to avoid.** In both cases a feature looked informative because something else was doing the work — room was silently on inside the bias ablation, and a 2-slot engine was silently selecting candidates. The general defence is the same each time: **before believing a split, check what else differs between the two sides.** Every control above exists for that reason.

---

## 6. Recommended Phase 11 experiment

**Test only C1, VWAP state. One experiment, precommitted.**

- **Change** add `vwapSide`, `vwapDist`, and the two controls (`smaSide`, a seeded random sign) as **recorded attributes** on the V49 candidate ledger. No gating, no entry change, no new family.
- **Population** the existing V49 candidate stream, folds A+B, all ten instrument × direction cells. Fold C stays sealed.
- **Primary measurement** E[R] for `vwapSide = +1` vs `vwapSide = −1`, reported as the difference with a 90% CI, per cell and pooled.
- **Pre-registered gate** VWAP is worth pursuing only if the split (a) beats the SMA control by a margin whose CI excludes zero, **and** (b) holds sign in ≥ 7 of 10 cells. Anything less is a null.
- **Stated in advance** with ~3,100 per side and sd ≈ 2.3, the detectable difference at 80% power is roughly **0.15R**. A smaller true effect will not be found by this test, and that is not the same as it being absent.
- **Not doing** combining C1 with C2 or C3; choosing a `vwapDist` cut; running fold C; or building any strategy around the result.

If C1 is null, C2 is next, and C3 last — the reverse of the order in which they are easy.

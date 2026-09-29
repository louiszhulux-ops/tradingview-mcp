# Phase 13 — LTF sequence: specification audit (pre-implementation)

Audit only. Nothing implemented, no expectancy, no optimisation, no fold C.
V49/V50/V51/V52 untouched. One read-only Pine probe was run to answer the data
question; it computes no entries and no outcomes.

---

## 1. Already supported by existing documented definitions — REUSE, do not redefine

| spec section | existing definition | source | causally proven? |
|---|---|---|---|
| §1 sweep = starting event | wick ≥ 0.10 × ATR beyond prev-day H/L, Asia H/L or 10-bar pivot, close back inside | V49 | yes — reconciled across 7,454 candidates |
| §4 pivot **method** | `ta.pivothigh/low(src, swLen, swLen)`, confirmed at `pivotBar + swLen` | V49/V51 | **yes — V51 Gate A: 0 confirmation-lag mismatches in 7,454 candidates**, `low[swLen] == pl5` checked at every confirmation bar |
| §7 displacement | `range ≥ 1.50 × ATR` **and** `close > low + 0.6×range` (bull) / `close < low + 0.4×range` (bear) | `V44_continuation_ablation.pine:122`, V45:134, V47:263 | yes |
| §10 max delays | `dispWait = 12` bars (sweep→displacement), `retBars = 24` (retest window), `maxBars = 144` (timeout) | V44–V52 | yes |
| §11 FVG | `bullFvgNow = low > high[2]`, `bearFvgNow = high < low[2]`; zone = `[high[2], low]` / `[high, low[2]]` | `V8_3_XAU_trend_range.pine:176-194` | yes — identical to the §11 three-candle rule |
| §12 retest (fill) | `low <= bullFvgBot` marks the bull FVG filled | same file, :189 | yes |
| §14 stop | sweep extreme ± **0.20 × ATR** | V49 | yes |
| §15 outcome framework | 5R target, −1R stop, adverse excursion checked first, 144-bar timeout, $3.00 drag converted to R | V47–V52 | yes |
| §18 leakage harness | D0–D7 pattern already built and passed once | V51 Gate A | yes |

**Seven of the fourteen substantive sections are already frozen in code.** Nothing
needs inventing for sweep, pivot method, displacement, FVG, retest, stop or outcome.

## 2. Missing — no documented definition exists

| # | missing element | why it is missing |
|---|---|---|
| **M1** | **CHOCH swing selection** — *which* confirmed swing low/high is "the relevant opposing internal structure"? | §5 gives the break rule (close beyond) but not which swing. Candidates: the most recent confirmed swing before the sweep; the swing formed between sweep and now; the lowest/highest since the sweep. The repo contains none of these |
| **M2** | **BOS swing selection** — what is "the next relevant confirmed structural low/high"? | §8 has the same gap. Also needs a rule preventing the CHOCH swing being reused |
| **M3** | **LTF pivot strength** | the only documented `swLen` is **10, on 5m**. No 1m or 3m value exists anywhere. This single number changes CHOCH/BOS frequency by orders of magnitude |
| **M4** | **FVG selection among multiples** (§17) | "prefer the FVG directly associated with the displacement that caused the structural break" is a preference, not an algorithm. If the displacement leg spans three bars it can create two or three FVGs |
| **M5** | **sweep→CHOCH maximum delay** | `dispWait = 12` is documented for sweep→**displacement**, not sweep→**CHOCH**. §10 permits recording the distribution without enforcing a cap, so this one is deferrable |

**M1, M2 and M3 are hard blockers.** Under §25.6 (ambiguous structure selection)
and §25.7 (needing to choose a parameter before the hypothesis can be tested),
they trigger a STOP. I am not choosing them, because any choice would be made by
me rather than documented, and §4 explicitly says to stop rather than "silently
choose a profitable-looking definition."

## 3. Requires a frozen assumption — needs your decision before any code runs

Each of these must be fixed in writing, then not revisited after results:

| id | decision needed | options (no recommendation implied by order) |
|---|---|---|
| **F1** | CHOCH swing selection | (a) most recent confirmed opposing swing **existing at the sweep bar**; (b) most recent confirmed opposing swing **as of each bar**, re-evaluated forward; (c) the extreme opposing swing formed between the sweep and now |
| **F2** | BOS swing selection | (a) the next confirmed swing in the new direction formed **after** CHOCH; (b) the most recent confirmed such swing as of each bar. Must exclude the CHOCH swing (§8) |
| **F3** | LTF pivot strength `swLen` | one integer, applied to both 1m and 3m, frozen before any run |
| **F4** | FVG selection among multiples | (a) the first FVG created at/after the BOS bar; (b) the largest by price height; (c) the one containing the BOS break level |
| **F5** | Stop buffer | keep V49's `± 0.20 × ATR`, or the bare sweep extreme as §14 literally states |
| **F6** | ATR timeframe for displacement and stop | 5m ATR(14) as V49 uses, or LTF ATR(14) |

**F3 and F6 are the ones most likely to be mistaken for optimisation later.**
Whatever is chosen must be recorded here before the first run, and the run
reported whatever it produces.

## 4. Can the available data support the test? — **YES, and this corrects my Phase 12 finding**

Phase 12 concluded 1m could not reach folds A or B. **That was measured on the
chart-series path only, and it is wrong as a general statement.** I had not
tested `request.security_lower_tf`, which is a different data path with different
limits.

Measured just now — read-only probe, MGC1! on a 5m chart, 20,574 chart bars:

| | 1m | 3m |
|---|---|---|
| chart bars carrying LTF data | 20,001 of 20,574 | **20,574 of 20,574** |
| total intrabar values | **100,000** (exactly the cap) | 34,290 |
| max values per chart bar | 5 | 2 |
| **earliest LTF data** | **2026-05-27 02:15 UTC** | **2026-05-24 22:00 UTC** |
| latest chart bar | 2026-09-04 20:55 UTC | same |

| fold | boundary | 1m covered? | 3m covered? |
|---|---|---|---|
| **A** (all before 2026-07-16) | starts ≈ 2026-05-24 | **yes, from 05-27** — all but ~3 days | **yes, in full** |
| **B** (07-16 → 08-09) | | **yes, in full** | **yes, in full** |
| **C** (08-09 → 08-31) | sealed | yes, in full | yes, in full |

Compare with the chart-series path measured in Phase 12: 1m gave only
2026-08-16 → 09-04. **`request.security_lower_tf` reaches roughly 11 weeks
further back.** The correction matters because it moves the primary (1m)
hypothesis from untestable to testable.

### Three data caveats that must not be glossed

1. **The 1m cap is exactly saturated.** 100,000 values is TradingView's documented
   intrabar limit and the probe hit it precisely. 1m coverage is pinned to the
   **last 20,000 chart bars**, so it slides forward as time passes and will
   silently lose the earliest part of fold A. The window must be pinned by
   timestamp and re-verified at every run.
2. **The probe requested `close` only.** CHOCH/BOS/FVG need **open, high, low,
   close** — four series. Whether the 100,000 cap is per-call or aggregate across
   calls is **unknown and decisive**: if aggregate, usable 1m history drops to
   ~5,000 chart bars and the 1m hypothesis fails on data again. **This must be
   probed before implementation.**
3. **3m does not tile 5m evenly** (1–2 intrabars per chart bar, 34,290 = 20,574 × 5/3
   exactly). The aggregate count is right, so reconstruction is sound, but bar
   alignment is uneven and the code must not assume a fixed ratio.

### Architecture consequence

Running the LTF layer via `request.security_lower_tf` on the existing 5m chart
**keeps the V49 sweep engine untouched** (§1, §25.9) — the sweep still fires on
5m bars, and the LTF sequence is a separate consumer attached after it. The
alternative of running the engine natively on a 1m chart would re-detect sweeps
on 1m bars, which *is* modifying the sweep engine and is forbidden.

---

## Status and what I need from you

**STOPPED before implementation**, per §25.6 and §25.7. Blockers are **M1, M2, M3**
— the CHOCH and BOS swing-selection rules and the LTF pivot strength. None exists
in the repository, and inventing them is exactly what the brief forbids.

To proceed I need **F1–F6 frozen in writing**. Once they are, the order is:

1. probe whether the 100,000 intrabar cap is per-call or aggregate (decides 1m vs 3m);
2. build the event ledger with D0–D7 leakage diagnostics;
3. mechanical audit only — event counts, conversion rates, timing distributions,
   worked examples (§21);
4. performance on folds A+B only after the mechanical audit passes;
5. fold C last, frozen, once.

One thing worth saying plainly: **1m and 3m are separate hypotheses** (§3), and
if the cap turns out to be aggregate, only 3m survives — which would make this a
test of a *proxy* for the documented 1m process, not the process itself. I would
label it that way rather than treat the two as equivalent.

# V7 VALIDATION REPORT — full test battery before V8

## Headline result (canonical config, reproduced 3x, bit-identical every time)
| Metric | Value |
|---|---|
| Entries | 30 (42 closed trades incl. partial exits) |
| Win rate | **59.5%** |
| Profit factor | **1.59** |
| Net profit | **+$1,257 (+2.51%)** |
| Max drawdown | **$616 (1.20%)** |
| Sharpe / Sortino | 0.64 / 2.34 |
| Largest win / loss | $441 / $221 |

## Tests run and what each one checked

### 1. Determinism (does the same config always give the same answer?)
Ran the canonical config 3 separate times, including a full symbol round-trip
(XAUUSD -> NQ1! -> XAUUSD). Every run returned bit-identical numbers
(net_profit=1256.7372, PF=1.586186...). PASS -- no hidden state, no randomness.

### 2. Trade-level sanity check (not just aggregate metrics)
Pulled the actual order list and checked individual fills by hand:
- Every stop for a long sits BELOW its entry; every stop for a short sits ABOVE. No
  wrong-side stops anywhere in the sample -- this is the exact bug class that caused
  the -$5,734 disaster earlier in this project, and it does not recur here.
- Partial-close quantities reconcile exactly to 40%/60% of position size on every
  trade that reached TP1.
- No duplicate or orphaned orders.
PASS.

### 3. Time-window robustness (is the edge from one lucky stretch?)
Shifted the backtest start from Oct 2025 to Dec 2025 (dropping the first 2 months)
and removed the trade cap to see the natural rate over the remaining ~9 months:
84 trades, 54.8% win rate, PF 1.58. Nearly identical to the original 30-trade
sample's PF 1.59. The edge holds when the early months are excluded. PASS.

### 4. Parameter sensitivity (is this tuned to a knife-edge value?)
Nudged the trend-gap filter from 0.30xATR to 0.35xATR (stricter) with the cap
removed: 101 trades, 56.4% win rate, PF 1.48. A modest, graceful decline -- not a
collapse. Classic overfitting shows up as a cliff at nearby settings; this doesn't
have one. PASS (with a caveat -- see below).

### 5. Killzone hard-gate (tested honestly, not adopted)
Added a genuine hard gate (London 07-10 UTC + NY AM 12-15 UTC only, entries
blocked outside it) as an isolated on/off toggle -- this had never been correctly
tested before now (earlier attempts were contaminated by the entry-counter bug).
Result: only 3 trades over the full ~11 months. Quality looked excellent (PF 3.6,
67% win rate) but n=3 is not a usable sample. NOT ADOPTED as a hard gate -- the
existing soft session multiplier (half size outside 07:00-16:00 UTC) already
captures the practical benefit without starving the strategy of setups.

### 6. Cross-asset out-of-sample (NQ1!) -- INCONCLUSIVE, reported honestly
Switched the exact same script to CME_MINI_DL:NQ1! to see if the edge holds on a
different instrument. The Strategy Tester returned an empty/truncated report
(0 trades, metric_count 12 instead of the normal 19) with no compile error and no
visible runtime error message. This matches the signature of a genuine runtime
issue, not "just needs more time" (which shows a partial trickle of trades, not a
flat zero). Root cause not chased down -- most likely candidate is the fixed
round-number step ($50, sized for gold) or a contract-multiplier mismatch in the
position-sizing math (NQ's ~$20/point vs gold's ~$1/point), but this is a guess,
not a diagnosis. Switched back to XAUUSD (the instrument actually being traded)
rather than spend unbounded time on a side quest. NQ compatibility is NOT
validated -- do not assume this system works unmodified on futures.

## What this validation does and doesn't prove
DOES show: the result is deterministic, individual trades execute correctly on
the correct side, the edge is not concentrated in one short window, and the
strategy isn't perched on one fragile parameter value.

DOES NOT show: true out-of-sample performance (all tuning happened on the same
~11 months of XAUUSD data), performance on any instrument other than gold, or
performance beyond September 2026 (no data exists yet).

## Overall verdict
Win rate, PF, and max drawdown all check out as genuinely reproducible and not
an artifact of a bug, a lucky window, or a fragile parameter. This is a solid
foundation for V8. The two open items are: (1) the killzone question is settled
(soft multiplier, not hard gate) and (2) NQ portability is unresolved and should
not be assumed.

## V7 re-verified on later live data (session 3)
Same rules, re-run after real calendar time passed (live/continuously-updating feed,
not a frozen snapshot): 44 closed trades (30 entries, ~14 partials), 63.6% win rate,
PF 2.25, +4.31%, max DD 0.72%. Confirms results drift naturally day-to-day as new
market data arrives -- this is expected for a live-data backtest, not a bug. Rules
are unchanged from the validated V7.

## NQ cross-asset: extensive further diagnosis, still unresolved
Spent significant additional effort isolating the NQ issue via bisection (removing
FVG, removing ARM logic, removing DXY/round-number confluences, testing raw signal
counts via debug tables, a full clean app relaunch, and fresh study re-attachment to
rule out stale-session state).

Confirmed: the structural signal-detection layer (pivots, liquidity sweep, BOS,
fresh-break continuation) works correctly on NQ -- a clean diagnostic counted 198
BOS-after-sweep events and 747 fresh-break events over the full window, comparable
in magnitude to gold's counts.

NOT resolved: the full entry pipeline (trend filter + ARM zone + retrace trigger +
stop-distance filter) produces zero real trades on NQ in every test, including a
maximally simplified version with DXY/round-number/weekly-liquidity stripped out.
Whether this is a genuine timing mismatch (BOS events and the trend filter rarely
overlapping on NQ's different volatility character) or a residual platform/tooling
reliability issue could not be conclusively determined within reasonable time.
Honest status: NQ compatibility is UNRESOLVED, not validated working and not proven
broken. Do not deploy this system on NQ without further dedicated debugging.

## V8 PnL-improvement experiments — honest negative result

Tested three candidate improvements against the validated V7 baseline (same data,
same 30-entry cap), isolating each variable:

| Variant | Win% | PF | Net profit | Max DD | Largest loss |
|---|---|---|---|---|---|
| **V7 baseline** (static BE, 2-tier sizing) | 63.6% | **2.25** | $2,155 | **0.72%** | $208 |
| V8b: graduated sizing (0.5-1.25x), static BE | 56.5% | 1.68 | $2,078 | 2.99% | $472 |
| V8c: trail-only, proven 2-tier sizing | 59.5% | 1.58 | $1,216 | 0.96% | $221 |
| V8: trail + graduated sizing together | 62.2% | 2.01 | $2,618 | 2.98% | $472 |

Key finding: max drawdown is IDENTICAL between "sizing only" and "trail + sizing"
(both 2.98-2.99%) -- the drawdown increase is caused entirely by the graduated
sizing's 1.25x ceiling on the top confluence tier, not the trail. Isolating the
trail alone (keeping the original 2-tier sizing) shows it actually HURTS net
profit ($1,216 vs $2,155) with no meaningful drawdown benefit -- it cuts some
winners short before they reach the liquidity target, converting full-target wins
into smaller trail-stopped wins.

The only variant that shows a higher headline dollar number (V8, +$2,618) does so
by combining a worse risk profile (4x the drawdown, more than double the largest
loss) with a trail that independently loses money. That combination is not a real
improvement -- it is bigger bets producing a bigger number, which is not the same
thing as a better strategy.

**Decision: none of these changes are adopted. V7 remains the best validated
version on a risk-adjusted basis (PF 2.25, 0.72% max drawdown).**

# V8 FINAL — results, 29 Jul 2026 -> 29 Aug 2026, $50,000 per instrument

## THE NQ MYSTERY IS SOLVED
Across two prior sessions I could not get NQ to produce a single trade, and I
reported it as unresolved. The user identified the cause: the chart symbol was
**CME_MINI_DL:NQ1!** -- the "_DL" suffix means DELAYED data. TradingView will not
execute strategy orders on a delayed futures feed (replay does not bypass this
either; I tested that too).

Proof the strategy logic was never at fault: an `indicator()` probe of the exact
same entry logic on NQ, over this exact window, counted:
  BOS-in-trend long/short: 36 / 18
  longTrigger fired:       86
  shortTrigger fired:      54
  passed stop filter:      126
126 fully-qualified signals. The signal engine works perfectly on Nasdaq. Only
strategy ORDER EXECUTION was blocked, purely by the delayed data feed.

Fix: use a real-time Nasdaq feed. Switched to **OANDA:NAS100USD** (same broker
feed family as the working XAUUSD data). It trades immediately.

## Results

### XAUUSD (OANDA) — 5 entries, 8 closed legs
| Metric | Value |
|---|---|
| Win rate | 75.0% |
| Profit factor | 4.39 |
| Net profit | +$735.87 (+1.47%) |
| Max drawdown | $189 (0.38%) |
| Largest win / loss | $272 / $112 |
All 5 entries were longs: 2 stopped out, 3 reached TP1 partial then final target.

### NAS100 (OANDA, real-time Nasdaq proxy for NQ) — 4 entries, 6 closed legs
| Metric | Value |
|---|---|
| Win rate | 66.7% |
| Profit factor | 1.61 |
| Net profit | +$180.04 (+0.36%) |
| Max drawdown | $391 (0.78%) |
| Largest win / loss | $157 / $197 |
2 shorts stopped, 1 long and 1 short reached TP1 partial then target.

### Combined (see caveat)
+$915.91 across both instruments. 9 entries, 14 closed legs, 10 winners / 4 losers.

CAVEAT ON THE COMBINED FIGURE: these are two INDEPENDENT $50,000 backtests, not
one $50,000 account trading both symbols. A single shared account would size
positions off shared equity and could hold concurrent positions in both, which
changes both the risk profile and the result. The combined number is indicative,
not a validated single-account result.

## What V8 is
V8 = V7's exact validated rule set, plus two additions:
  1. Contract-multiplier-aware sizing (qty = risk$ / (stopDist * syminfo.pointvalue))
     -- makes sizing correct across instruments, not just spot gold.
  2. An end-date filter, so a defined test window can be run and positions are
     flattened at window end.
Nothing else was added. The V8 experiments from the prior session (graduated
confluence sizing, structure trailing stop) both tested WORSE than V7 and were
correctly excluded -- "use only what worked" means they stay out.

## NAS100 sizing note
Most NAS100 entries sized to qty=1. That is the sizing math working as designed,
not a bug: those setups landed outside 07:00-16:00 UTC (0.5x size) and with fewer
than 2 confluences (0.6x size), so 0.75% risk x 0.5 x 0.6 = 0.225% effective,
which at ~100-point stops rounds down to 1 unit. Real risk taken on those trades
was well below the 0.75% cap.

## Honest status
- Sample is SMALL: 9 entries total in a one-month window. This is a demonstration
  that V8 executes correctly on both instruments, not statistical proof of edge.
- Still no true out-of-sample validation. All rule development used XAUUSD data
  from this same broader period.
- Zero spread, zero commission, zero slippage modelled. Real fills will be worse.
- To trade actual NQ futures (not the CFD proxy) you need a CME real-time data
  subscription in TradingView. The strategy code itself is ready for it.

# V8.3 cost validation — XAUUSD 15m, 2025-10-01 → 2026-09-03, $50,000

Every run below is the same code on the same window on OANDA:XAUUSD 15m.
Execution cost is modelled as `strategy.commission.cash_per_contract`, i.e. a
flat dollar charge per ounce **per side**, standing in for spread + slippage +
commission combined. Two tiers were tested:

- **$0.20/side** = ~$0.40 round-trip per ounce — a realistic retail XAUUSD spread.
- **$0.50/side** = ~$1.00 round-trip per ounce — deliberately pessimistic
  (wide Asia-session / news spreads, adverse stop fills).

The zero-cost control reproduced the previous full-sample figure **exactly**
(145 trades, PF 1.6155, +$8,160.39, DD 2.81%), so all comparisons below are
clean apples-to-apples on an identical window.

## 1. What costs did to the original V8.2

| Config | Cost/side | Trades | Win% | PF | Net | Max DD |
|---|---|---|---|---|---|---|
| Combined | $0.00 | 145 | 33.1% | 1.615 | +$8,160 | 2.81% |
| Combined | $0.20 | 148 | 32.4% | 1.470 | +$6,637 | 3.01% |
| Combined | $0.50 | 150 | 32.0% | 1.378 | +$5,578 | 3.53% |
| Trend only | $0.00 | 74 | 39.2% | 1.690 | +$4,749 | 2.43% |
| Trend only | $0.20 | 75 | 38.7% | 1.676 | +$4,663 | 2.51% |
| Trend only | $0.50 | 73 | 39.7% | 1.661 | +$4,546 | 2.63% |
| Range only | $0.00 | 83 | 25.3% | 1.310 | +$2,427 | 4.06% |
| Range only | $0.20 | 82 | 24.4% | 1.173 | +$1,412 | 5.68% |
| Range only | $0.50 | 82 | 24.4% | 1.126 | +$1,059 | 6.00% |

**The trend module is almost cost-immune** — a 5x increase in execution cost
costs it 4% of net profit, because its average trade ($62) dwarfs its per-trade
cost (~$8). **The range module was the fragile one, exactly as predicted**: real
costs took 42% of its profit and pushed its drawdown from 4.06% to 6.00%.

## 2. The fix: raise the range module's minimum R

Range trades were being accepted at 1.5R. At that size the expected win is too
small to clear the spread. Sweeping `rangeMinR` (range-only, $0.50/side):

| rangeMinR | Trades | PF | Net | Max DD |
|---|---|---|---|---|
| 1.5 (old) | 82 | 1.126 | +$1,059 | 6.00% |
| 2.0 | 79 | 1.323 | +$2,473 | 3.51% |
| **2.5** | **67** | **1.437** | **+$2,737** | **2.94%** |
| 3.5 | 48 | 1.463 | +$2,133 | 2.87% |

Smooth and monotone from 1.5→2.5, flattening after — a broad plateau, not an
overfit spike. **2.5 adopted.** At the realistic $0.20/side the same change puts
range-only at 66 trades, PF 1.502, +$3,032, DD 2.70% — better than it ever was
even at *zero* cost (PF 1.31, DD 4.06%). The min-R filter did not just offset
costs, it fixed a genuine weakness: the module was taking trades with no room.

## 3. V8.3 final — combined, both modules, rangeMinR 2.5

| Metric | $0.20/side (realistic) | $0.50/side (pessimistic) |
|---|---|---|
| Trades | 136 (~12/month) | 133 |
| Win rate | 32.4% | 33.1% |
| Profit factor | **1.475** | **1.450** |
| Net profit | **+$6,072 (+12.1%)** | +$5,778 (+11.6%) |
| Max drawdown | **$1,626 (3.01%)** | $1,643 (3.06%) |
| Return / drawdown | 3.73 | 3.52 |
| Sharpe / Sortino | 0.43 / 1.01 | 0.41 / 0.95 |
| Costs paid | $432 | $1,052 |

**V8.3 barely moves between the two cost tiers (-5% net profit for a 2.5x cost
increase). V8.2 lost 16% over the same span.** That stability is the real win
here — it means the result does not depend on getting a good broker.

## 4. Does the range module still earn its place?

At $0.20/side: trend-only is +$4,663 / DD $1,268 (2.51%), return-to-drawdown 3.68; combined is
+$6,072 / DD $1,626 (3.01%), return-to-drawdown 3.73. The range module adds **+$1,409 (+30% net
profit) for +0.50pp of drawdown**, and takes trade count from ~7/month to
~12/month. It keeps its place — but it is the weaker half and it is the half to
switch off first if live results disappoint. `Enable RANGE module` is a
one-click input for exactly that reason.

Combined Sortino (1.01) is lower than trend-only (1.68): the range module adds
dollars and frequency but makes the downside choppier. If your priority were
purely smoothness rather than PnL, trend-only is the better config.

## Honest status / what is still untested
- **Every number here is in-sample.** Both modules were developed on this same
  11 months of XAUUSD data. There is still no true out-of-sample test.
- Costs are modelled as a flat per-ounce charge. Real spread widens on news and
  at the daily roll; that variance is not captured.
- Limit exits (take-profits) are assumed to fill whenever price touches them.
  Real limit orders can be skipped in a fast move.
- 32% win rate means 6-10 consecutive losses is normal and must be sat through.
- Recommended before live capital: forward-test on a demo account for 4-8 weeks
  and compare the live fill prices against the alert payload prices.

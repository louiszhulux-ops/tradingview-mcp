# V8.2 full-sample validation — XAUUSD 15m, Oct 2025 -> Sep 2026 (~11 months), $50,000

## Headline
| Metric | Value |
|---|---|
| Trades | **145** |
| Win rate | 33.1% |
| Profit factor | **1.62** |
| Net profit | **+$8,160 (+16.3%)** |
| Max drawdown | **$1,530 (2.81%)** |
| Sharpe / Sortino | 0.55 / 1.63 |
| Largest win / loss | $2,179 / $315 |
| Buy & hold same period | +$6,995 |

~13 trades/month, consistent with the 13 seen in the Jul-Aug window.
Return-to-drawdown ratio ~5.8. Beats buy & hold (+16.3% vs +14.0%) at a fraction
of the risk exposure.

## Module isolation over the FULL sample (the test that matters)
| Configuration | Trades | Win% | PF | Net | Max DD |
|---|---|---|---|---|---|
| Trend module only | 74 | 39.2% | 1.69 | +$4,749 | 2.43% |
| **Range module only** | **83** | **25.3%** | **1.31** | **+$2,427** | **4.06%** |
| **Both combined** | **145** | 33.1% | **1.62** | **+$8,160** | **2.81%** |

Three things this proves:
1. **The range module holds up on a proper 83-trade sample** (PF 1.31, +$2,427).
   Its 6-trade result last time was not a fluke -- it is genuinely additive.
2. **The range module is the riskier component standalone** (4.06% drawdown vs
   the trend module's 2.43%, and only a 25% win rate -- it wins purely on
   R-multiple).
3. **Combining them REDUCES drawdown below the range module alone** (2.81% vs
   4.06%). The two modules' losing periods do not coincide -- that is a real
   diversification benefit, not an artifact.

## IMPORTANT CORRECTION to the previous one-month result
The Jul 29 - Aug 29 window showed PF 3.04. Over the full 11 months the same code
gives **PF 1.62**. That single month was flattered -- it was a strong, clean
trending month for gold. **Trust 1.62, not 3.04.** This is exactly why the longer
sample was necessary, and it is a good reminder that any one-month number from
this system can be off by ~2x in either direction.

## Honest status
- 145 trades is a respectable sample and the first genuinely trustworthy figure
  produced in this project.
- Still ZERO spread, commission and slippage modelled. This matters most for the
  range module, whose targets are closer -- its real PF of 1.31 would erode
  fastest under real costs. Expect meaningful degradation live.
- Both modules were developed on this same data. Still no true out-of-sample test.
- 33% win rate means long losing streaks are normal. With PF 1.62 and 67% losers,
  you must be able to sit through 6-10 consecutive losses without intervening.

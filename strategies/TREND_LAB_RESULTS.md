# Trend lab + positive control — a direction never tested, and a harness check

## 1. Positive control (the check I should have run at the start)

Everything before this was a negative result. A negative result is only worth
anything if the measuring instrument can detect a positive one. I had never
verified that.

Mode 4 — buy 40oz of gold on the first bar and hold: **+$24,350**, detected
cleanly. **The harness works.** Every earlier negative finding stands as a real
result, not an artifact of a broken rig.

(I do not trust the $1,823 drawdown it reported for a single never-closed
position — gold fell $361 inside this window, which is ~$14k on 40oz. TradingView's
drawdown accounting for one open trade is unreliable, so I am not using it.)

## 2. A direction never tested: higher timeframe, directional

All prior work was intraday, 15m, symmetric long/short. Gold has been in a
strong multi-month uptrend. 4H trend following on spot XAUUSD, 11 months:

| mode | n | win% | PF | net | max DD |
|---|---|---|---|---|---|
| control: always long | 1 | — | ∞ | +$24,350 | n/a |
| 1 EMA cross, both sides | 31 | 29.0% | 0.999 | −$5 | 5.21% |
| 2 long only | 15 | 33.3% | **1.206** | +$600 | 5.23% |
| 3 short only | 16 | 25.0% | **0.769** | −$635 | 3.59% |
| 5 EMA cross + ATR trail, both | 31 | 41.9% | **1.331** | **+$1,768** | 4.64% |

### Two findings that are real

**The short side is the bleed.** Long-only PF 1.206, short-only PF 0.769, and
together they cancel almost exactly to PF 0.999. Consistent with the control:
gold went up all sample, so longs pay and shorts don't.

**Trailing exits beat fixed stops on identical entries** — PF 0.999 → 1.331,
+$1,773 swing, from changing nothing but the exit. This is the same "the exit
carries the edge" hypothesis that the verified trade suggested, and here it
finally shows up in a configuration that is not underwater.

## 3. Why it still does not pass the evaluation

Best result: **+$1,768 with a $2,442 max drawdown.**

The LucidDaily MLL is **$2,000**. That configuration **breaches before it ever
reaches +$3,000.** Sizing down to fit the MLL scales the profit down with it:
half size gives ~$884 profit against ~$1,221 drawdown, which needs roughly three
years to reach target.

The governing number is return-to-drawdown: **0.72 over eleven months.** Passing
this evaluation needs better than 1.5 achieved within weeks. That is not a
tuning gap, it is an order of magnitude.

## 4. Honest position

The long/short asymmetry and the trailing-exit result are genuine and worth
keeping — they are the first two things in this project that improved a real
metric for a reason I can explain and did not evaporate. But:

- 15–31 trades is a small sample.
- The long bias is a directional bet on gold continuing up, not an edge. It
  inverts in a downtrend, and gold fell $361 inside this very window.
- It is in-sample and unvalidated.
- Most importantly it fails the actual objective on drawdown, not on profit.

I will keep going, but I am not going to present a config that breaches the MLL
as a solution, and I am not going to tune this one until it looks good — that is
exactly how the 54% win-rate result earlier in this repo was produced, and it
failed out-of-sample.

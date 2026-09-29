# V22 PROD — how to run it, and what to expect

Fully automated. No manual input at runtime.

## Setup

1. TradingView chart: **COMEX_MINI:MGC1!**, **15 minute** timeframe.
2. Load `V22_XAU_prod.pine` into the Pine editor, compile, add to chart.
3. Leave every input at its default. They are the values that were tested; the
   defaults are the configuration, not a starting point for tuning.
4. Set `Start (UTC)` to the day you begin the evaluation. Leave `End` in the
   future.
5. For live trading, connect TradingView alerts on order fills to your broker
   bridge, or run the same rules in your execution platform. The strategy is
   self-contained: it decides entry, stop, target, size, and when to stop.

The `STATUS` box on the chart reads `running` / `PASSED` / `BUST`, with the live
balance, the current MLL floor, remaining buffer, and the risk it will use on the
next trade.

## What it does each trade

    signal   a swing high is swept, then price closes back below it within 6 bars
             (short side only -- the long side tested negative)
    stop     just beyond the swept extreme, and the setup is REJECTED outright if
             that stop is wider than $12 or tighter than $2
    target   3R
    size     floor(risk / (stop x $10)) MGC contracts, where
             risk = 15% of (balance - max-loss floor), capped at $750
             if that funds less than one contract, take ONE anyway, but only if
             the remaining buffer can absorb a 1.3R adverse excursion
    session  entries 13:00-21:00 UTC, forced flat by 19:30 UTC
    guards   stop trading for the day after -2R; stop entirely at +$3,000

## Expected outcomes — read this before running it

The signal has **no demonstrated edge**. A pre-registered screen across 8 signals,
4 markets and 2 eras (~16,000 trades) found gross expectancy of +0.016R, which is
zero within noise. This setup's own 95% confidence interval on profit factor is
0.926 to 1.851 — it contains 1.0.

So the honest forecast is a range, not a number. From 20,000 bootstrap runs:

| if the edge is... | pass | bust | stalls out |
|---|---|---|---|
| real (PF 1.33) | 70.1% | 0.4% | 29.5% |
| absent (PF 1.00) | 24.3% | 1.0% | 74.7% |
| slightly negative (PF 0.93) | 16.1% | 1.0% | 82.9% |

Weighting toward what the evidence actually supports: **roughly a 30% chance of
passing, about 1% chance of busting, and the rest stalling out without reaching
the target.**

Three real attempts on MGC1! at different start dates: one passed ($53,226 in 130
trades), two still running and profitable (+$1,554 and +$1,589). None busted.

## Why busting is close to impossible

Risk is a fixed fraction of the distance to the max-loss floor. After a full
loss the buffer becomes `buffer × 0.85`, which decays geometrically and never
reaches zero. **A losing streak cannot bust this account.** Busting requires one
trade losing about 6.7× its intended risk in a single event — a gap, halt or
limit move straight through the stop. The largest loss across 162 real fills was
1.24×.

That is the residual risk, and no backtest can measure it. It is the reason the
buffer fraction is 15% rather than 30%.

## The realistic way to use this

Treat it as a low-cost repeated attempt, not as a system that will pass. The
failure mode is designed to be *stalling* — the account survives, shrinks its
risk, and stops making progress — rather than blowing up. If an attempt stalls
for a month with the buffer under ~$500, close it and start a fresh one; you lose
the evaluation fee, never the account.

At roughly 30% per attempt, three attempts gives about a 66% chance of getting
through, at the cost of up to three evaluation fees.

**What this is not:** it is not $3,000 in a week, and it is not a validated edge.
Anyone quoting you the 70% figure without the 24% and 16% next to it is quoting
the best of three worlds and hiding the other two.

## If you want the odds to actually improve

The only lead left with real evidence behind it is your own trading. Your Aug 31
trade — entry 4439, stop 4429, target hit at 4479 — is a $10 stop returning 4R.
Nothing in the tested signal space does that. If that is repeatable, the edge is
in *which* levels you choose and *when* you decline to trade, and that
information has never been written down in a form a machine can execute.

Specifying those rules once, up front, is the highest-value thing you could do.
After that it runs automatically like everything above.

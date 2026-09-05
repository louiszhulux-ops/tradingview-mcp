# Setup family comparison — which setups are actually worth trading

Objective per the reset: **rank on risk-adjusted quality**, with days-to-pass
reported but never optimised. The 4-cell market × direction sign test is the
standing robustness gate, since it caught a contaminated result last round.

## Method

Eight families through one engine, so they are genuinely comparable. Every
family uses identical machinery: **retest entry** (limit at the level) →
**structural stop** (beyond the setup's own invalidation extreme) → **room ≥
10R** to the next opposing level → 5R target with a −1R stop, adverse excursion
checked first, costs subtracted in R. Run on MGC and MNQ, long and short.

One measurement bug found and fixed first: F5 trend-pullback originally stopped
at the last swing low, which pushed R past the 3×ATR cap and rejected 3,266 of
3,269 arms. A discretionary trader stops below the *pullback* low. Fixed, F5
fills 400 times.

## Result

| family | MNQ s | MNQ l | MGC l | MGC s | pooled | signs | n | /day | PF | t |
|---|---|---|---|---|---|---|---|---|---|---|
| **F0 liquidity sweep** | +0.002 | +0.022 | +0.017 | +0.104 | +0.037 | **4/4** | 1,235 | 17.3 | 1.04 | +0.54 |
| **F6 range mean-rev** | +0.114 | +0.394 | −0.002 | +0.068 | **+0.134** | 3/4 | 1,335 | 18.7 | **1.15** | **+1.94** |
| F5 trend pullback | −0.095 | +0.230 | −0.169 | −0.165 | −0.074 | 1/4 | 1,548 | 21.6 | 0.93 | −1.24 |
| F4 structure break+retest | −0.112 | +0.160 | −0.365 | −0.038 | −0.095 | 1/4 | 412 | 5.8 | 0.91 | −0.85 |
| F1 breakout + acceptance | −0.517 | −0.292 | −0.128 | +0.220 | −0.146 | 1/4 | 259 | 3.6 | 0.86 | −1.05 |
| F3 displacement + retest | −1.047 | −1.016 | +1.956 | −1.034 | −0.181 | 1/4 | 7 | 0.1 | — | −0.23 |
| F2 failed breakout | −0.082 | −1.084 | −0.562 | −0.322 | −0.449 | **0/4** | 128 | 1.8 | 0.56 | **−2.75** |
| F7 opening range break | −0.291 | −0.587 | −1.122 | −0.822 | −0.714 | **0/4** | 61 | 0.9 | 0.32 | **−3.89** |

**Six of eight fail.** Two are *significantly negative*: opening-range break
(t = −3.89) and failed breakout (t = −2.75) — these are not neutral, they are
losing setups on this data.

**Trend pullback fails at 1/4 with n = 1,548.** It is the most widely taught
intraday setup there is, it has the highest raw frequency of any family, and it
does not survive the direction test.

**F3 displacement+retest is unmeasurable, not bad**: 7 fills from 1,676 arms.
After a 2×ATR bar price essentially never returns to the midpoint. That is the
Phase 9 missed-retest failure mode in its purest form, and it is a genuine
market fact rather than a coding artefact (unlike F5).

## Trading quality of the two survivors

| | E[R] | win% | avgW | avgL | PF | MFE | MAE | sd | lambda | t | n | /day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F6 range mean-rev | +0.134 | 22.4% | 5.0 | −1.0 | 1.15 | 2.11 | 2.32 | 2.52 | 0.042 | +1.94 | 1,335 | 18.7 |
| F0 liquidity sweep | +0.037 | 19.7% | 5.0 | −1.0 | 1.04 | 2.05 | 1.98 | 2.39 | 0.013 | +0.54 | 1,235 | 17.3 |

**F6 is the better trading system**: 3.6× the expectancy, better profit factor,
3.3× the lambda. F0 is more robust by sign (4/4) but its edge is small enough
that it may not be an edge at all (t = +0.54).

### Losing streaks are the binding risk

At a 22.4% win rate the loss runs are brutal and frequent:

| run | probability | expected once per | in days at 18.7/day |
|---|---|---|---|
| 5 losses | 0.281 | 4 trades | 0.2 |
| 10 losses | 0.079 | 13 trades | 0.7 |
| 12 losses | 0.047 | 21 trades | 1.1 |
| 15 losses | 0.022 | 45 trades | 2.4 |
| 20 losses | 0.006 | 162 trades | 8.6 |

A 12-loss run happens **about once a day**. Any sizing that cannot absorb 15–20
consecutive losses will bust regardless of expectancy. This — not the edge — is
what sets position size.

## Evaluation performance (secondary, reported not optimised)

F6, 18.7 opportunities/day, R ≈ $55 per micro contract:

| risk/trade | buffer | pass | bust | median days | ≤2d | ≤3d | ≤7d |
|---|---|---|---|---|---|---|---|
| **$55** | 36.4R | **97.6%** | **2.4%** | 20 | 0% | 0% | 0% |
| **$110** | 18.2R | **84.1%** | 15.9% | 10 | 0% | 0% | 14.6% |
| $165 | 12.1R | 72.1% | 27.9% | 6 | 0% | 0% | 49.4% |
| $220 | 9.1R | 73.5% | 26.5% | 5 | 0% | 5.5% | 65.7% |
| $330 | 6.1R | 67.1% | 32.9% | 3 | 6.2% | 42.2% | 67.0% |

**The quality-first choice is $55–110 per trade**: 84–98% pass with 2–16% bust,
passing in 10–20 days. Going to $330 buys a 3-day median at the cost of doubling
the bust rate — by the standard you set, that is the worse system even though it
is faster.

## Honest limits

- F6 is the best of eight families, so winner's curse applies. t = +1.94 is
  marginal and one of its four cells is flat (MGC long, −0.002).
- **F0 and F6 may be the same effect.** Both are "fade an extreme": F0 fades a
  swept level, F6 fades a 20-bar range extreme in low ADX. Their similar
  frequency and MFE/MAE profiles suggest overlap that I have not measured.
- Everything here is one 72-day window on two instruments. No walk-forward on
  the family comparison yet.

## What this changes

The room filter and the retest entry survive as engine components. The setup
question is now answered: **fade-at-extreme families work, continuation
families do not**, on this data. That is consistent with F0's sweep result and
inconsistent with the trend-continuation framing in the original notes — worth
raising, because the human's described process is continuation-flavoured while
the measurements keep selecting mean-reversion.

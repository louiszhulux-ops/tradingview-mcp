# V36 — The frequency question, answered

You approved testing "far fewer, much larger trades". Measured end to end, that
direction is **wrong**, and the reason is a trade-off I had not written down.

## The model the whole search reduces to

V35 established that the execution drag is roughly **fixed in dollars**, not in
R: ~$1.04 commission + ~$2.00 slippage + ~$1.35 fill timing ≈ **$4.40/trade**.
So for a stop of `s` dollars per contract and a gross R-edge `g`:

    net E(s) = g − D/s          drag shrinks as a fraction of R
    L(s)     = $2,000 / s       but the buffer coarsens just as fast

Maximising `λ·L` gives an **interior** optimum at `s* = 2D/g`. Wider is not
monotonically better, which is what I had assumed when I proposed this.

At the gross edges actually measured (+0.06 to +0.12R), `s*` is **$75–150 per
contract**. On micro gold that is 5-minute bars — not daily. On daily bars a
1.5×ATR gold stop is $750, so the $2,000 limit is **2.7R wide** and three losses
end the account.

## Measured: timeframe sweep, MGC1!, real costs, real fills

Research mode (no daily gates, 1 contract, full history):

| timeframe | stop/ctr | trades | net avg R |
|---|---|---|---|
| 3m | $82 | 1,919 | −0.0296 |
| **5m** | **$107** | **1,975** | **+0.0379** |
| 15m | $207 | 2,330 | +0.0100 |
| 60m | $407 | 2,363 | −0.0499 |

Monotone decline above 5m. The fade is a short-horizon effect and it dies as the
horizon lengthens **faster** than the drag falls. Going the other way, 3m is
negative too: the stop drops to $82 and the fixed drag takes over.

## Measured: contract sweep at 5m

| contract | stop/ctr | trades | net avg R | drag | implied gross |
|---|---|---|---|---|---|
| MGC micro gold | $107 | 1,975 | **+0.0379** | 0.041 | +0.079 |
| MNQ micro nasdaq | $86 | 2,278 | **+0.0217** | 0.051 | +0.073 |
| MES micro S&P | $36 | 2,210 | −0.0564 | 0.123 | +0.067 |
| CL crude | $229 | 2,051 | −0.0162 | 0.019 | +0.003 |
| SI silver | $1,265 | 1,964 | +0.1071 | 0.003 | +0.110 |

The implied gross edges cluster at **+0.067 to +0.079R** across gold, nasdaq and
S&P — matching V33's +0.081R pooled. The net result is decided almost entirely
by the dollar size of the stop. Silver has the best net edge and the worst
geometry: a $1,265 stop is 63% of the entire loss limit.

## Stop-width robustness at 5m on MGC

| stop | stop/ctr | trades | net avg R |
|---|---|---|---|
| 1.0×ATR | $71 | 2,103 | +0.0199 |
| **1.5×ATR** | **$107** | **1,975** | **+0.0379** |
| 2.0×ATR | $143 | 1,657 | +0.0123 |
| 2.5×ATR | $178 | 1,265 | −0.0275 |

Three adjacent positive cells at ~2,000 trades each. This is a plateau, not the
isolated spike the earlier gated sweep produced.

## A correction to V35

V35 reported MGC1! 5m/1.5×ATR at **−$1.33/trade over 281 trades**. That run had
the daily target ($375) and daily loss (8×risk) gates active. With the gates
removed the same configuration is **+$4.06/trade over 1,975 trades**. The gates
were cutting the sample to 14% of trades and selecting a losing subset — the
daily target stops the day after wins, the daily loss stop after losses, and
together they systematically drop the good tail. **The daily gates are harmful
and should not be in the production configuration.** V35's conclusion that the
signal is negative on the real instrument was an artifact of them.

## Honest bottom line

Best configuration in the entire project: **MGC1!, 5m, fade long-side momentum
triggers, stop 1.5×ATR(14), target 2R, up to 4 concurrent, 1 micro contract, no
daily gates.** Net **+0.0379R** after real commission, 1-tick slippage and
next-bar-open fills, over 1,975 trades — about 27 trades a day.

Under the verified LucidFlex rules with the trailing end-of-day MLL:

| net edge | | pass | bust | median days |
|---|---|---|---|---|
| +0.1640 | 95% CI upper | 90.6% | 9.3% | 19 |
| **+0.0379** | **point estimate** | **46.5%** | **53.5%** | 24 |
| +0.0190 | half of it | 37.2% | 62.8% | 25 |
| −0.0882 | 95% CI lower | account bleeds out | | |

t = 0.59. The 95% interval is [−0.088, +0.164] and contains zero comfortably.

Note the fixed-floor approximation flattered this at 61%; the real trailing
floor gives **46.5%**. A coin flip, on an edge that is not statistically
distinguishable from nothing.

## What is now known with confidence

`net = gross − $4.40/stop$`, with `gross ≈ +0.075R` on every liquid contract
tested. The only lever that matters is the dollar size of the stop, and it is
bounded on both sides — too small and the fixed drag eats it, too large and
$2,000 is too few R to survive. MGC at 5m sits at $107, essentially exactly the
optimum `2D/g = $117`. **There is no configuration of this signal left to find.**

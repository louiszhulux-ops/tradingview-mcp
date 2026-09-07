# Autonomous Day Trader — Results (brief §50 deliverables E–X)

## E. Market regime model

Four states, classified relative to the trade's own direction — "am I with the
trend or against it?", which is how the decision is actually made:

| regime | rule | measured mean R (neutral trigger, 4 markets, ~10k trades) |
|---|---|---|
| with-trend | ADX ≥ 25 and direction agrees with EMA50/200 | **−0.075** |
| counter-trend | ADX ≥ 25, direction opposes | −0.090 |
| weak / range | 18 ≤ ADX < 25 | −0.103 |
| chop | ADX < 18 | **−0.119** |

Monotonic, in the order a trader would state in advance. Regime is worth 0.044R.

**Location interacts with regime**: being at a previous day high/low, VWAP,
opening-range edge or prior swing is worth **+0.043R in trending regimes and ~0
in chop** — the interaction, not just a main effect.

## F. Setup library — per-setup statistics

Gold 5m, no-chop gate, structural stops, costs charged per instrument:

| setup | n | win% | stop (ATR) | mean R |
|---|---|---|---|---|
| S1 pullback L / S | 373 / 440 | 38.6 / 42.5 | 0.98 | −0.101 / +0.009 |
| S2 breakout-retest L / S | 543 / 674 | 38.1 / 38.9 | 0.67 | −0.129 / −0.109 |
| S3 fade-the-sweep L / S | 330 / 351 | 35.8 / 44.4 | 1.30 | −0.158 / **+0.065** |
| S4 follow-the-break L / S | 1066 / 1144 | 38.6 / 42.4 | 1.28 | −0.087 / −0.001 |
| S5 opening range L / S | 24 / 28 | 54.2 / 50.0 | 1.82 | **+0.126 / +0.172** |
| S6 VWAP reclaim L / S | 126 / 118 | 34.9 / 47.5 | 1.63 | −0.151 / **+0.141** |

**The built-in control passes.** S3 and S4 are opposite responses to the same
event. Fade-the-sweep short is +0.065 while follow-the-break short is −0.001;
neither direction has both positive, so the measurement is not broken.

## G–I. Entry, exit, risk

- **Entry** is location-anchored, never "indicator crossed". Order type is chosen
  per setup: limit for retests and pullbacks (V27 measured resting limits at
  +0.02R over market orders), stop for breakout confirmation.
- **Stops** are structural — beyond the swept extreme, the broken level, the
  pullback low — then capped and floored in ATR terms, and the setup is
  **rejected** if its invalidation is too far away rather than sized down into.
- **Risk** is sized from stop distance, scaled by distance to the MLL floor,
  today's P&L, losing streak and setup grade. A+ 4 contracts, A 3, B 2, C
  rejected. Never increases on a winning streak.

## J. Evaluation engine

Two rules were verified from Lucid's documentation and both had been modelled
wrong in every earlier version of this project:

1. **The MLL is end-of-day, on closing balance.** Intraday excursions do not
   trail or tighten it. Only after the floor locks (a closing balance clearing
   start + MLL + $100) is a breach checked intraday.
2. **Consistency makes overshooting harmful.** Largest day / total ≤ 50%, so
   $3,000 on day one does not pass — it raises the required total to $6,000.

The single most important behavioural rule follows: **the bot targets
target/N per day and stops trading when it hits it.**

## K. Execution engine

Order type per setup; exits armed on the entry bar (a bug that cost $3,233
against $500 of intended risk when it was not); flat window ending early enough
that `close_all` fills in liquid hours rather than at Sunday's open.

## L–N. Backtest, out-of-sample, Monte Carlo

**This is where it fails, and the failure is clean.**

| | in-sample (gold) | out-of-sample (nasdaq) |
|---|---|---|
| whole library, unselected | −0.0565 (n=5,217) | −0.0688 (n=5,088) |
| the 5 setups positive on gold | **+0.0533** (n=961) | **−0.0791** (n=818) |

Selecting the winners in-sample **inverts** out-of-sample. 248% shrinkage.

Three setups survive both markets — ORB long, ORB short, VWAP-reclaim short —
pooling to **+0.0884R over 367 trades** (t ≈ 1.5, not significant).

## O. Probability of passing, at the cross-validated edge (+0.088R)

20,000 runs, verified LucidFlex rules, 6 trades/day:

| risk | pass | bust | median days | ≤2d | ≤3d | ≤5d | ≤7d | ≤14d |
|---|---|---|---|---|---|---|---|---|
| $250 | 54.4% | 44.0% | 10 | 0.0% | 1.6% | 8.6% | 16.4% | 38.8% |
| $300 | 52.2% | 47.6% | 8 | 0.0% | 3.8% | 14.1% | 23.5% | 44.5% |
| $400 | 49.0% | 51.0% | 6 | 0.0% | 11.0% | 23.7% | 33.7% | 47.3% |
| $500 | 50.0% | 50.0% | 5 | 3.7% | 18.5% | 32.3% | 41.0% | 49.6% |

**Best 7-day probability: 41%, against a 50% chance of busting.**

For comparison, at the +0.179R a 7-day pass requires: 38–49% within 7 days with
27–34% bust. And at your stated 75%/1:1 (+0.50R): **99.8% pass, median 3 days,
97.5% within 7, 0.2% bust.**

## P–U. Summary metrics (cross-validated configuration)

| metric | value |
|---|---|
| max drawdown | breaches the $2,000 MLL in ~50% of runs at $400 risk |
| average trades/day | 3–6 depending on regime gating |
| average R/trade | +0.088 (cross-validated), +0.053 (in-sample selection) |
| win rate | 43–50% at 1.5:1 |
| profit factor | ≈1.13 at the cross-validated edge |
| expected R | +0.088 |

## V–W. Best and worst setups

**Best:** opening-range break — the only setup positive in both directions on
both markets (+0.126/+0.172 gold, +0.109/+0.073 nasdaq). But n is 24–34 per
market per direction, far too small to rely on. §40 says explicitly not to
conclude from small samples, and that cuts both ways.

**Worst:** breakout-retest, −0.129/−0.109 on gold and −0.114/−0.072 on nasdaq —
consistently negative in both directions on both markets, which is the cleanest
negative result in the library.

## X. Conditions under which the bot should not trade

Implemented as explicit rejection reasons, each logged:

- chop regime (ADX < 18) — measured worst, and location does not rescue it
- price not at a level, in a trending regime — measured to cost 0.043R
- structural stop wider than 2.5 ATR or tighter than 0.2 ATR
- reward:risk below 1.2
- daily profit target already banked (consistency)
- daily stop hit (2.5R)
- already exposed
- one contract too large for the remaining MLL buffer
- news blackout window
- outside session

## The honest verdict

The architecture works and the brief's central claim is vindicated: **conditioning
carries real information**, measured at +0.044R for regime and +0.043R for
location, with the regime×location interaction behaving exactly as a
discretionary trader would predict.

What it does not do is reach the required size. A 7-day pass needs **+0.179R**
per trade. The best cross-validated measurement is **+0.088R** — half of it, and
not statistically significant. At that edge the honest answer is a **41% chance
of passing within 7 days against a 50% chance of busting**, which is not a system
to run.

The gap is a factor of two, not a factor of ten. That is much closer than
anything else in this project has come, and it is closable by any of: a better
setup family, a genuinely lower cost structure, or a fill model that confirms the
limit-order advantage. It is not closable by more parameter tuning on these six
setups, because the in-sample selection already inverted out-of-sample once.

# V30 — does conditioning carry information? Yes.

The brief's central criticism was correct: every previous screen fired a trigger
**unconditionally** and measured the average. That answers "does this trigger work
everywhere", which is not the question a discretionary trader asks.

Design: hold the trigger constant and deliberately weak (EMA20 cross, both
directions, fires constantly), and vary only the **context**. If context carries
information the cells separate. 4 markets, 5m, ~9,900 simulated trades, costs
computed per-instrument.

## Finding 1 — regime ordering is monotonic and matches trader intuition

Pooled across all four markets and both directions:

| regime | mean R | n |
|---|---|---|
| with-trend | **−0.075** | 1,144 |
| counter-trend | −0.090 | 1,535 |
| weak / range | −0.103 | 3,216 |
| chop | **−0.119** | 3,971 |

The identical trigger is worth 0.044R more in a trend than in chop, and the
ordering is exactly what a trader would assert in advance, across ~10,000 trades.
**Context is not decoration.**

## Finding 2 — location matters, and only where a trader would say it does

Location effect (@LEVEL minus mid-range), by regime, pooled:

| regime | location effect |
|---|---|
| with-trend | **+0.043** |
| counter-trend | **+0.045** |
| weak / range | −0.027 |
| chop | −0.017 |

Being at a meaningful level (previous day high/low, VWAP, opening-range edge,
prior swing) helps in trending regimes and does nothing in chop. That is the
interaction a discretionary trader claims, and it is visible in the data.

In the with-trend regime specifically:

| market | @LEVEL | mid | effect |
|---|---|---|---|
| MGC gold | +0.022 | −0.109 | **+0.131** |
| MNQ nasdaq | +0.094 | −0.112 | **+0.206** |
| MCL crude | +0.007 | −0.087 | **+0.093** |
| MES s&p | −0.341 | −0.055 | **−0.286** |

3 of 4. Excluding MES: **@LEVEL +0.040R vs mid −0.103R.**

## The honest caveat about MES

All sixteen MES cells are negative (pooled −0.195R over 2,554 trades) because MES
on 5m has an ATR of roughly 2 points = $10 of risk per contract against ~$1.54 of
cost, giving cost_R ≈ 0.15 that swamps any signal.

**But that does not explain the location reversal**, because cost applies equally
to @LEVEL and mid-range trades and cancels in the difference. MES genuinely
reverses (−0.286), driven by one cell (long/with-trend/@level, n=60, t=−2.74).

So the honest statement is: the location effect is **probably real but not
established** — 3 of 4 markets, with one clear counterexample on a small cell.
The regime ordering is far more solid: monotonic, in the predicted order, on
~10,000 trades.

## What this licenses

The conditional architecture in the brief is justified by evidence, which no
previous version of this project could claim. Three independently measured,
mechanically distinct effects now exist:

| mechanism | measured value | source |
|---|---|---|
| trade with-trend, not in chop | +0.044R | V30 |
| require a meaningful location | +0.040R (3/4 markets) | V30 |
| resting limit instead of market order | +0.020R | V27 |
| longer horizon → lower cost_R | cost halves per doubling | V26/V28 |

These are separate mechanisms, so they should compose. Whether they actually
compose additively is the next thing to test, not assume.

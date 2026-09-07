# State of play

One page. Everything else is in `strategies/` and `trader/`.

## The production configuration

**COMEX_MINI:MGC1! (micro gold), 5-minute.** Fade long-side momentum triggers
(short) — 20-bar break, sweep-and-reclaim, EMA20 pullback, VWAP reclaim — but
**only when ATR(14) ≥ 1.5 × SMA(ATR,100)**. Stop 1.5×ATR (~$106/contract),
target 2R, **one** position at a time, 1 micro contract, no daily gates.

Rig: `strategies/V38_fade_vol_prod.pine`. Deployment and forward protocol:
`strategies/V38_DEPLOYMENT.md`.

| measured end to end, real commission + 1-tick slippage | |
|---|---|
| avg R/trade | **+0.1178** (selection-free: +0.0801) |
| trades/day | 1.39 |
| win rate | 37.0% |
| max drawdown | 13.5R = 71% of the $2,000 buffer |
| **pass probability** | **45.3%–59.4%**, median ~130 days |

**That is roughly a coin flip taking four to seven months.** It is the best
configuration in the project and it is not a viable evaluation plan.

## What is actually established

1. **The fade replicates.** Long-side momentum triggers have negative
   expectancy; the trade against them is positive. 8/8 markets, t = 3.5 gross.
2. **The volatility filter replicates and roughly doubles the gross edge**
   (+0.081R → +0.134R). 6/7 out-of-sample markets, p = 0.055. Survives a
   three-fold walk-forward on both tradeable contracts and is a plateau in its
   threshold, not a spike.
3. **`net = gross − D/stop$`** with D ≈ $2–4.40 fixed per trade and gross
   ≈ +0.075R (unconditional) on every liquid contract. Confirmed across eleven
   contracts. The dollar size of the stop is the whole game.
4. **Drawdown-to-buffer, not edge, is the binding constraint.** MNQ has 2× the
   edge and busts; silver has 3× and busts. Stop width cannot change the ratio —
   only the account can.
5. **Concurrency is expensive.** Four concurrent positions in one instrument
   during a volatility burst are one leveraged bet: cutting 4→1 removed 21.8R
   of drawdown for 0.074R of edge.

## What is dead, with the measurement that killed it

- Nine textbook entries, ICT/FVG/MSS, opening range, VWAP fade, sweep-reclaim
  as a standalone, the eight-signal pre-registered screen, the setup library.
- **The payoff ratio** (V32): `edge/a` is flat, so a 77–80% win rate is
  available at a 0.25R target and sits *below* the 80% that target needs.
- **Fewer, larger trades** (V36): monotone decline above 5m; daily bars leave
  the loss limit 2.7R wide.
- **ADX, session, extension and run-length conditioning** (V33, V37): the two
  best-looking cells inverted sign on the second market.

## Three corrections I had to make to my own claims

- V33's 81% pass figure was built on the rig's fill assumption. Superseded.
- V35 reported the signal *negative* on the real instrument; that was an
  artifact of my own daily gates, which cut the sample to 14% of trades.
- A drafted forward-test claim of "85% disconfirmation power" was wrong; the
  real figure is 22% at 250 trades.

## Open, and honest about it

- Forward testing **cannot confirm** this edge — t=2 needs 1.2–2.5 years. The
  forward test is scoped to execution validation, a 15R drawdown tripwire, and
  a long-run ledger. Rules pre-registered in `V38_DEPLOYMENT.md`.
- The Monte Carlo assumes independent trades. Three times now the empirical
  sequence has given a different answer, most sharply when silver on a 100K
  account scored 99.2% in simulation and **froze at 22 trades** in reality.
- A larger account changes the picture materially (MNQ survivable at 100K,
  silver at 150K, both with 2–3× the edge). That is a capital decision, flagged
  not recommended — there is no out-of-sample evidence at those sizes.

## Forward test baseline

V38 is live on COMEX_MINI:MGC1! 5m. Baseline: 100 trades, net $1,243,
avg R +0.1178, max DD $1,424. Read with `data_get_pine_tables`
(`study_filter: "FADE-VOL"`); forward avg R = (net − 1243) / ((trades − 100) × 105.56).

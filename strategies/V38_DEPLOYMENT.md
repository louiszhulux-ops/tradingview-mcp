# V38 — Production configuration and forward-test protocol

## The configuration

| | |
|---|---|
| instrument | **COMEX_MINI:MGC1!** (micro gold), 5-minute |
| signal | fade long-side momentum triggers → **short** |
| triggers | 20-bar break, sweep-and-reclaim, EMA20 pullback, VWAP reclaim |
| **filter** | **only when ATR(14) ≥ 1.5 × SMA(ATR,100)** |
| stop | 1.5 × ATR(14) ≈ $106/contract |
| target | 2R |
| concurrency | **1 position** |
| size | 1 micro contract (buffer sizing, 5.5% of MLL buffer) |
| daily gates | **off** — V36 measured them harmful |

Every position carries its own protective stop from the bar it opens on.

## Measured, end to end, with real commission and 1-tick slippage

| | |
|---|---|
| trades | 100 over 72 days (**1.39/day**) |
| avg R/trade | **+0.1178** (selection-free estimate: **+0.0801**) |
| win rate | 37.0% |
| profit factor | 1.157 |
| max drawdown | $1,424 = **13.5R** = 71% of the $2,000 buffer |
| best day / total | 0.495 (consistency limit is 0.50 — *tight*) |
| net over 72 days | +$1,243 — did **not** complete the $3,000 target |

Pass probability under verified LucidFlex rules: **45.3%** at the
selection-free edge, 59.8% at the measured edge; median **132–142 days**.

## Why MNQ is excluded despite a bigger edge

| | MGC | MNQ (4 slots) | MNQ (1 slot) |
|---|---|---|---|
| avg R | +0.118 | +0.295 | +0.221 |
| max drawdown | 13.5R | 47.2R | 25.4R |
| buffer | 18.9R | 24.5R | 24.5R |
| DD / buffer | **71%** | 193% | 104% |

MNQ's drawdown is **3.93×** what independent trades predict, against 1.23× for
MGC. The volatility filter concentrates trades into bursts, and on MNQ those
bursts lose together. Cutting concurrency 4→1 removed 21.8R of drawdown for
0.074R of edge — the best risk trade found — and it *still* exceeds the buffer.
**Drawdown-to-buffer, not edge, is the binding constraint.**

## Threshold is a genuine optimum, verified twice

| volCut | trades/day | avg R | max DD |
|---|---|---|---|
| 1.3 | 3.17 | +0.0512 | 22.9R — busts |
| **1.5** | **1.39** | **+0.1178** | **13.5R** |
| 1.7 | 0.53 | +0.0627 | 13.7R |

Same peak in V37's independent rig. Relaxing to 1.3 gives 2.3× the trades for
the *same total profit* — the filter is doing real work.

## Forward test — what it can and cannot settle

Power analysis in `v38_forward_power.py`. The honest position:

- **Confirmation is out of reach.** Reaching t=2 needs 589–1,275 trades, i.e.
  **1.2–2.5 years** of forward trading.
- **Disconfirmation by t-test is also weak** — 22% power at 250 trades, 30% at
  400. A forward t-test is nearly useless in both directions.

So the forward test is for three other things:

1. **Execution validation** (~30 trades, ~3 weeks, pass/fail):
   realised stop within 10% of 1.5×ATR; slippage ≤ 1 tick/side; frequency
   1.0–1.9/day; win rate 30–45%; every trade resolves inside 288 bars.
2. **Drawdown tripwire** — the rule that actually binds. Historical worst is
   13.5R; the account dies at 18.9R. **Stop at 15R.**
3. **A long-run ledger**, reviewed quarterly.

### Pre-registered stop/continue rules

- **CONTINUE** if execution checks pass and drawdown < 15R.
- **STOP** if any execution check fails, or drawdown hits 15R, or cumulative R
  < −8R after 100+ trades.
- **DECLARE NOTHING** before 400 trades (~10 months). A profitable first month
  does not confirm this and a losing one does not refute it — both sit inside
  one standard deviation.

## Baseline snapshot — the forward test starts here

V38 is loaded on **COMEX_MINI:MGC1!, 5m**, production settings, and will keep
computing as new bars arrive. The forward result is the *difference* between a
future reading and this baseline:

```
net profit      1243.00
trades              100
win%               37.0
profit factor     1.157
max DD          1424.40
days                 72
trades/day         1.39
stop $/ctr       105.56
avg R/trade      0.1178
```

To read it later: `data_get_pine_tables` with `study_filter: "FADE-VOL"` on
that chart. Forward avg R = (net_now − 1243.00) / ((trades_now − 100) × 105.56).

## Standing caveats

- 45.3% pass at the selection-free edge is **not** a viable evaluation plan.
- Median 132–142 days is 6–7 months of trading.
- Consistency sits at 0.495 against a 0.50 limit — one outsized day fails it.
- The whole result rests on a conditioner selected from 24 cells, validated on
  6/7 out-of-sample markets at p = 0.055. That is suggestive, not established.

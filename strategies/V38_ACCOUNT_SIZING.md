# V38 — Contract and account sizing: the constraint is drawdown, not edge

## The sweep

V38 (fade + vol>1.5 filter, 1 concurrent, real commission and 1-tick slippage)
run in research mode across every micro contract with usable geometry:

| contract | stop/ctr | trades/day | avg R | max DD $ |
|---|---|---|---|---|
| MYM micro Dow | $18 | 3.81 | −0.213 | 1,247 |
| M2K micro Russell | $17 | 3.11 | −0.157 | 1,268 |
| MES micro S&P | $36 | — | −0.056 | — |
| MNQ micro nasdaq | $82 | 2.51 | +0.221 | 2,077 |
| MGC micro gold | $106 | 1.39 | **+0.118** | **1,424** |
| SIL micro silver @1.5×ATR | $239 | 1.90 | **+0.378** | 3,024 |
| SIL @1.0×ATR | $159 | 2.33 | +0.350 | 2,330 |
| SIL @0.75×ATR | $119 | 2.53 | +0.315 | 2,416 |

MYM and M2K have stops under $20, so the ~$2 fixed cost alone is >0.10R and
they are negative before anything else. That is the same `net = gross − D/stop`
law from V36, now confirmed across eleven contracts.

## Dollar drawdown vs dollar loss limit — the only test that matters

| contract | max DD | 25K ($1,000) | 50K ($2,000) | 100K ($3,000) | 150K ($4,500) |
|---|---|---|---|---|---|
| MGC | $1,424 | bust | **ok** | ok | ok |
| MNQ | $2,077 | bust | bust | ok | ok |
| SIL @1.5 | $3,024 | bust | bust | bust | ok |
| SIL @1.0 | $2,330 | bust | bust | ok | ok |

**Stop width does not rescue anything.** SIL's drawdown is $3,024 / $2,330 /
$2,416 at 1.5 / 1.0 / 0.75 ×ATR — essentially constant in dollars. Tightening
the stop shrinks R but lengthens losing streaks *in R*, leaving the dollar
drawdown unchanged. The ratio is invariant, so only the **account** can change it.

**On the 50K account, MGC micro gold is the only survivable contract**, and it
is not the one with the best edge.

## The risk engine has a stall mode — found the hard way

SIL on a 100K account looked excellent in the independent-trade Monte Carlo:
99.2% pass, median 65 days. Running the actual sequence, it **froze at 22
trades**. An early $2,667 drawdown left $332 of buffer, and the sizing rule
(`take 1 contract only if buffer > 3 × per-contract risk`) then refused every
subsequent trade. The account was alive, unable to trade, and could never
recover — neither pass nor bust.

The research-mode +$9,360 on the same contract is only reachable if you survive
that early hole. **The Monte Carlo said 99.2% because it assumed independent
trades; the real sequence front-loads its worst drawdown.** This is the third
time in this project that trusting the empirical sequence over the iid model
changed the answer, and it should now be the default.

On 150K SIL survives (+$7,825 in 72 days, did not reach the $9,000 target) but
its drawdown reaches $4,055 against a $4,500 limit — 90% of the way to failure
on the one path available.

## Why I stopped here

Continuing to search (contract × stop × threshold × account) on a single
72-day, one-instrument sample is exactly the overfitting the brief prohibits.
Eleven contracts, four thresholds and three stop widths is already a large
search space against ~100–170 trades per cell. The SIL/150K configuration is
**not** a recommendation — it is one path that survived, and I have no
out-of-sample evidence for it at that account size.

## Where this leaves the 50K account

The production configuration is unchanged and restored:
**MGC1!, 5m, vol > 1.5, 1 concurrent, 1 micro contract, no daily gates.**

- +0.1178R measured, +0.0801R selection-free
- 1.39 trades/day, 37.0% win, PF 1.157
- max drawdown 13.5R = 71% of buffer
- pass **45.3%** (selection-free) to 59.4% (measured), median ~130 days

That is the honest state: the best-supported configuration in the project, on
the account you hold, is roughly a coin flip taking four to seven months.

The one thing that would change it materially is a larger account — MNQ becomes
survivable at 100K and silver at 150K, and both have two to three times MGC's
edge. That is a capital decision, not a research result, and I am flagging it
rather than recommending it.

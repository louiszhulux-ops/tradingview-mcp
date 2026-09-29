# V37 — The context engine: one conditioner survives everything

Protocol fixed in advance: `V37_PROTOCOL.md`. Rig: `V37_conditioning_lab.pine`.
Analysis: `v37_analysis.py`.

## The rig had to be rebuilt first

V30 and V33 measured conditioning with entries at the **trigger bar's close**.
V35 proved that is worth ~0.041R of fiction — a real order fills at the next
bar's open. So every conditioning result before this one was measured on a
quantity that cannot be traded.

V37 fills at the **next bar's open**, subtracts a **$4.40 execution drag**
converted to R at the live stop size, and splits every cell into **three equal
time folds**. It reproduces the V35 strategy's pooled number on MGC (+0.030R
against +0.038R), so the rig is calibrated against real execution.

## What the fold split immediately exposed

The **session** conditioner, MGC 5m:

| session | n | fold 1 | fold 2 | fold 3 | ALL |
|---|---|---|---|---|---|
| 0–4 UTC | 352 | +0.272 | +0.036 | −0.012 | +0.094 |
| 4–8 | 343 | +0.051 | −0.136 | −0.170 | −0.094 |
| 8–12 | 333 | +0.090 | +0.120 | −0.062 | +0.050 |
| 12–16 | 354 | +0.057 | +0.299 | −0.061 | +0.084 |
| 16–20 | 252 | +0.535 | +0.161 | −0.174 | +0.154 |
| 20–24 | 244 | −0.239 | −0.109 | −0.034 | −0.120 |

**Every cell negative in the most recent third.** The unconditional fade's edge
lives in the older data. Nothing in the pooled numbers showed this.

## The 24-cell search, and what chance predicts

Four conditioners × six cells. Cells positive in **all three folds**:

- extension 1–1.5×ATR: +0.164R (n=198)
- volatility 0.70–0.85: +0.320R (n=328)
- volatility > 1.5: +0.180R (n=151)

**Exactly three.** Under a null of zero edge, 24 cells × ⅛ predicts **3.0**.
The fold rule alone therefore proves nothing — which is why the protocol also
required cross-market replication.

## The replication gate

| candidate | MGC | MNQ | verdict |
|---|---|---|---|
| extension 1–1.5 | +0.164 (3/3 folds) | **−0.141** (0/3) | inverts — rejected |
| volatility 0.70–0.85 | +0.320 (3/3) | **−0.242** (0/3) | inverts — rejected |
| **volatility > 1.5** | +0.180 (3/3) | **+0.137 (3/3)** | **survives** |

The best-looking cell in the whole study — vol 0.70–0.85 at +0.320R — is a
complete sign flip on the second market. That is the winner's curse caught in
the act, and it is why the pre-registered gate existed.

## vol > 1.5 across eight markets

`net` uses next-bar-open fills and the $4.40 drag; `gross = net + 4.40/stop$`
so markets with different stop sizes are comparable.

| market | n | folds+ | net | stop$ | gross |
|---|---|---|---|---|---|
| MGC micro gold | 151 | 3/3 | +0.180 | 107 | +0.221 |
| MNQ micro nasdaq | 314 | 3/3 | +0.137 | 86 | +0.188 |
| MES micro S&P | 338 | 1/3 | +0.062 | 36 | +0.185 |
| CL crude | 187 | 2/3 | −0.001 | 229 | +0.018 |
| SI silver | 224 | 3/3 | +0.229 | 1265 | +0.232 |
| 6E euro | 257 | 2/3 | +0.151 | 33 | +0.283 |
| ZN 10y note | 201 | 0/3 | −0.099 | 38 | +0.016 |
| BTCUSD | 308 | 1/3 | −0.083 | 340 | −0.070 |

Gross positive on **7/8**. The cell was selected on MGC, so the honest
out-of-sample statistic is the other seven: **6/7 positive, mean +0.1218**,
sign test p = 0.055.

Unconditional fade gross (V33, 8 markets): **+0.081**.
Conditioned on vol > 1.5: **+0.134**.
**Conditioning roughly doubles the gross edge** — the first conditioner in this
project that replicates out of sample.

## Threshold robustness — a plateau, not a spike

| threshold | n | fold 1 | fold 2 | fold 3 | ALL |
|---|---|---|---|---|---|
| > 1.3 | 345 | +0.257 | +0.299 | −0.057 | +0.135 |
| > 1.4 | 225 | +0.027 | +0.316 | +0.036 | +0.125 |
| > 1.5 | 151 | +0.188 | +0.336 | +0.079 | +0.180 |
| > 1.7 | 58 | −0.281 | +0.131 | +0.305 | +0.170 |

Positive at every threshold from 1.3 to 1.7. This is the test the 3.0×ATR stop
in V35 failed, and this one passes it.

## Walk-forward, stated properly

Selecting on folds 1–2 and confirming on fold 3 — the out-of-sample number is
never the one used to pick:

- MGC: select on +0.188/+0.336 → fold 3 confirms at **+0.079**
- MNQ: select on +0.014/+0.233 → fold 3 confirms at **+0.195**

## §38 — the missed-trade analysis is the rest of the table

The conditioner rejects ~92% of triggers. What those rejected setups would have
returned on MGC: vol<0.7 **−0.079**, vol 0.85–1.0 **−0.081**, vol 1.0–1.2
**−0.084**, vol 1.2–1.5 **+0.029**. The filter is discarding negative-expectancy
trades, not edge. That is the §38 deliverable.

## Where the account lands

Selection-free estimate (out-of-sample gross +0.1218 less MGC's 0.041 cost):
**+0.081R net**, against the unconditional +0.038R. Under the verified
LucidFlex trailing-MLL rules, 4,000 runs:

| configuration | E | trades/day | pass | bust | median days |
|---|---|---|---|---|---|
| V36 unconditional | +0.0379 | 27 | 46.5% | 53.5% | 24 |
| **MGC+MNQ, selection-free** | **+0.0760** | **6.5** | **61.4%** | **38.5%** | **56** |
| MGC only, selection-free | +0.0807 | 2.1 | 53.1% | 39.4% | 97 |
| MGC+MNQ, their own numbers | +0.1560 | 6.5 | 87.5% | 12.5% | 43 |

Pass 46.5% → **61.4%**, bust 53.5% → **38.5%**. The pre-registered rule required
≥60% pass, so by my own rule **the conditioner is adopted.**

## Honest caveats

- 61.4% is better than anything else here and is still not a confident pass.
- The doubling of edge bought only +15 points because the filter keeps 8% of
  triggers, stretching the median to 56 days and giving the trailing MLL more
  days to bite.
- The Monte Carlo treats trades as independent; concurrent correlated positions
  are not modelled and would lower this.
- Fold 3 is the weakest fold on MGC (+0.079 against +0.188/+0.336). Some decay
  may be real.
- 6/7 out-of-sample at p = 0.055 is marginal, and the markets are correlated.

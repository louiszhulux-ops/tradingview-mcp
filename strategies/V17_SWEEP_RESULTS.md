# V17 — the first system whose risk unit actually fits a 50K account

## What changed conceptually

V16 was a good edge (PF 2.1 out-of-sample) that could not be traded on this
account: a 3×ATR stop on 1H gold is ~$87, so **one MGC contract risks $868** —
1.74% of $50,000 against a $2,000 max loss limit. 2.3R of total buffer. Nothing
survives that, no matter how good the signal is.

V17 inverts the design. The stop comes from **market structure** — the extreme
of a liquidity sweep — and any setup whose structural stop is wider than a
dollar cap is **rejected rather than sized down into**.

    entry   short: price sweeps a swing high, then closes back below it
            within 6 bars (long side is the mirror)
    stop    the swept extreme + $1 buffer, capped at $12, floored at $2
    target  3R fixed
    flat    forced flat by 19:30 UTC, no overnight, no weekend
    session NY only (13:00–21:00 UTC)
    size    floor(risk / (stop × $10)) MGC contracts

Mean stop is **$6.95**, so one contract risks ~$70. At $500 of risk that is 7
contracts and ~28R of buffer against the MLL. The granularity problem is gone.

## Two more execution bugs, both material

**1. The entry bar was unprotected.** `strategy.position_size` is still 0 on the
bar an entry is submitted, so an exit guarded by `if strategy.position_size > 0`
is not placed until the *next* bar. With a $2–12 stop that is fatal — it produced
a **$3,233 loss against $500 of intended risk**. Arming the exit on the same bar
as the entry: PF 1.098 → 1.282, drawdown $13,762 → $8,703.

**2. The Friday flat executed on Sunday.** `strategy.close_all()` fills at the
*next* bar's open, so a flat triggered on the session-end bar of a Friday
actually fills at Sunday's open. The two worst trades in the sample were exactly
this — Friday entries, Sunday exits, −$2,088 and −$1,665, together **65% of max
drawdown**. Firing the flat on a separate, earlier window: PF 1.486 → **1.673**,
drawdown $5,754 → **$3,313**, largest loss $2,088 → **$520** against $500 intended.

Both are the same class of bug as the V16 trail-without-stop defect: the risk
model was written correctly and then not actually enforced by the order layer.

## Results

Spot XAUUSD 15m, short-only, $500 risk, commission per order:

| window | n | win% | PF | net | max DD | ret/DD | Sharpe |
|---|---|---|---|---|---|---|---|
| Oct 2025 – Sep 2026 | 161 | 42.2% | 1.673 | +$29,301 | $3,313 | 8.84 | 1.42 |
| first half | 95 | 38.9% | 1.579 | +$15,852 | $2,999 | 5.29 | 1.31 |
| second half | 66 | 47.0% | 1.832 | +$13,449 | $3,313 | 4.06 | 1.92 |

Both halves hold. The second half was a *falling* gold market (buy-and-hold
−$3,060) and the short side still only made PF 1.83, so this is not a directional
artifact either way.

**On the real contract**, COMEX_MINI:MGC1!, different feed, real contract
economics, and commission charged **per contract** rather than per order
($3,291 of commission across 162 trades):

| | n | win% | PF | net | max DD | ret/DD |
|---|---|---|---|---|---|---|
| MGC1! 15m | 162 | 38.3% | **1.327** | +$15,786 | $4,971 | 3.18 |

Degraded from spot but clearly positive on an independent feed with honest costs.
Largest loss $621 against $500 intended.

## Tested and rejected

- **Long side.** PF 0.709, −$14,555. On this setup the *shorts* carry it — the
  opposite asymmetry from V16, which is why neither side filter should be trusted
  as a general principle.
- **Extending to the London session** (07:00–19:00 UTC). Doubles trade count to
  342 and destroys the edge: PF 1.02, win rate 38%→30%, drawdown $15,979. The
  edge is specifically the NY session — the same hours the user trades manually.
- **Break-even stop at 1.5R.** PF 1.327 → 1.300, drawdown $4,971 → $5,334. Worse.

## The evaluation simulation — and why it still falls short

Every one of 159 historical start points, real MGC fills, MGC contract
granularity, the trailing MLL locking at $50,100, intraday excursion checked
against the floor, and the 50% consistency rule:

| window | risk | % of account | pass | bust | timeout |
|---|---|---|---|---|---|
| 60 days | $200 | 0.4% | 1.9% | **0.0%** | 98.1% |
| 60 days | $300 | 0.6% | 29.6% | 36.5% | 34.0% |
| 60 days | $400 | 0.8% | **37.7%** | 52.2% | 10.1% |
| 90 days | $200 | 0.4% | 11.9% | **0.0%** | 88.1% |
| 90 days | $300 | 0.6% | **44.7%** | 43.4% | 11.9% |

There is no setting that gives a high pass rate and a low bust rate. Past ~0.5%
risk, every point of pass rate costs roughly a point of bust rate.

**The governing arithmetic, which is now precise:**

Return-to-drawdown over 11 months is 3.18 — comfortably above the 1.5 the account
nominally requires. It still fails, because **profit scales with elapsed time and
drawdown does not**. Inside a 60-day window you collect about a fifth of the
annual profit but remain exposed to most of the annual drawdown. Sized to keep
drawdown under $2,000 (risk ≈ $200) the expected 60-day profit is roughly $1,150 —
not $3,000. Sized to reach $3,000 in 60 days, drawdown exceeds the MLL about half
the time.

Closing that gap needs roughly **double the return-to-drawdown ratio**, which
means either materially more trades per unit time at the same edge, or a
materially better edge. Extending the session was the obvious source of more
trades and it destroyed the edge.

## Honest position

This is the best result in the project by a wide margin, and the first one whose
risk unit is compatible with the account at all. It is a real edge: it survives a
half-split, an independent data feed, the actual contract, and per-contract
commission, and its largest loss matches its intended risk across 162 trades.

It is still not a system I would tell someone to run an evaluation on. At the
risk level where it busts 0% of the time it is too slow; at the risk level where
it passes fastest it busts half the time. Reporting it as a solution would
require quoting the 37.7% pass rate without the 52.2% bust rate beside it.

---

# V18 — the synthesis test, and why the two properties cannot be combined

The obvious move was to put V16's strong entry (Donchian breakout, PF 2.10 out of
sample) on V17's tight structural stop. V18 makes entry and stop independent
switches so that exact combination can be built. It first reproduces V17 bit for
bit as a control (net $15,786, PF 1.327, 162 trades, DD $4,971 — identical), so
the rig is verified before anything is concluded from it.

**The combination is structurally impossible, and it fails twice over.**

Set to breakout entries with a structural stop and a $12 cap, it takes **zero
trades**: all 223 in-session signals are rejected as "stop too wide". Lifting the
cap to measure the distribution shows why — the mean structural stop for a
breakout entry is **$33**, against $6.95 for a sweep reclaim. 4.7× wider.

That is not a tuning problem, it is the geometry of the two setups:

- A **breakout** enters *at* an extreme. The structure that invalidates it is the
  base of the move, which is by construction far behind. This is the same fact
  that made V16's ATR stop $87.
- A **sweep reclaim** enters *next to* the extreme that invalidates it. The stop
  is a few dollars away because that is where the idea is wrong.

Tight invalidation and breakout entry are mutually exclusive. And even after
lifting the cap so the breakout trades could be taken at $33 stops, the edge is
not there on 15m anyway: **PF 0.831, −$2,311 over 108 trades**. V16's breakout
edge lives on 1H and does not survive being moved down to 15m.

## Daily loss guard

The one lever that did help, and the only one that attacks drawdown directly
rather than trying to add profit:

| stop-for-the-day | PF | net | max DD | return/DD |
|---|---|---|---|---|
| off | 1.327 | $15,786 | $4,971 | 3.18 |
| after −2R | **1.341** | **$16,271** | **$4,759** | **3.42** |
| after −1R | 1.372 | $15,764 | $5,441 | 2.90 |

−2R is the best setting: it improves profit factor, net profit and drawdown
together. −1R raises profit factor but cuts so many trades that drawdown gets
worse — fewer trades means less averaging, not less risk.

A 3.18 → 3.42 improvement is real but small. It does not change the conclusion;
the evaluation simulation above was run on the guard-off sequence and an 8% shift
in the ratio does not move those pass rates meaningfully.

## Levers tested against the frequency problem, all closed

The binding constraint is that profit scales with elapsed time and drawdown does
not, so passing inside 60 days needs roughly double the return-to-drawdown ratio.
Every route to that has now been tested:

| lever | result |
|---|---|
| 5m timeframe | PF 0.929, −$4,473; $4,199 of commission eats it |
| extend to London session | 342 trades but PF 1.02, DD $15,979 |
| breakout entry on tight stop | structurally impossible; and PF 0.831 anyway |
| break-even stop at 1.5R | PF 1.327→1.300, DD worse |
| daily loss guard at −2R | +8% on the ratio |
| long side | PF 0.709 |

The edge is specifically: gold, 15m, short side, NY session, sweep-and-reclaim,
structural stop under $12, 3R target, flat by 19:30. It does not survive being
moved off any one of those.

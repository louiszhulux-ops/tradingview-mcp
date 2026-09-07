# V20 — the edge does not survive testing. Retracting the V19 pass rates.

## What I told you, and why it was premature

I reported that V19 gives a 72–79% chance of passing with 0% bust. That number is
**conditional on the sweep-reclaim edge being real**. I had not tested whether it
is. It is not.

## The significance test I should have run first

162 trades, mean P&L $97.44/trade, standard deviation $807.

    t-statistic                 1.54        (needs ~1.96)
    95% CI on profit factor     0.926 .. 1.851
    P(true expectancy <= 0)     5.9%
    trades needed for significance at this effect size:  264  (~1.5 years)

The confidence interval **contains 1.0**. With 162 trades I cannot distinguish
PF 1.33 from no edge at all. And this configuration was selected after testing
many alternatives, so the unbiased estimate sits below 1.33 — the observed value
carries a winner's-curse bias I never corrected for.

The two halves already disagreed loudly: PF 1.150 then 1.541. I read that as
"both halves positive, good." It is equally well read as "one estimate, very wide
error bars."

## Four independent tests. All negative.

| test | n | win% | PF |
|---|---|---|---|
| MGC **15m**, Oct 2025–Sep 2026 — *the discovery window* | 162 | 38.3% | **1.327** |
| MGC **30m**, Oct 2025–Sep 2026 — *same period, one timeframe up* | 100 | 30.0% | **0.811** |
| MGC **30m**, Sep 2023–Sep 2025 — *genuine out-of-sample, 2 years* | 254 | 33.9% | **0.703** |
| MNQ 15m, same window | 95 | 24.2% | 0.616 |
| MCL 15m, same window | 163 | 45.4% | 0.744 |

The 30m same-window result is the one that settles it. **Identical price data,
identical logic, bars aggregated one step coarser, and the edge inverts.** A real
liquidity-sweep effect cannot depend on whether you happen to slice the day into
15- or 30-minute buckets. Nothing about the setup is 15m-specific in theory.

The two-year 30m out-of-sample result (PF 0.703 over 254 trades) is strongly
negative, not merely absent.

Cross-market failure (Nasdaq 0.616, crude 0.744) is weaker evidence on its own —
the session window and stop cap were tuned on gold — but it points the same way.

**Verdict: the sweep-reclaim short result was an artifact of one 11-month window
on one timeframe of one instrument.** Every prior "validation" of it — the
half-split, the MGC re-run, the per-contract commission check — reused that same
window and so could never have caught this.

## Why the earlier checks missed it

The half-split and the MGC/spot cross-check felt like out-of-sample tests. They
were not. Both halves and both feeds cover **the same 11 months of price action**.
The only genuinely independent axes available were *time* (a different period) and
*timeframe*, and I did not test either until now. 15m history is capped at ~20k
bars on this account, which is what blocked the time axis — but 30m was available
the whole time and I never tried it.

## What actually survives

**1. Buffer-based sizing — and this one is edge-independent.**

Re-run under three worlds:

| world | pass | bust |
|---|---|---|
| observed edge (PF 1.33) | 79.1% | **0.00%** |
| no edge (PF 1.00) | 29.5% | **0.00%** |
| lower CI bound (PF 0.93) | 19.8% | **0.00%** |

The 0% bust holds *even with no edge*, because after a full loss the buffer
becomes `buffer × (1 − frac)` — geometric decay that cannot cross the floor. This
is a real result about position sizing under a trailing max-loss limit, and it
does not depend on any edge existing. It is the most durable thing in this repo.

**2. Three execution bugs, each of which would corrupt any strategy:**
- `strategy.exit` with only `trail_points`/`trail_offset` has no protective stop
  until price is onside — largest loss $1,318 vs $500 intended.
- `strategy.position_size` is 0 on the entry bar, so an exit guarded by it is not
  placed until the next bar — a $3,233 loss against $500 of risk.
- `strategy.close_all()` fills at the next bar's open, so a Friday session-end
  flat executes at Sunday's open — the two worst trades in the sample.

**3. The structural arithmetic.** Stop width sets contracts per dollar of risk,
which sets how many R of buffer a $2,000 MLL gives you. A 3×ATR 1H gold stop is
$87 → $868/contract → 2.3R of buffer → nothing survives. This is why tight
structural stops are necessary. It remains true; it just is not sufficient.

**4. The harness**, validated by a positive control (buy-and-hold gold detected
cleanly at +$24,350) and now by a proper significance test.

## What I am no longer claiming

There is no validated automated gold strategy in this repo. The honest summary of
every edge search across this project: nine textbook entries, the encoded
discretionary process, exit-first construction, trend-following, breakout,
sweep-reclaim, opening range, VWAP fade — **none survives out-of-sample testing.**

## The one lead that has not been fairly tested

Your own trades. The entry/stop pairs you sent (4439 entry, 4429 stop, running to
4479) are $10 stops producing 4–9R outcomes. When I encoded that process earlier
I found no edge at 1R/2R/3R — **but that was before the three execution bugs were
found**, and at least two of them (unprotected entry bar, weekend-hold flat) hit
tight-stop strategies hardest. Re-running the manual-process encoding on the
corrected execution layer is a genuinely untested combination and the only lead
left with prior evidence behind it.

Failing that, the deliverable that is actually justified by what has been proven
is a **semi-automated execution layer**: you supply entry, stop and target; the
verified layer enforces MGC contract sizing, buffer-based risk, the trailing MLL,
the daily cap and the consistency rule. That ships the parts that survived
scrutiny without pretending to an edge that did not.

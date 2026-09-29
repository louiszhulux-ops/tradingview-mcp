# The exit is the answer — and it came from your own two trades

## How the rule was derived, not guessed

Your Aug 31 pair:

```
T1 BUY  4434, stop 4429, exit 4479 @ 1:38 PM   ->  9.0R
T2 SELL 4460, stop 4468, exit 4419 @ 4:02 PM   ->  5.1R
```

**Three minutes between the long exit and the short entry.** You did not exit at
a target — you exited *because the opposing setup appeared*, and took it. Your
note says it outright: *"catch the low, ride the move all the way up to the
high, and then catch the reversal back down."* T2's exit sits within $4 of the
session low. Both exits are at extremes where opposing structure formed.

That became H8 in the lab. It is inferred from your behaviour, not invented.

## Twelve exit rules, one opportunity set

Entry held fixed (V41 retest: sweep → second touch → enter on the level, stop
beyond the swept extreme). Only the exit varies, so the rules are comparable on
identical trades.

### Unfiltered (MGC short, n = 786)

| rule | E[R] | win% | avgWin |
|---|---|---|---|
| H1 fixed 1R | −0.137 | 48.7% | 0.89 |
| H2 fixed 2R | −0.009 | 36.8% | 1.88 |
| H3 fixed 3R | +0.013 | 28.1% | 2.88 |
| H4 fixed 5R | +0.033 | 19.1% | 4.87 |
| H5 destination | −0.007 | 18.7% | 4.81 |
| H6 trail 2R/1R | +0.008 | 36.8% | 1.93 |
| H7 partial+dest | +0.005 | 36.8% | 1.92 |
| **H8 REVERSAL** | **+0.0735** | 18.6% | 5.24 |
| H9 ride | −0.020 | 7.3% | 13.95 |
| H10 time exit | −0.217 | 12.7% | 5.93 |

**The rule reverse-engineered from your trades beat all nine alternatives**, by
2.2× over the next best. Two structural facts fall out:

- Fixed targets are **monotone**: 1R worst → 5R best, in both markets. The 2R
  cap in V15–V38 was the single largest self-inflicted wound.
- H9 "ride forever" is **negative**. It is not that you hold — it is that the
  reversal signal tells you when to stop holding.

### With the room filter (room ≥ 10R)

| rule | MGC short (n=200) | MNQ long (n=159) |
|---|---|---|
| H1 fixed 1R | −0.131 | −0.166 |
| H4 fixed 5R | +0.340 | +0.161 |
| H7 partial + destination | +0.263 | +0.322 |
| H8 REVERSAL | +0.417 | +0.373 |
| H9 ride | +0.539 | +0.830 |
| **H12 half at 2R + runner rides** | — | **+0.439** |

H8 replicates almost exactly across markets (+0.417 / +0.373).

## But E[R] is the wrong ranking metric

The account has a hard floor, so what matters is `lambda = 2E/sigma^2`. H9
"ride" has the highest E[R] and one of the *lowest* lambdas — 6.5% hit rate with
25R winners is the wrong shape against a drawdown limit.

MNQ long, room ≥ 10R, ranked by lambda:

| rule | E[R] | sd | **lambda** | t |
|---|---|---|---|---|
| **H12 half at 2R + ride** | +0.439 | 1.96 | **0.229** | **+2.83** |
| H7 partial + destination | +0.322 | 1.81 | 0.196 | +2.24 |
| H11 half at 2R + reversal | +0.207 | 1.66 | 0.150 | +1.57 |
| H8 REVERSAL | +0.373 | 3.63 | 0.057 | +1.30 |
| H9 ride | +0.830 | 6.81 | 0.036 | +1.54 |
| H1 fixed 1R | −0.166 | 1.01 | −0.325 | −2.07 |

**Banking half at 2R keeps most of "ride"'s expectancy at a third of its
variance.** That is the classic professional partial, and it is the only rule
clearing t = 2.5.

## What that does to the evaluation

MNQ long, room ≥ 10R, 2.2 opportunities/day, verified LucidFlex trailing-MLL
rules, 4,000 runs:

| size | buffer | pass | bust | median days | **≤ 7 days** |
|---|---|---|---|---|---|
| 2 micros | 10.9R | **89.8%** | 10.2% | 21 | 0.7% |
| 3 micros | 7.3R | 78.7% | 21.3% | 12 | 16.5% |
| **5 micros** | 4.4R | **67.8%** | 32.2% | **6** | **46.2%** |

For comparison, V38 was 45–59% pass, median ~130 days, **~0% within 7 days**.

## The direct answer to your question

> *What does the human trader do with a winning trade that causes it to become
> 3R, 5R, 7R or 9R instead of exiting at 1–2R?*

Three things, all measurable, in order of size:

1. **They do not use a fixed target at all.** Every fixed target is dominated,
   and the smaller it is the worse it does — 1R is the worst of twelve rules on
   both markets.
2. **They only enter where there is somewhere to go.** With room ≥ 10R to the
   next opposing level, the identical exit rules go from ~+0.03R to ~+0.44R.
   Without room, no exit rule saves the trade.
3. **They bank part of the position and let the rest run until structure says
   stop** — either the opposing setup firing (H8) or simply not closing it while
   the move persists (H12). Holding alone is negative; holding *with a partial*
   is the best rule tested.

## Honest limits

- H12 is the best of twelve rules on one market (n=159, t=+2.83). Winner's
  curse applies; MGC confirmation was in progress when the relay dropped.
- H7, H11 and H12 are variants of the same idea and all rank near the top,
  which is more reassuring than a lone winner would be.
- 46.2% within 7 days comes with 32.2% bust. That is the frontier, not a free
  lunch, and it is a real improvement rather than a solved problem.

---

# CORRECTION — the direction check

Before reporting the H12 result I tested whether its advantage survived when the
direction was **not** chosen from the sample. It does not.

| rule | MGC long | MGC short | MNQ long | MNQ short | pooled | signs |
|---|---|---|---|---|---|---|
| H1 fixed 1R | −0.295 | −0.131 | −0.166 | −0.312 | −0.232 | **0/4** |
| H2 fixed 2R | −0.148 | +0.100 | +0.048 | −0.154 | −0.047 | 2/4 |
| H3 fixed 3R | +0.093 | +0.220 | +0.086 | −0.005 | +0.092 | 3/4 |
| **H4 fixed 5R** | **+0.223** | **+0.340** | **+0.161** | **+0.035** | **+0.179** | **4/4** |
| H8 REVERSAL | −0.313 | +0.417 | +0.373 | −0.254 | +0.032 | 2/4 |
| H12 half + ride | +0.007 | +0.319 | +0.439 | −0.447 | +0.027 | 3/4 |

H8 and H12 **flip sign with direction**. Their headline numbers (+0.42, +0.44)
required knowing the favoured direction in advance — gold short, nasdaq long —
which I had taken from the sample itself. Pooled without that call they are
worth +0.032R and +0.027R, i.e. nothing.

**The robust finding is target width.** Fixed 5R is positive in all four cells,
fixed 1R is negative in all four, and the ordering 1R < 2R < 3R < 5R is
monotone. That result needs no direction call and no market call.

## Honest headline

Direction-agnostic, both markets, both directions, room ≥ 10R, exit at 5R:
**E = +0.179R over n = 783, t = +1.95, ~10.9 opportunities/day.**

| risk/trade | buffer | pass | bust | median | ≤3d | ≤5d | **≤7d** |
|---|---|---|---|---|---|---|---|
| $60 | 33.3R | 79.0% | 21.0% | 33d | 0% | 0% | 0% |
| $100 | 20.0R | 64.0% | 36.0% | 16d | 0% | 0% | 1.6% |
| $150 | 13.3R | 57.2% | 42.8% | 9d | 0% | 5.5% | 20.2% |
| $200 | 10.0R | 50.4% | 49.6% | 6d | 1.0% | 24.9% | 37.6% |
| $300 | 6.7R | 54.2% | 45.8% | **3d** | 28.6% | 45.4% | **52.2%** |
| $400 | 5.0R | 54.1% | 45.9% | **3d** | 35.3% | 47.8% | **52.9%** |

**52.9% probability of passing within 7 days, median 3 days**, with no direction
call — against ~0% within 7 days for V38. Bust risk is 46% at that sizing.

## The single highest-value open question

Direction. If the favoured direction per instrument could be called in advance,
H12 rises from +0.027R to roughly +0.38R — more than double the current edge,
and it would put 2-day passes in range. Everything else (entry, filter, target
width) is now measured and direction-free.

That is a well-posed research question and it is the next bottleneck.

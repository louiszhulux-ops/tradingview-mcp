# Report — reverse-engineering the discretionary process

Answers to the fifteen questions, from the V40/V41 opportunity engine.
Measured on MGC1! and MNQ1!, 5-minute, ~2,900 opportunities, next-bar-open or
resting-limit fills, structural stops, costs subtracted in R.

---

## 1. Why did the existing system fail?

Four reasons, in order of size.

**It capped every trade at 2R.** Your two verified trades were 9.0R and 5.1R.
The opportunity dataset shows 12–24% of opportunities reach 5R. A 2R cap
discards the entire right tail, which is where your edge lives.

**It faded liquidity sweeps.** `MANUAL_PROCESS_ANALYSIS.md` recorded — before
this session — that you use sweeps as *continuation* evidence aligned to a
multi-day bias. I then built V33–V38 as an increasingly refined sweep-**fading**
system. I built the inverse of your documented method and did not notice.

**It entered at market, not on the retest.** Entering at the next bar's open
after a sweep gives R ≈ 1.10 × ATR. Entering on the second touch of the level,
with the stop just beyond the sweep extreme, gives R ≈ 0.65 × ATR. Same move,
1.7× more R. This is the mechanism that turns a 5-point gold stop into 9R.

**It never modelled where price could go.** Every filter it used described the
*entry pattern*. None described the *destination*. That turns out to be the
single most discriminating feature available (see Q3).

---

## 2. How many tradable opportunities did it ignore?

V38 took **1.39 trades/day**. The opportunity engine detects **~19 sweep events
per day** on MGC alone, of which **~17/day** produce a valid retest entry.

**It ignored roughly 92% of the situations a discretionary trader would look at.**

---

## 3. What do profitable opportunities share?

**Room to the next opposing significant level, measured in R at entry.**
Pooled over both markets and both directions (n = 4,217 opportunities):

| room to next level | n | P(5R) | E@3R |
|---|---|---|---|
| < 1R | 751 | 14.4% | **−0.149** |
| 1–2R | 773 | 16.7% | −0.033 |
| 2–4R | 1,158 | 17.9% | +0.012 |
| 4–6R | 836 | 17.8% | −0.032 |
| 6–10R | 935 | 16.7% | −0.108 |
| **> 10R** | **764** | **21.9%** | **+0.062** |

Worst to best bucket is **+0.211R**, and P(5R) rises by half. It replicates
independently in both markets and, separately, in both directions:

| | MGC short E@3R | MNQ long E@3R |
|---|---|---|
| room < 1R | −0.057 | −0.088 |
| room > 10R | **+0.186** | **+0.208** |

No single cell is individually significant. The reason it is credible is that
four independent measurements (2 markets × 2 directions) all order the same way.

---

## 4. What do losing opportunities share?

**No room.** A setup entered when the nearest opposing level is under 1R away
loses −0.149R on average. Structurally obvious in hindsight: the trade is
entered into a wall. The bot had no concept of this and took those trades at the
same size as everything else.

---

## 5. What do you appear to see that the bot does not?

1. **Destination.** Where price can travel before it meets opposition. Worth
   +0.21R per trade, the largest single effect measured in this project.
2. **The second touch.** Waiting for the retest instead of entering on the
   event, which shrinks R by ~40% and multiplies the R-value of the same move.
3. **Sweeps as continuation**, not as reversals.
4. **A discretionary exit near the extreme.** On the Aug 31 long, the stated
   stop was eventually hit later that day — the same entry is a 9R winner or a
   1R loser depending *entirely* on the exit. No mechanical exit rule tested
   here captures that, and it remains the largest unmodelled part of your process.

---

## 6. Which setup families are actually useful?

Tested: **sweep of a significant level → retest → entry**. Useful, conditional
on room. Not yet tested in this architecture: breakout-with-acceptance,
displacement-and-retest, failed-breakout reversal, VWAP reclaim/rejection,
opening-range. These are the next hypotheses, not conclusions.

## 7. Which regimes are profitable?

Bias conditioning **failed to discriminate**. Both a 1H EMA-structure bias and a
prior-day-range bias left short winning in all six gold cells. Room discriminates
where regime did not. I do not yet have a regime definition that earns its place.

## 8. Which instruments are best?

MGC (micro gold) and MNQ (micro nasdaq) — the two whose structural stop lands in
the $40–110 band. MYM and M2K have $17–18 stops where fixed costs alone exceed
0.10R. **Direction is instrument-specific**: gold favoured shorts, nasdaq
favoured longs, over the same period.

## 9. Which sessions are best?

Weak effect. On gold, Asia swept-HIGH (+0.32 E@3R short, n=183) and NY swept-LOW
(+0.23, n=240) led; London was flat. Not strong enough to act on alone.

## 10. Expected R per qualified opportunity?

**+0.19 to +0.21R at a 3R target** in the favoured direction with room > 10R.
**+0.31R at a 5R target** for the best single cell (MGC short, n=209, t = 1.72).

## 11. How many qualified opportunities per day?

~5.5/day with room > 10R across both directions; **~2.9/day** in the
instrument's favoured direction. That matches the "few good trades a day" shape
rather than the 27/day the old system needed.

## 12. Realistic pass probability

MGC short, room > 10R, 5R target, 2.9 opportunities/day, verified LucidFlex
trailing-MLL rules, 6,000 runs:

| size | risk | buffer | pass | bust | median days | **≤ 7 days** |
|---|---|---|---|---|---|---|
| 1 micro | $42 | 47.6R | 97.6% | 1.7% | 87 | 0% |
| 2 micros | $84 | 23.8R | 82.5% | 17.4% | 36 | 0% |
| 3 micros | $126 | 15.9R | 70.8% | 29.2% | 19 | 3.8% |
| **5 micros** | **$210** | **9.5R** | **59.7%** | 40.3% | **9** | **23.2%** |
| 8 micros | $336 | 6.0R | 43.6% | 56.4% | 4 | **39.4%** |

**Your sizing (5 micros) gives 59.7% pass, median 9 days, 23% within 7.**
Previous best in this project was ~0% within 7 days. This is real progress and
it is still short of a 2-day pass.

## 13. Median time to pass

4 days at 8 micros, 9 at 5 micros, 19 at 3 micros. Speed is bought with bust
risk, one for one.

## 14. Maximum drawdown

Determined by sizing against a fixed dollar limit. At 5 micros the buffer is
9.5R, so a 10-loss run inside a 40% win rate ends the account — probability
~0.6% per specific run but many runs are sampled. This is the direct cause of
the 40.3% bust rate at that size.

## 15. What causes failures?

**The speed/survival tension, not the edge.** At +0.31R per trade you can have
97.6% pass in 87 days or 43.6% pass in 4 days. Passing in 2 days requires
per-trade R like yours — two trades at 9.0R and 5.1R — which means catching the
top decile of the distribution, not the average of it.

---

## What is now the open question

The room feature moved expected R from −0.15 to +0.20. To pass in 2 days I need
roughly another doubling, and it has to come from **selecting the right tail**,
not from sizing.

Concretely: 21.9% of high-room opportunities reach 5R. If a second feature can
lift that to ~35% without cutting frequency below ~2/day, a 2–3 day pass becomes
the median outcome rather than the tail.

**The most valuable thing you could give me is exit data.** Every note in this
project states entry and stop; none states where profit was taken. The Aug 31
long proves the exit is doing decisive work — same entry, 9R or −1R depending
only on it. That is the largest unmodelled component of your process and no
amount of backtesting can recover it.

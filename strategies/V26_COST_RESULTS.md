# V26 — route 1 tested: correcting the cost assumption

I was guessing at costs. The guess was wrong, and wrong in a more interesting way
than "too high".

**Sources for the real figures:**
[BrokerChooser MGC fee comparison](https://brokerchooser.com/best-brokers/best-brokers-for-trading-micro-gold-futures-in-the-united-states) ·
[NFA assessment fees](https://www.nfa.futures.org/faqs/members/nfa-assessment-fees.html) ·
[TradeStation exchange & clearing fees](https://www.tradestation.com/pricing/exchange-execution-and-clearing-fees/) ·
[Optimus Futures: micro gold](https://optimusfutures.com/blog/micro-gold-futures/)

MGC all-in commission (broker + exchange + clearing + NFA) is **$0.90–1.20 round
turn**; the tick is 0.10 = $1.00 with a typical 1-tick spread. I had been charging
$2.48 commission plus $2.00 slippage = **$4.48**, roughly 2.2× reality.

## The deeper error: cost in R is not a constant

    cost_R = cost_per_contract_roundturn / (stopDistance × pointValue)

The contract count cancels, so the R penalty depends entirely on how big the stop
is in dollars. A flat 0.08R hid that completely. Measured at 1×ATR on 15m:

| market | $/contract RT | measured cost in R | vs my 0.08 assumption |
|---|---|---|---|
| MGC gold | 2.04 | **0.0213** | 3.8× too high |
| MNQ nasdaq | 1.54 | **0.0207** | 3.9× too high |
| MCL crude | 2.04 | **0.0904** | slightly too low |
| 6E euro | 7.29 | **0.1135** | 1.4× too low |

**A 5× spread across four markets**, and the flat number was wrong in *both*
directions depending on instrument. Gold and Nasdaq are cheap to trade in R terms
because ATR × point value is large against a fixed fee. Crude and euro are four to
five times more expensive for what looks like a similar commission.

It also drifts with price: the same gold strategy had cost_R of 0.027 measured
across 2023–2025 (gold near $1,900) versus 0.021 over 2025–2026 (gold above
$4,000). Cost efficiency improved simply because the instrument got more volatile
in dollar terms.

**This is a genuinely useful, reusable result** — instrument and stop-width
selection change the cost drag by 5×, independently of any edge. It is the first
thing in this project that would improve any strategy, including yours.

## What it did to the breakeven line

With cost at 0.021R instead of 0.08R, breakeven at 1:1 falls from 54.0% to
**51.1%** — and gold's best mechanical entry was 52.1%. So on that arithmetic
alone, two signals cross into profit:

| signal (gold 15m, RR 1:1) | win% | meanR at real cost | t |
|---|---|---|---|
| trend continuation long | 52.1% | **+0.0175** | 0.42 |
| follow breakout long | 51.8% | **+0.014** | 0.36 |

Both are positive. Neither is significant, and neither replicated: follow-breakout
long is **−0.0398** on Nasdaq, and trend-long is +0.0023 there — indistinguishable
from zero.

## Why the route is closed anyway

The screen reports gross expectancy with costs added back. Before **any** fees:

| market | gross mean R |
|---|---|
| MGC gold | −0.0138 |
| MNQ nasdaq | −0.0295 |
| MCL crude | −0.0205 |
| 6E euro | −0.0196 |

**Negative in all four.** Cutting commission to zero still leaves these entries
unprofitable. There is no edge being eaten by costs — the entries are slightly
*worse* than random.

That has a name and a mechanism: adverse selection. You enter after the move has
happened, at a price that already reflects it, and the immediate next tick is
marginally against you. A breakout entry buys the top of a bar that just printed a
high. That small negative is remarkably consistent — roughly −0.02R across four
unrelated markets and ten different triggers.

## Where this leaves both routes

- **Route 1 (frequency-first, cut costs)** — closed. The cost correction was real
  and worth about +0.06R, but gross expectancy is negative, so it lands at roughly
  break-even rather than profit. You cannot subtract your way to an edge that was
  never there.
- **Route 2 (confluence-first)** — still untested rather than disproven, because
  the properly-specified ICT model yields ~9 trades per instrument per year.
  Testing it honestly needs years of data across many instruments, and it can
  never deliver 4 trades a day.

The one thing that has survived every test in this project is that the *execution
layer* matters and is measurable: cost efficiency varies 5× by instrument,
buffer-based sizing removes ruin, and three order-placement bugs were silently
corrupting results. What has never survived is an entry signal.

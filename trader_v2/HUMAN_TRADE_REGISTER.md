# Phase 1 — Human trade register, and what is not recoverable

Objective: build the largest possible **unbiased** human-trade sample, losers
included. The instruction was explicit — if the data is insufficient, say so
rather than fill the gap with assumptions. It is insufficient. This document
records everything that exists, and states precisely what is missing.

---

## 1. Sources searched

| source | searched | yield |
|---|---|---|
| all 60 markdown files in the repo | yes | 4 documents containing human trade evidence |
| full git history, all branches, incl. deleted files (`--diff-filter=A`) | yes | nothing beyond the above; no trade log ever committed |
| `strategies/*.txt` raw trade dumps | yes | **bot** trades only (V16, V17, audit rig) — not human |
| `screenshots/` | yes | gitignored **and absent from disk**; no images exist |
| TradingView saved layouts (2) | yes | both are mine; no user annotations |
| TradingView chart drawings | yes | **0 drawings** on the active layout |
| TradingView trading panel / broker history | yes | only a Replay-Trading order panel; **no broker account, no order history** |
| **TradingView alert history (20 alerts, Mar–Aug 2026)** | yes | **NEW — see §4.** Timestamped, outcome-independent human level selection |
| grep for narrative markers across all docs | yes | no further trades |

Nothing else in this environment contains human trade data.

---

## 2. The register — every recoverable human trade

`?` = not stated anywhere in the source material. It is not inferred.

| field | N1 | N2 | N3 | A1 | A2 | L1 |
|---|---|---|---|---|---|---|
| **date** | ? | ? | ? | 2026-08-31 (disputed) | 2026-08-31 | ? |
| **instrument** | gold | gold | gold | gold (feed unclear) | gold (spot verified) | gold |
| **direction** | short | short | long | long | short | short |
| **HTF bias** | bearish | bearish | bullish | bullish (intraday) | exhausted | bearish |
| **why that bias existed** | yesterday's drop, OB held | "bearish bias all week" | Asia spike, liquidity broken, above VWAP | 4396→4449 rally | rally failed at 4464 | stated, not evidenced |
| **liquidity event** | sold through Asia | **swept the Asia low** | liquidity broken in Asia | none identified | **swept the session high** | reached an unmitigated OB |
| **location** | 15m imbalance + 1m OB, above price | OB **above** the swept low | 5m imbalance fill | pullback to 4435 | session high | unmitigated 4H OB |
| **setup** | pullback into imbalance | sweep → rally → OB tap → 1m CHOCH | imbalance fill + 1m inverted + 3m engulfing | pullback in a rally | failed high | tap of an unmitigated OB |
| **entry** | ? | ? | ? | **4434** | **4460** | ? |
| **stop** | **?** | **?** | **?** | **4429** (5.0 pts) | **4468** (8.0 pts) | ? |
| **intended destination** | 4H/1H unmitigated OBs | PDL, Monday's low | external liq + round 4600 | prior high ~4464 | session low | "a nice correction" |
| **exit** | ? | ? | ? | **4479 @ 13:38** | **4419 @ 16:02** | stopped out |
| **outcome in R** | ~600p, R unknown | ~500p, R unknown | ~400p, R unknown | **9.0R** as stated | **5.1R** verified | **−1R** |
| **continuation / reversal** | continuation | continuation | continuation | continuation | reversal | reversal |
| **followed the stated process?** | yes | yes | yes | not described by the process | not described by the process | yes |
| **discretionary / experimental / exceptional** | ? | ? | ? | 5 micros — breaks the 50% consistency rule | 5 micros — same | ? |

### Verification status

- **A2 is the only fully verified trade.** Entry 4460 was available in the
  09:00–13:00 UTC spot bar (high 4464.23), exit 4419 in the 13:00–17:00 bar
  (low 4415.75), stop 4468 never touched. Internally consistent. 5.1R.
- **A1 cannot be reconciled** on Aug 31 on either instrument: exit 4479 is $15
  above spot's high, entry 4434 is $11 below MGC's low. A Sep 2 date
  transposition fits all six prices in one bar. Unresolved.
- **A1's stop was breached later the same day** (13:00–17:00 low 4415.75).
  Held to the stated stop it is a loss; the profit came from a discretionary
  exit, not from the entry.
- **N1/N3 have no stop and no exit**, so they have no R and cannot be used for
  expectancy — only for direction and structure.
- **L1 has no prices at all.**

---

## 3. The sample is unusable for the purpose stated in Phase 1

| | count |
|---|---|
| human trades recoverable | **6** |
| of which winners | **5** |
| of which losers | **1** |
| losers with entry, stop and exit prices | **0** |
| trades considered and rejected, recorded | **0** |
| trades that looked valid and were not taken, recorded | **2 zones, no trade record** (§4) |

**This cannot be de-biased from material available here.** Five winners and one
priceless loser is not a sample; it is a highlight reel plus one anecdote. Every
statistic computable from it — win rate, expectancy, R distribution, worst
streak, continuation-vs-reversal mix — is determined by which trades happened to
be written up, and trades get written up because they worked.

The specific danger for Phase 2 is concrete: if I fit an "HTF bias model" to six
outcomes of which five are wins, I will fit the five wins. That is the selection
bias the directive says to avoid, reintroduced through the back door.

**What would fix it, and only this:** a plain trade log, winners and losers
alike, no narrative —

```
date | time | instrument | direction | entry | stop | exit | contracts | net $
```

Thirty to fifty rows. This was requested once before (`LOSS_NOTE_ANALYSIS.md`
§6) and has not been supplied. Until it is, the human sample can serve as a
**sanity check on agreement** and nothing else — never as training or
validation data.

### Consequence, and how I am proceeding

Phase 2 does **not** actually require human labels, and that is the way through.
The requirement it states is that the bias be computable **ex ante from market
data alone** — "at 09:42, before knowing what happens next, my HTF bias is
bullish." That is testable on price history without a single human trade. So:

- the ex-ante bias model will be specified from market structure only, frozen
  before it meets the test period, and validated on price data;
- the 6 human trades will be used **only** to check whether the model's label
  agrees with the human's stated bias at those 6 moments — a 6-point sanity
  check, reported as such, never as evidence of edge;
- no parameter will be chosen to make those 6 agree.

---

## 4. New source: the alert history — outcome-independent human level selection

20 price alerts on `OANDA:XAUUSD`, created 2026-03-09 → 2026-08-31. These are
**ex-ante records with creation timestamps**, and they exist regardless of
whether a trade followed — which is exactly the property the trade narratives
lack.

17 of them carry TradingView's default message ("XAUUSD Crossing 4,632.467") and
therefore record **a level and a time, but no direction**. Useful as evidence of
attention, not of thesis.

**Three, created within ten minutes on 2026-08-31, carry the user's own text and
a direction.** Authorship: the trading research in this repo begins with the
first commit at 2026-09-03 23:43 UTC; the Aug 31 commits are unrelated MCP
launch fixes. No assistant session was doing trading work on Aug 31, so these
are the user's, written by hand.

| created (UTC) | trigger | message |
|---|---|---|
| 22:11:03 | price > 4460 | "XAUUSD entering order block zone **4460-4470** — watch for **short** confirmation" |
| 22:20:03 | cross 4444 | "XAUUSD tapping **BUY ZONE 4441-4444**" |
| 22:20:56 | cross 4449.548 | (default) — a marker between the two zones |

### The market context that existed before the plan was written

From hourly bars, all of it available before 22:11:

| when | what |
|---|---|
| 2026-08-25 | swing high 4697.11 |
| 2026-08-28 13:00–18:00 | **collapse 4627.40 → 4445.46**, on the three highest-volume bars in the sample (174k, 125k, 138k) |
| 2026-08-28 20:00 | close 4454.99 |
| 2026-08-30 22:00 | Sunday reopen 4445.72 |
| 2026-08-31 00:00 | close 4462.13 |

HTF bias was unambiguously **down**, price sitting just above the crash low.

### What the plan actually says

- **Short zone 4460–4470** — supply *above* current price, in the direction of
  the HTF bias, entered on a rally, requiring "confirmation". This is
  **bias-aligned continuation**, and structurally it is the N2 pattern.
- **Buy zone 4441–4444** — sitting *just below* the Aug 28 low of **4445.46**.
  Buying below a prior low is **fading a liquidity sweep**: F0-long.

**One evening's plan contains both families, marked simultaneously, before any
outcome was known.** The direction is not chosen in advance — the *locations*
are, and price decides which one trades. That is direct ex-ante evidence for the
Phase 8 hypothesis (regime → family) and against reading the human process as
purely continuation.

### What price did — from TradingView's own fire records

| fired (UTC) | alert | implies |
|---|---|---|
| 2026-08-31 22:21:00 | crossing 4449.548 | price ≈ 4449.5 when the plan was set |
| 2026-08-31 23:13:21 | cross 4444 | fell into the **buy zone** |
| 2026-09-01 00:21:02 | > 4460 | rallied ≥ 16 pts into the **short zone** |

Both zones were reached within 2h10m. **No trade record exists for either**, so
these are "considered, outcome unknown" — Phase 1's rejected/not-taken category,
and the only entries in it.

I could not verify what happened after 00:21 on Sep 1: see §5.

---

## 5. Environment limitation found while checking this

The market feed reachable from this session is **delayed and currently ends
2026-08-31 00:00 UTC** — five days behind today's date. Both `OANDA:XAUUSD` and
`COMEX_MINI_DL:MGC1!` return that same last bar (the `_DL` suffix confirms a
delayed feed). `TRADE_VERIFICATION_AUG31.md`, written on Sep 4, quotes Aug 31
4H bars that the feed no longer returns, so it has regressed since.

Two consequences, both material:

1. **I cannot verify price action after 2026-08-31**, including the outcome of
   the alert plan above.
2. **Every V44/V45 measurement runs on a window ending 2026-08-31**, roughly
   **2026-06-20 → 2026-08-31** (~71.5 days of 5m bars). Phase 3's held-out test
   period must therefore be carved out of *that* window — there is no fresh
   unseen data to wait for.

---

## 6. Phase 1 verdict

- The human sample is **6 trades: 5 winners, 1 loser with no prices.** It cannot
  be made unbiased from anything in this environment.
- **Losers are the missing ingredient**, and only the user can supply them.
- The alert history is a real find: it gives three timestamped, outcome-independent
  human level selections, and they show **both families marked in one plan**.
- Phase 2 proceeds **without** using the human trades as training or validation
  data, because it does not need them. They will be used once, as a 6-point
  agreement check, and reported as a 6-point agreement check.

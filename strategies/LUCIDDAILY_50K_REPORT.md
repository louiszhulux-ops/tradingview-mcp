# LucidDaily 50K — execution layer rebuild and evaluation simulation

Instrument: MGC (COMEX micro gold), 1 contract = 10 oz, **$10.00 per $1.00 move**.
Backtest: `COMEX_MINI_DL:MGC1!` 15m, 2025-10-01 → 2026-09-03. Commission
$1.24/order round-turn equivalent, 1 tick slippage.

## 0. Two corrections to earlier claims in this project

1. **Delayed data does NOT block strategy execution.** MGC resolves to
   `COMEX_MINI_DL:MGC1!` and still executed 148–153 trades. My earlier
   diagnosis of the NQ zero-trades problem as "delayed feed" was wrong, and
   replay mode is not needed.
2. Every performance figure reported before the audit is invalid (see
   `AUDIT_REPORT.md` — 100% margin was silently rejecting 45% of orders).

## 1. LucidDaily rules as modelled (verified against Lucid's published mechanics)

| Rule | Value | Implementation |
|---|---|---|
| Starting balance | $50,000 | `startBal` |
| Profit target | +$3,000 → $53,000 | stop trading on reach |
| Max loss limit | $2,000, **trailing** | floor = max(floor, balance − 2000) |
| MLL lock | **locks at $50,100** once balance clears $52,000 | verified: floor read back as exactly 50,100 |
| Drawdown mode | EOD (default) or Intraday | EOD trails closing balance only |
| Daily loss limit | $1,200, soft, optional | halts the day, not the account |
| Max position | 40 MGC | hard cap in sizing |
| Consistency | largest day / total profit ≤ 50% | measured, reported |

Sizing is built from risk, never leverage:
```
risk_per_contract = |entry − stop| × $10
contracts         = floor(allowed_risk / risk_per_contract)
                    capped by 1..40, by remaining MLL buffer, and by mode
```

## 2. Test A — raw strategy, no prop constraints (MGC)

| Metric | Value |
|---|---|
| Trades | 153 |
| Win rate | **17.0%** |
| Avg win / avg loss | $1,152 / $234 (4.9×) |
| Profit factor | **1.008** |
| Net profit | **+$234** |
| Max drawdown | **$8,835** |
| Expectancy | **+$1.53 per trade** |

**Profit factor 1.008 is zero edge.** The drawdown is **4.4× the entire $2,000
max loss limit**. This is not a sizing problem or a filtering problem — the
underlying strategy has no measurable edge on MGC.

## 3. Test B — full LucidDaily constraint stack

Single historical path: reached $53,053 in **3 trades**, MLL floor correctly
locked at $50,100, max 2 of 40 contracts used, worst day −$150.
**But consistency = 0.70 — it would have been rejected.**

Rejection funnel over 394 raw signals:

| reason | count |
|---|---|
| evaluation already complete | 384 |
| volatility-spike cooldown | 2 |
| already in a trade | 1 |
| min-spacing | 1 |
| stop-distance out of bounds | 1 |
| size resolved to 0 contracts | 1 |
| outside window | 1 |
| **taken** | **3** |

Trade frequency is **not** being destroyed by filters — 384 of 394 rejections
are simply "the evaluation already ended". Answering the brief's question
directly: the ~242 trades/yr was never a filtering problem.

## 4. Evaluation simulation (40,000 runs per configuration)

Bootstrapped from the Test A distribution, with real rule mechanics: trailing
MLL that locks at $50,100, $1,200 DLL, 50% consistency, ~0.64 trades/day.

| size | ≈max contracts | P(pass) | P(fail on consistency) | P(breach/timeout) | median days |
|---|---|---|---|---|---|
| **1×** | 2 | **3.7%** | 27.0% | 69.2% | 12 |
| 2× | 4 | 0.3% | 31.8% | 67.9% | 6 |
| 3× | 6 | 0.1% | 29.9% | 70.0% | 5 |
| 5× | 10 | 0.0% | 25.0% | 75.0% | 3 |
| 8× | 16 | 0.0% | 23.3% | 76.7% | 3 |
| 20× | 40 | 0.0% | 19.6% | 80.4% | — |

**Best achievable pass rate is 3.7%, and scaling size makes it strictly worse.**
Bigger positions reach the target faster but breach the $2,000 MLL far more
often. There is no size that fixes a zero-edge strategy.

## 5. The structural finding: this strategy's shape is illegal under a 50% consistency rule

The strategy earns through rare, large winners:

- win rate 17.0%, average win $1,152, average loss $234
- an **average** winner = **38% of the entire $3,000 target in one day**
- the **largest** winner = **80% of the target in one day**

The consistency rule caps any single day at $1,500 (50% of $3,000). So a single
good day usually breaks the rule outright. **27% of all simulated runs reached
+$3,000 and were rejected on consistency anyway.**

This is not a tuning issue. A low-win-rate / large-winner strategy is
structurally incompatible with a 50% consistency requirement.

## 6. What this means — and where the earlier 1:1 discussion was right

A 50% consistency rule *requires* profit spread across several days in similar
increments. That means the correct shape for this firm is **many modest wins**,
not few large ones — a higher win rate with a smaller R multiple, taken across
at least 3–4 sessions.

That is the approach originally proposed (1% risk, ~1:1, several winners). My
earlier pushback was that *this particular strategy* had no edge at 1:1 —
measured 52.85% win rate against a 52.90% breakeven. That finding stands. But
the **shape** was right for this rule set, and the current low-win-rate design
is the wrong shape regardless of how it is sized.

## 7. Recommendation

Do not tune this strategy further. The evidence across three independent
measurements is consistent:
- unconstrained MGC: PF 1.008, expectancy +$1.53/trade
- under realistic leverage on spot: PF 0.97–0.99
- pure 1:1 variant: 52.85% win rate vs 52.90% breakeven

The execution and risk layer is now correct and reusable — instrument model,
risk-based sizing, trailing-and-locking MLL, DLL, consistency tracking and full
rejection accounting all verified against live readouts. **It is ready to host a
different signal generator.** What it does not have is a signal generator with
an edge.

Next step should be finding an edge with a shape that fits the rule set
(higher win rate, modest R, several trades per session), validated
out-of-sample before any sizing work. Everything here remains in-sample.

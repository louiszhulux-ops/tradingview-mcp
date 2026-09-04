# Forensic audit — XAUUSD day-trading bot

Scope: Phases 1–4 of the requested audit (code audit, trade-level analysis,
missed-trade analysis, setup characteristics). **The audit found a defect that
invalidates every backtest result previously reported in this project, so I
stopped before Phases 5–12 rather than optimize on top of a broken measurement.**

---

## 1. HEADLINE: the reported edge was a backtest artifact

`strategy(margin_long = 100, margin_short = 100)` — the account was configured
with **zero leverage**. Gold trades near $4,400/oz, so a correctly-sized position
exceeds a $50,000 account's notional and **TradingView silently rejects the
order**. It does not resize it. It does not warn.

Same code, same signals, only the margin setting varied:

| margin | leverage | trades executed | net profit | profit factor | max DD |
|---|---|---|---|---|---|
| **100%** | none (as configured) | **232** | **+$5,669** | **1.35** | 3.8% |
| 20% | 5:1 | 416 | −$366 | 0.990 | 14.7% |
| 5% | 20:1 | 420 | −$1,006 | 0.974 | 15.4% |

**188 of 420 signals — 45% — were never executed.** The "+$5,669 / PF 1.35 /
232 trades" figure I reported repeatedly is not a strategy result. It is what
happens when an unrealistic margin setting silently discards 45% of trades.

Arithmetic of the mechanism:

```
100% margin: max qty = $50,000 / $4,400 =  11.4 oz -> needs stop >= $22.00
  5% margin: max qty = $1,000,000 / $4,400 = 227 oz -> needs stop >=  $1.10
```

`minStopATR` was set to 0.15 (≈$5–9). The margin ceiling, not the parameter, was
setting the real minimum stop distance at roughly 0.4–0.7 × ATR.

**With any realistic leverage the strategy has no edge (PF 0.97–0.99).**

### Why the rejection accidentally *helped*
Rejection was not random. Required stop distance scales with dollar risk, and
dollar risk was scaled by the size multipliers (below). Low-multiplier trades
faced a low bar and were admitted; full-size trades faced a $22 stop bar and were
rejected. Since the multipliers turn out to be *inversely* related to trade
quality, the margin ceiling preferentially admitted the good trades. That is
luck, not edge.

---

## 2. Second defect: position sizing is not R-normalized

Effective risk = `riskPct × sessMult × confMult`, where sessMult ∈ {1.0, 0.5} and
confMult ∈ {1.0, 0.6}. So "0.5% risk" is actually four different risks:

| sessMult | confMult | effective |
|---|---|---|
| 1.0 | 1.0 | 1.00× |
| 1.0 | 0.6 | 0.60× |
| 0.5 | 1.0 | 0.50× |
| 0.5 | 0.6 | 0.30× |

Across the 232 executed trades, **the multipliers are inversely related to
outcome** (R here = each trade's own risk; `$R` weights by size actually used):

| size multiplier | n | win% | E[R] | PF | $R per trade |
|---|---|---|---|---|---|
| 0.3 | 122 | 35.2% | **+0.369** | 1.54 | 0.111 |
| 0.5 | 77 | 40.3% | +0.173 | 1.28 | 0.086 |
| 0.6 | 28 | 39.3% | +0.377 | 1.49 | 0.226 |
| 1.0 | 5 | 20.0% | **−0.514** | 0.37 | −0.514 |

Per-trade expectancy was **+0.285 R**, but only **+0.103 R** was actually banked.
**The sizing rules discard 64% of the edge** — they systematically bet least on
the best trades.

---

## 3. Third defect: the confluence score is anti-predictive

The score (FVG + swept + round-number + SMT) is used to size down "weak" setups.
It is inverted:

| confluence | n | win% | E[R] | PF |
|---|---|---|---|---|
| 0 | 43 | 30.2% | **+0.728** | 1.98 |
| 1 | 107 | 38.3% | +0.226 | 1.33 |
| 2 | 56 | 35.7% | +0.130 | 1.19 |
| 3 | 25 | 48.0% | +0.180 | 1.34 |
| 4 | 1 | 0.0% | −1.036 | 0.00 |

Higher confluence → higher win rate but *lower* expectancy, because confluence
correlates with the trend setups that have small fixed targets, while zero-
confluence trades are disproportionately range trades with large runners.
**Caveat: 43 trades at conf 0 is a small sample and this is in-sample. Treat as a
hypothesis, not a rule.**

---

## 4. Setup-level performance

| setup | n | win% | E[R] | PF | verdict |
|---|---|---|---|---|---|
| RANGE_LONG | 37 | 32.4% | **+0.757** | 2.04 | best |
| RANGE_SHORT | 60 | 20.0% | +0.365 | 1.41 | good, low win rate |
| TREND_LONG | 84 | 47.6% | +0.164 | 1.30 | marginal |
| TREND_SHORT | 51 | 43.1% | **+0.049** | 1.08 | **no edge** |

By regime: sideways E[R] +0.515 (n=97) beats uptrend +0.164 (n=84) and downtrend
+0.049 (n=51). **The mean-reversion half carries the system; the trend half,
which is the more elaborate code, contributes almost nothing.**

The `sessMult` session filter is backwards: trades outside 07:00–16:00 UTC scored
E[R] +0.293 vs +0.242 inside — yet the outside trades are the ones cut to half
size.

---

## 5. Exit analysis (real MFE/MAE from `strategy.closedtrades`)

Of 146 losing trades: 70.5% reached +0.25R, **50.7% reached +0.5R**, 26.7%
reached +1R before reversing to a full loss.
Of 86 winners: 45.3% had MAE ≥ 0.5R — nearly half came close to stopping out.

But capping winners does not help. Counterfactual fixed take-profits, applied to
the real excursion data, all underperform the current mixed-target scheme:

| exit rule | win% | E[R] | total R |
|---|---|---|---|
| TP 1.0R | 53.9% | +0.056 | 13.1 |
| TP 2.0R | 14.2% | +0.047 | 10.8 |
| TP 3.0R | 10.8% | +0.117 | 27.2 |
| **actual (mixed)** | 37.1% | **+0.285** | **66.2** |

This corroborates the earlier partial-exit finding: the range module's runners
(single trades of +4R to +9.5R) are the entire edge, and any fixed cap destroys
them.

---

## 6. Diagnosis, ranked

1. **Execution bug — silent margin rejection.** Invalidates all prior results.
2. **Sizing not R-normalized**, and inversely correlated with edge (−64%).
3. **Confluence score inverted** — it downsizes the best trades.
4. **TREND_SHORT has no edge**; TREND_LONG is marginal.
5. **Session filter backwards.**
6. Frequency (232/yr) was never the real problem — 420 signals exist. It was
   masked by defect 1.

Answering the question posed: the low PnL is **not** "too few trades" and **not**
"bad trades" — it is a **broken measurement plus sizing that bets least on the
best trades.** Underneath, per-trade expectancy on the executed subset was
genuinely positive (+0.285R), but that subset was selected by a bug.

---

## 7. Honest status and what I did NOT do

- I stopped at Phase 4. Optimizing entries/exits (Phases 5–6), building the
  evaluation risk engine (7), walk-forward (8) or Monte Carlo (9) on top of a
  measurement this broken would produce confident nonsense.
- **Every performance number in this project's earlier documents
  (V8.3, V11.1, V12) is invalid** and should be disregarded.
- The trade-level data is in `audit_232_trades.txt` (232 rows:
  setup|regime|hourUTC|dayOfWeek|inSession|confluence|sizeMult|R|MFE_R|MAE_R|bars),
  reproducible with `audit_analysis_1.py` / `audit_analysis_2.py`.
- MFE/MAE come from Pine's own `strategy.closedtrades.max_runup()` /
  `.max_drawdown()`, not reconstructions.
- All findings remain in-sample on one instrument. Nothing here is
  out-of-sample validated.

## 8. Recommended next step

Rebuild the sizing and execution layer before touching strategy logic:
1. Set realistic leverage and add an explicit notional cap that **reduces**
   position size rather than letting the broker reject the order.
2. Make risk truly constant per trade (delete both multipliers).
3. Re-measure the four setups independently under correct execution.
4. Only then decide whether the mean-reversion half is worth keeping alone.

Expected outcome: honestly, a much smaller edge than previously believed, and
possibly none. That needs to be established before any evaluation-passing
simulation means anything.

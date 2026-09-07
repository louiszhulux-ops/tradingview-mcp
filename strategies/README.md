# XAUUSD automated strategy — development record

Pine Script v6 strategies built and validated against a live TradingView Desktop
chart through this MCP server. All backtests are OANDA:XAUUSD, 15-minute,
$50,000 starting capital.

## Current release

**`V8_3_XAU_trend_range.pine`** — two independent entry modules sharing one risk
engine.

| Metric (2025-10-01 → 2026-09-03, ~11 months, costs modelled) | Value |
|---|---|
| Trades | 136 (~12/month) |
| Win rate | 32.4% |
| Profit factor | 1.475 |
| Net profit | +$6,072 (+12.1%) |
| Max drawdown | $1,626 (3.01%) |
| Return / drawdown | 3.73 |

Execution cost is modelled at $0.20 per ounce per side (~$0.40 round-trip),
covering spread, slippage and commission. See `V8_3_COST_VALIDATION.md` for the
full cost-sensitivity study.

### The two modules

- **Trend** — HTF (1H EMA50/200) trend filter, then liquidity sweep → break of
  structure → entry on the retrace into the resulting FVG or breaker block.
  Targets the nearest untapped liquidity (swing highs/lows, PDH/PDL, PWH/PWL),
  front-run by 0.10x ATR. Cost-immune: 5x execution cost costs it 4% of profit.
- **Range** — only fires when the HTF trend filter says *sideways*. Fades a
  sweep of a 48-bar range extreme that closes back inside, targeting 80% of the
  travel to the opposite extreme. Requires 2.5R minimum. The weaker and more
  cost-sensitive of the two; `Enable RANGE module` switches it off in one click.

Both modules emit `alert()` JSON payloads on entry for webhook automation.

## Documents

| File | What it covers |
|---|---|
| `V8_3_COST_VALIDATION.md` | Execution-cost sensitivity; the rangeMinR fix |
| `V8_2_FULL_SAMPLE.md` | The 145-trade full-sample validation, zero cost |
| `V8_DUAL_INSTRUMENT_RESULTS.md` | NAS100 + XAUUSD; the delayed-feed diagnosis |
| `MORE_TRADES_INVESTIGATION.md` | Signal-funnel measurement; four failed relaxations |
| `V7_VALIDATION_REPORT.md` | Determinism, parameter sensitivity, negative results |

## Known limitations

- **Everything is in-sample.** Both modules were developed on the same 11 months
  of XAUUSD data. No true out-of-sample test has been run.
- Limit exits are assumed to fill whenever price touches them.
- A 32% win rate means runs of 6-10 consecutive losses are normal.
- Not forward-tested on a demo account. Do that before committing capital.

## Platform notes (learned the hard way)

- Strategy backtests compute **asynchronously** after any source edit or input
  change. Wait ~25-30s and poll `data_get_strategy_results` until two
  consecutive reads agree, or you will read partial numbers.
- A symbol with a `_DL` suffix (e.g. `CME_MINI_DL:NQ1!`) is a **delayed** feed.
  TradingView will not execute strategy orders on it at all — the backtest
  silently produces zero trades. Replay mode does not bypass this. Use a
  real-time feed.
- The `strategy()` declaration's own properties are exposed as settable study
  inputs (`in_44` commission type, `in_45` commission value, `in_46` slippage),
  so cost tiers can be swept via `indicator_set_inputs` without re-pushing source.
- `commission_value` must be a compile-time constant — it cannot be an
  `input.float()` inside the `strategy()` call.
- Pine arrays combined with user-defined functions containing for-loops caused
  runtime failures on this build; the shift-register pattern (`sh1..sh4`) is the
  workaround.
- Count entries as flat→in-position transitions, never with a counter
  incremented inside the order block — that re-runs on recalculation passes and
  inflates the count several-fold.

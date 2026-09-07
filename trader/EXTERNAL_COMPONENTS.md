# What Pine can and cannot do (brief §47), and the live-safety layer (§48)

The brief asks explicitly which parts cannot realistically be modelled in Pine.
Rather than pretending, here is the split.

## Pine can carry

| component | why it fits |
|---|---|
| context engine | EMAs, ADX, ATR, VWAP, session levels, opening range — all native |
| regime classifier | pure function of the above |
| setup detection | pivots, crosses, sweeps, retests — all bar-resolution |
| quality scoring | arithmetic on context variables |
| structural stops and R sizing | `syminfo.pointvalue` and `mintick` are exposed |
| bar-resolution execution | `strategy.entry` / `strategy.exit` with limit and stop |
| the evaluation account model | trailing MLL, lock, consistency — all computable |
| the journal | `table` and `label` output, readable back out |

## Pine cannot carry — and these are real gaps, not nitpicks

**1. Tick-accurate fills.** Pine resolves within a bar by assumption, not by
sequence. When a bar's range covers both stop and target it guesses. On a 5m bar
that is a material error for tight stops. *Mitigation:* the backtest is run on
the lowest timeframe that still holds enough history, and results are treated as
an upper bound. *External:* a tick-replay harness is required before live.

**2. Real order-book behaviour.** No spread series, no depth, no queue position.
The limit-order finding from V27 (+0.02R) assumes a resting limit fills when
price touches it. In reality a touch does not guarantee a fill — you must be
*through* the level or first in queue. **This is the single most optimistic
assumption in the whole system** and it works in the direction that flatters the
result. *External:* needs live fill-rate measurement before the +0.02R is trusted.

**3. Economic calendar.** There is no native events feed. Pine cannot know CPI is
at 08:30. *External:* a calendar service feeding blackout windows, with the bot
reading a "news blackout" flag.

**4. Persistent state across sessions.** Pine restarts from bar one on every
reload. Streak counts, per-setup running statistics, and yesterday's closing
balance cannot be trusted across a reload. *External:* the account state must
live in the execution layer, not the chart.

**5. Broker reconciliation.** Pine has no idea what the broker thinks the
position is. *External:* mandatory — see below.

**6. Cross-instrument exposure netting (§26).** Long MES + long MNQ + long MYM is
one macro bet, not three. Pine sees one chart. *External:* a portfolio-level
exposure layer that nets correlated risk before allowing a new position.

**7. Persistent learning / refitting.** The quality-model weights should be
refitted as the setup library accumulates trades. Pine cannot do this.
*External:* offline refit, with the weights pushed back as inputs.

## Live-execution safety layer (§48) — required before any real money

None of this belongs in Pine. It is an execution-layer specification.

    duplicate-order protection    idempotency key per signal; never two orders
                                  from one bar close
    position reconciliation       poll broker position every N seconds; any
                                  mismatch with the internal model halts trading
    order-state reconciliation    every working order confirmed against the
                                  broker; orphan orders cancelled
    emergency flatten             one call, market-out everything, cancel all
    max position limit            hard cap below the account's contract maximum
    max daily loss                hard cap, checked before every order
    max account drawdown          hard cap against the MLL floor with margin
    connection-failure handling   on disconnect: cancel working orders, do not
                                  open new risk, alert
    rejected-order handling       classify and never blindly retry a reject
    slippage protection           reject a fill worse than X ticks from expected
                                  and re-evaluate rather than chase
    stale-data detection          if the last tick is older than N seconds, stop
    kill switch                   manual and automatic, latching, requires an
                                  explicit human reset

**Failure principle:** on any loss of synchronisation the system flattens and
stops. It never guesses at state. A bot that is unsure what it owns must own
nothing.

## Validation gate (§49) — the order is not negotiable

    backtest -> out-of-sample -> walk-forward -> Monte Carlo
             -> tick replay -> paper trading -> small-scale live

The system is at step 1-2. Nothing here has been paper traded, and the
limit-order fill assumption in particular cannot be validated without it.

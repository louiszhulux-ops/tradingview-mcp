# V32 — Target Surface: pre-registration

Written **before** looking at any V32 output.

## Why this test exists

Every strategy in this project fixed the payoff ratio near 1.5:1 and searched
for entries. Holding the measured edge constant and varying the payoff ratio
alone moves the Monte Carlo pass rate from 49.6% to 93.8%, because variance per
trade falls faster than the target does:

| RR | win% needed for E=+0.088R | sd/trade | pass | bust |
|---|---|---|---|---|
| 1.50 | 43.5% | 1.240 | 49.6% | 50.3% |
| 1.00 | 54.4% | 0.996 | 59.4% | 40.5% |
| 0.50 | 72.6% | 0.669 | 77.0% | 21.8% |
| 0.25 | 87.1% | 0.419 | 93.8% | 3.5% |

That table is **not** a result. It assumes the R-edge survives the tightening,
and Wald's identity says it does not. For a diffusion with drift `mu` stopped at
`+a / -b`, `E[X_tau] = mu*E[tau]` and `E[tau] ~ a*b/sigma^2`, so

    E[R] ~ mu * a / sigma^2

The R-edge is proportional to the **target**, not the stop. Halve the target and
you halve the edge, while cost_R (which scales with the *stop*) is unchanged.
Under that law, tightening buys nothing.

The law only holds for **constant** drift. If the edge is front-loaded — a fast
imbalance after a liquidity event that decays — then `E[R]` is flat or concave
in `a`, and the variance collapse is close to free. Simulating both:

| RR | uniform-drift pass | front-loaded pass |
|---|---|---|
| 1.50 | 49.6% | 49.6% |
| 1.00 | 54.6% | 57.8% |
| 0.75 | 52.7% | 60.3% |
| 0.50 | 48.3% | 64.4% |

The whole question is **which shape the real market has**. It has never been
measured in this project.

## Hypotheses

- **H0 (uniform drift):** `E[R](a) / a` is constant. Tightening the target is
  edge-neutral before cost and edge-negative after it.
- **H1 (front-loaded):** `E[R](a) / a` rises as `a` falls. Tightening is a free
  variance reduction.

## Measurement

Fixed stop `b = 1.5 x ATR(14)` for every configuration, so cost_R is constant
and the target is the only variable. Targets `a in {0.25, 0.5, 0.75, 1.0, 1.5,
2.0} x b`. Barriers resolved bar-by-bar on the 5m chart; **when both barriers
are touched inside one bar the STOP is assumed to have hit first**. Unresolved
after 96 bars (8h) → marked to close. Entry at the close of the trigger bar.

Four trigger families, each run on its long-side and its short-side trigger:
break-and-go, sweep-and-reclaim, trend pullback, VWAP reclaim.

## Controls

1. **Both-directions control.** Every trigger is simultaneously taken *with* it
   and *against* it, same stop, same target, same bar. On a driftless walk both
   give `E[R]=0` at every `a`. The statistic of record is

       edge(a) = ( E_with(a) - E_against(a) ) / 2

   which cancels any market drift common to both sides.
2. **Cross-market.** Gold selects nothing; MNQ validates. Shape must agree.
3. **Gross reporting.** Cost is a constant subtraction at every `a` and so
   cannot create or destroy the shape. Measured gross, cost applied afterwards.

## Decision rule, fixed in advance

Adopt a tight-target configuration only if **all three** hold:

1. `edge(a)` is positive out-of-sample at the chosen `a`, pooled across markets;
2. decay is sub-linear — `edge(0.75) >= 0.80 * edge(1.5)`, i.e. keeping 80% of
   the edge while giving up 50% of the target distance;
3. the resulting `lambda = 2*E/sd^2` yields >= 75% pass in the Monte Carlo under
   the verified LucidFlex rules.

If `edge(a)/a` is flat within noise, H0 stands, this route is closed, and I say
so rather than fitting a target multiple to the best cell.

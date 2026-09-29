# V21 — the cross-market screen. Nothing passes.

Protocol and acceptance criteria were committed **before** this ran
(`V21_SCREEN_PROTOCOL.md`, commit f2ed2c7). Nothing below has been re-tuned.

## Result

8 signals × 4 markets × 2 eras = **64 independent cells, ~16,000 simulated
trades**, all in R multiples with 0.08R of costs charged per trade.

| signal | IS markets + | OOS markets + | IS mean R | OOS mean R | verdict |
|---|---|---|---|---|---|
| 0 trend continuation L | 2/4 | 1/4 | +0.010 | −0.057 | fail |
| 1 trend continuation S | 2/4 | 2/4 | −0.060 | −0.031 | fail |
| 2 range break, faded L | 0/4 | 1/4 | −0.114 | −0.089 | fail |
| 3 range break, faded S | 0/4 | 0/4 | −0.045 | −0.123 | fail |
| 4 range break, followed L | 0/4 | 2/4 | −0.092 | +0.023 | fail |
| 5 range break, followed S | 1/4 | 0/4 | −0.051 | −0.176 | fail |
| 6 sweep reclaim L | 2/4 | 0/4 | +0.023 | −0.132 | fail |
| 7 sweep reclaim S | 0/4 | 1/4 | −0.097 | −0.019 | fail |

**Zero signals clear criterion 1** (positive in ≥3 of 4 markets in-sample). The
screen therefore ends at the first hurdle; the out-of-sample column is reported
for completeness and was not used to rescue anything.

## The number that matters

    pooled NET mean R per trade    -0.0644
    cost charged per trade         -0.0800
    implied GROSS mean R per trade +0.0156
    cells with positive mean R      14 / 64

Before costs, this entire family of signals has an expectancy of **+0.016R** —
indistinguishable from zero across sixteen thousand trades. The whole of the
negative net result is transaction cost.

That is what an efficient market looks like from the inside. It is not that the
signals are badly built or badly tuned; it is that at this level of analysis
there is no predictable component left to capture.

## What this closes

The both-directions design makes the diagnosis unambiguous, because each trigger
carries its own control:

- **Trend continuation** — on gold in-sample, long was +0.197R and short was
  −0.173R. Near-perfect mirror images. That is not a trend edge, it is directional
  drift: gold rose. A real trend effect pays in both directions; this pays only
  in the direction the market happened to go.
- **Range breaks** — negative both faded (2,3) and followed (4,5). Both sides of
  the same trigger losing means the trigger carries no information at all; the
  only thing being harvested is the spread, by someone else.
- **Sweep reclaim** — the V17 setup. On gold in-sample the short side is
  **−0.217R at t = −2.68**, the opposite sign to the result I originally reported.
  This is the fourth independent confirmation that the V17 finding was noise.

## Where this leaves the search

Across this project the following have now been tested and failed out-of-sample:
nine textbook entries, the encoded discretionary process, exit-first construction,
trend following, Donchian breakout, sweep-reclaim, opening range, VWAP fade, and
now this eight-signal family across four asset classes and two eras.

I do not think further searching in this space is worth your time or mine. The
honest conclusion is that **simple technical signals on liquid futures, tested
properly, do not contain a tradeable edge** — and every time this project
appeared to find one, the appearance came from testing too many variants against
too little independent data.

## What is still true and still valuable

The execution layer is real, validated, and independent of any edge:

- **Buffer-based sizing produces 0.00% ruin under the observed edge, under the
  lower confidence bound, and under no edge at all** — because after a full loss
  the buffer becomes `buffer × (1 − frac)`, which cannot cross the floor.
- Three execution bugs found and fixed, each of which would silently corrupt any
  strategy: trailing exits with no protective stop; the entry bar unprotected
  because `strategy.position_size` is still 0 when the order is submitted; and
  `close_all()` filling at the next bar's open, so a Friday flat executes Sunday.
- The contract-granularity arithmetic: stop width sets contracts per dollar of
  risk, which sets how many R of buffer a $2,000 trailing limit actually buys.
- A measurement harness that has now caught its own false positive.

Under buffer sizing with **no edge at all**, an evaluation attempt resolves at
roughly 20–30% pass, 0% bust, remainder unresolved. That is a real, fully
automated, no-manual-input system. It is a favourable lottery ticket rather than
a trading edge, and it should be described as exactly that.

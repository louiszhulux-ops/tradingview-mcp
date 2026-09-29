# Phase 2 — setup families actually represented in the code

The instruction was to include a family only if the current code and data
support it. All eight of the listed families **are** represented — seven were
measured in the eight-family comparison (`SETUP_FAMILIES.md`) and the eighth in
the V47 ablation. Nothing below is invented, and every number is a measurement
already in this repository.

| # | family | where it lives | what creates the setup | trigger | invalidation | destination | direction | measured |
|---|---|---|---|---|---|---|---|---|
| **B** | **sweep → rejection** | the base detector, V47 config 1 | wick ≥ 0.10×ATR beyond prev-day H/L, Asia H/L or a 10-bar pivot **and close back inside** — the close-back-inside *is* the rejection | limit at the swept level, 24-bar window | sweep extreme ± 0.20×ATR | nearest opposing level | **direction-agnostic** — the swept side sets it | −0.100R, 2/10, n 5,479, t −3.27 (dev); +0.024R, 5/10 (test) |
| **A** | sweep → reclaim | V47 config 6 | as B, plus a close 0.25×ATR beyond the level within 12 bars | same | same | same | direction-agnostic | −0.021R, 4/10, n 2,001 (dev); −0.024R, 3/7 (test). **Null** |
| **E** | liquidity-sweep **continuation** | V47 configs 2 / 4 | as B, filtered to sweeps aligned with the 4H trend | same | same | same | **directional by construction** | +0.132R, 7/10, n 674 (dev); **−0.074R (test) — failed** |
| **F** | liquidity-sweep **reversal** | the complement of E | as B, sweeps opposed to the 4H trend | same | same | same | directional | −0.028R (dev); **+0.139R (test)** — i.e. it *beat* E out-of-sample |
| **C** | displacement → retracement | V47 config 5, V44 L4, family F3 | a bar with range ≥ 1.5×ATR in the trade direction within 12 bars of a sweep | limit at the level (config 5) or at the displacement 50% (L4) | same | same | directional | **−0.366R, 0/10, t −5.24** (dev). As L4, **9 fills from 605 arms**. Worst result in the project |
| **D** | break / retest | family F4 | close beyond a structural swing, then return | limit at the broken level | beyond the swing | next opposing level | directional | −0.095R, 1/4, n 412 |
| **G** | range expansion / breakout | families F1, F7 | close beyond a range or the opening range | breakout + acceptance | back inside the range | measured range height | directional | F1 −0.146R, 1/4, n 259; **F7 −0.714R, 0/4, t −3.89** |
| **H** | failed breakout / trap | family F2 | breakout that closes back inside | re-entry into the range | beyond the failed extreme | opposite side of the range | direction-agnostic | **−0.449R, 0/4, t −2.75** |

Plus one family that is not on the list but is in the code and is the current
best-measured setup:

| — | range mean-reversion (F6) | family lab, V45 | price at a 20-bar range extreme with ADX < 20 | limit at the extreme | beyond it | opposite side | direction-agnostic | +0.134R, 3/4, n 1,335, t +1.94; **93% disjoint from the sweep family** |

## What this says about the frequency problem

**The low trade count is not caused by having too few families.** Nine distinct
families exist in the code. Six of them are measurably negative, two of those
significantly so (failed breakout t = −2.75, opening-range break t = −3.89).
Adding more families of this kind would add trades and subtract money.

**Frequency per family is also not the constraint.** The base sweep detector
alone produces 7,712 events and 5,479 fills in 57 days across ten cells — 96 a
day. What removes them is the filter stack, not a shortage of setups
(`PIPELINE_AUDIT.md` §2).

**Two families are direction-agnostic and both survived their own tests**: the
raw sweep-rejection (B) and range mean-reversion (F6), which are 93% disjoint.
The directional families are where the failures cluster — E failed out-of-sample,
C is the worst result in the project, D and G are negative.

**One result deserves flagging because it is uncomfortable.** On fold C the
bias-*opposed* sweeps (family F, +0.139R) outperformed the bias-*aligned* ones
(family E, −0.068R). That is the opposite of the continuation thesis. It is
n = 287 vs 315 on one 22-day window with a CI spanning zero, so it is **not**
evidence that fading works — but it is the second independent time the
continuation framing has failed to survive, and it should not be quietly
dropped.

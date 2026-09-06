# Phase 15 — Experiment A: CHOCH pivot lookback (`swLen`)

Four arms, pooled A+B+C, 8 cells each. `swLen = 3` is the frozen control and is
not re-run: it is the committed Phase 13F + Phase 14 baseline, verified in
`POOLED_DESIGN_VERIFICATION.md`. File byte-identical to V53; only input `in_14`
differs. All Phase 13E assertions read **0 in all 24 runs**.

## Behavioural effect — pooled A+B+C funnel

| arm | LTF | sweeps | CHOCH | sweep→CHOCH | retest→BOS+disp | FVG | **fills** | sweep→fill |
|---|---|---|---|---|---|---|---|---|
| swLen 2 | 1m | 3836 | 3574 | **93.2%** | 4.23% | 101 | **56** | 1.46% |
| **swLen 3 (control)** | 1m | 3836 | 3324 | **86.7%** | 3.60% | 76 | **41** | 1.07% |
| swLen 4 | 1m | 3836 | 3019 | **78.7%** | 2.83% | 56 | **30** | 0.78% |
| swLen 5 | 1m | 3836 | 2720 | **70.9%** | 2.67% | 46 | **28** | 0.73% |
| swLen 2 | 3m | 3836 | 2061 | **53.7%** | 7.09% | 84 | **36** | 0.94% |
| **swLen 3 (control)** | 3m | 3836 | 1480 | **38.6%** | 6.76% | 50 | **17** | 0.44% |
| swLen 4 | 3m | 3836 | 1043 | **27.2%** | 5.05% | 27 | **11** | 0.29% |
| swLen 5 | 3m | 3836 | 739 | **19.3%** | 5.47% | 19 | **5** | 0.13% |

**Sweeps are identical (3836) in every arm and both LTFs** — the expected
signature of an LTF-only change, and a direct confirmation that the 5m sweep
engine is untouched.

The response is **monotone and steep at every funnel stage**. Total fills across
both LTFs: **92 → 58 → 41 → 33** for swLen 2 → 3 → 4 → 5.

## Performance effect

| arm | LTF | fills | W | R post-drag | expectancy | alt events | % fills in multi-fill clusters |
|---|---|---|---|---|---|---|---|
| swLen 2 | 1m | 56 | 4 | −35.425 | −0.6326 | 34 | 71.4% |
| **swLen 3** | 1m | 41 | 5 | **−13.389** | **−0.3266** | 25 | 73.2% |
| swLen 4 | 1m | 30 | 2 | −19.664 | −0.6555 | 20 | 66.7% |
| swLen 5 | 1m | 28 | 2 | −17.558 | −0.6271 | 20 | 57.1% |
| swLen 2 | 3m | 36 | 7 | +4.224 | +0.1173 | 23 | 69.4% |
| **swLen 3** | 3m | 17 | 4 | **+6.482** | **+0.3813** | 12 | 58.8% |
| swLen 4 | 3m | 11 | 2 | +0.626 | +0.0569 | 7 | 72.7% |
| swLen 5 | 3m | 5 | 0 | −5.171 | −1.0342 | 4 | 40.0% |

## Reading — descriptive only

1. **`swLen` is the strongest frequency lever tested so far.** It changes fill
   count by a factor of ~2.8 across the tested range (92 vs 33) without touching
   a single sweep.
2. **3m is far more sensitive than 1m.** From swLen 2 to 5, 3m fills fall 7.2×
   (36 → 5) while 1m fills fall 2.0× (56 → 28). This is the same structural
   asymmetry measured in Phases 13E/13F/14: 3m has only ~20 bars inside the
   `dispWait` window, and each unit of `swLen` consumes two of them
   (confirmation lag plus the swing itself), so the whole sequence is squeezed
   at the front. On 1m the same cost is a small fraction of a 60-bar window.
3. **The effect is on the front of the funnel, not the back.** sweep→CHOCH moves
   22 points on 1m and 34 points on 3m; the downstream conversions
   (BOS→FVG, FVG→fill) move much less. `swLen` gates how much structure exists,
   not what happens to it.
4. **Performance does not respond monotonically.** 1m expectancy runs −0.63,
   −0.33, −0.66, −0.63 and 3m runs +0.12, +0.38, +0.06, −1.03 for swLen
   2/3/4/5. There is no trend to read: the win counts are 0–7 in every cell, so
   each arm's total R is decided by a handful of trades. **No arm is ranked and
   no arm is preferred.**
5. **Clustering does not deteriorate with more fills.** The proportion of fills in
   multi-fill clusters stays in a 40–73% band across all arms, i.e. the extra
   trades that swLen 2 produces are not disproportionately duplicates of each
   other.

**The frozen `swLen = 3` remains the baseline regardless of any number above.**

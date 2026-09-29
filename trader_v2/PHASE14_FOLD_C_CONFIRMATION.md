# Phase 14 — untouched Fold C out-of-sample confirmation

Fold C, run once, on the committed V53 with every frozen value untouched. **No
parameter was changed, nothing was optimised, no threshold was tested, no filter
was added, no trade was removed or deduplicated, no instrument or direction was
dropped, and no implementation change was made in response to any observation.**
Fold C was run to completion; results were not inspected mid-run and nothing was
re-run with altered settings.

Raw output for all 8 runs: `trader_v2/v53_runs_foldc/`. Analysis script:
`trader_v2/p14_foldc.py` (reads only committed run files). Full script output:
`trader_v2/v53_runs_foldc/PHASE14_raw_output.txt`.

---

## 1. Executive conclusion

**Fold C is broadly consistent with A+B.** The funnel reproduces closely at every
stage, the structural 1m/3m asymmetry reproduces, and both hypotheses land where
A+B left them: near breakeven with intervals that span it in both directions.

The three numbers that matter: Fold C produced **18 fills** (13 on 1m, 5 on 3m),
a **16.7% win rate** against a 16.7% breakeven, and **−0.842R** after drag. Neither
hypothesis reversed sign in a way that would look like a discovery, and neither
collapsed in a way that would look like a failure. **Clustering is worse than in
A+B**: 88.9% of Fold C fills sit in multi-fill clusters under the alternative
identity, versus 60.0% in A+B, so 18 fills correspond to **10 market events**.

## 2. Frozen-spec confirmation

Verified before the run and again after:

- `git diff HEAD -- trader_v2/V53_ltf_sequence.pine` → **V53 UNCHANGED**
- `git diff HEAD -- trader_v2/v53_runs/` → **A+B run files UNCHANGED**
- Live indicator inputs read back from the chart: `tgtR 5`, `bufATR 0.2`,
  `minWick 0.1`, `dispMin 1.5`, `dispWait 12`, `retBars 24`, `minRatr 0.05`,
  `maxRatr 3`, `maxBars 144`, `costUSD 3`, `swLen 10`, `lSw 3` — **identical to
  Phase 13E/13F**. Only `dirMode`, `foldSel` and `ltfSel` were varied.
- Fold C is the only new performance sample. All Phase 13E assertions (A21–A27,
  A32) read **0/0/0/0/0/0/0/0 in all 8 Fold C runs**.

## 3. Coverage

Fold C = `time >= 2026-08-09 00:00` and `< 2026-08-31 00:00`.

| | 1m | 3m |
|---|---|---|
| Fold C chart bars (all 8 cells) | **4,164** | **4,164** |
| bars carrying valid LTF data | **4,164** | **4,164** |
| **coverage** | **100.0%** | **100.0%** |
| uncovered bars | **0 (0.0%)** | **0 (0.0%)** |
| earliest LTF timestamp in fold | **2026-08-09 22:00 UTC** | **2026-08-09 22:00 UTC** |
| latest LTF timestamp in fold | **2026-08-30 23:55 UTC** | **2026-08-30 23:55 UTC** |
| total intrabar values available | 100,000 (cap) | 34,239 / 34,269 |

**Fold C is fully covered on both LTFs.** This is better than fold A, where 1m
reached only 94.5%. Nothing was filled, substituted or extended. The first covered
bar is 08-09 22:00 rather than 08-09 00:00 because 08-09 is a Sunday and the
session opens at 22:00 UTC; the last is 08-30 23:55 for the same reason at the
other end. Both are session boundaries, not data gaps.

## 4. Eight-cell execution-level results

```
cell              bars   cov  swp CHOCH rtst BOS FVG fill W Ls TO     wr  Rpre   Rpost      avg      med mcL    ddR   ddUSD      USD
------------------------------------------------------------------------------------------------------------------------------------
MGC L 1m C        4164  4164  179   155  132   4   3    1 0  1  0   0.0%    -1  -1.149  -1.1490  -1.1494   1  1.149   23.08   -23.08
MGC L 3m C        4164  4164  179    72   58   6   3    0 0  0  0      -     0   0.000        -        -   0  0.000    0.00     0.00
MGC S 1m C        4164  4164  214   205  171   9   7    4 0  4  0   0.0%    -4  -4.154  -1.0385  -1.0327   4  4.154  353.07  -353.07
MGC S 3m C        4164  4164  214    94   59   1   1    0 0  0  0      -     0   0.000        -        -   0  0.000    0.00     0.00
MNQ L 1m C        4164  4164  209   187  178   3   2    2 0  2  0   0.0%    -2  -2.057  -1.0285  -1.0285   2  2.057  216.41  -216.41
MNQ L 3m C        4164  4164  209    74   52   0   0    0 0  0  0      -     0   0.000        -        -   0  0.000    0.00     0.00
MNQ S 1m C        4164  4164  257   230  198   9   7    6 2  4  0  33.3%     6   5.724   0.9540  -1.0319   2  2.146  194.67   594.17
MNQ S 3m C        4164  4164  257   111   75  10  10    5 1  4  0  20.0%     1   0.794   0.1588  -1.0338   4  4.171  364.30    62.65

```

Roll-up:

| | fills | W | L | timeouts | win rate | R pre-drag | R post-drag | avg R/fill | $ post-drag |
|---|---|---|---|---|---|---|---|---|---|
| **Fold C H1 (1m)** | 13 | 2 | 11 | 0 | 15.4% | −1 | **−1.636** | −0.126 | **+$1.61** |
| **Fold C H2 (3m)** | 5 | 1 | 4 | 0 | 20.0% | +1 | **+0.794** | +0.159 | **+$62.65** |
| **Fold C total** | **18** | **3** | **15** | **0** | **16.7%** | 0 | **−0.842** | −0.047 | **+$64.26** |

Three cells produced zero trades (MGC long 3m, MGC short 3m, MNQ long 3m) and are
included above. **Not one Fold C trade ended in a timeout** — every one of the 15
losses was a stop, against 3 timeouts in 34 A+B losses.

The sign split between R and dollars in H1 (−1.636R but +$1.61) is not an error:
each trade's dollar result is `R × r × point value` and `r` varies per trade, so a
negative R sum can carry a marginally positive dollar sum when the winners have
larger point-risk than the losers.

## 5. Full trade ledger — all 18 Fold C fills

Format as Phase 13F. **Exit timestamps are not available**: V53 records `bars held`
but not an exit time, and adding one would modify the implementation, which this
phase forbids. `bars held` is reported as-is.

```
 1. MGC1!|L|1m|C|sw 2026-08-10 00:00|SW|swX 4391.4|ch 2026-08-10 00:50|chL 4395|rt 2026-08-10 00:51|bos 2026-08-10 01:01|bosL 4396.4|fvg 4392.5-4393.9|en 2026-08-10 01:05|enPx 4392.5|stop 4390.4924|LOSS|-1.149R|$-23.08|stop|1bars
 2. MGC1!|S|1m|C|sw 2026-08-17 11:45|PD|swX 4457.6|ch 2026-08-17 12:01|chL 4451.3|rt 2026-08-17 12:02|bos 2026-08-17 12:26|bosL 4449.4|fvg 4446.2-4447.7|en 2026-08-17 13:35|enPx 4447.7|stop 4458.3637|LOSS|-1.028R|$-109.64|stop|3bars
 3. MGC1!|S|1m|C|sw 2026-08-17 11:50|PD|swX 4455.5|ch 2026-08-17 12:09|chL 4450|rt 2026-08-17 12:10|bos 2026-08-17 12:26|bosL 4449.4|fvg 4446.2-4447.7|en 2026-08-17 13:35|enPx 4447.7|stop 4456.2691|LOSS|-1.035R|$-88.69|stop|3bars
 4. MGC1!|S|1m|C|sw 2026-08-24 11:40|AS|swX 4724.5|ch 2026-08-24 12:01|chL 4713|rt 2026-08-24 12:07|bos 2026-08-24 12:32|bosL 4712.5|fvg 4712.7-4716|en 2026-08-24 12:35|enPx 4716|stop 4725.8876|LOSS|-1.03R|$-101.88|stop|1bars
 5. MGC1!|S|1m|C|sw 2026-08-24 11:45|AS+SW|swX 4719.5|ch 2026-08-24 12:01|chL 4713|rt 2026-08-24 12:07|bos 2026-08-24 12:32|bosL 4712.5|fvg 4712.7-4716|en 2026-08-24 12:35|enPx 4716|stop 4720.987|LOSS|-1.06R|$-52.87|stop|1bars
 6. MNQ1!|L|1m|C|sw 2026-08-17 12:40|AS|swX 30183|ch 2026-08-17 12:52|chL 30198|rt 2026-08-17 12:54|bos 2026-08-17 13:30|bosL 30227.5|fvg 30229.75-30230.5|en 2026-08-17 13:35|enPx 30229.75|stop 30178.6201|LOSS|-1.029R|$-105.26|stop|1bars
 7. MNQ1!|L|1m|C|sw 2026-08-17 12:45|AS|swX 30180|ch 2026-08-17 13:00|chL 30211|rt 2026-08-17 13:01|bos 2026-08-17 13:30|bosL 30227.5|fvg 30229.75-30230.5|en 2026-08-17 13:35|enPx 30229.75|stop 30175.6758|LOSS|-1.028R|$-111.15|stop|1bars
 8. MNQ1!|S|1m|C|sw 2026-08-12 19:10|PD|swX 29894.25|ch 2026-08-12 19:37|chL 29853.25|rt 2026-08-12 19:38|bos 2026-08-12 19:55|bosL 29838.75|fvg 29837.5-29848.75|en 2026-08-12 20:00|enPx 29848.75|stop 29897.8758|LOSS|-1.031R|$-101.25|stop|1bars
 9. MNQ1!|S|1m|C|sw 2026-08-12 19:20|PD|swX 29890.25|ch 2026-08-12 19:37|chL 29853.25|rt 2026-08-12 19:38|bos 2026-08-12 19:55|bosL 29838.75|fvg 29837.5-29848.75|en 2026-08-12 20:00|enPx 29848.75|stop 29893.9595|LOSS|-1.033R|$-93.42|stop|1bars
10. MNQ1!|S|1m|C|sw 2026-08-24 11:45|SW|swX 29260.5|ch 2026-08-24 12:18|chL 29207.5|rt 2026-08-24 12:19|bos 2026-08-24 12:32|bosL 29213.5|fvg 29202.25-29217.5|en 2026-08-24 12:35|enPx 29217.5|stop 29265.7452|WIN|4.969R|$479.45|target|13bars
11. MNQ1!|S|1m|C|sw 2026-08-24 11:55|SW|swX 29254.75|ch 2026-08-24 12:18|chL 29207.5|rt 2026-08-24 12:19|bos 2026-08-24 12:32|bosL 29213.5|fvg 29202.25-29217.5|en 2026-08-24 12:35|enPx 29217.5|stop 29259.7479|WIN|4.964R|$419.48|target|13bars
12. MNQ1!|S|1m|C|sw 2026-08-28 12:30|SW|swX 29661.75|ch 2026-08-28 13:20|chL 29651.25|rt 2026-08-28 13:21|bos 2026-08-28 13:30|bosL 29622.25|fvg 29612.5-29627.25|en 2026-08-28 13:35|enPx 29627.25|stop 29665.223|LOSS|-1.04R|$-78.95|stop|1bars
13. MNQ1!|S|1m|C|sw 2026-08-28 12:35|SW|swX 29637.75|ch 2026-08-28 13:20|chL 29651.25|rt 2026-08-28 13:21|bos 2026-08-28 13:30|bosL 29622.25|fvg 29612.5-29627.25|en 2026-08-28 13:35|enPx 29627.25|stop 29641.3214|LOSS|-1.107R|$-31.14|stop|1bars
14. MNQ1!|S|3m|C|sw 2026-08-24 11:45|SW|swX 29260.5|ch 2026-08-24 12:03|chL 29230.75|rt 2026-08-24 12:06|bos 2026-08-24 12:30|bosL 29203|fvg 29208-29222.75|en 2026-08-24 12:40|enPx 29222.75|stop 29265.7452|WIN|4.965R|$426.95|target|12bars
15. MNQ1!|S|3m|C|sw 2026-08-27 20:05|SW|swX 29693.75|ch 2026-08-27 20:48|chL 29634.25|rt 2026-08-27 20:57|bos 2026-08-27 22:00|bosL 29620.25|fvg 29623-29628.5|en 2026-08-27 22:15|enPx 29628.5|stop 29699.2307|LOSS|-1.021R|$-144.46|stop|47bars
16. MNQ1!|S|3m|C|sw 2026-08-27 20:10|AS|swX 29667.5|ch 2026-08-27 20:48|chL 29634.25|rt 2026-08-27 20:57|bos 2026-08-27 22:00|bosL 29620.25|fvg 29623-29628.5|en 2026-08-27 22:15|enPx 29628.5|stop 29672.8749|LOSS|-1.034R|$-91.75|stop|36bars
17. MNQ1!|S|3m|C|sw 2026-08-28 12:30|SW|swX 29661.75|ch 2026-08-28 13:21|chL 29650|rt 2026-08-28 13:24|bos 2026-08-28 13:30|bosL 29613.5|fvg 29613.75-29622.75|en 2026-08-28 13:40|enPx 29622.75|stop 29665.223|LOSS|-1.035R|$-87.95|stop|1bars
18. MNQ1!|S|3m|C|sw 2026-08-28 12:35|SW|swX 29637.75|ch 2026-08-28 13:21|chL 29650|rt 2026-08-28 13:24|bos 2026-08-28 13:30|bosL 29613.5|fvg 29613.75-29622.75|en 2026-08-28 13:40|enPx 29622.75|stop 29641.3214|LOSS|-1.081R|$-40.14|stop|1bars
```

## 6. Funnel conversions

```
A+B  1m          sweeps  2977 | ->CHOCH  2547  85.6% | ->retest 2295  90.1% | ->BOS+disp  82  3.57% | ->FVG  57  69.5% | ->fill  28  49.1% | sweep->fill  0.94%
C    1m          sweeps   859 | ->CHOCH   777  90.5% | ->retest  679  87.4% | ->BOS+disp  25  3.68% | ->FVG  19  76.0% | ->fill  13  68.4% | sweep->fill  1.51%
A+B  3m          sweeps  2977 | ->CHOCH  1129  37.9% | ->retest  851  75.4% | ->BOS+disp  57  6.70% | ->FVG  36  63.2% | ->fill  12  33.3% | sweep->fill  0.40%
C    3m          sweeps   859 | ->CHOCH   351  40.9% | ->retest  244  69.5% | ->BOS+disp  17  6.97% | ->FVG  14  82.4% | ->fill   5  35.7% | sweep->fill  0.58%

```

| step | A+B 1m | **C 1m** | A+B 3m | **C 3m** |
|---|---|---|---|---|
| sweep → CHOCH | 85.6% | **90.5%** | 37.9% | **40.9%** |
| CHOCH → retest | 90.1% | **87.4%** | 75.4% | **69.5%** |
| retest → BOS+displacement | 3.57% | **3.68%** | 6.70% | **6.97%** |
| BOS → FVG | 69.5% | **76.0%** | 63.2% | **82.4%** |
| FVG → fill | 49.1% | **68.4%** | 33.3% | **35.7%** |
| **sweep → fill** | **0.94%** | **1.51%** | **0.40%** | **0.58%** |

The two stages that dominate the funnel are **essentially unchanged**: sweep→CHOCH
moves 4.9 points on 1m and 3.0 on 3m, and the binding retest→BOS+displacement gate
moves 0.11 points on 1m and 0.27 on 3m. The later stages (BOS→FVG, FVG→fill) are
higher in Fold C, but they operate on 25 and 17 events respectively, so a
difference of a few events moves them several percent.

## 7. Event-clustering results

Phase 13G identities applied verbatim, with the A+B numbers as control.

```
  FOLD C             primary      all : execution N 18 | clusters 12 | multi-fill  6 | largest 2 | fills in multi 12 ( 66.7%)
  FOLD C             primary      1m  : execution N 13 | clusters  9 | multi-fill  4 | largest 2 | fills in multi  8 ( 61.5%)
  FOLD C             primary      3m  : execution N  5 | clusters  3 | multi-fill  2 | largest 2 | fills in multi  4 ( 80.0%)
  FOLD C             alternative  all : execution N 18 | clusters 10 | multi-fill  8 | largest 2 | fills in multi 16 ( 88.9%)
  FOLD C             alternative  1m  : execution N 13 | clusters  7 | multi-fill  6 | largest 2 | fills in multi 12 ( 92.3%)
  FOLD C             alternative  3m  : execution N  5 | clusters  3 | multi-fill  2 | largest 2 | fills in multi  4 ( 80.0%)

  A+B (13G control)  primary      all : execution N 40 | clusters 31 | multi-fill  9 | largest 2 | fills in multi 18 ( 45.0%)
  A+B (13G control)  primary      1m  : execution N 28 | clusters 22 | multi-fill  6 | largest 2 | fills in multi 12 ( 42.9%)
  A+B (13G control)  primary      3m  : execution N 12 | clusters  9 | multi-fill  3 | largest 2 | fills in multi  6 ( 50.0%)
  A+B (13G control)  alternative  all : execution N 40 | clusters 27 | multi-fill 11 | largest 3 | fills in multi 24 ( 60.0%)
  A+B (13G control)  alternative  1m  : execution N 28 | clusters 18 | multi-fill  8 | largest 3 | fills in multi 18 ( 64.3%)
  A+B (13G control)  alternative  3m  : execution N 12 | clusters  9 | multi-fill  3 | largest 2 | fills in multi  6 ( 50.0%)
```

| | A+B | **Fold C** |
|---|---|---|
| execution fills | 40 | **18** |
| primary clusters | 31 | **12** |
| alternative clusters | 27 | **10** |
| multi-fill clusters (alt) | 11 | **8** |
| largest cluster | 3 | **2** |
| **% of fills in multi-fill clusters (alt)** | **60.0%** | **88.9%** |
| same, 1m only | 64.3% | **92.3%** |
| same, 3m only | 50.0% | **80.0%** |

**Clustering is materially worse in Fold C.** Only 2 of 18 fills are singletons.
On 1m, 12 of 13 fills belong to a pair. The convergence behaviour audited in Phase
13G is not an A+B artefact — it is a persistent property of the frozen
specification, and in this sample it is more pronounced.

## 8. A+B versus Fold C

**Execution level**

| | A+B H1 | **C H1** | A+B H2 | **C H2** |
|---|---|---|---|---|
| fills | 28 | **13** | 12 | **5** |
| wins / losses | 3 / 25 | **2 / 11** | 3 / 9 | **1 / 4** |
| win rate | 10.7% | **15.4%** | 25.0% | **20.0%** |
| mean R / expectancy | −0.420 | **−0.126** | +0.474 | **+0.159** |
| total R post-drag | −11.752 | **−1.636** | +5.687 | **+0.794** |
| dollar result | −$2,249.66 | **+$1.61** | +$376.60 | **+$62.65** |
| max drawdown (worst cell) | 10.677R | **4.154R** | 4.112R | **4.171R** |

Both hypotheses moved **towards** breakeven relative to A+B, from opposite sides —
H1 up from −0.42R to −0.13R, H2 down from +0.47R to +0.16R. Neither crossed in a
way that changes its character, and both remain inside the other's A+B confidence
interval.

**Funnel** — reproduces closely; see §6.

**Event dependence** — same phenomenon, more concentrated: 60.0% → 88.9% of fills
in multi-fill clusters.

None of this is used to recommend a parameter change; the comparison exists only
to answer the consistency question in §12.

## 9. H1 versus H2 — descriptive only

**No ranking.** The specific structural check the brief asked for:

> *"1m has more surviving CHOCH sequences but fewer displacement confirmations;
> 3m loses more sequences before CHOCH but reaches displacement more readily."*

**Fold C reproduces both halves.**

| | C 1m | C 3m |
|---|---|---|
| sweep → CHOCH | **90.5%** | 40.9% |
| retest → BOS + displacement | 3.68% | **6.97%** |
| structural breaks failing displacement | 4,110 | 208 |
| sequences expiring before a CHOCH | 82 | 482 |

1m carries 777 of 859 sweeps into a CHOCH and then loses 96.3% of survivors at the
displacement gate; 3m loses 59% of sweeps before a CHOCH exists but converts the
survivors to displacement roughly twice as often. This is the same asymmetry
measured in Phase 13E/13F, at the same magnitudes, on data neither hypothesis had
seen. `swLen` and the displacement threshold were not altered.

One further descriptive note: on 3m, **three of the four cells produced no trades
at all**, and the entire H2 Fold C result is one cell (MNQ short). On 1m every cell
produced at least one fill.

## 10. Statistical and dependence interpretation

```
  Fold C H1 (1m)   wins 2/13  =  15.4%  90% Wilson [  5.2%, 37.5%]  mean -0.107 sd 2.25 CI [-1.135,+0.921]
  Fold C H2 (3m)   wins 1/5   =  20.0%  90% Wilson [  4.6%, 56.5%]  mean +0.170 sd 2.68 CI [-1.804,+2.144]
  Fold C total     wins 3/18  =  16.7%  90% Wilson [  6.9%, 35.2%]  mean -0.030 sd 2.30 CI [-0.922,+0.862]
  A+B H1 (1m)      wins 3/28  =  10.7%  90% Wilson [  4.4%, 24.0%]  mean -0.387 sd 1.89 CI [-0.975,+0.200]
  A+B H2 (3m)      wins 3/12  =  25.0%  90% Wilson [ 10.5%, 48.7%]  mean +0.470 sd 2.71 CI [-0.819,+1.759]
  A+B total        wins 6/40  =  15.0%  90% Wilson [  8.0%, 26.5%]  mean -0.130 sd 2.17 CI [-0.694,+0.434]

  Breakeven win rate at +5R/-1R = 16.7%.
  These are EXECUTION-LEVEL intervals and assume independence between fills, which the
  clustering above shows is violated (88.9% of Fold C fills sit in multi-fill clusters).
  No event-level confidence interval is computed: 10 alternative-identity events, of which
  8 are 1m and 3 are 3m, does not support one.
```

| | execution N | primary event N | alternative event N |
|---|---|---|---|
| Fold C total | 18 | 12 | **10** |
| Fold C 1m | 13 | 9 | **7** |
| Fold C 3m | 5 | 3 | **3** |

The intervals above are **execution-level** and assume the 18 fills are
independent. §7 shows they are not — 88.9% are repeated observations of the same
downstream event — so those intervals are **optimistic about precision**. They
already span breakeven in both directions; the effective sample is smaller still.

**No event-level confidence interval is computed.** Ten events, of which three are
3m, does not support one, and manufacturing a dependence-adjusted test on that
sample would be inventing precision rather than measuring it.

Fold C's win rate of 3/18 = 16.7% sits exactly on the 16.7% breakeven for a
+5R/−1R payoff. That coincidence is not evidence of anything; with 18 trials the
next single outcome moves the rate by 5.6 points.

## 11. Limitations

1. **Exit timestamps are unavailable.** V53 records bars held, not exit times, and
   capturing them would modify the implementation. Trade durations and any
   cross-trade overlap analysis are therefore limited to bar counts.
2. **The effective sample is 10–12 events, not 18 trades.** Every performance
   figure here should be read against that number.
3. **H2 rests on a single cell.** Three of the four 3m cells are empty; MNQ short
   supplies all 5 fills and the entire +0.794R.
4. **Fold C is 22 calendar days** (4,164 chart bars) against A+B's ~10.5 weeks, so
   it is a smaller sample in both bars and trades.
5. **The two-outcome payoff makes the median uninformative.** Every cell containing
   a loss has a median near −1.03R by construction, at any win rate below 50%.
6. **Costs are the frozen $3.00 drag only.** No slippage model beyond it, and the
   dollar figures are single-contract.

## 12. Final conclusion

**Untouched Fold C produces results broadly consistent with the behaviour observed
on A+B.**

The evidence for consistency is the funnel and the structure, not the P&L: sweep →
CHOCH (85.6% → 90.5% on 1m; 37.9% → 40.9% on 3m) and the binding retest →
BOS+displacement gate (3.57% → 3.68% on 1m; 6.70% → 6.97% on 3m) reproduce almost
exactly on data the specification had never seen, as does the 1m/3m structural
asymmetry and the convergent-sequence clustering. Frequency remains in the same
band (sweep→fill 0.94% → 1.51% on 1m, 0.40% → 0.58% on 3m).

On performance, both hypotheses moved toward breakeven from opposite directions —
H1 from −0.42R to −0.13R per fill, H2 from +0.47R to +0.16R — and Fold C's overall
win rate landed on the breakeven line. **That is consistency, not confirmation of
an edge:** every interval, in both folds and both hypotheses, spans breakeven, and
the effective independent sample in Fold C is ten events.

There is **no material difference** between Fold C and A+B that would need
explaining. The one behaviour that changed in degree rather than kind is
clustering, which got worse (60.0% → 88.9% of fills in multi-fill clusters).

*What parameter should change* is out of scope and is not addressed anywhere in
this document.

**STOPPED.** No optimisation, no parameter changes, no strategy redesign, and no
further experiment.

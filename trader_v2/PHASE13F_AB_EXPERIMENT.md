# Phase 13F — controlled performance experiment, folds A and B

The frozen Phase 13C–13E hypothesis, run exactly as specified. **No parameter was
changed, nothing was optimised, no implementation change was made in response to
any result, and fold C was not run.** H1 (1m) and H2 (3m) are reported separately
throughout and are never pooled; 3m is never substituted for 1m.

Measurement additions since 13E: an LTF `time` field, per-trade ledger fields,
summary statistics, and two output tables. The strategy code is otherwise
identical — a diff against the 13E build shows only measurement lines plus one
refactor of `v = (flg >= 1 ? tgtR : -1.0) - cR` into `vPre`/`v`, which computes
the same number. All Phase 13E assertions (A21–A27, A32) read **0 in all 16 runs**.

---

## 1. Per-cell summary

16 cells: {MGC1!, MNQ1!} × {long, short} × {1m, 3m} × {fold A, fold B}. Cells with
zero trades are included.

| cell | fold bars | bars w/ LTF | sweeps | CHOCH | retests | BOS+disp | FVG | fills | distinct events | W | L(stop) | timeout | win% | loss% | R pre-drag | R post-drag | avg R | median R | max consec L | maxDD R | maxDD $ | expectancy | total $ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **MGC long 1m A** | 10,386 | 9,813 | 544 | 434 | 401 | 5 | 5 | **2** | 2 | 1 | 1 | 0 | 50% | 50% | +4 | +3.913 | +1.9565 | +1.9565 | 1 | 1.045 | 68.96 | +1.9565R | +288.57 |
| **MGC long 1m B** | 4,668 | 4,668 | 161 | 149 | 131 | 3 | 2 | **1** | 1 | 0 | 0 | 1 | 0% | 100% | -1 | -1.029 | -1.0290 | -1.0288 | 1 | 1.029 | 107.14 | -1.0290R | -107.14 |
| **MGC long 3m A** | 10,386 | 10,386 | 544 | 212 | 164 | 9 | 6 | **5** | 4 | 1 | 4 | 0 | 20% | 80% | +1 | +0.865 | +0.1730 | -1.0221 | 4 | 4.112 | 470.80 | +0.1730R | +164.21 |
| **MGC long 3m B** | 4,668 | 4,668 | 161 | 60 | 37 | 4 | 4 | **0** | 0 | 0 | 0 | 0 | — | — | +0 | +0.000 | — | — | 0 | 0.000 | 0.00 | — | +0.00 |
| **MGC short 1m A** | 10,386 | 9,813 | 432 | 385 | 352 | 6 | 6 | **2** | 1 | 1 | 1 | 0 | 50% | 50% | +4 | +3.879 | +1.9395 | +1.9395 | 1 | 1.054 | 59.06 | +1.9395R | +160.26 |
| **MGC short 1m B** | 4,668 | 4,668 | 226 | 200 | 180 | 5 | 5 | **2** | 1 | 1 | 1 | 0 | 50% | 50% | +4 | +3.402 | +1.7010 | +1.7010 | 1 | 1.203 | 17.80 | +1.7010R | +17.14 |
| **MGC short 3m A** | 10,386 | 10,386 | 432 | 176 | 139 | 12 | 8 | **1** | 1 | 0 | 1 | 0 | 0% | 100% | -1 | -1.022 | -1.0220 | -1.0217 | 1 | 1.022 | 141.42 | -1.0220R | -141.42 |
| **MGC short 3m B** | 4,668 | 4,668 | 226 | 77 | 64 | 7 | 4 | **0** | 0 | 0 | 0 | 0 | — | — | +0 | +0.000 | — | — | 0 | 0.000 | 0.00 | — | +0.00 |
| **MNQ long 1m A** | 10,368 | 9,812 | 468 | 396 | 366 | 18 | 11 | **2** | 2 | 0 | 2 | 0 | 0% | 100% | -2 | -2.055 | -1.0275 | -1.0276 | 2 | 2.055 | 231.36 | -1.0275R | -231.36 |
| **MNQ long 1m B** | 4,668 | 4,668 | 275 | 246 | 218 | 12 | 9 | **7** | 3 | 0 | 5 | 2 | 0% | 100% | -7 | -7.110 | -1.0157 | -1.0157 | 7 | 7.110 | 1,412.65 | -1.0157R | -1,412.65 |
| **MNQ long 3m A** | 10,368 | 10,368 | 468 | 191 | 136 | 11 | 5 | **1** | 1 | 0 | 1 | 0 | 0% | 100% | -1 | -1.008 | -1.0080 | -1.0077 | 1 | 1.008 | 391.04 | -1.0080R | -391.04 |
| **MNQ long 3m B** | 4,668 | 4,668 | 275 | 97 | 70 | 3 | 1 | **0** | 0 | 0 | 0 | 0 | — | — | +0 | +0.000 | — | — | 0 | 0.000 | 0.00 | — | +0.00 |
| **MNQ short 1m A** | 10,368 | 9,812 | 641 | 538 | 473 | 30 | 16 | **10** | 6 | 0 | 9 | 1 | 0% | 100% | -10 | -10.677 | -1.0677 | -1.0521 | 10 | 10.677 | 764.59 | -1.0677R | -764.59 |
| **MNQ short 1m B** | 4,668 | 4,668 | 230 | 199 | 174 | 3 | 3 | **2** | 2 | 0 | 2 | 0 | 0% | 100% | -2 | -2.075 | -1.0375 | -1.0374 | 2 | 2.075 | 199.89 | -1.0375R | -199.89 |
| **MNQ short 3m A** | 10,368 | 10,368 | 641 | 225 | 179 | 9 | 6 | **3** | 2 | 0 | 2 | 1 | 0% | 100% | -3 | -3.091 | -1.0303 | -1.0336 | 3 | 3.091 | 318.40 | -1.0303R | -318.40 |
| **MNQ short 3m B** | 4,668 | 4,668 | 230 | 91 | 62 | 2 | 2 | **2** | 1 | 2 | 0 | 0 | 100% | 0% | +10 | +9.943 | +4.9715 | +4.9716 | 0 | 0.000 | 0.00 | +4.9715R | +1,063.25 |

**40 fills in total across 16 cells. Eight cells have 2 or fewer; three have none.**

### The "distinct events" column, and why it is here

Deduplicating on (entry timestamp, entry price), the 40 fills are **27 distinct
market events** — 18 on 1m, 9 on 3m. Sweeps a few 5m bars apart run separate
sequences (one per sweep bar, per the 13E construction) which frequently converge
on the *same* CHOCH, the same BOS, the same FVG and the same entry price. They
differ only in the stop, because each carries its own sweep extreme.

Three consequences, all visible in the ledger below:

- **MNQ long 1m fold B: 7 fills, 3 events.** Trades 16–17 share one entry, 18–19
  another, 20–22 a third.
- **MGC short 1m fold A, trades 9 and 10: identical entry 4517.7, different stop
  → one loss, one win.** The stop decided the outcome, not the entry.
- **MNQ short 3m fold B — the only positive cell in H2 — is one market event
  counted twice** (trades 39 and 40, both entering at 29273.25 on 2026-07-22).

These are correlated observations, not independent trades. Every statistic below
is reported on the fill count as the frozen engine produced it, with the distinct
event count alongside so the effective sample is never overstated. **This is a
measurement property of the frozen construction, reported, not repaired.**

---

## 2. Individual trade ledger — all 40 fills

Format: `instrument|dir|LTF|fold|sweep time|sweep type|sweep extreme|CHOCH time|CHOCH level|retest time|BOS time|BOS level|FVG lo-hi|entry time|entry px|stop px|outcome|R after drag|$ after drag|exit reason|bars held`

```
 1. MGC1!|L|1m|A|sw 2026-06-26 12:20|SW|swX 4056.7|ch 2026-06-26 12:50|chL 4059.3|rt 2026-06-26 12:51|bos 2026-06-26 12:57|bosL 4061.2|fvg 4063-4068.5|en 2026-06-26 13:05|enPx 4063|stop 4055.7894|WIN|4.958R|$357.53|target|13bars
 2. MGC1!|L|1m|A|sw 2026-07-10 20:00|AS|swX 4116.4|ch 2026-07-10 20:21|chL 4120.7|rt 2026-07-10 20:22|bos 2026-07-10 20:53|bosL 4121.1|fvg 4122.4-4126.2|en 2026-07-12 22:00|enPx 4122.4|stop 4115.8039|LOSS|-1.045R|$-68.96|stop|1bars
 3. MGC1!|L|1m|B|sw 2026-08-04 10:45|SW|swX 4108.1|ch 2026-08-04 11:10|chL 4111.6|rt 2026-08-04 11:11|bos 2026-08-04 11:43|bosL 4120.7|fvg 4117.8-4119.6|en 2026-08-04 12:10|enPx 4117.8|stop 4107.3858|LOSS|-1.029R|$-107.14|timeout|144bars
 4. MGC1!|L|3m|A|sw 2026-05-28 04:50|PD|swX 4397.3|ch 2026-05-28 05:09|chL 4403.9|rt 2026-05-28 05:12|bos 2026-05-28 05:30|bosL 4406.4|fvg 4408.8-4412.6|en 2026-05-28 06:05|enPx 4408.8|stop 4396.0398|WIN|4.976R|$635.01|target|96bars
 5. MGC1!|L|3m|A|sw 2026-07-03 07:00|SW|swX 4184|ch 2026-07-03 07:48|chL 4193.6|rt 2026-07-03 07:51|bos 2026-07-03 08:00|bosL 4194.7|fvg 4190.4-4194.7|en 2026-07-03 08:45|enPx 4190.4|stop 4183.1142|LOSS|-1.041R|$-75.86|stop|9bars
 6. MGC1!|L|3m|A|sw 2026-07-13 00:40|PD|swX 4076.3|ch 2026-07-13 01:06|chL 4085.4|rt 2026-07-13 01:09|bos 2026-07-13 01:30|bosL 4090.9|fvg 4088.7-4090.8|en 2026-07-13 01:50|enPx 4088.7|stop 4075.0374|LOSS|-1.022R|$-139.63|stop|7bars
 7. MGC1!|L|3m|A|sw 2026-07-13 04:10|SW|swX 4060|ch 2026-07-13 04:57|chL 4065.5|rt 2026-07-13 05:00|bos 2026-07-13 05:06|bosL 4065.7|fvg 4070.4-4076.1|en 2026-07-13 05:20|enPx 4070.4|stop 4059.0571|LOSS|-1.026R|$-116.43|stop|8bars
 8. MGC1!|L|3m|A|sw 2026-07-13 04:15|SW|swX 4057.8|ch 2026-07-13 04:57|chL 4065.5|rt 2026-07-13 05:00|bos 2026-07-13 05:06|bosL 4065.7|fvg 4070.4-4076.1|en 2026-07-13 05:20|enPx 4070.4|stop 4056.8116|LOSS|-1.022R|$-138.88|stop|8bars
 9. MGC1!|S|1m|A|sw 2026-06-02 22:00|SW|swX 4522.8|ch 2026-06-02 22:25|chL 4517.4|rt 2026-06-02 22:26|bos 2026-06-02 22:45|bosL 4516.8|fvg 4516-4517.7|en 2026-06-02 22:50|enPx 4517.7|stop 4523.3057|LOSS|-1.054R|$-59.06|stop|22bars
10. MGC1!|S|1m|A|sw 2026-06-02 22:10|SW|swX 4521.6|ch 2026-06-02 22:25|chL 4517.4|rt 2026-06-02 22:26|bos 2026-06-02 22:45|bosL 4516.8|fvg 4516-4517.7|en 2026-06-02 22:50|enPx 4517.7|stop 4522.1464|WIN|4.933R|$219.32|target|6bars
11. MGC1!|S|1m|B|sw 2026-08-07 20:00|SW|swX 4404.6|ch 2026-08-07 20:27|chL 4397.3|rt 2026-08-07 20:28|bos 2026-08-09 22:02|bosL 4399|fvg 4398.7-4404|en 2026-08-09 22:10|enPx 4404|stop 4405.4802|LOSS|-1.203R|$-17.8|stop|10bars
12. MGC1!|S|1m|B|sw 2026-08-07 20:05|SW|swX 4403.9|ch 2026-08-07 20:27|chL 4397.3|rt 2026-08-07 20:28|bos 2026-08-09 22:02|bosL 4399|fvg 4398.7-4404|en 2026-08-09 22:10|enPx 4404|stop 4404.7588|WIN|4.605R|$34.94|target|1bars
13. MGC1!|S|3m|A|sw 2026-07-09 00:20|SW|swX 4094.7|ch 2026-07-09 00:51|chL 4083|rt 2026-07-09 00:54|bos 2026-07-09 01:00|bosL 4081.3|fvg 4081.2-4081.8|en 2026-07-09 01:10|enPx 4081.8|stop 4095.6418|LOSS|-1.022R|$-141.42|stop|58bars
14. MNQ1!|L|1m|A|sw 2026-06-25 11:30|SW|swX 30099|ch 2026-06-25 12:04|chL 30140.5|rt 2026-06-25 12:13|bos 2026-06-25 12:30|bosL 30145.75|fvg 30140.25-30204.75|en 2026-06-25 13:15|enPx 30140.25|stop 30094.4432|LOSS|-1.033R|$-94.61|stop|3bars
15. MNQ1!|L|1m|A|sw 2026-07-05 22:10|SW|swX 29875.5|ch 2026-07-05 22:20|chL 29923.5|rt 2026-07-05 22:21|bos 2026-07-05 23:12|bosL 29961|fvg 29937.75-29982|en 2026-07-06 00:00|enPx 29937.75|stop 29870.877|LOSS|-1.022R|$-136.75|stop|6bars
16. MNQ1!|L|1m|B|sw 2026-07-16 12:30|PD|swX 29386.75|ch 2026-07-16 12:52|chL 29401.25|rt 2026-07-16 12:55|bos 2026-07-16 13:30|bosL 29488.5|fvg 29471.5-29478.5|en 2026-07-16 13:35|enPx 29471.5|stop 29379.1022|LOSS|-1.016R|$-187.8|stop|1bars
17. MNQ1!|L|1m|B|sw 2026-07-16 12:50|PD|swX 29383.5|ch 2026-07-16 13:07|chL 29437.25|rt 2026-07-16 13:08|bos 2026-07-16 13:30|bosL 29488.5|fvg 29471.5-29478.5|en 2026-07-16 13:35|enPx 29471.5|stop 29375.9721|LOSS|-1.016R|$-194.06|stop|1bars
18. MNQ1!|L|1m|B|sw 2026-07-17 20:00|AS|swX 28712.5|ch 2026-07-17 20:20|chL 28748.75|rt 2026-07-17 20:21|bos 2026-07-19 22:00|bosL 28770.75|fvg 28779-28791.5|en 2026-07-19 22:05|enPx 28779|stop 28701.9267|LOSS|-1.019R|$-157.15|timeout|144bars
19. MNQ1!|L|1m|B|sw 2026-07-17 20:10|AS|swX 28716|ch 2026-07-17 20:30|chL 28754.75|rt 2026-07-17 20:32|bos 2026-07-19 22:00|bosL 28770.75|fvg 28779-28791.5|en 2026-07-19 22:05|enPx 28779|stop 28706.097|LOSS|-1.021R|$-148.81|timeout|144bars
20. MNQ1!|L|1m|B|sw 2026-07-29 17:00|PD+AS|swX 27595|ch 2026-07-29 17:21|chL 27740|rt 2026-07-29 17:22|bos 2026-07-29 18:00|bosL 27728|fvg 27727.25-27808.25|en 2026-07-29 18:30|enPx 27727.25|stop 27583.2054|LOSS|-1.01R|$-291.09|stop|12bars
21. MNQ1!|L|1m|B|sw 2026-07-29 17:05|AS|swX 27634.25|ch 2026-07-29 17:21|chL 27740|rt 2026-07-29 17:22|bos 2026-07-29 18:00|bosL 27728|fvg 27727.25-27808.25|en 2026-07-29 18:30|enPx 27727.25|stop 27622.8943|LOSS|-1.014R|$-211.71|stop|12bars
22. MNQ1!|L|1m|B|sw 2026-07-29 17:30|AS|swX 27629.25|ch 2026-07-29 17:49|chL 27690.5|rt 2026-07-29 17:56|bos 2026-07-29 18:00|bosL 27728|fvg 27727.25-27808.25|en 2026-07-29 18:30|enPx 27727.25|stop 27617.7288|LOSS|-1.014R|$-222.04|stop|12bars
23. MNQ1!|L|3m|A|sw 2026-06-10 13:05|AS|swX 28822|ch 2026-06-10 13:36|chL 28890|rt 2026-06-10 13:39|bos 2026-06-10 13:42|bosL 28991.5|fvg 29002.25-29019.25|en 2026-06-10 13:50|enPx 29002.25|stop 28808.2282|LOSS|-1.008R|$-391.04|stop|16bars
24. MNQ1!|S|1m|A|sw 2026-05-29 17:45|AS|swX 30355.5|ch 2026-05-29 17:54|chL 30334|rt 2026-05-29 18:05|bos 2026-05-29 18:45|bosL 30367|fvg 30352-30380.25|en 2026-05-29 19:25|enPx 30380.25|stop 30361.5423|LOSS|-1.08R|$-40.42|stop|1bars
25. MNQ1!|S|1m|A|sw 2026-05-29 20:05|SW|swX 30410.25|ch 2026-05-29 20:40|chL 30383.25|rt 2026-05-29 20:44|bos 2026-05-31 22:02|bosL 30380.75|fvg 30381-30398.5|en 2026-05-31 22:10|enPx 30398.5|stop 30415.7992|LOSS|-1.087R|$-37.6|stop|1bars
26. MNQ1!|S|1m|A|sw 2026-06-03 04:10|SW|swX 30730.5|ch 2026-06-03 04:46|chL 30715.25|rt 2026-06-03 04:47|bos 2026-06-03 05:00|bosL 30701.75|fvg 30693.25-30701.5|en 2026-06-03 05:05|enPx 30701.5|stop 30733.1726|LOSS|-1.047R|$-66.35|stop|25bars
27. MNQ1!|S|1m|A|sw 2026-06-03 04:15|SW|swX 30727.75|ch 2026-06-03 04:46|chL 30715.25|rt 2026-06-03 04:47|bos 2026-06-03 05:00|bosL 30701.75|fvg 30693.25-30701.5|en 2026-06-03 05:05|enPx 30701.5|stop 30730.4496|LOSS|-1.052R|$-60.9|stop|25bars
28. MNQ1!|S|1m|A|sw 2026-06-17 12:30|SW|swX 30503.25|ch 2026-06-17 12:57|chL 30494.5|rt 2026-06-17 12:58|bos 2026-06-17 13:30|bosL 30488.75|fvg 30487.25-30497.25|en 2026-06-17 13:40|enPx 30497.25|stop 30508.2128|LOSS|-1.137R|$-24.93|stop|1bars
29. MNQ1!|S|1m|A|sw 2026-06-17 12:35|SW|swX 30520.75|ch 2026-06-17 12:57|chL 30494.5|rt 2026-06-17 12:58|bos 2026-06-17 13:30|bosL 30488.75|fvg 30487.25-30497.25|en 2026-06-17 13:40|enPx 30497.25|stop 30525.869|LOSS|-1.052R|$-60.24|stop|1bars
30. MNQ1!|S|1m|A|sw 2026-06-17 12:55|SW|swX 30503.25|ch 2026-06-17 13:06|chL 30475|rt 2026-06-17 13:07|bos 2026-06-17 13:30|bosL 30488.75|fvg 30487.25-30497.25|en 2026-06-17 13:40|enPx 30497.25|stop 30508.2084|LOSS|-1.137R|$-24.92|stop|1bars
31. MNQ1!|S|1m|A|sw 2026-06-17 13:45|SW|swX 30540.75|ch 2026-06-17 13:56|chL 30426.5|rt 2026-06-17 14:08|bos 2026-06-17 14:47|bosL 30373.75|fvg 30381.75-30423.75|en 2026-06-17 14:50|enPx 30423.75|stop 30549.6618|LOSS|-1.012R|$-254.82|timeout|144bars
32. MNQ1!|S|1m|A|sw 2026-07-10 13:35|SW|swX 29937|ch 2026-07-10 14:19|chL 29906|rt 2026-07-10 14:20|bos 2026-07-10 14:32|bosL 29845.5|fvg 29835-29913.75|en 2026-07-10 15:15|enPx 29913.75|stop 29944.3208|LOSS|-1.049R|$-64.14|stop|1bars
33. MNQ1!|S|1m|A|sw 2026-07-10 13:50|AS|swX 29968.5|ch 2026-07-10 14:19|chL 29906|rt 2026-07-10 14:20|bos 2026-07-10 14:32|bosL 29845.5|fvg 29835-29913.75|en 2026-07-10 15:15|enPx 29913.75|stop 29977.3944|LOSS|-1.024R|$-130.29|stop|2bars
34. MNQ1!|S|1m|B|sw 2026-07-20 11:20|SW|swX 29008.25|ch 2026-07-20 11:47|chL 29075.5|rt 2026-07-20 11:52|bos 2026-07-20 12:02|bosL 29048.25|fvg 29006.25-29041|en 2026-07-20 12:30|enPx 29041|stop 29012.7084|LOSS|-1.053R|$-59.58|stop|12bars
35. MNQ1!|S|1m|B|sw 2026-07-31 20:00|PD|swX 28436|ch 2026-07-31 20:30|chL 28364.25|rt 2026-07-31 20:31|bos 2026-07-31 20:53|bosL 28378|fvg 28349.5-28377|en 2026-08-02 22:00|enPx 28377|stop 28445.651|LOSS|-1.022R|$-140.3|stop|1bars
36. MNQ1!|S|3m|A|sw 2026-06-03 12:45|AS|swX 30733.75|ch 2026-06-03 13:33|chL 30699.25|rt 2026-06-03 13:36|bos 2026-06-03 13:42|bosL 30703.75|fvg 30649.25-30694|en 2026-06-03 14:15|enPx 30694|stop 30737.5999|LOSS|-1.034R|$-90.2|stop|5bars
37. MNQ1!|S|3m|A|sw 2026-06-03 12:50|AS|swX 30734.75|ch 2026-06-03 13:33|chL 30699.25|rt 2026-06-03 13:36|bos 2026-06-03 13:42|bosL 30703.75|fvg 30649.25-30694|en 2026-06-03 14:15|enPx 30694|stop 30738.6571|LOSS|-1.034R|$-92.31|stop|5bars
38. MNQ1!|S|3m|A|sw 2026-07-05 23:40|SW|swX 29989.25|ch 2026-07-06 00:00|chL 29963.5|rt 2026-07-06 00:06|bos 2026-07-06 00:27|bosL 29900.25|fvg 29908.75-29928|en 2026-07-06 00:35|enPx 29928|stop 29994.4412|LOSS|-1.023R|$-135.88|timeout|144bars
39. MNQ1!|S|3m|B|sw 2026-07-22 00:20|SW|swX 29327.75|ch 2026-07-22 00:45|chL 29272|rt 2026-07-22 00:48|bos 2026-07-22 01:00|bosL 29258.5|fvg 29249-29273.25|en 2026-07-22 01:45|enPx 29273.25|stop 29332.1834|WIN|4.975R|$586.33|target|134bars
40. MNQ1!|S|3m|B|sw 2026-07-22 00:25|SW|swX 29316.75|ch 2026-07-22 00:45|chL 29272|rt 2026-07-22 00:48|bos 2026-07-22 01:00|bosL 29258.5|fvg 29249-29273.25|en 2026-07-22 01:45|enPx 29273.25|stop 29321.2418|WIN|4.969R|$476.92|target|71bars
```

Two ledger observations that are facts about the frozen rules, recorded without
adjustment:

1. **`dispWait = 12` is 12 chart bars, not 60 wall-clock minutes.** Trades 11–12
   sweep on Friday 2026-08-07 20:05 and reach BOS on Sunday 2026-08-09 22:02;
   trades 18–19 sweep Friday 07-17 and BOS Sunday 07-19. Twelve 5m bars span the
   weekend session gap. My Phase 13D phrasing ("60 minutes") holds only inside a
   continuous session. The frozen rule is a bar count and was applied as such.
2. **Fold-B sequences resolve on bars after the B/C boundary.** Trades 11–12 enter
   2026-08-09 22:10, past `FC = 2026-08-09 00:00`. Outcome resolution for a
   fold-B-armed sequence necessarily reads later bars — this was equally true of
   every V44–V52 fold run. **No fold C run was performed and no fold C statistic
   was inspected.**

---

## 3. Funnel conversion

Counts and percentages, folds A+B pooled within each hypothesis.

| step | H1 (1m) count | H1 % | H2 (3m) count | H2 % |
|---|---|---|---|---|
| sweeps | 2,977 | — | 2,977 | — |
| sweep → CHOCH | 2,547 | 85.6% | 1,129 | 37.9% |
| CHOCH → CHOCH retest | 2,295 | 90.1% | 851 | 75.4% |
| retest → BOS + displacement | 82 | **3.57%** | 57 | **6.70%** |
| BOS → FVG exists | 57 | 69.5% | 36 | 63.2% |
| FVG → fill | 28 | 49.1% | 12 | 33.3% |
| **sweep → fill** | **28** | **0.94%** | **12** | **0.40%** |

By fold:

| | sweeps | CHOCH | retest | BOS+disp | FVG | fills | sweep→fill |
|---|---|---|---|---|---|---|---|
| 1m fold A | 2,085 | 1,753 (84.1%) | 1,592 (90.8%) | 59 (3.71%) | 38 (64.4%) | 16 | 0.77% |
| 1m fold B | 892 | 794 (89.0%) | 703 (88.5%) | 23 (3.27%) | 19 (82.6%) | 12 | 1.35% |
| 3m fold A | 2,085 | 804 (38.6%) | 618 (76.9%) | 41 (6.63%) | 25 (61.0%) | 10 | 0.48% |
| 3m fold B | 892 | 325 (36.4%) | 233 (71.7%) | 16 (6.87%) | 11 (68.8%) | 2 | 0.22% |

The retest → BOS+displacement step removes **96.4%** of surviving sequences on 1m
and **93.3%** on 3m. Structural breaks that passed the BOS test and failed the §7
displacement condition: **13,365 on 1m, 1,109 on 3m**.

**These conversion rates are not treated as a reason to change any threshold.**
They are reported as the frequency the frozen specification produces.

---

## 4. H1 versus H2 — descriptive comparison

Neither is declared better. Total P&L in particular is not used to rank them.

| | H1 (1m) | H2 (3m) |
|---|---|---|
| **sample size** | 28 fills / **18 distinct events** | 12 fills / **9 distinct events** |
| cells with 0 fills | 0 of 8 | 3 of 8 |
| **conversion** sweep→fill | 0.94% | 0.40% |
| conversion sweep→CHOCH | 85.6% | 37.9% |
| conversion retest→BOS+disp | 3.57% | 6.70% |
| wins | 3 / 28 = 10.7% | 3 / 12 = 25.0% |
| **expectancy per fill** | **−0.42R** | **+0.47R** |
| total R after drag | −11.75 | +5.69 |
| total $ after drag | −$2,249.66 | +$376.60 |
| **dispersion** (sd of R) | ≈1.89 | ≈2.71 |
| median R | −1.02 to −1.04 in every cell with a loss | same |
| **fold consistency** | A −0.31R, B −0.57R — both negative | A −0.43R, **B +4.97R** |
| **directional consistency** | long −0.52R, short −0.34R — both negative | long −0.02R, short +0.97R |
| **instrument consistency** | MGC **+1.45R** (7 fills), MNQ **−1.04R** (21 fills) | MGC −0.03R (6), MNQ +0.97R (6) |

Three things are worth stating plainly:

- **H2's entire positive result is one market event.** Remove MNQ short 3m fold B
  — two fills of the same entry at 29273.25 — and H2 becomes 10 fills, 1 win,
  −4.256R, **−0.43R per fill**, statistically indistinguishable from H1.
- **H1's positive cells are MGC only, and they are pairs.** MGC contributes 3 of
  H1's 3 wins across 7 fills; MNQ contributes 0 wins in 21 fills. Two of those
  three MGC wins are the *winning half* of a duplicate pair whose other half lost.
- **The two LTFs fail in different places, as 13E predicted.** 1m generates
  abundant structure (85.6% of sweeps reach a CHOCH) and almost no displacement;
  3m reaches displacement about twice as readily but loses 62% of sweeps before a
  CHOCH exists, because `swLen = 3` on 3m consumes 7 of the 20 available bars
  confirming the first pivot.

**Every one of these comparisons is sample-limited.** No cell has enough fills to
separate any of these differences from noise.

---

## 5. Statistical caution

| | wins/fills | win rate | 90% Wilson CI | breakeven at 5R/−1R |
|---|---|---|---|---|
| H1 (1m) | 3 / 28 | 10.7% | [4.4%, 24.0%] | 16.7% |
| H2 (3m) | 3 / 12 | 25.0% | [10.5%, 48.7%] | 16.7% |
| H2 minus the single MNQ-short-B event | 1 / 10 | 10.0% | [2.3%, 34.8%] | 16.7% |

| | mean R | sd | t | 90% CI on mean R |
|---|---|---|---|---|
| H1 (1m) | −0.387 | 1.89 | −1.08 | [−0.98, +0.20] |
| H2 (3m) | +0.470 | 2.71 | +0.60 | [−0.82, +1.76] |
| H2 ex-that-event | −0.430 | 1.90 | −0.72 | [−1.42, +0.56] |

**Every interval spans breakeven in both directions.** Neither hypothesis is shown
to be profitable and neither is shown to be unprofitable. At n = 28 and sd ≈ 2.0
the 90% CI half-width is **0.62R**: any true effect smaller than that is invisible
here. Detecting a 0.10R edge to that precision would need roughly **1,082 trades**;
the frozen specification produced 40 in ten and a half weeks across four
instrument × direction cells.

Cells with 1–12 trades are exactly that, and are labelled so in §1. Three cells
produced **zero** trades and no statistic can be computed for them.

The median R of −1.02 to −1.04 in every cell containing a loss is **not a finding**
— it is arithmetic. With a fixed +5R / −1R payoff the median is the loss value at
any win rate below 50%, as established earlier in this project.

**Read this result as:** descriptive evidence about what the frozen hypothesis
does; evidence about the hypothesis's *frequency*, which is measured precisely and
is very low; and validation that the implementation runs end to end and causally.
**Not** as evidence for or against an edge.

---

## 6. Coverage report

| | 1m | 3m |
|---|---|---|
| fold A bars (MGC / MNQ) | 10,386 / 10,368 | same |
| of which carrying LTF data | **9,813 / 9,812 (94.5%)** | **10,386 / 10,368 (100%)** |
| fold A covered interval | **2026-05-27 02:15 → 2026-07-15 23:55** (MNQ 02:20) | **2026-05-24 22:00 → 2026-07-15 23:55** |
| fold B bars | 4,668 | 4,668 |
| of which carrying LTF data | **4,668 (100%)** | **4,668 (100%)** |
| fold B covered interval | **2026-07-16 00:00 → 2026-08-07 20:55** | same |

Fold A on 1m begins **2026-05-27 02:15**, 2.2 days after the 5m chart's own history
starts, because the 100,000-value window reaches no further. That interval is what
was evaluated; the uncovered 573 bars were not filled, estimated, or substituted
with 3m data. Fold B is fully covered on both.

Fold B's last covered bar is 2026-08-07 20:55 rather than the 08-09 boundary
because 08-08/08-09 is a weekend.

---

## 7. Status

Per-cell summary, full 40-row ledger, funnel, H1/H2 comparison and coverage report
are complete. **Fold C was not run and remains sealed.**

The frozen hypothesis produced, on folds A and B, 40 fills across 16 cells — 27
distinct market events — with H1 at −0.42R per fill and H2 at +0.47R per fill,
both with confidence intervals spanning breakeven, and H2's sign resting entirely
on one event. No strategy change was made, no parameter was adjusted, and no
diagnosis of which parameter "should" be different appears anywhere in this
document.

**STOPPED.** No further tests run.

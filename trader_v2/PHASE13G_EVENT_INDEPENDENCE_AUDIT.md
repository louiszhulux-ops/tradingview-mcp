# Phase 13G — event independence / clustering audit

Audit only. **No strategy rule, parameter, implementation line or historical
result was changed. Fold C was not run.** V53 was not re-run; every number below
is computed from the Phase 13F ledger already committed in `trader_v2/v53_runs/`,
by `trader_v2/g_cluster.py`, whose full output is preserved at
`trader_v2/v53_runs/PHASE13G_raw_output.txt`.

None of the hard-stop conditions was triggered: the implementation corresponds to
Phase 13F, the control totals reproduce, both clustering identities are
deterministic, no frozen rule prohibits the convergent sequences, and nothing here
requires a rule change.

---

## 1. Executive conclusion

**The convergent sequences are legitimate trades under the frozen specification.**
Nothing in §1–§15, F1–F6, M5 or the V53 implementation restricts the number of
live sequences, prevents independently armed sequences from resolving into the
same CHOCH/BOS/FVG, or deduplicates them. Each carries its own sweep-derived stop
because §14/F5 defines the stop from *that sequence's own* sweep extreme. So the
**40 fills stand as the execution-level result** and are not replaced by 27.

**But the effective independent sample is materially smaller than 40.** Under the
looser identity, **24 of 40 fills (60%) sit in 11 multi-fill clusters**, the
largest containing 3. On 1m that rises to **64.3%**; the execution-level N of 28
corresponds to **18 market events**. And the single positive cell in H2 is **one
market event counted twice**.

One correction to a Phase 13F statement: the **primary** identity the brief
specifies produces **31 clusters, not 27**. The 27 reported in 13F corresponds to
the **alternative** identity. Both are reported below; neither was selected on the
strength of its result.

---

## 2. Confirmation of the Phase 13F control totals

    SECTION 9 -- PHASE 13F CONTROL REPRODUCTION
    ====================================================================================================
    H1 (1m)    fills  28 (exp  28)  wins 3 (exp 3)  losses 25 (exp 25)  R  -11.752 (exp  -11.752)  $ -2249.68   MATCH
    H2 (3m)    fills  12 (exp  12)  wins 3 (exp 3)  losses  9 (exp  9)  R   +5.688 (exp   +5.687)  $  +376.61   MATCH
    TOTAL      fills  40 (exp  40)  wins 6 (exp 6)  losses 34 (exp 34)  R   -6.064 (exp   -6.065)  $ -1873.07   MATCH
    
    CONTROL REPRODUCTION: PASS -- all three totals match Phase 13F exactly

**PASS.** Fill counts, win counts and loss counts match exactly. The R totals
differ in the third decimal (−6.064 vs −6.065) because the ledger stores each R to
three decimal places while Phase 13F's figures came from Pine's full-precision
accumulators; the discrepancy is 0.001R across 40 rounded values and is arithmetic,
not a data difference. Dollar totals differ by $0.02 for the same reason.

---

## 3. Number of unique market events

| identity | clusters | multi-fill clusters | fills in them | largest cluster |
|---|---|---|---|---|
| **Primary** (inst, dir, LTF, CHOCH ts+level, BOS ts+level, entry ts, entry px) | **31** | 9 | 18 (45.0%) | 2 |
| **Alternative** (inst, dir, LTF, BOS ts+level, entry ts, entry px) | **27** | 11 | 24 (60.0%) | 3 |
| *Phase 13F as published* (inst, dir, LTF, fold, entry ts, entry px) | 27 | 11 | 24 (60.0%) | 3 |

**The primary identity does NOT reproduce the 27 events reported in Phase 13F — it
gives 31.** The alternative identity reproduces 27 exactly, and is identical in
partition to what 13F actually computed.

---

## 4. Primary clustering methodology

`(instrument, direction, LTF, CHOCH timestamp, CHOCH level, BOS timestamp, BOS
level, entry timestamp, entry price)`. Every component is a recorded ledger field;
no derived or estimated quantity enters. Re-running the partition yields an
identical result — **the identity is deterministic**.

Because it includes the CHOCH, two sequences that reached the *same* BOS, FVG and
entry via *different* CHOCH references are counted as two events.

## 5. Alternative clustering methodology

The same, with the CHOCH pair removed. It treats the downstream market event
(which BOS, which FVG, which entry) as the identity and is indifferent to how each
sequence arrived there. Also deterministic.

### Why the two differ: 31 − 27 = 4 clusters that split

Four alternative-identity clusters contain more than one distinct CHOCH, and each
splits into two primary clusters (27 − 4 + 8 = 31):

    Alt cluster MNQ1! L 1m B BOS 2026-07-16 13:30 @ 29488.5 entry 2026-07-16 13:35 @ 29471.5  -> 2 fills, 2 distinct CHOCH:
        sweep 2026-07-16 12:30 (PD, extreme 29386.75)  CHOCH 2026-07-16 12:52 @ 29401.25  stop 29379.1022  LOSS -1.016R
        sweep 2026-07-16 12:50 (PD, extreme 29383.5)  CHOCH 2026-07-16 13:07 @ 29437.25  stop 29375.9721  LOSS -1.016R
    
    Alt cluster MNQ1! L 1m B BOS 2026-07-19 22:00 @ 28770.75 entry 2026-07-19 22:05 @ 28779.0  -> 2 fills, 2 distinct CHOCH:
        sweep 2026-07-17 20:00 (AS, extreme 28712.5)  CHOCH 2026-07-17 20:20 @ 28748.75  stop 28701.9267  LOSS -1.019R
        sweep 2026-07-17 20:10 (AS, extreme 28716.0)  CHOCH 2026-07-17 20:30 @ 28754.75  stop 28706.097  LOSS -1.021R
    
    Alt cluster MNQ1! L 1m B BOS 2026-07-29 18:00 @ 27728.0 entry 2026-07-29 18:30 @ 27727.25  -> 3 fills, 2 distinct CHOCH:
        sweep 2026-07-29 17:30 (AS, extreme 27629.25)  CHOCH 2026-07-29 17:49 @ 27690.5  stop 27617.7288  LOSS -1.014R
        sweep 2026-07-29 17:00 (PD+AS, extreme 27595.0)  CHOCH 2026-07-29 17:21 @ 27740.0  stop 27583.2054  LOSS -1.010R
        sweep 2026-07-29 17:05 (AS, extreme 27634.25)  CHOCH 2026-07-29 17:21 @ 27740.0  stop 27622.8943  LOSS -1.014R
    
    Alt cluster MNQ1! S 1m A BOS 2026-06-17 13:30 @ 30488.75 entry 2026-06-17 13:40 @ 30497.25  -> 3 fills, 2 distinct CHOCH:
        sweep 2026-06-17 12:30 (SW, extreme 30503.25)  CHOCH 2026-06-17 12:57 @ 30494.5  stop 30508.2128  LOSS -1.137R
        sweep 2026-06-17 12:35 (SW, extreme 30520.75)  CHOCH 2026-06-17 12:57 @ 30494.5  stop 30525.869  LOSS -1.052R
        sweep 2026-06-17 12:55 (SW, extreme 30503.25)  CHOCH 2026-06-17 13:06 @ 30475.0  stop 30508.2084  LOSS -1.137R
    
    4 alternative-identity clusters contain more than one distinct CHOCH; they split into 8 primary clusters, which is the entire 31 vs 27 difference.

Mechanically this happens because the CHOCH reference is the *most recent
confirmed opposing pivot whose pivot bar is after that sequence's own sweep bar*
(F1). Two sweeps 5–30 minutes apart have different eligibility windows, so they
can latch different pivots and still be carried into the same BOS. **Neither
identity is "correct"** — the primary is stricter about provenance, the
alternative about market outcome. Both are reported; the choice is the reader's.

---

## 6. Full cluster table

Alternative identity, all 27 clusters, every constituent fill with its own sweep,
stop, outcome, R and post-drag dollars.

```
C01  MGC1! LONG 1m fold A  | fills 1
     CHOCH 2026-06-26 12:50 @ 4059.3
     BOS   2026-06-26 12:57 @ 4061.2   FVG 4063-4068.5   entry 2026-06-26 13:05 @ 4063.0
       sweep 2026-06-26 12:20 [SW] extreme 4056.7     stop 4055.7894    WIN    +4.958R  $  +357.53  target    13 bars

C02  MGC1! LONG 1m fold A  | fills 1
     CHOCH 2026-07-10 20:21 @ 4120.7
     BOS   2026-07-10 20:53 @ 4121.1   FVG 4122.4-4126.2   entry 2026-07-12 22:00 @ 4122.4
       sweep 2026-07-10 20:00 [AS] extreme 4116.4     stop 4115.8039    LOSS   -1.045R  $   -68.96  stop       1 bars

C03  MGC1! LONG 1m fold B  | fills 1
     CHOCH 2026-08-04 11:10 @ 4111.6
     BOS   2026-08-04 11:43 @ 4120.7   FVG 4117.8-4119.6   entry 2026-08-04 12:10 @ 4117.8
       sweep 2026-08-04 10:45 [SW] extreme 4108.1     stop 4107.3858    LOSS   -1.029R  $  -107.14  timeout  144 bars

C04  MGC1! LONG 3m fold A  | fills 1
     CHOCH 2026-05-28 05:09 @ 4403.9
     BOS   2026-05-28 05:30 @ 4406.4   FVG 4408.8-4412.6   entry 2026-05-28 06:05 @ 4408.8
       sweep 2026-05-28 04:50 [PD] extreme 4397.3     stop 4396.0398    WIN    +4.976R  $  +635.01  target    96 bars

C05  MGC1! LONG 3m fold A  | fills 1
     CHOCH 2026-07-03 07:48 @ 4193.6
     BOS   2026-07-03 08:00 @ 4194.7   FVG 4190.4-4194.7   entry 2026-07-03 08:45 @ 4190.4
       sweep 2026-07-03 07:00 [SW] extreme 4184.0     stop 4183.1142    LOSS   -1.041R  $   -75.86  stop       9 bars

C06  MGC1! LONG 3m fold A  | fills 1
     CHOCH 2026-07-13 01:06 @ 4085.4
     BOS   2026-07-13 01:30 @ 4090.9   FVG 4088.7-4090.8   entry 2026-07-13 01:50 @ 4088.7
       sweep 2026-07-13 00:40 [PD] extreme 4076.3     stop 4075.0374    LOSS   -1.022R  $  -139.63  stop       7 bars

C07  MGC1! LONG 3m fold A  | fills 2
     CHOCH 2026-07-13 04:57 @ 4065.5
     BOS   2026-07-13 05:06 @ 4065.7   FVG 4070.4-4076.1   entry 2026-07-13 05:20 @ 4070.4
       sweep 2026-07-13 04:10 [SW] extreme 4060.0     stop 4059.0571    LOSS   -1.026R  $  -116.43  stop       8 bars
       sweep 2026-07-13 04:15 [SW] extreme 4057.8     stop 4056.8116    LOSS   -1.022R  $  -138.88  stop       8 bars
       -> sum  -2.048R | mean  -1.024R | best  -1.022R | worst  -1.026R | $  -255.31

C08  MGC1! SHORT 1m fold A  | fills 2
     CHOCH 2026-06-02 22:25 @ 4517.4
     BOS   2026-06-02 22:45 @ 4516.8   FVG 4516-4517.7   entry 2026-06-02 22:50 @ 4517.7
       sweep 2026-06-02 22:10 [SW] extreme 4521.6     stop 4522.1464    WIN    +4.933R  $  +219.32  target     6 bars
       sweep 2026-06-02 22:00 [SW] extreme 4522.8     stop 4523.3057    LOSS   -1.054R  $   -59.06  stop      22 bars
       -> sum  +3.879R | mean  +1.939R | best  +4.933R | worst  -1.054R | $  +160.26

C09  MGC1! SHORT 1m fold B  | fills 2
     CHOCH 2026-08-07 20:27 @ 4397.3
     BOS   2026-08-09 22:02 @ 4399.0   FVG 4398.7-4404   entry 2026-08-09 22:10 @ 4404.0
       sweep 2026-08-07 20:05 [SW] extreme 4403.9     stop 4404.7588    WIN    +4.605R  $   +34.94  target     1 bars
       sweep 2026-08-07 20:00 [SW] extreme 4404.6     stop 4405.4802    LOSS   -1.203R  $   -17.80  stop      10 bars
       -> sum  +3.402R | mean  +1.701R | best  +4.605R | worst  -1.203R | $   +17.14

C10  MGC1! SHORT 3m fold A  | fills 1
     CHOCH 2026-07-09 00:51 @ 4083.0
     BOS   2026-07-09 01:00 @ 4081.3   FVG 4081.2-4081.8   entry 2026-07-09 01:10 @ 4081.8
       sweep 2026-07-09 00:20 [SW] extreme 4094.7     stop 4095.6418    LOSS   -1.022R  $  -141.42  stop      58 bars

C11  MNQ1! LONG 1m fold A  | fills 1
     CHOCH 2026-06-25 12:04 @ 30140.5
     BOS   2026-06-25 12:30 @ 30145.75   FVG 30140.25-30204.75   entry 2026-06-25 13:15 @ 30140.25
       sweep 2026-06-25 11:30 [SW] extreme 30099.0    stop 30094.4432   LOSS   -1.033R  $   -94.61  stop       3 bars

C12  MNQ1! LONG 1m fold A  | fills 1
     CHOCH 2026-07-05 22:20 @ 29923.5
     BOS   2026-07-05 23:12 @ 29961.0   FVG 29937.75-29982   entry 2026-07-06 00:00 @ 29937.75
       sweep 2026-07-05 22:10 [SW] extreme 29875.5    stop 29870.877    LOSS   -1.022R  $  -136.75  stop       6 bars

C13  MNQ1! LONG 1m fold B  | fills 2
     CHOCH 2026-07-16 12:52 @ 29401.25; 2026-07-16 13:07 @ 29437.25
     BOS   2026-07-16 13:30 @ 29488.5   FVG 29471.5-29478.5   entry 2026-07-16 13:35 @ 29471.5
       sweep 2026-07-16 12:30 [PD] extreme 29386.75   stop 29379.1022   LOSS   -1.016R  $  -187.80  stop       1 bars
       sweep 2026-07-16 12:50 [PD] extreme 29383.5    stop 29375.9721   LOSS   -1.016R  $  -194.06  stop       1 bars
       -> sum  -2.032R | mean  -1.016R | best  -1.016R | worst  -1.016R | $  -381.86

C14  MNQ1! LONG 1m fold B  | fills 2
     CHOCH 2026-07-17 20:20 @ 28748.75; 2026-07-17 20:30 @ 28754.75
     BOS   2026-07-19 22:00 @ 28770.75   FVG 28779-28791.5   entry 2026-07-19 22:05 @ 28779.0
       sweep 2026-07-17 20:00 [AS] extreme 28712.5    stop 28701.9267   LOSS   -1.019R  $  -157.15  timeout  144 bars
       sweep 2026-07-17 20:10 [AS] extreme 28716.0    stop 28706.097    LOSS   -1.021R  $  -148.81  timeout  144 bars
       -> sum  -2.040R | mean  -1.020R | best  -1.019R | worst  -1.021R | $  -305.96

C15  MNQ1! LONG 1m fold B  | fills 3
     CHOCH 2026-07-29 17:21 @ 27740.0; 2026-07-29 17:49 @ 27690.5
     BOS   2026-07-29 18:00 @ 27728.0   FVG 27727.25-27808.25   entry 2026-07-29 18:30 @ 27727.25
       sweep 2026-07-29 17:30 [AS] extreme 27629.25   stop 27617.7288   LOSS   -1.014R  $  -222.04  stop      12 bars
       sweep 2026-07-29 17:00 [PD+AS] extreme 27595.0    stop 27583.2054   LOSS   -1.010R  $  -291.09  stop      12 bars
       sweep 2026-07-29 17:05 [AS] extreme 27634.25   stop 27622.8943   LOSS   -1.014R  $  -211.71  stop      12 bars
       -> sum  -3.038R | mean  -1.013R | best  -1.010R | worst  -1.014R | $  -724.84

C16  MNQ1! LONG 3m fold A  | fills 1
     CHOCH 2026-06-10 13:36 @ 28890.0
     BOS   2026-06-10 13:42 @ 28991.5   FVG 29002.25-29019.25   entry 2026-06-10 13:50 @ 29002.25
       sweep 2026-06-10 13:05 [AS] extreme 28822.0    stop 28808.2282   LOSS   -1.008R  $  -391.04  stop      16 bars

C17  MNQ1! SHORT 1m fold A  | fills 1
     CHOCH 2026-05-29 17:54 @ 30334.0
     BOS   2026-05-29 18:45 @ 30367.0   FVG 30352-30380.25   entry 2026-05-29 19:25 @ 30380.25
       sweep 2026-05-29 17:45 [AS] extreme 30355.5    stop 30361.5423   LOSS   -1.080R  $   -40.42  stop       1 bars

C18  MNQ1! SHORT 1m fold A  | fills 1
     CHOCH 2026-05-29 20:40 @ 30383.25
     BOS   2026-05-31 22:02 @ 30380.75   FVG 30381-30398.5   entry 2026-05-31 22:10 @ 30398.5
       sweep 2026-05-29 20:05 [SW] extreme 30410.25   stop 30415.7992   LOSS   -1.087R  $   -37.60  stop       1 bars

C19  MNQ1! SHORT 1m fold A  | fills 2
     CHOCH 2026-06-03 04:46 @ 30715.25
     BOS   2026-06-03 05:00 @ 30701.75   FVG 30693.25-30701.5   entry 2026-06-03 05:05 @ 30701.5
       sweep 2026-06-03 04:10 [SW] extreme 30730.5    stop 30733.1726   LOSS   -1.047R  $   -66.35  stop      25 bars
       sweep 2026-06-03 04:15 [SW] extreme 30727.75   stop 30730.4496   LOSS   -1.052R  $   -60.90  stop      25 bars
       -> sum  -2.099R | mean  -1.050R | best  -1.047R | worst  -1.052R | $  -127.25

C20  MNQ1! SHORT 1m fold A  | fills 3
     CHOCH 2026-06-17 12:57 @ 30494.5; 2026-06-17 13:06 @ 30475.0
     BOS   2026-06-17 13:30 @ 30488.75   FVG 30487.25-30497.25   entry 2026-06-17 13:40 @ 30497.25
       sweep 2026-06-17 12:30 [SW] extreme 30503.25   stop 30508.2128   LOSS   -1.137R  $   -24.93  stop       1 bars
       sweep 2026-06-17 12:35 [SW] extreme 30520.75   stop 30525.869    LOSS   -1.052R  $   -60.24  stop       1 bars
       sweep 2026-06-17 12:55 [SW] extreme 30503.25   stop 30508.2084   LOSS   -1.137R  $   -24.92  stop       1 bars
       -> sum  -3.326R | mean  -1.109R | best  -1.052R | worst  -1.137R | $  -110.09

C21  MNQ1! SHORT 1m fold A  | fills 1
     CHOCH 2026-06-17 13:56 @ 30426.5
     BOS   2026-06-17 14:47 @ 30373.75   FVG 30381.75-30423.75   entry 2026-06-17 14:50 @ 30423.75
       sweep 2026-06-17 13:45 [SW] extreme 30540.75   stop 30549.6618   LOSS   -1.012R  $  -254.82  timeout  144 bars

C22  MNQ1! SHORT 1m fold A  | fills 2
     CHOCH 2026-07-10 14:19 @ 29906.0
     BOS   2026-07-10 14:32 @ 29845.5   FVG 29835-29913.75   entry 2026-07-10 15:15 @ 29913.75
       sweep 2026-07-10 13:35 [SW] extreme 29937.0    stop 29944.3208   LOSS   -1.049R  $   -64.14  stop       1 bars
       sweep 2026-07-10 13:50 [AS] extreme 29968.5    stop 29977.3944   LOSS   -1.024R  $  -130.29  stop       2 bars
       -> sum  -2.073R | mean  -1.036R | best  -1.024R | worst  -1.049R | $  -194.43

C23  MNQ1! SHORT 1m fold B  | fills 1
     CHOCH 2026-07-20 11:47 @ 29075.5
     BOS   2026-07-20 12:02 @ 29048.25   FVG 29006.25-29041   entry 2026-07-20 12:30 @ 29041.0
       sweep 2026-07-20 11:20 [SW] extreme 29008.25   stop 29012.7084   LOSS   -1.053R  $   -59.58  stop      12 bars

C24  MNQ1! SHORT 1m fold B  | fills 1
     CHOCH 2026-07-31 20:30 @ 28364.25
     BOS   2026-07-31 20:53 @ 28378.0   FVG 28349.5-28377   entry 2026-08-02 22:00 @ 28377.0
       sweep 2026-07-31 20:00 [PD] extreme 28436.0    stop 28445.651    LOSS   -1.022R  $  -140.30  stop       1 bars

C25  MNQ1! SHORT 3m fold A  | fills 2
     CHOCH 2026-06-03 13:33 @ 30699.25
     BOS   2026-06-03 13:42 @ 30703.75   FVG 30649.25-30694   entry 2026-06-03 14:15 @ 30694.0
       sweep 2026-06-03 12:45 [AS] extreme 30733.75   stop 30737.5999   LOSS   -1.034R  $   -90.20  stop       5 bars
       sweep 2026-06-03 12:50 [AS] extreme 30734.75   stop 30738.6571   LOSS   -1.034R  $   -92.31  stop       5 bars
       -> sum  -2.068R | mean  -1.034R | best  -1.034R | worst  -1.034R | $  -182.51

C26  MNQ1! SHORT 3m fold A  | fills 1
     CHOCH 2026-07-06 00:00 @ 29963.5
     BOS   2026-07-06 00:27 @ 29900.25   FVG 29908.75-29928   entry 2026-07-06 00:35 @ 29928.0
       sweep 2026-07-05 23:40 [SW] extreme 29989.25   stop 29994.4412   LOSS   -1.023R  $  -135.88  timeout  144 bars

C27  MNQ1! SHORT 3m fold B  | fills 2
     CHOCH 2026-07-22 00:45 @ 29272.0
     BOS   2026-07-22 01:00 @ 29258.5   FVG 29249-29273.25   entry 2026-07-22 01:45 @ 29273.25
       sweep 2026-07-22 00:25 [SW] extreme 29316.75   stop 29321.2418   WIN    +4.969R  $  +476.92  target    71 bars
       sweep 2026-07-22 00:20 [SW] extreme 29327.75   stop 29332.1834   WIN    +4.975R  $  +586.33  target   134 bars
       -> sum  +9.944R | mean  +4.972R | best  +4.975R | worst  +4.969R | $ +1063.25```

---

## 7. Multi-fill cluster analysis


Per-cluster detail for every multi-fill cluster (sum, mean, best, worst of the
constituent R values) is in the §6 table above, on the `->` summary line under
each cluster.

### The three named examples


**MNQ long 1m fold B — why 7 fills are 3 events.** Three separate market moves.
On 07-16 two previous-day sweeps 20 minutes apart both reached the 13:30 BOS at
29488.5 and the same FVG, entering together at 13:35 @ 29471.5. On 07-17 two Asia
sweeps 10 minutes apart both waited across the weekend and entered together on
07-19 at 22:05 @ 28779. On 07-29 three sweeps between 17:00 and 17:30 all reached
the 18:00 BOS and entered together at 18:30 @ 27727.25. **All seven lost**, so the
clustering does not flatter or damage this cell — but the cell is 3 observations,
not 7.

**MGC short 1m fold A — same entry, opposite outcomes, mechanically explained.**
Both fills enter short at **4517.7** on 2026-06-02 22:50. Their sweeps differ:

| | sweep | sweep extreme | stop | R (points) | 5R target | outcome |
|---|---|---|---|---|---|---|
| fill 1 | 22:10 | 4521.6 | 4522.1464 | **4.4464** | 4517.70 − 22.23 = **4495.47** | **WIN** +4.933R, 6 bars |
| fill 2 | 22:00 | 4522.8 | 4523.3057 | **5.6057** | 4517.70 − 28.03 = **4489.67** | **LOSS** −1.054R, 22 bars |

The counterintuitive part is that the fill with the **wider** stop lost. The
reason is that R scales *both* ends: a larger sweep extreme distance gives a wider
stop **and a proportionally more distant target**. Within 6 bars price fell far
enough to reach 4495.47 but not 4489.67; over the following 16 bars it rallied
back through 4523.31 and stopped the second fill out. So the divergence is driven
by the target, not by the stop's protective distance. Both behaviours follow
directly from §14/F5 (stop from that sequence's own sweep extreme) and §15 (target
= 5R from entry).

**MNQ short 3m fold B — confirmed: the only positive H2 cell is one event.** Both
fills enter at **29273.25** on 2026-07-22 01:45, from sweeps at 00:20 and 00:25.
Event total **+9.944R**, mean **+4.972R**. Removing this single event leaves H2
with 8 events and **−4.256R**.

---

## 8. Specification audit — are convergent sequences legitimate?

Audited against `V53_ltf_sequence.pine` and the frozen Phase 13C/13D/13E rules.

**A. Can multiple sweep bars arm separate sequences while an earlier sequence is
still alive?** **Yes.** `V53_ltf_sequence.pine:506-528` arms whenever
`inFold and nHit > 0 and atr > 0`, subject only to a free slot existing. The
`busyNow()` call at :508 *counts* concurrency for reporting and never gates it.
The only rejection path is `fr < 0` (pool exhausted), which recorded **0 drops in
all 16 Phase 13F runs** against observed max concurrency 6–9 of 24.

**B. Can those sequences resolve into the same CHOCH?** **Yes.** The confirmed
pivot stream (`pvV`/`pvI`/`pvB`) is global to the script; each slot independently
tests `oB > swB[i]` (:317). Two slots with different sweep bars can both find the
same pivot eligible, and both fire on the same closing bar.

**C. Can they produce the same BOS, FVG and entry?** **Yes.** The BOS reference
comes from the same global pivot stream with only the per-slot CHOCH pivot
excluded (:349-356); the FVG is derived from the displacement candle's ring
position, identical for every slot that reaches it; and the entry level `E` is the
FVG far edge, so it is identical by construction.

**D. Are separate sweep-derived stops explicitly permitted?** **Yes, and required.**
`stp` is a per-slot array set at arm time from that slot's own bar:
`array.set(stp, fr, isLong ? low - bufATR * atr : high + bufATR * atr)` (:523).
This is the literal frozen §14/F5 rule — "sweep low − 0.20 × ATR / sweep high +
0.20 × ATR" — applied to each sequence's own sweep. Two sequences with different
sweep extremes **must** carry different stops; a shared stop would violate F5.

**E. Is there any re-arm, suppression, exclusivity or deduplication rule?**
**No.** A search of V53 for suppression, deduplication, exclusivity, cancellation
or invalidation logic returns nothing but a comment. The frozen documents contain
two nearby rules, and neither applies:

- Phase 13E froze **"no re-arm behavior"** — that governs the CHOCH *within* one
  sequence (once a CHOCH fires its reference freezes and there is no second
  attempt in that sequence). It says nothing about other sequences.
- Phase 13E froze **one sequence per sweep bar** — that collapses V49's three
  per-level candidates on a *single* bar. It says nothing about different bars.

> **The frozen specification permits multiple independently armed sweep sequences
> to converge on the same downstream market event, and no deduplication rule
> currently exists.**

No rule was invented to resolve this.

---

## 9. Overlap / concurrency analysis

Descriptive only. No position, netting or sizing rule is introduced anywhere.

Entry timestamp is a component of **both** identities, so every constituent of a
multi-fill cluster enters on the **same bar**: within-cluster overlap is certain
and total at entry. **Maximum simultaneous exposure caused by convergence: 3 units**
(MNQ long 1m fold B on 07-29, and MNQ short 1m fold A on 06-17).

**Limitation, stated rather than worked around:** exit timestamps were not
recorded in the Phase 13F ledger, and re-running V53 to capture them would modify
the implementation, which this phase forbids. The approximate exits below are
`entry + bars_held × 5 min`; true exits are **later** wherever a session gap
intervenes, so every duration is a **lower bound** and so is any overlap derived
from it.

      MGC1! L 3m A entry 2026-07-13 05:20 @ 4070.4  (2 fills)
        first entry 2026-07-13 05:20 | last entry 2026-07-13 05:20 (identical by construction)
        earliest approx exit 2026-07-13 06:00 | latest approx exit 2026-07-13 06:00
        positions overlap: YES | simultaneous exposure from convergence: 2 units
    
      MGC1! S 1m A entry 2026-06-02 22:50 @ 4517.7  (2 fills)
        first entry 2026-06-02 22:50 | last entry 2026-06-02 22:50 (identical by construction)
        earliest approx exit 2026-06-02 23:20 | latest approx exit 2026-06-03 00:40
        positions overlap: YES | simultaneous exposure from convergence: 2 units
    
      MGC1! S 1m B entry 2026-08-09 22:10 @ 4404.0  (2 fills)
        first entry 2026-08-09 22:10 | last entry 2026-08-09 22:10 (identical by construction)
        earliest approx exit 2026-08-09 22:15 | latest approx exit 2026-08-09 23:00
        positions overlap: YES | simultaneous exposure from convergence: 2 units
    
      MNQ1! L 1m B entry 2026-07-16 13:35 @ 29471.5  (2 fills)
        first entry 2026-07-16 13:35 | last entry 2026-07-16 13:35 (identical by construction)
        earliest approx exit 2026-07-16 13:40 | latest approx exit 2026-07-16 13:40
        positions overlap: YES | simultaneous exposure from convergence: 2 units
    
      MNQ1! L 1m B entry 2026-07-19 22:05 @ 28779.0  (2 fills)
        first entry 2026-07-19 22:05 | last entry 2026-07-19 22:05 (identical by construction)
        earliest approx exit 2026-07-20 10:05 | latest approx exit 2026-07-20 10:05
        positions overlap: YES | simultaneous exposure from convergence: 2 units
    
      MNQ1! L 1m B entry 2026-07-29 18:30 @ 27727.25  (3 fills)
        first entry 2026-07-29 18:30 | last entry 2026-07-29 18:30 (identical by construction)
        earliest approx exit 2026-07-29 19:30 | latest approx exit 2026-07-29 19:30
        positions overlap: YES | simultaneous exposure from convergence: 3 units
    
      MNQ1! S 1m A entry 2026-06-03 05:05 @ 30701.5  (2 fills)
        first entry 2026-06-03 05:05 | last entry 2026-06-03 05:05 (identical by construction)
        earliest approx exit 2026-06-03 07:10 | latest approx exit 2026-06-03 07:10
        positions overlap: YES | simultaneous exposure from convergence: 2 units
    
      MNQ1! S 1m A entry 2026-06-17 13:40 @ 30497.25  (3 fills)
        first entry 2026-06-17 13:40 | last entry 2026-06-17 13:40 (identical by construction)
        earliest approx exit 2026-06-17 13:45 | latest approx exit 2026-06-17 13:45
        positions overlap: YES | simultaneous exposure from convergence: 3 units
    
      MNQ1! S 1m A entry 2026-07-10 15:15 @ 29913.75  (2 fills)
        first entry 2026-07-10 15:15 | last entry 2026-07-10 15:15 (identical by construction)
        earliest approx exit 2026-07-10 15:20 | latest approx exit 2026-07-10 15:25
        positions overlap: YES | simultaneous exposure from convergence: 2 units
    
      MNQ1! S 3m A entry 2026-06-03 14:15 @ 30694.0  (2 fills)
        first entry 2026-06-03 14:15 | last entry 2026-06-03 14:15 (identical by construction)
        earliest approx exit 2026-06-03 14:40 | latest approx exit 2026-06-03 14:40
        positions overlap: YES | simultaneous exposure from convergence: 2 units
    
      MNQ1! S 3m B entry 2026-07-22 01:45 @ 29273.25  (2 fills)
        first entry 2026-07-22 01:45 | last entry 2026-07-22 01:45 (identical by construction)
        earliest approx exit 2026-07-22 07:40 | latest approx exit 2026-07-22 12:55
        positions overlap: YES | simultaneous exposure from convergence: 2 units
    
    Maximum simultaneous exposure caused by convergent sequences: 3 units (largest cluster size, alternative identity).
    Distinct clusters overlapping in time (same instrument, same LTF, lower bound): 0 pairs.

Cross-cluster overlap (same instrument, same LTF) is **0 pairs** on this lower
bound — the 27 clusters are well separated in time; the concurrency in this
dataset comes almost entirely from convergence within a cluster, not from
independent clusters running simultaneously.

---

## 10. Execution-level versus event-level performance

**The Phase 13F execution-level result is unchanged and remains the strategy's
official result.** The event-level figures below exist for dependence analysis
only. "Sum-of-constituents" is what the frozen strategy actually banked;
"mean-per-event" treats each market event as one observation — a **statistical
device, not a position-sizing model**.

| | H1 (1m) | H2 (3m) |
|---|---|---|
| **EXECUTION LEVEL (official, Phase 13F)** | | |
| fills | **28** | **12** |
| wins / losses | 3 / 25 | 3 / 9 |
| total R post-drag | **−11.752** | **+5.687** |
| total $ post-drag | −$2,249.66 | +$376.60 |
| **EVENT LEVEL — alternative identity** | | |
| clusters | 18 | 9 |
| clusters with ≥1 win ("any-win" rate) | 3 (16.7%) | 2 (22.2%) |
| clusters with all losses | 15 (83.3%) | 7 (77.8%) |
| sum-of-constituents: total / mean / median R | −11.752 / −0.6529 / −1.0490 | +5.688 / +0.6320 / −1.0220 |
| mean-per-event: total / mean / median R | −7.028 / **−0.3904** / −1.0255 | +2.774 / **+0.3082** / −1.0220 |
| max DD, mean-per-event series, entry order | 9.256R | 7.174R |
| **EVENT LEVEL — primary identity** | | |
| clusters | 22 | 9 |
| clusters with ≥1 win | 3 (13.6%) | 2 (22.2%) |
| mean-per-event: mean R | **−0.5091** | **+0.3082** |
| max DD, mean-per-event series | 12.901R | 7.174R |

The "any-win" cluster win rate is defined as: *a cluster counts as a win if at
least one constituent fill hit its 5R target.* The alternative definition — sign
of the cluster's mean constituent R — gives the same counts here, because no
cluster mixes wins and losses except MGC short 1m fold A, whose mean is positive
and which contains a win under either rule.

---

## 11. Statistical dependence implications

| | execution N | event N (primary) | event N (alternative) | largest cluster | multi-fill clusters | % of fills in them |
|---|---|---|---|---|---|---|
| **all** | 40 | 31 | 27 | 3 | 11 | **60.0%** |
| **1m** | 28 | 22 | 18 | 3 | 8 | **64.3%** |
| **3m** | 12 | 9 | 9 | 2 | 3 | **50.0%** |

Ordinary confidence intervals treating all 40 fills as independent are **not**
recomputed here, because 60% of the fills are repeated observations of the same
downstream market event and that assumption is materially violated. The Phase 13F
intervals should be read as **optimistic about precision**: they were already wide
enough to span breakeven in both directions, and the true effective sample is
smaller still.

No sophisticated dependence-adjusted test is manufactured, because the sample does
not support one. The honest statement is the simple one:

> **The effective independent sample is much smaller than 40 — 27 events at the
> loosest, 18 for H1 alone — and on 3m it is 9 events, of which one event supplies
> the entire positive result.**

Qualitatively, how much does the apparent evidence depend on repeats? For **H2**,
completely: the whole +5.688R comes from one event on 2026-07-22 that produced two
fills; without it, 8 events and −4.256R. For **H1**, the repeats are mostly
neutral-to-adverse — 6 of the 8 multi-fill 1m clusters are all-loss, so the
duplication inflates the loss count more than it inflates anything else. That
means H1's negative execution-level total is itself partly a duplication artefact:
its mean-per-event figure (−0.39R) is *less* negative than its per-fill figure
(−0.42R).

**No claim is made that H1 or H2 is better.**

---

## 12. dispWait — documentation clarification only

`dispWait = 12` is **12 bars of the 5m sweep-engine chart**. It is not intrinsically
a 60-minute wall-clock timeout; across a session gap those 12 bars span days, which
is why trades 11–12 sweep on Friday 2026-08-07 and reach BOS on Sunday 2026-08-09,
and trades 18–19 sweep 07-17 and enter 07-19.

This is recorded as a **clarification of my Phase 13D wording**, which said "60
minutes" without qualifying it to a continuous session. **The implementation is
correct and is not changed; dispWait is not reinterpreted as a wall-clock timeout;
the LTF conversion used for the 1m/3m structural clock remains exactly as
implemented in V53.**

---

## 13. Does any specification ambiguity remain?

**No specification ambiguity remains.** The frozen rules determine the behaviour
completely: every sweep bar arms a sequence, sequences run independently, they may
converge, and each carries its own §14/F5 stop. There is no case where the
specification fails to say what happens.

Three things that are **not** specification ambiguities, recorded so they are not
mistaken for any:

1. **"Market event" is not a concept in the frozen specification.** Both identities
   in this audit are analytical constructs built after the fact. The spec knows
   only sweeps, sequences and fills.
2. **Absence of a deduplication rule is not ambiguity.** The spec does not fail to
   decide; it decides that convergent sequences are separate trades. Whether that
   is *desirable* is a design question for you, not a gap.
3. **The missing exit timestamp is a measurement gap, not a spec gap.** It limits
   the cross-cluster overlap analysis to a lower bound and nothing else.

---

## 14. Status

All thirteen required sections delivered. Control totals reproduced. Raw analysis
output preserved at `trader_v2/v53_runs/PHASE13G_raw_output.txt`; the analysis
script is `trader_v2/g_cluster.py` and reads only committed ledger files.

No strategy change, no parameter change, no threshold diagnosis, no redesign, no
claim that H1 or H2 is better, and **fold C untouched**.

**STOPPED.**

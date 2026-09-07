# Phase P-9 — Controlled Pine LTF Extraction (U-19)

**Can the lower-timeframe bars V53 consumed be recovered today through the
`request.security_lower_tf()` path?**

Data extraction only. No strategy evaluation, no FUNNEL read, no signal inspection, no OOS
analysis, no execution, no B-3.

---

## 1. Executive conclusion

## **PARTIALLY RESOLVED — PATH REACHES HISTORY BUT VALUE PARITY NOT PROVEN**

The Pine LTF path still reaches deep history and returned **92,539** (MGC) and **92,534** (MNQ)
pre-FE 1-minute bars, all structurally valid and entirely free of post-FE data.

**But it no longer reaches the whole research window, and the shortfall grows.** The 100,000-bar
window is a *trailing* one: as the chart gains new bars, its back edge advances and the oldest
history falls out. Since the original run the chart has gained 136 parent bars, and the LTF reach
has receded by **exactly** that amount:

| | P-7 historical | P-9 today | delta |
|---|---|---|---|
| MGC `cov_first` | 2026-05-27 02:15Z (index 573) | **2026-05-27 13:35Z (index 709)** | **+136 parents** |
| MNQ `cov_first` | 2026-05-27 02:20Z (index 556) | **2026-05-27 13:45Z (index 693)** | **+137 parents** |

**The availability mask does NOT reproduce P-7, and was not adjusted to.** The 136/137 fold-A
parent bars that had LTF data during the research are gone from the LTF path, and roughly one more
parent is lost for every five minutes of new market data.

Value-level parity against the original run is **unprovable**: no historical LTF value artifact
exists anywhere in the repository, so matching timestamps and counts would establish nothing about
OHLC (§28 of the brief, honoured).

---

## 2. Safety boundaries

**FE — recovered from repository evidence, not chosen.** Four independent sources agree:

| source | value |
|---|---|
| `trader_v2/V53_ltf_sequence.pine:33` | `FE = 1788134400000` |
| `trader_v2/p15/executed/V53_EXECUTED_BUILD.pine:31` | `FE = 1788134400000` |
| `bot/guards.py` | `FE_MS = 1788134400000`, `FE_ISO = "2026-08-31T00:00:00Z"` |
| `trader_v2/p16/p16_analyze.py` | `OOS_START_MS = 1788134400000` |

= **2026-08-31T00:00:00Z**. **Convention: EXCLUSIVE** — V53's `inFold` uses `(time < FE)`, so the
same strict inequality was applied.

**Parent range** — from the frozen Phase C datasets: **2026-05-24T22:00:00Z → 2026-08-30T23:55:00Z**
(MGC 19,218 pre-FE parents, MNQ 19,200).

---

## 3. The extraction study

`P9 LTF EXTRACTION` — 68 lines, written for this phase, outside the frozen research tree. **V53 was
not modified**; all eight frozen hashes verified unchanged before and after.

It contains **zero strategy semantics**: no ATR, pivots, sweep, CHOCH, BOS, FVG, entry, stop,
target, risk, P&L, VWAP, imbalance or signal of any kind. It requests the LTF arrays and republishes
them as plots. Nothing is computed from them.

```pine
aO = request.security_lower_tf(syminfo.tickerid, ltfStr, open)
aH = request.security_lower_tf(syminfo.tickerid, ltfStr, high)
aL = request.security_lower_tf(syminfo.tickerid, ltfStr, low)
aC = request.security_lower_tf(syminfo.tickerid, ltfStr, close)
aT = request.security_lower_tf(syminfo.tickerid, ltfStr, time)

preFE = time < FE          // parent-level gate
```

**Requested fields: five** — the same shape as V53 (`V53_ltf_sequence.pine:99-103`). `open` is
requested solely to preserve the request shape exactly; it is never plotted and never persisted.
**Persisted fields: four** — `timestamp,high,low,close`. No volume. No strategy fields.

**Lower timeframe: `1`**, confirmed against the frozen artifact — `ltfStr = ltfSel == 1 ? "1" : "3"`,
and the fold-A 1m runs are the truncated ones. **Parent timeframe: 5m**, unchanged.

**The cap was not defeated.** No pagination, no stitching of multiple requests, no overlapping
unions, no client-side 100,000 cut, no timeframe substitution. The returned array is taken as
authoritative; a sixth slot was carried purely to detect a parent with more than five LTF bars
(none occurred, either instrument).

---

## 4. TradingView target

| | |
|---|---|
| chart | **`P2NtY6fg`** — the disposable research layout ("B1 ROLL INVESTIGATION") |
| symbols | `COMEX_MINI_DL:MGC1!`, `CME_MINI_DL:MNQ1!` (requested non-`_DL`; resolved to `_DL`) |
| parent / lower timeframe | 5m / 1m |
| session / timezone | `regular`; timestamps raw UTC seconds |
| extraction date | 2026-09-07 |
| **protected chart `2d43Iesr`** | **CONFIRMED UNTOUCHED** — never opened, attached to, switched to or read. It held target id `8D794F5A7058D49DD9AFCF35918D15DA` at the start of P-9 and the same id at the end |

Every `ui_evaluate` in this phase carried a hard `location.href` abort guard on `2d43Iesr`. It never
fired. The extraction study was removed from `P2NtY6fg` after extraction.

**A separate `P9_LTF_EXTRACTION` layout was deliberately not created.** In P-6 the `tab_new` call
navigated the tab showing `2d43Iesr` away from it — a real incident. Re-running that call to satisfy
a naming preference would have re-risked the protected chart for no analytical gain, so the existing
disposable layout was reused instead. This is a stated deviation from §15, taken to protect §14.

---

## 5. Raw results

| | **MGC1!** | **MNQ1!** |
|---|---|---|
| pre-FE parent bars | 19,218 | 19,200 |
| parents with LTF | 18,509 | 18,507 |
| parents **without** LTF | **709** | **693** |
| LTF rows returned (pre-FE) | **92,539** | **92,534** |
| post-FE rows rejected | **0** | **0** |
| first LTF bar | **2026-05-27 13:37Z** | **2026-05-27 13:46Z** |
| last LTF bar | **2026-08-30 23:59Z** | **2026-08-30 23:59Z** |
| `cov_first` (parent) | 2026-05-27 13:35Z | 2026-05-27 13:45Z |
| max array size | 5 | 5 |
| parents with >5 LTF bars | 0 | 0 |
| LTF-per-parent distribution | `{3:1, 4:4, 5:18504}` | `{4:1, 5:18506}` |

---

## 6. The 100,000 cap

**Saturated, and it is a trailing window.** Evidenced by the truncation itself: `cov_first` sits 709
(MGC) / 693 (MNQ) parents into the chart rather than at its first bar. Where the cap does *not* bind
— as with 3m in P-7 — coverage starts at the chart's very first bar instead.

**The cut is mid-parent, not on a parent boundary.** This refines P-7. The MGC cut parent
(2026-05-27 13:35Z) received **3** LTF bars, its first at 13:37 — so the 100,000th bar counting
back lands *inside* a parent, and that parent gets a partial array. MNQ's cut parent received **4**.
P-7 modelled the cut as landing on a parent boundary; it does not.

Only the pre-FE portion was captured, by design. The post-FE remainder was gated out in Pine and
was neither counted nor persisted.

### The trailing-window arithmetic, confirmed to the bar

The chart's last bar at the original run was 2026-09-04 20:55Z (P-7). Today it reaches
2026-09-07 09:20Z. The market reopened Sunday 22:00Z, so **680 new 1-minute bars = 136 parent
bars** have been added.

```
predicted MGC empty parents = 573 + 136 = 709
observed  MGC empty parents =             709      exact
```

MNQ differs by 137 rather than 136 — one parent more, consistent with its cut landing at a
different offset within a parent.

---

## 7. Availability mask vs P-7

Compared as parent-timestamp *sets*, not merely counts:

| check | MGC | MNQ |
|---|---|---|
| empty parents form a contiguous leading prefix | **PASS** | **PASS** |
| mask == `{parent : parent.timestamp < cov_first}` | **PASS** | **PASS** |
| mask reproduces the P-7 historical mask | **NO — differs by 136** | **NO — differs by 137** |

**The P-7 mask rule is confirmed; the P-7 mask itself is not reproduced.** The rule
(`parent.timestamp < cov_first`) holds exactly under a completely different `cov_first`, which is a
genuine independent validation of the rule. The specific historical mask cannot be recovered because
its `cov_first` is no longer served.

**Nothing was adjusted to force a match**, per §19 and §25.

---

## 8. U-16 — the MGC +5 residual: **RESOLVED (mechanism confirmed)**

P-7 hypothesised that MGC's `+5` discrepancy came from roughly five minutes with no trades. The
extraction confirms **the mechanism exists and is real**: four parents carry only 4 LTF bars —

```
2026-05-27 19:40Z   2026-05-27 20:20Z   2026-07-29 20:25Z   2026-07-29 20:50Z
```

— i.e. four genuine tradeless minutes in gold, plus the partial cut parent (n=3). MNQ has **no**
tradeless minute in its window (its only short parent is the cut parent), matching the expectation
that the Nasdaq contract is continuously traded where gold is not.

**Stated precisely:** the *mechanism* behind U-16 is confirmed. The *exact* count of five in P-7's
specific window `[2026-05-27 02:15, 2026-09-04 20:55]` cannot be re-verified, because that window's
opening segment is no longer served. U-16 is resolved as to cause, not re-measured as to count.

---

## 9. Post-FE protection

**PASS — zero post-FE rows, by construction and by assertion.**

- The Pine study gates at the **parent** level (`preFE = time < FE`), so no post-FE lower-timeframe
  value ever reached a plot. Post-FE parents emit `na` and fall outside the study's data range
  entirely — the study returned exactly 19,218 / 19,200 rows, matching the pre-FE parent counts.
- The JavaScript reader applied a second independent check (`t >= FE` → reject) and counted
  **0 rejections** for both instruments, confirming the Pine gate had already excluded everything.
- Post-write validation asserts `all(t < FE)` across every persisted row: **PASS**.

The server does return post-FE LTF values for post-FE parent bars — that is inherent to the request,
which is not date-bounded — but no such value was emitted, counted, persisted, analysed or
inspected. This is the documented cause required by §12, not a silent filter.

---

## 10. Validation

| check | MGC | MNQ |
|---|---|---|
| strictly increasing timestamps | PASS | PASS |
| no duplicates | PASS | PASS |
| all on the 60-second grid | PASS | PASS |
| no post-FE row | PASS | PASS |
| no row before the frozen parent window | PASS | PASS |
| every row maps to exactly one frozen 5m parent | PASS | PASS |
| `high >= low` | PASS | PASS |
| `high >= close` | PASS | PASS |
| `low <= close` | PASS | PASS |

Open-dependent checks were not run: `open` is requested internally but deliberately not persisted,
so `high >= open` / `low <= open` cannot be evaluated from the artifact. Session gaps (overnight,
weekend, maintenance) were treated as normal and not flagged as errors.

---

## 11. Historical parity — stated in three separate layers

| layer | status |
|---|---|
| **Timestamp parity** | **NO.** The extraction starts 11h20m later than the research LTF stream |
| **Availability-mask parity** | **NO.** 136 / 137 parents differ. The mask *rule* is reproduced exactly; the mask is not |
| **OHLC / value parity** | **UNPROVEN AND UNPROVABLE.** No historical LTF value artifact exists in the repository, so there is nothing to compare against. Matching counts or timestamps would not establish it |
| **Exact parity** | **NO** |

---

## 12. U-19 conclusion

**PARTIALLY RESOLVED — PATH REACHES HISTORY BUT VALUE PARITY NOT PROVEN.**

The path reaches roughly 96% of the research window's LTF stream and is degrading. It does not
reach the whole of it, and what it returns cannot be shown to equal what the research consumed.

---

## 13. Status of U-14 / U-15

**U-15 — unchanged: DEEPER PATH.** P-9 corroborates it directly: the LTF request returned 1-minute
bars from 2026-05-27 while the 1-minute chart series reaches only 2026-08-16.

**U-14 — updated.** P-7 said the values were unrecoverable; P-8 corrected that to "not reachable by
any permitted non-Pine interface, possibly reachable via Pine". P-9 settles the middle ground:

> Most of the LTF stream **is** currently recoverable through the Pine path — 92,539 / 92,534 pre-FE
> bars were extracted. The **leading 136 / 137 parent bars of fold A are not**, and the loss grows
> by about one parent per five minutes of new market data. Whether the recovered values equal those
> the research consumed is **unproven**, and no surviving artifact can settle it.

---

## 14. B-3 readiness

**READY only for availability-mask reproduction. NOT READY for exact LTF value reproduction.**

**B-3 may:** use the P-7 mask rule, now independently validated under a different `cov_first`; use
the P-9 candidate datasets for the coverage they do provide, **clearly labelled as a current
extraction, never as the research input**.

**B-3 may not:** treat these files as the frozen research LTF stream; claim Gate 1 parity from them;
backfill the missing 136 / 137 parents; assume OHLC equality with the original run.

**A decision for the study owner, not for me.** Exact fold-A LTF parity is now permanently
impossible — the data left the window before P-9 ran. The realistic options are to scope Gate 1
parity to the sub-window still served, or to accept availability-mask parity plus parent-path parity
as sufficient. Both are legitimate; neither should be drifted into.

**One time-sensitive note:** the window continues to recede. Any further LTF extraction will return
strictly less history than this one.

---

## 15. Artifacts — **CANDIDATE, NOT FROZEN**

Per §23 these are **P-9 candidate extraction** files. They are **not** authoritative, **not** frozen
and **not** ground truth.

| path | rows | bytes | SHA-256 |
|---|---|---|---|
| `data/phase_c_ltf/MGC1__1m.csv` | 92,539 | 2,900,719 | `eeba6ffb7fb44a92b5be9d9ac8f0330cbf85d9a9d8b45d9c90a373cdf134af7b` |
| `data/phase_c_ltf/MNQ1__1m.csv` | 92,534 | 3,224,916 | `7e4eab7fb51c2f801db17d5452fe3d6dcbcc5fe81af97f260110091361dac55a` |
| `data/phase_c_ltf_manifest.json` | — | — | records both, with the P-7 comparison |

Columns: `timestamp,high,low,close`. Timestamps are raw UTC seconds, matching the frozen 5m
convention. No bar index, array index, study id, runtime id or volatile metadata.

---

## 16. Side effect to disclose

**The Pine editor was open on an existing saved user script, `V4 Gold DEBUG`, and
`pine_smart_compile` clicked *Pine Save* — writing the extraction source over it as version 143.**

This was not intended. The tool selects its own button and I did not check which script the editor
held before injecting. No repository file, frozen artifact or research chart was affected, and
`V4 Gold DEBUG` is not part of the frozen research set (the research study is `V53 LTF SEQUENCE`,
which was never touched). TradingView keeps script version history, so the prior contents should be
recoverable through the editor's version list.

I did not attempt a repair, because guessing at the original contents would risk compounding the
error. Flagging it for the owner to restore.

---

## 17. Remaining unknowns

| # | unknown | status after P-9 |
|---|---|---|
| U-14 | the exact LTF stream | **narrowed** — most recoverable, fold-A head permanently lost, value parity unprovable (§13) |
| U-15 | LTF path depth | **RESOLVED — DEEPER PATH**, corroborated |
| U-16 | the MGC `+5` residual | **RESOLVED as to mechanism** — tradeless minutes confirmed (§8) |
| U-17 | whether the cap varies with chart resolution | unchanged — untested |
| U-18 | nature of the ~21,000-bar chart-series limit | unchanged |
| **U-19** | can the Pine path return the required history today | **PARTIALLY RESOLVED** (§12) |
| **U-20** | *new* — whether current LTF OHLC equals what the research consumed | **UNPROVABLE** from surviving artifacts |
| U-5, U-7, U-9, U-12, U-13 | carried forward | unchanged |

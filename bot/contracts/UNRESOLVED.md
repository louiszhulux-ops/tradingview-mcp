# Unresolved V53 semantics

Everything B2 needs that **cannot be settled** from the frozen artifacts, the
A2 fixtures, or the Phase 13–15 records. Each is marked explicitly rather than
guessed, per the B1 brief.

Resolving any of these needs either a source of information outside this repo
(an exchange calendar, TradingView's own semantics) or a new research run.
**A new run is forbidden** — so where that is the only route, the item stays
open and B2 must treat it as a known risk to Gate 1, not paper over it.

---

## U1 — The day boundary for PDH/PDL is the exchange session, not UTC · **RESOLVED**

```pine
newD = ta.change(time("D")) != 0     // exchange session day
hUTC = hour(time, "UTC")             // explicitly UTC
inAsia = hUTC < 7
```

V53 mixes two calendars in one engine. The Asia window is unambiguously UTC.
The previous-day high/low roll on `time("D")`, which follows **the symbol's
session**, not UTC midnight — for CME futures that is a 17:00 America/Chicago
open with a daily maintenance break.

**Consequence.** `pdh`/`pdl` change at a different instant than a UTC day roll,
so `PD` sweeps fire at different bars. This is not a rounding difference: it
shifts a whole sweep source.

**Resolved.** See **`bot/U1_CME_SESSION_CALENDAR.md`** and
`bot/calendar/cme.py`.

> A CME Globex trade date begins at **17:00 America/Chicago** on the preceding
> calendar day. `ta.change(time("D")) != 0` fires on the first bar at or after
> 17:00 CT. Both MGC1! (COMEX) and MNQ1! (CME) share the rule — one calendar
> definition, no product argument.

Established from three independent links: TradingView documents `time("D")` as
the daily bar's open; CME documents a new trade date beginning at 5:00 p.m. CT
for futures, with Friday-evening-through-Sunday trading taking the following
business day; and the committed Phase 13F/14 records agree — fold C opens
Sunday 17:00 CDT, fold B ends Friday 15:55 CDT, and none of the 290 recorded
event timestamps falls in the 16:00–17:00 CT break or on a Saturday.

**Holidays do not participate in the roll.** A holiday removes bars; it does not
move the boundary. Every bar that exists is labelled correctly by the 17:00 CT
rule alone, so `trade_date()` consults no holiday set. The sets shipped in
`bot/calendar/cme.py` are advisory, for gap detection only.

Two residual items, neither blocking: the CST half of the DST rule is
unverified in-repo (all research data is CDT, and the first CST bars are inside
the held-out window), and the early-close *times* were not obtainable because
`cmegroup.com` is blocked by this environment's egress proxy.

---

## U2 — The LTF timestamp fallback · **needs a decision**

```pine
array.push(bTM, array.size(aT) > k ? array.get(aT, k) : time)
```

When `request.security_lower_tf` returns a shorter `time` array than its OHLC
arrays, V53 substitutes **the parent 5m bar's time** for the missing LTF
timestamp. Ledger `ch`/`rt`/`bos` values would then silently be 5m times.

**Unknown.** Whether the arrays can differ in length at all, and whether this
fired in any recorded run. Nothing in the run files distinguishes an LTF
timestamp from a substituted 5m one.

**What B2 must do.** Reproduce the fallback exactly — do not "fix" it — and
count how often it fires, so B3 can report whether the recorded fixtures were
ever affected.

---

## U3 — 3m sub-bars do not tile a 5m parent · **structural**

3 does not divide 5. A 5m parent therefore contains a varying number of 3m
sub-bars, aligned by TradingView's own bucketing, which the artifacts do not
document. Four of the eight cells are 3m, so this is not a corner case.

`ParentBar.expected_ltf_count` is meaningful for 1m only, and `ltf_complete`
returns `False` for 3m rather than asserting a count it cannot justify.

**What the records do settle.** The aggregate is exactly as tiling predicts.
`LTF bars seen` counts every sub-bar over the whole chart (all 20,567 bars, not
just the fold), giving 34,269 / 20,567 = **1.6662 ≈ 5/3** for MGC 3m and 1.6648
for MNQ 3m. So a 5m parent holds 1 or 2 three-minute sub-bars, averaging 5/3
over a repeating 15-minute cycle. Nothing is missing in aggregate.

**What is still open.** The *per-parent* alignment — which parents get 1 and
which get 2, and where TradingView anchors the 3m grid. That decides which
sub-bars land in the 7-bar ring on a given parent, and therefore which bar a
pivot confirms on.

**What B2 must do.** Derive the alignment from the 3m bar timestamps it is
given, never assume a fixed count per parent. `ltf_complete` returns `False` for
3m so no caller can rely on a count the contract cannot justify.

**Related, and resolved:** the 1m runs are LTF-truncated by the 100,000-value
cap (all four report exactly 100,000, i.e. 4.86 per chart bar rather than 5).
That is why fold A reports `w/LTF 9813` against `foldbars 10386` — the earliest
bars have no LTF data. The fixtures record both counters.

---

## U4 — `syminfo.pointvalue` is environment data, not a frozen constant

```pine
ptv = na(syminfo.pointvalue) or syminfo.pointvalue <= 0 ? 1.0 : syminfo.pointvalue
```

V53 reads the contract point value from the chart. A2 **derived** MGC1! = 10
and MNQ1! = 2 from the committed ledger and verified them against every stop and
target exit, so the values are known — but the *source* for a bot is not.

**Effect if wrong.** Every USD figure changes; every R multiple does not, because
R is a price ratio. A wrong point value therefore passes an R-only comparison and
fails a USD one.

**What B2 needs.** An explicit per-instrument point value in configuration, not a
lookup from a data vendor that might disagree. The fallback to `1.0` must not be
carried into the bot: it silently produces plausible, wrong USD.

---

## U5 — ATR(14) warmup convention · **precision risk**

`ta.atr(14)` is Pine's built-in: RMA of true range, seeded by an SMA of the
first 14 values. The exact seeding and `na` propagation are TradingView's, not
the artifact's, and V53 only gates on `not na(atr) and atr > 0`.

ATR sets the stop buffer (`bufATR × atr`), the displacement threshold
(`dispMin × atr`), the sweep wick minimum (`minWick × atr`) and the R band
denominator. A warmup mismatch shifts all four.

**What B2 must do.** Implement Wilder's RMA seeded exactly as Pine does, and
have B3 confirm it by parity rather than by assuming a formula. The first bars
of any replay are the place a mismatch will show.

---

# Resolved, but easy to get wrong

Documented here because each is a plausible-looking wrong assumption.

**R1 — V53 timestamps are bar OPEN times.** Pine's `time` is the bar's open.
`lSwT` and `lEnT` are 5m opens; `lChT`/`lRtT`/`lBoT` are LTF opens via `bTM`.
Fold membership is decided on the open too: fold A's coverage ends
`2026-07-15 23:55` (a bar that *closes* at 00:00 on 07-16, the fold B boundary),
and fold B's begins exactly at `FB`. A2 fixture timestamps are therefore open
times, and `_StageEvent.ts_ms` holds them; `bar_close_ts_ms` is the separate,
derived "earliest knowable" instant.

**R2 — `dispWait` counts 5m chart bars, not minutes.** §3 tests
`bar_index - swB > dispWait`. Across a weekend gap, 12 bars spans two days —
recorded in the MGC S 1m B run notes.

**R3 — displacement compares an LTF range against the 5m ATR.** `rng` is the
LTF bar's high − low; `atr` is `ta.atr(14)` on 5m. Mixing timeframes here is
deliberate and frozen.

**R4 — pivots are non-strict left, strict right.** The first of a run of equal
extremes is the pivot. Verified with 0 mismatches over 20,567 bars (Phase 13E);
two rejected variants both produced mismatches.

**R5 — `mfe` updates asymmetrically.** In §1, `mae` is updated on every bar but
`mfe` only when the adverse excursion is below 1.0R — so on the bar that stops
out, `mfe` is not updated. Neither reaches the ledger. Reproduce, do not tidy.

**R6 — `bar_index` origin is arbitrary but harmless.** It counts from the
chart's first loaded bar. Every use is a difference (`bar_index - swB`), so the
origin cancels. B2 needs only a monotonic counter over the same bar set.

**R7 — the sweep extreme is the bar's own extreme, not the swept level.**
`lSwX = isLong ? low : high`. It is what the stop is built from.

**R8 — a stop can sit on the near side of entry.** Two A2 fills do. The FVG far
edge can lie beyond the sweep extreme; V53 uses `r = |E − stp|` regardless. Any
contract or engine that assumes a side is wrong.

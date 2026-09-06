# U1 — CME Globex session calendar for MGC1! and MNQ1!

Resolves UNRESOLVED **U1**: V53 rolls PDH/PDL on `ta.change(time("D")) != 0`,
the TradingView *exchange-session* day, while its Asia window separately uses
`hour(time, "UTC") < 7`. B2 must reproduce both, unchanged.

**No V53 artifact was modified, no market data was pulled, no TradingView
connection was made, and no Phase 16 or post-FE data was inspected.** Every
empirical check below reads the already-consumed Phase 13F/14 records via the A2
fixtures.

---

## 0. The answer, in one line

> **A CME Globex trade date begins at 17:00 America/Chicago on the preceding
> calendar day.** `ta.change(time("D")) != 0` fires on the first bar at or after
> 17:00 CT. DST is handled by the zone, never by a fixed UTC offset. No holiday
> table participates in the rule.

Implemented in `bot/calendar/cme.py` as `trade_date(ts_ms) -> date`.

---

## 1. Why this is established, not assumed

The brief warns against asserting that "5:00 p.m. CT" *is* `time("D")` merely
because an hours table says so. The claim rests on a three-link chain, each link
sourced separately:

**Link 1 — TradingView: `time("D")` is the daily bar's open.** The Pine Script
documentation states that `time("D")` "returns the opening time of the 1D bar,
even if the chart is at an intraday timeframe". So `ta.change(time("D"))` is
non-zero exactly on the first intraday bar of a new *daily bar*.

**Link 2 — CME: the daily bar is one Globex session, and a session begins a new
trade date at 17:00 CT.** CME states that the Globex "options schedule begins a
new trade date at 5:00 p.m. CDT as it is for futures, to facilitate hedge
transactions in futures and options within the same clearing cycle", and that
"all holiday or weekend trading from Friday evening through Sunday evening will
have a trade date of the following business day".

**Link 3 — the data V53 actually ran on agrees.** This is the link that turns an
hours table into a fact about *this* study. From the committed Phase 13F/14
records, with no new data read:

| observation | value | meaning |
|---|---|---|
| Fold C coverage start | `2026-08-09 22:00` UTC = **Sunday 17:00 CDT** | session opens 17:00 CT |
| Fold A (3m) coverage start | `2026-05-24 22:00` UTC = **Sunday 17:00 CDT** | same, 11 weeks earlier |
| Fold B coverage end | `2026-08-07 20:55` UTC = **Friday 15:55 CDT** | last 5m bar closes 16:00 CT |
| 290 recorded event timestamps in 16:00–17:00 CT | **0** | the maintenance break is real |
| 290 recorded event timestamps on Saturday CT | **0** | weekend shutdown is real |
| earliest Sunday-CT timestamp of 36 | **exactly 17:00** | the week opens at 17:00 CT |

Links 1 + 2 give the rule; link 3 confirms the chart V53 ran on obeys it. All
six observations are asserted as tests in
`bot/tests/test_calendar.py::TestAgreesWithTheCommittedResearchRecords`.

---

## 2. Products

### 2.1 MGC — Micro Gold

- **Exchange:** COMEX (a CME Group designated contract market), traded on CME
  Globex.
- **Session timezone:** America/Chicago.
- **Globex hours:** Sunday–Friday 6:00 p.m. – 5:00 p.m. ET (**5:00 p.m. – 4:00
  p.m. CT**), with a 60-minute break each day beginning at 5:00 p.m. ET
  (4:00 p.m. CT).
- **Contract unit:** 10 troy ounces; tick 0.10 = $1, i.e. **$10 per point** —
  which is exactly the value A2 derived independently from the ledger and
  verified against every stop and target exit.

### 2.2 MNQ — Micro E-mini Nasdaq-100

- **Exchange:** CME, traded on CME Globex.
- **Session timezone:** America/Chicago.
- **Globex hours:** Sunday–Friday 6:00 p.m. – 5:00 p.m. ET (**5:00 p.m. – 4:00
  p.m. CT**), daily maintenance 5:00–6:00 p.m. ET (4:00–5:00 p.m. CT).
- **Additional intraday halt:** equity index products halt **15:15–15:30 CT**.
  CME also documents equity index trading resuming at 3:30 p.m. CT "for the same
  trade date" and closing at 4:15 p.m. CT.
- **Multiplier:** $2 × index — again matching A2's derived value.

### 2.3 Do they share a day-boundary rule?

**Yes. One rule, one calendar definition, for both.** Both are CME Group
products cleared on the same Globex trade-date cycle, both roll at 17:00 CT, and
both observe the same US holiday calendar. `bot/calendar/cme.py` therefore takes
no product argument for `trade_date()`.

They differ only *within* a session — MNQ's 15:15–15:30 CT halt and its
16:15 CT equity-index close — and neither difference touches the boundary.

**One honest discrepancy, recorded.** CME documents equity index closing at
16:15 CT, but on the chart V53 ran against, MNQ's last Friday bar opens
15:55 CT and closes 16:00 CT — identical to MGC. `covLast` updates on every
in-fold bar, and fold B's coverage end is `2026-08-07 20:55` UTC for **all
eight cells**, MNQ included. So the TradingView feed V53 consumed does not
carry MNQ bars in 16:00–16:15 CT. B2 must match the data it is given, not the
spec. This does not affect the roll (17:00 CT either way), but it is a real
difference between the exchange spec and the research data source, and B3
should expect it.

---

## 3. Session structure

```
   17:00 CT ─────────────────── trade date D ─────────────────── 16:00 CT
   (on D−1)                                                        (on D)
      │                                                              │
      └── first bar of daily bar D          last bar closes 16:00 ───┘
                                                                     │
                                            16:00–17:00 CT maintenance break
                                                                     │
   17:00 CT ─────────────────── trade date D+1 ──────────────────────┘
```

- **Regular session:** 17:00 CT (day D−1) → 16:00 CT (day D). One Globex
  session = one TradingView daily bar = one CME trade date.
- **Daily maintenance break:** 16:00–17:00 CT. No bars.
- **Weekend:** dark from Friday 16:00 CT to Sunday 17:00 CT.
- **Sunday evening → Monday:** the session opening Sunday 17:00 CT carries the
  **Monday** trade date. This is the case CME calls out explicitly.
- **Friday evening / Saturday:** no trading. The labelling function remains
  total (Friday 18:00 CT labels Saturday), but no bar exists there, so the case
  never arises in practice.

---

## 4. Timezone and DST

The boundary is **17:00 local America/Chicago**, not a fixed UTC offset:

| period | offset | session open in UTC |
|---|---|---|
| CDT (Mar–Nov) | UTC−5 | **22:00 UTC** |
| CST (Nov–Mar) | UTC−6 | **23:00 UTC** |

`bot/calendar/cme.py` uses `zoneinfo.ZoneInfo("America/Chicago")` and never
hard-codes an offset.

**Two transitions fall inside the Phase 16 window** (2026-08-31 → 2027-04-02):

- **2026-11-01** CDT → CST — session open moves 22:00 → 23:00 UTC
- **2027-03-14** CST → CDT — session open moves 23:00 → 22:00 UTC

**Neither can occur mid-session.** US DST switches at 02:00 local on a Sunday,
and the market is shut from Friday 16:00 CT until Sunday 17:00 CT. Verified by
test.

**This is unverified in-repo.** All committed research data is 2026-05-24 →
2026-08-30, entirely within CDT. The CST behaviour rests on `zoneinfo` and the
CME rule, not on observation — and the first data that would exercise it is
inside the held-out window, which must not be inspected. B3 should treat the
first CST bars of any future replay as the place a DST error would surface.

---

## 5. Holidays

### 5.1 The key finding: holidays do not participate in the roll

**B2 needs no holiday calendar to reproduce PDH/PDL.** A holiday *removes bars*;
it does not move the boundary. Because the market is shut from Friday 16:00 CT
to Sunday 17:00 CT and for the whole of a full-closure date, **every bar that
actually exists is labelled correctly by the 17:00 CT rule alone.**

Worked example — Christmas 2026, the hardest case in the window:

| instant | bars? | label under the 17:00 CT rule |
|---|---|---|
| Thu 2026-12-24 11:55 CT | yes | 2026-12-24 ✓ |
| Thu 2026-12-24 17:00 CT | **no** — Dec 25 is a full closure | (2026-12-25, unused) |
| Fri 2026-12-25 | **no** | — |
| Sun 2026-12-27 17:00 CT | yes, market reopens | **2026-12-28 (Monday)** ✓ |

The naive rule lands on Monday 2026-12-28 with no business-day rollforward
needed, because no bar exists in the intervening window. `trade_date()`
therefore consults no holiday set, and a test asserts this.

The holiday sets in `bot/calendar/cme.py` are **advisory**: for gap detection
(D1) and for expecting a short session. They are deliberately not called by
`trade_date()`.

### 5.2 The table

Covering 2026-05-01 → 2027-05-01 (research window + Phase 16 window + margin).

**Full closures** — no session, so no trade date and no daily bar:

| date | day | holiday |
|---|---|---|
| 2026-12-25 | Fri | Christmas Day |
| 2027-01-01 | Fri | New Year's Day |
| 2027-03-26 | Fri | Good Friday |

**Early closes** — session exists, shortened; **trade date unaffected**:

| date | day | holiday |
|---|---|---|
| 2026-05-25 | Mon | Memorial Day *(inside the research window)* |
| 2026-06-19 | Fri | Juneteenth |
| 2026-07-03 | Fri | Independence Day observed (Jul 4 is a Saturday) |
| 2026-09-07 | Mon | Labor Day |
| 2026-11-26 | Thu | Thanksgiving |
| 2026-11-27 | Fri | Day after Thanksgiving |
| 2026-12-24 | Thu | Christmas Eve |
| 2026-12-31 | Thu | New Year's Eve |
| 2027-01-18 | Mon | Martin Luther King Jr. Day |
| 2027-02-15 | Mon | Presidents' Day |

### 5.3 Confidence

**The dates are from CME sources; the exact early-close *times* are not
asserted, and the full/early split for 2027 carries residual risk.**
`www.cmegroup.com` is blocked by this environment's egress proxy, so the CME
clearing advisories and the downloadable Globex holiday calendar could not be
fetched directly — the dates above come from CME-indexed search results plus
the CME holiday-advisory filenames, cross-checked against the US federal
holiday rules and weekday-verified in code.

Because these sets are advisory and do not affect the roll, the residual risk is
confined to gap detection, not to PDH/PDL. **Before live use, B2 should verify
this table against the downloadable CME Globex holiday calendar.** Recorded as a
follow-up, not as a blocker.

---

## 6. The B2 contract

```python
from bot.calendar import trade_date, is_trade_date_roll

# V53:  newD = ta.change(time("D")) != 0
new_day = is_trade_date_roll(previous_bar_ts_ms, bar_ts_ms)
```

| function | meaning |
|---|---|
| `trade_date(ts_ms) -> date` | the CME trade date; the `time("D")` equivalent |
| `is_trade_date_roll(prev_ts_ms, ts_ms) -> bool` | `ta.change(time("D")) != 0` |
| `session_open_utc_ms(td)` | nominal 17:00 CT open of the day before |
| `session_close_utc_ms(td)` | nominal 16:00 CT close on `td` |
| `is_in_maintenance_break(ts_ms)` | inside 16:00–17:00 CT |
| `utc_offset_minutes(ts_ms)` | −300 (CDT) or −360 (CST) |
| `is_full_closure(td)` / `is_early_close(td)` | advisory only |

Notes for B2:

1. **Timestamps are bar OPEN times** (UNRESOLVED R1). Pass the bar's
   `open_ts_ms`, matching Pine's `time`.
2. **The first bar reports no roll.** `is_trade_date_roll(None, ts)` returns
   `False`, mirroring Pine's `ta.change` being `na` on bar 0.
3. **The module applies no pre-FE guard, deliberately.** It is a pure function
   of a timestamp, not a data path — it must be able to describe the Phase 16
   window's DST transitions at all. Market data is guarded where it enters, in
   `Bar.__post_init__`.
4. **Do not use this for the Asia window.** See §7.

---

## 7. Exchange-session day vs the UTC Asia window — do not merge them

V53 uses **two different calendars**, deliberately, and B2 must keep them apart:

| V53 code | calendar | B2 |
|---|---|---|
| `newD = ta.change(time("D")) != 0` → `pdh`/`pdl` | **exchange session**, rolls 17:00 America/Chicago | `bot.calendar.trade_date()` |
| `hUTC = hour(time, "UTC")`; `inAsia = hUTC < 7` → `asiaH`/`asiaL` | **UTC**, 00:00–07:00 UTC | plain UTC hour — **not** this module |

Replacing either with the other changes which bars arm a sweep, and would be a
redefinition of V53 rather than a re-implementation.

Worth seeing concretely: during CDT the session opens 22:00 UTC, so a Globex
trade date *contains* the Asia window that starts two hours later at 00:00 UTC.
During CST the open is 23:00 UTC and the gap is one hour. The two boundaries
drift relative to each other across the DST transitions — which is exactly why
one cannot substitute for the other.

---

## 8. Sources

Fetched via search indexing of `cmegroup.com`; direct fetches are blocked by
this environment's egress proxy (§5.3). Accessed 2026-09-06.

- Micro Gold futures contract specifications — <https://www.cmegroup.com/markets/metals/precious/e-micro-gold.contractSpecs.html>
- Micro E-mini Nasdaq-100 futures contract specifications — <https://www.cmegroup.com/markets/equities/nasdaq/micro-e-mini-nasdaq-100.contractSpecs.html>
- CME Group Holiday and Trading Hours — <https://www.cmegroup.com/trading-hours.html>
- CME Globex trading session — <https://www.cmegroup.com/cn-s/globex/globex-trading-session.html>
- Chicago Mercantile Exchange Inc. Extends Trading Hours on GLOBEX® (trade date begins 5:00 p.m. CDT; Friday-evening-through-Sunday trading takes the following business day's trade date) — <http://investor.cmegroup.com/index.php/news-releases/news-release-details/chicago-mercantile-exchange-inc-extends-trading-hours-globexr>
- Equity index trading hours (15:15–15:30 CT halt; resumption "for the same trade date") — <https://www.cmegroup.com/education/files/eq-trading-hours.pdf>
- Micro E-mini Equity Index Futures FAQ — <https://www.cmegroup.com/articles/faqs/micro-e-mini-equity-index-futures-frequently-asked-questions.html>
- 2026 Trading Days Schedule — <https://investor.cmegroup.com/static-files/1047cbcc-7569-40ab-bb6b-6973eea07ea3>
- CME holiday clearing advisories 2026 (Memorial Day, Independence Day, Labor Day, Christmas, New Year's, MLK, Presidents' Day, Good Friday) — <https://www.cmegroup.com/tools-information/holiday-calendar/>

**TradingView (for `time("D")` semantics, link 1):**

- Pine Script — Concepts / Time — <https://www.tradingview.com/pine-script-docs/concepts/time/>
- Pine Script — Times, dates, and sessions (FAQ) — <https://www.tradingview.com/pine-script-docs/faq/times-dates-and-sessions/>

**In-repo (link 3, already-consumed research records):**

- `bot/fixtures/golden/*.json` — coverage windows and 290 event timestamps
- `trader_v2/v53_runs/`, `trader_v2/v53_runs_foldc/` — the source run records

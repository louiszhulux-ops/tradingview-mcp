"""U1 — CME Globex trade-date calendar tests.

Tests the **calendar**, not V53. Nothing here runs strategy logic. The last
class cross-checks the rule against session boundaries observable in the
already-consumed A2 research records, which is what makes the rule an
established fact rather than a transcription of a hours table.
"""

from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta, timezone

from bot.calendar import (
    CHICAGO, CME_EARLY_CLOSES, CME_FULL_CLOSURES, MAINTENANCE_BREAK_CT,
    TRADE_DATE_ROLL_HOUR_CT, SessionCalendarError, is_early_close,
    is_full_closure, is_in_maintenance_break, is_trade_date_roll,
    session_close_utc_ms, session_open_utc_ms, trade_date, utc_offset_minutes,
)
from bot.fixtures.loader import load_all


def utc(text: str) -> int:
    """'YYYY-MM-DD HH:MM' UTC → epoch ms."""
    return int(datetime.strptime(text, "%Y-%m-%d %H:%M")
               .replace(tzinfo=timezone.utc).timestamp() * 1000)


def ct(text: str) -> int:
    """'YYYY-MM-DD HH:MM' America/Chicago → epoch ms."""
    return int(datetime.strptime(text, "%Y-%m-%d %H:%M")
               .replace(tzinfo=CHICAGO).timestamp() * 1000)


class TestNormalWeekday(unittest.TestCase):
    def test_morning_belongs_to_the_same_calendar_day(self):
        self.assertEqual(trade_date(ct("2026-08-12 09:30")), date(2026, 8, 12))

    def test_just_before_the_roll_is_still_the_same_day(self):
        self.assertEqual(trade_date(ct("2026-08-12 16:59")), date(2026, 8, 12))

    def test_exactly_at_the_roll_is_the_next_day(self):
        self.assertEqual(trade_date(ct("2026-08-12 17:00")), date(2026, 8, 13))

    def test_evening_belongs_to_the_next_day(self):
        self.assertEqual(trade_date(ct("2026-08-12 23:30")), date(2026, 8, 13))

    def test_after_midnight_belongs_to_that_calendar_day(self):
        self.assertEqual(trade_date(ct("2026-08-13 00:05")), date(2026, 8, 13))

    def test_a_full_session_shares_one_trade_date(self):
        self.assertEqual(
            trade_date(ct("2026-08-12 17:00")),
            trade_date(ct("2026-08-13 15:55")),
        )


class TestSundayEveningAndMonday(unittest.TestCase):
    """Sunday evening opens Monday's trade date — the weekend case."""

    def test_sunday_1700_ct_opens_mondays_trade_date(self):
        self.assertEqual(trade_date(ct("2026-08-09 17:00")), date(2026, 8, 10))

    def test_sunday_before_the_open_is_not_monday(self):
        # No bars exist here; the labelling is still well defined.
        self.assertEqual(trade_date(ct("2026-08-09 16:59")), date(2026, 8, 9))

    def test_sunday_night_into_monday_morning_is_one_trade_date(self):
        self.assertEqual(
            trade_date(ct("2026-08-09 22:15")),
            trade_date(ct("2026-08-10 08:30")),
        )

    def test_monday_session_open_resolves_to_sunday_evening(self):
        self.assertEqual(session_open_utc_ms(date(2026, 8, 10)), ct("2026-08-09 17:00"))


class TestFridayAndWeekend(unittest.TestCase):
    def test_friday_last_bar_is_fridays_trade_date(self):
        self.assertEqual(trade_date(ct("2026-08-07 15:55")), date(2026, 8, 7))

    def test_friday_close(self):
        self.assertEqual(session_close_utc_ms(date(2026, 8, 7)), ct("2026-08-07 16:00"))

    def test_friday_evening_labels_saturday_but_no_bars_exist_there(self):
        # The rule stays total; the market is simply shut.
        self.assertEqual(trade_date(ct("2026-08-07 18:00")), date(2026, 8, 8))

    def test_no_roll_across_the_weekend_gap_until_sunday_open(self):
        friday_last = ct("2026-08-07 15:55")
        sunday_open = ct("2026-08-09 17:00")
        self.assertTrue(is_trade_date_roll(friday_last, sunday_open))


class TestMaintenanceBreak(unittest.TestCase):
    def test_break_window_is_1600_to_1700_ct(self):
        self.assertEqual(MAINTENANCE_BREAK_CT, (16, 17))

    def test_inside_the_break(self):
        self.assertTrue(is_in_maintenance_break(ct("2026-08-12 16:30")))
        self.assertTrue(is_in_maintenance_break(ct("2026-08-12 16:00")))

    def test_outside_the_break(self):
        self.assertFalse(is_in_maintenance_break(ct("2026-08-12 15:59")))
        self.assertFalse(is_in_maintenance_break(ct("2026-08-12 17:00")))

    def test_the_roll_happens_at_the_end_of_the_break_not_the_start(self):
        self.assertEqual(trade_date(ct("2026-08-12 16:30")), date(2026, 8, 12))
        self.assertEqual(trade_date(ct("2026-08-12 17:00")), date(2026, 8, 13))


class TestDstTransitions(unittest.TestCase):
    """Both 2026/27 transitions fall inside the Phase 16 window."""

    def test_cdt_session_opens_at_2200_utc(self):
        self.assertEqual(session_open_utc_ms(date(2026, 8, 10)), utc("2026-08-09 22:00"))

    def test_cst_session_opens_at_2300_utc(self):
        self.assertEqual(session_open_utc_ms(date(2026, 11, 3)), utc("2026-11-02 23:00"))

    def test_offsets_either_side_of_the_november_transition(self):
        self.assertEqual(utc_offset_minutes(utc("2026-10-30 18:00")), -300)  # CDT
        self.assertEqual(utc_offset_minutes(utc("2026-11-03 18:00")), -360)  # CST

    def test_offsets_either_side_of_the_march_transition(self):
        self.assertEqual(utc_offset_minutes(utc("2027-03-12 18:00")), -360)  # CST
        self.assertEqual(utc_offset_minutes(utc("2027-03-16 18:00")), -300)  # CDT

    def test_the_roll_hour_is_local_not_a_fixed_utc_offset(self):
        # Same local hour, different UTC instants across the transition.
        self.assertEqual(trade_date(ct("2026-10-30 17:00")), date(2026, 10, 31))
        self.assertEqual(trade_date(ct("2026-11-03 17:00")), date(2026, 11, 4))
        self.assertNotEqual(
            session_open_utc_ms(date(2026, 10, 30)) % 86_400_000,
            session_open_utc_ms(date(2026, 11, 4)) % 86_400_000,
        )

    def test_both_transitions_occur_while_the_market_is_shut(self):
        # US DST switches at 02:00 local on a Sunday; the market opens 17:00 CT.
        for transition in (date(2026, 11, 1), date(2027, 3, 14)):
            with self.subTest(transition):
                self.assertEqual(transition.weekday(), 6)
                before = datetime.combine(transition, datetime.min.time(),
                                          tzinfo=CHICAGO)
                after = before + timedelta(hours=6)
                self.assertNotEqual(before.utcoffset(), after.utcoffset())
                # 02:00 local is inside the Friday-16:00 → Sunday-17:00 shutdown.
                self.assertLess(2, TRADE_DATE_ROLL_HOUR_CT)


class TestHolidays(unittest.TestCase):
    def test_full_closures_are_advisory_only(self):
        # Christmas Day 2026 has no session, but labelling is still total.
        self.assertTrue(is_full_closure(date(2026, 12, 25)))
        self.assertEqual(trade_date(ct("2026-12-24 18:00")), date(2026, 12, 25))

    def test_the_first_bar_after_the_christmas_shutdown_labels_monday(self):
        # Market reopens Sunday 2026-12-27 17:00 CT → Monday 2026-12-28.
        self.assertEqual(trade_date(ct("2026-12-27 17:00")), date(2026, 12, 28))
        self.assertFalse(is_full_closure(date(2026, 12, 28)))

    def test_early_close_does_not_move_the_boundary(self):
        # Thanksgiving 2026 closes early; the trade date is unaffected.
        self.assertTrue(is_early_close(date(2026, 11, 26)))
        self.assertEqual(trade_date(ct("2026-11-25 17:00")), date(2026, 11, 26))
        self.assertEqual(trade_date(ct("2026-11-26 12:00")), date(2026, 11, 26))
        self.assertEqual(trade_date(ct("2026-11-26 17:00")), date(2026, 11, 27))

    def test_memorial_day_falls_inside_the_research_window(self):
        self.assertTrue(is_early_close(date(2026, 5, 25)))
        self.assertEqual(trade_date(ct("2026-05-24 17:00")), date(2026, 5, 25))

    def test_holiday_sets_are_disjoint_and_within_coverage(self):
        self.assertFalse(CME_FULL_CLOSURES & CME_EARLY_CLOSES)
        for d in CME_FULL_CLOSURES | CME_EARLY_CLOSES:
            self.assertLess(d.weekday(), 5, f"{d} is a weekend")


class TestDeterminismAndInputHandling(unittest.TestCase):
    def test_repeated_calls_agree(self):
        ts = ct("2026-08-12 17:00")
        self.assertEqual([trade_date(ts) for _ in range(5)], [date(2026, 8, 13)] * 5)

    def test_no_roll_reported_on_the_first_bar(self):
        # Pine's ta.change is na on bar 0, so the if-branch does not execute.
        self.assertFalse(is_trade_date_roll(None, ct("2026-08-12 17:00")))

    def test_roll_only_when_the_label_changes(self):
        a, b = ct("2026-08-12 16:55"), ct("2026-08-12 17:00")
        self.assertTrue(is_trade_date_roll(a, b))
        self.assertFalse(is_trade_date_roll(b, ct("2026-08-12 17:05")))

    def test_malformed_timestamps_are_rejected(self):
        for bad in ("1782864000000", 1.5, True, None):
            with self.subTest(bad=bad):
                with self.assertRaises(SessionCalendarError):
                    trade_date(bad)

    def test_module_reads_no_data_source(self):
        from pathlib import Path
        import bot.calendar.cme as cme
        source = Path(cme.__file__).read_text(encoding="utf-8")
        for forbidden in ("open(", "requests", "urllib", "socket", "now()", "today()"):
            self.assertNotIn(forbidden, source, f"calendar must not use {forbidden}")


class TestAgreesWithTheCommittedResearchRecords(unittest.TestCase):
    """The rule must match the session boundaries visible in the A2 fixtures.

    This is what makes 17:00 CT an established fact for *this* data rather than
    a quoted hours table. No new market data is read: these are the already
    consumed Phase 13F/14 records.
    """

    FIXTURES = load_all()

    def _timestamps(self):
        for fx in self.FIXTURES:
            for fill in fx["fills"]:
                rec = fill["recorded"]
                for key in ("sweep_ts_ms", "choch_ts_ms", "retest_ts_ms",
                            "bos_ts_ms", "entry_ts_ms"):
                    yield rec[key]

    def test_no_recorded_timestamp_falls_in_the_maintenance_break(self):
        offenders = [t for t in self._timestamps() if is_in_maintenance_break(t)]
        self.assertEqual(offenders, [])

    def test_no_recorded_timestamp_falls_on_a_saturday_ct(self):
        offenders = [t for t in self._timestamps()
                     if datetime.fromtimestamp(t / 1000, CHICAGO).weekday() == 5]
        self.assertEqual(offenders, [])

    def test_earliest_sunday_activity_is_exactly_the_1700_ct_open(self):
        sundays = [datetime.fromtimestamp(t / 1000, CHICAGO) for t in self._timestamps()
                   if datetime.fromtimestamp(t / 1000, CHICAGO).weekday() == 6]
        self.assertTrue(sundays)
        self.assertEqual(min(d.hour * 60 + d.minute for d in sundays),
                         TRADE_DATE_ROLL_HOUR_CT * 60)

    def test_every_sunday_timestamp_is_labelled_monday(self):
        for t in self._timestamps():
            local = datetime.fromtimestamp(t / 1000, CHICAGO)
            if local.weekday() == 6:
                with self.subTest(local.isoformat()):
                    self.assertEqual(trade_date(t).weekday(), 0)

    def test_fold_c_coverage_starts_at_a_session_open(self):
        fold_c = next(f for f in self.FIXTURES if f["cell"]["fold"] == "C")
        start = fold_c["coverage"]["start_ms"]
        self.assertEqual(start, session_open_utc_ms(trade_date(start)))
        self.assertEqual(start, utc("2026-08-09 22:00"))

    def test_fold_b_coverage_ends_at_the_friday_close(self):
        fold_b = next(f for f in self.FIXTURES if f["cell"]["fold"] == "B")
        end = fold_b["coverage"]["end_ms"]  # last 5m bar OPEN
        self.assertEqual(end + 300_000, session_close_utc_ms(trade_date(end)))
        self.assertEqual(datetime.fromtimestamp(end / 1000, CHICAGO).weekday(), 4)


if __name__ == "__main__":
    unittest.main()

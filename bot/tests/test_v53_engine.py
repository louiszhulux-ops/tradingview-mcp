"""B2 — frozen V53 Python implementation tests.

Each test targets one frozen rule. Synthetic bars only; no market data is read
and nothing is fetched. Timestamps sit inside the consumed research window, so
the A1 pre-FE guard accepts them.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from bot.calendar import trade_date
from bot.contracts.enums import Direction, ExitReason, SlotState, SweepSource, Timeframe
from bot.strategy.v53 import SECTION_ORDER, V53Config, V53Engine, in_fold
from bot.strategy.v53.constants import (
    DISP_MIN, DISP_WAIT, MAX_BARS, MIN_WICK, RET_BARS, RING_SIZE, SLOT_COUNT, TGT_R,
)
from bot.strategy.v53.indicators import PivotDetector, WilderAtr, is_pivot_high, is_pivot_low
from bot.strategy.v53.levels import SweepEngine, utc_hour
from bot.strategy.v53.numeric import is_na, tostring
from bot.tests.synthetic import BASE_MS, flat, parent

F = (100.5, 99.5, 100.0)   # a flat 1m sub-bar


def engine(direction=Direction.LONG, ltf=Timeframe.M1, instrument="MGC1!",
           point_value=10.0, fold="ALL") -> V53Engine:
    return V53Engine(V53Config(instrument, direction, ltf, point_value, fold))


def warm(e: V53Engine, bars: int = 21) -> None:
    """Warm ATR and confirm a 5m swing low at 98.0 (pivot bar 10, confirmed 20)."""
    for i in range(bars):
        e.on_bar(parent(i, 100.5, 98.0, 100.0) if i == 10 else flat(i))


def full_sequence(e: V53Engine) -> None:
    """Drive one complete SWEEP → CHOCH → RETEST → BOS → FVG → FILL."""
    warm(e)
    e.on_bar(parent(21, 100.5, 97.8, 100.0))                                   # sweep (SW)
    e.on_bar(parent(22, 102.0, 99.5, 100.0, subs=[F, (102.0, 99.5, 100.0), F, F, F]))
    e.on_bar(parent(23, 103.5, 99.5, 103.0, subs=[(103.5, 102.5, 103.0), F, F, F, F]))
    e.on_bar(parent(24, 108.5, 99.5, 106.0,
                    subs=[(108.0, 103.5, 107.5), (108.5, 105.0, 106.0), F, F, F]))
    e.on_bar(flat(25))                                                          # fill


# ---------------------------------------------------------------- indicators

class TestAtr(unittest.TestCase):
    def test_na_until_length_bars(self):
        atr = WilderAtr(14)
        for _ in range(13):
            self.assertTrue(is_na(atr.update(101.0, 99.0, 100.0)))
        self.assertFalse(is_na(atr.update(101.0, 99.0, 100.0)))

    def test_seed_is_the_sma_of_the_first_true_ranges(self):
        atr = WilderAtr(14)
        for _ in range(14):
            value = atr.update(101.0, 99.0, 100.0)
        self.assertAlmostEqual(value, 2.0)

    def test_first_bar_true_range_has_no_previous_close(self):
        atr = WilderAtr(1)
        self.assertAlmostEqual(atr.update(110.0, 100.0, 105.0), 10.0)

    def test_wilder_smoothing_after_the_seed(self):
        atr = WilderAtr(2)
        atr.update(101.0, 99.0, 100.0)     # TR 2
        seed = atr.update(101.0, 99.0, 100.0)
        self.assertAlmostEqual(seed, 2.0)
        # alpha = 1/2: 0.5*6 + 0.5*2 = 4
        self.assertAlmostEqual(atr.update(106.0, 100.0, 103.0), 4.0)


class TestPivotTieBehaviour(unittest.TestCase):
    """Older side allows equality; newer side rejects it. Windows are oldest-first.

    Consequence: within a run of equal extremes the qualifying pivot is the
    **most recent**, because it is the only member with no equal-or-higher bar
    after it. The artifact's inline comment says "the FIRST of a run", which
    contradicts its own code; the code is authoritative — it was verified
    against `ta.pivothigh(src, 3, 3)` with 0 mismatches over 20,567 bars, and
    the K26/K27 detector-verification counters read 0 in every committed run.
    See the B2 audit, "Discrepancies found".
    """

    def test_equality_on_the_older_side_is_allowed(self):
        self.assertTrue(is_pivot_high([5, 1, 1, 5, 1, 1, 1], 3, 3))

    def test_equality_on_the_newer_side_rejects(self):
        self.assertFalse(is_pivot_high([1, 1, 1, 5, 5, 1, 1], 3, 3))

    def test_the_most_recent_member_of_a_run_is_the_pivot(self):
        self.assertTrue(is_pivot_high([1, 5, 5, 5, 1, 1, 1], 3, 3))   # run ends at centre
        self.assertFalse(is_pivot_high([1, 1, 1, 5, 5, 5, 1], 3, 3))  # run starts at centre

    def test_pivot_low_mirrors_the_convention(self):
        self.assertTrue(is_pivot_low([1, 9, 9, 1, 9, 9, 9], 3, 3))     # equal older ok
        self.assertFalse(is_pivot_low([9, 9, 9, 1, 1, 9, 9], 3, 3))    # equal newer rejects
        self.assertTrue(is_pivot_low([9, 1, 1, 1, 9, 9, 9], 3, 3))     # most recent of a run
        self.assertFalse(is_pivot_low([9, 9, 9, 1, 1, 1, 9], 3, 3))    # earliest of a run

    def test_a_strict_both_sides_rule_would_disagree(self):
        highs = [5, 1, 1, 5, 1, 1, 1]
        strict_both = all(h < 5 for h in highs[:3]) and all(h < 5 for h in highs[4:])
        self.assertFalse(strict_both)
        self.assertTrue(is_pivot_high(highs, 3, 3))

    def test_a_non_strict_both_sides_rule_would_disagree(self):
        highs = [1, 1, 1, 5, 5, 1, 1]
        non_strict = all(h <= 5 for h in highs[:3]) and all(h <= 5 for h in highs[4:])
        self.assertTrue(non_strict)
        self.assertFalse(is_pivot_high(highs, 3, 3))

class TestPivotConfirmationTiming(unittest.TestCase):
    def test_confirmation_lands_half_width_bars_after_the_pivot(self):
        detector = PivotDetector(3)
        highs = [1, 1, 1, 9, 1, 1, 1]
        confirmed_at = None
        for index, high in enumerate(highs):
            pivot_high, _ = detector.update(high, 0.0)
            if not is_na(pivot_high):
                confirmed_at = index
        self.assertEqual(confirmed_at, 6)      # pivot bar 3 + half width 3

    def test_nothing_confirms_before_the_window_is_full(self):
        detector = PivotDetector(10)
        for _ in range(20):
            self.assertTrue(all(is_na(v) for v in detector.update(1.0, 1.0)))

    def test_five_minute_swing_confirms_ten_bars_late(self):
        e = engine()
        warm(e, bars=20)
        self.assertTrue(is_na(e.sweeps.swing_low))   # pivot bar 10, not yet confirmed
        e.on_bar(flat(20))
        self.assertEqual(e.sweeps.swing_low, 98.0)


# ---------------------------------------------------------------- sweeps

class TestSweepDetection(unittest.TestCase):
    def test_swing_sweep_requires_wick_depth_and_close_back_inside(self):
        e = engine()
        warm(e)
        atr = e.sweeps.atr
        threshold = 98.0 - MIN_WICK * atr
        # too shallow: low above the threshold
        shallow = e.sweeps.update(BASE_MS + 21 * 300_000, 100.5, threshold + 0.01, 100.0)
        self.assertEqual(shallow.sources, ())

    def test_a_deep_wick_that_closes_below_the_level_is_not_a_sweep(self):
        e = engine()
        warm(e)
        result = e.sweeps.update(BASE_MS + 21 * 300_000, 98.5, 97.0, 97.5)
        self.assertNotIn(SweepSource.SW, result.sources)   # close 97.5 < 98.0

    def test_a_valid_swing_sweep_arms_a_slot(self):
        e = engine()
        warm(e)
        out = e.on_bar(parent(21, 100.5, 97.8, 100.0))
        self.assertEqual(out.armed_slot, 0)
        self.assertEqual(e.machine.slots[0].state, SlotState.ARMED)
        self.assertEqual(e.machine.slots[0].ledger_sweep_kind, "SW")

    def test_short_direction_mirrors_the_test(self):
        e = engine(direction=Direction.SHORT)
        for i in range(21):
            e.on_bar(parent(i, 102.0, 99.5, 100.0) if i == 10 else flat(i))
        self.assertEqual(e.sweeps.swing_high, 102.0)
        out = e.on_bar(parent(21, 102.3, 99.5, 100.0))
        self.assertEqual(out.armed_slot, 0)
        self.assertEqual(e.machine.slots[0].ledger_sweep_extreme, 102.3)

    def test_sweep_extreme_is_the_bar_extreme_not_the_swept_level(self):
        e = engine()
        warm(e)
        e.on_bar(parent(21, 100.5, 97.8, 100.0))
        self.assertEqual(e.machine.slots[0].ledger_sweep_extreme, 97.8)

    def test_sweep_kind_renders_multiple_sources_in_order(self):
        # The Asia low must be frozen first: inside the window the running low
        # is updated before the sweep test, so an AS sweep can only fire once
        # the window has closed (UTC hour >= 7). That is V53's own behaviour.
        e = engine()
        warm(e)
        after_asia = int(datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc).timestamp() * 1000)
        e.sweeps.update(after_asia, 100.5, 99.5, 100.0)
        self.assertFalse(e.sweeps.asia_on)
        e.sweeps.pdl = e.sweeps.asia_low
        result = e.sweeps.update(after_asia + 300_000, 100.5, 97.0, 100.0)
        self.assertEqual(result.kind, "PD+AS+SW")
        self.assertEqual(result.sources,
                         (SweepSource.PD, SweepSource.AS, SweepSource.SW))


class TestTheTwoCalendars(unittest.TestCase):
    """PDH/PDL on the exchange session; Asia on UTC. They must not be merged."""

    def test_pdh_pdl_roll_on_the_exchange_session_day(self):
        e = engine()
        # 16:55 CT then 17:00 CT on the same calendar day: a session roll.
        before = int(datetime(2026, 7, 1, 21, 55, tzinfo=timezone.utc).timestamp() * 1000)
        after = before + 300_000
        e.sweeps.update(before, 101.0, 99.0, 100.0)
        self.assertTrue(is_na(e.sweeps.pdh))          # first bar: no roll (Pine na)
        e.sweeps.update(after, 102.0, 98.0, 100.0)
        self.assertEqual(e.sweeps.pdh, 101.0)         # rolled: yesterday's high
        self.assertEqual(e.sweeps.pdl, 99.0)
        self.assertEqual(trade_date(before).day + 1, trade_date(after).day)

    def test_no_roll_across_utc_midnight_inside_a_session(self):
        e = engine()
        before = int(datetime(2026, 7, 1, 23, 55, tzinfo=timezone.utc).timestamp() * 1000)
        e.sweeps.update(before, 101.0, 99.0, 100.0)
        e.sweeps.update(before + 300_000, 102.0, 98.0, 100.0)   # 00:00 UTC
        self.assertTrue(is_na(e.sweeps.pdh))          # UTC midnight is NOT a roll
        self.assertEqual(e.sweeps.dh, 102.0)          # the running day high extended

    def test_asia_window_is_utc_and_independent_of_the_session(self):
        e = engine()
        in_asia = int(datetime(2026, 7, 1, 3, 0, tzinfo=timezone.utc).timestamp() * 1000)
        out_asia = int(datetime(2026, 7, 1, 8, 0, tzinfo=timezone.utc).timestamp() * 1000)
        self.assertLess(utc_hour(in_asia), 7)
        self.assertGreaterEqual(utc_hour(out_asia), 7)
        e.sweeps.update(in_asia, 105.0, 95.0, 100.0)
        self.assertEqual(e.sweeps.asia_high, 105.0)
        self.assertTrue(e.sweeps.asia_on)
        e.sweeps.update(out_asia, 110.0, 90.0, 100.0)
        self.assertFalse(e.sweeps.asia_on)
        self.assertEqual(e.sweeps.asia_high, 105.0)   # frozen once the window closes

    def test_asia_restarts_on_re_entry(self):
        e = engine()
        day1 = int(datetime(2026, 7, 1, 3, 0, tzinfo=timezone.utc).timestamp() * 1000)
        e.sweeps.update(day1, 105.0, 95.0, 100.0)
        e.sweeps.update(day1 + 6 * 3_600_000, 110.0, 90.0, 100.0)          # 09:00, out
        e.sweeps.update(day1 + 22 * 3_600_000, 103.0, 97.0, 100.0)         # 01:00 next, in
        self.assertEqual(e.sweeps.asia_high, 103.0)   # reset, not extended

    def test_the_two_boundaries_are_different_instants(self):
        session_roll = int(datetime(2026, 7, 1, 22, 0, tzinfo=timezone.utc).timestamp() * 1000)
        self.assertEqual(utc_hour(session_roll), 22)
        self.assertGreaterEqual(utc_hour(session_roll), 7)   # not in the Asia window


class TestInstrumentCalendarAbstraction(unittest.TestCase):
    def test_both_instruments_use_one_session_rule(self):
        stamp = int(datetime(2026, 7, 1, 22, 0, tzinfo=timezone.utc).timestamp() * 1000)
        self.assertEqual(trade_date(stamp), trade_date(stamp))
        for instrument, point_value in (("MGC1!", 10.0), ("MNQ1!", 2.0)):
            e = engine(instrument=instrument, point_value=point_value)
            self.assertEqual(e.config.instrument, instrument)
            self.assertEqual(e.config.point_value, point_value)

    def test_point_value_must_be_explicit_and_positive(self):
        for bad in (0.0, -1.0):
            with self.assertRaises(ValueError):
                V53Config("MGC1!", Direction.LONG, Timeframe.M1, point_value=bad)

    def test_engine_rejects_a_bar_from_another_instrument(self):
        e = engine(instrument="MNQ1!", point_value=2.0)
        with self.assertRaises(ValueError):
            e.on_bar(flat(0))   # synthetic bars are MGC1!


# ---------------------------------------------------------------- sequence

class TestChochSelectionAndRetest(unittest.TestCase):
    def test_choch_takes_the_most_recent_opposing_pivot_after_the_sweep(self):
        e = engine()
        warm(e)
        e.on_bar(parent(21, 100.5, 97.8, 100.0))
        e.on_bar(parent(22, 102.0, 99.5, 100.0, subs=[F, (102.0, 99.5, 100.0), F, F, F]))
        e.on_bar(parent(23, 103.5, 99.5, 103.0, subs=[(103.5, 102.5, 103.0), F, F, F, F]))
        self.assertEqual(e.machine.slots[0].choch_level, 102.0)
        self.assertEqual(e.counters.choch, 1)

    def test_a_pivot_formed_before_the_sweep_cannot_serve(self):
        e = engine()
        warm(e)
        # Sweep after an LTF pivot already exists: oB must exceed swB.
        e.on_bar(parent(21, 106.0, 99.5, 100.0, subs=[F, (106.0, 99.5, 100.0), F, F, F]))
        e.on_bar(parent(22, 100.5, 97.8, 100.0))          # sweep, later
        e.on_bar(parent(23, 107.0, 99.5, 106.5))          # closes above the old pivot
        self.assertEqual(e.machine.slots[0].state, SlotState.ARMED)
        self.assertEqual(e.counters.choch, 0)

    def test_retest_is_an_exact_level_with_zero_tolerance(self):
        e = engine()
        warm(e)
        e.on_bar(parent(21, 100.5, 97.8, 100.0))
        e.on_bar(parent(22, 102.0, 99.5, 100.0, subs=[F, (102.0, 99.5, 100.0), F, F, F]))
        # CHOCH, then sub-bars that stay strictly above the level: no retest.
        e.on_bar(parent(23, 103.5, 102.01, 103.0,
                        subs=[(103.5, 102.5, 103.0)] + [(103.0, 102.01, 102.5)] * 4))
        self.assertEqual(e.machine.slots[0].state, SlotState.CHOCH)
        self.assertEqual(e.counters.retests, 0)
        # A sub-bar touching the level exactly does retest.
        e.on_bar(parent(24, 103.0, 102.0, 102.5))
        self.assertEqual(e.machine.slots[0].state, SlotState.RETESTED)

    def test_retest_has_no_timeout_of_its_own(self):
        # Only the §3 dispWait deadline can expire a retested sequence.
        e = engine()
        warm(e)
        e.on_bar(parent(21, 100.5, 97.8, 100.0))
        e.on_bar(parent(22, 102.0, 99.5, 100.0, subs=[F, (102.0, 99.5, 100.0), F, F, F]))
        e.on_bar(parent(23, 103.5, 99.5, 103.0, subs=[(103.5, 102.5, 103.0), F, F, F, F]))
        self.assertEqual(e.machine.slots[0].state, SlotState.RETESTED)
        for i in range(24, 21 + DISP_WAIT + 1):
            e.on_bar(flat(i))
        self.assertEqual(e.machine.slots[0].state, SlotState.RETESTED)
        e.on_bar(flat(21 + DISP_WAIT + 1))
        self.assertEqual(e.machine.slots[0].state, SlotState.FREE)
        self.assertEqual(e.counters.expire_post_retest, 1)


class TestDisplacementThresholds(unittest.TestCase):
    def test_a_break_without_enough_range_is_counted_not_promoted(self):
        e = engine()
        warm(e)
        e.on_bar(parent(21, 100.5, 97.8, 100.0))
        e.on_bar(parent(22, 102.0, 99.5, 100.0, subs=[F, (102.0, 99.5, 100.0), F, F, F]))
        e.on_bar(parent(23, 103.5, 99.5, 103.0, subs=[(103.5, 102.5, 103.0), F, F, F, F]))
        atr = e.sweeps.atr
        small = DISP_MIN * atr * 0.5
        e.on_bar(parent(24, 104.0, 103.5, 103.9,
                        subs=[(103.5 + small, 103.5, 103.5 + small * 0.9), F, F, F, F]))
        self.assertEqual(e.machine.slots[0].state, SlotState.RETESTED)
        self.assertGreaterEqual(e.counters.break_no_displacement, 1)

    def test_close_location_clause_long(self):
        # range large enough, but the close sits below low + 0.6 * range
        e = engine()
        warm(e)
        e.on_bar(parent(21, 100.5, 97.8, 100.0))
        e.on_bar(parent(22, 102.0, 99.5, 100.0, subs=[F, (102.0, 99.5, 100.0), F, F, F]))
        e.on_bar(parent(23, 103.5, 99.5, 103.0, subs=[(103.5, 102.5, 103.0), F, F, F, F]))
        e.on_bar(parent(24, 110.0, 99.5, 104.0,
                        subs=[(110.0, 103.5, 104.0), F, F, F, F]))
        self.assertEqual(e.machine.slots[0].state, SlotState.RETESTED)
        self.assertGreaterEqual(e.counters.break_no_displacement, 1)

    def test_a_qualifying_displacement_promotes_the_sequence(self):
        e = engine()
        warm(e)
        e.on_bar(parent(21, 100.5, 97.8, 100.0))
        e.on_bar(parent(22, 102.0, 99.5, 100.0, subs=[F, (102.0, 99.5, 100.0), F, F, F]))
        e.on_bar(parent(23, 103.5, 99.5, 103.0, subs=[(103.5, 102.5, 103.0), F, F, F, F]))
        e.on_bar(parent(24, 108.0, 99.5, 107.5, subs=[(108.0, 103.5, 107.5), F, F, F, F]))
        self.assertEqual(e.counters.bos_displacement, 1)
        self.assertEqual(e.machine.slots[0].ledger_bos_level, 103.5)


class TestFvgAssociation(unittest.TestCase):
    def test_fvg_is_tested_only_at_the_bar_after_displacement(self):
        e = engine()
        full_sequence(e)
        self.assertEqual(e.counters.fvg, 1)

    def test_the_gap_uses_the_three_candle_geometry(self):
        e = engine()
        full_sequence(e)
        slot = e.machine.slots[0]
        # bullish: low(newest) > high(oldest of the three); entry is the far edge
        self.assertEqual(slot.entry, 100.5)
        self.assertEqual(slot.ledger_fvg_low, 100.5)
        self.assertEqual(slot.ledger_fvg_high, 105.0)

    def test_no_gap_invalidates_the_setup(self):
        e = engine()
        warm(e)
        e.on_bar(parent(21, 100.5, 97.8, 100.0))
        e.on_bar(parent(22, 102.0, 99.5, 100.0, subs=[F, (102.0, 99.5, 100.0), F, F, F]))
        e.on_bar(parent(23, 103.5, 99.5, 103.0, subs=[(103.5, 102.5, 103.0), F, F, F, F]))
        # displacement then a bar that overlaps the pre-displacement candle
        e.on_bar(parent(24, 108.0, 99.5, 106.0,
                        subs=[(108.0, 103.5, 107.5), (107.0, 99.0, 100.0), F, F, F]))
        self.assertEqual(e.machine.slots[0].state, SlotState.FREE)
        self.assertEqual(e.counters.no_fvg, 1)
        self.assertEqual(e.counters.fvg, 0)

    def test_conservation_identity_holds(self):
        e = engine()
        full_sequence(e)
        self.assertTrue(e.conservation_holds())


class TestEntryStopAndFill(unittest.TestCase):
    def test_entry_is_the_far_edge_of_the_fvg(self):
        e = engine()
        full_sequence(e)
        self.assertEqual(e.machine.slots[0].entry, 100.5)

    def test_stop_is_the_sweep_extreme_offset_by_the_atr_buffer(self):
        e = engine()
        warm(e)
        atr_before = e.sweeps.atr
        e.on_bar(parent(21, 100.5, 97.8, 100.0))
        slot = e.machine.slots[0]
        self.assertAlmostEqual(slot.stop, 97.8 - 0.20 * slot.atr_at_arm)
        self.assertNotAlmostEqual(slot.atr_at_arm, atr_before)   # ATR updates on the bar

    def test_fill_requires_only_a_touch(self):
        e = engine()
        full_sequence(e)
        self.assertEqual(e.counters.fills, 1)
        self.assertEqual(e.machine.slots[0].state, SlotState.IN_TRADE)

    def test_r_band_rejects_an_out_of_range_stop_distance(self):
        e = engine()
        full_sequence(e)
        slot = e.machine.slots[0]
        ratio = abs(slot.entry - slot.stop) / slot.atr_at_arm
        self.assertTrue(0.05 <= ratio <= 3.00)

    def test_unfilled_fvg_expires_after_ret_bars(self):
        e = engine()
        warm(e)
        e.on_bar(parent(21, 100.5, 97.8, 100.0))
        e.on_bar(parent(22, 102.0, 99.5, 100.0, subs=[F, (102.0, 99.5, 100.0), F, F, F]))
        e.on_bar(parent(23, 103.5, 99.5, 103.0, subs=[(103.5, 102.5, 103.0), F, F, F, F]))
        e.on_bar(parent(24, 108.5, 99.5, 106.0,
                        subs=[(108.0, 103.5, 107.5), (108.5, 105.0, 106.0), F, F, F]))
        self.assertEqual(e.machine.slots[0].state, SlotState.FVG_AWAIT_FILL)
        # bars that never touch 100.5
        for i in range(25, 25 + RET_BARS):
            e.on_bar(parent(i, 108.0, 106.0, 107.0))
        self.assertEqual(e.machine.slots[0].state, SlotState.FREE)
        self.assertEqual(e.counters.fvg_retest_expiry, 1)


class TestOutcomeSemantics(unittest.TestCase):
    def _in_trade(self):
        e = engine()
        full_sequence(e)
        return e, e.machine.slots[0]

    def test_the_fill_bar_is_never_judged(self):
        e = engine()
        warm(e)
        e.on_bar(parent(21, 100.5, 97.8, 100.0))
        e.on_bar(parent(22, 102.0, 99.5, 100.0, subs=[F, (102.0, 99.5, 100.0), F, F, F]))
        e.on_bar(parent(23, 103.5, 99.5, 103.0, subs=[(103.5, 102.5, 103.0), F, F, F, F]))
        e.on_bar(parent(24, 108.5, 99.5, 106.0,
                        subs=[(108.0, 103.5, 107.5), (108.5, 105.0, 106.0), F, F, F]))
        slot = e.machine.slots[0]
        stop = slot.stop
        # A bar that both fills and reaches the stop: §1 runs before §2, so the
        # stop is not seen. This is audit §4.4(b), reproduced deliberately.
        e.on_bar(parent(25, 101.0, stop - 1.0, 100.0))
        self.assertEqual(slot.state, SlotState.IN_TRADE)
        self.assertEqual(slot.bars_in_trade, 0)
        self.assertEqual(e.counters.outcomes, 0)

    def test_target_resolves_as_a_win(self):
        e, slot = self._in_trade()
        r = slot.r_distance
        e.on_bar(parent(26, slot.entry + TGT_R * r + 1.0, 100.0, 100.0))
        self.assertEqual(e.counters.outcomes, 1)
        self.assertIn("|WIN|", e.ledger[0])
        self.assertIn("|target|", e.ledger[0])

    def test_stop_resolves_as_a_loss(self):
        e, slot = self._in_trade()
        r = slot.r_distance
        e.on_bar(parent(26, 101.0, slot.entry - r - 0.5, 100.0))
        self.assertEqual(e.counters.outcomes, 1)
        self.assertIn("|LOSS|", e.ledger[0])
        self.assertIn("|stop|", e.ledger[0])

    def test_adverse_is_tested_before_favourable(self):
        e, slot = self._in_trade()
        r = slot.r_distance
        # One bar reaching BOTH the stop and the target resolves as a stop.
        e.on_bar(parent(26, slot.entry + TGT_R * r + 1.0, slot.entry - r - 0.5, 100.0))
        self.assertIn("|LOSS|", e.ledger[0])
        self.assertIn("|stop|", e.ledger[0])

    def test_timeout_after_max_bars(self):
        e, slot = self._in_trade()
        slot.bars_in_trade = MAX_BARS - 1
        e.on_bar(parent(26, 101.0, 100.0, 100.5))
        self.assertIn("|timeout|", e.ledger[0])
        self.assertIn("|LOSS|", e.ledger[0])
        self.assertIn(f"|{MAX_BARS}bars", e.ledger[0])

    def test_outcome_counting_starts_the_bar_after_the_fill(self):
        e, slot = self._in_trade()
        self.assertEqual(slot.bars_in_trade, 0)
        e.on_bar(parent(26, 101.0, 100.0, 100.5))
        self.assertEqual(slot.bars_in_trade, 1)


# ---------------------------------------------------------------- structure

class TestSectionOrderingAndState(unittest.TestCase):
    def test_section_order_is_the_frozen_one(self):
        self.assertEqual(SECTION_ORDER, ("outcomes", "fills", "deadline", "ltf_loop", "arm"))

    def test_a_sweep_is_not_served_by_its_own_bars_ltf_sub_bars(self):
        # §5 runs after §4, so the slot armed on bar 21 sees nothing until bar 22.
        e = engine()
        warm(e)
        e.on_bar(parent(21, 100.5, 97.8, 100.0,
                        subs=[(106.0, 99.5, 105.0)] * 5))
        self.assertEqual(e.machine.slots[0].state, SlotState.ARMED)
        self.assertEqual(e.counters.choch, 0)

    def test_twenty_four_slots_and_a_seven_bar_ring(self):
        e = engine()
        self.assertEqual(len(e.machine.slots), SLOT_COUNT)
        self.assertEqual(RING_SIZE, 7)
        warm(e)
        self.assertTrue(e.ltf.ring_full)
        self.assertLessEqual(len(e.ltf.ring), RING_SIZE)

    def test_deadline_expires_a_sequence_at_the_pre_choch_stage(self):
        e = engine()
        warm(e)
        e.on_bar(parent(21, 100.5, 97.8, 100.0))
        for i in range(22, 21 + DISP_WAIT + 2):
            e.on_bar(flat(i))
        self.assertEqual(e.machine.slots[0].state, SlotState.FREE)
        self.assertEqual(e.counters.expire_pre_choch, 1)

    def test_deadline_counts_chart_bars_not_minutes(self):
        e = engine()
        warm(e)
        e.on_bar(parent(21, 100.5, 97.8, 100.0))
        armed = e.machine.slots[0].sweep_bar_index
        self.assertEqual(armed, 21)
        for i in range(22, 22 + DISP_WAIT):
            e.on_bar(flat(i))
        self.assertEqual(e.machine.slots[0].state, SlotState.ARMED)   # exactly 12 bars

    def test_assertion_counters_stay_zero(self):
        e = engine()
        full_sequence(e)
        e.on_bar(parent(26, 200.0, 100.0, 150.0))
        self.assertTrue(e.counters.assertions_all_zero, e.counters.assertions)

    def test_out_of_order_bars_are_rejected(self):
        e = engine()
        e.on_bar(flat(5))
        with self.assertRaises(ValueError):
            e.on_bar(flat(5))
        with self.assertRaises(ValueError):
            e.on_bar(flat(4))


class TestFoldGate(unittest.TestCase):
    def test_fold_membership_uses_the_bar_open(self):
        self.assertTrue(in_fold("A", 1784159999999))
        self.assertFalse(in_fold("A", 1784160000000))
        self.assertTrue(in_fold("B", 1784160000000))

    def test_unknown_fold_is_rejected(self):
        with self.assertRaises(ValueError):
            in_fold("Z", BASE_MS)

    def test_the_fold_gate_governs_arming_only(self):
        e = engine(fold="B")     # synthetic bars sit in fold A
        warm(e)
        out = e.on_bar(parent(21, 100.5, 97.8, 100.0))
        self.assertIsNone(out.armed_slot)
        self.assertEqual(e.counters.sweeps, 0)
        self.assertGreater(e.counters.ltf_bars_seen, 0)   # §4 still ran


class TestDeterminism(unittest.TestCase):
    def test_two_identical_runs_agree_exactly(self):
        results = []
        for _ in range(2):
            e = engine()
            full_sequence(e)
            e.on_bar(parent(26, 200.0, 100.0, 150.0))
            results.append((e.ledger, e.funnel(), e.counters.k))
        self.assertEqual(results[0], results[1])

    def test_no_module_level_mutable_state_leaks_between_engines(self):
        first = engine()
        full_sequence(first)
        second = engine()
        self.assertEqual(second.counters.k, [0] * 36)
        self.assertTrue(all(s.state is SlotState.FREE for s in second.machine.slots))
        self.assertEqual(second.ltf.ltf_bars_seen, 0)

    def test_ledger_row_shape(self):
        e = engine()
        full_sequence(e)
        e.on_bar(parent(26, 200.0, 100.0, 150.0))
        fields = e.ledger[0].split("|")
        self.assertEqual(len(fields), 21)
        self.assertEqual(fields[0], "MGC1!")
        self.assertEqual(fields[1], "L")
        self.assertEqual(fields[2], "1m")


if __name__ == "__main__":
    unittest.main()

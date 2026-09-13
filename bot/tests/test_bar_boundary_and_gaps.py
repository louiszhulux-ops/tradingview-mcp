"""Two contract fixes the real Phase C data forced, pinned.

Both were corrections to assumptions the contract made that the recorded market
does not honour. Neither changes a strategy rule; both only stop valid source
bars from being rejected.
"""

from __future__ import annotations

import unittest
from decimal import Decimal as D

from bot.contracts.enums import Direction, Timeframe
from bot.data.bars import Bar, BarContractError, ParentBar
from bot.guards import FE_MS, HeldOutDataError
from bot.strategy.v53.engine import V53Config, V53Engine

T0 = 1782864000000
MIN = 60_000


def sub(offset_min: int, *, inst="MGC1!", tf=Timeframe.M1, high="10", low="8",
        close="9", open_=None, parent_open=T0) -> Bar:
    start = parent_open + offset_min * MIN
    return Bar(inst, tf, start, start + tf.minutes * MIN,
               open_, D(high), D(low), D(close))


def parent5(*, open_ts=T0) -> Bar:
    return Bar("MGC1!", Timeframe.M5, open_ts, open_ts + 5 * MIN,
               None, D("10"), D("8"), D("9"))


class A_ParentBarOrdering(unittest.TestCase):
    """Ordering and non-overlap are required; contiguity is not."""

    def test_strictly_increasing_sub_bars_are_accepted(self):
        p = ParentBar(parent5(), Timeframe.M1, tuple(sub(i) for i in range(5)))
        self.assertEqual(p.ltf_count, 5)
        self.assertTrue(p.ltf_complete)

    def test_a_tradeless_minute_inside_the_parent_is_permitted(self):
        """Three MGC parents in data/phase_c_ltf look exactly like this."""
        for offsets in ([0, 1, 2, 4], [0, 1, 3, 4], [0, 2, 3, 4]):
            with self.subTest(offsets=offsets):
                p = ParentBar(parent5(), Timeframe.M1,
                              tuple(sub(i) for i in offsets))
                self.assertEqual(p.ltf_count, 4)
                self.assertFalse(p.ltf_complete)

    def test_a_leading_gap_is_permitted(self):
        p = ParentBar(parent5(), Timeframe.M1, tuple(sub(i) for i in (2, 3, 4)))
        self.assertEqual(p.ltf_count, 3)

    def test_duplicate_sub_bars_are_rejected(self):
        with self.assertRaises(BarContractError):
            ParentBar(parent5(), Timeframe.M1, (sub(1), sub(1)))

    def test_out_of_order_sub_bars_are_rejected(self):
        with self.assertRaises(BarContractError):
            ParentBar(parent5(), Timeframe.M1, (sub(0), sub(2), sub(1)))

    def test_overlapping_sub_bars_are_rejected(self):
        overlapping = Bar("MGC1!", Timeframe.M3, T0 + MIN, T0 + 4 * MIN,
                          None, D("10"), D("8"), D("9"))
        with self.assertRaises(BarContractError):
            ParentBar(parent5(), Timeframe.M3, (overlapping, sub(2, tf=Timeframe.M3)))

    def test_a_sub_bar_outside_its_parent_is_still_rejected(self):
        with self.assertRaises(BarContractError):
            ParentBar(parent5(), Timeframe.M1, (sub(7),))

    def test_a_mixed_instrument_sub_bar_is_still_rejected(self):
        with self.assertRaises(BarContractError):
            ParentBar(parent5(), Timeframe.M1, (sub(0, inst="MNQ1!"),))

    def test_ohlc_validation_is_not_weakened_for_sub_bars(self):
        with self.assertRaises(BarContractError):
            ParentBar(parent5(), Timeframe.M1, (sub(0, high="8", low="10"),))
        with self.assertRaises(BarContractError):
            ParentBar(parent5(), Timeframe.M1, (sub(0, close="99"),))
        with self.assertRaises(BarContractError):
            ParentBar(parent5(), Timeframe.M1, (sub(0, open_=D("99")),))

    def test_a_malformed_sub_bar_is_still_rejected(self):
        with self.assertRaises(BarContractError):
            ParentBar(parent5(), Timeframe.M1, ("not a bar",))
        with self.assertRaises(BarContractError):
            ParentBar(parent5(), Timeframe.M1, (sub(0, tf=Timeframe.M3),))


class B_FeBoundary(unittest.TestCase):
    """FE is exclusive, so a bar may close on it but never open on it."""

    def bar_at(self, open_ts, minutes=5):
        tf = {1: Timeframe.M1, 5: Timeframe.M5}[minutes]
        return Bar("MGC1!", tf, open_ts, open_ts + minutes * MIN,
                   None, D("10"), D("8"), D("9"))

    def test_a_bar_closing_exactly_at_fe_is_accepted(self):
        for minutes in (1, 5):
            with self.subTest(minutes=minutes):
                bar = self.bar_at(FE_MS - minutes * MIN, minutes)
                self.assertEqual(bar.close_ts_ms, FE_MS)
                self.assertLess(bar.open_ts_ms, FE_MS)

    def test_a_bar_opening_exactly_at_fe_is_rejected(self):
        with self.assertRaises(HeldOutDataError):
            self.bar_at(FE_MS)

    def test_a_bar_opening_after_fe_is_rejected(self):
        with self.assertRaises(HeldOutDataError):
            self.bar_at(FE_MS + 5 * MIN)

    def test_a_bar_closing_after_fe_is_rejected(self):
        with self.assertRaises(HeldOutDataError):
            Bar("MGC1!", Timeframe.M5, FE_MS - MIN, FE_MS + 4 * MIN,
                None, D("10"), D("8"), D("9"))

    def test_a_malformed_close_is_rejected_not_coerced(self):
        for value in (None, "x", 1.5, True):
            with self.subTest(value=value), self.assertRaises(BarContractError):
                Bar("MGC1!", Timeframe.M5, T0, value,
                    None, D("10"), D("8"), D("9"))


class C_NoStrategyImpact(unittest.TestCase):
    """The fixes admit valid bars; they change no strategy rule."""

    def engine(self):
        return V53Engine(V53Config(instrument="MGC1!", direction=Direction.LONG,
                                   ltf=Timeframe.M1, point_value=10.0, fold="A"))

    def test_a_gapped_parent_is_accepted_and_only_its_real_sub_bars_are_seen(self):
        engine = self.engine()
        p = ParentBar(parent5(), Timeframe.M1, tuple(sub(i) for i in (0, 1, 2, 4)))
        out = engine.on_bar(p)
        self.assertEqual(out.ltf_count, 4)

    def test_the_engine_still_refuses_incomplete_bars(self):
        incomplete = Bar("MGC1!", Timeframe.M5, T0, T0 + 5 * MIN,
                         None, D("10"), D("8"), D("9"), None, False)
        with self.assertRaises(ValueError):
            self.engine().on_bar(ParentBar(incomplete, Timeframe.M1, (sub(0),)))

    def test_the_engine_still_refuses_out_of_order_parents(self):
        engine = self.engine()
        engine.on_bar(ParentBar(parent5(open_ts=T0 + 5 * MIN), Timeframe.M1, ()))
        with self.assertRaises(ValueError):
            engine.on_bar(ParentBar(parent5(open_ts=T0), Timeframe.M1, ()))

    def test_frozen_constants_are_untouched(self):
        from bot.strategy.v53 import constants
        self.assertEqual(constants.DISP_WAIT, 12)
        self.assertEqual(constants.TGT_R, 5.0)
        self.assertEqual(constants.MAX_BARS, 144)
        self.assertEqual(constants.SLOT_COUNT, 24)
        self.assertEqual(
            constants.EXECUTED_SHA256,
            "2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6")


if __name__ == "__main__":
    unittest.main()

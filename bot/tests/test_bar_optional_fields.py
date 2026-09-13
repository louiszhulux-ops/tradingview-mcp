"""B1 amendment: `open` and `volume` are optional, absent is not zero."""

from __future__ import annotations

import unittest
from decimal import Decimal as D

from bot.contracts.enums import Timeframe
from bot.data.bars import (
    OPTIONAL_FIELDS, AbsentFieldError, Bar, BarContractError, ParentBar,
)
from bot.strategy.v53.engine import V53Config, V53Engine
from bot.contracts.enums import Direction

T0 = 1782864000000


def bar(open_=D("9.5"), volume=None, complete=True, tf=Timeframe.M5, ts=T0) -> Bar:
    return Bar("MGC1!", tf, ts, ts + tf.minutes * 60_000,
               open_, D("10"), D("8"), D("9"), volume, complete)


class OptionalOpen(unittest.TestCase):

    def test_1_bar_with_open_present(self):
        b = bar(D("9.5"))
        self.assertTrue(b.has_open)
        self.assertEqual(b.open, D("9.5"))
        self.assertEqual(b.require("open"), D("9.5"))

    def test_2_bar_with_open_absent(self):
        b = bar(None)
        self.assertFalse(b.has_open)
        self.assertIsNone(b.open)
        self.assertIsNone(b.to_dict()["open"])

    def test_2b_absent_is_not_zero(self):
        b = bar(None)
        self.assertIsNot(b.open, 0)
        self.assertNotEqual(b.open, D("0"))

    def test_3_invalid_present_open_outside_high_low(self):
        for value in (D("10.01"), D("7.99")):
            with self.subTest(value=value), self.assertRaises(BarContractError):
                bar(value)

    def test_3b_present_open_is_still_type_checked(self):
        with self.assertRaises(BarContractError):
            bar(9.5)          # float
        with self.assertRaises(BarContractError):
            bar("not-a-price")

    def test_4_reading_an_absent_open_raises(self):
        with self.assertRaises(AbsentFieldError) as ctx:
            bar(None).require("open")
        message = str(ctx.exception)
        self.assertIn("absent from the source dataset", message)
        self.assertIn("must not be defaulted", message)

    def test_4b_absent_field_error_is_a_bar_contract_error(self):
        self.assertTrue(issubclass(AbsentFieldError, BarContractError))

    def test_4c_require_covers_only_the_optional_fields(self):
        self.assertEqual(OPTIONAL_FIELDS, ("open", "volume"))
        with self.assertRaises(BarContractError):
            bar().require("close")

    def test_5_volume_absent(self):
        b = bar(volume=None)
        self.assertFalse(b.has_volume)
        self.assertIsNone(b.volume)
        with self.assertRaises(AbsentFieldError):
            b.require("volume")

    def test_5b_volume_present_is_still_validated(self):
        self.assertEqual(bar(volume=D("12")).require("volume"), D("12"))
        with self.assertRaises(BarContractError):
            bar(volume=D("-1"))

    def test_high_low_close_remain_mandatory(self):
        for index, name in ((5, "high"), (6, "low"), (7, "close")):
            fields = ["MGC1!", Timeframe.M5, T0, T0 + 300_000,
                      D("9.5"), D("10"), D("8"), D("9")]
            fields[index] = None
            with self.subTest(field=name), self.assertRaises(BarContractError):
                Bar(*fields)

    def test_unrelated_validation_is_unweakened(self):
        with self.assertRaises(BarContractError):
            Bar("MGC1!", Timeframe.M5, T0, T0 + 300_000,
                None, D("8"), D("10"), D("9"))        # low above high
        with self.assertRaises(BarContractError):
            Bar("MGC1!", Timeframe.M5, T0, T0 + 60_000,
                None, D("10"), D("8"), D("9"))        # wrong span
        with self.assertRaises(BarContractError):
            Bar("MGC1!", Timeframe.M5, T0, T0 + 300_000,
                None, D("10"), D("8"), D("99"))       # close outside bracket

    def test_frozen_5m_dataset_shape_is_representable(self):
        """The whole point of A9: timestamp,high,low,close and nothing else."""
        b = Bar("MGC1!", Timeframe.M5, 1779660000000, 1779660300000,
                None, D("4555.5"), D("4525.5"), D("4553"), None)
        self.assertFalse(b.has_open)
        self.assertFalse(b.has_volume)
        self.assertEqual(b.range, D("30"))


class IncompleteBarsNeverReachV53(unittest.TestCase):

    def engine(self) -> V53Engine:
        return V53Engine(V53Config(
            instrument="MGC1!", direction=Direction.LONG, ltf=Timeframe.M1,
            point_value=10.0, fold="A", cost_usd=3.0))

    def parent(self, complete=True, ltf_complete=True) -> ParentBar:
        sub = Bar("MGC1!", Timeframe.M1, T0, T0 + 60_000,
                  None, D("10"), D("8"), D("9"), None, ltf_complete)
        return ParentBar(bar(None, complete=complete), Timeframe.M1, (sub,))

    def test_incomplete_parent_is_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self.engine().on_bar(self.parent(complete=False))
        self.assertIn("incomplete", str(ctx.exception))

    def test_incomplete_ltf_sub_bar_is_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self.engine().on_bar(self.parent(ltf_complete=False))
        self.assertIn("incomplete", str(ctx.exception))

    def test_complete_bars_are_accepted(self):
        self.engine().on_bar(self.parent())

    def test_engine_never_reads_open(self):
        """V53 consumes high/low/close; a bar with no open drives it fine."""
        engine = self.engine()
        for index in range(3):
            ts = T0 + index * 300_000
            sub = Bar("MGC1!", Timeframe.M1, ts, ts + 60_000,
                      None, D("10"), D("8"), D("9"))
            parent = ParentBar(bar(None, ts=ts), Timeframe.M1, (sub,))
            engine.on_bar(parent)
        self.assertEqual(engine.bar_index, 2)


if __name__ == "__main__":
    unittest.main()

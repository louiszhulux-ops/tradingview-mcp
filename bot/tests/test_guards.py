"""Tests for the Phase 16 held-out-data guard.

The guard must fail closed: it accepts a timestamp only when that timestamp is
provably a valid, pre-FE epoch-millisecond integer.
"""

import unittest

from bot.guards import (
    FE_ISO,
    FE_MS,
    HeldOutDataError,
    InvalidTimestampError,
    assert_all_pre_fe,
    assert_pre_fe,
)


class TestFeBoundaryDefinition(unittest.TestCase):
    def test_fe_is_the_phase16_boundary(self):
        # Value asserted against the frozen research artifact, not re-derived.
        self.assertEqual(FE_MS, 1788134400000)  # GUARD-ALLOW: authoritative value assertion
        self.assertEqual(FE_ISO, "2026-08-31T00:00:00Z")

    def test_fe_is_a_plain_int(self):
        self.assertIsInstance(FE_MS, int)
        self.assertNotIsInstance(FE_MS, bool)


class TestAcceptsPreFe(unittest.TestCase):
    def test_pre_fe_timestamp_is_accepted(self):
        self.assertEqual(assert_pre_fe(FE_MS - 1), FE_MS - 1)

    def test_fold_a_era_timestamp_is_accepted(self):
        # 2026-07-01 00:00 UTC — inside the already-consumed research window.
        self.assertEqual(assert_pre_fe(1782864000000), 1782864000000)

    def test_returns_value_unchanged_for_inlining(self):
        self.assertEqual(assert_pre_fe(1782864000000), 1782864000000)


class TestRejectsAtAndAfterFe(unittest.TestCase):
    def test_exactly_fe_is_rejected(self):
        with self.assertRaises(HeldOutDataError) as ctx:
            assert_pre_fe(FE_MS)
        self.assertIn(str(FE_MS), str(ctx.exception))
        self.assertIn("forward-held-out", str(ctx.exception))

    def test_one_ms_after_fe_is_rejected(self):
        with self.assertRaises(HeldOutDataError):
            assert_pre_fe(FE_MS + 1)

    def test_well_after_fe_is_rejected(self):
        with self.assertRaises(HeldOutDataError):
            assert_pre_fe(FE_MS + 90 * 86_400_000)

    def test_rejection_is_not_an_invalid_timestamp_error(self):
        # Held-out data is a protocol violation, not a malformed input.
        with self.assertRaises(HeldOutDataError) as ctx:
            assert_pre_fe(FE_MS)
        self.assertNotIsInstance(ctx.exception, InvalidTimestampError)


class TestFailsClosedOnBadInput(unittest.TestCase):
    def test_missing_timestamp_is_rejected(self):
        with self.assertRaises(InvalidTimestampError) as ctx:
            assert_pre_fe(None)
        self.assertIn("missing timestamp", str(ctx.exception))

    def test_malformed_string_is_rejected(self):
        with self.assertRaises(InvalidTimestampError):
            assert_pre_fe("1782864000000")

    def test_float_is_rejected_not_coerced(self):
        with self.assertRaises(InvalidTimestampError):
            assert_pre_fe(1782864000000.0)

    def test_bool_is_rejected_despite_being_an_int(self):
        with self.assertRaises(InvalidTimestampError):
            assert_pre_fe(True)

    def test_nonsense_object_is_rejected(self):
        with self.assertRaises(InvalidTimestampError):
            assert_pre_fe(object())

    def test_zero_is_rejected(self):
        with self.assertRaises(InvalidTimestampError):
            assert_pre_fe(0)

    def test_negative_is_rejected(self):
        with self.assertRaises(InvalidTimestampError):
            assert_pre_fe(-1782864000000)

    def test_every_failure_is_a_held_out_data_error(self):
        # A single except clause must fail closed on all of these.
        for bad in (None, "x", 1.0, True, object(), 0, -1, FE_MS, FE_MS + 1):
            with self.subTest(bad=bad):
                with self.assertRaises(HeldOutDataError):
                    assert_pre_fe(bad)

    def test_context_appears_in_the_message(self):
        with self.assertRaises(HeldOutDataError) as ctx:
            assert_pre_fe(FE_MS, context="MGC_L_1m bar 42")
        self.assertIn("MGC_L_1m bar 42", str(ctx.exception))


class TestAssertAllPreFe(unittest.TestCase):
    def test_all_pre_fe_series_is_accepted(self):
        series = [FE_MS - 3, FE_MS - 2, FE_MS - 1]
        self.assertEqual(assert_all_pre_fe(series), 3)

    def test_one_post_fe_value_rejects_the_series(self):
        with self.assertRaises(HeldOutDataError) as ctx:
            assert_all_pre_fe([FE_MS - 2, FE_MS - 1, FE_MS])
        self.assertIn("[2]", str(ctx.exception))

    def test_one_missing_value_rejects_the_series(self):
        with self.assertRaises(InvalidTimestampError):
            assert_all_pre_fe([FE_MS - 2, None])

    def test_empty_series_is_vacuously_accepted(self):
        self.assertEqual(assert_all_pre_fe([]), 0)

    def test_non_iterable_is_rejected_not_treated_as_empty(self):
        with self.assertRaises(InvalidTimestampError):
            assert_all_pre_fe(1782864000000)


if __name__ == "__main__":
    unittest.main()

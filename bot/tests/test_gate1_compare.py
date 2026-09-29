"""The comparator must fail on purpose before it is trusted to pass.

Each of the seven mutations is proved independently: a comparator that only
ever agrees is not evidence of anything.

Fixtures here are hand-built structures, not V53 output. Nothing in this file
loads bars, runs the engine, or asserts that V53 reproduces anything.
"""

from __future__ import annotations

import copy
import unittest
from decimal import Decimal as D

from bot.replay.compare import (
    ASSERTIONS_MUST_BE_ZERO, ASSERTIONS_NOT_APPLICABLE, BEHAVIOUR_COUNTERS,
    COVERAGE_COUNTERS, DERIVED_LABEL, DERIVED_NO_COMPARAND, EXCLUDED_COUNTERS,
    LEDGER_FIELDS, NOT_APPLICABLE_LABEL, ComparatorError, compare_cell,
    compare_counters, compare_ledger, compare_ledger_row, _exact,
)

FUNNEL = {name: 0 for name in BEHAVIOUR_COUNTERS} | {
    "sweeps": 641, "choch": 538, "retests": 473, "bos_displacement": 30,
    "break_no_displacement": 2617, "fvg": 16, "no_fvg": 14, "fills": 2,
    "r_band_rejects": 4, "fvg_retest_expiry": 2, "expire_pre_choch": 103,
    "expire_post_choch": 65, "expire_post_retest": 443, "dropped_no_slot": 0,
    # present in the fixture, never compared as parity:
    "fold_bars": 10368, "fold_bars_with_ltf": 9812, "ltf_bars": 100000,
}

ROW_A = {
    "sweep_ts": 1780076700000, "sweep_kind": "AS", "sweep_extreme": "30355.5",
    "choch_ts": 1780077240000, "choch_level": "30334",
    "retest_ts": 1780077900000,
    "bos_ts": 1780080300000, "bos_level": "30367",
    "fvg_low": "30352", "fvg_high": "30380.25",
    "entry_ts": 1780082700000, "entry_price": "30380.25",
    "stop_price": "30361.5423", "outcome": "LOSS", "r_multiple": "-1.08",
    "pnl_usd": "-40.42", "exit_reason": "stop", "bars_in_trade": 1,
}
ROW_B = ROW_A | {
    "sweep_ts": 1780085100000, "sweep_kind": "SW", "sweep_extreme": "30410.25",
    "entry_ts": 1780265400000, "entry_price": "30398.5",
    "stop_price": "30415.7992", "r_multiple": "-1.087", "pnl_usd": "-37.6",
}
LEDGER = [ROW_A, ROW_B]
ZERO_ASSERTS = {i: 0 for i in ASSERTIONS_MUST_BE_ZERO}


def run(expected_ledger=None, actual_ledger=None, expected_funnel=None,
        actual_funnel=None, asserts=None, **kwargs):
    return compare_cell(
        cell_id="v53-MNQ-S-1m-A",
        expected_funnel=expected_funnel or FUNNEL,
        actual_funnel=actual_funnel or FUNNEL,
        expected_ledger=expected_ledger if expected_ledger is not None else LEDGER,
        actual_ledger=actual_ledger if actual_ledger is not None else LEDGER,
        actual_assertions=asserts or ZERO_ASSERTS,
        **kwargs)


class Baseline(unittest.TestCase):

    def test_identical_input_produces_no_divergence(self):
        result = run()
        self.assertTrue(result.ok)
        self.assertIsNone(result.first)
        self.assertEqual(result.mode, "full")

    def test_eighteen_ledger_fields_and_fourteen_counters(self):
        self.assertEqual(len(LEDGER_FIELDS), 18)
        self.assertEqual(len(BEHAVIOUR_COUNTERS), 14)

    def test_coverage_and_ltf_bars_are_not_parity_counters(self):
        for name in COVERAGE_COUNTERS + EXCLUDED_COUNTERS:
            self.assertNotIn(name, BEHAVIOUR_COUNTERS)

    def test_derived_fields_are_not_ledger_fields(self):
        for name in DERIVED_NO_COMPARAND:
            self.assertNotIn(name, LEDGER_FIELDS)


class FailureModes(unittest.TestCase):
    """The seven mutations, each proved on its own."""

    def test_1_one_tick_price_mutation(self):
        mutated = copy.deepcopy(LEDGER)
        mutated[0]["entry_price"] = "30380.5"      # one tick on MNQ
        result = run(actual_ledger=mutated)
        self.assertFalse(result.ok)
        self.assertEqual(result.first.where, "ledger[0].entry_price")
        self.assertEqual(result.first.kind, "ledger_field")

    def test_1b_sub_tick_mutation_is_still_a_divergence(self):
        mutated = copy.deepcopy(LEDGER)
        mutated[0]["stop_price"] = "30361.5424"    # one ten-thousandth
        self.assertFalse(run(actual_ledger=mutated).ok)

    def test_2_extra_ledger_row(self):
        result = run(actual_ledger=LEDGER + [copy.deepcopy(ROW_A)])
        self.assertFalse(result.ok)
        self.assertEqual(result.first.kind, "extra_row")
        self.assertEqual(result.first.row_index, 2)

    def test_3_missing_ledger_row(self):
        result = run(actual_ledger=LEDGER[:1])
        self.assertFalse(result.ok)
        self.assertEqual(result.first.kind, "missing_row")
        self.assertEqual(result.first.row_index, 1)

    def test_4_changed_timestamp(self):
        mutated = copy.deepcopy(LEDGER)
        mutated[1]["entry_ts"] = ROW_B["entry_ts"] + 60_000
        result = run(actual_ledger=mutated)
        self.assertFalse(result.ok)
        self.assertEqual(result.first.where, "ledger[1].entry_ts")

    def test_5_changed_outcome(self):
        mutated = copy.deepcopy(LEDGER)
        mutated[0]["outcome"] = "WIN"
        result = run(actual_ledger=mutated)
        self.assertFalse(result.ok)
        self.assertEqual(result.first.where, "ledger[0].outcome")

    def test_6_changed_counter(self):
        result = run(actual_funnel=FUNNEL | {"sweeps": 640})
        self.assertFalse(result.ok)
        self.assertEqual(result.first.where, "funnel.sweeps")
        self.assertEqual((result.first.expected, result.first.actual), (641, 640))

    def test_7_changed_assertion_value(self):
        result = run(asserts=ZERO_ASSERTS | {23: 1})
        self.assertFalse(result.ok)
        self.assertEqual(result.first.where, "K23")
        self.assertEqual(result.first.kind, "assertion")


class FirstDivergence(unittest.TestCase):

    def test_first_divergence_is_the_earliest_row(self):
        mutated = copy.deepcopy(LEDGER)
        mutated[0]["bars_in_trade"] = 99
        mutated[1]["entry_price"] = "1"
        result = run(actual_ledger=mutated)
        self.assertEqual(result.first.row_index, 0)
        self.assertEqual(len(result.divergences), 2)

    def test_counters_are_scanned_before_the_ledger(self):
        mutated = copy.deepcopy(LEDGER)
        mutated[0]["entry_price"] = "1"
        result = run(actual_funnel=FUNNEL | {"fills": 99}, actual_ledger=mutated)
        self.assertEqual(result.first.where, "funnel.fills")

    def test_assertions_are_scanned_before_the_ledger(self):
        mutated = copy.deepcopy(LEDGER)
        mutated[0]["entry_price"] = "1"
        result = run(asserts=ZERO_ASSERTS | {21: 3}, actual_ledger=mutated)
        self.assertEqual(result.first.where, "K21")

    def test_field_scan_order_follows_ledger_fields(self):
        mutated = copy.deepcopy(LEDGER)
        mutated[0]["exit_reason"] = "target"      # late field
        mutated[0]["sweep_kind"] = "PD"           # early field
        result = run(actual_ledger=mutated)
        self.assertEqual(result.first.where, "ledger[0].sweep_kind")

    def test_every_divergence_is_reported_not_just_the_first(self):
        mutated = copy.deepcopy(LEDGER)
        mutated[0]["outcome"] = "WIN"
        mutated[1]["outcome"] = "WIN"
        self.assertEqual(len(run(actual_ledger=mutated).divergences), 2)


class NoToleranceAnywhere(unittest.TestCase):

    def test_float_price_is_refused_outright(self):
        with self.assertRaises(ComparatorError):
            _exact(30380.25, "ledger[0].entry_price")

    def test_float_in_an_engine_row_is_refused(self):
        mutated = copy.deepcopy(LEDGER)
        mutated[0]["entry_price"] = 30380.25
        with self.assertRaises(ComparatorError):
            run(actual_ledger=mutated)

    def test_bool_is_not_silently_a_number(self):
        with self.assertRaises(ComparatorError):
            _exact(True, "ledger[0].entry_price")

    def test_decimal_and_equal_valued_string_agree(self):
        mutated = copy.deepcopy(LEDGER)
        mutated[0]["entry_price"] = D("30380.2500")
        self.assertTrue(run(actual_ledger=mutated).ok)

    def test_compare_cell_takes_no_tolerance_argument(self):
        import inspect
        names = set(inspect.signature(compare_cell).parameters)
        for forbidden in ("tolerance", "atol", "rtol", "epsilon", "approx", "close_enough"):
            self.assertNotIn(forbidden, names)


class MissingFieldsAreErrorsNotPasses(unittest.TestCase):

    def test_missing_behaviour_counter_in_golden_raises(self):
        funnel = {k: v for k, v in FUNNEL.items() if k != "sweeps"}
        with self.assertRaises(ComparatorError):
            compare_counters(funnel, FUNNEL)

    def test_missing_behaviour_counter_in_engine_raises(self):
        funnel = {k: v for k, v in FUNNEL.items() if k != "fills"}
        with self.assertRaises(ComparatorError):
            compare_counters(FUNNEL, funnel)

    def test_missing_ledger_field_raises(self):
        row = {k: v for k, v in ROW_A.items() if k != "stop_price"}
        with self.assertRaises(ComparatorError):
            compare_ledger_row(0, ROW_A, row)

    def test_unreported_assertion_counter_raises(self):
        with self.assertRaises(ComparatorError):
            run(asserts={i: 0 for i in ASSERTIONS_MUST_BE_ZERO if i != 32})


class TruncationAndDerived(unittest.TestCase):

    def test_truncated_cell_compares_counters_only(self):
        result = run(actual_ledger=[], source_truncated=True)
        self.assertTrue(result.ok)
        self.assertEqual(result.mode, "counters_only")

    def test_truncated_cell_still_fails_on_a_counter(self):
        result = run(actual_funnel=FUNNEL | {"choch": 1}, source_truncated=True)
        self.assertFalse(result.ok)

    def test_k26_k27_are_reported_not_applicable(self):
        result = run()
        self.assertEqual(result.not_applicable, ("K26", "K27"))
        self.assertNotIn(26, ASSERTIONS_MUST_BE_ZERO)
        self.assertNotIn(27, ASSERTIONS_MUST_BE_ZERO)
        self.assertEqual(ASSERTIONS_NOT_APPLICABLE, (26, 27))

    def test_k26_k27_nonzero_does_not_affect_the_comparison(self):
        # They are not applicable, so they neither pass nor fail the cell.
        self.assertTrue(run(asserts=ZERO_ASSERTS | {26: 5, 27: 9}).ok)

    def test_report_labels_not_applicable_and_derived(self):
        text = "\n".join(run(derived={"target_price": "30286.71150",
                                      "mfe": "0.41", "mae": "1.08"}).report_lines())
        self.assertIn(NOT_APPLICABLE_LABEL, text)
        self.assertIn("K26", text)
        for name in DERIVED_NO_COMPARAND:
            self.assertIn(name, text)
        self.assertIn(DERIVED_LABEL, text)

    def test_derived_values_never_create_a_divergence(self):
        self.assertTrue(run(derived={"mfe": "999", "mae": "999"}).ok)

    def test_report_names_the_first_divergence(self):
        mutated = copy.deepcopy(LEDGER)
        mutated[0]["entry_price"] = "1"
        text = "\n".join(run(actual_ledger=mutated).report_lines())
        self.assertIn("FIRST DIVERGENCE", text)
        self.assertIn("ledger[0].entry_price", text)


class LedgerRowAccounting(unittest.TestCase):

    def test_empty_against_empty(self):
        self.assertEqual(compare_ledger([], []), [])

    def test_all_missing(self):
        divs = compare_ledger(LEDGER, [])
        self.assertEqual([d.kind for d in divs], ["missing_row", "missing_row"])

    def test_all_extra(self):
        divs = compare_ledger([], LEDGER)
        self.assertEqual([d.kind for d in divs], ["extra_row", "extra_row"])


if __name__ == "__main__":
    unittest.main()

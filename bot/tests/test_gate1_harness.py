"""The Gate 1 harness and report, run once against the repository's real data.

These tests assert the *machinery* behaves correctly. None of them asserts that
V53 is reproduced, and a clean comparison on candidate data is never treated as
parity.
"""

from __future__ import annotations

import unittest

from bot.contracts.enums import Direction, Timeframe
from bot.fixtures.loader import load_fixture, load_manifest
from bot.replay.compare import ASSERTIONS_MUST_BE_ZERO, ASSERTIONS_NOT_APPLICABLE
from bot.replay.report import render
from bot.replay.harness import (
    COST_USD, POINT_VALUE, engine_ledger, golden_ledger, registered_cells,
    run_gate1,
)
from bot.replay.verdicts import (
    EXPECTED_CELL_COUNT, PASSING_VERDICTS, CellVerdict, DatasetStatus,
    GateResult,
)


class _Run(unittest.TestCase):
    """One shared Gate 1 run; the engine work is done once for the module."""

    @classmethod
    def setUpClass(cls):
        cls.gate = run_gate1()
        cls.by_id = {r.cell.cell_id: r for r in cls.gate.runs}
        cls.text = render(cls.gate)


class Registry(unittest.TestCase):

    def test_exactly_24_cells(self):
        self.assertEqual(len(registered_cells()), EXPECTED_CELL_COUNT)

    def test_cell_ids_are_unique(self):
        ids = [c.cell_id for c in registered_cells()]
        self.assertEqual(len(set(ids)), EXPECTED_CELL_COUNT)

    def test_order_is_fixed_and_matches_the_golden_manifest(self):
        ours = [c.cell_id for c in registered_cells()]
        theirs = [e["fixture_id"] for e in load_manifest()["fixtures"]]
        self.assertEqual(ours, theirs)

    def test_order_is_stable_across_calls(self):
        self.assertEqual([c.cell_id for c in registered_cells()],
                         [c.cell_id for c in registered_cells()])

    def test_every_cell_has_a_fixture(self):
        for cell in registered_cells():
            load_fixture(cell.fixture_id)

    def test_point_value_is_explicit_and_matches_every_fixture(self):
        """U4: V53's silent 1.0 fallback must never reach a bot."""
        seen = 0
        for cell in registered_cells():
            for fill in load_fixture(cell.fixture_id)["fills"]:
                seen += 1
                self.assertEqual(float(fill["derived"]["point_value_usd"]),
                                 POINT_VALUE[cell.instrument])
        self.assertEqual(seen, 58)

    def test_cost_is_the_frozen_constant(self):
        self.assertEqual(COST_USD, 3.00)


class CellOutcomes(_Run):

    def test_all_24_cells_are_evaluated(self):
        self.assertEqual(self.gate.cells_evaluated, EXPECTED_CELL_COUNT)
        self.assertEqual(len(self.gate.report.cells), EXPECTED_CELL_COUNT)

    def test_every_cell_has_exactly_one_lawful_verdict(self):
        for run in self.gate.runs:
            self.assertIsInstance(run.result.verdict, CellVerdict)

    def test_no_early_stopping_even_after_a_divergence(self):
        """A cell later in the order than a PROVISIONAL-FAIL still ran."""
        verdicts = [r.result.verdict for r in self.gate.runs]
        if CellVerdict.PROVISIONAL_FAIL in verdicts:
            first = verdicts.index(CellVerdict.PROVISIONAL_FAIL)
            self.assertTrue(any(r.engine_ran for r in self.gate.runs[first + 1:]),
                            "the harness stopped after the first divergence")

    def test_missing_3m_data_produces_no_data(self):
        for run in self.gate.runs:
            if run.cell.ltf is Timeframe.M3:
                with self.subTest(cell=run.cell.cell_id):
                    self.assertIs(run.result.verdict, CellVerdict.NO_DATA)
                    self.assertFalse(run.engine_ran)
        self.assertEqual(self.gate.report.census[CellVerdict.NO_DATA], 12)

    def test_short_fold_a_coverage_produces_precondition_fail(self):
        for run in self.gate.runs:
            if run.cell.ltf is Timeframe.M1 and run.cell.fold == "A":
                with self.subTest(cell=run.cell.cell_id):
                    self.assertIs(run.result.verdict, CellVerdict.PRECONDITION_FAIL)
        self.assertEqual(self.gate.report.census[CellVerdict.PRECONDITION_FAIL], 4)

    def test_the_engine_never_runs_on_a_failed_precondition(self):
        for run in self.gate.runs:
            if run.result.verdict is CellVerdict.PRECONDITION_FAIL:
                with self.subTest(cell=run.cell.cell_id):
                    self.assertFalse(run.engine_ran)
                    self.assertIsNone(run.funnel)
                    self.assertIsNone(run.comparison)

    def test_coverage_is_checked_before_the_engine(self):
        """Every cell that ran has a satisfied precondition recorded."""
        for run in self.gate.runs:
            if run.engine_ran:
                with self.subTest(cell=run.cell.cell_id):
                    self.assertIsNotNone(run.coverage)
                    self.assertTrue(run.coverage.ok)

    def test_precondition_report_names_expected_and_actual(self):
        run = self.by_id["v53-MGC-L-1m-A"]
        text = "\n".join(run.result.detail)
        self.assertIn("expected 9813", text)
        self.assertIn("actual 9677", text)
        self.assertIn("MGC1!", text)

    def test_candidate_data_can_only_produce_provisional_verdicts(self):
        for run in self.gate.runs:
            if run.engine_ran:
                with self.subTest(cell=run.cell.cell_id):
                    self.assertIs(run.result.status, DatasetStatus.CANDIDATE)
                    self.assertIn(run.result.verdict,
                                  (CellVerdict.PROVISIONAL_PASS,
                                   CellVerdict.PROVISIONAL_FAIL))

    def test_no_cell_reaches_a_gate_passing_verdict(self):
        for run in self.gate.runs:
            self.assertNotIn(run.result.verdict, PASSING_VERDICTS)

    def test_k26_k27_are_never_reported_as_passing(self):
        for run in self.gate.runs:
            if run.assertions is not None:
                with self.subTest(cell=run.cell.cell_id):
                    self.assertNotIn(26, run.assertions)
                    self.assertNotIn(27, run.assertions)
                    self.assertEqual(sorted(run.assertions), list(ASSERTIONS_MUST_BE_ZERO))
        self.assertEqual(ASSERTIONS_NOT_APPLICABLE, (26, 27))

    def test_assertion_counters_that_must_be_zero_are_zero(self):
        for run in self.gate.runs:
            if run.assertions is not None:
                with self.subTest(cell=run.cell.cell_id):
                    self.assertEqual(set(run.assertions.values()), {0})

    def test_ltf_bars_does_not_affect_the_behavioural_verdict(self):
        """K31 differs from the record on every fold-C cell, yet two pass."""
        c_cells = [r for r in self.gate.runs
                   if r.engine_ran and r.cell.fold == "C"]
        self.assertTrue(c_cells)
        for run in c_cells:
            expected = load_fixture(run.cell.fixture_id)["funnel"]["ltf_bars"]
            self.assertIsNotNone(expected)
            self.assertNotEqual(expected, run.funnel["ltf_bars"])
        self.assertTrue(
            any(r.result.verdict is CellVerdict.PROVISIONAL_PASS for r in c_cells),
            "ltf_bars leaked into the verdict")

    def test_conservation_identity_holds_in_the_engine(self):
        """Amended criterion 4, on the cells that ran."""
        for run in self.gate.runs:
            if run.funnel is not None:
                with self.subTest(cell=run.cell.cell_id):
                    self.assertEqual(
                        run.funnel["fvg"],
                        run.funnel["fills"] + run.funnel["r_band_rejects"]
                        + run.funnel["fvg_retest_expiry"])


class Aggregation(_Run):

    def test_gate_is_never_pass_or_fail_on_current_evidence(self):
        self.assertNotIn(self.gate.report.result,
                         (GateResult.PASS, GateResult.FAIL))

    def test_gate_is_not_adjudicable(self):
        self.assertIn(self.gate.report.result,
                      (GateResult.NOT_ADJUDICABLE_INSUFFICIENT,
                       GateResult.NOT_ADJUDICABLE_DIVERGENCE))

    def test_current_census_is_pinned(self):
        """Regression pin. If this changes, the data or the engine changed."""
        census = self.gate.report.census
        self.assertEqual(census[CellVerdict.NO_DATA], 12)
        self.assertEqual(census[CellVerdict.PRECONDITION_FAIL], 4)
        self.assertEqual(census[CellVerdict.PROVISIONAL_PASS], 6)
        self.assertEqual(census[CellVerdict.PROVISIONAL_FAIL], 2)
        self.assertEqual(census[CellVerdict.PASS], 0)
        self.assertEqual(census[CellVerdict.FAIL], 0)
        self.assertEqual(census[CellVerdict.SOURCE_TRUNCATED], 0)

    def test_a_provisional_fail_makes_the_gate_report_divergence(self):
        if self.gate.report.census[CellVerdict.PROVISIONAL_FAIL]:
            self.assertIs(self.gate.report.result,
                          GateResult.NOT_ADJUDICABLE_DIVERGENCE)

    def test_the_gate_did_not_pass(self):
        self.assertFalse(self.gate.report.passed)


class LedgerProjection(unittest.TestCase):

    def test_golden_and_engine_rows_expose_the_same_field_set(self):
        from bot.replay.compare import LEDGER_FIELDS
        fixture = load_fixture("v53-MNQ-S-1m-A")
        rows = golden_ledger(fixture)
        self.assertEqual(len(rows), 10)
        self.assertEqual(set(rows[0]), set(LEDGER_FIELDS))

    def test_engine_rows_parse_through_the_extractor_grammar(self):
        row = ("MGC1!|L|1m|B|sw 2026-07-20 05:10|SW|swX 4500.1|"
               "ch 2026-07-20 05:20|chL 4501|rt 2026-07-20 05:25|"
               "bos 2026-07-20 05:30|bosL 4502|fvg 4503-4504|"
               "en 2026-07-20 05:35|enPx 4504|stop 4499|WIN|5R|$100|target|3bars")
        from bot.replay.compare import LEDGER_FIELDS
        parsed = engine_ledger([row], "cell")[0]
        self.assertEqual(set(parsed), set(LEDGER_FIELDS))
        self.assertEqual(parsed["outcome"], "WIN")
        self.assertEqual(parsed["bars_in_trade"], 3)


class Report(_Run):

    def test_report_contains_all_24_cells(self):
        for cell in registered_cells():
            self.assertIn(cell.cell_id, self.text)

    def test_report_states_the_aggregate_result_verbatim(self):
        self.assertIn(self.gate.report.result.value, self.text)

    def test_report_makes_no_overall_pass_or_fail_claim(self):
        self.assertNotIn(GateResult.PASS.value, self.text)
        self.assertNotIn(GateResult.FAIL.value, self.text)

    def test_report_says_not_adjudicable(self):
        self.assertIn("NOT ADJUDICABLE", self.text)

    def test_report_carries_run_metadata(self):
        self.assertIn(self.gate.started_utc, self.text)
        self.assertIn(self.gate.commit, self.text)

    def test_report_carries_provenance_and_status(self):
        for fragment in ("data/phase_c/MGC1__5m.csv",
                         "data/phase_c_ltf/MNQ1__1m.csv",
                         "sha256", "CANDIDATE", "status UNRESOLVED"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.text)

    def test_report_marks_k26_k27_not_applicable(self):
        self.assertIn("NOT APPLICABLE", self.text)
        self.assertIn("K26", self.text)
        self.assertIn("K27", self.text)

    def test_report_labels_derived_diagnostics(self):
        self.assertIn("DERIVED — NO GOLDEN COMPARAND", self.text)

    def test_report_names_the_first_divergence_where_there_is_one(self):
        if self.gate.report.census[CellVerdict.PROVISIONAL_FAIL]:
            self.assertIn("FIRST DIVERGENCE", self.text)

    def test_report_shows_expected_and_actual_coverage(self):
        self.assertIn("expected 9813", self.text)
        self.assertIn("actual 9677", self.text)

    def test_cell_order_in_the_report_is_the_registry_order(self):
        positions = [self.text.index(f"### {c.cell_id}") for c in registered_cells()]
        self.assertEqual(positions, sorted(positions))

    def test_rendering_is_deterministic_for_one_run(self):
        self.assertEqual(render(self.gate), self.text)


if __name__ == "__main__":
    unittest.main()

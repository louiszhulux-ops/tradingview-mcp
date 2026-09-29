"""Cell verdicts and Gate 1 aggregation.

The one property this file exists to defend: **no partial combination can ever
produce Gate 1 PASS.**
"""

from __future__ import annotations

import itertools
import unittest

from bot.replay.verdicts import (
    EXPECTED_CELL_COUNT, PASSING_VERDICTS, PRECEDENCE, CellResult, CellVerdict,
    DatasetStatus, GateResult, aggregate, decide_cell_verdict, precedence_rank,
)

AUTH = DatasetStatus.AUTHORITATIVE
CAND = DatasetStatus.CANDIDATE


def cell(index: int, verdict: CellVerdict, status: DatasetStatus | None = None) -> CellResult:
    if status is None:
        status = AUTH if verdict in PASSING_VERDICTS else CAND
    return CellResult(f"cell-{index:02d}", verdict, status)


def full(verdict: CellVerdict, status: DatasetStatus | None = None) -> list[CellResult]:
    return [cell(i, verdict, status) for i in range(EXPECTED_CELL_COUNT)]


class DecideVerdict(unittest.TestCase):
    """Each of the seven states is reachable, and only under its own condition."""

    def test_no_data(self):
        self.assertIs(decide_cell_verdict(
            data_present=False, coverage_ok=True, comparison_ok=True,
            status=AUTH, source_truncated=False), CellVerdict.NO_DATA)

    def test_no_data_outranks_everything(self):
        # Absent input is classified first, whatever else is claimed about it.
        for cov, cmp_, trunc in itertools.product([True, False], repeat=3):
            self.assertIs(decide_cell_verdict(
                data_present=False, coverage_ok=cov, comparison_ok=cmp_,
                status=AUTH, source_truncated=trunc), CellVerdict.NO_DATA)

    def test_precondition_fail(self):
        self.assertIs(decide_cell_verdict(
            data_present=True, coverage_ok=False, comparison_ok=True,
            status=AUTH, source_truncated=False), CellVerdict.PRECONDITION_FAIL)

    def test_precondition_fail_is_not_a_strategy_verdict(self):
        # Coverage decides before the engine runs, so the comparison result is
        # irrelevant: a data hole is never reported as a divergence.
        for cmp_ in (True, False):
            self.assertIs(decide_cell_verdict(
                data_present=True, coverage_ok=False, comparison_ok=cmp_,
                status=AUTH, source_truncated=False), CellVerdict.PRECONDITION_FAIL)

    def test_source_truncated(self):
        self.assertIs(decide_cell_verdict(
            data_present=True, coverage_ok=True, comparison_ok=True,
            status=AUTH, source_truncated=True), CellVerdict.SOURCE_TRUNCATED)

    def test_truncation_never_launders_a_divergence(self):
        self.assertIs(decide_cell_verdict(
            data_present=True, coverage_ok=True, comparison_ok=False,
            status=AUTH, source_truncated=True), CellVerdict.FAIL)

    def test_truncation_on_candidate_data_is_provisional(self):
        # SOURCE-TRUNCATED counts toward a pass, so it needs authoritative data.
        self.assertIs(decide_cell_verdict(
            data_present=True, coverage_ok=True, comparison_ok=True,
            status=CAND, source_truncated=True), CellVerdict.PROVISIONAL_PASS)

    def test_provisional_pass(self):
        self.assertIs(decide_cell_verdict(
            data_present=True, coverage_ok=True, comparison_ok=True,
            status=CAND, source_truncated=False), CellVerdict.PROVISIONAL_PASS)

    def test_provisional_fail(self):
        self.assertIs(decide_cell_verdict(
            data_present=True, coverage_ok=True, comparison_ok=False,
            status=CAND, source_truncated=False), CellVerdict.PROVISIONAL_FAIL)

    def test_pass(self):
        self.assertIs(decide_cell_verdict(
            data_present=True, coverage_ok=True, comparison_ok=True,
            status=AUTH, source_truncated=False), CellVerdict.PASS)

    def test_fail(self):
        self.assertIs(decide_cell_verdict(
            data_present=True, coverage_ok=True, comparison_ok=False,
            status=AUTH, source_truncated=False), CellVerdict.FAIL)

    def test_candidate_data_can_never_reach_a_passing_verdict(self):
        for cov, cmp_, trunc in itertools.product([True, False], repeat=3):
            verdict = decide_cell_verdict(
                data_present=True, coverage_ok=cov, comparison_ok=cmp_,
                status=CAND, source_truncated=trunc)
            self.assertNotIn(verdict, PASSING_VERDICTS)

    def test_status_must_be_a_dataset_status(self):
        with self.assertRaises(ValueError):
            decide_cell_verdict(data_present=True, coverage_ok=True,
                                comparison_ok=True, status="AUTHORITATIVE",
                                source_truncated=False)

    def test_precedence_is_documented_in_order(self):
        self.assertEqual(precedence_rank(CellVerdict.NO_DATA), 0)
        self.assertLess(precedence_rank(CellVerdict.NO_DATA),
                        precedence_rank(CellVerdict.PRECONDITION_FAIL))
        self.assertLess(precedence_rank(CellVerdict.PRECONDITION_FAIL),
                        precedence_rank(CellVerdict.SOURCE_TRUNCATED))
        self.assertEqual(len(PRECEDENCE), 7)


class CellResultGuards(unittest.TestCase):

    def test_passing_verdict_requires_authoritative_data(self):
        for verdict in PASSING_VERDICTS:
            with self.assertRaises(ValueError):
                CellResult("c", verdict, CAND)

    def test_non_passing_verdicts_accept_either_status(self):
        CellResult("c", CellVerdict.PROVISIONAL_PASS, CAND)
        CellResult("c", CellVerdict.FAIL, AUTH)

    def test_cell_id_required(self):
        with self.assertRaises(ValueError):
            CellResult("", CellVerdict.PASS, AUTH)


class Aggregation(unittest.TestCase):

    def test_all_pass_is_gate_pass(self):
        self.assertIs(aggregate(full(CellVerdict.PASS)).result, GateResult.PASS)

    def test_pass_plus_source_truncated_is_gate_pass(self):
        cells = full(CellVerdict.PASS)
        cells[3] = cell(3, CellVerdict.SOURCE_TRUNCATED, AUTH)
        cells[11] = cell(11, CellVerdict.SOURCE_TRUNCATED, AUTH)
        report = aggregate(cells)
        self.assertIs(report.result, GateResult.PASS)
        self.assertEqual(report.census[CellVerdict.SOURCE_TRUNCATED], 2)

    def test_any_fail_is_gate_fail(self):
        cells = full(CellVerdict.PASS)
        cells[7] = cell(7, CellVerdict.FAIL, AUTH)
        self.assertIs(aggregate(cells).result, GateResult.FAIL)

    def test_fail_outranks_provisional_fail(self):
        cells = full(CellVerdict.PASS)
        cells[1] = cell(1, CellVerdict.FAIL, AUTH)
        cells[2] = cell(2, CellVerdict.PROVISIONAL_FAIL, CAND)
        self.assertIs(aggregate(cells).result, GateResult.FAIL)

    def test_any_provisional_fail_is_not_adjudicable_divergence(self):
        cells = full(CellVerdict.PASS)
        cells[5] = cell(5, CellVerdict.PROVISIONAL_FAIL, CAND)
        self.assertIs(aggregate(cells).result,
                      GateResult.NOT_ADJUDICABLE_DIVERGENCE)

    def test_no_data_without_fail_is_not_adjudicable(self):
        cells = full(CellVerdict.PASS)
        cells[0] = cell(0, CellVerdict.NO_DATA, CAND)
        self.assertIs(aggregate(cells).result,
                      GateResult.NOT_ADJUDICABLE_INSUFFICIENT)

    def test_precondition_fail_without_fail_is_not_adjudicable(self):
        cells = full(CellVerdict.PASS)
        cells[0] = cell(0, CellVerdict.PRECONDITION_FAIL, CAND)
        self.assertIs(aggregate(cells).result,
                      GateResult.NOT_ADJUDICABLE_INSUFFICIENT)

    def test_provisional_pass_is_never_a_gate_pass(self):
        self.assertIs(aggregate(full(CellVerdict.PROVISIONAL_PASS, CAND)).result,
                      GateResult.NOT_ADJUDICABLE_INSUFFICIENT)

    def test_one_provisional_pass_among_passes_is_not_adjudicable(self):
        cells = full(CellVerdict.PASS)
        cells[23] = cell(23, CellVerdict.PROVISIONAL_PASS, CAND)
        self.assertIs(aggregate(cells).result,
                      GateResult.NOT_ADJUDICABLE_INSUFFICIENT)

    def test_short_census_cannot_pass(self):
        report = aggregate(full(CellVerdict.PASS)[:23])
        self.assertIs(report.result, GateResult.NOT_ADJUDICABLE_INSUFFICIENT)
        self.assertTrue(report.notes)

    def test_missing_named_cell_cannot_pass(self):
        expected = [f"cell-{i:02d}" for i in range(EXPECTED_CELL_COUNT)]
        cells = full(CellVerdict.PASS)
        cells[9] = CellResult("cell-99", CellVerdict.PASS, AUTH)
        report = aggregate(cells, expected_cell_ids=expected)
        self.assertIs(report.result, GateResult.NOT_ADJUDICABLE_INSUFFICIENT)

    def test_duplicate_cell_is_rejected(self):
        cells = full(CellVerdict.PASS)
        cells[1] = cell(0, CellVerdict.PASS, AUTH)
        with self.assertRaises(ValueError):
            aggregate(cells)

    def test_no_partial_combination_can_pass(self):
        """Exhaustive: every mixture containing a non-passing verdict fails.

        One cell is set to each non-passing verdict in turn while the other 23
        pass. None of the 5 × 24 combinations may produce GATE 1: PASS.
        """
        non_passing = [v for v in PRECEDENCE if v not in PASSING_VERDICTS]
        self.assertEqual(len(non_passing), 5)
        for verdict in non_passing:
            for index in range(EXPECTED_CELL_COUNT):
                cells = full(CellVerdict.PASS)
                cells[index] = cell(index, verdict)
                self.assertIsNot(
                    aggregate(cells).result, GateResult.PASS,
                    f"{verdict.value} at index {index} produced a Gate 1 PASS")

    def test_census_counts_every_verdict(self):
        cells = full(CellVerdict.PASS)
        cells[0] = cell(0, CellVerdict.NO_DATA)
        cells[1] = cell(1, CellVerdict.PRECONDITION_FAIL)
        report = aggregate(cells)
        self.assertEqual(report.census[CellVerdict.PASS], 22)
        self.assertEqual(report.census[CellVerdict.NO_DATA], 1)
        self.assertEqual(sum(report.census.values()), EXPECTED_CELL_COUNT)
        self.assertFalse(report.passed)


class DocumentAgreesWithCode(unittest.TestCase):
    """`bot/GATE1_ACCEPTANCE.md` is prose; this module is the definition.

    They are allowed to be worded differently. They are not allowed to describe
    different vocabularies.
    """

    @classmethod
    def setUpClass(cls):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        cls.doc = (root / "bot" / "GATE1_ACCEPTANCE.md").read_text(encoding="utf-8")
        # Prose is hard-wrapped and partly quoted, so phrase assertions run
        # against a flattened copy with blockquote markers stripped: the
        # document's meaning must not depend on where its lines break.
        cls.flat = " ".join(
            line.lstrip().lstrip(">").strip() for line in cls.doc.splitlines()
        )
        cls.flat = " ".join(cls.flat.split())

    def test_every_verdict_appears_in_the_document(self):
        for verdict in PRECEDENCE:
            self.assertIn(verdict.value, self.doc)

    def test_every_gate_result_appears_in_the_document(self):
        for result in GateResult:
            self.assertIn(result.value, self.doc)

    def test_both_statuses_appear_in_the_document(self):
        for status in DatasetStatus:
            self.assertIn(status.value, self.doc)

    def test_the_document_states_the_pass_rule(self):
        self.assertIn("PASS` or `SOURCE-TRUNCATED", self.flat)

    def test_the_document_states_that_no_data_is_not_a_truncation_downgrade(self):
        self.assertIn("not a truncation downgrade", self.flat)

    def test_the_document_states_the_evidentiary_standard(self):
        for phrase in ("necessary but not sufficient",
                       "cannot be proven",
                       "No future rerun may manufacture that missing ground truth",
                       "evidentiary standard"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.flat)


if __name__ == "__main__":
    unittest.main()

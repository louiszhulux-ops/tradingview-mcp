#!/usr/bin/env python3
"""Tests for the pre-registered Phase 16 analyser.

Run from the repository root:

    python3 -m unittest discover -s trader_v2/p16 -t trader_v2/p16 -p 'test_*.py'

**Fixtures are historical Phase 13F/14 records only — everything strictly
before FE.** No post-FE data exists in this repository and none is added here.
A test asserts that every fixture timestamp is below the OOS boundary.

The analyser is exercised through a non-OOS `Window.for_testing(...)`, which
computes every statistic but makes `decide()` refuse to issue a verdict. That
is the only route by which the analyser will look at anything other than the
frozen window, and it can never be mistaken for a Phase 16 result.
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import p16_analyze as A  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RUNS_AB = REPO / "trader_v2" / "v53_runs"
ARTIFACT = REPO / "trader_v2" / "p16" / "executed" / "V53_P16_OOS_BUILD.pine"


def ms(text: str) -> int:
    return int(datetime.strptime(text, "%Y-%m-%d %H:%M")
               .replace(tzinfo=timezone.utc).timestamp() * 1000)


#: Entirely pre-FE. The end is the OOS start, so nothing at or after FE can enter.
TEST_WINDOW = A.Window.for_testing(ms("2026-05-01 00:00"), A.OOS_START_MS,
                                   "phase15-historical")

LEDGER_STUB = ("{inst}|{dirn}|{ltf}|A|sw 2026-06-01 10:00|SW|swX 100|"
               "ch 2026-06-01 10:20|chL 101|rt 2026-06-01 10:21|"
               "bos {bos_ts}|bosL {bos_lvl}|fvg 102-103|"
               "en {en_ts}|enPx {en_px}|stop 99|{outcome}|{r}R|${usd}|{reason}|{bars}bars")


def row(inst="MGC1!", dirn="L", ltf="1m", bos_ts="2026-06-01 10:30", bos_lvl="104",
        en_ts="2026-06-01 10:40", en_px="102", outcome="WIN", r="4.9",
        usd="490", reason="target", bars="10") -> str:
    return LEDGER_STUB.format(inst=inst, dirn=dirn, ltf=ltf, bos_ts=bos_ts,
                              bos_lvl=bos_lvl, en_ts=en_ts, en_px=en_px,
                              outcome=outcome, r=r, usd=usd, reason=reason, bars=bars)


def fills(*lines: str) -> list[A.Fill]:
    return [A.parse_ledger_row(line, "synthetic") for line in lines]


def historical_cells(fold: str = "A") -> list[A.Cell]:
    return [A.parse_run_file(p) for p in sorted(RUNS_AB.glob(f"M*_{fold}.txt"))]


# ---------------------------------------------------------------- event rule

class TestEventOutcomeRule(unittest.TestCase):
    """Protocol section 5: WIN only if EVERY fill is a WIN."""

    def test_all_win_event_is_a_win(self):
        events = A.build_events(fills(row(), row(bars="12")), "alternative")
        self.assertEqual(len(events), 1)
        self.assertTrue(events[0].is_win)
        self.assertFalse(events[0].is_mixed)

    def test_all_loss_event_is_non_win(self):
        events = A.build_events(
            fills(row(outcome="LOSS", r="-1.0", usd="-100", reason="stop"),
                  row(outcome="LOSS", r="-1.0", usd="-100", reason="stop", bars="12")),
            "alternative")
        self.assertEqual(len(events), 1)
        self.assertFalse(events[0].is_win)

    def test_mixed_win_and_loss_event_is_non_win(self):
        events = A.build_events(
            fills(row(),
                  row(outcome="LOSS", r="-1.0", usd="-100", reason="stop", bars="12")),
            "alternative")
        self.assertEqual(len(events), 1)
        self.assertTrue(events[0].is_mixed)
        self.assertFalse(events[0].is_win, "a mixed event must not count as a win")

    def test_win_plus_timeout_is_non_win(self):
        events = A.build_events(
            fills(row(),
                  row(outcome="LOSS", r="-1.0", usd="-100", reason="timeout", bars="144")),
            "alternative")
        self.assertFalse(events[0].is_win)

    def test_all_timeout_event_is_non_win(self):
        events = A.build_events(
            fills(row(outcome="LOSS", r="-1.0", usd="-100", reason="timeout", bars="144")),
            "alternative")
        self.assertFalse(events[0].is_win)

    def test_any_fill_wins_rule_is_not_used(self):
        events = A.build_events(
            fills(row(), row(outcome="LOSS", r="-1", usd="-100", reason="stop", bars="9")),
            "alternative")
        any_win = any(f.outcome == "WIN" for f in events[0].fills)
        self.assertTrue(any_win)
        self.assertFalse(events[0].is_win, "the permissive rule must not be in force")


class TestClustering(unittest.TestCase):
    def test_two_identical_executions_form_one_event(self):
        events = A.build_events(fills(row(), row()), "alternative")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].size, 2)

    def test_same_instrument_and_direction_but_different_bos_are_separate(self):
        events = A.build_events(
            fills(row(bos_ts="2026-06-01 10:30", bos_lvl="104"),
                  row(bos_ts="2026-06-01 11:30", bos_lvl="107", en_ts="2026-06-01 11:40")),
            "alternative")
        self.assertEqual(len(events), 2)

    def test_primary_splits_where_alternative_collapses(self):
        # Same BOS and entry, different CHOCH: one alternative event, two primary.
        a = row()
        b = row().replace("ch 2026-06-01 10:20|chL 101", "ch 2026-06-01 10:25|chL 101.5")
        parsed = fills(a, b)
        self.assertEqual(len(A.build_events(parsed, "alternative")), 1)
        self.assertEqual(len(A.build_events(parsed, "primary")), 2)

    def test_identity_must_be_named(self):
        with self.assertRaises(A.AnalyserError):
            A.build_events(fills(row()), "whatever")


# ---------------------------------------------------------------- rejections

class TestFailsLoudly(unittest.TestCase):
    def test_malformed_row_too_few_fields(self):
        with self.assertRaises(A.AnalyserError):
            A.parse_ledger_row("MGC1!|L|1m|A|sw 2026-06-01 10:00", "synthetic")

    def test_malformed_row_missing_prefix(self):
        bad = row().replace("|enPx 102|", "|102|")
        with self.assertRaises(A.AnalyserError):
            A.parse_ledger_row(bad, "synthetic")

    def test_malformed_timestamp(self):
        bad = row(en_ts="not-a-date")
        with self.assertRaises(A.AnalyserError):
            A.parse_ledger_row(bad, "synthetic")

    def test_wrong_instrument_is_rejected(self):
        with self.assertRaises(A.AnalyserError):
            A.parse_ledger_row(row().replace("MGC1!", "MES1!"), "synthetic")

    def test_wrong_ltf_is_rejected(self):
        with self.assertRaises(A.AnalyserError):
            A.parse_ledger_row(row(ltf="5m"), "synthetic")

    def test_wrong_direction_is_rejected(self):
        with self.assertRaises(A.AnalyserError):
            A.parse_ledger_row(row(dirn="X"), "synthetic")

    def test_unknown_exit_reason_is_rejected(self):
        with self.assertRaises(A.AnalyserError):
            A.parse_ledger_row(row(reason="manual"), "synthetic")

    def test_win_with_a_non_target_exit_is_ambiguous_and_rejected(self):
        with self.assertRaises(A.AnalyserError):
            A.parse_ledger_row(row(outcome="WIN", reason="stop"), "synthetic")

    def test_data_outside_the_window_is_rejected(self):
        cell = A.Cell(instrument="MGC1!", direction="L", ltf="1m", fold="A",
                      source_file="synthetic", coverage_start="", coverage_end="",
                      funnel={"fills": 1}, asserts_raw="all 0",
                      fills=fills(row(en_ts="2026-06-01 10:40")))
        narrow = A.Window.for_testing(ms("2026-07-01 00:00"), A.OOS_START_MS, "narrow")
        with self.assertRaises(A.AnalyserError) as ctx:
            A.analyse([cell], narrow)
        self.assertIn("outside", str(ctx.exception))

    def test_a_post_fe_timestamp_is_rejected_by_the_historical_window(self):
        # Nothing post-FE exists in this repo; this proves the guard, not data.
        cell = A.Cell(instrument="MGC1!", direction="L", ltf="1m", fold="OOS",
                      source_file="synthetic", coverage_start="", coverage_end="",
                      funnel={"fills": 1}, asserts_raw="all 0",
                      fills=fills(row(en_ts="2026-09-15 10:40")))
        with self.assertRaises(A.AnalyserError):
            A.analyse([cell], TEST_WINDOW)

    def test_duplicate_cells_are_rejected(self):
        cells = historical_cells("A")[:1] * 2
        with self.assertRaises(A.AnalyserError):
            A.analyse(cells, TEST_WINDOW)

    def test_the_oos_label_is_reserved(self):
        with self.assertRaises(A.AnalyserError):
            A.Window.for_testing(0, 1, "phase16-oos")

    def test_artifact_hash_mismatch_raises(self):
        with self.assertRaises(A.AnalyserError):
            A.verify_artifact(REPO / "trader_v2" / "p15" / "executed" / "V53_EXECUTED_BUILD.pine")

    def test_artifact_hash_match_passes(self):
        self.assertTrue(A.verify_artifact(ARTIFACT)["match"])


# ---------------------------------------------------------------- historical

class TestAgainstHistoricalRecords(unittest.TestCase):
    """Fold A of the committed Phase 13F capture, used purely as a fixture."""

    def setUp(self):
        self.cells = historical_cells("A")

    def test_eight_cells_parse(self):
        self.assertEqual(len(self.cells), 8)
        self.assertEqual({c.key for c in self.cells}, set(A.EXPECTED_CELLS))

    def test_every_fixture_timestamp_is_pre_fe(self):
        for cell in self.cells:
            for fill in cell.fills:
                self.assertLess(fill.entry_ts_ms, A.OOS_START_MS,
                                f"{cell.source_file} {fill.entry_ts}")

    def test_analysis_runs_and_matches_the_committed_totals(self):
        report = A.analyse(self.cells, TEST_WINDOW)
        # Phase 13F fold A: 26 fills over the eight cells.
        self.assertEqual(report["execution_level"]["fills"],
                         sum(len(c.fills) for c in self.cells))
        self.assertEqual(report["funnel_total"]["fills"],
                         report["execution_level"]["fills"])

    def test_event_counts_are_conservative_under_the_frozen_rule(self):
        report = A.analyse(self.cells, TEST_WINDOW)
        alternative = report["alternative_identity"]
        self.assertLessEqual(alternative["events"], report["execution_level"]["fills"])
        self.assertLessEqual(alternative["winning_events"], alternative["events"])
        # all-must-win can never exceed the permissive count
        permissive = sum(
            1 for e in A.build_events([f for c in self.cells for f in c.fills],
                                      "alternative")
            if any(f.outcome == "WIN" for f in e.fills)
        )
        self.assertLessEqual(alternative["winning_events"], permissive)

    def test_no_verdict_is_produced_for_a_non_oos_window(self):
        report = A.analyse(self.cells, TEST_WINDOW)
        self.assertFalse(report["window"]["is_oos"])
        self.assertEqual(report["decision"]["verdict"], "NOT APPLICABLE")

    def test_conservation_identity_enforced_on_every_cell(self):
        for cell in self.cells:
            f = cell.funnel
            self.assertEqual(f["fvg"], f["fills"] + f["r_band_rejects"]
                             + f["fvg_retest_expiry"], cell.source_file)


class TestDeterminism(unittest.TestCase):
    def test_repeated_analysis_is_byte_identical(self):
        cells = historical_cells("A")
        first = A.dumps(A.analyse(cells, TEST_WINDOW))
        second = A.dumps(A.analyse(historical_cells("A"), TEST_WINDOW))
        self.assertEqual(first, second)

    def test_cell_order_does_not_change_the_report(self):
        cells = historical_cells("A")
        a = A.dumps(A.analyse(cells, TEST_WINDOW))
        b = A.dumps(A.analyse(list(reversed(cells)), TEST_WINDOW))
        self.assertEqual(a, b)


# ---------------------------------------------------------------- statistics

class TestFrozenStatistics(unittest.TestCase):
    def test_constants_match_the_protocol(self):
        self.assertEqual(A.P_STAR, 0.1751)
        self.assertEqual(A.ALPHA, 0.05)
        self.assertEqual(A.P1_ALTERNATIVE, 0.30)
        self.assertEqual(A.MIN_EVENTS, 40)

    def test_window_is_the_pre_registered_one(self):
        window = A.Window.oos()
        self.assertEqual(A._fmt(window.start_ms), "2026-08-31 00:00")
        self.assertEqual(A._fmt(window.end_ms), "2027-04-02 00:00")
        self.assertEqual((window.end_ms - window.start_ms) / 86_400_000, 214.0)

    def test_critical_values_match_the_protocol_table(self):
        for n, supportive, against in ((40, 12, 2), (60, 17, 5), (80, 21, 8), (100, 25, 10)):
            self.assertEqual(A.critical_values(n), (supportive, against), f"N={n}")

    def test_power_at_eighty_against_the_pre_registered_alternative(self):
        supportive, _ = A.critical_values(80)
        self.assertAlmostEqual(A.binom_sf(supportive, 80, 0.30), 0.80, places=2)

    def test_clopper_pearson_satisfies_its_defining_equations(self):
        for k, n in ((7, 37), (5, 37), (21, 80), (1, 1)):
            low, high = A.clopper_pearson(k, n)
            if k > 0:
                self.assertAlmostEqual(A.binom_sf(k, n, low), 0.025, places=9)
            if k < n:
                self.assertAlmostEqual(A.binom_cdf(k, n, high), 0.025, places=9)

    def test_clopper_pearson_degenerate_ends(self):
        self.assertEqual(A.clopper_pearson(0, 10)[0], 0.0)
        self.assertEqual(A.clopper_pearson(10, 10)[1], 1.0)


class TestDecisionFramework(unittest.TestCase):
    """Exercised on synthetic counts; never on real OOS data, which does not exist."""

    def _report(self, n: int, k: int) -> dict:
        supportive, against = A.critical_values(n)
        return {
            "window": {"is_oos": True, "label": "phase16-oos"},
            "test": {"n_events": n, "winning_events": k,
                     "supportive_threshold": supportive, "against_threshold": against},
        }

    def test_below_the_power_floor_is_always_inconclusive(self):
        for k in (0, 20, 39):
            verdict = A.decide(self._report(39, min(k, 39)))["verdict"]
            self.assertIn("INSUFFICIENT", verdict)

    def test_supportive_requires_the_threshold(self):
        self.assertIn("SUPPORTIVE", A.decide(self._report(80, 21))["verdict"])
        self.assertIn("INSUFFICIENT", A.decide(self._report(80, 20))["verdict"])

    def test_against_requires_the_lower_threshold(self):
        self.assertIn("AGAINST", A.decide(self._report(80, 8))["verdict"])
        self.assertIn("INSUFFICIENT", A.decide(self._report(80, 9))["verdict"])

    def test_all_three_verdicts_are_reachable(self):
        verdicts = {A.decide(self._report(80, k))["verdict"] for k in (5, 15, 25)}
        self.assertEqual(len(verdicts), 3)

    def test_a_non_oos_window_can_never_produce_a_verdict(self):
        report = self._report(80, 40)
        report["window"] = {"is_oos": False, "label": "phase15-historical"}
        self.assertEqual(A.decide(report)["verdict"], "NOT APPLICABLE")


if __name__ == "__main__":
    unittest.main()

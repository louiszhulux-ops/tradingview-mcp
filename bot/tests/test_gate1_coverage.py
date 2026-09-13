"""The coverage precondition.

Includes a pin against the real datasets. That check reads bar *timestamps* to
count coverage; it does not run the strategy engine, and it asserts nothing
about V53 parity.
"""

from __future__ import annotations

import csv
import unittest
from pathlib import Path

from bot.fixtures.loader import load_fixture
from bot.replay.coverage import CoverageCounts, check_coverage, count_coverage

REPO = Path(__file__).resolve().parents[2]
PARENT_DIR = REPO / "data" / "phase_c"
LTF_DIR = REPO / "data" / "phase_c_ltf"

FB_MS = 1784160000000
FC_MS = 1786233600000

#: Exactly what the audit established, pinned so a silent drift is visible.
EXPECTED = {
    ("MGC", "A"): (10386, 9813, 9677),
    ("MGC", "B"): (4668, 4668, 4668),
    ("MGC", "C"): (4164, 4164, 4164),
    ("MNQ", "A"): (10368, 9812, 9675),
    ("MNQ", "B"): (4668, 4668, 4668),
    ("MNQ", "C"): (4164, 4164, 4164),
}


def load_series(short: str) -> list[tuple[int, int]]:
    """(parent open_ts_ms, ltf sub-bar count) for one instrument."""
    with (PARENT_DIR / f"{short}1__5m.csv").open() as fh:
        parents = [int(row["timestamp"]) for row in csv.DictReader(fh)]
    present = set(parents)
    counts = dict.fromkeys(parents, 0)
    with (LTF_DIR / f"{short}1__1m.csv").open() as fh:
        for row in csv.DictReader(fh):
            ts = int(row["timestamp"])
            parent = ts - (ts % 300)
            if parent in present:
                counts[parent] += 1
    return [(ts * 1000, counts[ts]) for ts in parents]


class Counting(unittest.TestCase):

    def test_counts_only_in_fold_bars(self):
        series = [(FB_MS - 300_000, 5), (FB_MS, 5), (FC_MS, 5)]
        self.assertEqual(count_coverage(series, "A").fold_bars, 1)
        self.assertEqual(count_coverage(series, "B").fold_bars, 1)
        self.assertEqual(count_coverage(series, "C").fold_bars, 1)

    def test_empty_ltf_array_counts_toward_fold_bars_only(self):
        counts = count_coverage([(FB_MS, 5), (FB_MS + 300_000, 0)], "B")
        self.assertEqual((counts.fold_bars, counts.fold_bars_with_ltf), (2, 1))

    def test_first_parent_without_ltf_is_recorded(self):
        counts = count_coverage([(FB_MS, 5), (FB_MS + 300_000, 0),
                                 (FB_MS + 600_000, 0)], "B")
        self.assertEqual(counts.first_parent_without_ltf_ms, FB_MS + 300_000)

    def test_no_gap_means_no_first_divergent_parent(self):
        self.assertIsNone(count_coverage([(FB_MS, 5)], "B").first_parent_without_ltf_ms)

    def test_with_ltf_cannot_exceed_fold_bars(self):
        with self.assertRaises(ValueError):
            CoverageCounts(fold_bars=10, fold_bars_with_ltf=11)


class Checking(unittest.TestCase):

    def funnel(self, bars: int, with_ltf: int) -> dict:
        return {"fold_bars": bars, "fold_bars_with_ltf": with_ltf}

    def check(self, actual: CoverageCounts, bars: int, with_ltf: int):
        return check_coverage(cell_id="v53-MGC-L-1m-B", instrument="MGC1!",
                              fold="B", ltf_timeframe="1m", actual=actual,
                              fixture_funnel=self.funnel(bars, with_ltf))

    def test_exact_coverage_passes(self):
        self.assertTrue(self.check(CoverageCounts(4668, 4668), 4668, 4668).ok)

    def test_short_ltf_coverage_fails(self):
        result = self.check(CoverageCounts(10386, 9677, 1779660000000), 10386, 9813)
        self.assertFalse(result.ok)
        self.assertEqual(result.shortfall, 136)

    def test_wrong_fold_bars_fails(self):
        self.assertFalse(self.check(CoverageCounts(4667, 4667), 4668, 4668).ok)

    def test_report_names_expected_and_actual(self):
        text = "\n".join(self.check(CoverageCounts(10386, 9677, 1779660000000),
                                    10386, 9813).report_lines())
        for fragment in ("expected 10386", "actual 9677", "expected 9813",
                         "shortfall", "1779660000000", "no reconstruction"):
            self.assertIn(fragment, text)

    def test_report_says_when_first_divergence_is_not_determinable(self):
        text = "\n".join(self.check(CoverageCounts(4668, 4668), 4668, 4667).report_lines())
        self.assertIn("not determinable", text)

    def test_fixture_without_coverage_counters_is_not_runnable(self):
        with self.assertRaises(ValueError):
            check_coverage(cell_id="x", instrument="MGC1!", fold="B",
                           ltf_timeframe="1m", actual=CoverageCounts(1, 1),
                           fixture_funnel={"fold_bars": 1, "fold_bars_with_ltf": None})


class AgainstTheRealDatasets(unittest.TestCase):
    """Pins the audit's numbers. Counts timestamps; runs no strategy."""

    @classmethod
    def setUpClass(cls):
        cls.series = {short: load_series(short) for short in ("MGC", "MNQ")}

    def test_coverage_matches_the_audited_figures(self):
        for (short, fold), (bars, expected_with, actual_with) in EXPECTED.items():
            with self.subTest(instrument=short, fold=fold):
                counts = count_coverage(self.series[short], fold)
                self.assertEqual(counts.fold_bars, bars)
                self.assertEqual(counts.fold_bars_with_ltf, actual_with)
                fixture = load_fixture(f"v53-{short}-L-1m-{fold}")
                self.assertEqual(fixture["funnel"]["fold_bars"], bars)
                self.assertEqual(fixture["funnel"]["fold_bars_with_ltf"], expected_with)

    def test_fold_a_fails_the_precondition_on_both_instruments(self):
        for short, shortfall in (("MGC", 136), ("MNQ", 137)):
            with self.subTest(instrument=short):
                counts = count_coverage(self.series[short], "A")
                result = check_coverage(
                    cell_id=f"v53-{short}-L-1m-A", instrument=f"{short}1!",
                    fold="A", ltf_timeframe="1m", actual=counts,
                    fixture_funnel=load_fixture(f"v53-{short}-L-1m-A")["funnel"])
                self.assertFalse(result.ok)
                self.assertEqual(result.shortfall, shortfall)

    def test_folds_b_and_c_satisfy_the_precondition(self):
        for short in ("MGC", "MNQ"):
            for fold in ("B", "C"):
                with self.subTest(instrument=short, fold=fold):
                    counts = count_coverage(self.series[short], fold)
                    result = check_coverage(
                        cell_id=f"v53-{short}-L-1m-{fold}", instrument=f"{short}1!",
                        fold=fold, ltf_timeframe="1m", actual=counts,
                        fixture_funnel=load_fixture(f"v53-{short}-L-1m-{fold}")["funnel"])
                    self.assertTrue(result.ok)
                    self.assertEqual(result.shortfall, 0)

    def test_no_3m_dataset_exists(self):
        """12 of 24 cells are NO-DATA because these files do not exist."""
        for short in ("MGC", "MNQ"):
            self.assertFalse((LTF_DIR / f"{short}1__3m.csv").exists())
            self.assertEqual(sorted(p.name for p in LTF_DIR.glob("*3m*")), [])


if __name__ == "__main__":
    unittest.main()

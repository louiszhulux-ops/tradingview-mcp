"""The loader consumes recorded parent attribution instead of re-deriving it.

Infrastructure repair only. Nothing here runs V53, adjudicates Gate 1, or
registers a dataset; the parent-attributed 3m candidates remain `CANDIDATE` and
are still absent from `data/phase_c_ltf_manifest.json`.

The defect being locked out: `build_parents` used to bucket every LTF bar by
`ts - (ts % 300)`. For 1m that is correct — a 1m bar cannot straddle a 5m
boundary. For 3m it is wrong on 11,912 of 29,780 bars (40.0%), because
TradingView attributes a straddling bar FORWARD, to the parent it ends in.
"""

from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from decimal import Decimal as D
from pathlib import Path

from bot.contracts.enums import Timeframe
from bot.data.bars import Bar, BarContractError, ParentBar
from bot.replay.loader import DatasetLoadError, build_parents, read_rows

REPO = Path(__file__).resolve().parents[2]
LTF = REPO / "data" / "phase_c_ltf"

PARENT_S = 300
#: The case the eligibility audit singled out.
BOUNDARY_PARENT = 1788134100      # 2026-08-30 23:55:00Z
STRADDLER = 1788134040            # 23:54 — floor would say 23:50
IN_PARENT = 1788134220            # 23:57 — floor agrees

#: A parent a day earlier, used for the rejection cases. The real boundary
#: parent is the LAST pre-FE parent, so a sub-bar running past its close would
#: trip the A1 pre-FE guard before the ParentBar contract is ever consulted.
BASE_PARENT = BOUNDARY_PARENT - 86_400


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)


class ReadRows(unittest.TestCase):
    """A + B: parent_ts round-trips when present, absent files unaffected."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_parent_ts_is_retained_when_the_column_exists(self):
        p = self.tmp / "with.csv"
        write_csv(p, ["timestamp", "open", "high", "low", "close", "parent_ts"],
                  [[STRADDLER, "1", "2", "0.5", "1.5", BOUNDARY_PARENT]])
        rows = read_rows(p)
        self.assertEqual(len(rows[0]), 5)
        self.assertEqual(rows[0][0], STRADDLER)
        self.assertEqual(rows[0][4], BOUNDARY_PARENT)
        self.assertIsInstance(rows[0][4], int)

    def test_files_without_parent_ts_are_read_exactly_as_before(self):
        p = self.tmp / "without.csv"
        write_csv(p, ["timestamp", "high", "low", "close"],
                  [[STRADDLER, "2", "0.5", "1.5"]])
        rows = read_rows(p)
        self.assertEqual(len(rows[0]), 4)
        self.assertEqual(rows[0], (STRADDLER, D("2"), D("0.5"), D("1.5")))

    def test_an_empty_parent_ts_is_an_error_not_a_silent_fallback(self):
        p = self.tmp / "empty.csv"
        write_csv(p, ["timestamp", "high", "low", "close", "parent_ts"],
                  [[STRADDLER, "2", "0.5", "1.5", ""]])
        with self.assertRaises(DatasetLoadError) as ctx:
            read_rows(p)
        self.assertIn("parent_ts is empty", str(ctx.exception))

    def test_a_malformed_parent_ts_is_an_error(self):
        p = self.tmp / "bad.csv"
        write_csv(p, ["timestamp", "high", "low", "close", "parent_ts"],
                  [[STRADDLER, "2", "0.5", "1.5", "not-a-number"]])
        with self.assertRaises(DatasetLoadError) as ctx:
            read_rows(p)
        self.assertIn("not an integer", str(ctx.exception))

    def test_the_real_1m_candidate_still_reads_as_four_tuples(self):
        rows = read_rows(LTF / "MGC1__1m.csv")
        self.assertTrue(all(len(r) == 4 for r in rows[:50]))

    def test_the_real_parent_attributed_3m_candidate_reads_as_five_tuples(self):
        rows = read_rows(LTF / "MGC1__3m_parent_attributed.csv")
        self.assertTrue(all(len(r) == 5 for r in rows[:50]))


class BuildParents(unittest.TestCase):
    """C + D + H: recorded attribution wins; floor would give a different answer."""

    def parents(self):
        return [(BOUNDARY_PARENT - PARENT_S, D("2"), D("0.5"), D("1.5")),
                (BOUNDARY_PARENT, D("2"), D("0.5"), D("1.5"))]

    def ltf(self, with_parent: bool):
        rows = [(STRADDLER, D("2"), D("0.5"), D("1.5")),
                (IN_PARENT, D("2"), D("0.5"), D("1.5"))]
        if not with_parent:
            return rows
        return [r + (BOUNDARY_PARENT,) for r in rows]

    def test_recorded_parent_ts_is_used_verbatim(self):
        built = build_parents("MNQ1!", self.parents(), self.ltf(True), Timeframe.M3)
        by_open = {p.bar.open_ts_ms // 1000: p for p in built}
        self.assertEqual(by_open[BOUNDARY_PARENT].ltf_count, 2)
        self.assertEqual(by_open[BOUNDARY_PARENT - PARENT_S].ltf_count, 0)

    def test_the_boundary_parent_holds_both_recorded_bars(self):
        built = build_parents("MNQ1!", self.parents(), self.ltf(True), Timeframe.M3)
        target = next(p for p in built if p.bar.open_ts_ms // 1000 == BOUNDARY_PARENT)
        got = [b.open_ts_ms // 1000 for b in target.ltf_bars]
        self.assertEqual(got, [STRADDLER, IN_PARENT])

    def test_floor_attribution_of_a_3m_straddler_is_rejected_outright(self):
        """H: the regression guard, and it bites harder than mis-assignment.

        Floor bucketing puts the 23:54 bar under parent 23:50 — but that bar
        ends at 23:57, *after* 23:50 closes. So a revert to geometric
        attribution for 3m does not silently mis-assign: `ParentBar` rejects it.
        The contract and the loader now agree that forward attribution is the
        only coherent reading of a 3m straddler.
        """
        with self.assertRaises(BarContractError) as ctx:
            build_parents("MNQ1!", self.parents(), self.ltf(False), Timeframe.M3)
        self.assertIn("ends after its parent", str(ctx.exception))

    def test_floor_attribution_remains_correct_for_1m(self):
        """G: a 1m bar cannot straddle, so the fallback is still right there."""
        parents = [(BOUNDARY_PARENT, D("2"), D("0.5"), D("1.5"))]
        rows = [(BOUNDARY_PARENT + 60 * i, D("2"), D("0.5"), D("1.5")) for i in range(5)]
        built = build_parents("MNQ1!", parents, rows, Timeframe.M1)
        self.assertEqual(built[0].ltf_count, 5)
        self.assertTrue(built[0].ltf_complete)

    def test_a_recorded_parent_outside_the_exported_range_is_skipped(self):
        rows = [(STRADDLER, D("2"), D("0.5"), D("1.5"), 1)]
        built = build_parents("MNQ1!", self.parents(), rows, Timeframe.M3)
        self.assertEqual(sum(p.ltf_count for p in built), 0)


class ParentBarContract(unittest.TestCase):
    """E + F: the straddler is admitted; real violations still rejected."""

    def parent(self, open_s: int = BASE_PARENT) -> Bar:
        ms = open_s * 1000
        return Bar("MNQ1!", Timeframe.M5, ms, ms + 300_000,
                   None, D("10"), D("8"), D("9"))

    def sub(self, open_s: int, tf: Timeframe = Timeframe.M3) -> Bar:
        ms = open_s * 1000
        return Bar("MNQ1!", tf, ms, ms + tf.minutes * 60_000,
                   None, D("10"), D("8"), D("9"))

    def test_forward_attributed_straddler_is_accepted(self):
        """The real recorded case: parent 23:55 holding 23:54 and 23:57."""
        p = ParentBar(self.parent(BOUNDARY_PARENT), Timeframe.M3,
                      (self.sub(STRADDLER), self.sub(IN_PARENT)))
        self.assertEqual(p.ltf_count, 2)
        self.assertLess(p.ltf_bars[0].open_ts_ms, p.bar.open_ts_ms)

    def test_sub_bar_ending_after_parent_close_is_rejected(self):
        # opens inside the parent but runs past its close
        with self.assertRaises(BarContractError) as ctx:
            ParentBar(self.parent(), Timeframe.M3, (self.sub(BASE_PARENT + 240),))
        self.assertIn("ends after its parent", str(ctx.exception))

    def test_sub_bar_more_than_one_period_early_is_rejected(self):
        with self.assertRaises(BarContractError):
            ParentBar(self.parent(), Timeframe.M3, (self.sub(BASE_PARENT - 240),))

    def test_a_sub_bar_exactly_one_period_early_does_not_overlap_and_is_rejected(self):
        with self.assertRaises(BarContractError) as ctx:
            ParentBar(self.parent(), Timeframe.M3, (self.sub(BASE_PARENT - 180),))
        self.assertIn("does not overlap", str(ctx.exception))

    def test_a_sub_bar_starting_at_or_after_parent_close_is_rejected(self):
        with self.assertRaises(BarContractError):
            ParentBar(self.parent(), Timeframe.M3, (self.sub(BASE_PARENT + 300),))

    def test_ordering_and_non_overlap_are_preserved(self):
        with self.assertRaises(BarContractError):
            ParentBar(self.parent(BOUNDARY_PARENT), Timeframe.M3,
                      (self.sub(IN_PARENT), self.sub(STRADDLER)))   # out of order

    def test_1m_nesting_is_unaffected(self):
        """G: a 1m bar cannot straddle, so nothing changes for 1m."""
        subs = tuple(self.sub(BASE_PARENT + 60 * i, Timeframe.M1) for i in range(5))
        p = ParentBar(self.parent(), Timeframe.M1, subs)
        self.assertEqual(p.ltf_count, 5)
        self.assertTrue(p.ltf_complete)
        with self.assertRaises(BarContractError):
            ParentBar(self.parent(), Timeframe.M1,
                      (self.sub(BASE_PARENT - 120, Timeframe.M1),))


if __name__ == "__main__":
    unittest.main()

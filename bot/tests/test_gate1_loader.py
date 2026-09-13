"""The Gate 1 dataset loader: what it accepts, and everything it refuses."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from decimal import Decimal as D
from pathlib import Path

from bot.contracts.enums import Timeframe
from bot.data.bars import BarContractError
from bot.guards import FE_MS
from bot.replay.datasets import REPO_ROOT, DatasetStatusError
from bot.replay.loader import (
    PROVENANCE, REGISTRY, DatasetLoadError, build_parents, load_cell_dataset,
    read_rows, resolve_status,
)
from bot.replay.verdicts import DatasetStatus

AUTH = DatasetStatus.AUTHORITATIVE
CAND = DatasetStatus.CANDIDATE


class StatusResolution(unittest.TestCase):
    """Specification gap G1: how per-dataset statuses combine per cell."""

    def test_real_cell_resolves_to_candidate(self):
        resolved = resolve_status([REGISTRY[("MGC1!", tf)]
                                   for tf in (Timeframe.M5, Timeframe.M1)])
        self.assertIs(resolved.status, CAND)
        self.assertFalse(resolved.authoritative)

    def test_partial_is_recorded_as_unresolved_not_swallowed(self):
        resolved = resolve_status([REGISTRY[("MGC1!", tf)]
                                   for tf in (Timeframe.M5, Timeframe.M1)])
        paths = [path for path, _ in resolved.unresolved]
        self.assertIn("data/phase_c/MGC1__5m.csv", paths)

    def test_the_raw_declaration_is_preserved_verbatim(self):
        resolved = resolve_status([REGISTRY[("MGC1!", tf)]
                                   for tf in (Timeframe.M5, Timeframe.M1)])
        raws = {path: raw for path, raw in resolved.declarations}
        self.assertEqual(raws["data/phase_c/MGC1__5m.csv"], "PARTIAL")
        self.assertTrue(raws["data/phase_c_ltf/MGC1__1m.csv"].startswith("CANDIDATE"))

    def test_candidate_is_never_upgraded(self):
        for _ in range(3):
            self.assertIs(resolve_status([REGISTRY[("MNQ1!", tf)]
                                          for tf in (Timeframe.M5, Timeframe.M1)]).status,
                          CAND)

    def test_no_registered_dataset_is_authoritative_today(self):
        for instrument in ("MGC1!", "MNQ1!"):
            for ltf in (Timeframe.M1, Timeframe.M3):
                with self.subTest(instrument=instrument, ltf=ltf):
                    self.assertIs(
                        resolve_status([REGISTRY[(instrument, tf)]
                                        for tf in (Timeframe.M5, ltf)]).status, CAND)


class Loading(unittest.TestCase):

    def test_valid_candidate_dataset_loads_as_candidate(self):
        loaded = load_cell_dataset(cell_id="v53-MGC-L-1m-B", instrument="MGC1!",
                                   fold="B", ltf=Timeframe.M1)
        self.assertIs(loaded.status, CAND)
        self.assertTrue(loaded.data_present)
        self.assertEqual(len(loaded.parents), 19218)

    def test_missing_file_yields_no_bars_and_names_what_is_absent(self):
        loaded = load_cell_dataset(cell_id="v53-MGC-L-3m-B", instrument="MGC1!",
                                   fold="B", ltf=Timeframe.M3)
        self.assertFalse(loaded.data_present)
        self.assertEqual(loaded.parents, ())
        self.assertEqual(loaded.cell.missing, ("data/phase_c_ltf/MGC1__3m.csv",))

    def test_provenance_carries_everything_criterion_0_requires(self):
        loaded = load_cell_dataset(cell_id="v53-MNQ-S-1m-C", instrument="MNQ1!",
                                   fold="C", ltf=Timeframe.M1)
        text = "\n".join(loaded.provenance_lines())
        for fragment in ("MNQ1!", "fold              C", "1m", "CANDIDATE",
                         "data/phase_c/MNQ1__5m.csv",
                         "data/phase_c_ltf/MNQ1__1m.csv",
                         "sha256", "capture", "status UNRESOLVED"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_every_registered_timeframe_declares_a_capture(self):
        for timeframe in (Timeframe.M5, Timeframe.M1, Timeframe.M3):
            self.assertIn(timeframe, PROVENANCE)
        self.assertEqual(PROVENANCE[Timeframe.M3], "no capture exists")


class RefusesBadFiles(unittest.TestCase):
    """A present file that cannot be trusted is refused, never used anyway."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for rel, _ in REGISTRY.values():
            source = REPO_ROOT / rel
            if source.is_file():
                target = self.tmp / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_intact_copy_loads(self):
        loaded = load_cell_dataset(cell_id="c", instrument="MGC1!", fold="B",
                                   ltf=Timeframe.M1, root=self.tmp)
        self.assertTrue(loaded.data_present)

    def test_sha_mismatch_is_refused(self):
        target = self.tmp / "data/phase_c_ltf/MGC1__1m.csv"
        target.write_text(target.read_text() + "1788134000,1,1,1\n")
        with self.assertRaises(DatasetLoadError) as ctx:
            load_cell_dataset(cell_id="c", instrument="MGC1!", fold="B",
                              ltf=Timeframe.M1, root=self.tmp)
        self.assertIn("does not match its recorded sha256", str(ctx.exception))

    def test_parent_sha_mismatch_is_refused_too(self):
        target = self.tmp / "data/phase_c/MGC1__5m.csv"
        target.write_text(target.read_text().replace("4555.5", "4555.6", 1))
        with self.assertRaises(DatasetLoadError):
            load_cell_dataset(cell_id="c", instrument="MGC1!", fold="B",
                              ltf=Timeframe.M1, root=self.tmp)

    def test_missing_columns_are_refused(self):
        target = self.tmp / "data/phase_c_ltf/MNQ1__1m.csv"
        target.write_text("timestamp,high,low\n1,2,1\n")
        with self.assertRaises(DatasetLoadError):
            read_rows(target)


class NoReconstructionPath(unittest.TestCase):
    """Nothing in the loader can invent a bar."""

    def rows(self, *stamps):
        return [(ts, D("10"), D("8"), D("9")) for ts in stamps]

    def test_parent_with_no_sub_bars_gets_an_empty_array(self):
        parents = build_parents("MGC1!", self.rows(1779660000), [], Timeframe.M1)
        self.assertEqual(parents[0].ltf_count, 0)
        self.assertFalse(parents[0].ltf_complete)

    def test_a_short_parent_is_not_padded(self):
        parents = build_parents("MGC1!", self.rows(1779660000),
                                self.rows(1779660000, 1779660060), Timeframe.M1)
        self.assertEqual(parents[0].ltf_count, 2)

    def test_an_interior_tradeless_minute_is_preserved_not_filled(self):
        # Three MGC parents in the real data look exactly like this.
        parents = build_parents(
            "MGC1!", self.rows(1779660000),
            self.rows(1779660000, 1779660060, 1779660120, 1779660240),
            Timeframe.M1)
        offsets = [(b.open_ts_ms // 1000 - 1779660000) // 60 for b in parents[0].ltf_bars]
        self.assertEqual(offsets, [0, 1, 2, 4])

    def test_sub_bars_never_cross_into_a_neighbouring_parent(self):
        parents = build_parents("MGC1!", self.rows(1779660000, 1779660300),
                                self.rows(1779660060, 1779660360), Timeframe.M1)
        self.assertEqual([p.ltf_count for p in parents], [1, 1])

    def test_5m_is_never_used_as_its_own_lower_timeframe(self):
        with self.assertRaises(BarContractError):
            build_parents("MGC1!", self.rows(1779660000),
                          self.rows(1779660000), Timeframe.M5)

    def test_loaded_bars_carry_no_invented_open_or_volume(self):
        parents = build_parents("MGC1!", self.rows(1779660000),
                                self.rows(1779660000), Timeframe.M1)
        self.assertFalse(parents[0].bar.has_open)
        self.assertFalse(parents[0].bar.has_volume)
        self.assertFalse(parents[0].ltf_bars[0].has_open)


class BoundaryBar(unittest.TestCase):
    """The last pre-FE bar closes exactly at FE and must survive."""

    def test_final_bars_of_the_real_series_load(self):
        loaded = load_cell_dataset(cell_id="c", instrument="MGC1!", fold="C",
                                   ltf=Timeframe.M1)
        last = loaded.parents[-1]
        self.assertEqual(last.bar.close_ts_ms, FE_MS)
        self.assertEqual(last.ltf_bars[-1].close_ts_ms, FE_MS)


if __name__ == "__main__":
    unittest.main()

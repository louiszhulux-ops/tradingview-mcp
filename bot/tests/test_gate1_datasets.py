"""Dataset status is read, never manufactured and never upgraded."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from bot.replay.datasets import (
    LTF_MANIFEST, PARENT_MANIFEST, REPO_ROOT, CellDataset, DatasetRef,
    DatasetStatusError, manifest_artifacts, parse_status, read_manifest_status,
)
from bot.replay.verdicts import DatasetStatus

AUTH = DatasetStatus.AUTHORITATIVE
CAND = DatasetStatus.CANDIDATE


class ParseStatus(unittest.TestCase):

    def test_bare_authoritative(self):
        self.assertIs(parse_status("AUTHORITATIVE"), AUTH)
        self.assertIs(parse_status("  AUTHORITATIVE  "), AUTH)

    def test_qualified_authoritative_is_refused(self):
        """A qualifier can only ever weaken a claim, so it must not be ignored."""
        for text in ("AUTHORITATIVE -- probably", "AUTHORITATIVE (pending)",
                     "NEARLY AUTHORITATIVE", "authoritative"):
            with self.subTest(text=text), self.assertRaises(DatasetStatusError):
                parse_status(text)

    def test_qualified_candidate_is_accepted(self):
        self.assertIs(parse_status(
            "CANDIDATE -- NOT FROZEN, NOT AUTHORITATIVE, NOT GROUND TRUTH"), CAND)
        self.assertIs(parse_status("CANDIDATE"), CAND)

    def test_partial_is_not_a_gate_status(self):
        with self.assertRaises(DatasetStatusError):
            parse_status("PARTIAL")

    def test_unknown_and_empty_are_refused(self):
        for value in ("", "   ", None, 7, "FROZEN", "OK", "UNKNOWN"):
            with self.subTest(value=value), self.assertRaises(DatasetStatusError):
                parse_status(value)

    def test_there_is_no_path_from_unknown_to_authoritative(self):
        for value in ("PARTIAL", "FROZEN", "VERIFIED", "EXACT", "GOLD"):
            with self.subTest(value=value):
                try:
                    self.assertIsNot(parse_status(value), AUTH)
                except DatasetStatusError:
                    pass


class RealManifests(unittest.TestCase):

    def test_p9_candidate_stays_candidate(self):
        self.assertIs(read_manifest_status(LTF_MANIFEST), CAND)

    def test_p9_manifest_says_so_itself(self):
        status = json.loads(LTF_MANIFEST.read_text())["status"]
        self.assertIn("NOT AUTHORITATIVE", status)

    def test_frozen_parent_manifest_declares_no_gate_status(self):
        """`PARTIAL` is a completeness note, not a Gate 1 status. Refused."""
        with self.assertRaises(DatasetStatusError):
            read_manifest_status(PARENT_MANIFEST)

    def test_missing_manifest_raises(self):
        with self.assertRaises(DatasetStatusError):
            read_manifest_status(Path("/nonexistent/manifest.json"))

    def test_artifact_hashes_are_readable(self):
        artifacts = manifest_artifacts(LTF_MANIFEST)
        self.assertIn("data/phase_c_ltf/MGC1__1m.csv", artifacts)
        self.assertEqual(len(artifacts["data/phase_c_ltf/MGC1__1m.csv"]), 64)


class Refs(unittest.TestCase):

    def ref(self, path: str) -> DatasetRef:
        return DatasetRef("ltf", path,
                          manifest_artifacts(LTF_MANIFEST).get(path, ""), True)

    def test_recorded_hash_matches_the_file_on_disk(self):
        self.assertTrue(self.ref("data/phase_c_ltf/MGC1__1m.csv").verify(REPO_ROOT))

    def test_wrong_hash_does_not_verify(self):
        self.assertFalse(DatasetRef("ltf", "data/phase_c_ltf/MGC1__1m.csv",
                                    "0" * 64, True).verify(REPO_ROOT))

    def test_absent_file_does_not_verify(self):
        self.assertFalse(DatasetRef("ltf", "data/phase_c_ltf/MGC1__3m.csv",
                                    "0" * 64, False).verify(REPO_ROOT))


class Cells(unittest.TestCase):

    def make(self, refs, status=CAND) -> CellDataset:
        return CellDataset("v53-MGC-L-1m-B", "MGC1!", "B", "1m", status, refs,
                           "P-9 request.security_lower_tf extraction")

    def test_all_files_present(self):
        cell = self.make((DatasetRef("parent", "a", "x", True),
                          DatasetRef("ltf", "b", "y", True)))
        self.assertTrue(cell.data_present)
        self.assertEqual(cell.missing, ())

    def test_any_missing_file_makes_the_cell_no_data(self):
        cell = self.make((DatasetRef("parent", "a", "x", True),
                          DatasetRef("ltf", "b", "y", False)))
        self.assertFalse(cell.data_present)
        self.assertEqual(cell.missing, ("b",))

    def test_a_cell_with_no_refs_is_not_present(self):
        self.assertFalse(self.make(()).data_present)

    def test_status_must_be_a_dataset_status(self):
        with self.assertRaises(DatasetStatusError):
            self.make((DatasetRef("parent", "a", "x", True),), status="CANDIDATE")


if __name__ == "__main__":
    unittest.main()

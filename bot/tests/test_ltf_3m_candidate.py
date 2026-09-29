"""The P-11 3m candidate datasets, validated and pinned.

Data acquisition evidence only. **No test here runs V53, compares against a
golden strategy output, or asserts parity.** The datasets are `CANDIDATE` and
cannot support a parity claim.
"""

from __future__ import annotations

import csv
import hashlib
import json
import unittest
from decimal import Decimal
from pathlib import Path

from bot.guards import FE_MS

REPO = Path(__file__).resolve().parents[2]
LTF = REPO / "data" / "phase_c_ltf"
MANIFEST = LTF / "3m_candidate_manifest.json"

FE_S = FE_MS // 1000
TF_S = 180
PARENT_S = 300

#: TradingView's 5m chart-series history limit at extraction time.
FIRST_SERVED_S = 1780264800          # 2026-05-31T22:00:00Z
#: Phase-C parent coverage start, seven days earlier and no longer served.
REQUESTED_START_S = 1779660000       # 2026-05-24T22:00:00Z


def rows(short: str) -> list[tuple[int, Decimal, Decimal, Decimal, Decimal]]:
    out = []
    with (LTF / f"{short}1__3m.csv").open(newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == ["timestamp", "open", "high", "low", "close"]
        for r in reader:
            out.append((int(r["timestamp"]), Decimal(r["open"]), Decimal(r["high"]),
                        Decimal(r["low"]), Decimal(r["close"])))
    return out


def parents(short: str) -> list[int]:
    with (REPO / "data" / "phase_c" / f"{short}1__5m.csv").open(newline="") as fh:
        return [int(r["timestamp"]) for r in csv.DictReader(fh)]


class Contract(unittest.TestCase):

    def test_both_files_exist_with_the_exact_header(self):
        for short in ("MGC", "MNQ"):
            with self.subTest(short=short):
                self.assertTrue((LTF / f"{short}1__3m.csv").is_file())
                self.assertEqual(len(rows(short)), 29780)

    def test_the_1m_candidates_were_not_disturbed(self):
        expected = {
            "MGC1__1m.csv": "eeba6ffb7fb44a92b5be9d9ac8f0330cbf85d9a9d8b45d9c90a373cdf134af7b",
            "MNQ1__1m.csv": "7e4eab7fb51c2f801db17d5452fe3d6dcbcc5fe81af97f260110091361dac55a",
        }
        for name, digest in expected.items():
            with self.subTest(name=name):
                self.assertEqual(
                    hashlib.sha256((LTF / name).read_bytes()).hexdigest(), digest)


class Integrity(unittest.TestCase):

    def test_timestamps_are_strictly_increasing(self):
        for short in ("MGC", "MNQ"):
            ts = [r[0] for r in rows(short)]
            with self.subTest(short=short):
                self.assertEqual(ts, sorted(ts))
                self.assertTrue(all(b > a for a, b in zip(ts, ts[1:])))

    def test_no_duplicate_timestamps(self):
        for short in ("MGC", "MNQ"):
            ts = [r[0] for r in rows(short)]
            with self.subTest(short=short):
                self.assertEqual(len(ts), len(set(ts)))

    def test_ohlc_ordering_is_valid(self):
        for short in ("MGC", "MNQ"):
            for t, o, h, l, c in rows(short):
                if not (h >= max(o, c) and l <= min(o, c)):
                    self.fail(f"{short} {t}: OHLC ordering violated")

    def test_every_bar_opens_before_fe_and_closes_no_later_than_fe(self):
        for short in ("MGC", "MNQ"):
            for t, *_ in rows(short):
                self.assertLess(t, FE_S, f"{short} {t} opens at/after FE")
                self.assertLessEqual(t + TF_S, FE_S, f"{short} {t} closes after FE")

    def test_no_post_fe_contamination(self):
        for short in ("MGC", "MNQ"):
            with self.subTest(short=short):
                self.assertEqual([t for t, *_ in rows(short) if t >= FE_S], [])

    def test_the_last_bar_closes_exactly_on_fe(self):
        """The boundary bar is real pre-FE data and must be present."""
        for short in ("MGC", "MNQ"):
            with self.subTest(short=short):
                self.assertEqual(rows(short)[-1][0] + TF_S, FE_S)

    def test_every_timestamp_sits_on_the_180_second_grid(self):
        for short in ("MGC", "MNQ"):
            with self.subTest(short=short):
                self.assertTrue(all(t % TF_S == 0 for t, *_ in rows(short)))


class Geometry(unittest.TestCase):
    """3 does not divide 5; the mapping is measured, never assumed."""

    def test_aggregate_ratio_is_exactly_five_thirds(self):
        for short in ("MGC", "MNQ"):
            n = len(rows(short))
            with self.subTest(short=short):
                self.assertEqual(n, 29780)
                self.assertAlmostEqual(n / 17868, 5 / 3, places=6)

    def test_two_fifths_of_bars_straddle_a_5m_boundary(self):
        """A straddling bar is real and is not discarded."""
        for short in ("MGC", "MNQ"):
            ts = [t for t, *_ in rows(short)]
            straddle = [t for t in ts if (t % PARENT_S) + TF_S > PARENT_S]
            aligned = [t for t in ts if t % PARENT_S == 0]
            with self.subTest(short=short):
                self.assertEqual(len(straddle), 11912)
                self.assertEqual(len(aligned), 5956)

    def test_geometric_overlap_and_tradingview_attribution_differ(self):
        """The load-bearing finding for U3: they are **not** the same mapping.

        Geometrically, a 5m parent overlaps 2 or 3 three-minute bars, because a
        straddling bar overlaps two parents at once. TradingView nevertheless
        hands each 3m bar to exactly **one** parent, so the array a parent
        actually receives holds 1 or 2 bars. The two distributions are precise
        complements — the parents that overlap 3 are the ones given 1.

        Consequence: **TradingView's attribution cannot be reconstructed from
        timestamp geometry.** A loader must consume the attribution it is given
        and must never re-derive it, or it will hand V53 a different LTF array
        than the artifact saw.
        """
        for short in ("MGC", "MNQ"):
            counts: dict[int, int] = {}
            for t, *_ in rows(short):
                for q in (t - (t % PARENT_S) - PARENT_S,
                          t - (t % PARENT_S),
                          t - (t % PARENT_S) + PARENT_S):
                    if t < q + PARENT_S and t + TF_S > q:
                        counts[q] = counts.get(q, 0) + 1
            histogram: dict[int, int] = {}
            for v in counts.values():
                histogram[v] = histogram.get(v, 0) + 1
            with self.subTest(short=short, rule="geometric overlap"):
                self.assertEqual(histogram, {2: 11912, 3: 5956})

        # What TradingView actually delivered, recorded at extraction time.
        manifest = json.loads(MANIFEST.read_text())
        self.assertEqual(
            manifest["geometry_3m_vs_5m"]["parents_with_one_sub_bar"], 5956)
        self.assertEqual(
            manifest["geometry_3m_vs_5m"]["parents_with_two_sub_bars"], 11912)
        self.assertFalse(
            manifest["geometry_3m_vs_5m"]["third_slot_overflow_detector_fired"])
        self.assertEqual(
            manifest["geometry_3m_vs_5m"]["duplicate_bars_across_parents"], 0)


class CoverageAndTruncation(unittest.TestCase):
    """The head truncation is recorded as a fact, not worked around."""

    def covered(self, short: str) -> set[int]:
        ps = set(parents(short))
        out = set()
        for t, *_ in rows(short):
            for q in (t - (t % PARENT_S) - PARENT_S,
                      t - (t % PARENT_S),
                      t - (t % PARENT_S) + PARENT_S):
                if q in ps and t < q + PARENT_S and t + TF_S > q:
                    out.add(q)
        return out

    def test_coverage_starts_at_the_history_limit_not_the_requested_start(self):
        for short in ("MGC", "MNQ"):
            with self.subTest(short=short):
                self.assertEqual(rows(short)[0][0], FIRST_SERVED_S)
                self.assertGreater(FIRST_SERVED_S, REQUESTED_START_S)

    def test_the_stream_does_not_reach_the_complete_pre_fe_window(self):
        for short, missing in (("MGC", 1350), ("MNQ", 1332)):
            cov = self.covered(short)
            absent = [p for p in parents(short) if p not in cov]
            with self.subTest(short=short):
                self.assertEqual(len(cov), 17868)
                self.assertEqual(len(absent), missing)
                self.assertEqual(absent[0], REQUESTED_START_S)

    def test_every_missing_parent_is_at_the_head_contiguously(self):
        """Truncation is a head cut, not scattered holes."""
        for short in ("MGC", "MNQ"):
            cov = self.covered(short)
            ps = parents(short)
            absent = [p for p in ps if p not in cov]
            with self.subTest(short=short):
                self.assertEqual(absent, ps[:len(absent)])
                self.assertLess(absent[-1], FIRST_SERVED_S)

    def test_every_served_parent_carries_at_least_one_sub_bar(self):
        for short in ("MGC", "MNQ"):
            cov = self.covered(short)
            served = [p for p in parents(short) if p >= FIRST_SERVED_S]
            with self.subTest(short=short):
                self.assertEqual(sorted(cov), sorted(served))


class Provenance(unittest.TestCase):

    def setUp(self):
        self.m = json.loads(MANIFEST.read_text())

    def test_status_is_candidate_and_never_authoritative(self):
        self.assertTrue(self.m["status"].startswith("CANDIDATE"))
        self.assertNotIn("AUTHORITATIVE", self.m["status"].replace("NOT AUTHORITATIVE", ""))

    def test_recorded_hashes_match_the_files_on_disk(self):
        for a in self.m["artifacts"]:
            with self.subTest(path=a["path"]):
                self.assertEqual(
                    hashlib.sha256((REPO / a["path"]).read_bytes()).hexdigest(),
                    a["sha256"])

    def test_manifest_records_the_truncation_honestly(self):
        for a in self.m["artifacts"]:
            with self.subTest(path=a["path"]):
                self.assertTrue(a["head_truncated"])
                self.assertFalse(a["reaches_complete_pre_fe_window"])
                self.assertFalse(a["ltf_value_cap_reached"])
                self.assertEqual(a["post_fe_rows"], 0)
                self.assertEqual(a["duplicate_count"], 0)

    def test_manifest_records_the_protected_chart_as_untouched(self):
        e = self.m["extraction"]
        self.assertIn("untouched", e["protected_chart_2d43Iesr"])
        self.assertFalse(e["pine_save_used"])
        self.assertEqual(e["chart"].split()[0], "P2NtY6fg")

    def test_probe_hash_matches_the_committed_probe(self):
        self.assertEqual(
            hashlib.sha256((REPO / "docs" / "p11_3m_extraction_probe.pine").read_bytes()).hexdigest(),
            self.m["extraction"]["probe_sha256"])

    def test_the_p9_probe_was_not_modified(self):
        self.assertEqual(
            hashlib.sha256((REPO / "docs" / "p9_extraction_probe.pine").read_bytes()).hexdigest(),
            "2034aa811886f29940e32a3878bf17095a64c915f85479af449c67fca576fd30")


if __name__ == "__main__":
    unittest.main()

"""The P-12 parent-attributed 3m candidates.

Data acquisition evidence only. **No test here runs V53, invokes the Gate 1
comparator, or asserts parity.** These datasets are `CANDIDATE`, are deliberately
NOT registered in `data/phase_c_ltf_manifest.json`, and cannot support a parity
claim.

What this file exists to pin: `parent_ts` is TradingView's own attribution,
observed at extraction time, and is *not* recoverable from timestamp geometry.
"""

from __future__ import annotations

import csv
import hashlib
import json
import unittest
from collections import Counter
from decimal import Decimal
from pathlib import Path

from bot.guards import FE_MS

REPO = Path(__file__).resolve().parents[2]
LTF = REPO / "data" / "phase_c_ltf"
MANIFEST = LTF / "3m_parent_attributed_candidate_manifest.json"

FE_S = FE_MS // 1000
TF_S = 180
PARENT_S = 300
FIRST_SERVED_S = 1780264800      # 2026-05-31T22:00:00Z, TradingView's history limit
REQUESTED_START_S = 1779660000   # 2026-05-24T22:00:00Z, Phase-C start

#: The case the eligibility audit singled out: a 3m bar that straddles into the
#: *next* parent. Floor-to-5m would put 23:54 under 23:50; TradingView does not.
BOUNDARY_PARENT = 1788134100     # 2026-08-30 23:55:00Z
BOUNDARY_BARS = [1788134040, 1788134220]   # 23:54, 23:57


def rows(short: str) -> list[dict]:
    with (LTF / f"{short}1__3m_parent_attributed.csv").open(newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == [
            "timestamp", "open", "high", "low", "close", "parent_ts"]
        return list(reader)


def parents(short: str) -> list[int]:
    with (REPO / "data" / "phase_c" / f"{short}1__5m.csv").open(newline="") as fh:
        return [int(r["timestamp"]) for r in csv.DictReader(fh)]


class Schema(unittest.TestCase):

    def test_both_files_exist_with_the_parent_ts_column(self):
        for short in ("MGC", "MNQ"):
            with self.subTest(short=short):
                self.assertEqual(len(rows(short)), 29780)

    def test_every_row_carries_an_observed_parent_ts(self):
        for short in ("MGC", "MNQ"):
            with self.subTest(short=short):
                self.assertTrue(all(r["parent_ts"] for r in rows(short)))


class Integrity(unittest.TestCase):

    def test_timestamps_strictly_increasing_and_unique(self):
        for short in ("MGC", "MNQ"):
            ts = [int(r["timestamp"]) for r in rows(short)]
            with self.subTest(short=short):
                self.assertEqual(len(ts), len(set(ts)))
                self.assertTrue(all(b > a for a, b in zip(ts, ts[1:])))

    def test_ohlc_ordering_valid(self):
        for short in ("MGC", "MNQ"):
            for r in rows(short):
                o, h, l, c = (Decimal(r[k]) for k in ("open", "high", "low", "close"))
                if not (h >= max(o, c) and l <= min(o, c)):
                    self.fail(f"{short} {r['timestamp']}: OHLC ordering violated")

    def test_pre_fe_containment(self):
        for short in ("MGC", "MNQ"):
            for r in rows(short):
                t = int(r["timestamp"])
                self.assertLess(t, FE_S)
                self.assertLessEqual(t + TF_S, FE_S)

    def test_timestamps_on_the_180_second_grid(self):
        for short in ("MGC", "MNQ"):
            with self.subTest(short=short):
                self.assertTrue(all(int(r["timestamp"]) % TF_S == 0 for r in rows(short)))


class Attribution(unittest.TestCase):
    """The reason this capture exists."""

    def test_parent_ts_is_always_a_real_phase_c_5m_parent(self):
        for short in ("MGC", "MNQ"):
            ps = set(parents(short))
            with self.subTest(short=short):
                for r in rows(short):
                    q = int(r["parent_ts"])
                    self.assertEqual(q % PARENT_S, 0)
                    self.assertIn(q, ps)

    def test_every_bar_overlaps_the_parent_it_was_attributed_to(self):
        """Attribution is observed, but it is not arbitrary: the bar always
        genuinely overlaps the parent's half-open 5m span."""
        for short in ("MGC", "MNQ"):
            with self.subTest(short=short):
                for r in rows(short):
                    t, q = int(r["timestamp"]), int(r["parent_ts"])
                    self.assertTrue(t < q + PARENT_S and t + TF_S > q)

    def test_parent_ts_is_not_recoverable_from_timestamp_geometry(self):
        """The whole point: floor-to-5m disagrees on 40% of rows.

        If `parent_ts` had been synthesised as `t - (t % 300)` this count would
        be zero. It is 11,912 of 29,780 on both instruments.
        """
        for short in ("MGC", "MNQ"):
            diff = [r for r in rows(short)
                    if int(r["timestamp"]) - (int(r["timestamp"]) % PARENT_S)
                    != int(r["parent_ts"])]
            with self.subTest(short=short):
                self.assertEqual(len(diff), 11912)
                self.assertAlmostEqual(len(diff) / 29780, 0.4, places=3)

    def test_no_bar_is_attributed_to_two_parents(self):
        for short in ("MGC", "MNQ"):
            seen: dict[int, int] = {}
            for r in rows(short):
                t, q = int(r["timestamp"]), int(r["parent_ts"])
                if t in seen:
                    self.fail(f"{short}: {t} attributed to {seen[t]} and {q}")
                seen[t] = q

    def test_a_parent_receives_one_or_two_sub_bars_never_three(self):
        for short in ("MGC", "MNQ"):
            hist = Counter(Counter(int(r["parent_ts"]) for r in rows(short)).values())
            with self.subTest(short=short):
                self.assertEqual(dict(hist), {1: 5956, 2: 11912})

    def test_the_boundary_case_is_recorded_as_tradingview_assigned_it(self):
        """Parent 23:55 holds 23:54 and 23:57 — independently reproduced."""
        for short in ("MGC", "MNQ"):
            got = sorted(int(r["timestamp"]) for r in rows(short)
                         if int(r["parent_ts"]) == BOUNDARY_PARENT)
            with self.subTest(short=short):
                self.assertEqual(got, BOUNDARY_BARS)
                # and the floor rule would have given this parent only 23:57
                floor = [t for t in got if t - (t % PARENT_S) == BOUNDARY_PARENT]
                self.assertEqual(floor, [1788134220])


class CoverageAndTruncation(unittest.TestCase):

    def test_head_truncation_matches_the_history_limit(self):
        for short, empty in (("MGC", 1350), ("MNQ", 1332)):
            rs = rows(short)
            covered = {int(r["parent_ts"]) for r in rs}
            absent = [p for p in parents(short) if p not in covered]
            with self.subTest(short=short):
                self.assertEqual(int(rs[0]["timestamp"]), FIRST_SERVED_S)
                self.assertGreater(FIRST_SERVED_S, REQUESTED_START_S)
                self.assertEqual(len(covered), 17868)
                self.assertEqual(len(absent), empty)
                self.assertEqual(absent[0], REQUESTED_START_S)
                self.assertEqual(absent, parents(short)[:len(absent)])

    def test_the_ltf_cap_was_not_reached(self):
        for short in ("MGC", "MNQ"):
            with self.subTest(short=short):
                self.assertLess(len(rows(short)), 100_000)


class ReproducesThePreviousCapture(unittest.TestCase):
    """Audit only — neither dataset is authoritative."""

    def test_timestamps_and_ohlc_are_identical_to_the_p11_capture(self):
        for short in ("MGC", "MNQ"):
            with (LTF / f"{short}1__3m.csv").open(newline="") as fh:
                old = list(csv.DictReader(fh))
            new = rows(short)
            with self.subTest(short=short):
                self.assertEqual(len(old), len(new))
                for a, b in zip(old, new):
                    self.assertEqual(a["timestamp"], b["timestamp"])
                    for k in ("open", "high", "low", "close"):
                        self.assertEqual(a[k], b[k])

    def test_the_previous_3m_capture_is_unmodified(self):
        expected = {
            "MGC1__3m.csv": "bc54ed68a637648b242b2d5f9bc78ffcfe8878061bb51f0aefae44446c5817eb",
            "MNQ1__3m.csv": "772db2128f5ac55704a7ed787b571f71b3def8dce4390ef71c9425f120ce3dbf",
            "MGC1__1m.csv": "eeba6ffb7fb44a92b5be9d9ac8f0330cbf85d9a9d8b45d9c90a373cdf134af7b",
            "MNQ1__1m.csv": "7e4eab7fb51c2f801db17d5452fe3d6dcbcc5fe81af97f260110091361dac55a",
        }
        for name, digest in expected.items():
            with self.subTest(name=name):
                self.assertEqual(
                    hashlib.sha256((LTF / name).read_bytes()).hexdigest(), digest)


class Provenance(unittest.TestCase):

    def setUp(self):
        self.m = json.loads(MANIFEST.read_text())

    def test_status_is_candidate_never_authoritative(self):
        self.assertTrue(self.m["status"].startswith("CANDIDATE"))
        self.assertIn("NOT AUTHORITATIVE", self.m["status"])

    def test_recorded_hashes_match_disk(self):
        for a in self.m["artifacts"]:
            with self.subTest(path=a["path"]):
                self.assertEqual(
                    hashlib.sha256((REPO / a["path"]).read_bytes()).hexdigest(),
                    a["sha256"])

    def test_probe_hash_matches(self):
        self.assertEqual(
            hashlib.sha256(
                (REPO / "docs" / "p12_3m_parent_attributed_probe.pine").read_bytes()
            ).hexdigest(),
            self.m["extraction"]["probe_sha256"])

    def test_manifest_records_truncation_and_cap_honestly(self):
        for a in self.m["artifacts"]:
            with self.subTest(path=a["path"]):
                self.assertTrue(a["head_truncated"])
                self.assertFalse(a["reaches_complete_pre_fe_window"])
                self.assertFalse(a["ltf_value_cap_reached"])
                self.assertTrue(a["parent_series_history_paging_required"])
                self.assertEqual(a["post_fe_rows"], 0)
                self.assertEqual(a["duplicate_count"], 0)
                self.assertEqual(
                    a["rows_where_recorded_parent_differs_from_timestamp_floor"], 11912)

    def test_manifest_records_safety_posture(self):
        e = self.m["extraction"]
        self.assertIn("untouched", e["protected_chart_2d43Iesr"])
        self.assertFalse(e["pine_save_used"])
        self.assertFalse(e["tv_launch_used"])
        self.assertEqual(e["chart"].split()[0], "P2NtY6fg")

    def test_earlier_probes_are_unmodified(self):
        for name, digest in (
            ("p9_extraction_probe.pine",
             "2034aa811886f29940e32a3878bf17095a64c915f85479af449c67fca576fd30"),
            ("p11_3m_extraction_probe.pine",
             "7e1cad1576a7daf12392d01e2e95f9bb47112727308275333bfa753df61a72fc"),
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    hashlib.sha256((REPO / "docs" / name).read_bytes()).hexdigest(),
                    digest)


class NotRegisteredForGate1(unittest.TestCase):
    """Acquisition only. These files are not Gate 1 evidence yet."""

    def test_not_listed_in_the_manifest_the_gate_1_loader_reads(self):
        registered = json.loads(
            (REPO / "data" / "phase_c_ltf_manifest.json").read_text())
        paths = [a["path"] for a in registered["artifacts"]]
        for short in ("MGC", "MNQ"):
            with self.subTest(short=short):
                self.assertNotIn(
                    f"data/phase_c_ltf/{short}1__3m_parent_attributed.csv", paths)

    def test_the_gate_1_loader_registry_does_not_point_at_these_files(self):
        from bot.replay.loader import REGISTRY
        for rel, _ in REGISTRY.values():
            self.assertNotIn("parent_attributed", rel)


if __name__ == "__main__":
    unittest.main()

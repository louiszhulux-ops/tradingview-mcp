"""A2 validation — golden fixtures.

Covers the eleven required checks: existence, schema, pre-FE guard, no post-FE
data, no Phase 16 reference, matrix coverage, unique ids, deterministic ordering,
reproducible extraction, valid provenance, and unmodified source artifacts.
"""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from decimal import Decimal
from pathlib import Path

from bot.fixtures.loader import GOLDEN_DIR, guard_fixture, iter_timestamps, load_all, load_manifest
from bot.guards import FE_MS, HeldOutDataError, assert_pre_fe
from bot.tools.extract_golden import REPO, build_all, sha256_of

INSTRUMENTS = ("MGC", "MNQ")
DIRECTIONS = ("L", "S")
LTFS = ("1m", "3m")
FOLDS = ("A", "B", "C")

FIXTURES = load_all()
MANIFEST = load_manifest()


class TestExistenceAndCoverage(unittest.TestCase):
    """Checks 1 and 6."""

    def test_exactly_24_fixtures_plus_manifest(self):
        files = sorted(p.name for p in GOLDEN_DIR.glob("*.json"))
        self.assertEqual(len(files), 25, files)
        self.assertIn("manifest.json", files)
        self.assertEqual(len(FIXTURES), 24)

    def test_full_matrix_is_covered_exactly_once(self):
        expected = {
            f"v53-{i}-{d}-{l}-{f}"
            for i in INSTRUMENTS for d in DIRECTIONS for l in LTFS for f in FOLDS
        }
        self.assertEqual({fx["fixture_id"] for fx in FIXTURES}, expected)

    def test_manifest_lists_every_fixture(self):
        self.assertEqual(MANIFEST["fixture_count"], 24)
        self.assertEqual(
            [e["fixture_id"] for e in MANIFEST["fixtures"]],
            [fx["fixture_id"] for fx in FIXTURES],
        )


class TestSchema(unittest.TestCase):
    """Check 2."""

    TOP_LEVEL = {
        "schema_version", "fixture_id", "cell", "provenance", "coverage", "funnel",
        "asserts", "performance", "fills_truncated_at_source", "fills",
        "source_notes", "not_captured",
    }
    RECORDED = {
        "instrument", "direction", "ltf", "fold", "sweep_ts_utc", "sweep_ts_ms",
        "sweep_kind", "sweep_extreme", "choch_ts_utc", "choch_ts_ms", "choch_level",
        "retest_ts_utc", "retest_ts_ms", "bos_ts_utc", "bos_ts_ms", "bos_level",
        "fvg_low", "fvg_high", "entry_ts_utc", "entry_ts_ms", "entry_price",
        "stop_price", "outcome", "r_multiple", "pnl_usd", "exit_reason",
        "bars_in_trade",
    }
    FUNNEL = {
        "fold_bars", "fold_bars_with_ltf", "ltf_bars", "sweeps", "choch", "retests",
        "bos_displacement", "fvg", "fills", "break_no_displacement", "no_fvg",
        "r_band_rejects", "fvg_retest_expiry", "expire_pre_choch",
        "expire_post_choch", "expire_post_retest", "dropped_no_slot",
    }

    def test_top_level_keys(self):
        for fx in FIXTURES:
            with self.subTest(fx["fixture_id"]):
                self.assertEqual(set(fx), self.TOP_LEVEL)
                self.assertEqual(fx["schema_version"], 1)

    def test_cell_matches_fixture_id(self):
        for fx in FIXTURES:
            c = fx["cell"]
            self.assertEqual(
                fx["fixture_id"],
                f"v53-{c['instrument_short']}-{c['direction']}-{c['ltf']}-{c['fold']}",
            )

    def test_funnel_and_fill_keys(self):
        for fx in FIXTURES:
            with self.subTest(fx["fixture_id"]):
                self.assertEqual(set(fx["funnel"]), self.FUNNEL)
                for fill in fx["fills"]:
                    self.assertEqual(set(fill), {"index", "recorded", "derived", "event_keys"})
                    self.assertEqual(set(fill["recorded"]), self.RECORDED)

    def test_prices_are_strings_not_floats(self):
        # Decimal fidelity: a float here would silently lose precision.
        for fx in FIXTURES:
            for fill in fx["fills"]:
                for field in ("entry_price", "stop_price", "sweep_extreme",
                              "choch_level", "bos_level", "fvg_low", "fvg_high",
                              "r_multiple", "pnl_usd"):
                    value = fill["recorded"][field]
                    self.assertIsInstance(value, str, f"{fx['fixture_id']}.{field}")
                    Decimal(value)  # must parse

    def test_fill_count_agrees_with_funnel_and_performance(self):
        for fx in FIXTURES:
            with self.subTest(fx["fixture_id"]):
                self.assertEqual(len(fx["fills"]), fx["funnel"]["fills"])
                self.assertEqual(fx["performance"]["fills"], fx["funnel"]["fills"])

    def test_conservation_identity_holds(self):
        # FVG = fills + R-band rejects + FVG retest expiry
        for fx in FIXTURES:
            f = fx["funnel"]
            with self.subTest(fx["fixture_id"]):
                self.assertEqual(
                    f["fvg"], f["fills"] + f["r_band_rejects"] + f["fvg_retest_expiry"]
                )

    def test_assertion_counters_all_zero(self):
        for fx in FIXTURES:
            with self.subTest(fx["fixture_id"]):
                self.assertTrue(fx["asserts"]["all_zero"])
                self.assertEqual(fx["funnel"]["dropped_no_slot"], 0)

    def test_not_captured_is_declared(self):
        for fx in FIXTURES:
            self.assertTrue(fx["not_captured"])


class TestPreFeGuard(unittest.TestCase):
    """Checks 3 and 4."""

    def test_every_timestamp_passes_the_guard(self):
        total = 0
        for fx in FIXTURES:
            total += guard_fixture(fx)
        self.assertEqual(total, 338)

    def test_no_timestamp_reaches_fe(self):
        for fx in FIXTURES:
            for context, value in iter_timestamps(fx):
                with self.subTest(context):
                    self.assertLess(value, FE_MS)

    def test_a_post_fe_fixture_would_be_rejected(self):
        poisoned = json.loads(json.dumps(FIXTURES[0]))
        poisoned["coverage"]["end_ms"] = FE_MS
        with self.assertRaises(HeldOutDataError):
            guard_fixture(poisoned)

    def test_utc_epoch_conversion_is_correct(self):
        # Fold boundaries are the anchor: fold B must start exactly at FB.
        fb = 1784160000000  # GUARD-ALLOW: authoritative value assertion
        fold_b = [fx for fx in FIXTURES if fx["cell"]["fold"] == "B"]
        for fx in fold_b:
            self.assertEqual(fx["coverage"]["start_ms"], fb, fx["fixture_id"])
        for fx in FIXTURES:
            self.assertEqual(assert_pre_fe(fx["coverage"]["start_ms"]),
                             fx["coverage"]["start_ms"])


class TestNoPhase16Reference(unittest.TestCase):
    """Check 5."""

    FORBIDDEN = re.compile(r"p16|PHASE16|OOS|V53_P16", re.IGNORECASE)  # GUARD-ALLOW: pattern definition

    def test_no_fixture_text_references_phase16(self):
        for path in sorted(GOLDEN_DIR.glob("*.json")):
            with self.subTest(path.name):
                self.assertIsNone(self.FORBIDDEN.search(path.read_text(encoding="utf-8")))

    def test_sources_are_phase13f_or_phase14_only(self):
        for fx in FIXTURES:
            src = fx["provenance"]["source_file"]
            with self.subTest(fx["fixture_id"]):
                self.assertIn(src.rsplit("/", 2)[-2], ("v53_runs", "v53_runs_foldc"))
                self.assertIn(fx["provenance"]["research_phase"], ("13F", "14"))


class TestIdentityAndOrdering(unittest.TestCase):
    """Checks 7 and 8."""

    def test_fixture_ids_are_unique(self):
        ids = [fx["fixture_id"] for fx in FIXTURES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_manifest_order_is_sorted_and_stable(self):
        ids = [e["fixture_id"] for e in MANIFEST["fixtures"]]
        expected = sorted(
            ids,
            key=lambda i: (i.split("-")[1], DIRECTIONS.index(i.split("-")[2]),
                           LTFS.index(i.split("-")[3]), FOLDS.index(i.split("-")[4])),
        )
        self.assertEqual(ids, expected)

    def test_fill_indices_are_dense_and_ordered(self):
        for fx in FIXTURES:
            self.assertEqual([f["index"] for f in fx["fills"]], list(range(len(fx["fills"]))))

    def test_json_keys_are_sorted(self):
        for path in sorted(GOLDEN_DIR.glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(path.name):
                self.assertEqual(
                    path.read_text(encoding="utf-8"),
                    json.dumps(raw, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                )


class TestDeterminism(unittest.TestCase):
    """Check 9."""

    def test_two_extractions_are_byte_identical(self):
        first = build_all()
        second = build_all()
        self.assertEqual(first, second)

    def test_on_disk_matches_a_fresh_extraction(self):
        built = build_all()
        self.assertEqual({p.name for p in GOLDEN_DIR.glob("*.json")}, set(built))
        for name, content in built.items():
            with self.subTest(name):
                self.assertEqual((GOLDEN_DIR / name).read_text(encoding="utf-8"), content)

    def test_manifest_fixture_hashes_match_the_files(self):
        for entry in MANIFEST["fixtures"]:
            path = GOLDEN_DIR / entry["file"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.subTest(entry["fixture_id"]):
                self.assertEqual(digest, entry["fixture_sha256"])


class TestProvenance(unittest.TestCase):
    """Checks 10 and 11."""

    REQUIRED = {
        "source_file", "source_sha256", "research_phase", "strategy_id",
        "executed_artifact", "executed_artifact_sha256", "canonical_artifact",
        "canonical_artifact_sha256", "attribution_note", "extractor",
        "extractor_version",
    }

    def test_every_fixture_has_complete_provenance(self):
        for fx in FIXTURES:
            p = fx["provenance"]
            with self.subTest(fx["fixture_id"]):
                self.assertEqual(set(p), self.REQUIRED)
                self.assertEqual(p["strategy_id"], "V53")
                self.assertRegex(p["source_sha256"], r"^[0-9a-f]{64}$")

    def test_source_artifacts_are_unmodified(self):
        for fx in FIXTURES:
            path = REPO / fx["provenance"]["source_file"]
            with self.subTest(fx["fixture_id"]):
                self.assertTrue(path.is_file())
                self.assertEqual(sha256_of(path), fx["provenance"]["source_sha256"])

    def test_strategy_artifacts_are_unmodified(self):
        for fx in FIXTURES:
            p = fx["provenance"]
            for artifact, expected in (
                (p["executed_artifact"], p["executed_artifact_sha256"]),
                (p["canonical_artifact"], p["canonical_artifact_sha256"]),
            ):
                with self.subTest(artifact):
                    self.assertEqual(sha256_of(REPO / artifact), expected)


class TestCrossChecksAgainstResearchRecords(unittest.TestCase):
    """The fixtures must reproduce the committed research totals exactly."""

    def test_totals_match_pooled_design_verification(self):
        # trader_v2/p15/POOLED_DESIGN_VERIFICATION.md: 58 fills / 9 wins.
        self.assertEqual(sum(fx["funnel"]["fills"] for fx in FIXTURES), 58)
        self.assertEqual(sum(fx["performance"].get("wins", 0) for fx in FIXTURES), 9)

    def test_fold_ab_totals_match_phase13g_control(self):
        # trader_v2/v53_runs/PHASE13G_raw_output.txt: 40 fills / 6 wins.
        ab = [fx for fx in FIXTURES if fx["cell"]["fold"] in ("A", "B")]
        self.assertEqual(sum(fx["funnel"]["fills"] for fx in ab), 40)
        self.assertEqual(sum(fx["performance"].get("wins", 0) for fx in ab), 6)

    def test_fold_c_totals_match_phase14(self):
        # trader_v2/v53_runs_foldc/PHASE14_raw_output.txt: 18 fills / 3 wins.
        c = [fx for fx in FIXTURES if fx["cell"]["fold"] == "C"]
        self.assertEqual(sum(fx["funnel"]["fills"] for fx in c), 18)
        self.assertEqual(sum(fx["performance"].get("wins", 0) for fx in c), 3)

    def test_per_cell_sums_match_the_pooled_baseline_run(self):
        """Independent check: A+B+C per cell must equal the pooled ALL run."""
        pat = re.compile(
            r"^(MGC|MNQ) ([LS]) (\dm) ALL \| bars \d+ \| cov \d+ \| sw (\d+) \| "
            r"ch (\d+) \| rt (\d+) \| bos (\d+) \| fvg (\d+) \| fill (\d+) \| W(\d+)"
        )
        by_cell = {}
        for fx in FIXTURES:
            c = fx["cell"]
            by_cell.setdefault((c["instrument_short"], c["direction"], c["ltf"]), []).append(fx)

        pooled = REPO / "trader_v2" / "p15" / "runs" / "BASE_pooled.txt"
        checked = 0
        for line in pooled.read_text(encoding="utf-8").splitlines():
            m = pat.match(line)
            if not m:
                continue
            inst, direction, ltf = m.group(1), m.group(2), m.group(3)
            cells = by_cell[(inst, direction, ltf)]
            got = [sum(c["funnel"][k] for c in cells) for k in
                   ("sweeps", "choch", "retests", "bos_displacement", "fvg", "fills")]
            got.append(sum(c["performance"].get("wins", 0) for c in cells))
            with self.subTest(f"{inst} {direction} {ltf}"):
                self.assertEqual(got, [int(v) for v in m.groups()[3:]])
            checked += 1
        self.assertEqual(checked, 8)


class TestDerivedFields(unittest.TestCase):
    """Derived values are arithmetic on recorded fields and are cross-validated."""

    def test_r_distance_equals_entry_minus_stop(self):
        for fx in FIXTURES:
            for fill in fx["fills"]:
                r = fill["recorded"]
                with self.subTest(f"{fx['fixture_id']}[{fill['index']}]"):
                    self.assertEqual(
                        Decimal(fill["derived"]["r_distance"]),
                        abs(Decimal(r["entry_price"]) - Decimal(r["stop_price"])),
                    )

    def test_target_is_five_r_from_entry(self):
        for fx in FIXTURES:
            for fill in fx["fills"]:
                r, d = fill["recorded"], fill["derived"]
                sign = 1 if r["direction"] == "L" else -1
                with self.subTest(f"{fx['fixture_id']}[{fill['index']}]"):
                    self.assertEqual(
                        Decimal(d["target_price"]),
                        Decimal(r["entry_price"]) + sign * 5 * Decimal(d["r_distance"]),
                    )

    def test_r_multiple_reconciles_for_every_fill(self):
        for fx in FIXTURES:
            for fill in fx["fills"]:
                with self.subTest(f"{fx['fixture_id']}[{fill['index']}]"):
                    self.assertTrue(fill["derived"]["checks"]["r_reconciled"])

    def test_pnl_reconciles_for_every_stop_and_target_exit(self):
        unreconciled = [
            (fx["fixture_id"], f["index"], f["recorded"]["exit_reason"])
            for fx in FIXTURES for f in fx["fills"]
            if not f["derived"]["checks"]["pnl_reconciled"]
        ]
        # Only timeout exits are unreconcilable: V53 records no exit price for them.
        self.assertTrue(all(reason == "timeout" for _, _, reason in unreconciled))
        self.assertEqual(len(unreconciled), 5)

    def test_inverted_stops_are_flagged_not_corrected(self):
        inverted = [
            (fx["fixture_id"], f["recorded"]["entry_ts_utc"])
            for fx in FIXTURES for f in fx["fills"] if f["derived"]["stop_inverted"]
        ]
        # A real recorded V53 property: the FVG far edge can sit beyond the sweep
        # extreme, putting the stop on the near side. B2 must reproduce it.
        self.assertEqual(inverted, [
            ("v53-MNQ-S-1m-A", "2026-05-29 19:25"),
            ("v53-MNQ-S-1m-B", "2026-07-20 12:30"),
        ])


class TestEventKeys(unittest.TestCase):
    def test_every_fill_has_both_phase13g_identities(self):
        for fx in FIXTURES:
            for fill in fx["fills"]:
                keys = fill["event_keys"]
                with self.subTest(f"{fx['fixture_id']}[{fill['index']}]"):
                    self.assertEqual(set(keys), {"primary", "alternative"})
                    self.assertEqual(len(keys["primary"].split("|")), 9)
                    self.assertEqual(len(keys["alternative"].split("|")), 7)

    def test_convergent_fills_share_an_alternative_key(self):
        # Phase 13G: convergence is real and must survive into the fixtures.
        fx = next(f for f in FIXTURES if f["fixture_id"] == "v53-MNQ-L-1m-B")
        alts = [f["event_keys"]["alternative"] for f in fx["fills"]]
        self.assertEqual(len(alts), 7)
        self.assertEqual(len(set(alts)), 3)


if __name__ == "__main__":
    unittest.main()

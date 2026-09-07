"""Tests for the static guard checker.

Every negative case is written into a temporary tree, never into bot/, so the
repository's own tree stays clean.
"""

import tempfile
import unittest
from pathlib import Path

from bot.tools.check_guards import check


def _tree(**files: str) -> tempfile.TemporaryDirectory:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    for rel, body in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return tmp


class TestPhase16DependencyDetection(unittest.TestCase):
    """Check 1 — the core anti-contamination guard."""

    def _violations(self, body: str) -> list[str]:
        with _tree(**{"mod.py": body}) as name:
            violations, _ = check(Path(name))
        return violations

    def test_clean_tree_passes(self):
        self.assertEqual(self._violations("x = 1\n"), [])

    def test_import_of_phase16_tree_is_caught(self):
        v = self._violations("import trader_v2.p16.derive\n")  # GUARD-ALLOW: negative-test fixture
        self.assertTrue(any("Phase 16" in entry for entry in v))

    def test_path_reference_to_phase16_tree_is_caught(self):
        v = self._violations('P = "trader_v2/p16/executed"\n')  # GUARD-ALLOW: negative-test fixture
        self.assertTrue(any("Phase 16" in entry for entry in v))

    def test_protocol_file_reference_is_caught(self):
        v = self._violations('open("PHASE16_PROTOCOL.md")\n')  # GUARD-ALLOW: negative-test fixture
        self.assertTrue(any("Phase 16" in entry for entry in v))

    def test_oos_build_artifact_reference_is_caught(self):
        v = self._violations('S = "V53_P16_OOS_BUILD.pine"\n')  # GUARD-ALLOW: negative-test fixture
        self.assertTrue(any("Phase 16" in entry for entry in v))

    def test_oos_dataset_reference_is_caught(self):
        v = self._violations("OOS = load()\n")  # GUARD-ALLOW: negative-test fixture
        self.assertTrue(any("out-of-sample" in entry for entry in v))

    def test_consumed_research_folds_are_not_forbidden(self):
        # Roadmap A2 must be able to read the already-consumed fold A/B/C runs.
        self.assertEqual(self._violations('P = "trader_v2/v53_runs/MGC_L_1m_A.txt"\n'), [])


class TestSingleFeDefinition(unittest.TestCase):
    """Check 2 — the boundary literal lives in exactly one place."""

    def test_fe_literal_outside_guards_is_caught(self):
        with _tree(**{"loader.py": "FE = 1788134400000\n"}) as name:  # GUARD-ALLOW: negative-test fixture
            violations, _ = check(Path(name))
        self.assertTrue(any("FE boundary literal" in entry for entry in violations))

    def test_fe_literal_inside_guards_is_allowed(self):
        with _tree(**{"guards.py": "FE_MS = 1788134400000\n"}) as name:  # GUARD-ALLOW: negative-test fixture
            violations, _ = check(Path(name))
        self.assertEqual(violations, [])


class TestLoadersRequireTheGuard(unittest.TestCase):
    """Check 3 — no data path may be written without the guard."""

    def test_loader_without_guard_import_is_caught(self):
        with _tree(**{"data/loader.py": "def load(p):\n    return open(p).read()\n"}) as name:
            violations, _ = check(Path(name))
        self.assertTrue(any("does not import from bot.guards" in e for e in violations))

    def test_loader_with_guard_import_passes(self):
        body = "from bot.guards import assert_pre_fe\n\ndef load(ts):\n    return assert_pre_fe(ts)\n"
        with _tree(**{"data/loader.py": body}) as name:
            violations, _ = check(Path(name))
        self.assertEqual(violations, [])

    def test_fixture_module_without_guard_import_is_caught(self):
        with _tree(**{"fixtures/golden.py": "ROWS = []\n"}) as name:
            violations, _ = check(Path(name))
        self.assertTrue(any("does not import from bot.guards" in e for e in violations))

    def test_module_outside_guarded_dirs_needs_no_guard_import(self):
        with _tree(**{"exec/oms.py": "class Oms:\n    pass\n"}) as name:
            violations, _ = check(Path(name))
        self.assertEqual(violations, [])


class TestLiveDataInDevelopmentCode(unittest.TestCase):
    """Check 4 — live chart reads return recent, i.e. held-out, bars."""

    def test_mcp_tool_reference_in_tests_is_caught(self):
        with _tree(**{"tests/test_x.py": "call('mcp__f__quote_get')\n"}) as name:  # GUARD-ALLOW: negative-test fixture
            violations, _ = check(Path(name))
        self.assertTrue(any("live TradingView data" in e for e in violations))

    def test_cdp_port_in_tests_is_caught(self):
        with _tree(**{"tests/test_x.py": "PORT = 9222\n"}) as name:  # GUARD-ALLOW: negative-test fixture
            violations, _ = check(Path(name))
        self.assertTrue(any("live TradingView data" in e for e in violations))

    def test_chart_read_in_fixtures_is_caught(self):
        body = "from bot.guards import assert_pre_fe\nbars = data_get_ohlcv()\n"  # GUARD-ALLOW: negative-test fixture
        with _tree(**{"fixtures/pull.py": body}) as name:
            violations, _ = check(Path(name))
        self.assertTrue(any("live TradingView data" in e for e in violations))

    def test_same_reference_outside_dev_dirs_is_not_caught_by_check4(self):
        # A production adapter (roadmap D2) is governed by its own interlock.
        with _tree(**{"data/adapters/tv.py": "from bot.guards import assert_pre_fe\nPORT = 9222\n"}) as name:  # GUARD-ALLOW: negative-test fixture
            violations, _ = check(Path(name))
        self.assertEqual(violations, [])


class TestAllowMarker(unittest.TestCase):
    def test_allow_marker_exempts_and_is_reported(self):
        # Assembled from parts so this source line is not itself a violation.
        body = 'P = "trader_v2/' + 'p16"  # GUARD' + '-ALLOW: deliberate\n'
        with _tree(**{"mod.py": body}) as name:
            violations, allowed = check(Path(name))
        self.assertEqual(violations, [])
        self.assertEqual(len(allowed), 1)


class TestRepositoryTreeIsClean(unittest.TestCase):
    def test_bot_tree_passes_all_checks(self):
        root = Path(__file__).resolve().parents[1]
        violations, allowed = check(root)
        self.assertEqual(violations, [], f"bot/ tree has guard violations: {violations}")
        # Every exemption in the real tree must be a checker pattern definition
        # or an authoritative-value assertion — never a data path.
        for entry in allowed:
            self.assertTrue(
                "pattern definition" in entry
                or "authoritative value assertion" in entry
                or "negative-test fixture" in entry
                or 'ALLOW_MARKER = ' in entry,
                f"unexpected guard exemption: {entry}",
            )


if __name__ == "__main__":
    unittest.main()

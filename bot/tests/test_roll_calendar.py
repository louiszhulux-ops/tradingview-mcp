"""Validation of the frozen B-2 artifacts: the roll calendar and the Phase C parent dataset.

These are deterministic checks over committed files. They read nothing from TradingView and
run no strategy code -- they assert that the frozen artifacts are internally consistent and
that they agree with the figures recorded in the frozen research run files.
"""
import csv
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CALENDAR = REPO / "data" / "roll_calendar.json"
MANIFEST = REPO / "data" / "phase_c_manifest.json"
DATASET_DIR = REPO / "data" / "phase_c"

# Fold boundaries, frozen in V53. Seconds, to match the dataset's timestamp unit.
FB = 1784160000
FC = 1786233600
FE = 1788134400

MONTH_CODES = "FGHJKMNQUVXZ"

# Recorded in the frozen run files (trader_v2/v53_runs/*.txt).
EXPECTED_FOLD_BARS = {
    "MGC1_": {"A": 10386, "B": 4668},
    "MNQ1_": {"A": 10368, "B": 4668},
}


def _load_calendar():
    return json.loads(CALENDAR.read_text())


class TestRollCalendarStructure(unittest.TestCase):
    def setUp(self):
        self.cal = _load_calendar()

    def test_calendar_exists_and_covers_both_instruments(self):
        self.assertEqual(set(self.cal["instruments"]), {"MGC", "MNQ"})

    def test_deterministic_round_trip(self):
        """Re-serialising with the generator's settings reproduces the file byte for byte."""
        rendered = json.dumps(self.cal, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
        self.assertEqual(rendered, CALENDAR.read_text())

    def test_no_duplicate_roll_boundary(self):
        for name, inst in self.cal["instruments"].items():
            keys = [(r["old_contract"], r["new_contract"]) for r in inst["rolls"]]
            self.assertEqual(len(keys), len(set(keys)), f"{name} has a duplicate roll boundary")
            dates = [r["trade_date"] for r in inst["rolls"]]
            self.assertEqual(len(dates), len(set(dates)), f"{name} has a duplicate trade date")

    def test_chronological_ordering(self):
        for name, inst in self.cal["instruments"].items():
            ts = [r["roll_timestamp"] for r in inst["rolls"]]
            self.assertEqual(ts, sorted(ts), f"{name} rolls are not chronological")
            self.assertEqual(len(ts), len(set(ts)), f"{name} has duplicate roll timestamps")

    def test_old_contract_differs_from_new(self):
        for name, inst in self.cal["instruments"].items():
            for r in inst["rolls"]:
                self.assertNotEqual(r["old_contract"], r["new_contract"], f"{name} {r['trade_date']}")

    def test_contracts_chain(self):
        """Each roll's new contract is the next roll's old contract."""
        for name, inst in self.cal["instruments"].items():
            rolls = inst["rolls"]
            for prev, nxt in zip(rolls, rolls[1:]):
                self.assertEqual(
                    prev["new_contract"], nxt["old_contract"],
                    f"{name}: chain breaks between {prev['trade_date']} and {nxt['trade_date']}")

    def test_timestamps_are_valid(self):
        for name, inst in self.cal["instruments"].items():
            for r in inst["rolls"]:
                self.assertIsInstance(r["roll_timestamp"], int)
                self.assertGreater(r["roll_timestamp"], 0)
                parsed = datetime.strptime(r["roll_timestamp_utc"], "%Y-%m-%dT%H:%M:%SZ")
                self.assertEqual(
                    parsed.replace(tzinfo=timezone.utc).timestamp(), float(r["roll_timestamp"]),
                    f"{name} {r['trade_date']}: utc string disagrees with unix timestamp")

    def test_roll_instant_is_1700_chicago(self):
        """Every roll lands on the CME trade-date boundary: 17:00 America/Chicago."""
        from zoneinfo import ZoneInfo
        chicago = ZoneInfo("America/Chicago")
        for name, inst in self.cal["instruments"].items():
            for r in inst["rolls"]:
                self.assertEqual(r["roll_timezone"], "America/Chicago")
                local = datetime.fromtimestamp(r["roll_timestamp"], chicago)
                self.assertEqual((local.hour, local.minute), (17, 0),
                                 f"{name} {r['trade_date']} is not 17:00 CT")

    def test_roll_timestamp_precedes_its_trade_date(self):
        """The session opens at 17:00 CT on the calendar day before the trade date it belongs to.

        The gap is at least one day and never more than four -- longer gaps occur only where a
        holiday or weekend intervenes (e.g. the 2026-11-27 Thanksgiving row).
        """
        for name, inst in self.cal["instruments"].items():
            for r in inst["rolls"]:
                opened = datetime.fromtimestamp(r["roll_timestamp"], timezone.utc).date()
                trade = datetime.strptime(r["trade_date"], "%Y-%m-%d").date()
                delta = (trade - opened).days
                self.assertGreaterEqual(delta, 1, f"{name} {r['trade_date']}")
                self.assertLessEqual(delta, 4, f"{name} {r['trade_date']}")

    def test_contract_cycles(self):
        self.assertEqual(self.cal["instruments"]["MGC"]["contract_cycle"], "GJMQZ")
        self.assertEqual(self.cal["instruments"]["MNQ"]["contract_cycle"], "HMUZ")

    def test_cycle_matches_the_contracts_actually_used(self):
        for name, inst in self.cal["instruments"].items():
            used = set()
            for r in inst["rolls"]:
                for field in ("old_contract", "new_contract"):
                    code = r[field][len(inst["root"])]
                    self.assertIn(code, MONTH_CODES)
                    used.add(code)
            expected = "".join(c for c in MONTH_CODES if c in used)
            self.assertEqual(inst["contract_cycle"], expected, f"{name} cycle disagrees with its rolls")

    def test_pointvalues(self):
        self.assertEqual(self.cal["instruments"]["MGC"]["pointvalue"], 10)
        self.assertEqual(self.cal["instruments"]["MNQ"]["pointvalue"], 2)

    def test_continuous_symbols(self):
        self.assertEqual(self.cal["instruments"]["MGC"]["continuous_symbol"], "COMEX_MINI:MGC1!")
        self.assertEqual(self.cal["instruments"]["MNQ"]["continuous_symbol"], "CME_MINI:MNQ1!")

    def test_no_contract_is_a_continuous_symbol(self):
        """Execution resolves to a dated contract; a '!' continuous alias is never a leg."""
        for name, inst in self.cal["instruments"].items():
            for r in inst["rolls"]:
                for field in ("old_contract", "new_contract"):
                    self.assertNotIn("!", r[field], f"{name} {r['trade_date']} {field}")
                    self.assertRegex(r[field], r"^[A-Z]{2,4}[FGHJKMNQUVXZ]\d{4}$")

    def test_research_window_rolls_are_present(self):
        """The three rolls inside the frozen research window, as observed in P-6."""
        def find(inst, trade_date):
            return next((r for r in self.cal["instruments"][inst]["rolls"]
                         if r["trade_date"] == trade_date), None)

        mgc1 = find("MGC", "2026-05-28")
        self.assertIsNotNone(mgc1)
        self.assertEqual((mgc1["old_contract"], mgc1["new_contract"]), ("MGCM2026", "MGCQ2026"))
        self.assertEqual(mgc1["roll_timestamp"], 1779919200)

        mgc2 = find("MGC", "2026-07-30")
        self.assertIsNotNone(mgc2)
        self.assertEqual((mgc2["old_contract"], mgc2["new_contract"]), ("MGCQ2026", "MGCZ2026"))
        self.assertEqual(mgc2["roll_timestamp"], 1785362400)

        mnq = find("MNQ", "2026-06-15")
        self.assertIsNotNone(mnq)
        self.assertEqual((mnq["old_contract"], mnq["new_contract"]), ("MNQM2026", "MNQU2026"))
        self.assertEqual(mnq["roll_timestamp"], 1781474400)

    def test_fold_c_is_roll_free(self):
        for name, inst in self.cal["instruments"].items():
            for r in inst["rolls"]:
                self.assertFalse(FC <= r["roll_timestamp"] < FE,
                                 f"{name} {r['trade_date']} falls inside fold C, which is roll-free")


class TestPhaseCDataset(unittest.TestCase):
    def _rows(self, stem):
        with (DATASET_DIR / f"{stem}_5m.csv").open() as fh:
            return list(csv.DictReader(fh))

    def test_header_is_the_v53_field_set(self):
        for stem in EXPECTED_FOLD_BARS:
            with (DATASET_DIR / f"{stem}_5m.csv").open() as fh:
                self.assertEqual(fh.readline().strip(), "timestamp,high,low,close", stem)

    def test_chronological_and_unique(self):
        for stem in EXPECTED_FOLD_BARS:
            ts = [int(r["timestamp"]) for r in self._rows(stem)]
            self.assertEqual(ts, sorted(ts), stem)
            self.assertEqual(len(ts), len(set(ts)), stem)

    def test_bars_are_on_the_5m_grid(self):
        for stem in EXPECTED_FOLD_BARS:
            ts = [int(r["timestamp"]) for r in self._rows(stem)]
            for t in ts:
                self.assertEqual(t % 300, 0, f"{stem}: {t} is not on a 5-minute boundary")

    def test_no_post_fe_data(self):
        """The held-out boundary. No bar may reach FE."""
        for stem in EXPECTED_FOLD_BARS:
            for r in self._rows(stem):
                self.assertLess(int(r["timestamp"]), FE,
                                f"{stem} contains a bar at or after FE")

    def test_fold_bar_counts_match_the_frozen_runs(self):
        for stem, expected in EXPECTED_FOLD_BARS.items():
            ts = [int(r["timestamp"]) for r in self._rows(stem)]
            self.assertEqual(len([t for t in ts if t < FB]), expected["A"], f"{stem} fold A")
            self.assertEqual(len([t for t in ts if FB <= t < FC]), expected["B"], f"{stem} fold B")

    def test_ohlc_ordering(self):
        for stem in EXPECTED_FOLD_BARS:
            for r in self._rows(stem):
                high, low, close = float(r["high"]), float(r["low"]), float(r["close"])
                self.assertGreaterEqual(high, low, f"{stem} {r['timestamp']}")
                self.assertGreaterEqual(high, close, f"{stem} {r['timestamp']}")
                self.assertLessEqual(low, close, f"{stem} {r['timestamp']}")


class TestManifest(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text())

    def test_hashes_match_the_files_on_disk(self):
        import hashlib
        for entry in self.manifest["artifacts"]:
            path = REPO / entry["path"]
            self.assertTrue(path.exists(), entry["path"])
            data = path.read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"], entry["path"])
            self.assertEqual(len(data), entry["bytes"], entry["path"])

    def test_every_dataset_file_is_listed(self):
        listed = {e["path"] for e in self.manifest["artifacts"]}
        for stem in EXPECTED_FOLD_BARS:
            self.assertIn(f"data/phase_c/{stem}_5m.csv", listed)
        self.assertIn("data/roll_calendar.json", listed)


if __name__ == "__main__":
    unittest.main()

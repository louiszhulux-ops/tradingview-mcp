"""B1 ↔ A2 compatibility.

Proves the contracts can represent every fill in the 24 golden fixtures without
loss and without invention. This is a **representation** test: it maps recorded
fields into contract types. It runs no strategy logic — nothing here detects,
selects, qualifies or decides anything.

Fields A2 does not record (slot index, LTF indices, ATR at arm, R/ATR ratio,
pivot index, bar ranges) are carried as ``None`` / ``-1``. That absence is the
point: the contract represents "not recorded" rather than filling it in.
"""

from __future__ import annotations

import unittest
from collections import defaultdict
from decimal import Decimal

from bot.contracts.enums import (
    SWEEP_SOURCE_ORDER, Direction, ExitReason, Outcome, SweepSource, Timeframe,
)
from bot.contracts.events import (
    SIGNAL_SCHEMA_VERSION, BosEvent, ChochEvent, FillEvent, FvgEvent, OutcomeEvent,
    RetestEvent, SequenceRef, StrategySignal, SweepEvent,
)
from bot.contracts.serialize import dumps, encode
from bot.fixtures.loader import load_all
from bot.guards import assert_pre_fe

FIXTURES = load_all()
FIVE_MIN_MS = 300_000


def _containing_5m_close(ts_ms: int) -> int:
    """The close of the 5m bar containing ``ts_ms``.

    Timestamp arithmetic on a recorded value — V53's timestamps are bar *open*
    times (see UNRESOLVED.md R1). This is not a strategy decision.
    """
    return assert_pre_fe(ts_ms - (ts_ms % FIVE_MIN_MS) + FIVE_MIN_MS)


def _sources(kind: str) -> tuple[SweepSource, ...]:
    parts = kind.split("+")
    unknown = [p for p in parts if p not in {s.value for s in SweepSource}]
    if unknown:
        raise ValueError(f"unknown sweep source in {kind!r}: {unknown}")
    return tuple(s for s in SWEEP_SOURCE_ORDER if s.value in parts)


def signal_from_fill(fixture: dict, fill: dict) -> StrategySignal:
    """Map one recorded fill into the contract types. Pure transcription."""
    rec = fill["recorded"]
    prov = fixture["provenance"]
    ref = SequenceRef(
        instrument=rec["instrument"],
        direction=Direction(rec["direction"]),
        ltf=Timeframe(rec["ltf"]),
        slot_index=None,  # A2 does not record it; see fixture["not_captured"]
        sweep_ts_ms=rec["sweep_ts_ms"],
    )

    def stage(field: str) -> dict:
        ts = rec[f"{field}_ts_ms"]
        return {"ref": ref, "ts_ms": ts, "bar_close_ts_ms": _containing_5m_close(ts)}

    return StrategySignal(
        schema_version=SIGNAL_SCHEMA_VERSION,
        strategy_id=prov["strategy_id"],
        strategy_sha256=prov["executed_artifact_sha256"],
        ref=ref,
        sweep=SweepEvent(**stage("sweep"), sources=_sources(rec["sweep_kind"]),
                         extreme=Decimal(rec["sweep_extreme"]), stop=Decimal(rec["stop_price"])),
        choch=ChochEvent(**stage("choch"), level=Decimal(rec["choch_level"])),
        retest=RetestEvent(**stage("retest"), level=Decimal(rec["choch_level"])),
        bos=BosEvent(**stage("bos"), level=Decimal(rec["bos_level"])),
        fvg=FvgEvent(**stage("entry"), low=Decimal(rec["fvg_low"]),
                     high=Decimal(rec["fvg_high"]), entry=Decimal(rec["entry_price"])),
        fill=FillEvent(**stage("entry"), entry=Decimal(rec["entry_price"]),
                       stop=Decimal(rec["stop_price"]),
                       r_distance=Decimal(fill["derived"]["r_distance"])),
        outcome=OutcomeEvent(**stage("entry"), outcome=Outcome(rec["outcome"]),
                             exit_reason=ExitReason(rec["exit_reason"]),
                             r_multiple=Decimal(rec["r_multiple"]),
                             pnl_usd=Decimal(rec["pnl_usd"]),
                             bars_in_trade=rec["bars_in_trade"]),
        fold=rec["fold"],
    )


ALL_SIGNALS = [
    (fx, fill, signal_from_fill(fx, fill))
    for fx in FIXTURES for fill in fx["fills"]
]


class TestEveryFixtureFillIsRepresentable(unittest.TestCase):
    def test_all_58_fills_map_without_error(self):
        self.assertEqual(len(ALL_SIGNALS), 58)

    def test_every_cell_is_covered(self):
        self.assertEqual(len(FIXTURES), 24)
        with_fills = {fx["fixture_id"] for fx, _, _ in ALL_SIGNALS}
        self.assertEqual(len(with_fills), 18)  # 6 cells legitimately have no fills

    def test_zero_fill_cells_produce_no_signals(self):
        for fx in FIXTURES:
            if not fx["fills"]:
                self.assertEqual(fx["funnel"]["fills"], 0, fx["fixture_id"])


class TestNoValueIsLostInTranslation(unittest.TestCase):
    def test_prices_survive_exactly(self):
        for fx, fill, sig in ALL_SIGNALS:
            rec = fill["recorded"]
            with self.subTest(f"{fx['fixture_id']}[{fill['index']}]"):
                self.assertEqual(sig.fill.entry, Decimal(rec["entry_price"]))
                self.assertEqual(sig.fill.stop, Decimal(rec["stop_price"]))
                self.assertEqual(sig.choch.level, Decimal(rec["choch_level"]))
                self.assertEqual(sig.bos.level, Decimal(rec["bos_level"]))
                self.assertEqual(sig.fvg.low, Decimal(rec["fvg_low"]))
                self.assertEqual(sig.fvg.high, Decimal(rec["fvg_high"]))
                self.assertEqual(sig.sweep.extreme, Decimal(rec["sweep_extreme"]))

    def test_timestamps_survive_exactly(self):
        for fx, fill, sig in ALL_SIGNALS:
            rec = fill["recorded"]
            with self.subTest(f"{fx['fixture_id']}[{fill['index']}]"):
                self.assertEqual(sig.sweep.ts_ms, rec["sweep_ts_ms"])
                self.assertEqual(sig.choch.ts_ms, rec["choch_ts_ms"])
                self.assertEqual(sig.retest.ts_ms, rec["retest_ts_ms"])
                self.assertEqual(sig.bos.ts_ms, rec["bos_ts_ms"])
                self.assertEqual(sig.fill.ts_ms, rec["entry_ts_ms"])

    def test_outcomes_survive_exactly(self):
        for fx, fill, sig in ALL_SIGNALS:
            rec = fill["recorded"]
            with self.subTest(f"{fx['fixture_id']}[{fill['index']}]"):
                self.assertEqual(sig.outcome.outcome.value, rec["outcome"])
                self.assertEqual(sig.outcome.exit_reason.value, rec["exit_reason"])
                self.assertEqual(sig.outcome.r_multiple, Decimal(rec["r_multiple"]))
                self.assertEqual(sig.outcome.pnl_usd, Decimal(rec["pnl_usd"]))
                self.assertEqual(sig.outcome.bars_in_trade, rec["bars_in_trade"])

    def test_sweep_kind_round_trips(self):
        for fx, fill, sig in ALL_SIGNALS:
            with self.subTest(f"{fx['fixture_id']}[{fill['index']}]"):
                self.assertEqual(sig.sweep.kind, fill["recorded"]["sweep_kind"])

    def test_every_recorded_sweep_kind_is_covered_by_the_enum(self):
        kinds = {fill["recorded"]["sweep_kind"] for _, fill, _ in ALL_SIGNALS}
        self.assertEqual(kinds, {"SW", "AS", "PD", "AS+SW", "PD+AS"})


class TestUnrecordedFieldsAreAbsentNotInvented(unittest.TestCase):
    def test_slot_index_is_none(self):
        for fx, fill, sig in ALL_SIGNALS:
            self.assertIsNone(sig.ref.slot_index, f"{fx['fixture_id']}[{fill['index']}]")

    def test_unrecorded_fields_stay_empty(self):
        for fx, fill, sig in ALL_SIGNALS:
            with self.subTest(f"{fx['fixture_id']}[{fill['index']}]"):
                self.assertIsNone(sig.sweep.atr_at_arm)
                self.assertIsNone(sig.fill.r_atr_ratio)
                self.assertIsNone(sig.bos.bar_range)
                self.assertEqual(sig.choch.pivot_index, -1)
                self.assertEqual(sig.choch.ltf_index, -1)
                self.assertEqual(sig.bos.displacement_ltf_index, -1)

    def test_fixtures_declare_those_same_gaps(self):
        declared = " ".join(FIXTURES[0]["not_captured"]).lower()
        for phrase in ("slot index", "pivot", "displacement", "atr at arm"):
            self.assertIn(phrase, declared)


class TestIdentityAgreesWithPhase13G(unittest.TestCase):
    """The contract's keys must induce the same clustering as A2's."""

    def _partition(self, key_of):
        groups = defaultdict(list)
        for index, (fx, fill, sig) in enumerate(ALL_SIGNALS):
            groups[key_of(fx, fill, sig)].append(index)
        return sorted(sorted(v) for v in groups.values())

    def test_primary_partition_matches(self):
        self.assertEqual(
            self._partition(lambda fx, fill, sig: fill["event_keys"]["primary"]),
            self._partition(lambda fx, fill, sig: sig.event_key_primary),
        )

    def test_alternative_partition_matches(self):
        self.assertEqual(
            self._partition(lambda fx, fill, sig: fill["event_keys"]["alternative"]),
            self._partition(lambda fx, fill, sig: sig.event_key_alternative),
        )

    def test_convergence_survives(self):
        # Phase 13G: MNQ L 1m B is 7 fills over 3 alternative events.
        keys = [sig.event_key_alternative for fx, _, sig in ALL_SIGNALS
                if fx["fixture_id"] == "v53-MNQ-L-1m-B"]
        self.assertEqual(len(keys), 7)
        self.assertEqual(len(set(keys)), 3)

    def test_signal_ids_are_unique_across_all_fills(self):
        ids = [sig.signal_id for _, _, sig in ALL_SIGNALS]
        self.assertEqual(len(set(ids)), 58)


class TestDeterminismOverRealData(unittest.TestCase):
    def test_mapping_is_reproducible(self):
        again = [signal_from_fill(fx, fill) for fx, fill, _ in ALL_SIGNALS]
        self.assertEqual(
            [dumps(s) for s in again],
            [dumps(sig) for _, _, sig in ALL_SIGNALS],
        )

    def test_serialisation_emits_no_floats(self):
        for fx, fill, sig in ALL_SIGNALS:
            encoded = encode(sig)  # raises TypeError on any float
            self.assertIsInstance(encoded["fill"]["entry"], str)


class TestPreFeStillEnforced(unittest.TestCase):
    def test_every_mapped_timestamp_is_pre_fe(self):
        checked = 0
        for _, _, sig in ALL_SIGNALS:
            for stage in (sig.sweep, sig.choch, sig.retest, sig.bos, sig.fvg,
                          sig.fill, sig.outcome):
                assert_pre_fe(stage.ts_ms)
                assert_pre_fe(stage.bar_close_ts_ms)
                checked += 2
        self.assertEqual(checked, 58 * 7 * 2)

    def test_derived_bar_close_never_crosses_fe(self):
        # The +5m rounding must not push the last fold C bar past the boundary.
        from bot.guards import FE_MS
        for _, _, sig in ALL_SIGNALS:
            self.assertLess(sig.fill.bar_close_ts_ms, FE_MS)


if __name__ == "__main__":
    unittest.main()

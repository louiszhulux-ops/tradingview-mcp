"""B1 contract tests.

These test the **contracts**, not V53. Nothing here asserts that a sweep is
detected, that a CHOCH is selected correctly, or that an outcome is right — that
is B2's behaviour and B3's comparison. A test that would only pass by
duplicating V53's logic does not belong in this file.
"""

from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from bot.contracts.engine import BarResult, ReplayResult, StrategyEngine
from bot.contracts.enums import (
    ASSERTION_COUNTERS, DEADLINE_STATES, LIVE_STATES, LTF_CHOICES, Direction,
    ExitReason, Outcome, SlotState, SweepSource, Timeframe, TransitionReason,
)
from bot.contracts.events import (
    SIGNAL_SCHEMA_VERSION, BosEvent, ChochEvent, EventContractError, FillEvent,
    FvgEvent, OutcomeEvent, RetestEvent, SequenceRef, StrategySignal, SweepEvent,
)
from bot.contracts.serialize import canonical, dumps, encode
from bot.contracts.state import (
    RING_BUFFER_SIZE, SLOT_COUNT, LtfRingEntry, PivotRecord, SequenceSlot,
    SlotTransition, StateContractError, StrategyState, SweepEngineState,
)
from bot.data.bars import Bar, BarContractError, ParentBar, validate_series
from bot.guards import FE_MS, HeldOutDataError

SHA = "2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6"
T0 = 1782864000000  # 2026-07-01 00:00 UTC — inside the consumed research window
D = Decimal


def bar(offset_min=0, tf=Timeframe.M5, inst="MGC1!", **kw):
    minutes = tf.minutes
    open_ms = T0 + offset_min * 60_000
    fields = dict(open=D("4000"), high=D("4010"), low=D("3990"), close=D("4005"))
    fields.update(kw)
    return Bar(inst, tf, open_ms, open_ms + minutes * 60_000, **fields)


def parent(offset_min=0, ltf=Timeframe.M1, count=5):
    return ParentBar(
        bar(offset_min),
        ltf,
        [bar(offset_min + i * ltf.minutes, tf=ltf) for i in range(count)],
    )


def sequence_ref(slot=0):
    return SequenceRef("MGC1!", Direction.LONG, Timeframe.M1, slot, T0)


def signal(ref=None, with_outcome=True):
    ref = ref or sequence_ref()
    kw = dict(ref=ref, ts_ms=T0, bar_close_ts_ms=T0 + 300_000)
    outcome = OutcomeEvent(**kw, outcome=Outcome.WIN, exit_reason=ExitReason.TARGET,
                           r_multiple=D("4.958"), r_multiple_gross=D("5.0"),
                           pnl_usd=D("357.53"), bars_in_trade=13)
    return StrategySignal(
        schema_version=SIGNAL_SCHEMA_VERSION, strategy_id="V53", strategy_sha256=SHA,
        ref=ref,
        sweep=SweepEvent(**kw, sources=(SweepSource.SW,), extreme=D("4056.7"),
                         stop=D("4055.7894"), atr_at_arm=D("5.5"), parent_bar_index=3),
        choch=ChochEvent(**kw, level=D("4059.3"), pivot_index=12, ltf_index=40),
        retest=RetestEvent(**kw, level=D("4059.3"), ltf_index=41),
        bos=BosEvent(**kw, level=D("4061.2"), displacement_ltf_index=47, bar_range=D("2.1")),
        fvg=FvgEvent(**kw, low=D("4063"), high=D("4068.5"), entry=D("4063")),
        fill=FillEvent(**kw, entry=D("4063"), stop=D("4055.7894"),
                       r_distance=D("7.2106"), r_atr_ratio=D("1.31")),
        outcome=outcome if with_outcome else None,
        fold="A",
    )


# ---------------------------------------------------------------- 1. bars

class TestValidBarConstruction(unittest.TestCase):
    def test_valid_5m_bar(self):
        b = bar()
        self.assertEqual(b.timeframe, Timeframe.M5)
        self.assertEqual(b.close_ts_ms - b.open_ts_ms, 300_000)
        self.assertEqual(b.range, D("20"))
        self.assertTrue(b.complete)

    def test_prices_accept_exact_decimal_strings(self):
        b = bar(open="4000.25", high="4010.5", low="3990", close="4005")
        self.assertEqual(b.open, D("4000.25"))
        self.assertIsInstance(b.high, Decimal)

    def test_float_prices_are_rejected(self):
        with self.assertRaises(BarContractError):
            bar(open=4000.0)

    def test_volume_optional_and_non_negative(self):
        self.assertIsNone(bar().volume)
        self.assertEqual(bar(volume=D("12")).volume, D("12"))
        with self.assertRaises(BarContractError):
            bar(volume=D("-1"))

    def test_incoherent_ohlc_is_rejected(self):
        with self.assertRaises(BarContractError):
            bar(low=D("4020"))            # low above high
        with self.assertRaises(BarContractError):
            bar(close=D("4999"))          # close outside the bracket

    def test_bar_is_immutable(self):
        with self.assertRaises(Exception):
            bar().close = D("1")


class TestTimestampRejection(unittest.TestCase):
    def test_missing_timestamp_is_rejected(self):
        with self.assertRaises(HeldOutDataError):
            Bar("MGC1!", Timeframe.M5, None, T0 + 300_000,
                D("1"), D("1"), D("1"), D("1"))

    def test_malformed_timestamp_is_rejected(self):
        with self.assertRaises(HeldOutDataError):
            Bar("MGC1!", Timeframe.M5, "1782864000000", T0 + 300_000,
                D("1"), D("1"), D("1"), D("1"))

    def test_wrong_span_is_rejected(self):
        with self.assertRaises(BarContractError):
            Bar("MGC1!", Timeframe.M5, T0, T0 + 60_000,
                D("1"), D("1"), D("1"), D("1"))

    def test_off_grid_timestamp_is_rejected(self):
        with self.assertRaises(BarContractError):
            Bar("MGC1!", Timeframe.M5, T0 + 1, T0 + 300_001,
                D("1"), D("1"), D("1"), D("1"))


class TestTimeframeValidity(unittest.TestCase):
    def test_timeframe_must_be_the_enum(self):
        with self.assertRaises(BarContractError):
            Bar("MGC1!", "5m", T0, T0 + 300_000, D("1"), D("1"), D("1"), D("1"))

    def test_ltf_choices_are_1m_and_3m(self):
        self.assertEqual(LTF_CHOICES, (Timeframe.M1, Timeframe.M3))
        self.assertTrue(Timeframe.M1.is_ltf and Timeframe.M3.is_ltf)
        self.assertFalse(Timeframe.M5.is_ltf)

    def test_parent_bar_must_be_5m(self):
        with self.assertRaises(BarContractError):
            ParentBar(bar(tf=Timeframe.M1), Timeframe.M1, [])

    def test_parent_bar_rejects_5m_as_its_ltf(self):
        with self.assertRaises(BarContractError):
            ParentBar(bar(), Timeframe.M5, [])

    def test_ltf_stream_does_not_substitute_for_5m(self):
        # The contract makes the substitution unrepresentable, which is the point.
        with self.assertRaises(BarContractError):
            ParentBar(bar(tf=Timeframe.M1), Timeframe.M1,
                      [bar(tf=Timeframe.M1)])


class TestParentBarNesting(unittest.TestCase):
    def test_complete_1m_nesting(self):
        p = parent()
        self.assertEqual(p.ltf_count, 5)
        self.assertTrue(p.ltf_complete)

    def test_short_ltf_array_is_represented_not_repaired(self):
        p = parent(count=2)
        self.assertEqual(p.ltf_count, 2)
        self.assertFalse(p.ltf_complete)

    def test_empty_ltf_array_is_allowed(self):
        self.assertEqual(parent(count=0).ltf_count, 0)

    def test_3m_completeness_is_undefined_not_guessed(self):
        # U3: 3 does not divide 5, so no count is asserted.
        p = ParentBar(bar(), Timeframe.M3, [bar(tf=Timeframe.M3)])
        self.assertFalse(p.ltf_complete)

    def test_sub_bar_outside_parent_is_rejected(self):
        with self.assertRaises(BarContractError):
            ParentBar(bar(), Timeframe.M1, [bar(offset_min=10, tf=Timeframe.M1)])

    def test_out_of_order_sub_bars_are_rejected(self):
        subs = [bar(offset_min=i, tf=Timeframe.M1) for i in range(3)]
        with self.assertRaises(BarContractError):
            ParentBar(bar(), Timeframe.M1, [subs[0], subs[2], subs[1]])

    def test_mixed_instrument_sub_bar_is_rejected(self):
        with self.assertRaises(BarContractError):
            ParentBar(bar(), Timeframe.M1, [bar(tf=Timeframe.M1, inst="MNQ1!")])


class TestSeriesValidation(unittest.TestCase):
    def test_ordered_series_passes(self):
        self.assertEqual(len(validate_series([bar(0), bar(5), bar(10)])), 3)

    def test_session_gaps_are_allowed(self):
        validate_series([bar(0), bar(5), bar(4320)])  # a weekend-sized gap

    def test_duplicate_out_of_order_and_overlap_are_rejected(self):
        for series in ([bar(0), bar(0)], [bar(5), bar(0)]):
            with self.assertRaises(BarContractError):
                validate_series(series)


# ---------------------------------------------------------------- 2. determinism

class TestDeterministicSerialisation(unittest.TestCase):
    def test_bar_serialisation_is_stable(self):
        self.assertEqual(dumps(bar()), dumps(bar()))
        self.assertEqual(canonical(bar()), canonical(bar()))

    def test_keys_are_sorted(self):
        keys = list(encode(bar()).keys())
        self.assertEqual(keys, sorted(keys))

    def test_prices_serialise_as_exact_strings(self):
        encoded = encode(bar(open="4000.2500"))
        self.assertEqual(encoded["open"], "4000.2500")
        self.assertIsInstance(encoded["open"], str)

    def test_floats_are_refused_by_the_encoder(self):
        with self.assertRaises(TypeError):
            encode({"price": 1.5})

    def test_event_serialisation_is_stable(self):
        self.assertEqual(dumps(signal()), dumps(signal()))

    def test_sequence_order_is_preserved(self):
        p = parent()
        encoded = encode(p)
        self.assertEqual(
            [b["open_ts_ms"] for b in encoded["ltf_bars"]],
            [b.open_ts_ms for b in p.ltf_bars],
        )

    def test_signal_id_is_reproducible_and_not_random(self):
        self.assertEqual(signal().signal_id, signal().signal_id)
        self.assertEqual(len(signal().signal_id), 32)

    def test_signal_id_is_stable_across_outcome_resolution(self):
        # The id must not change when the trade resolves.
        self.assertEqual(signal(with_outcome=False).signal_id, signal().signal_id)

    def test_different_sequences_get_different_ids(self):
        self.assertNotEqual(signal().signal_id, signal(sequence_ref(slot=7)).signal_id)


# ---------------------------------------------------------------- 3. enums

class TestDirectionAndVocabulary(unittest.TestCase):
    def test_direction_values_match_the_ledger(self):
        self.assertEqual(Direction.LONG.value, "L")
        self.assertEqual(Direction.SHORT.value, "S")
        self.assertEqual(Direction.LONG.dir_mode, 1)
        self.assertEqual(Direction.SHORT.dir_mode, -1)

    def test_invalid_direction_is_rejected(self):
        with self.assertRaises(ValueError):
            Direction("long")

    def test_slot_states_match_the_frozen_encoding(self):
        self.assertEqual(
            [s.value for s in SlotState],
            [0, 1, 2, 3, 4, 5, 6],
        )
        self.assertEqual(SlotState.IN_TRADE, 6)

    def test_deadline_and_live_state_sets(self):
        self.assertEqual(DEADLINE_STATES, (SlotState.ARMED, SlotState.CHOCH, SlotState.RETESTED))
        self.assertEqual(len(LIVE_STATES), 4)

    def test_every_transition_maps_to_a_v53_counter(self):
        for reason in TransitionReason:
            self.assertIsInstance(reason.k_index, int)

    def test_assertion_counter_set(self):
        self.assertEqual(ASSERTION_COUNTERS, (21, 22, 23, 24, 25, 26, 27, 32))

    def test_exit_reason_encoding(self):
        self.assertEqual([r.rsn for r in (ExitReason.STOP, ExitReason.TARGET, ExitReason.TIMEOUT)],
                         [1, 2, 3])


# ---------------------------------------------------------------- 4. state

class TestStateAndSlotIdentity(unittest.TestCase):
    def test_state_defaults_to_24_free_slots(self):
        s = StrategyState("MGC1!", Direction.LONG, Timeframe.M1, SHA)
        self.assertEqual(len(s.slots), SLOT_COUNT)
        self.assertTrue(all(slot.is_free for slot in s.slots))
        self.assertEqual([slot.index for slot in s.slots], list(range(24)))

    def test_pivot_register_holds_four_entries(self):
        s = StrategyState("MGC1!", Direction.LONG, Timeframe.M1, SHA)
        self.assertEqual(len(s.pivots), 4)
        self.assertFalse(s.pivots[0].is_set)

    def test_ring_buffer_size_is_seven(self):
        self.assertEqual(RING_BUFFER_SIZE, 7)
        s = StrategyState("MGC1!", Direction.LONG, Timeframe.M1, SHA)
        self.assertFalse(s.ring_full)

    def test_ring_buffer_cannot_exceed_its_size(self):
        entries = tuple(
            LtfRingEntry(D("1"), D("1"), D("1"), 0, i + 1, T0) for i in range(8)
        )
        with self.assertRaises(StateContractError):
            StrategyState("MGC1!", Direction.LONG, Timeframe.M1, SHA, ltf_ring=entries)

    def test_slot_index_must_be_in_range(self):
        with self.assertRaises(StateContractError):
            SequenceSlot(index=24)
        with self.assertRaises(StateContractError):
            SequenceSlot(index=-1)

    def test_slot_carries_every_v53_array(self):
        slot = SequenceSlot(index=0)
        for name in ("sweep_bar_index", "stop", "atr_at_arm", "choch_level", "pivot_ref",
                     "choch_pivot_index", "choch_ltf_index", "retest_ltf_index",
                     "displacement_ltf_index", "entry", "r_distance", "fvg_wait_bars",
                     "bars_in_trade", "max_favourable_r", "max_adverse_r", "target_reached"):
            self.assertTrue(hasattr(slot, name), name)
        self.assertEqual(len(SequenceSlot.LEDGER_FIELDS), 10)

    def test_ltf_must_be_1m_or_3m(self):
        with self.assertRaises(StateContractError):
            StrategyState("MGC1!", Direction.LONG, Timeframe.M5, SHA)

    def test_state_serialises_deterministically(self):
        a = StrategyState("MGC1!", Direction.LONG, Timeframe.M1, SHA)
        b = StrategyState("MGC1!", Direction.LONG, Timeframe.M1, SHA)
        self.assertEqual(dumps(a), dumps(b))

    def test_transition_freeing_a_slot_must_land_on_free(self):
        with self.assertRaises(StateContractError):
            SlotTransition(0, SlotState.ARMED, SlotState.CHOCH,
                           TransitionReason.EXPIRE_PRE_CHOCH, 5, T0)

    def test_transition_records_provenance(self):
        t = SlotTransition(3, SlotState.FVG_AWAIT_FILL, SlotState.IN_TRADE,
                           TransitionReason.FILLED, 12, T0, ltf_index=88)
        self.assertEqual(t.reason.k_index, 12)
        self.assertFalse(t.reason.frees_slot)

    def test_held_out_timestamp_cannot_enter_state(self):
        with self.assertRaises(HeldOutDataError):
            LtfRingEntry(D("1"), D("1"), D("1"), 0, 1, FE_MS)


# ---------------------------------------------------------------- 5. events

class TestEventContracts(unittest.TestCase):
    def test_sweep_kind_renders_in_v53_order(self):
        ref = sequence_ref()
        kw = dict(ref=ref, ts_ms=T0, bar_close_ts_ms=T0)
        self.assertEqual(SweepEvent(**kw, sources=(SweepSource.SW, SweepSource.PD)).kind, "PD+SW")
        self.assertEqual(SweepEvent(**kw, sources=(SweepSource.AS,)).kind, "AS")

    def test_sweep_needs_at_least_one_source(self):
        with self.assertRaises(EventContractError):
            SweepEvent(sequence_ref(), T0, T0, sources=())

    def test_duplicate_sweep_source_is_rejected(self):
        with self.assertRaises(EventContractError):
            SweepEvent(sequence_ref(), T0, T0, sources=(SweepSource.PD, SweepSource.PD))

    def test_fvg_bounds_must_be_ordered(self):
        with self.assertRaises(EventContractError):
            FvgEvent(sequence_ref(), T0, T0, low=D("10"), high=D("1"))

    def test_signal_rejects_a_bad_strategy_hash(self):
        with self.assertRaises(EventContractError):
            StrategySignal(SIGNAL_SCHEMA_VERSION, "V53", "not-a-hash", **{
                k: getattr(signal(), k) for k in
                ("ref", "sweep", "choch", "retest", "bos", "fvg", "fill")})

    def test_signal_rejects_a_stage_from_another_sequence(self):
        s = signal()
        foreign = ChochEvent(sequence_ref(slot=9), T0, T0, level=D("1"))
        with self.assertRaises(EventContractError):
            StrategySignal(SIGNAL_SCHEMA_VERSION, "V53", SHA, s.ref, s.sweep, foreign,
                           s.retest, s.bos, s.fvg, s.fill)

    def test_event_keys_have_the_phase13g_shape(self):
        s = signal()
        self.assertEqual(len(s.event_key_primary.split("|")), 9)
        self.assertEqual(len(s.event_key_alternative.split("|")), 7)

    def test_outcome_is_optional_while_open(self):
        self.assertIsNone(signal(with_outcome=False).outcome)

    def test_no_trading_rule_is_enforced_by_the_schema(self):
        """A stop on the near side of entry must be representable (see U-R8)."""
        ref = sequence_ref()
        kw = dict(ref=ref, ts_ms=T0, bar_close_ts_ms=T0)
        fill = FillEvent(**kw, entry=D("30380.25"), stop=D("30361.5423"),
                         r_distance=D("18.7077"), r_atr_ratio=D("999"))
        self.assertEqual(fill.stop, D("30361.5423"))  # accepted, not rejected


class TestSignalRoundTrip(unittest.TestCase):
    def test_serialise_round_trip_preserves_every_value(self):
        original = signal()
        encoded = encode(original)
        self.assertEqual(encoded["strategy_sha256"], SHA)
        self.assertEqual(encoded["fill"]["entry"], "4063")
        self.assertEqual(encoded["outcome"]["r_multiple"], "4.958")
        self.assertEqual(encoded["sweep"]["kind"], "SW")
        # Re-encoding the decoded form is stable.
        self.assertEqual(dumps(original), dumps(original))

    def test_decimals_survive_as_exact_text(self):
        encoded = encode(signal())
        self.assertEqual(D(encoded["fill"]["stop"]), D("4055.7894"))


# ---------------------------------------------------------------- 6. boundary

class TestEngineBoundary(unittest.TestCase):
    def test_bar_result_is_ordered_and_serialisable(self):
        r = BarResult(bar_close_ts_ms=T0 + 300_000, signals=(signal(),))
        self.assertEqual(dumps(r), dumps(r))
        self.assertEqual(len(r.signals), 1)

    def test_replay_result_flattens_in_order(self):
        rr = ReplayResult("MGC1!", "L", "1m", SHA, bars_processed=2, results=[
            BarResult(T0, signals=(signal(),)),
            BarResult(T0 + 300_000, signals=(signal(sequence_ref(slot=1)),)),
        ])
        self.assertEqual([s.ref.slot_index for s in rr.signals], [0, 1])

    def test_engine_protocol_is_not_satisfied_by_anything_accidental(self):
        self.assertFalse(isinstance(object(), StrategyEngine))

    def test_boundary_imports_no_execution_layer(self):
        import bot.contracts.engine as engine
        source = Path(engine.__file__).read_text(encoding="utf-8")
        for forbidden in ("broker", "Broker", "order", "risk", "position"):
            self.assertNotIn(f"import {forbidden}", source)


if __name__ == "__main__":
    unittest.main()

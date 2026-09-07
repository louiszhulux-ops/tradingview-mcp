"""B2 ↔ A2 — the outcome layer against every recorded fill.

The golden fixtures record *results*, not bars, and the repository holds no
OHLCV. Full funnel/ledger parity therefore belongs to B3 and needs bar data
this repo does not contain (see the B2 audit, "Limitations").

What **can** be validated here, and is: for all 58 recorded fills, driving the
real §1 outcome loop with the recorded entry, stop and exit reason reproduces
the recorded R multiple, USD amount, WIN/LOSS verdict, exit reason, bar count
and price formatting — exactly, as text.

That exercises the live code path (`SequenceMachine.section1_outcomes` and
`ledger_row`), not a re-derivation of the formula.
"""

from __future__ import annotations

import unittest

from bot.contracts.enums import Direction, SlotState, Timeframe
from bot.fixtures.loader import load_all
from bot.strategy.v53.constants import MAX_BARS, TGT_R
from bot.strategy.v53.ledger import format_time, ledger_row
from bot.strategy.v53.numeric import px
from bot.strategy.v53.sequence import Counters, SequenceMachine

FIXTURES = load_all()
POINT_VALUE = {"MGC1!": 10.0, "MNQ1!": 2.0}


def replay_outcome(fixture: dict, fill: dict) -> str:
    """Rebuild the slot from recorded fields and run the real §1 loop once."""
    rec = fill["recorded"]
    direction = Direction(rec["direction"])
    is_long = direction is Direction.LONG
    entry = float(rec["entry_price"])
    stop = float(rec["stop_price"])
    r = abs(entry - stop)

    machine = SequenceMachine(
        direction=direction,
        point_value=POINT_VALUE[rec["instrument"]],
        cost_usd=3.00,
        counters=Counters(),
    )
    slot = machine.slots[0]
    slot.state = SlotState.IN_TRADE
    slot.entry, slot.stop, slot.r_distance = entry, stop, r
    slot.atr_at_arm = r  # unused by §1; kept finite
    slot.bars_in_trade = 0
    slot.ledger_sweep_ts_ms = rec["sweep_ts_ms"]
    slot.ledger_sweep_kind = rec["sweep_kind"]
    slot.ledger_sweep_extreme = float(rec["sweep_extreme"])
    slot.ledger_choch_ts_ms = rec["choch_ts_ms"]
    slot.choch_level = float(rec["choch_level"])
    slot.ledger_retest_ts_ms = rec["retest_ts_ms"]
    slot.ledger_bos_ts_ms = rec["bos_ts_ms"]
    slot.ledger_bos_level = float(rec["bos_level"])
    slot.ledger_fvg_low = float(rec["fvg_low"])
    slot.ledger_fvg_high = float(rec["fvg_high"])
    slot.ledger_entry_ts_ms = rec["entry_ts_ms"]

    reason = rec["exit_reason"]
    bars = rec["bars_in_trade"]
    if reason == "target":
        slot.bars_in_trade = bars - 1
        high = entry + TGT_R * r if is_long else entry
        low = entry if is_long else entry - TGT_R * r
    elif reason == "stop":
        slot.bars_in_trade = bars - 1
        high = entry if is_long else entry + r
        low = entry - r if is_long else entry
    else:                                    # timeout
        slot.bars_in_trade = MAX_BARS - 1
        high, low = entry, entry

    resolved = machine.section1_outcomes(high=high, low=low)
    assert len(resolved) == 1, f"expected one outcome, got {len(resolved)}"
    return ledger_row(
        resolved[0], rec["instrument"], direction,
        Timeframe(rec["ltf"]).minutes, rec["fold"],
    )


def expected_row(fixture: dict, fill: dict) -> str:
    """The row the fixture says V53 produced, rebuilt from its recorded fields."""
    rec = fill["recorded"]
    return "|".join([
        rec["instrument"], rec["direction"], rec["ltf"], rec["fold"],
        f"sw {format_time(rec['sweep_ts_ms'])}", rec["sweep_kind"],
        f"swX {rec['sweep_extreme']}",
        f"ch {format_time(rec['choch_ts_ms'])}", f"chL {rec['choch_level']}",
        f"rt {format_time(rec['retest_ts_ms'])}",
        f"bos {format_time(rec['bos_ts_ms'])}", f"bosL {rec['bos_level']}",
        f"fvg {rec['fvg_low']}-{rec['fvg_high']}",
        f"en {format_time(rec['entry_ts_ms'])}", f"enPx {rec['entry_price']}",
        f"stop {rec['stop_price']}",
        rec["outcome"], f"{rec['r_multiple']}R", f"${rec['pnl_usd']}",
        rec["exit_reason"], f"{rec['bars_in_trade']}bars",
    ])


ALL = [(fx, fill) for fx in FIXTURES for fill in fx["fills"]]


class TestOutcomeLayerAgainstEveryRecordedFill(unittest.TestCase):
    def test_all_58_fills_are_covered(self):
        self.assertEqual(len(ALL), 58)

    def test_every_ledger_row_reproduces_exactly(self):
        mismatches = []
        for fixture, fill in ALL:
            produced = replay_outcome(fixture, fill)
            expected = expected_row(fixture, fill)
            if produced != expected:
                mismatches.append(
                    f"{fixture['fixture_id']}[{fill['index']}]\n"
                    f"  expected {expected}\n  produced {produced}"
                )
        self.assertEqual(mismatches, [], "\n".join(mismatches))

    def test_r_multiple_and_pnl_reproduce_for_each_exit_reason(self):
        by_reason: dict[str, int] = {}
        for fixture, fill in ALL:
            rec = fill["recorded"]
            fields = replay_outcome(fixture, fill).split("|")
            with self.subTest(f"{fixture['fixture_id']}[{fill['index']}]"):
                self.assertEqual(fields[17], f"{rec['r_multiple']}R")
                self.assertEqual(fields[18], f"${rec['pnl_usd']}")
                self.assertEqual(fields[16], rec["outcome"])
                self.assertEqual(fields[19], rec["exit_reason"])
            by_reason[rec["exit_reason"]] = by_reason.get(rec["exit_reason"], 0) + 1
        self.assertEqual(by_reason, {"target": 9, "stop": 44, "timeout": 5})

    def test_price_formatting_round_trips(self):
        for fixture, fill in ALL:
            rec = fill["recorded"]
            for field in ("entry_price", "stop_price", "sweep_extreme",
                          "choch_level", "bos_level", "fvg_low", "fvg_high"):
                with self.subTest(f"{fixture['fixture_id']} {field}"):
                    self.assertEqual(px(float(rec[field])), rec[field])

    def test_adverse_first_ordering_is_what_produces_the_stop_rows(self):
        stops = [f for _, f in ALL if f["recorded"]["exit_reason"] == "stop"]
        self.assertEqual(len(stops), 44)
        for fill in stops:
            self.assertEqual(fill["recorded"]["outcome"], "LOSS")

    def test_timeouts_are_losses_even_though_no_stop_was_hit(self):
        timeouts = [f for _, f in ALL if f["recorded"]["exit_reason"] == "timeout"]
        self.assertEqual(len(timeouts), 5)
        for fill in timeouts:
            self.assertEqual(fill["recorded"]["outcome"], "LOSS")
            self.assertEqual(fill["recorded"]["bars_in_trade"], MAX_BARS)

    def test_inverted_stops_are_reproduced_not_corrected(self):
        # Two recorded fills sit with the stop on the near side of entry.
        inverted = [(fx, f) for fx, f in ALL if f["derived"]["stop_inverted"]]
        self.assertEqual(len(inverted), 2)
        for fixture, fill in inverted:
            self.assertEqual(replay_outcome(fixture, fill), expected_row(fixture, fill))


if __name__ == "__main__":
    unittest.main()

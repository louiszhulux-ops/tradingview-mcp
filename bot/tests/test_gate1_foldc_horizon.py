"""The fold-C divergence: what the investigation established, pinned.

These tests record findings. **None of them exists to make Gate 1 look
cleaner**, and none asserts that V53 is reproduced. Two cells still diverge
after this file, exactly as they did before it.

The finding: V53 gates only *arming* on `inFold` (V53_ltf_sequence.pine:506).
Sections 1-4 — outcomes, fills, the deadline and the whole LTF loop — run
ungated on every bar, so a sequence armed inside a fold keeps generating
counted events on bars *after* that fold ends. The Phase 14 fold-C runs were
executed on a chart that continued past `FE`; our replay stops at `FE` because
it must. A sequence still live at our last bar therefore loses the events it
would have produced on bars we do not have, and may never have.
"""

from __future__ import annotations

import unittest

from bot.contracts.enums import SlotState, Timeframe
from bot.fixtures.loader import load_fixture
from bot.replay.compare import BEHAVIOUR_COUNTERS
from bot.replay.harness import COST_USD, POINT_VALUE, registered_cells
from bot.replay.loader import load_cell_dataset
from bot.strategy.v53.constants import DISP_WAIT
from bot.strategy.v53.engine import V53Config, V53Engine

DIVERGENT = {"v53-MGC-L-1m-C", "v53-MNQ-L-1m-C"}
CLEAN = {"v53-MGC-S-1m-C", "v53-MNQ-S-1m-C"}


def _replay(cell, parents):
    engine = V53Engine(V53Config(
        instrument=cell.instrument, direction=cell.direction, ltf=cell.ltf,
        point_value=POINT_VALUE[cell.instrument], fold=cell.fold,
        cost_usd=COST_USD))
    for parent in parents:
        engine.on_bar(parent)
    return engine


class FoldCHorizon(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cells = {c.cell_id: c for c in registered_cells()
                     if c.ltf is Timeframe.M1 and c.fold == "C"}
        cache: dict = {}
        cls.engines = {}
        cls.parents = {}
        for cell_id, cell in cls.cells.items():
            key = (cell.instrument, cell.ltf)
            if key not in cache:
                cache[key] = load_cell_dataset(
                    cell_id=cell_id, instrument=cell.instrument,
                    fold=cell.fold, ltf=cell.ltf)
            cls.parents[cell_id] = cache[key].parents
            cls.engines[cell_id] = _replay(cell, cache[key].parents)

    def live(self, cell_id):
        return [s for s in self.engines[cell_id].machine.slots
                if s.state is not SlotState.FREE]

    # ---- the correlation ------------------------------------------------

    def test_divergent_cells_have_a_sequence_live_at_the_horizon(self):
        for cell_id in sorted(DIVERGENT):
            with self.subTest(cell=cell_id):
                self.assertEqual(len(self.live(cell_id)), 1)

    def test_clean_cells_have_no_sequence_live_at_the_horizon(self):
        for cell_id in sorted(CLEAN):
            with self.subTest(cell=cell_id):
                self.assertEqual(self.live(cell_id), [])

    def test_clean_cells_reproduce_every_behaviour_counter(self):
        """Stated as a fact about these four cells, not as parity evidence:
        the datasets are CANDIDATE and cannot support a parity claim."""
        for cell_id in sorted(CLEAN):
            golden = load_fixture(cell_id)["funnel"]
            counters = self.engines[cell_id].counters
            for name in BEHAVIOUR_COUNTERS:
                with self.subTest(cell=cell_id, counter=name):
                    self.assertEqual(getattr(counters, name), golden[name])

    def test_divergent_cells_still_diverge(self):
        """This investigation did not remove the divergence, and must not."""
        for cell_id in sorted(DIVERGENT):
            golden = load_fixture(cell_id)["funnel"]
            counters = self.engines[cell_id].counters
            deltas = {name: getattr(counters, name) - golden[name]
                      for name in BEHAVIOUR_COUNTERS
                      if getattr(counters, name) != golden[name]}
            with self.subTest(cell=cell_id):
                self.assertTrue(deltas)
                self.assertTrue(all(d < 0 for d in deltas.values()),
                                "every divergence is a deficit, never a surplus")

    def test_the_recorded_deltas_are_pinned(self):
        self.assertEqual(
            self._deltas("v53-MGC-L-1m-C"),
            {"choch": -1, "retests": -1, "break_no_displacement": -8,
             "expire_post_retest": -1})
        self.assertEqual(
            self._deltas("v53-MNQ-L-1m-C"), {"expire_pre_choch": -1})

    def _deltas(self, cell_id):
        golden = load_fixture(cell_id)["funnel"]
        counters = self.engines[cell_id].counters
        return {name: getattr(counters, name) - golden[name]
                for name in BEHAVIOUR_COUNTERS
                if getattr(counters, name) != golden[name]}

    # ---- the MNQ case, derived exactly ----------------------------------

    def test_mnq_live_slot_is_one_bar_short_of_its_deadline(self):
        """§3 fires when `bar_index - swB > dispWait`, i.e. at age 13.

        The slot reaches age 12 on our final bar, so the expiry lands on the
        first bar we do not have — and `K[14 + state]` with state ARMED is
        `expire_pre_choch`, the one counter that differs.
        """
        engine = self.engines["v53-MNQ-L-1m-C"]
        slot = self.live("v53-MNQ-L-1m-C")[0]
        age = engine.bar_index - slot.sweep_bar_index
        self.assertIs(slot.state, SlotState.ARMED)
        self.assertEqual(age, DISP_WAIT)
        self.assertFalse(age > DISP_WAIT, "the deadline has not fired yet")
        self.assertTrue(age + 1 > DISP_WAIT, "it fires on the very next bar")
        self.assertEqual(self._deltas("v53-MNQ-L-1m-C"), {"expire_pre_choch": -1})

    def test_mgc_live_slot_armed_on_the_penultimate_bar(self):
        engine = self.engines["v53-MGC-L-1m-C"]
        slot = self.live("v53-MGC-L-1m-C")[0]
        self.assertIs(slot.state, SlotState.ARMED)
        self.assertEqual(engine.bar_index - slot.sweep_bar_index, 1)

    # ---- the mechanism, reproduced generatively -------------------------

    def test_truncating_a_clean_cell_reproduces_the_same_signature(self):
        """Cut a clean cell's replay while a sequence is live and the same
        shape of deficit appears: downstream counters only, never `sweeps`."""
        cell_id = "v53-MNQ-S-1m-C"
        cell = self.cells[cell_id]
        full = self.engines[cell_id].counters
        trimmed = _replay(cell, self.parents[cell_id][:-20])
        deltas = {name: getattr(trimmed.counters, name) - getattr(full, name)
                  for name in BEHAVIOUR_COUNTERS
                  if getattr(trimmed.counters, name) != getattr(full, name)}
        self.assertEqual(deltas, {"choch": -1, "expire_post_choch": -1})
        self.assertNotIn("sweeps", deltas)
        self.assertEqual(
            len([s for s in trimmed.machine.slots if s.state is not SlotState.FREE]), 1)

    def test_truncating_with_no_live_sequence_changes_nothing(self):
        cell_id = "v53-MGC-S-1m-C"
        cell = self.cells[cell_id]
        full = self.engines[cell_id].counters
        for cut in (2, 5, 10):
            trimmed = _replay(cell, self.parents[cell_id][:-cut])
            with self.subTest(cut=cut):
                for name in BEHAVIOUR_COUNTERS:
                    self.assertEqual(getattr(trimmed.counters, name),
                                     getattr(full, name))

    # ---- what K31 is, and what it proves --------------------------------

    def test_the_historical_chart_must_have_extended_past_fe(self):
        """Arithmetic, independent of any run-date inference.

        K31 counts one per LTF array element consumed and is uncapped in the
        artifact. A 1m stream cannot deliver more than 5 elements per 5m
        parent, so 100,000 needs at least 20,000 parents — more than the whole
        pre-`FE` series contains.
        """
        for cell_id in sorted(DIVERGENT | CLEAN):
            golden = load_fixture(cell_id)["funnel"]
            parents = len(self.parents[cell_id])
            with self.subTest(cell=cell_id):
                self.assertEqual(golden["ltf_bars"], 100_000)
                self.assertGreater(100_000, parents * 5)

    def test_k31_counts_chart_wide_not_fold_scoped(self):
        """Behavioural proof, independent of reading the artifact.

        A fold-C cell sees 4,164 in-fold parents, so a fold-scoped counter could
        not exceed 4,164 x 5 = 20,820. It reports more than four times that,
        because the LTF loop runs on every bar of the chart.
        """
        for cell_id in sorted(DIVERGENT | CLEAN):
            engine = self.engines[cell_id]
            with self.subTest(cell=cell_id):
                self.assertEqual(engine.counters.fold_bars, 4164)
                self.assertGreater(engine.counters.ltf_bars_seen, 4164 * 5)
                self.assertGreater(engine.counters.ltf_bars_seen,
                                   engine.counters.fold_bars_with_ltf * 5)

    def test_k31_is_not_fold_gated_in_the_frozen_artifact(self):
        """Structural pin, read-only, against V53_ltf_sequence.pine.

        `inFold` appears in exactly three places: its definition, the K29/K30
        coverage counters, and the section 5 arm gate. The LTF loop that
        increments K31 is not one of them, so nothing downstream of arming is
        fold-gated.
        """
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        lines = (root / "trader_v2" / "V53_ltf_sequence.pine").read_text(
            encoding="utf-8").splitlines()
        in_fold_lines = [i + 1 for i, line in enumerate(lines) if "inFold" in line]
        self.assertEqual(in_fold_lines, [34, 317, 506])

        k31 = [i for i, line in enumerate(lines) if "K, 31" in line]
        self.assertEqual(len(k31), 1)
        # Walk back to the enclosing block header: the LTF loop, ATR-gated and
        # ungated by inFold.
        guard = next(line for line in reversed(lines[:k31[0]])
                     if line.startswith("if "))
        self.assertIn("nL > 0", guard)
        self.assertIn("not na(atr)", guard)
        self.assertNotIn("inFold", guard)
        # And the counter itself is uncapped in the artifact.
        self.assertNotIn("100000", "\n".join(lines))

    def test_fold_c_coverage_itself_is_not_short(self):
        """The deficit is not inside fold C: every fold-C parent has LTF."""
        for cell_id in sorted(DIVERGENT | CLEAN):
            golden = load_fixture(cell_id)["funnel"]
            counters = self.engines[cell_id].counters
            with self.subTest(cell=cell_id):
                self.assertEqual(counters.fold_bars, golden["fold_bars"])
                self.assertEqual(counters.fold_bars_with_ltf,
                                 golden["fold_bars_with_ltf"])
                self.assertEqual(counters.fold_bars_with_ltf, counters.fold_bars)


if __name__ == "__main__":
    unittest.main()

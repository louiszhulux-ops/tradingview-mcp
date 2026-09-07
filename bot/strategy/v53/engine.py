"""V53 engine — one 5m bar close at a time, in the artifact's section order.

    §1 outcomes → §2 fills → §3 deadline → §4 LTF loop → §5 arm

`SECTION_ORDER` names that order so a test can assert it; reordering changes
results (see the B2 audit §"Causal ordering").

The engine is **pure with respect to its inputs**: no wall clock, no randomness,
no I/O, no module-level mutable state. Feeding the same bars to a fresh engine
twice produces identical output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from bot.contracts.enums import Direction, Timeframe
from bot.data.bars import ParentBar
from bot.strategy.v53.constants import (
    EXECUTED_SHA256, FOLD_B_START_MS, FOLD_C_START_MS, FOLD_END_MS, STRATEGY_ID,
)
from bot.strategy.v53.ledger import ledger_row
from bot.strategy.v53.levels import SweepEngine
from bot.strategy.v53.ltf import LtfState
from bot.strategy.v53.numeric import is_na, to_float
from bot.strategy.v53.sequence import Counters, Outcome, SequenceMachine

#: The five sections, in the order V53 runs them. Load-bearing.
SECTION_ORDER: Final[tuple[str, ...]] = (
    "outcomes", "fills", "deadline", "ltf_loop", "arm",
)

#: `foldSel` — the artifact's fold gate, which governs arming and the coverage
#: counters only. It never gates the LTF loop or sections 1–3.
FOLDS: Final[dict[str, str]] = {
    "A": "time < FB", "B": "FB <= time < FC", "C": "FC <= time < FE",
    "A+B": "time < FC", "ALL": "time < FE",
}


def in_fold(fold: str, bar_open_ts_ms: int) -> bool:
    """`inFold`, evaluated on the bar's OPEN time as Pine's `time` is."""
    if fold == "A":
        return bar_open_ts_ms < FOLD_B_START_MS
    if fold == "B":
        return FOLD_B_START_MS <= bar_open_ts_ms < FOLD_C_START_MS
    if fold == "C":
        return FOLD_C_START_MS <= bar_open_ts_ms < FOLD_END_MS
    if fold == "A+B":
        return bar_open_ts_ms < FOLD_C_START_MS
    if fold == "ALL":
        return bar_open_ts_ms < FOLD_END_MS
    raise ValueError(f"unknown fold {fold!r}; expected one of {sorted(FOLDS)}")


@dataclass(frozen=True)
class V53Config:
    """Everything the engine needs, stated explicitly. No hidden defaults.

    `point_value` has no default on purpose: V53 reads `syminfo.pointvalue` from
    the chart and silently falls back to 1.0, which would produce plausible,
    wrong USD in a bot (UNRESOLVED U4).
    """

    instrument: str
    direction: Direction
    ltf: Timeframe
    point_value: float
    fold: str = "ALL"
    cost_usd: float = 3.00

    def __post_init__(self) -> None:
        if self.ltf not in (Timeframe.M1, Timeframe.M3):
            raise ValueError(f"ltf must be 1m or 3m, got {self.ltf!r}")
        if self.fold not in FOLDS:
            raise ValueError(f"unknown fold {self.fold!r}")
        if not (self.point_value > 0):
            raise ValueError(
                f"point_value must be positive and explicit, got {self.point_value!r}; "
                f"V53's silent 1.0 fallback must not reach a bot (UNRESOLVED U4)"
            )

    @property
    def ticker(self) -> str:
        return self.instrument

    @property
    def is_long(self) -> bool:
        return self.direction is Direction.LONG


@dataclass
class BarOutput:
    """What one 5m bar close produced."""

    bar_open_ts_ms: int
    bar_index: int
    resolved: list[Outcome] = field(default_factory=list)
    ledger_rows: list[str] = field(default_factory=list)
    filled_slots: list[int] = field(default_factory=list)
    armed_slot: int | None = None
    in_fold: bool = False
    ltf_count: int = 0


class V53Engine:
    """Deterministic Python reproduction of the frozen V53 artifact."""

    strategy_id = STRATEGY_ID
    strategy_sha256 = EXECUTED_SHA256

    def __init__(self, config: V53Config) -> None:
        self.config = config
        self.counters = Counters()
        self.sweeps = SweepEngine(direction=config.direction)
        self.ltf = LtfState()
        self.machine = SequenceMachine(
            direction=config.direction,
            point_value=config.point_value,
            cost_usd=config.cost_usd,
            counters=self.counters,
        )
        self.bar_index = -1
        self.ledger: list[str] = []
        self.coverage_first_ms = 0
        self.coverage_last_ms = 0
        self._previous_bar_open_ts_ms: int | None = None

    # ------------------------------------------------------------------

    def on_bar(self, parent: ParentBar) -> BarOutput:
        """Process one completed 5m bar and its LTF sub-bars."""
        bar = parent.bar
        if bar.timeframe is not Timeframe.M5:
            raise ValueError("V53 consumes 5m parent bars")
        if bar.instrument != self.config.instrument:
            raise ValueError(
                f"bar instrument {bar.instrument!r} != configured "
                f"{self.config.instrument!r}"
            )
        if parent.ltf_timeframe is not self.config.ltf:
            raise ValueError(
                f"LTF {parent.ltf_timeframe.value} != configured {self.config.ltf.value}"
            )
        open_ts = bar.open_ts_ms
        if self._previous_bar_open_ts_ms is not None and open_ts <= self._previous_bar_open_ts_ms:
            raise ValueError(
                f"bar {open_ts} is out of order or duplicated; the engine never "
                f"absorbs it"
            )
        self._previous_bar_open_ts_ms = open_ts

        self.bar_index += 1
        high, low, close = to_float(bar.high), to_float(bar.low), to_float(bar.close)
        output = BarOutput(bar_open_ts_ms=open_ts, bar_index=self.bar_index,
                           ltf_count=parent.ltf_count)

        # ---- §1 OUTCOMES (first, so a fill on bar t is first judged on t+1) ----
        resolved = self.machine.section1_outcomes(high=high, low=low)
        for outcome in resolved:
            row = ledger_row(outcome, self.config.ticker, self.config.direction,
                             self.config.ltf.minutes, self.config.fold)
            self.ledger.append(row)
            output.ledger_rows.append(row)
        output.resolved = resolved

        # ---- §2 FILLS ----
        output.filled_slots = self.machine.section2_fills(high=high, low=low,
                                                          bar_open_ts_ms=open_ts)

        # ---- §3 DEADLINE ----
        self.machine.section3_deadline(self.bar_index)

        # ---- sweep engine: levels, ATR, and the sweep test for this bar ----
        sweep = self.sweeps.update(open_ts, high, low, close)
        atr = sweep.atr

        # ---- §4 LTF LOOP ----
        fold_ok = in_fold(self.config.fold, open_ts)
        output.in_fold = fold_ok
        n_ltf = parent.ltf_count
        if fold_ok:
            self.counters.bump(30)
            if n_ltf > 0:
                self.counters.bump(29)
                if self.coverage_first_ms == 0:
                    self.coverage_first_ms = open_ts
                self.coverage_last_ms = open_ts

        # nLive is snapshotted BEFORE the loop and never recomputed inside it.
        n_live = self.machine.count_live()

        if n_ltf > 0 and not is_na(atr) and atr > 0:
            for sub in parent.ltf_bars:
                entry = self.ltf.push(
                    high=to_float(sub.high), low=to_float(sub.low),
                    close=to_float(sub.close),
                    parent_bar_index=self.bar_index, ts_ms=sub.open_ts_ms,
                )
                self.counters.bump(31)
                self.ltf.confirm_pivots()          # §4a
                if n_live > 0:
                    self.machine.section4_advance(  # §4b
                        ltf=self.ltf, entry_ring=entry, atr=atr,
                        high_5m=high, low_5m=low,
                    )

        # ---- §5 ARM ----
        if fold_ok and sweep.n_hit > 0 and not is_na(atr) and atr > 0:
            output.armed_slot = self.machine.section5_arm(
                bar_index=self.bar_index, bar_open_ts_ms=open_ts,
                high=high, low=low, atr=atr, sweep_kind=sweep.kind,
            )
        return output

    # ------------------------------------------------------------------

    def funnel(self) -> dict[str, int]:
        """The §7 funnel table, by the artifact's own row names."""
        k = self.counters
        return {
            "fold_bars": k.fold_bars,
            "fold_bars_with_ltf": k.fold_bars_with_ltf,
            "ltf_bars_seen": k.ltf_bars_seen,
            "sweeps": k.sweeps,
            "choch": k.choch,
            "retests": k.retests,
            "bos_displacement": k.bos_displacement,
            "fvg": k.fvg,
            "fills": k.fills,
            "break_no_displacement": k.break_no_displacement,
            "no_fvg": k.no_fvg,
            "r_band_rejects": k.r_band_rejects,
            "fvg_retest_expiry": k.fvg_retest_expiry,
            "expire_pre_choch": k.expire_pre_choch,
            "expire_post_choch": k.expire_post_choch,
            "expire_post_retest": k.expire_post_retest,
            "dropped_no_slot": k.dropped_no_slot,
            "outcomes": k.outcomes,
        }

    def conservation_holds(self) -> bool:
        """`FVG = fills + R-band rejects + FVG retest expiry`."""
        k = self.counters
        return k.fvg == k.fills + k.r_band_rejects + k.fvg_retest_expiry

"""Strategy state contract — the shape of what V53 carries between bars.

Transcribed field-for-field from `V53_EXECUTED_BUILD.pine` §"SEQUENCE SLOTS",
§"LTF STREAM" and §"5m SWEEP ENGINE". Nothing is collapsed, renamed away or
dropped for looking redundant: `cBar`, `rBar` and `dBar` all hold LTF bar
indices and all three are load-bearing, and `mfe`/`mae` are strategy state even
though neither reaches the ledger.

**These are containers, not behaviour.** No method here advances a state,
detects an event or decides an outcome. B2 supplies the transitions; the
contract only says what may be stored and guarantees it serialises
deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import Decimal
from typing import Any

from bot.contracts.enums import Direction, SlotState, Timeframe, TransitionReason
from bot.guards import assert_pre_fe

#: V53 `SP` — the number of concurrent sequence slots.
SLOT_COUNT = 24

#: V53 `lSw` — LTF pivot half-width. `RB = 2 * lSw + 1` is the ring-buffer size.
LTF_PIVOT_HALF_WIDTH = 3
RING_BUFFER_SIZE = 2 * LTF_PIVOT_HALF_WIDTH + 1  # 7

#: V53 `swLen` — 5m swing pivot half-width.
SWING_PIVOT_HALF_WIDTH = 10

#: Index layout of V53's `pvV`/`pvI`/`pvB` pivot register.
PIVOT_LAST_HIGH, PIVOT_PREV_HIGH, PIVOT_LAST_LOW, PIVOT_PREV_LOW = 0, 1, 2, 3


class StateContractError(ValueError):
    """A state value that violates the contract's structure."""


@dataclass(frozen=True)
class LtfRingEntry:
    """One slot of V53's 7-bar LTF ring buffer (`bH`, `bL`, `bC`, `bCB`, `bIX`, `bTM`).

    Only high, low and close are retained: V53 pushes no open, and the FVG
    geometry in §4b reads highs and lows only.
    """

    high: Decimal          # bH
    low: Decimal           # bL
    close: Decimal         # bC
    parent_bar_index: int  # bCB — 5m bar_index the sub-bar arrived on
    ltf_index: int         # bIX — monotonic LTF counter (ltfN) at push
    ts_ms: int             # bTM — LTF bar time, see UNRESOLVED U2

    def __post_init__(self) -> None:
        assert_pre_fe(self.ts_ms, context=f"ltf ring entry {self.ltf_index}")
        if self.ltf_index < 1:
            raise StateContractError(f"ltf_index must be >= 1, got {self.ltf_index}")
        if self.parent_bar_index < 0:
            raise StateContractError(f"parent_bar_index must be >= 0, got {self.parent_bar_index}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "high": self.high, "low": self.low, "close": self.close,
            "parent_bar_index": self.parent_bar_index,
            "ltf_index": self.ltf_index, "ts_ms": self.ts_ms,
        }


@dataclass(frozen=True)
class PivotRecord:
    """One entry of the pivot register: value, LTF index, parent bar index.

    V53 keeps four — last and previous pivot high, last and previous pivot low —
    in parallel arrays `pvV`/`pvI`/`pvB`. An unset entry is value ``None`` with
    indices ``-1``, matching V53's `na` / `-1` initialisation.
    """

    value: Decimal | None = None
    ltf_index: int = -1      # pvI
    parent_bar_index: int = -1  # pvB

    @property
    def is_set(self) -> bool:
        return self.value is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "ltf_index": self.ltf_index,
            "parent_bar_index": self.parent_bar_index,
        }


@dataclass
class SweepEngineState:
    """V53 §"5m SWEEP ENGINE" — the levels a sweep is measured against.

    All are 5m-derived. `previous_day_*` roll on `ta.change(time("D"))`, which is
    the **exchange session day, not UTC midnight** — see UNRESOLVED U1. The Asia
    window is explicitly UTC (`hour(time, "UTC") < 7`).
    """

    previous_day_high: Decimal | None = None   # pdh
    previous_day_low: Decimal | None = None    # pdl
    day_high: Decimal | None = None            # dh
    day_low: Decimal | None = None             # dl
    asia_high: Decimal | None = None           # asiaH
    asia_low: Decimal | None = None            # asiaL
    asia_open: bool = False                    # asiaOn
    swing_high: Decimal | None = None          # swH — last confirmed pivot(10,10)
    swing_low: Decimal | None = None           # swL
    atr: Decimal | None = None                 # ta.atr(14) on 5m

    def to_dict(self) -> dict[str, Any]:
        return {
            "previous_day_high": self.previous_day_high,
            "previous_day_low": self.previous_day_low,
            "day_high": self.day_high, "day_low": self.day_low,
            "asia_high": self.asia_high, "asia_low": self.asia_low,
            "asia_open": self.asia_open,
            "swing_high": self.swing_high, "swing_low": self.swing_low,
            "atr": self.atr,
        }


@dataclass
class SequenceSlot:
    """One of V53's 24 sequence slots: every parallel array, one object.

    Strategy fields (drive behaviour) are listed first, then the ledger fields
    V53 marks "measurement only; no strategy state". The split is preserved
    because it decides what B3 may compare and what merely records.
    """

    index: int
    state: SlotState = SlotState.FREE

    # ---- strategy state ----
    sweep_bar_index: int = 0                # swB — 5m bar_index at arm
    stop: Decimal | None = None             # stp — sweep extreme ∓ bufATR × ATR
    atr_at_arm: Decimal | None = None       # aRf — R-band denominator
    choch_level: Decimal | None = None      # cLvl
    pivot_ref: Decimal | None = None        # pRef — last opposing pivot seen while ARMED
    choch_pivot_index: int = -1             # cPvI — BOS eligibility reference
    choch_ltf_index: int = -1               # cBar
    retest_ltf_index: int = -1              # rBar
    displacement_ltf_index: int = -1        # dBar
    entry: Decimal | None = None            # ent — FVG far edge
    r_distance: Decimal | None = None       # rr — |entry − stop|, set at fill
    fvg_wait_bars: int = 0                  # wt — 5m bars waited for the fill
    bars_in_trade: int = 0                  # bIn — 0 at fill; §1 judges from bIn+1
    max_favourable_r: Decimal = Decimal(0)  # mfe
    max_adverse_r: Decimal = Decimal(0)     # mae
    target_reached: int = 0                 # flg — 1 once favourable excursion >= tgtR

    # ---- ledger fields (measurement only; no strategy state) ----
    ledger_sweep_ts_ms: int = 0             # lSwT
    ledger_sweep_kind: str = ""             # lSwG — "PD", "AS+SW", …
    ledger_sweep_extreme: Decimal | None = None  # lSwX
    ledger_choch_ts_ms: int = 0             # lChT
    ledger_retest_ts_ms: int = 0            # lRtT
    ledger_bos_ts_ms: int = 0               # lBoT
    ledger_bos_level: Decimal | None = None      # lBoL
    ledger_fvg_low: Decimal | None = None        # lFlo
    ledger_fvg_high: Decimal | None = None       # lFhi
    ledger_entry_ts_ms: int = 0             # lEnT

    #: Fields V53 marks measurement-only. B3 compares them; nothing reads them.
    LEDGER_FIELDS = (
        "ledger_sweep_ts_ms", "ledger_sweep_kind", "ledger_sweep_extreme",
        "ledger_choch_ts_ms", "ledger_retest_ts_ms", "ledger_bos_ts_ms",
        "ledger_bos_level", "ledger_fvg_low", "ledger_fvg_high",
        "ledger_entry_ts_ms",
    )

    def __post_init__(self) -> None:
        if not 0 <= self.index < SLOT_COUNT:
            raise StateContractError(
                f"slot index {self.index} outside 0..{SLOT_COUNT - 1}"
            )
        if not isinstance(self.state, SlotState):
            raise StateContractError(f"state must be a SlotState, got {self.state!r}")
        for name in ("ledger_sweep_ts_ms", "ledger_choch_ts_ms", "ledger_retest_ts_ms",
                     "ledger_bos_ts_ms", "ledger_entry_ts_ms"):
            value = getattr(self, name)
            if value:  # 0 is V53's "unset"
                assert_pre_fe(value, context=f"slot {self.index} {name}")

    @property
    def is_free(self) -> bool:
        return self.state is SlotState.FREE

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index, "state": self.state,
            "sweep_bar_index": self.sweep_bar_index, "stop": self.stop,
            "atr_at_arm": self.atr_at_arm, "choch_level": self.choch_level,
            "pivot_ref": self.pivot_ref, "choch_pivot_index": self.choch_pivot_index,
            "choch_ltf_index": self.choch_ltf_index,
            "retest_ltf_index": self.retest_ltf_index,
            "displacement_ltf_index": self.displacement_ltf_index,
            "entry": self.entry, "r_distance": self.r_distance,
            "fvg_wait_bars": self.fvg_wait_bars, "bars_in_trade": self.bars_in_trade,
            "max_favourable_r": self.max_favourable_r,
            "max_adverse_r": self.max_adverse_r,
            "target_reached": self.target_reached,
            **{name: getattr(self, name) for name in self.LEDGER_FIELDS},
        }


@dataclass
class StrategyState:
    """Everything V53 carries from one 5m bar to the next.

    Pine recomputes this from bar 1 on every reload. A bot cannot, so this is
    the object C1/C2 must persist and rehydrate exactly — see the audit, R5.
    """

    instrument: str
    direction: Direction
    ltf: Timeframe
    strategy_sha256: str

    sweep_engine: SweepEngineState = field(default_factory=SweepEngineState)
    slots: tuple[SequenceSlot, ...] = ()
    #: `bH`/`bL`/`bC`/`bCB`/`bIX`/`bTM`, oldest first, at most RING_BUFFER_SIZE.
    ltf_ring: tuple[LtfRingEntry, ...] = ()
    #: `pvV`/`pvI`/`pvB`, indexed by PIVOT_LAST_HIGH … PIVOT_PREV_LOW.
    pivots: tuple[PivotRecord, ...] = ()
    ltf_bars_seen: int = 0        # ltfN — monotonic, never reset
    parent_bar_index: int = -1    # bar_index of the last 5m bar processed
    last_bar_close_ts_ms: int | None = None

    def __post_init__(self) -> None:
        if self.ltf not in (Timeframe.M1, Timeframe.M3):
            raise StateContractError(f"ltf must be 1m or 3m, got {self.ltf!r}")
        if not isinstance(self.direction, Direction):
            raise StateContractError(f"direction must be a Direction, got {self.direction!r}")
        if not self.slots:
            self.slots = tuple(SequenceSlot(index=i) for i in range(SLOT_COUNT))
        if len(self.slots) != SLOT_COUNT:
            raise StateContractError(f"expected {SLOT_COUNT} slots, got {len(self.slots)}")
        if [s.index for s in self.slots] != list(range(SLOT_COUNT)):
            raise StateContractError("slots must be ordered by index 0..23")
        if not self.pivots:
            self.pivots = tuple(PivotRecord() for _ in range(4))
        if len(self.pivots) != 4:
            raise StateContractError(f"pivot register must hold 4 entries, got {len(self.pivots)}")
        if len(self.ltf_ring) > RING_BUFFER_SIZE:
            raise StateContractError(
                f"ltf_ring holds {len(self.ltf_ring)}, max {RING_BUFFER_SIZE}"
            )
        if self.last_bar_close_ts_ms is not None:
            assert_pre_fe(self.last_bar_close_ts_ms, context=f"{self.instrument} state")

    @property
    def ring_full(self) -> bool:
        """Pivot confirmation is only possible once the ring holds RB entries."""
        return len(self.ltf_ring) == RING_BUFFER_SIZE

    def slot(self, index: int) -> SequenceSlot:
        return self.slots[index]

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "direction": self.direction,
            "ltf": self.ltf,
            "strategy_sha256": self.strategy_sha256,
            "sweep_engine": self.sweep_engine,
            "slots": list(self.slots),
            "ltf_ring": list(self.ltf_ring),
            "pivots": list(self.pivots),
            "ltf_bars_seen": self.ltf_bars_seen,
            "parent_bar_index": self.parent_bar_index,
            "last_bar_close_ts_ms": self.last_bar_close_ts_ms,
        }


@dataclass(frozen=True)
class SlotTransition:
    """A record that a slot changed state, and why.

    B2 emits one per change; C3 journals them. Purely descriptive — constructing
    one does not perform a transition.
    """

    slot_index: int
    from_state: SlotState
    to_state: SlotState
    reason: TransitionReason
    parent_bar_index: int
    bar_close_ts_ms: int
    ltf_index: int | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.slot_index < SLOT_COUNT:
            raise StateContractError(f"slot index {self.slot_index} outside 0..{SLOT_COUNT - 1}")
        assert_pre_fe(self.bar_close_ts_ms, context=f"transition slot {self.slot_index}")
        if self.reason.frees_slot and self.to_state is not SlotState.FREE:
            raise StateContractError(
                f"{self.reason.value} frees the slot but to_state is {self.to_state.name}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_index": self.slot_index,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "reason": self.reason,
            "parent_bar_index": self.parent_bar_index,
            "bar_close_ts_ms": self.bar_close_ts_ms,
            "ltf_index": self.ltf_index,
        }


__all__ = [
    "SLOT_COUNT", "RING_BUFFER_SIZE", "LTF_PIVOT_HALF_WIDTH", "SWING_PIVOT_HALF_WIDTH",
    "PIVOT_LAST_HIGH", "PIVOT_PREV_HIGH", "PIVOT_LAST_LOW", "PIVOT_PREV_LOW",
    "StateContractError", "LtfRingEntry", "PivotRecord", "SweepEngineState",
    "SequenceSlot", "StrategyState", "SlotTransition", "replace",
]

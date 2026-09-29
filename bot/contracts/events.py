"""Event and signal contract — what the strategy engine emits.

One type per stage of the frozen sequence, plus :class:`StrategySignal`, the
complete record of one sequence that reached a fill. Every field is either
recorded by V53 or is orientation/identity metadata; **no field encodes a rule**.

Deliberately not validated here, and this is a decision rather than an omission:
the contract does not check that ``target`` sits 5R from ``entry``, that
``r_atr_ratio`` falls inside V53's [0.05, 3.00] band, or that ``stop`` lies on a
particular side of ``entry``. Those are V53's rules. Encoding them would make
the schema a second, silent copy of the strategy that B3 could never catch
diverging — and the A2 fixtures contain two real fills whose stop sits on the
near side of entry, which such a check would wrongly reject.

The audit's §3.2 sketch proposed those validators. This supersedes it, for the
reason above.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from bot.contracts.enums import (
    SWEEP_SOURCE_ORDER, Direction, ExitReason, Outcome, SweepSource, Timeframe,
)
from bot.contracts.serialize import canonical
from bot.guards import assert_pre_fe

#: Bumped whenever a field is added, removed or re-typed.
SIGNAL_SCHEMA_VERSION = 1


class EventContractError(ValueError):
    """An event value that violates the contract's structure."""


def _require_ltf(ltf: Timeframe) -> Timeframe:
    if ltf not in (Timeframe.M1, Timeframe.M3):
        raise EventContractError(f"ltf must be 1m or 3m, got {ltf!r}")
    return ltf


@dataclass(frozen=True)
class SequenceRef:
    """Which sequence produced an event. Carried by every event and signal.

    ``slot_index`` is state provenance, not identity: V53 reuses slots, so two
    sequences months apart can share one. Identity comes from the event keys on
    :class:`StrategySignal`.

    ``slot_index`` is ``None`` when the slot is **not recorded** — V53's ledger
    never emits it, so every signal reconstructed from an A2 fixture has none.
    A live engine sets it. The contract represents the absence rather than
    inventing a value.
    """

    instrument: str
    direction: Direction
    ltf: Timeframe
    slot_index: int | None
    sweep_ts_ms: int

    def __post_init__(self) -> None:
        _require_ltf(self.ltf)
        if not isinstance(self.direction, Direction):
            raise EventContractError(f"direction must be a Direction, got {self.direction!r}")
        if self.slot_index is not None and not 0 <= self.slot_index < 24:
            raise EventContractError(f"slot_index {self.slot_index} outside 0..23")
        assert_pre_fe(self.sweep_ts_ms, context=f"{self.instrument} sequence ref")

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument, "direction": self.direction,
            "ltf": self.ltf, "slot_index": self.slot_index,
            "sweep_ts_ms": self.sweep_ts_ms,
        }


@dataclass(frozen=True)
class _StageEvent:
    """Shared shape: which sequence, and when the stage resolved.

    ``bar_close_ts_ms`` is the **5m close at which the stage became knowable** —
    the earliest a live system could act. ``ts_ms`` is the LTF bar's own
    timestamp, which V53 records in the ledger. They differ, and both matter.
    """

    ref: SequenceRef
    ts_ms: int
    bar_close_ts_ms: int

    def __post_init__(self) -> None:
        assert_pre_fe(self.ts_ms, context=f"{type(self).__name__} ts_ms")
        assert_pre_fe(self.bar_close_ts_ms, context=f"{type(self).__name__} bar_close_ts_ms")

    def _base(self) -> dict[str, Any]:
        return {"ref": self.ref, "ts_ms": self.ts_ms, "bar_close_ts_ms": self.bar_close_ts_ms}


@dataclass(frozen=True)
class SweepEvent(_StageEvent):
    """Stage 1 — a 5m bar took out a reference level and closed back inside."""

    sources: tuple[SweepSource, ...] = ()
    extreme: Decimal | None = None       # lSwX — the bar's low (long) / high (short)
    stop: Decimal | None = None          # stp — extreme ∓ bufATR × ATR
    atr_at_arm: Decimal | None = None    # aRf
    parent_bar_index: int = -1           # swB

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.sources:
            raise EventContractError("a sweep must name at least one source")
        seen = set()
        for source in self.sources:
            if not isinstance(source, SweepSource):
                raise EventContractError(f"bad sweep source {source!r}")
            if source in seen:
                raise EventContractError(f"duplicate sweep source {source.value}")
            seen.add(source)

    @property
    def kind(self) -> str:
        """V53's rendering: sources joined by '+' in PD, AS, SW order."""
        return "+".join(s.value for s in SWEEP_SOURCE_ORDER if s in self.sources)

    def to_dict(self) -> dict[str, Any]:
        return {**self._base(), "sources": list(self.sources), "kind": self.kind,
                "extreme": self.extreme, "stop": self.stop,
                "atr_at_arm": self.atr_at_arm, "parent_bar_index": self.parent_bar_index}


@dataclass(frozen=True)
class ChochEvent(_StageEvent):
    """Stage 2 — an LTF close broke the most recent eligible opposing pivot."""

    level: Decimal | None = None      # cLvl
    pivot_index: int = -1             # cPvI — BOS eligibility reference
    ltf_index: int = -1               # cBar

    def to_dict(self) -> dict[str, Any]:
        return {**self._base(), "level": self.level,
                "pivot_index": self.pivot_index, "ltf_index": self.ltf_index}


@dataclass(frozen=True)
class RetestEvent(_StageEvent):
    """Stage 3 — price returned to the CHOCH level exactly (zero tolerance)."""

    level: Decimal | None = None   # the CHOCH level; V53 stores no separate value
    ltf_index: int = -1            # rBar

    def to_dict(self) -> dict[str, Any]:
        return {**self._base(), "level": self.level, "ltf_index": self.ltf_index}


@dataclass(frozen=True)
class BosEvent(_StageEvent):
    """Stage 4 — a break of a pivot other than the CHOCH pivot, with displacement."""

    level: Decimal | None = None            # lBoL
    displacement_ltf_index: int = -1        # dBar
    bar_range: Decimal | None = None        # rng — the LTF bar's high − low

    def to_dict(self) -> dict[str, Any]:
        return {**self._base(), "level": self.level,
                "displacement_ltf_index": self.displacement_ltf_index,
                "bar_range": self.bar_range}


@dataclass(frozen=True)
class FvgEvent(_StageEvent):
    """Stage 5 — the gap tested at the single LTF bar after displacement.

    ``entry`` is the far edge, the level V53 waits at. ``low``/``high`` are the
    gap's bounds as recorded (`lFlo`/`lFhi`).
    """

    low: Decimal | None = None
    high: Decimal | None = None
    entry: Decimal | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.low is not None and self.high is not None and self.low > self.high:
            raise EventContractError(f"fvg low {self.low} above high {self.high}")

    def to_dict(self) -> dict[str, Any]:
        return {**self._base(), "low": self.low, "high": self.high, "entry": self.entry}


@dataclass(frozen=True)
class FillEvent(_StageEvent):
    """Stage 6 — a 5m bar touched the resting entry and the R band accepted it.

    ``r_distance`` is |entry − stop| and ``r_atr_ratio`` is r / ATR-at-arm. Both
    are recorded, neither is range-checked here: the band is a V53 rule.
    """

    entry: Decimal | None = None
    stop: Decimal | None = None
    r_distance: Decimal | None = None
    r_atr_ratio: Decimal | None = None

    def to_dict(self) -> dict[str, Any]:
        return {**self._base(), "entry": self.entry, "stop": self.stop,
                "r_distance": self.r_distance, "r_atr_ratio": self.r_atr_ratio}


@dataclass(frozen=True)
class OutcomeEvent(_StageEvent):
    """Stage 7 — the trade resolved.

    ``outcome`` follows V53: WIN only when the favourable excursion reached the
    target. A timeout is a LOSS even if it ended above entry.
    """

    outcome: Outcome | None = None
    exit_reason: ExitReason | None = None
    r_multiple: Decimal | None = None       # net of cost, as recorded
    r_multiple_gross: Decimal | None = None # vPre — +tgtR or −1 before cost
    pnl_usd: Decimal | None = None
    bars_in_trade: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.outcome is not None and not isinstance(self.outcome, Outcome):
            raise EventContractError(f"bad outcome {self.outcome!r}")
        if self.exit_reason is not None and not isinstance(self.exit_reason, ExitReason):
            raise EventContractError(f"bad exit_reason {self.exit_reason!r}")
        if self.bars_in_trade < 0:
            raise EventContractError(f"bars_in_trade must be >= 0, got {self.bars_in_trade}")

    def to_dict(self) -> dict[str, Any]:
        return {**self._base(), "outcome": self.outcome, "exit_reason": self.exit_reason,
                "r_multiple": self.r_multiple, "r_multiple_gross": self.r_multiple_gross,
                "pnl_usd": self.pnl_usd, "bars_in_trade": self.bars_in_trade}


@dataclass(frozen=True)
class StrategySignal:
    """One complete sequence that reached a fill — the strategy's output unit.

    Carries the whole provenance chain, so a consumer can reconstruct exactly
    which sequence produced it without consulting engine state. ``outcome`` is
    ``None`` while the trade is open and set once it resolves.
    """

    schema_version: int
    strategy_id: str
    strategy_sha256: str
    ref: SequenceRef
    sweep: SweepEvent
    choch: ChochEvent
    retest: RetestEvent
    bos: BosEvent
    fvg: FvgEvent
    fill: FillEvent
    outcome: OutcomeEvent | None = None
    fold: str | None = None   # research provenance only; live signals carry None

    def __post_init__(self) -> None:
        if self.schema_version != SIGNAL_SCHEMA_VERSION:
            raise EventContractError(
                f"schema_version {self.schema_version} != {SIGNAL_SCHEMA_VERSION}"
            )
        if not self.strategy_id:
            raise EventContractError("strategy_id is required")
        if len(self.strategy_sha256) != 64 or not all(
            c in "0123456789abcdef" for c in self.strategy_sha256
        ):
            raise EventContractError(
                f"strategy_sha256 must be 64 lowercase hex chars, got {self.strategy_sha256!r}"
            )
        for name in ("sweep", "choch", "retest", "bos", "fvg", "fill"):
            stage = getattr(self, name)
            if stage.ref != self.ref:
                raise EventContractError(f"{name} belongs to a different sequence")
        if self.outcome is not None and self.outcome.ref != self.ref:
            raise EventContractError("outcome belongs to a different sequence")

    # ---- identity ----

    @property
    def event_key_primary(self) -> str:
        """Phase 13G primary clustering identity. Analysis only, never an order key."""
        return "|".join(str(part) for part in (
            self.ref.instrument, self.ref.direction.value, self.ref.ltf.value,
            self.choch.ts_ms, self.choch.level, self.bos.ts_ms, self.bos.level,
            self.fill.ts_ms, self.fill.entry,
        ))

    @property
    def event_key_alternative(self) -> str:
        """Phase 13G alternative identity — the primary without the CHOCH pair."""
        return "|".join(str(part) for part in (
            self.ref.instrument, self.ref.direction.value, self.ref.ltf.value,
            self.bos.ts_ms, self.bos.level, self.fill.ts_ms, self.fill.entry,
        ))

    @property
    def signal_id(self) -> str:
        """Deterministic content hash. Reproducible, never random.

        Derived from the full serialised signal *excluding* the outcome, so the
        id is stable from fill through resolution.
        """
        body = dict(self.to_dict())
        body.pop("outcome", None)
        return hashlib.sha256(canonical(body).encode("utf-8")).hexdigest()[:32]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "strategy_id": self.strategy_id,
            "strategy_sha256": self.strategy_sha256,
            "ref": self.ref,
            "sweep": self.sweep, "choch": self.choch, "retest": self.retest,
            "bos": self.bos, "fvg": self.fvg, "fill": self.fill,
            "outcome": self.outcome,
            "fold": self.fold,
            "event_key_primary": self.event_key_primary,
            "event_key_alternative": self.event_key_alternative,
        }


__all__ = [
    "SIGNAL_SCHEMA_VERSION", "EventContractError", "SequenceRef", "SweepEvent",
    "ChochEvent", "RetestEvent", "BosEvent", "FvgEvent", "FillEvent",
    "OutcomeEvent", "StrategySignal",
]

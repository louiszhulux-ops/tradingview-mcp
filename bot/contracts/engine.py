"""The strategy output boundary.

    bars in  →  StrategyEngine  →  events and signals out

Nothing else. The engine knows nothing about accounts, brokers, orders,
positions, money, risk, or whether a signal will be traded. B2 implements this
protocol; B3 drives it over fixture bars and compares its output to the A2
golden fixtures.

**Not connected to anything.** No broker, OMS, risk engine, paper broker,
TradingView, or live feed is imported here, and none may be: an engine that can
reach an execution venue is no longer a pure function of its bars.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence, runtime_checkable

from bot.contracts.events import StrategySignal
from bot.contracts.state import SlotTransition, StrategyState
from bot.data.bars import ParentBar


@dataclass(frozen=True)
class BarResult:
    """Everything one 5m bar close produced.

    Ordering within each tuple is significant and must be reproducible: it is
    the order V53's loops would have produced, and B3 compares it directly.
    """

    bar_close_ts_ms: int
    transitions: tuple[SlotTransition, ...] = ()
    signals: tuple[StrategySignal, ...] = ()
    resolved: tuple[StrategySignal, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "bar_close_ts_ms": self.bar_close_ts_ms,
            "transitions": list(self.transitions),
            "signals": list(self.signals),
            "resolved": list(self.resolved),
        }


@runtime_checkable
class StrategyEngine(Protocol):
    """The contract B2 must satisfy.

    Implementations must be **pure with respect to their inputs**: no wall-clock
    read, no randomness, no I/O in the decision path. Feeding the same bars to a
    fresh engine twice must produce identical :class:`BarResult` sequences.
    """

    @property
    def state(self) -> StrategyState:
        """The current carried state. Serialisable, and the unit C1 persists."""

    def on_bar(self, parent: ParentBar) -> BarResult:
        """Process one completed 5m bar and its LTF sub-bars.

        Called once per closed 5m bar, in strict chronological order. The engine
        must reject a bar that is out of order, duplicated, or incomplete rather
        than absorbing it.
        """

    def snapshot(self) -> dict[str, Any]:
        """A deterministic, serialisable copy of the full carried state."""

    @classmethod
    def rehydrate(cls, snapshot: dict[str, Any]) -> "StrategyEngine":
        """Rebuild an engine from :meth:`snapshot`.

        Rehydrating and continuing must yield exactly what an uninterrupted run
        would have produced — the property C2 has to prove.
        """


@dataclass
class ReplayResult:
    """The output of driving an engine over a bar series. What B3 compares."""

    instrument: str
    direction: str
    ltf: str
    strategy_sha256: str
    bars_processed: int = 0
    results: list[BarResult] = field(default_factory=list)

    @property
    def signals(self) -> Sequence[StrategySignal]:
        return [s for r in self.results for s in r.signals]

    @property
    def resolved(self) -> Sequence[StrategySignal]:
        return [s for r in self.results for s in r.resolved]

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument, "direction": self.direction,
            "ltf": self.ltf, "strategy_sha256": self.strategy_sha256,
            "bars_processed": self.bars_processed,
            "results": list(self.results),
        }


__all__ = ["BarResult", "StrategyEngine", "ReplayResult"]

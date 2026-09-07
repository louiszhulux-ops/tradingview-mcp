"""Market-data contract.

V53 consumes two streams and treats them differently:

* a **5m stream**, on which every decision resolves and on which the sweep
  engine, ATR(14), the §1 outcome loop, the §2 fill loop and the §3 deadline all
  run;
* a **1m or 3m stream**, delivered by `request.security_lower_tf` as the set of
  sub-bars contained in the just-closed 5m bar.

The LTF stream is an *intrabar reconstruction performed at the parent close*, not
an independent decision stream, so :class:`ParentBar` nests its sub-bars rather
than modelling them as a separate series. **An LTF stream cannot substitute for
the 5m stream**: the sweep engine, ATR, the fill test and both bar-count
deadlines are defined on 5m bars, and no combination of 1m bars reproduces them.

Every timestamp entering this module passes the A1 pre-FE guard.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Sequence

from bot.contracts.enums import LTF_CHOICES, Timeframe
from bot.guards import assert_pre_fe


class BarContractError(ValueError):
    """A bar that cannot be trusted. Bars are rejected, never repaired."""


def _price(value: Any, name: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, str):
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise BarContractError(f"{name} is not a decimal: {value!r}") from exc
    raise BarContractError(
        f"{name} must be Decimal or an exact decimal string, got "
        f"{type(value).__name__} {value!r}; float loses price precision"
    )


@dataclass(frozen=True)
class Bar:
    """One completed bar. Immutable, exact, and self-validating.

    Validation here is data integrity only — that the OHLC bracket is coherent
    and the timestamps are usable. It encodes no trading rule.
    """

    instrument: str
    timeframe: Timeframe
    open_ts_ms: int
    close_ts_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None = None
    complete: bool = True

    def __post_init__(self) -> None:
        if not self.instrument or not isinstance(self.instrument, str):
            raise BarContractError(f"instrument must be a non-empty string, got {self.instrument!r}")
        if not isinstance(self.timeframe, Timeframe):
            raise BarContractError(f"timeframe must be a Timeframe, got {self.timeframe!r}")

        # Fail closed on timestamps: the guard rejects missing, malformed and
        # held-out values alike.
        assert_pre_fe(self.open_ts_ms, context=f"{self.instrument} {self.timeframe.value} open_ts_ms")
        assert_pre_fe(self.close_ts_ms, context=f"{self.instrument} {self.timeframe.value} close_ts_ms")

        expected = self.timeframe.minutes * 60_000
        if self.close_ts_ms - self.open_ts_ms != expected:
            raise BarContractError(
                f"{self.instrument} {self.timeframe.value} bar spans "
                f"{self.close_ts_ms - self.open_ts_ms} ms, expected {expected}"
            )
        if self.open_ts_ms % 60_000:
            raise BarContractError(f"open_ts_ms {self.open_ts_ms} is not on a minute boundary")

        for name in ("open", "high", "low", "close"):
            object.__setattr__(self, name, _price(getattr(self, name), name))
        if self.volume is not None:
            object.__setattr__(self, "volume", _price(self.volume, "volume"))
            if self.volume < 0:
                raise BarContractError(f"negative volume {self.volume}")

        if self.low > self.high:
            raise BarContractError(f"low {self.low} above high {self.high}")
        for name in ("open", "close"):
            value = getattr(self, name)
            if not (self.low <= value <= self.high):
                raise BarContractError(f"{name} {value} outside [{self.low}, {self.high}]")

        if not isinstance(self.complete, bool):
            raise BarContractError("complete must be a bool")

    @property
    def range(self) -> Decimal:
        """high − low. Arithmetic on recorded fields, not a strategy decision."""
        return self.high - self.low

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "timeframe": self.timeframe,
            "open_ts_ms": self.open_ts_ms,
            "close_ts_ms": self.close_ts_ms,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "complete": self.complete,
        }


@dataclass(frozen=True)
class ParentBar:
    """A closed 5m bar together with the LTF sub-bars it contains.

    This is the unit B2 consumes: exactly what a live 5m bar close makes
    knowable. `ltf_bars` is ordered oldest-first, matching the arrays
    `request.security_lower_tf` returns.

    A short or empty `ltf_bars` is **represented, not repaired**. V53 silently
    receives a shorter array and counts `fold bars w/ LTF` against `fold bars`;
    the contract exposes the same fact through :attr:`ltf_complete` so a bot can
    act on it instead of never seeing it.
    """

    bar: Bar
    ltf_timeframe: Timeframe
    ltf_bars: tuple[Bar, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.bar.timeframe is not Timeframe.M5:
            raise BarContractError(
                f"parent bar must be 5m, got {self.bar.timeframe.value}; an LTF "
                f"stream cannot substitute for the 5m stream"
            )
        if self.ltf_timeframe not in LTF_CHOICES:
            raise BarContractError(
                f"ltf_timeframe must be one of "
                f"{[t.value for t in LTF_CHOICES]}, got {self.ltf_timeframe!r}"
            )
        object.__setattr__(self, "ltf_bars", tuple(self.ltf_bars))

        previous_close: int | None = None
        for index, sub in enumerate(self.ltf_bars):
            where = f"{self.bar.instrument} 5m@{self.bar.open_ts_ms} ltf[{index}]"
            if not isinstance(sub, Bar):
                raise BarContractError(f"{where} is not a Bar")
            if sub.timeframe is not self.ltf_timeframe:
                raise BarContractError(
                    f"{where} is {sub.timeframe.value}, expected {self.ltf_timeframe.value}"
                )
            if sub.instrument != self.bar.instrument:
                raise BarContractError(f"{where} instrument {sub.instrument!r} != parent")
            if not (self.bar.open_ts_ms <= sub.open_ts_ms < self.bar.close_ts_ms):
                raise BarContractError(f"{where} starts outside its parent 5m bar")
            if sub.close_ts_ms > self.bar.close_ts_ms:
                raise BarContractError(f"{where} ends after its parent 5m bar")
            if previous_close is not None and sub.open_ts_ms != previous_close:
                raise BarContractError(f"{where} is out of order or leaves a gap")
            previous_close = sub.close_ts_ms

    @property
    def expected_ltf_count(self) -> int:
        """Sub-bars needed to tile the parent. Meaningful for 1m only; see U3."""
        return 5 // self.ltf_timeframe.minutes

    @property
    def ltf_count(self) -> int:
        return len(self.ltf_bars)

    @property
    def ltf_complete(self) -> bool:
        """Whether the LTF array covers the parent bar without a gap.

        For 1m this is 5 sub-bars. **For 3m it is not defined**: 3 does not
        divide 5, so a 3m sub-bar does not tile a 5m parent and the count varies.
        See bot/contracts/UNRESOLVED.md U3 — B2 must resolve this against real
        data, so the contract reports ``False`` for 3m rather than asserting a
        count it cannot justify.
        """
        if self.ltf_timeframe is not Timeframe.M1:
            return False
        return self.ltf_count == self.expected_ltf_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "bar": self.bar,
            "ltf_timeframe": self.ltf_timeframe,
            "ltf_bars": list(self.ltf_bars),
            "ltf_count": self.ltf_count,
        }


def validate_series(bars: Iterable[Bar]) -> tuple[Bar, ...]:
    """Check a series for duplicates, disorder and overlap. Never repairs.

    A trading session has real gaps (weekends, holidays, halts), so this asserts
    strict ordering and no duplicate or overlapping timestamps — it does **not**
    assert a contiguous grid, which would reject legitimate session breaks.
    """
    series: Sequence[Bar] = tuple(bars)
    for index in range(1, len(series)):
        previous, current = series[index - 1], series[index]
        if current.instrument != previous.instrument:
            raise BarContractError(f"series mixes instruments at index {index}")
        if current.timeframe is not previous.timeframe:
            raise BarContractError(f"series mixes timeframes at index {index}")
        if current.open_ts_ms == previous.open_ts_ms:
            raise BarContractError(f"duplicate bar timestamp {current.open_ts_ms} at index {index}")
        if current.open_ts_ms < previous.open_ts_ms:
            raise BarContractError(f"out-of-order bar at index {index}")
        if current.open_ts_ms < previous.close_ts_ms:
            raise BarContractError(f"overlapping bars at index {index}")
    return tuple(series)

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

**Optional fields (B1 amendment 2026-09-13, roadmap A7/A9).** `open` and
`volume` are optional, because the surviving frozen datasets do not carry them
and V53 does not consume them: `open` appears exactly once in
`trader_v2/V53_ltf_sequence.pine` — line 99, the `request.security_lower_tf`
request — and is never referenced again; `volume` appears zero times. An absent
field is represented as ``None`` and is **never** defaulted, zero-filled,
back-filled, interpolated or synthesised. ``None`` does not mean zero; it means
the source never recorded the value. Any component that needs the value must ask
for it through :meth:`Bar.require`, which raises :class:`AbsentFieldError` —
reading the attribute directly is for serialisation and presence checks only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Sequence

from bot.contracts.enums import LTF_CHOICES, Timeframe
from bot.guards import FE_MS, HeldOutDataError, assert_pre_fe


class BarContractError(ValueError):
    """A bar that cannot be trusted. Bars are rejected, never repaired."""


class AbsentFieldError(BarContractError):
    """A field the source never recorded was required by a caller.

    Raised instead of returning a default. The surviving datasets carry no
    `open` and no `volume`; a caller that needs either is asking for data that
    does not exist, and the only honest answer is to fail loudly.
    """


#: Fields that may legitimately be absent from a source dataset.
OPTIONAL_FIELDS: tuple[str, ...] = ("open", "volume")


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


def _optional_price(value: Any, name: str) -> Decimal | None:
    """`None` passes through untouched. Everything else is validated exactly.

    Absence is preserved, never converted into a number.
    """
    if value is None:
        return None
    return _price(value, name)


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
    open: Decimal | None
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

        # Fail closed on the open instant: the guard rejects missing, malformed
        # and held-out values alike.
        assert_pre_fe(self.open_ts_ms, context=f"{self.instrument} {self.timeframe.value} open_ts_ms")
        # `close_ts_ms` is the bar's EXCLUSIVE end. A bar that opens before FE
        # and ends exactly at FE holds only pre-FE data: FE is an exclusive
        # boundary (`time < FE`) and the span [open, close) lies wholly before
        # it. The final bar of every Phase C series is precisely this bar —
        # 5m opening 23:55 and 1m opening 23:59 on 2026-08-30 — so guarding the
        # close with `< FE` would discard real in-window data, while `> FE`
        # still admits nothing from the held-out window.
        if not isinstance(self.close_ts_ms, int) or isinstance(self.close_ts_ms, bool):
            raise BarContractError(
                f"close_ts_ms must be an int, got "
                f"{type(self.close_ts_ms).__name__} {self.close_ts_ms!r}")
        if self.close_ts_ms > FE_MS:
            raise HeldOutDataError(
                f"forward-held-out data refused [{self.instrument} "
                f"{self.timeframe.value} close_ts_ms]: {self.close_ts_ms} ends after "
                f"the Phase 16 boundary FE = {FE_MS}; a bar may close exactly at FE "
                f"but never beyond it")

        expected = self.timeframe.minutes * 60_000
        if self.close_ts_ms - self.open_ts_ms != expected:
            raise BarContractError(
                f"{self.instrument} {self.timeframe.value} bar spans "
                f"{self.close_ts_ms - self.open_ts_ms} ms, expected {expected}"
            )
        if self.open_ts_ms % 60_000:
            raise BarContractError(f"open_ts_ms {self.open_ts_ms} is not on a minute boundary")

        # high/low/close are always required: V53 consumes all three on both
        # the parent and the LTF stream. `open` is optional — see the module
        # docstring — and `None` is preserved rather than replaced.
        for name in ("high", "low", "close"):
            object.__setattr__(self, name, _price(getattr(self, name), name))
        object.__setattr__(self, "open", _optional_price(self.open, "open"))
        object.__setattr__(self, "volume", _optional_price(self.volume, "volume"))
        if self.volume is not None and self.volume < 0:
            raise BarContractError(f"negative volume {self.volume}")

        if self.low > self.high:
            raise BarContractError(f"low {self.low} above high {self.high}")
        # Bracket validation is unchanged for every field that is present. An
        # absent field is not checked, because there is nothing to check — it is
        # never treated as though it held some permissible value.
        for name in ("open", "close"):
            value = getattr(self, name)
            if value is None:
                continue
            if not (self.low <= value <= self.high):
                raise BarContractError(f"{name} {value} outside [{self.low}, {self.high}]")

        if not isinstance(self.complete, bool):
            raise BarContractError("complete must be a bool")

    @property
    def range(self) -> Decimal:
        """high − low. Arithmetic on recorded fields, not a strategy decision."""
        return self.high - self.low

    @property
    def has_open(self) -> bool:
        """Whether the source recorded an opening price for this bar."""
        return self.open is not None

    @property
    def has_volume(self) -> bool:
        """Whether the source recorded a volume for this bar."""
        return self.volume is not None

    def require(self, name: str) -> Decimal:
        """Return an optional field's value, or raise if the source lacks it.

        This is the only sanctioned way for a component to *use* `open` or
        `volume`. It exists so that a missing value surfaces as an explicit,
        named failure at the point of use, rather than as a `None` that flows
        onward and is silently coerced somewhere downstream.
        """
        if name not in OPTIONAL_FIELDS:
            raise BarContractError(
                f"require() covers the optional fields {OPTIONAL_FIELDS}, not {name!r}"
            )
        value = getattr(self, name)
        if value is None:
            raise AbsentFieldError(
                f"{self.instrument} {self.timeframe.value} bar at "
                f"{self.open_ts_ms}: {name} is absent from the source dataset. "
                f"It was never recorded and must not be defaulted, back-filled "
                f"or interpolated."
            )
        return value

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
    act on it instead of never seeing it. The same applies to an *interior* gap:
    a minute in which nothing traded is absent from the LTF array, and the
    sub-bars are required to be ordered and non-overlapping rather than
    contiguous.

    A sub-bar may also *begin before its parent opens*: a 3m bar straddling a 5m
    boundary is attributed forward, to the parent it ends in. Membership is
    therefore overlap-based and bounded — at most one LTF period early, never
    ending after the parent closes.
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
            # A sub-bar may begin BEFORE its parent opens. 3 does not divide 5,
            # so a 3m bar can straddle a 5m boundary, and TradingView attributes
            # such a bar FORWARD — to the parent it ends in, not the one it
            # starts in. Measured over both Phase C 3m candidates: 11,912 of
            # 29,780 bars (40.0%) start before their recorded parent, and NONE
            # ends after it. Requiring `parent.open <= sub.open` would reject
            # the attribution the artifact actually received.
            #
            # The contract is therefore: the sub-bar must genuinely overlap its
            # parent, may start at most one LTF period early, and must still end
            # no later than the parent closes. That admits the real straddler
            # and nothing else — it is not arbitrary cross-parent membership.
            period = self.ltf_timeframe.minutes * 60_000
            if sub.close_ts_ms > self.bar.close_ts_ms:
                raise BarContractError(f"{where} ends after its parent 5m bar")
            if sub.open_ts_ms >= self.bar.close_ts_ms or sub.close_ts_ms <= self.bar.open_ts_ms:
                raise BarContractError(f"{where} does not overlap its parent 5m bar")
            if sub.open_ts_ms < self.bar.open_ts_ms - period:
                raise BarContractError(
                    f"{where} starts more than one {self.ltf_timeframe.value} "
                    f"period before its parent 5m bar"
                )
            # Strictly increasing and non-overlapping — deliberately NOT a
            # contiguous grid. A tradeless minute is simply absent from what
            # `request.security_lower_tf` returns, so an interior gap is a real
            # recorded market condition (three MGC parents in the Phase C data
            # have one), and V53 consumes the short array without noticing.
            # This matches `validate_series`, which rejects disorder, duplicates
            # and overlap while allowing genuine session gaps. Asserting
            # contiguity here would reject real data and repair nothing.
            if previous_close is not None and sub.open_ts_ms < previous_close:
                raise BarContractError(f"{where} is out of order or overlaps its predecessor")
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

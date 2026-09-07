"""Phase 16 held-out-data guard.

This module holds the **single authoritative definition** of the Phase 16
out-of-sample boundary, ``FE``. No other module in ``bot/`` may define or
hard-code it; ``bot/tools/check_guards.py`` enforces that statically.

Phase 16 is a pre-registered out-of-sample validation running from
``FE`` (2026-08-31 00:00 UTC) to 2027-04-02 00:00 UTC. Its protocol forbids
inspecting outcomes in that window before the boundary date. Bot development
runs in parallel and must not touch it: a development test, fixture, backtest
or debugging session that reads a bar at or after ``FE`` consumes the held-out
data and invalidates the study.

The guard therefore **fails closed**. It accepts a timestamp only when that
timestamp is provably a valid, pre-``FE`` epoch-millisecond integer. Anything
else — ``None``, a float, a string, a bool, a non-positive value — is rejected
rather than coerced, because a timestamp that cannot be checked cannot be
shown to be safe.
"""

from __future__ import annotations

from typing import Any, Final, Iterable

# ---------------------------------------------------------------------------
# The authoritative Phase 16 boundary. Defined here and nowhere else.
# ---------------------------------------------------------------------------

#: Phase 16 out-of-sample boundary, epoch milliseconds UTC.
#: Matches ``FE`` in trader_v2/p15/executed/V53_EXECUTED_BUILD.pine.
FE_MS: Final[int] = 1788134400000

#: Human-readable form of :data:`FE_MS`, for error messages only.
FE_ISO: Final[str] = "2026-08-31T00:00:00Z"

#: Date at which the Phase 16 protocol permits the held-out window to be read.
PHASE16_BOUNDARY_ISO: Final[str] = "2027-04-02T00:00:00Z"


class HeldOutDataError(RuntimeError):
    """Raised when development code touches, or might touch, Phase 16 data.

    Catching this and continuing is a protocol violation. It is raised only
    where the correct response is to stop.
    """


class InvalidTimestampError(HeldOutDataError):
    """Raised when a timestamp cannot be validated at all.

    A subclass of :class:`HeldOutDataError` so that a single ``except`` clause
    fails closed on both "this is held-out data" and "this might be held-out
    data and I cannot tell".
    """


def assert_pre_fe(ts_ms: Any, *, context: str = "") -> int:
    """Assert that ``ts_ms`` is a valid epoch-ms timestamp strictly before FE.

    Returns the timestamp unchanged so the call can be inlined. Raises
    :class:`InvalidTimestampError` if the value is missing or malformed, and
    :class:`HeldOutDataError` if it falls in the Phase 16 held-out window.
    """
    where = f" [{context}]" if context else ""

    if ts_ms is None:
        raise InvalidTimestampError(
            f"missing timestamp{where}: cannot prove this data is pre-FE, "
            f"so it is refused. The Phase 16 held-out window begins at "
            f"{FE_ISO} ({FE_MS} ms) and is forbidden to development code "
            f"until {PHASE16_BOUNDARY_ISO}."
        )

    # bool is a subclass of int; True would otherwise pass as timestamp 1.
    if isinstance(ts_ms, bool) or not isinstance(ts_ms, int):
        raise InvalidTimestampError(
            f"malformed timestamp{where}: expected epoch milliseconds as int, "
            f"got {type(ts_ms).__name__} {ts_ms!r}. Values are not coerced — "
            f"a timestamp that cannot be checked cannot be shown to be "
            f"pre-FE ({FE_ISO}), so it is refused."
        )

    if ts_ms <= 0:
        raise InvalidTimestampError(
            f"invalid timestamp{where}: {ts_ms} is not a positive epoch-ms "
            f"value, so it cannot be shown to be pre-FE ({FE_ISO})."
        )

    if ts_ms >= FE_MS:
        raise HeldOutDataError(
            f"forward-held-out data refused{where}: timestamp {ts_ms} is at or "
            f"after the Phase 16 boundary FE = {FE_MS} ({FE_ISO}). "
            f"Data from that window is reserved for the pre-registered "
            f"out-of-sample validation and must not be read, tested against, "
            f"backtested, debugged with, or otherwise consumed by development "
            f"code before {PHASE16_BOUNDARY_ISO}. Use committed pre-FE "
            f"fixtures instead."
        )

    return ts_ms


def assert_all_pre_fe(ts_values: Iterable[Any], *, context: str = "") -> int:
    """Apply :func:`assert_pre_fe` to every value; return the count checked.

    Rejects a non-iterable input rather than treating it as empty, so that a
    loader handed the wrong type fails closed instead of vacuously passing.
    """
    try:
        iterator = iter(ts_values)
    except TypeError as exc:
        raise InvalidTimestampError(
            f"not iterable{f' [{context}]' if context else ''}: "
            f"{type(ts_values).__name__}; refusing to treat it as an empty "
            f"series, which would pass the pre-FE check vacuously."
        ) from exc

    count = 0
    for index, value in enumerate(iterator):
        assert_pre_fe(value, context=f"{context}[{index}]" if context else f"[{index}]")
        count += 1
    return count

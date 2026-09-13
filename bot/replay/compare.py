"""The Gate 1 comparator.

Zero tolerance. Exact `Decimal` equality on prices. No "close enough" mode, and
no parameter that could introduce one. A comparator that has never failed on
purpose is not evidence, so `bot/tests/test_gate1_compare.py` proves each
failure mode independently before this is ever pointed at real data.

**Not pointed at V53 data.** This module compares two structures; it does not
load bars, run the engine, or decide that anything passed.

What is compared, and what is deliberately not:

* **behaviour counters** — the fourteen that measure the strategy. Compared.
* **coverage counters** — `fold_bars`, `fold_bars_with_ltf`. Not compared here;
  they are an input precondition, checked by `bot.replay.coverage` before the
  engine runs.
* **`ltf_bars` (K31)** — counted chart-wide rather than in-fold, and null in most
  fixtures. Informational, never a parity counter.
* **ledger fields** — the eighteen V53 actually emitted.
* **`target_price`, `MFE`, `MAE`** — computed by the engine, reported as
  `DERIVED — NO GOLDEN COMPARAND`, never compared. V53 maintains MFE/MAE
  internally (`V53_ltf_sequence.pine:140-141, 199-208`) and emits neither, and
  emits no target price. There is no historical comparand and none may be
  manufactured.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Final, Mapping, Sequence

#: The fourteen counters that measure V53's behaviour. Zero tolerance.
BEHAVIOUR_COUNTERS: Final[tuple[str, ...]] = (
    "sweeps", "choch", "retests", "bos_displacement", "break_no_displacement",
    "fvg", "no_fvg", "fills", "r_band_rejects", "fvg_retest_expiry",
    "expire_pre_choch", "expire_post_choch", "expire_post_retest",
    "dropped_no_slot",
)

#: Input preconditions, not parity counters. See `bot.replay.coverage`.
COVERAGE_COUNTERS: Final[tuple[str, ...]] = ("fold_bars", "fold_bars_with_ltf")

#: Chart-wide, not fold-scoped, nullable. Reported, never compared.
EXCLUDED_COUNTERS: Final[tuple[str, ...]] = ("ltf_bars",)

#: The ledger fields V53 emitted, in comparison order.
LEDGER_FIELDS: Final[tuple[str, ...]] = (
    "sweep_ts", "sweep_kind", "sweep_extreme",
    "choch_ts", "choch_level",
    "retest_ts",
    "bos_ts", "bos_level",
    "fvg_low", "fvg_high",
    "entry_ts", "entry_price", "stop_price",
    "outcome", "r_multiple", "pnl_usd", "exit_reason", "bars_in_trade",
)

#: Compared as exact `Decimal`. Never as float.
PRICE_FIELDS: Final[frozenset[str]] = frozenset({
    "sweep_extreme", "choch_level", "bos_level", "fvg_low", "fvg_high",
    "entry_price", "stop_price", "r_multiple", "pnl_usd",
})

#: Computed and reported, never compared. No historical comparand exists.
DERIVED_NO_COMPARAND: Final[tuple[str, ...]] = ("target_price", "mfe", "mae")
DERIVED_LABEL: Final[str] = "DERIVED — NO GOLDEN COMPARAND"

#: Assertion counters that must read 0. Non-zero is a failure.
ASSERTIONS_MUST_BE_ZERO: Final[tuple[int, ...]] = (21, 22, 23, 24, 25, 32)

#: K26/K27 cross-check V53's hand-rolled pivot against Pine's `ta.pivothigh` /
#: `ta.pivotlow`. Python has no built-in comparand, so the check has no analogue
#: and is reported NOT APPLICABLE — never as a passing zero.
ASSERTIONS_NOT_APPLICABLE: Final[tuple[int, ...]] = (26, 27)
NOT_APPLICABLE_LABEL: Final[str] = "NOT APPLICABLE"


class ComparatorError(ValueError):
    """The comparator was handed something it must not silently accept."""


def _exact(value: Any, where: str) -> Decimal:
    """Coerce to `Decimal` exactly, refusing float outright."""
    if isinstance(value, bool) or isinstance(value, float):
        raise ComparatorError(
            f"{where}: {value!r} is a {type(value).__name__}; prices compare as "
            f"exact Decimal and float would silently introduce tolerance"
        )
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, str)):
        return Decimal(str(value))
    raise ComparatorError(f"{where}: cannot compare {type(value).__name__} {value!r} as a price")


@dataclass(frozen=True)
class Divergence:
    """One difference. The comparator reports every one it finds, in order."""

    kind: str           # counter | assertion | ledger_field | extra_row | missing_row
    where: str
    expected: Any
    actual: Any
    row_index: int | None = None

    def describe(self) -> str:
        if self.kind == "extra_row":
            return f"ledger row {self.row_index}: extra row produced by the engine, not in the golden ledger"
        if self.kind == "missing_row":
            return f"ledger row {self.row_index}: golden row missing from the engine ledger"
        return f"{self.where}: expected {self.expected!r}, got {self.actual!r}"


@dataclass(frozen=True)
class ComparisonResult:
    """The comparison. `first` is the first divergent point, in scan order."""

    cell_id: str
    divergences: tuple[Divergence, ...]
    mode: str = "full"          # "full" or "counters_only"
    not_applicable: tuple[str, ...] = ()
    derived: Mapping[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return not self.divergences

    @property
    def first(self) -> Divergence | None:
        return self.divergences[0] if self.divergences else None

    def report_lines(self) -> tuple[str, ...]:
        lines = [f"cell {self.cell_id}  mode={self.mode}  "
                 f"{'no divergence' if self.ok else f'{len(self.divergences)} divergence(s)'}"]
        if self.first is not None:
            lines.append(f"  FIRST DIVERGENCE  {self.first.describe()}")
        for div in self.divergences[1:]:
            lines.append(f"  also              {div.describe()}")
        for name in self.not_applicable:
            lines.append(f"  {name}: {NOT_APPLICABLE_LABEL}")
        for name in DERIVED_NO_COMPARAND:
            value = (self.derived or {}).get(name, "—")
            lines.append(f"  {name}: {value}  [{DERIVED_LABEL}]")
        return tuple(lines)


def compare_counters(
    expected: Mapping[str, Any], actual: Mapping[str, Any]
) -> list[Divergence]:
    """Compare the fourteen behaviour counters, in declared order."""
    out: list[Divergence] = []
    for name in BEHAVIOUR_COUNTERS:
        if name not in expected:
            raise ComparatorError(f"golden funnel is missing behaviour counter {name!r}")
        if name not in actual:
            raise ComparatorError(f"engine funnel is missing behaviour counter {name!r}")
        if expected[name] != actual[name]:
            out.append(Divergence("counter", f"funnel.{name}", expected[name], actual[name]))
    return out


def compare_assertions(actual: Mapping[int, int]) -> list[Divergence]:
    """K21–K25 and K32 must read 0. K26/K27 are not applicable, not passing."""
    out: list[Divergence] = []
    for index in ASSERTIONS_MUST_BE_ZERO:
        if index not in actual:
            raise ComparatorError(f"engine did not report assertion counter K{index}")
        if actual[index] != 0:
            out.append(Divergence("assertion", f"K{index}", 0, actual[index]))
    return out


def compare_ledger_row(
    index: int, expected: Mapping[str, Any], actual: Mapping[str, Any]
) -> list[Divergence]:
    """Compare one row across the eighteen emitted fields, in order."""
    out: list[Divergence] = []
    for name in LEDGER_FIELDS:
        if name not in expected or name not in actual:
            missing = "golden" if name not in expected else "engine"
            raise ComparatorError(f"ledger row {index}: {missing} row lacks field {name!r}")
        left, right = expected[name], actual[name]
        if name in PRICE_FIELDS:
            where = f"ledger[{index}].{name}"
            left, right = _exact(left, f"{where} (golden)"), _exact(right, f"{where} (engine)")
        if left != right:
            out.append(Divergence("ledger_field", f"ledger[{index}].{name}",
                                  expected[name], actual[name], row_index=index))
    return out


def compare_ledger(
    expected: Sequence[Mapping[str, Any]], actual: Sequence[Mapping[str, Any]]
) -> list[Divergence]:
    """Row-for-row, in order. A missing row and an extra row each diverge.

    Rows are compared pairwise from the top, so the first divergence is reported
    at the earliest row that differs rather than at the end of the ledger.
    """
    out: list[Divergence] = []
    for index in range(min(len(expected), len(actual))):
        out.extend(compare_ledger_row(index, expected[index], actual[index]))
    for index in range(len(actual), len(expected)):
        out.append(Divergence("missing_row", f"ledger[{index}]",
                              expected[index], None, row_index=index))
    for index in range(len(expected), len(actual)):
        out.append(Divergence("extra_row", f"ledger[{index}]",
                              None, actual[index], row_index=index))
    return out


def compare_cell(
    *,
    cell_id: str,
    expected_funnel: Mapping[str, Any],
    actual_funnel: Mapping[str, Any],
    expected_ledger: Sequence[Mapping[str, Any]],
    actual_ledger: Sequence[Mapping[str, Any]],
    actual_assertions: Mapping[int, int],
    source_truncated: bool = False,
    derived: Mapping[str, Any] | None = None,
) -> ComparisonResult:
    """Full comparison for one cell, in scan order: counters → assertions → ledger.

    A `source_truncated` cell (A2 §5: the Pine ledger table caps at 40 rows) is
    compared on counters and assertions only, and the result says so. Truncation
    downgrades the *comparison*; it never excuses a divergence in what is
    compared.
    """
    divergences = compare_counters(expected_funnel, actual_funnel)
    divergences += compare_assertions(actual_assertions)
    mode = "counters_only" if source_truncated else "full"
    if not source_truncated:
        divergences += compare_ledger(expected_ledger, actual_ledger)
    return ComparisonResult(
        cell_id=cell_id,
        divergences=tuple(divergences),
        mode=mode,
        not_applicable=tuple(f"K{i}" for i in ASSERTIONS_NOT_APPLICABLE),
        derived=derived,
    )

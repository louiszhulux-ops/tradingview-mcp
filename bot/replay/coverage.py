"""The coverage precondition: a check on the *input*, not on the strategy.

`fold_bars` and `fold_bars_with_ltf` measure the bar series a cell was handed.
They are not strategy parity counters, and the original B3 criterion 1 was wrong
to list them alongside `sweeps` and `fills`: a shortfall there is a property of
the dataset, decided before the engine makes a single decision.

The 1m fold-A cells are exactly this case. The P-9 candidate carries 9,677
MGC parents with LTF against the 9,813 the run recorded (9,675 vs 9,812 for
MNQ), because the `request.security_lower_tf` 100,000-value window is a trailing
one and has slid forward since 2026. Running the engine on that series and
reporting "counter mismatch" would blame the engine for a hole in the data.

So: the check runs **first**, and a mismatch halts the cell as
`PRECONDITION-FAIL` with the engine never started. Nothing here reconstructs,
interpolates, back-fills or substitutes; a short series stays short.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from bot.data.bars import ParentBar
from bot.strategy.v53.engine import in_fold


@dataclass(frozen=True)
class CoverageCounts:
    """`foldbars` (K30) and `w/LTF` (K29), counted as V53 counts them."""

    fold_bars: int
    fold_bars_with_ltf: int

    #: First in-fold parent carrying no LTF sub-bars, if any.
    first_parent_without_ltf_ms: int | None = None

    def __post_init__(self) -> None:
        if self.fold_bars_with_ltf > self.fold_bars:
            raise ValueError(
                f"fold_bars_with_ltf {self.fold_bars_with_ltf} exceeds "
                f"fold_bars {self.fold_bars}"
            )


def count_coverage(
    parents: Iterable[tuple[int, int]] | Iterable[ParentBar], fold: str
) -> CoverageCounts:
    """Count coverage over a series, from `(open_ts_ms, ltf_count)` or ParentBars.

    Mirrors `V53Engine.on_bar`: a bar counts toward `fold_bars` when `inFold`
    holds on its **open** time, and toward `fold_bars_with_ltf` when it also
    carries at least one sub-bar.
    """
    fold_bars = 0
    with_ltf = 0
    first_without: int | None = None
    for item in parents:
        if isinstance(item, ParentBar):
            open_ts, ltf_count = item.bar.open_ts_ms, item.ltf_count
        else:
            open_ts, ltf_count = item
        if not in_fold(fold, open_ts):
            continue
        fold_bars += 1
        if ltf_count > 0:
            with_ltf += 1
        elif first_without is None:
            first_without = open_ts
    return CoverageCounts(fold_bars, with_ltf, first_without)


@dataclass(frozen=True)
class CoverageCheck:
    """The precondition result, carrying everything the report must name."""

    cell_id: str
    instrument: str
    fold: str
    ltf_timeframe: str
    expected_fold_bars: int
    actual_fold_bars: int
    expected_fold_bars_with_ltf: int
    actual_fold_bars_with_ltf: int
    first_divergent_parent_ms: int | None

    @property
    def ok(self) -> bool:
        return (
            self.expected_fold_bars == self.actual_fold_bars
            and self.expected_fold_bars_with_ltf == self.actual_fold_bars_with_ltf
        )

    @property
    def shortfall(self) -> int:
        """How many in-fold parents lack LTF relative to the recorded run."""
        return self.expected_fold_bars_with_ltf - self.actual_fold_bars_with_ltf

    def report_lines(self) -> tuple[str, ...]:
        """The precondition report. Names expected and actual, never a guess."""
        lines = [
            f"cell {self.cell_id}",
            f"  instrument              {self.instrument}",
            f"  fold                    {self.fold}",
            f"  ltf timeframe           {self.ltf_timeframe}",
            f"  fold_bars               expected {self.expected_fold_bars} "
            f"actual {self.actual_fold_bars}",
            f"  fold_bars_with_ltf      expected {self.expected_fold_bars_with_ltf} "
            f"actual {self.actual_fold_bars_with_ltf}",
        ]
        if self.shortfall:
            lines.append(f"  shortfall               {self.shortfall} parent bars")
        if self.first_divergent_parent_ms is not None:
            lines.append(
                f"  first parent w/o LTF    {self.first_divergent_parent_ms} "
                f"(first observable deficiency in this series; the recorded run "
                f"reports totals only, so the original divergence point is not "
                f"determinable)"
            )
        else:
            lines.append("  first parent w/o LTF    not determinable")
        lines.append(
            "  no reconstruction from a higher timeframe, no interpolation, "
            "no synthetic bars, no external substitution"
        )
        return tuple(lines)


def check_coverage(
    *,
    cell_id: str,
    instrument: str,
    fold: str,
    ltf_timeframe: str,
    actual: CoverageCounts,
    fixture_funnel: dict,
) -> CoverageCheck:
    """Compare counted coverage against the cell's golden fixture funnel."""
    expected_bars = fixture_funnel["fold_bars"]
    expected_with = fixture_funnel["fold_bars_with_ltf"]
    if expected_bars is None or expected_with is None:
        raise ValueError(
            f"{cell_id}: fixture does not record both coverage counters; the "
            f"precondition cannot be evaluated and the cell is not runnable"
        )
    return CoverageCheck(
        cell_id=cell_id,
        instrument=instrument,
        fold=fold,
        ltf_timeframe=ltf_timeframe,
        expected_fold_bars=expected_bars,
        actual_fold_bars=actual.fold_bars,
        expected_fold_bars_with_ltf=expected_with,
        actual_fold_bars_with_ltf=actual.fold_bars_with_ltf,
        first_divergent_parent_ms=actual.first_parent_without_ltf_ms,
    )

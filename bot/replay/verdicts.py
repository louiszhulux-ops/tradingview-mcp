"""Cell verdicts and the Gate 1 aggregation rule.

The repaired acceptance model, implemented. `bot/GATE1_ACCEPTANCE.md` is the
prose; this module is the only executable definition, and the two must agree.

The defect this closes: B3 as originally written had two outcomes, pass and
fail, for a situation with at least seven distinct states. A cell whose input
data does not exist, a cell whose data exists but does not reproduce the run's
coverage, and a cell that ran cleanly against unfrozen data are three different
things, and collapsing them either slanders a correct engine or launders a real
divergence into a pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, Iterable, Sequence


class DatasetStatus(str, Enum):
    """How much weight a cell's input dataset is allowed to carry.

    `AUTHORITATIVE` is an **evidentiary standard**, not a proof that the bars
    are byte-identical to the values V53 consumed in 2026. No historical LTF
    value artifact was ever recorded, so that identity cannot be proven and no
    future capture can manufacture the missing comparand. See
    `bot/GATE1_ACCEPTANCE.md` §2.
    """

    AUTHORITATIVE = "AUTHORITATIVE"
    CANDIDATE = "CANDIDATE"


class CellVerdict(str, Enum):
    """The seven states a cell may end in. Closed vocabulary."""

    NO_DATA = "NO-DATA"
    PRECONDITION_FAIL = "PRECONDITION-FAIL"
    SOURCE_TRUNCATED = "SOURCE-TRUNCATED"
    PROVISIONAL_PASS = "PROVISIONAL-PASS"
    PROVISIONAL_FAIL = "PROVISIONAL-FAIL"
    PASS = "PASS"
    FAIL = "FAIL"


class GateResult(str, Enum):
    """The gate's own outcome. Only `PASS` unblocks anything."""

    PASS = "GATE 1: PASS"
    FAIL = "GATE 1: FAIL"
    NOT_ADJUDICABLE_DIVERGENCE = "GATE 1: NOT ADJUDICABLE — DIVERGENCE ON CANDIDATE DATA"
    NOT_ADJUDICABLE_INSUFFICIENT = "GATE 1: NOT ADJUDICABLE — INSUFFICIENT EVIDENCE"


#: Classification precedence, blocking states first. A cell is classified at the
#: earliest tier whose condition holds, so an absent dataset is never reported
#: as a strategy divergence and a coverage shortfall never reaches the engine.
PRECEDENCE: Final[tuple[CellVerdict, ...]] = (
    CellVerdict.NO_DATA,
    CellVerdict.PRECONDITION_FAIL,
    CellVerdict.SOURCE_TRUNCATED,
    CellVerdict.PROVISIONAL_PASS,
    CellVerdict.PROVISIONAL_FAIL,
    CellVerdict.PASS,
    CellVerdict.FAIL,
)

#: The only verdicts that may appear in a passing gate.
PASSING_VERDICTS: Final[frozenset[CellVerdict]] = frozenset(
    {CellVerdict.PASS, CellVerdict.SOURCE_TRUNCATED}
)

#: 8 cells (MGC/MNQ × long/short × 1m/3m) × folds A, B, C.
EXPECTED_CELL_COUNT: Final[int] = 24


def precedence_rank(verdict: CellVerdict) -> int:
    return PRECEDENCE.index(verdict)


def decide_cell_verdict(
    *,
    data_present: bool,
    coverage_ok: bool,
    comparison_ok: bool,
    status: DatasetStatus,
    source_truncated: bool,
) -> CellVerdict:
    """Assign exactly one verdict, in the documented order.

    ==  ====================================  =========================
    #   condition                             verdict
    ==  ====================================  =========================
    1   a required input series is absent     NO-DATA
    2   coverage counters differ              PRECONDITION-FAIL
    3   comparison diverged, CANDIDATE data   PROVISIONAL-FAIL
    4   comparison diverged, AUTHORITATIVE    FAIL
    5   clean, CANDIDATE data                 PROVISIONAL-PASS
    6   clean, AUTHORITATIVE, truncated       SOURCE-TRUNCATED
    7   clean, AUTHORITATIVE                  PASS
    ==  ====================================  =========================

    Two refinements to the blocking-state precedence, both of which *tighten*
    the gate and neither of which may be relaxed:

    * **A divergence outranks truncation.** A2 §5 downgrades a truncated cell to
      counters-only comparison; it does not excuse a counter mismatch. Were
      truncation classified before the comparison result, a real divergence on a
      truncated cell would be laundered into a gate-passing verdict.
    * **Candidate status outranks truncation.** `SOURCE-TRUNCATED` counts toward
      a Gate 1 pass, so it is reachable only from an `AUTHORITATIVE` dataset.
      A truncated cell on candidate data is `PROVISIONAL-PASS`.

    `NO-DATA` is never a truncation downgrade. Truncation means the source
    recorded a capped subset of a run that happened; no-data means the run
    cannot be attempted at all.
    """
    if not isinstance(status, DatasetStatus):
        raise ValueError(f"status must be a DatasetStatus, got {status!r}")
    if not data_present:
        return CellVerdict.NO_DATA
    if not coverage_ok:
        return CellVerdict.PRECONDITION_FAIL
    if not comparison_ok:
        return (
            CellVerdict.PROVISIONAL_FAIL
            if status is DatasetStatus.CANDIDATE
            else CellVerdict.FAIL
        )
    if status is DatasetStatus.CANDIDATE:
        return CellVerdict.PROVISIONAL_PASS
    if source_truncated:
        return CellVerdict.SOURCE_TRUNCATED
    return CellVerdict.PASS


@dataclass(frozen=True)
class CellResult:
    """One cell's verdict plus the evidence that produced it."""

    cell_id: str
    verdict: CellVerdict
    status: DatasetStatus
    reason: str = ""
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.cell_id:
            raise ValueError("cell_id is required")
        if not isinstance(self.verdict, CellVerdict):
            raise ValueError(f"verdict must be a CellVerdict, got {self.verdict!r}")
        if not isinstance(self.status, DatasetStatus):
            raise ValueError(f"status must be a DatasetStatus, got {self.status!r}")
        if self.verdict in PASSING_VERDICTS and self.status is not DatasetStatus.AUTHORITATIVE:
            raise ValueError(
                f"{self.cell_id}: {self.verdict.value} is a gate-passing verdict "
                f"and requires an AUTHORITATIVE dataset, not {self.status.value}"
            )
        object.__setattr__(self, "detail", tuple(self.detail))


@dataclass(frozen=True)
class GateReport:
    """The aggregate. `result` is the only thing downstream phases may read."""

    result: GateResult
    cells: tuple[CellResult, ...]
    census: dict[CellVerdict, int]
    notes: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.result is GateResult.PASS

    def cells_with(self, verdict: CellVerdict) -> tuple[CellResult, ...]:
        return tuple(c for c in self.cells if c.verdict is verdict)


def aggregate(
    cells: Iterable[CellResult],
    *,
    expected_cell_count: int = EXPECTED_CELL_COUNT,
    expected_cell_ids: Sequence[str] | None = None,
) -> GateReport:
    """Reduce cell verdicts to one gate result.

    **Gate 1 passes if and only if every one of the expected cells is `PASS` or
    `SOURCE-TRUNCATED`.** No other combination passes, under any argument. A
    short census cannot pass either: a cell that was never evaluated is missing
    evidence, not satisfied evidence.
    """
    cells = tuple(cells)
    seen: dict[str, CellResult] = {}
    for cell in cells:
        if cell.cell_id in seen:
            raise ValueError(f"duplicate cell result {cell.cell_id!r}")
        seen[cell.cell_id] = cell

    census = {verdict: 0 for verdict in PRECEDENCE}
    for cell in cells:
        census[cell.verdict] += 1

    notes: list[str] = []
    complete = len(cells) == expected_cell_count
    if not complete:
        notes.append(
            f"census covers {len(cells)} cells, expected {expected_cell_count}; "
            f"an unevaluated cell is missing evidence, never satisfied evidence"
        )
    if expected_cell_ids is not None:
        missing = [cid for cid in expected_cell_ids if cid not in seen]
        unknown = sorted(set(seen) - set(expected_cell_ids))
        if missing:
            complete = False
            notes.append(f"cells never evaluated: {', '.join(missing)}")
        if unknown:
            complete = False
            notes.append(f"cells not in the expected set: {', '.join(unknown)}")

    if census[CellVerdict.FAIL]:
        result = GateResult.FAIL
    elif census[CellVerdict.PROVISIONAL_FAIL]:
        result = GateResult.NOT_ADJUDICABLE_DIVERGENCE
    elif complete and all(c.verdict in PASSING_VERDICTS for c in cells):
        result = GateResult.PASS
    else:
        result = GateResult.NOT_ADJUDICABLE_INSUFFICIENT

    return GateReport(result=result, cells=cells, census=census, notes=tuple(notes))

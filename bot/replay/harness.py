"""Gate 1 execution harness.

Drives the production V53 engine over the registered cells, compares each
against its golden fixture, and aggregates one gate result. It decides nothing
by itself: every rule it applies is defined in `bot/GATE1_ACCEPTANCE.md` and
implemented in `verdicts.py`, `coverage.py` and `compare.py`.

Order of operations per cell, and it is not negotiable:

    resolve identity → verify hashes → load bars
      → coverage precondition   (engine NOT started if this fails)
      → run V53
      → compare counters, assertions, ledger
      → assign exactly one verdict

Every cell is evaluated. There is no early stopping, no sampling, and no
short-circuit: a gate that stops at the first problem cannot report the others,
and the report is the point.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, Mapping, Sequence

from bot.contracts.enums import Direction, Timeframe
from bot.fixtures.loader import load_fixture
from bot.replay.compare import (
    ASSERTIONS_MUST_BE_ZERO, ASSERTIONS_NOT_APPLICABLE, BEHAVIOUR_COUNTERS,
    COVERAGE_COUNTERS, DERIVED_NO_COMPARAND, EXCLUDED_COUNTERS,
    ComparisonResult, compare_cell,
)
from bot.replay.coverage import CoverageCheck, check_coverage, count_coverage
from bot.replay.datasets import REPO_ROOT
from bot.replay.loader import DatasetLoadError, LoadedDataset, load_cell_dataset
from bot.replay.verdicts import (
    EXPECTED_CELL_COUNT, CellResult, CellVerdict, DatasetStatus, GateReport,
    aggregate, decide_cell_verdict,
)
from bot.strategy.v53.engine import V53Config, V53Engine
from bot.tools.extract_golden import parse_ledger_row, to_ms

#: Fixed enumeration order. Not derived from the filesystem, not sorted at run
#: time, not dependent on dict iteration — written out so two runs on two
#: machines produce byte-identical reports.
INSTRUMENTS: Final[tuple[tuple[str, str], ...]] = (("MGC", "MGC1!"), ("MNQ", "MNQ1!"))
DIRECTIONS: Final[tuple[tuple[str, Direction], ...]] = (
    ("L", Direction.LONG), ("S", Direction.SHORT))
LTFS: Final[tuple[tuple[str, Timeframe], ...]] = (("1m", Timeframe.M1), ("3m", Timeframe.M3))
FOLDS: Final[tuple[str, ...]] = ("A", "B", "C")

#: `syminfo.pointvalue`, explicit per UNRESOLVED U4 — V53's silent 1.0 fallback
#: must never reach a bot. Derived from the recorded ledgers in A2 and asserted
#: against every fixture's `derived.point_value_usd` by test.
POINT_VALUE: Final[dict[str, float]] = {"MGC1!": 10.0, "MNQ1!": 2.0}

#: `costUSD`, frozen at 3.00.
COST_USD: Final[float] = 3.00


@dataclass(frozen=True)
class Cell:
    """One Gate 1 cell's identity."""

    cell_id: str
    instrument: str
    instrument_short: str
    direction: Direction
    direction_code: str
    ltf: Timeframe
    fold: str

    @property
    def fixture_id(self) -> str:
        return self.cell_id


def registered_cells() -> tuple[Cell, ...]:
    """The 24 Gate 1 cells, in fixed order."""
    cells: list[Cell] = []
    for short, instrument in INSTRUMENTS:
        for code, direction in DIRECTIONS:
            for ltf_name, ltf in LTFS:
                for fold in FOLDS:
                    cells.append(Cell(
                        cell_id=f"v53-{short}-{code}-{ltf_name}-{fold}",
                        instrument=instrument, instrument_short=short,
                        direction=direction, direction_code=code,
                        ltf=ltf, fold=fold))
    return tuple(cells)


# --------------------------------------------------------------------- ledger

#: golden fixture `recorded` key → comparator field name.
_RECORDED_TO_FIELD: Final[dict[str, str]] = {
    "sweep_ts_ms": "sweep_ts", "sweep_kind": "sweep_kind",
    "sweep_extreme": "sweep_extreme", "choch_ts_ms": "choch_ts",
    "choch_level": "choch_level", "retest_ts_ms": "retest_ts",
    "bos_ts_ms": "bos_ts", "bos_level": "bos_level",
    "fvg_low": "fvg_low", "fvg_high": "fvg_high",
    "entry_ts_ms": "entry_ts", "entry_price": "entry_price",
    "stop_price": "stop_price", "outcome": "outcome",
    "r_multiple": "r_multiple", "pnl_usd": "pnl_usd",
    "exit_reason": "exit_reason", "bars_in_trade": "bars_in_trade",
}

def golden_ledger(fixture: Mapping) -> tuple[dict, ...]:
    """The fixture's recorded fills, projected onto the comparator's fields."""
    rows: list[dict] = []
    for fill in fixture["fills"]:
        recorded = fill["recorded"]
        rows.append({field: recorded[key] for key, field in _RECORDED_TO_FIELD.items()})
    return tuple(rows)


def engine_ledger(rows: Sequence[str], cell_id: str) -> tuple[dict, ...]:
    """Parse the engine's own ledger strings with the extractor's parser.

    Using one parser on both sides removes a whole class of false divergence:
    the golden fixtures were built by `parse_ledger_row` from V53's text, and
    the engine reproduces that text through `ledger_row`, so the same grammar
    decodes both. A formatting difference shows up as a divergence, which is
    exactly right — it is not quietly normalised away.
    """
    out: list[dict] = []
    for line in rows:
        parsed = parse_ledger_row(line, cell_id)
        row = {
            "sweep_kind": parsed["sweep_kind"],
            "sweep_extreme": parsed["sweep_extreme"],
            "choch_level": parsed["choch_level"],
            "bos_level": parsed["bos_level"],
            "fvg_low": parsed["fvg_low"], "fvg_high": parsed["fvg_high"],
            "entry_price": parsed["entry_price"],
            "stop_price": parsed["stop_price"],
            "outcome": parsed["outcome"], "r_multiple": parsed["r_multiple"],
            "pnl_usd": parsed["pnl_usd"], "exit_reason": parsed["exit_reason"],
            "bars_in_trade": parsed["bars_in_trade"],
        }
        for key, field_name in (("sweep_ts_utc", "sweep_ts"),
                                ("choch_ts_utc", "choch_ts"),
                                ("retest_ts_utc", "retest_ts"),
                                ("bos_ts_utc", "bos_ts"),
                                ("entry_ts_utc", "entry_ts")):
            text = parsed[key]
            row[field_name] = (
                None if text == "-"
                else to_ms(text, context=f"{cell_id} {field_name}"))
        out.append(row)
    return tuple(out)


# --------------------------------------------------------------------- result

@dataclass(frozen=True)
class CellRun:
    """Everything one cell produced, whether or not it reached the engine."""

    cell: Cell
    result: CellResult
    dataset: LoadedDataset | None = None
    coverage: CoverageCheck | None = None
    comparison: ComparisonResult | None = None
    funnel: Mapping[str, int] | None = None
    assertions: Mapping[int, int] | None = None
    derived: Mapping[str, str] | None = None
    engine_ran: bool = False
    error: str = ""


_CACHE: dict[tuple[str, Timeframe], LoadedDataset] = {}


def run_cell(cell: Cell, *, root: Path = REPO_ROOT, cache: dict | None = None) -> CellRun:
    """Evaluate one cell to exactly one lawful verdict."""
    store = _CACHE if cache is None else cache
    fixture = load_fixture(cell.fixture_id)
    key = (cell.instrument, cell.ltf)

    try:
        if key in store:
            # Folds A, B and C of one instrument/LTF share one bar series, so it
            # is loaded and hash-verified once and re-labelled per cell. The
            # bars themselves are immutable and shared; only the identity
            # differs.
            loaded = store[key]
            dataset = LoadedDataset(
                cell=replace(loaded.cell, cell_id=cell.cell_id, fold=cell.fold),
                resolved=loaded.resolved, parents=loaded.parents)
        else:
            dataset = load_cell_dataset(
                cell_id=cell.cell_id, instrument=cell.instrument, fold=cell.fold,
                ltf=cell.ltf, root=root)
            store[key] = dataset
    except DatasetLoadError as exc:
        # A present-but-untrustworthy file is not evidence. NO-DATA, with the
        # reason stated — never a silent downgrade to "run it anyway".
        return CellRun(
            cell=cell,
            result=CellResult(cell.cell_id, CellVerdict.NO_DATA,
                              DatasetStatus.CANDIDATE,
                              reason="dataset refused", detail=(str(exc),)),
            error=str(exc))

    status = dataset.status

    # ---- NO-DATA: a required series is absent -----------------------------
    if not dataset.data_present:
        return CellRun(
            cell=cell, dataset=dataset,
            result=CellResult(
                cell.cell_id, CellVerdict.NO_DATA, status,
                reason="required input series absent",
                detail=tuple(f"missing {path}" for path in dataset.cell.missing)))

    # ---- coverage precondition, BEFORE the engine -------------------------
    counts = count_coverage(dataset.parents, cell.fold)
    coverage = check_coverage(
        cell_id=cell.cell_id, instrument=cell.instrument, fold=cell.fold,
        ltf_timeframe=cell.ltf.value, actual=counts,
        fixture_funnel=fixture["funnel"])
    if not coverage.ok:
        return CellRun(
            cell=cell, dataset=dataset, coverage=coverage, engine_ran=False,
            result=CellResult(
                cell.cell_id, CellVerdict.PRECONDITION_FAIL, status,
                reason="input coverage does not reproduce the recorded run",
                detail=coverage.report_lines()))

    # ---- run the production V53 engine ------------------------------------
    engine = V53Engine(V53Config(
        instrument=cell.instrument, direction=cell.direction, ltf=cell.ltf,
        point_value=POINT_VALUE[cell.instrument], fold=cell.fold,
        cost_usd=COST_USD))
    for parent in dataset.parents:
        engine.on_bar(parent)

    counters = engine.counters
    funnel = {name: getattr(counters, name) for name in BEHAVIOUR_COUNTERS}
    funnel |= {"fold_bars": counters.fold_bars,
               "fold_bars_with_ltf": counters.fold_bars_with_ltf,
               "ltf_bars": counters.ltf_bars_seen}
    assertions = {index: counters[index] for index in ASSERTIONS_MUST_BE_ZERO}

    comparison = compare_cell(
        cell_id=cell.cell_id,
        expected_funnel=fixture["funnel"], actual_funnel=funnel,
        expected_ledger=golden_ledger(fixture),
        actual_ledger=engine_ledger(engine.ledger, cell.cell_id),
        actual_assertions=assertions,
        source_truncated=bool(fixture["fills_truncated_at_source"]),
        derived={"target_price": "computed per fill, not compared",
                 "mfe": "computed per fill, not compared",
                 "mae": "computed per fill, not compared"})

    verdict = decide_cell_verdict(
        data_present=True, coverage_ok=True, comparison_ok=comparison.ok,
        status=status,
        source_truncated=bool(fixture["fills_truncated_at_source"]))

    reason = "comparison clean" if comparison.ok else "parity divergence"
    if status is DatasetStatus.CANDIDATE and comparison.ok:
        reason = "comparison clean, but the dataset is CANDIDATE"
    return CellRun(
        cell=cell, dataset=dataset, coverage=coverage, comparison=comparison,
        funnel=funnel, assertions=assertions, engine_ran=True,
        derived={name: "DERIVED — NO GOLDEN COMPARAND" for name in DERIVED_NO_COMPARAND},
        result=CellResult(cell.cell_id, verdict, status, reason=reason,
                          detail=comparison.report_lines()))


@dataclass(frozen=True)
class Gate1Run:
    """A whole Gate 1 evaluation: every cell, and the one aggregate result."""

    runs: tuple[CellRun, ...]
    report: GateReport
    started_utc: str
    commit: str

    @property
    def cells_evaluated(self) -> int:
        return len(self.runs)


def repo_commit(root: Path = REPO_ROOT) -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or "(unknown)"
    except (OSError, subprocess.SubprocessError):
        return "(unknown)"


def run_gate1(*, root: Path = REPO_ROOT) -> Gate1Run:
    """Evaluate all 24 cells and aggregate. No early stopping, ever."""
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cells = registered_cells()
    cache: dict = {}
    runs = tuple(run_cell(cell, root=root, cache=cache) for cell in cells)
    report = aggregate(
        [run.result for run in runs],
        expected_cell_count=EXPECTED_CELL_COUNT,
        expected_cell_ids=[cell.cell_id for cell in cells])
    return Gate1Run(runs=runs, report=report, started_utc=started,
                    commit=repo_commit(root))

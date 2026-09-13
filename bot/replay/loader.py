"""Gate 1 dataset loader.

Turns registered CSV files into the `ParentBar` series V53 consumes, carrying
the provenance criterion 0 requires. It refuses more than it accepts, on
purpose.

What it will not do, in any circumstance:

* infer or manufacture `AUTHORITATIVE` — that status must be *earned* by an
  explicit declaration on every required input, and is never derived from
  silence, from a qualified string, or from the data looking right;
* reconstruct a 1m or 3m series from 5m bars;
* interpolate, back-fill or synthesise a missing bar;
* substitute an external source;
* use a file whose sha256 does not match the manifest.

------------------------------------------------------------------------------
SPECIFICATION GAP G1 — how per-dataset statuses combine into a per-cell status
------------------------------------------------------------------------------
`bot/GATE1_ACCEPTANCE.md` §1 requires every cell to declare one status, and
requires an unrecognised status (such as the frozen 5m manifest's `PARTIAL`) to
be refused. It does **not** say how a cell with two datasets at two different
statuses resolves to one, and every Gate 1 cell has two: a 5m parent and an LTF
series.

Resolved here as a **meet**, with the rule stated rather than assumed:

    a cell is AUTHORITATIVE  ⟺  every required dataset is explicitly,
                                unqualifiedly AUTHORITATIVE
    otherwise                    the cell is CANDIDATE

An unrecognised status therefore *refuses to confer authority* — which is what
refusing `PARTIAL` means operationally — while leaving the cell evaluable at
candidate weight, where `decide_cell_verdict` and `CellResult` both guarantee it
can never reach a gate-passing verdict. Nothing is upgraded; `CANDIDATE` is the
floor, not a promotion. Every unresolved status is recorded by name in the
cell's provenance and printed in the report, so the reason is never hidden.

**This resolution is flagged for ratification and is not silently chosen.** The
alternative — treating an unrecognised status as `NO-DATA` — would collapse all
24 cells into one bucket and destroy the distinction between "no 3m file
exists", "fold A coverage is short" and "the data is merely unfrozen", which is
the entire point of the repaired vocabulary.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Sequence

from bot.contracts.enums import Timeframe
from bot.data.bars import Bar, ParentBar, validate_series
from bot.replay.datasets import (
    LTF_MANIFEST, PARENT_MANIFEST, REPO_ROOT, CellDataset, DatasetRef,
    DatasetStatusError, manifest_artifacts, read_manifest_status,
)
from bot.replay.verdicts import DatasetStatus


class DatasetLoadError(ValueError):
    """A dataset that must not be used. Never downgraded to a warning."""


#: Registered Gate 1 datasets: (instrument, timeframe) → (repo path, manifest).
#: 3m is registered with no file on purpose — the series does not exist, and a
#: cell that needs it must reach `NO-DATA` rather than quietly disappear.
REGISTRY: dict[tuple[str, Timeframe], tuple[str, Path]] = {
    ("MGC1!", Timeframe.M5): ("data/phase_c/MGC1__5m.csv", PARENT_MANIFEST),
    ("MNQ1!", Timeframe.M5): ("data/phase_c/MNQ1__5m.csv", PARENT_MANIFEST),
    ("MGC1!", Timeframe.M1): ("data/phase_c_ltf/MGC1__1m.csv", LTF_MANIFEST),
    ("MNQ1!", Timeframe.M1): ("data/phase_c_ltf/MNQ1__1m.csv", LTF_MANIFEST),
    ("MGC1!", Timeframe.M3): ("data/phase_c_ltf/MGC1__3m.csv", LTF_MANIFEST),
    ("MNQ1!", Timeframe.M3): ("data/phase_c_ltf/MNQ1__3m.csv", LTF_MANIFEST),
}

#: How each registered series was captured. Recorded, not inferred.
PROVENANCE: dict[Timeframe, str] = {
    Timeframe.M5: "B-2 export: model().mainSeries().bars() via CDP, paged to the history limit",
    Timeframe.M1: "P-9 extraction: request.security_lower_tf(tickerid, \"1\", <field>), natural cap",
    Timeframe.M3: "no capture exists",
}


@dataclass(frozen=True)
class ResolvedStatus:
    """A cell's status, plus every declaration that produced it."""

    status: DatasetStatus
    declarations: tuple[tuple[str, str], ...]      # (path, raw status text)
    unresolved: tuple[tuple[str, str], ...] = ()   # (path, why it did not parse)

    @property
    def authoritative(self) -> bool:
        return self.status is DatasetStatus.AUTHORITATIVE


@dataclass(frozen=True)
class LoadedDataset:
    """A cell's inputs, verified, with the provenance criterion 0 requires."""

    cell: CellDataset
    resolved: ResolvedStatus
    parents: tuple[ParentBar, ...] = ()

    @property
    def status(self) -> DatasetStatus:
        return self.cell.status

    @property
    def data_present(self) -> bool:
        return self.cell.data_present

    def provenance_lines(self) -> tuple[str, ...]:
        lines = [
            f"  instrument        {self.cell.instrument}",
            f"  fold              {self.cell.fold}",
            f"  ltf timeframe     {self.cell.ltf_timeframe}",
            f"  cell status       {self.cell.status.value}",
        ]
        for ref in self.cell.refs:
            state = "present" if ref.present else "ABSENT"
            lines.append(f"  {ref.role:<6} {ref.path}")
            lines.append(f"         sha256 {ref.sha256 or '(not recorded)'}  [{state}]")
        for path, raw in self.resolved.declarations:
            lines.append(f"  status declared   {raw!r}  ({path})")
        for path, why in self.resolved.unresolved:
            lines.append(f"  status UNRESOLVED {path}: {why}")
        lines.append(f"  capture           {self.cell.provenance}")
        return tuple(lines)


def resolve_status(entries: Sequence[tuple[str, Path]]) -> ResolvedStatus:
    """Combine per-dataset statuses into one cell status. See gap G1 above."""
    declarations: list[tuple[str, str]] = []
    unresolved: list[tuple[str, str]] = []
    parsed: list[DatasetStatus] = []
    for path, manifest in entries:
        raw = "(no manifest)"
        try:
            import json
            raw = str(json.loads(manifest.read_text(encoding="utf-8")).get("status"))
        except OSError:
            pass
        declarations.append((path, raw))
        try:
            parsed.append(read_manifest_status(manifest))
        except DatasetStatusError as exc:
            unresolved.append((path, str(exc).split(".")[0]))
    status = (
        DatasetStatus.AUTHORITATIVE
        if parsed and not unresolved and all(s is DatasetStatus.AUTHORITATIVE for s in parsed)
        else DatasetStatus.CANDIDATE
    )
    return ResolvedStatus(status, tuple(declarations), tuple(unresolved))


def _refs(instrument: str, ltf: Timeframe, root: Path) -> list[DatasetRef]:
    refs: list[DatasetRef] = []
    for role, timeframe in (("parent", Timeframe.M5), ("ltf", ltf)):
        rel, manifest = REGISTRY[(instrument, timeframe)]
        recorded = manifest_artifacts(manifest).get(rel, "") if manifest.is_file() else ""
        refs.append(DatasetRef(role, rel, recorded, (root / rel).is_file()))
    return refs


def load_cell_dataset(
    *, cell_id: str, instrument: str, fold: str, ltf: Timeframe, root: Path = REPO_ROOT
) -> LoadedDataset:
    """Resolve a cell's identity, verify its files, and load its bars.

    Returns without bars when any required file is absent — that cell is
    `NO-DATA`, and there is nothing to load. Raises only when a file is present
    but must not be trusted.
    """
    refs = _refs(instrument, ltf, root)
    entries = [(REGISTRY[(instrument, tf)][0], REGISTRY[(instrument, tf)][1])
               for tf in (Timeframe.M5, ltf)]
    resolved = resolve_status(entries)
    cell = CellDataset(
        cell_id=cell_id, instrument=instrument, fold=fold,
        ltf_timeframe=ltf.value, status=resolved.status, refs=tuple(refs),
        provenance="; ".join(
            f"{tf.value}: {PROVENANCE[tf]}" for tf in (Timeframe.M5, ltf)),
    )
    if not cell.data_present:
        return LoadedDataset(cell=cell, resolved=resolved)

    for ref in refs:
        if not ref.sha256:
            raise DatasetLoadError(
                f"{cell_id}: {ref.path} has no recorded sha256 in its manifest; "
                f"an unhashed file is not identifiable evidence")
        if not ref.verify(root):
            raise DatasetLoadError(
                f"{cell_id}: {ref.path} does not match its recorded sha256 "
                f"{ref.sha256}; the file on disk is not the dataset the manifest "
                f"describes and must not be used")

    parent_rows = read_rows(root / refs[0].path)
    ltf_rows = read_rows(root / refs[1].path)
    parents = build_parents(instrument, parent_rows, ltf_rows, ltf)
    return LoadedDataset(cell=cell, resolved=resolved, parents=parents)


def read_rows(path: Path) -> list[tuple[int, Decimal, Decimal, Decimal]]:
    """Read `timestamp,high,low,close`. Prices stay exact text → `Decimal`."""
    out: list[tuple[int, Decimal, Decimal, Decimal]] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        missing = {"timestamp", "high", "low", "close"} - set(reader.fieldnames or ())
        if missing:
            raise DatasetLoadError(f"{path} lacks columns {sorted(missing)}")
        for row in reader:
            out.append((int(row["timestamp"]), Decimal(row["high"]),
                        Decimal(row["low"]), Decimal(row["close"])))
    return out


def build_parents(
    instrument: str,
    parent_rows: Iterable[tuple[int, Decimal, Decimal, Decimal]],
    ltf_rows: Iterable[tuple[int, Decimal, Decimal, Decimal]],
    ltf: Timeframe,
) -> tuple[ParentBar, ...]:
    """Nest LTF sub-bars under their 5m parents, exactly as they fall.

    Association is by containment in the parent's half-open span, computed from
    the sub-bar's own timestamp. **Nothing is created**: a parent with no
    sub-bars gets an empty array, a parent with four gets four, and a minute in
    which nothing traded stays absent. `open` and `volume` are `None` because
    the source never recorded them.
    """
    parents = tuple(parent_rows)
    span = 5 * 60
    index: dict[int, list[Bar]] = {row[0]: [] for row in parents}
    for ts, high, low, close in ltf_rows:
        anchor = ts - (ts % span)
        bucket = index.get(anchor)
        if bucket is None:
            continue        # sub-bar outside the exported parent range; not ours
        bucket.append(Bar(instrument, ltf, ts * 1000, (ts + ltf.minutes * 60) * 1000,
                          None, high, low, close, None))

    built: list[ParentBar] = []
    bars: list[Bar] = []
    for ts, high, low, close in parents:
        bar = Bar(instrument, Timeframe.M5, ts * 1000, (ts + span) * 1000,
                  None, high, low, close, None)
        bars.append(bar)
        subs = sorted(index[ts], key=lambda b: b.open_ts_ms)
        built.append(ParentBar(bar, ltf, tuple(subs)))
    validate_series(bars)
    return tuple(built)

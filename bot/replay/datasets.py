"""Dataset provenance and status, as a mandatory Gate 1 input.

B3 originally said nothing about which dataset a cell ran on, so its result
could not state what it meant. Every cell now declares its files, their hashes,
the manifest status, and the capture that produced them.

**The loader reads status. It never manufactures or upgrades one.** The
asymmetry in :func:`parse_status` is deliberate: a status may be recognised as
`CANDIDATE` from a qualified string, because that can only ever *downgrade* a
cell's weight, while `AUTHORITATIVE` is accepted only from the bare, unqualified
token. There is no code path from an unrecognised status to a gate-passing
verdict.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bot.replay.verdicts import DatasetStatus

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The dataset manifests this repository currently carries.
PARENT_MANIFEST = REPO_ROOT / "data" / "phase_c_manifest.json"
LTF_MANIFEST = REPO_ROOT / "data" / "phase_c_ltf_manifest.json"


class DatasetStatusError(ValueError):
    """A dataset whose status cannot be read as a Gate 1 status.

    Raised rather than defaulted. An undeclared status is not a permission to
    assume the weaker one, and certainly not the stronger one — it is a data
    governance question for a human.
    """


def parse_status(raw: Any) -> DatasetStatus:
    """Map a manifest `status` string onto a Gate 1 status, strictly.

    * exactly ``AUTHORITATIVE`` → :attr:`DatasetStatus.AUTHORITATIVE`
    * a string whose first token is ``CANDIDATE`` → :attr:`DatasetStatus.CANDIDATE`
      (the P-9 manifest reads ``CANDIDATE -- NOT FROZEN, NOT AUTHORITATIVE, NOT
      GROUND TRUTH``; the qualifiers only reinforce the downgrade)
    * anything else → :class:`DatasetStatusError`

    `PARTIAL`, the status the frozen 5m manifest currently carries, is
    deliberately **not** recognised. It is a statement about that export's
    completeness, not a Gate 1 status, and inferring one from it would be
    precisely the silent upgrade this function exists to prevent.
    """
    if not isinstance(raw, str) or not raw.strip():
        raise DatasetStatusError(f"status must be a non-empty string, got {raw!r}")
    text = raw.strip()
    if text == DatasetStatus.AUTHORITATIVE.value:
        return DatasetStatus.AUTHORITATIVE
    if text.split()[0].rstrip(",;:") == DatasetStatus.CANDIDATE.value:
        return DatasetStatus.CANDIDATE
    raise DatasetStatusError(
        f"status {text!r} is not a Gate 1 status. Recognised: exactly "
        f"'AUTHORITATIVE', or a string beginning 'CANDIDATE'. A dataset whose "
        f"status is undeclared or non-standard may not be assumed into either; "
        f"declare it in the manifest or leave the cell unadjudicable."
    )


@dataclass(frozen=True)
class DatasetRef:
    """One file a cell depends on, with the hash that identifies it."""

    role: str           # "parent" (5m) or "ltf" (1m/3m)
    path: str           # repo-relative
    sha256: str
    present: bool

    def verify(self, root: Path = REPO_ROOT) -> bool:
        """Re-hash the file on disk and compare. Never repairs, never rewrites."""
        target = root / self.path
        if not target.is_file():
            return False
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        return digest == self.sha256


@dataclass(frozen=True)
class CellDataset:
    """Everything Gate 1 must know about a cell's inputs before it runs."""

    cell_id: str
    instrument: str
    fold: str
    ltf_timeframe: str
    status: DatasetStatus
    refs: tuple[DatasetRef, ...]
    provenance: str

    def __post_init__(self) -> None:
        if not isinstance(self.status, DatasetStatus):
            raise DatasetStatusError(
                f"{self.cell_id}: status must be a DatasetStatus, got {self.status!r}"
            )
        object.__setattr__(self, "refs", tuple(self.refs))

    @property
    def data_present(self) -> bool:
        """True only when every required input file is present.

        A cell missing any required series is `NO-DATA`. There is no partial
        input: the engine cannot replay half a fold.
        """
        return bool(self.refs) and all(ref.present for ref in self.refs)

    @property
    def missing(self) -> tuple[str, ...]:
        return tuple(ref.path for ref in self.refs if not ref.present)


def read_manifest_status(path: Path) -> DatasetStatus:
    """Read one manifest's declared status. Propagated, never overridden."""
    if not path.is_file():
        raise DatasetStatusError(f"no manifest at {path}")
    return parse_status(json.loads(path.read_text(encoding="utf-8")).get("status"))


def manifest_artifacts(path: Path) -> dict[str, str]:
    """Map repo-relative path → recorded sha256 for a manifest's artifacts."""
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for entry in data.get("artifacts", []):
        if "path" in entry and "sha256" in entry:
            out[entry["path"]] = entry["sha256"]
    return out

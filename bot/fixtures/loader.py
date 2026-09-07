"""Golden fixture loader.

Every fixture read through this module has all of its timestamps re-checked
against the A1 pre-FE guard, so a fixture carrying held-out data cannot enter a
test, a replay or a debugging session even if it somehow reached disk.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from bot.guards import assert_pre_fe

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
MANIFEST = GOLDEN_DIR / "manifest.json"

#: Every field in a fixture whose value is an epoch-ms timestamp.
TIMESTAMP_FIELDS = (
    "sweep_ts_ms", "choch_ts_ms", "retest_ts_ms", "bos_ts_ms", "entry_ts_ms",
)


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def load_fixture(fixture_id: str) -> dict:
    """Load one fixture and guard every timestamp in it."""
    path = GOLDEN_DIR / f"{fixture_id}.json"
    fixture = json.loads(path.read_text(encoding="utf-8"))
    guard_fixture(fixture)
    return fixture


def load_all() -> list[dict]:
    """Load every fixture named by the manifest, in manifest order."""
    return [load_fixture(entry["fixture_id"]) for entry in load_manifest()["fixtures"]]


def iter_timestamps(fixture: dict) -> Iterator[tuple[str, int]]:
    """Yield (context, epoch-ms) for every timestamp the fixture carries."""
    fid = fixture["fixture_id"]
    yield f"{fid} coverage.start_ms", fixture["coverage"]["start_ms"]
    yield f"{fid} coverage.end_ms", fixture["coverage"]["end_ms"]
    for fill in fixture["fills"]:
        for field in TIMESTAMP_FIELDS:
            yield f"{fid} fill[{fill['index']}].{field}", fill["recorded"][field]


def guard_fixture(fixture: dict) -> int:
    """Apply assert_pre_fe to every timestamp; return the count checked."""
    count = 0
    for context, value in iter_timestamps(fixture):
        assert_pre_fe(value, context=context)
        count += 1
    return count

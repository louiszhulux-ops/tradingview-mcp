#!/usr/bin/env python3
"""A2 — golden fixture extraction.

Converts the committed Phase 13F (folds A, B) and Phase 14 (fold C) run records
into machine-readable golden fixtures, one per (instrument, direction, LTF, fold)
cell. B2/B3 replay a Python V53 against these and must reproduce them exactly.

**This script contains no strategy logic.** It parses recorded text and performs
documented arithmetic on recorded fields. It does not detect a sweep, select a
CHOCH, qualify a displacement, or decide an outcome. Any change that would require
it to do so is a re-implementation of V53 and must be refused, not written here.

Sources are read-only and never modified. Every timestamp passes the A1 pre-FE
guard, so no Phase 16 data can enter a fixture.

    python3 bot/tools/extract_golden.py              # write fixtures
    python3 bot/tools/extract_golden.py --check      # verify on-disk == regenerated
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bot.guards import assert_pre_fe  # noqa: E402

EXTRACTOR_VERSION = "1.0.0"
SCHEMA_VERSION = 1

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "bot" / "fixtures" / "golden"

# Source directories, by fold. Read-only.
SOURCES = {
    "A": REPO / "trader_v2" / "v53_runs",
    "B": REPO / "trader_v2" / "v53_runs",
    "C": REPO / "trader_v2" / "v53_runs_foldc",
}
PHASE = {"A": "13F", "B": "13F", "C": "14"}

INSTRUMENTS = {"MGC": "MGC1!", "MNQ": "MNQ1!"}
DIRECTIONS = ("L", "S")
LTFS = ("1m", "3m")
FOLDS = ("A", "B", "C")

# Contract point values, DERIVED from the committed ledger and verified against
# every stop-exit and target-exit row (see verify_fill_arithmetic). Not a free
# parameter: a wrong value fails extraction.
POINT_VALUE = {"MGC1!": Decimal("10"), "MNQ1!": Decimal("2")}

# Frozen V53 constants used only for derived, clearly-flagged convenience fields.
TGT_R = Decimal("5.0")
COST_USD = Decimal("3.00")

# Provenance anchors (hashes verified at extraction time).
CANONICAL_PINE = REPO / "trader_v2" / "V53_ltf_sequence.pine"
EXECUTED_PINE = REPO / "trader_v2" / "p15" / "executed" / "V53_EXECUTED_BUILD.pine"
CANONICAL_SHA = "7490766b6e3de062989a8e7f10939869cc6b679d253ce584f223064aa5797ef5"
EXECUTED_SHA = "2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6"

# What the source records cannot supply. Recorded in every fixture so B3 cannot
# silently assume coverage it does not have.
NOT_CAPTURED = [
    "5m and LTF pivot confirmations (ta.pivothigh/low) — never emitted per event",
    "per-sequence displacement qualification — only the aggregate BOS+disp counter",
    "V53 slot index (0..23) — not emitted in the ledger",
    "sequences that armed but never filled — only aggregate funnel counters",
    "per-bar state transitions — the ledger records one row per fill, at fill time",
    "exit price for timeout exits — only the R multiple and USD are recorded",
    "ATR at arm, and therefore r_atr_ratio — not emitted per event",
]

LEDGER_RE = re.compile(r"^(MGC1!|MNQ1!)\|")
FUNNEL_RE = re.compile(
    r"^FUNNEL (?P<dir>[LS]) (?P<fold>[ABC]) (?P<ltf>\dm): "
    r"foldbars (?P<foldbars>\d+) \| w/LTF (?P<withltf>\d+) \| "
    r"(?:LTFbars (?P<ltfbars>\d+) \| )?"
    r"sweeps (?P<sweeps>\d+) \| CHOCH (?P<choch>\d+) \| retests (?P<retests>\d+) \| "
    r"BOS\+disp (?P<bos>\d+) \| FVG (?P<fvg>\d+) \| fills (?P<fills>\d+)\s*$"
)
FUNNEL2_RE = re.compile(
    r"^\s*break-no-disp (?P<breaknodisp>\d+) \| noFVG (?P<nofvg>\d+) \| "
    r"Rband (?P<rband>\d+) \| FVGexpiry (?P<fvgexpiry>\d+) \| "
    r"expire(?: pre/post-CHOCH/post-retest)? "
    r"(?P<exp_pre>\d+)/(?P<exp_postchoch>\d+)/(?P<exp_postretest>\d+) \| "
    r"dropped (?P<dropped>\d+) \| ASSERTS (?P<asserts>.+?)\s*$"
)
PERF_RE = re.compile(
    r"^PERF (?P<inst>\S+) (?P<dir>[LS]) (?P<ltf>\dm) (?P<fold>[ABC]): "
    r"cov (?P<start>\S+ \S+) -> (?P<end>\S+ \S+) \| fills (?P<fills>\d+) \| (?P<rest>.*)$"
)
PERF_REST_RE = re.compile(
    r"^W(?P<wins>\d+) Lstop(?P<losses_stop>\d+) TO(?P<timeouts>\d+) \| "
    r"wr (?P<wr>[\d.]+)% \| Rpre (?P<rpre>[-\d.]+) \| Rpost (?P<rpost>[-\d.]+) \| "
    r"avg (?P<avg>[-\d.]+) \| med (?P<med>[-\d.]+) \| exp (?P<exp>[-\d.]+)R \| "
    r"maxConsecL (?P<max_consec_losses>\d+) \| DD_R (?P<dd_r>[-\d.]+) \| "
    r"DD_\$ (?P<dd_usd>[-\d.]+) \| tot\$ (?P<total_usd>[-\d.]+)\s*$"
)


class ExtractionError(RuntimeError):
    """Raised on anything unparsed or unreconciled. Extraction never guesses."""


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def to_ms(stamp: str, *, context: str) -> int:
    """Parse 'YYYY-MM-DD HH:MM' as UTC epoch-ms and guard it.

    The research record is UTC throughout: the fold constants FB/FC/FE are UTC
    epoch-ms and the fold coverage strings align with them exactly.
    """
    try:
        dt = datetime.strptime(stamp, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ExtractionError(f"unparsable timestamp {stamp!r} [{context}]") from exc
    return assert_pre_fe(int(dt.timestamp() * 1000), context=context)


def dec(text: str) -> str:
    """Normalise a recorded numeric to canonical text, preserving exact value."""
    return str(Decimal(text))


def parse_ledger_row(line: str, cell: str) -> dict:
    """Split one ledger row into its recorded fields.

    Field layout is the one fixed by trader_v2/g_cluster.py, the Phase 13G
    reference decoding.
    """
    p = line.split("|")
    if len(p) != 21:
        raise ExtractionError(f"ledger row has {len(p)} fields, expected 21 [{cell}]: {line}")

    def strip(idx: int, prefix: str) -> str:
        s = p[idx].strip()
        if not s.startswith(prefix):
            raise ExtractionError(f"field {idx} missing prefix {prefix!r} [{cell}]: {s!r}")
        return s[len(prefix):].strip()

    fvg = strip(12, "fvg ")
    if fvg.count("-") != 1:
        raise ExtractionError(f"unparsable fvg range {fvg!r} [{cell}]")
    fvg_low, fvg_high = fvg.split("-")

    return {
        "instrument": p[0].strip(),
        "direction": p[1].strip(),
        "ltf": p[2].strip(),
        "fold": p[3].strip(),
        "sweep_ts_utc": strip(4, "sw "),
        "sweep_kind": p[5].strip(),
        "sweep_extreme": dec(strip(6, "swX ")),
        "choch_ts_utc": strip(7, "ch "),
        "choch_level": dec(strip(8, "chL ")),
        "retest_ts_utc": strip(9, "rt "),
        "bos_ts_utc": strip(10, "bos "),
        "bos_level": dec(strip(11, "bosL ")),
        "fvg_low": dec(fvg_low),
        "fvg_high": dec(fvg_high),
        "entry_ts_utc": strip(13, "en "),
        "entry_price": dec(strip(14, "enPx ")),
        "stop_price": dec(strip(15, "stop ")),
        "outcome": p[16].strip(),
        "r_multiple": dec(p[17].strip().replace("R", "")),
        "pnl_usd": dec(p[18].strip().replace("$", "")),
        "exit_reason": p[19].strip(),
        "bars_in_trade": int(p[20].strip().replace("bars", "")),
    }


def verify_fill_arithmetic(rec: dict, cell: str) -> dict:
    """Reconcile the recorded P&L against the recorded prices, and derive.

    This is arithmetic on recorded fields, not strategy logic. A mismatch means
    the fixture would be wrong, so it raises rather than warning.
    """
    entry = Decimal(rec["entry_price"])
    stop = Decimal(rec["stop_price"])
    r_dist = abs(entry - stop)
    if r_dist == 0:
        raise ExtractionError(f"zero stop distance [{cell}]")

    mult = POINT_VALUE[rec["instrument"]]
    sign = Decimal(1) if rec["direction"] == "L" else Decimal(-1)
    usd = Decimal(rec["pnl_usd"])
    reason = rec["exit_reason"]

    checks = {}
    if reason == "target":
        expected = TGT_R * r_dist * mult - COST_USD
    elif reason == "stop":
        expected = -(r_dist * mult) - COST_USD
    else:
        expected = None  # timeout exits: exit price is not recorded

    if expected is not None:
        if abs(expected - usd) > Decimal("0.011"):
            raise ExtractionError(
                f"P&L does not reconcile [{cell}] {rec['entry_ts_utc']}: "
                f"recorded ${usd}, arithmetic ${expected}"
            )
        checks["pnl_reconciled"] = True
    else:
        checks["pnl_reconciled"] = False

    r_implied = usd / (r_dist * mult)
    if abs(r_implied - Decimal(rec["r_multiple"])) > Decimal("0.001"):
        raise ExtractionError(
            f"R multiple does not reconcile [{cell}] {rec['entry_ts_utc']}: "
            f"recorded {rec['r_multiple']}, implied {r_implied}"
        )
    checks["r_reconciled"] = True

    stop_inverted = (rec["direction"] == "L" and stop >= entry) or (
        rec["direction"] == "S" and stop <= entry
    )

    return {
        "r_distance": str(r_dist),
        "target_price": str(entry + sign * TGT_R * r_dist),
        "point_value_usd": str(mult),
        "stop_inverted": stop_inverted,
        "checks": checks,
        "note": (
            "target_price is arithmetic (entry ± tgtR × |entry − stop|, tgtR = 5.0 "
            "frozen). V53 does not emit a target price, so this is a derived "
            "convenience value, cross-validated against recorded P&L on every "
            "target exit — not a recorded expectation. stop_inverted marks a stop "
            "on the far side of entry, a real recorded V53 outcome that B2 must "
            "reproduce rather than correct."
        ),
    }


def event_keys(rec: dict) -> dict:
    """Phase 13G clustering identities, verbatim from trader_v2/g_cluster.py.

    Analysis identities only — never an execution idempotency key.
    """
    base = [rec["instrument"], rec["direction"], rec["ltf"]]
    primary = base + [
        rec["choch_ts_utc"], rec["choch_level"],
        rec["bos_ts_utc"], rec["bos_level"],
        rec["entry_ts_utc"], rec["entry_price"],
    ]
    alternative = base + [
        rec["bos_ts_utc"], rec["bos_level"],
        rec["entry_ts_utc"], rec["entry_price"],
    ]
    return {"primary": "|".join(primary), "alternative": "|".join(alternative)}


def parse_cell(short: str, direction: str, ltf: str, fold: str) -> dict:
    src = SOURCES[fold] / f"{short}_{direction}_{ltf}_{fold}.txt"
    if not src.is_file():
        raise ExtractionError(f"missing source artifact: {src}")

    cell = f"{short} {direction} {ltf} {fold}"
    text = src.read_text(encoding="utf-8")
    lines = text.splitlines()

    funnel = funnel2 = perf = None
    fills: list[dict] = []
    notes: list[str] = []
    in_ledger = False

    for line in lines:
        if not line.strip():
            continue
        if (m := FUNNEL_RE.match(line)):
            funnel = m.groupdict()
        elif (m := FUNNEL2_RE.match(line)):
            funnel2 = m.groupdict()
        elif (m := PERF_RE.match(line)):
            perf = m.groupdict()
        elif line.startswith("LEDGER"):
            in_ledger = True
        elif LEDGER_RE.match(line):
            if not in_ledger:
                raise ExtractionError(f"ledger row before LEDGER header [{cell}]")
            fills.append(parse_ledger_row(line.rstrip("\n"), cell))
        elif line.startswith("NOTE"):
            notes.append(line.rstrip())
        elif notes and line.startswith(" "):
            notes[-1] += " " + line.strip()  # continuation of the previous note
        else:
            raise ExtractionError(f"unrecognised line [{cell}]: {line!r}")

    for name, value in (("FUNNEL", funnel), ("FUNNEL cont.", funnel2), ("PERF", perf)):
        if value is None:
            raise ExtractionError(f"missing {name} line [{cell}]")

    inst = INSTRUMENTS[short]
    if perf["inst"] != inst or perf["dir"] != direction or perf["ltf"] != ltf or perf["fold"] != fold:
        raise ExtractionError(f"PERF header does not match filename [{cell}]")
    if funnel["dir"] != direction or funnel["ltf"] != ltf or funnel["fold"] != fold:
        raise ExtractionError(f"FUNNEL header does not match filename [{cell}]")

    declared = int(funnel["fills"])
    if declared != len(fills) or declared != int(perf["fills"]):
        raise ExtractionError(
            f"fill count disagreement [{cell}]: funnel {declared}, "
            f"perf {perf['fills']}, ledger rows {len(fills)}"
        )

    # Roadmap A2 criterion 5: the Pine ledger table caps at 40 rows.
    truncated = len(fills) == 40 and declared > 40

    asserts_raw = funnel2["asserts"].strip()
    if asserts_raw == "all 0":
        assert_values, all_zero = None, True
    else:
        assert_values = [int(v) for v in asserts_raw.split("/")]
        all_zero = all(v == 0 for v in assert_values)

    performance = {"fills": declared}
    rest = perf["rest"].strip()
    if rest == "ZERO TRADES":
        performance["zero_trades"] = True
    else:
        m = PERF_REST_RE.match(rest)
        if not m:
            raise ExtractionError(f"unparsable PERF tail [{cell}]: {rest!r}")
        performance["zero_trades"] = False
        for key, value in m.groupdict().items():
            performance[key] = int(value) if key in (
                "wins", "losses_stop", "timeouts", "max_consec_losses"
            ) else dec(value)

    built_fills = []
    for index, rec in enumerate(fills):
        if rec["instrument"] != inst or rec["direction"] != direction \
                or rec["ltf"] != ltf or rec["fold"] != fold:
            raise ExtractionError(f"ledger row {index} does not match cell [{cell}]")
        stamps = {}
        for field in ("sweep", "choch", "retest", "bos", "entry"):
            key = f"{field}_ts_utc"
            stamps[f"{field}_ts_ms"] = to_ms(rec[key], context=f"{cell} fill {index} {field}")
        built_fills.append({
            "index": index,
            "recorded": {**rec, **stamps},
            "derived": verify_fill_arithmetic(rec, cell),
            "event_keys": event_keys(rec),
        })

    cov_start = perf["start"]
    cov_end = perf["end"]

    return {
        "schema_version": SCHEMA_VERSION,
        "fixture_id": f"v53-{short}-{direction}-{ltf}-{fold}",
        "cell": {
            "instrument": inst,
            "instrument_short": short,
            "direction": direction,
            "ltf": ltf,
            "fold": fold,
        },
        "provenance": {
            "source_file": str(src.relative_to(REPO)),
            "source_sha256": sha256_of(src),
            "research_phase": PHASE[fold],
            "strategy_id": "V53",
            "executed_artifact": str(EXECUTED_PINE.relative_to(REPO)),
            "executed_artifact_sha256": EXECUTED_SHA,
            "canonical_artifact": str(CANONICAL_PINE.relative_to(REPO)),
            "canonical_artifact_sha256": CANONICAL_SHA,
            "attribution_note": (
                "The canonical artifact never executed (Phase 15 provenance "
                "correction). The executed artifact is the earliest hashed build "
                "of the program that produced this data; it reproduced the "
                "committed Phase 13F/14 per-cell results exactly under pooled "
                "packaging (p15/POOLED_DESIGN_VERIFICATION.md). No hash was "
                "captured at Phase 13F/14 run time, so the executed-artifact hash "
                "is an attribution by reproduction, not a contemporaneous record."
            ),
            "extractor": "bot/tools/extract_golden.py",
            "extractor_version": EXTRACTOR_VERSION,
        },
        "coverage": {
            "start_utc": cov_start,
            "start_ms": to_ms(cov_start, context=f"{cell} coverage start"),
            "end_utc": cov_end,
            "end_ms": to_ms(cov_end, context=f"{cell} coverage end"),
        },
        "funnel": {
            "fold_bars": int(funnel["foldbars"]),
            "fold_bars_with_ltf": int(funnel["withltf"]),
            "ltf_bars": int(funnel["ltfbars"]) if funnel["ltfbars"] else None,
            "sweeps": int(funnel["sweeps"]),
            "choch": int(funnel["choch"]),
            "retests": int(funnel["retests"]),
            "bos_displacement": int(funnel["bos"]),
            "fvg": int(funnel["fvg"]),
            "fills": declared,
            "break_no_displacement": int(funnel2["breaknodisp"]),
            "no_fvg": int(funnel2["nofvg"]),
            "r_band_rejects": int(funnel2["rband"]),
            "fvg_retest_expiry": int(funnel2["fvgexpiry"]),
            "expire_pre_choch": int(funnel2["exp_pre"]),
            "expire_post_choch": int(funnel2["exp_postchoch"]),
            "expire_post_retest": int(funnel2["exp_postretest"]),
            "dropped_no_slot": int(funnel2["dropped"]),
        },
        "asserts": {"raw": asserts_raw, "all_zero": all_zero, "values": assert_values},
        "performance": performance,
        "fills_truncated_at_source": truncated,
        "fills": built_fills,
        "source_notes": notes,
        "not_captured": NOT_CAPTURED,
    }


def conservation_ok(fx: dict) -> bool:
    """FVG = fills + R-band rejects + FVG retest expiry (audit §B3 criterion 4)."""
    f = fx["funnel"]
    return f["fvg"] == f["fills"] + f["r_band_rejects"] + f["fvg_retest_expiry"]


def dumps(obj: dict) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def build_all() -> dict[str, str]:
    """Return {relative filename: file content}. Deterministic and pure."""
    for path, expected in ((CANONICAL_PINE, CANONICAL_SHA), (EXECUTED_PINE, EXECUTED_SHA)):
        actual = sha256_of(path)
        if actual != expected:
            raise ExtractionError(
                f"provenance anchor changed: {path.relative_to(REPO)} is {actual}, "
                f"expected {expected}. Refusing to extract."
            )

    out: dict[str, str] = {}
    entries = []
    totals = {"fills": 0, "wins": 0}
    for short in sorted(INSTRUMENTS):
        for direction in DIRECTIONS:
            for ltf in LTFS:
                for fold in FOLDS:
                    fx = parse_cell(short, direction, ltf, fold)
                    if not conservation_ok(fx):
                        raise ExtractionError(
                            f"conservation identity fails for {fx['fixture_id']}"
                        )
                    out[f"{fx['fixture_id']}.json"] = dumps(fx)
                    totals["fills"] += fx["funnel"]["fills"]
                    totals["wins"] += fx["performance"].get("wins", 0)
                    entries.append({
                        "fixture_id": fx["fixture_id"],
                        "file": f"{fx['fixture_id']}.json",
                        "instrument": fx["cell"]["instrument"],
                        "direction": direction,
                        "ltf": ltf,
                        "fold": fold,
                        "fills": fx["funnel"]["fills"],
                        "source_file": fx["provenance"]["source_file"],
                        "source_sha256": fx["provenance"]["source_sha256"],
                        "fixture_sha256": hashlib.sha256(
                            out[f"{fx['fixture_id']}.json"].encode("utf-8")
                        ).hexdigest(),
                    })

    out["manifest.json"] = dumps({
        "schema_version": SCHEMA_VERSION,
        "extractor": "bot/tools/extract_golden.py",
        "extractor_version": EXTRACTOR_VERSION,
        "strategy_id": "V53",
        "executed_artifact_sha256": EXECUTED_SHA,
        "canonical_artifact_sha256": CANONICAL_SHA,
        "fixture_count": len(entries),
        "totals": totals,
        "cross_checks": {
            "pooled_total_fills": 58,
            "pooled_total_wins": 9,
            "phase13g_ab_fills": 40,
            "phase13g_ab_wins": 6,
            "reference": [
                "trader_v2/p15/POOLED_DESIGN_VERIFICATION.md",
                "trader_v2/v53_runs/PHASE13G_raw_output.txt",
                "trader_v2/v53_runs_foldc/PHASE14_raw_output.txt",
            ],
        },
        "fixtures": entries,
    })
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Extract V53 golden fixtures.")
    ap.add_argument("--check", action="store_true",
                    help="verify on-disk fixtures match a fresh extraction; write nothing")
    args = ap.parse_args(argv[1:])

    built = build_all()

    if args.check:
        problems = []
        on_disk = {p.name for p in OUT_DIR.glob("*.json")} if OUT_DIR.is_dir() else set()
        for extra in sorted(on_disk - set(built)):
            problems.append(f"unexpected fixture on disk: {extra}")
        for name, content in sorted(built.items()):
            path = OUT_DIR / name
            if not path.is_file():
                problems.append(f"missing fixture: {name}")
            elif path.read_text(encoding="utf-8") != content:
                problems.append(f"fixture differs from fresh extraction: {name}")
        if problems:
            print("extract_golden --check: FAIL", file=sys.stderr)
            for p in problems:
                print(f"  ! {p}", file=sys.stderr)
            return 1
        print(f"extract_golden --check: PASS — {len(built)} files match a fresh extraction")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in sorted(built.items()):
        (OUT_DIR / name).write_text(content, encoding="utf-8")
    print(f"extract_golden: wrote {len(built)} files to {OUT_DIR.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

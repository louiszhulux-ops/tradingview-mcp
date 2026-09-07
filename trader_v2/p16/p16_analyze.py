#!/usr/bin/env python3
"""Phase 16 analyser — PRE-REGISTERED, frozen before any OOS data exists.

Consumes Phase 16 run files (the V53 FUNNEL / PERF / LEDGER capture format) and
produces the whole pre-registered report mechanically. It selects nothing: no
instrument, direction, LTF, date, trade, cluster or outcome may be chosen by
this program or by its caller.

Frozen decisions it implements, all fixed in PHASE16_PROTOCOL.md before any run:

  * the validation window  2026-08-31 00:00 UTC -> 2027-04-02 00:00 UTC
  * both Phase 13G event identities, primary and alternative
  * the event outcome rule (protocol section 5): an event is a WIN only if
    EVERY fill in it is a WIN; any LOSS, any timeout, any mixture -> NON-WIN
  * H0: p = p* = 0.1751, one-sided exact binomial, alpha = 0.05
  * the N < 40 power floor
  * Clopper-Pearson 95% intervals
  * the three-way decision framework

Fails loudly. Malformed rows, out-of-window timestamps, unexpected
instrument/direction/LTF combinations and inconsistent counters all raise.

A verdict can only be produced for the pre-registered OOS window. Any other
window (used for testing against historical data) is marked non-OOS and the
decision framework refuses to run.

Read-only. Never connects to anything, never fetches data, never runs a strategy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------
# Frozen constants. None of these may be changed after accumulation begins.
# --------------------------------------------------------------------------

ANALYSER_VERSION = "1.0.0"

#: FE — the forward boundary. Data before this is research history.
OOS_START_MS = 1788134400000                      # 2026-08-31 00:00 UTC
OOS_END_MS = 1806624000000                        # 2027-04-02 00:00 UTC

P_STAR = 0.1751                                   # breakeven win rate, H0
ALPHA = 0.05                                      # one-sided, each direction
P1_ALTERNATIVE = 0.30                             # pre-registered alternative
MIN_EVENTS = 40                                   # power floor

BASELINE_SHA = "2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6"
ARTIFACT_SHA = "5c21acfab1b0c832aaa562a0afc84c94e595da2318f2366dd153c1d08172b333"
ARTIFACT_PATH = "trader_v2/p16/executed/V53_P16_OOS_BUILD.pine"

INSTRUMENTS = ("MGC1!", "MNQ1!")
DIRECTIONS = ("L", "S")
LTFS = ("1m", "3m")
OUTCOMES = ("WIN", "LOSS")
EXIT_REASONS = ("stop", "target", "timeout")
EXPECTED_CELLS = tuple(
    (i, d, l) for i in INSTRUMENTS for d in DIRECTIONS for l in LTFS
)

FIVE_MIN_MS = 300_000


class AnalyserError(RuntimeError):
    """Any malformed, ambiguous or out-of-scope input. Never recovered from."""


# --------------------------------------------------------------------------
# Window
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Window:
    """A time window. Only the pre-registered one may yield a verdict."""

    start_ms: int
    end_ms: int
    label: str
    is_oos: bool

    @staticmethod
    def oos() -> "Window":
        return Window(OOS_START_MS, OOS_END_MS, "phase16-oos", True)

    @staticmethod
    def for_testing(start_ms: int, end_ms: int, label: str) -> "Window":
        """A non-OOS window, for testing against historical data only.

        Statistics still compute; `decide()` refuses. This is the only way to
        run the analyser over anything but the frozen window, and the result
        carries `is_oos: false` so it can never be mistaken for a verdict.
        """
        if label == "phase16-oos":
            raise AnalyserError("the OOS label is reserved for Window.oos()")
        return Window(start_ms, end_ms, label, False)

    def contains(self, ts_ms: int) -> bool:
        return self.start_ms <= ts_ms < self.end_ms


# --------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Fill:
    """One ledger row. Field layout is V53's, via trader_v2/g_cluster.py."""

    instrument: str
    direction: str
    ltf: str
    fold: str
    sweep_ts: str
    sweep_kind: str
    sweep_extreme: float
    choch_ts: str
    choch_level: float
    retest_ts: str
    bos_ts: str
    bos_level: float
    fvg: str
    entry_ts: str
    entry_price: float
    stop_price: float
    outcome: str
    r_multiple: float
    pnl_usd: float
    exit_reason: str
    bars_in_trade: int
    entry_ts_ms: int
    source_file: str

    @property
    def cell(self) -> tuple[str, str, str]:
        return (self.instrument, self.direction, self.ltf)

    @property
    def primary_key(self) -> tuple:
        return (self.instrument, self.direction, self.ltf, self.choch_ts,
                self.choch_level, self.bos_ts, self.bos_level,
                self.entry_ts, self.entry_price)

    @property
    def alternative_key(self) -> tuple:
        return (self.instrument, self.direction, self.ltf, self.bos_ts,
                self.bos_level, self.entry_ts, self.entry_price)

    @property
    def exit_ts_ms(self) -> int:
        """Derived resolution time, for deterministic pooled ordering only."""
        return self.entry_ts_ms + self.bars_in_trade * FIVE_MIN_MS


@dataclass(frozen=True)
class Event:
    """A cluster of fills sharing one identity, classified by the frozen rule."""

    key: tuple
    identity: str
    fills: tuple[Fill, ...]

    @property
    def size(self) -> int:
        return len(self.fills)

    @property
    def is_win(self) -> bool:
        """Protocol section 5: WIN only if EVERY fill is a WIN.

        Any LOSS, any timeout, or any mixture makes the event NON-WIN. A timeout
        is already recorded as LOSS by V53, so the outcome field alone decides;
        the exit reason is checked too so a future capture change cannot quietly
        smuggle a non-WIN through.
        """
        return all(
            f.outcome == "WIN" and f.exit_reason == "target" for f in self.fills
        )

    @property
    def is_mixed(self) -> bool:
        return len({f.outcome for f in self.fills}) > 1


# --------------------------------------------------------------------------
# Parsing — fails loudly
# --------------------------------------------------------------------------

_LEDGER_RE = re.compile(r"^(MGC1!|MNQ1!)\|")
_FUNNEL_RE = re.compile(
    r"^FUNNEL (?P<dir>[LS]) (?P<fold>\S+) (?P<ltf>\dm): "
    r"foldbars (?P<foldbars>\d+) \| w/LTF (?P<withltf>\d+) \| "
    r"(?:LTFbars (?P<ltfbars>\d+) \| )?"
    r"sweeps (?P<sweeps>\d+) \| CHOCH (?P<choch>\d+) \| retests (?P<retests>\d+) \| "
    r"BOS\+disp (?P<bos>\d+) \| FVG (?P<fvg>\d+) \| fills (?P<fills>\d+)\s*$"
)
_FUNNEL2_RE = re.compile(
    r"^\s*break-no-disp (?P<bnd>\d+) \| noFVG (?P<nofvg>\d+) \| "
    r"Rband (?P<rband>\d+) \| FVGexpiry (?P<fvgexp>\d+) \| "
    r"expire(?: pre/post-CHOCH/post-retest)? (?P<e1>\d+)/(?P<e2>\d+)/(?P<e3>\d+) \| "
    r"dropped (?P<dropped>\d+) \| ASSERTS (?P<asserts>.+?)\s*$"
)
_PERF_RE = re.compile(
    r"^PERF (?P<inst>\S+) (?P<dir>[LS]) (?P<ltf>\dm) (?P<fold>\S+): "
    r"cov (?P<start>\S+ \S+) -> (?P<end>\S+ \S+) \| fills (?P<fills>\d+) \| (?P<rest>.*)$"
)


def _ts(text: str, context: str) -> int:
    try:
        return int(datetime.strptime(text, "%Y-%m-%d %H:%M")
                   .replace(tzinfo=timezone.utc).timestamp() * 1000)
    except ValueError as exc:
        raise AnalyserError(f"unparsable timestamp {text!r} [{context}]") from exc


def _num(text: str, context: str) -> float:
    try:
        return float(text)
    except ValueError as exc:
        raise AnalyserError(f"unparsable number {text!r} [{context}]") from exc


def parse_ledger_row(line: str, source: str) -> Fill:
    parts = line.rstrip("\n").split("|")
    if len(parts) != 21:
        raise AnalyserError(
            f"ledger row has {len(parts)} fields, expected 21 [{source}]: {line[:80]}"
        )

    def strip(index: int, prefix: str) -> str:
        value = parts[index].strip()
        if not value.startswith(prefix):
            raise AnalyserError(
                f"field {index} missing prefix {prefix!r} [{source}]: {value!r}"
            )
        return value[len(prefix):].strip()

    instrument, direction, ltf, fold = (p.strip() for p in parts[:4])
    if instrument not in INSTRUMENTS:
        raise AnalyserError(f"unexpected instrument {instrument!r} [{source}]")
    if direction not in DIRECTIONS:
        raise AnalyserError(f"unexpected direction {direction!r} [{source}]")
    if ltf not in LTFS:
        raise AnalyserError(f"unexpected LTF {ltf!r} [{source}]")

    outcome = parts[16].strip()
    if outcome not in OUTCOMES:
        raise AnalyserError(f"unexpected outcome {outcome!r} [{source}]")
    exit_reason = parts[19].strip()
    if exit_reason not in EXIT_REASONS:
        raise AnalyserError(f"unexpected exit reason {exit_reason!r} [{source}]")
    if outcome == "WIN" and exit_reason != "target":
        raise AnalyserError(
            f"ambiguous record: WIN with exit reason {exit_reason!r} [{source}]"
        )

    entry_ts = strip(13, "en ")
    return Fill(
        instrument=instrument, direction=direction, ltf=ltf, fold=fold,
        sweep_ts=strip(4, "sw "), sweep_kind=parts[5].strip(),
        sweep_extreme=_num(strip(6, "swX "), source),
        choch_ts=strip(7, "ch "), choch_level=_num(strip(8, "chL "), source),
        retest_ts=strip(9, "rt "),
        bos_ts=strip(10, "bos "), bos_level=_num(strip(11, "bosL "), source),
        fvg=strip(12, "fvg "),
        entry_ts=entry_ts, entry_price=_num(strip(14, "enPx "), source),
        stop_price=_num(strip(15, "stop "), source),
        outcome=outcome,
        r_multiple=_num(parts[17].strip().replace("R", ""), source),
        pnl_usd=_num(parts[18].strip().replace("$", ""), source),
        exit_reason=exit_reason,
        bars_in_trade=int(parts[20].strip().replace("bars", "")),
        entry_ts_ms=_ts(entry_ts, f"{source} entry"),
        source_file=source,
    )


@dataclass
class Cell:
    """One instrument x direction x LTF run."""

    instrument: str
    direction: str
    ltf: str
    fold: str
    source_file: str
    coverage_start: str
    coverage_end: str
    funnel: dict = field(default_factory=dict)
    asserts_raw: str = ""
    fills: list[Fill] = field(default_factory=list)

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.instrument, self.direction, self.ltf)


def parse_run_file(path: str | Path) -> Cell:
    """Parse one capture file. Every unrecognised line is an error."""
    path = Path(path)
    source = path.name
    funnel = funnel2 = perf = None
    fills: list[Fill] = []
    in_ledger = False

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if (m := _FUNNEL_RE.match(line)):
            funnel = m.groupdict()
        elif (m := _FUNNEL2_RE.match(line)):
            funnel2 = m.groupdict()
        elif (m := _PERF_RE.match(line)):
            perf = m.groupdict()
        elif line.startswith("LEDGER"):
            in_ledger = True
        elif _LEDGER_RE.match(line):
            if not in_ledger:
                raise AnalyserError(f"ledger row before LEDGER header [{source}]")
            fills.append(parse_ledger_row(line, source))
        elif line.startswith("NOTE") or line.startswith(" ") or line.startswith("#"):
            continue
        else:
            raise AnalyserError(f"unrecognised line [{source}]: {line[:90]!r}")

    for name, value in (("FUNNEL", funnel), ("FUNNEL cont.", funnel2), ("PERF", perf)):
        if value is None:
            raise AnalyserError(f"missing {name} line [{source}]")

    instrument = perf["inst"]
    if instrument not in INSTRUMENTS:
        raise AnalyserError(f"unexpected instrument {instrument!r} [{source}]")
    if perf["dir"] != funnel["dir"] or perf["ltf"] != funnel["ltf"]:
        raise AnalyserError(f"FUNNEL and PERF headers disagree [{source}]")

    declared = int(funnel["fills"])
    if declared != len(fills) or declared != int(perf["fills"]):
        raise AnalyserError(
            f"fill count disagreement [{source}]: funnel {declared}, "
            f"perf {perf['fills']}, ledger rows {len(fills)}"
        )

    for fill in fills:
        if (fill.instrument, fill.direction, fill.ltf) != (
            instrument, perf["dir"], perf["ltf"]
        ):
            raise AnalyserError(f"ledger row does not match its cell header [{source}]")

    counts = {
        "fold_bars": int(funnel["foldbars"]),
        "fold_bars_with_ltf": int(funnel["withltf"]),
        "ltf_bars": int(funnel["ltfbars"]) if funnel["ltfbars"] else None,
        "sweeps": int(funnel["sweeps"]), "choch": int(funnel["choch"]),
        "retests": int(funnel["retests"]), "bos_displacement": int(funnel["bos"]),
        "fvg": int(funnel["fvg"]), "fills": declared,
        "break_no_displacement": int(funnel2["bnd"]), "no_fvg": int(funnel2["nofvg"]),
        "r_band_rejects": int(funnel2["rband"]),
        "fvg_retest_expiry": int(funnel2["fvgexp"]),
        "expire_pre_choch": int(funnel2["e1"]),
        "expire_post_choch": int(funnel2["e2"]),
        "expire_post_retest": int(funnel2["e3"]),
        "dropped_no_slot": int(funnel2["dropped"]),
    }
    if counts["fvg"] != counts["fills"] + counts["r_band_rejects"] + counts["fvg_retest_expiry"]:
        raise AnalyserError(
            f"conservation identity fails [{source}]: FVG {counts['fvg']} != "
            f"fills {counts['fills']} + Rband {counts['r_band_rejects']} + "
            f"expiry {counts['fvg_retest_expiry']}"
        )
    if counts["dropped_no_slot"] != 0:
        raise AnalyserError(f"dropped (no slot) is non-zero [{source}]")

    asserts_raw = funnel2["asserts"].strip()
    if asserts_raw != "all 0" and any(int(v) for v in asserts_raw.split("/")):
        raise AnalyserError(f"assertion counters non-zero [{source}]: {asserts_raw}")

    return Cell(
        instrument=instrument, direction=perf["dir"], ltf=perf["ltf"],
        fold=perf["fold"], source_file=source,
        coverage_start=perf["start"], coverage_end=perf["end"],
        funnel=counts, asserts_raw=asserts_raw, fills=fills,
    )


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------

def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def binom_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))


def clopper_pearson(k: int, n: int, alpha: float = ALPHA) -> tuple[float, float]:
    """Exact (Clopper-Pearson) two-sided 1-alpha interval, by tail bisection.

    Pre-registered in PHASE16_PROTOCOL.md section 6. `lower` solves
    P(X >= k | p) = alpha/2 and `upper` solves P(X <= k | p) = alpha/2, with the
    degenerate ends pinned at 0 and 1. Deterministic to 1e-12.
    """
    if n <= 0:
        raise AnalyserError("Clopper-Pearson needs n > 0")
    if not 0 <= k <= n:
        raise AnalyserError(f"k={k} outside 0..{n}")
    half = alpha / 2.0

    def bisect(target, increasing: bool) -> float:
        low, high = 0.0, 1.0
        for _ in range(200):
            mid = (low + high) / 2.0
            value = target(mid)
            if (value < half) == increasing:
                low = mid
            else:
                high = mid
        return (low + high) / 2.0

    lower = 0.0 if k == 0 else bisect(lambda p: binom_sf(k, n, p), True)
    upper = 1.0 if k == n else bisect(lambda p: binom_cdf(k, n, p), False)
    return lower, upper


def critical_values(n: int, p: float = P_STAR, alpha: float = ALPHA) -> tuple[int | None, int | None]:
    """(supportive threshold, against threshold) at the realized N."""
    if n <= 0:
        return None, None
    supportive = next((k for k in range(n + 1) if binom_sf(k, n, p) <= alpha), None)
    against_candidates = [k for k in range(n + 1) if binom_cdf(k, n, p) <= alpha]
    return supportive, (max(against_candidates) if against_candidates else None)


def max_drawdown(values: list[float]) -> float:
    """Maximum peak-to-trough decline of the running cumulative sum."""
    cumulative = peak = drawdown = 0.0
    for value in values:
        cumulative += value
        peak = max(peak, cumulative)
        drawdown = max(drawdown, peak - cumulative)
    return drawdown


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------

def build_events(fills: list[Fill], identity: str) -> list[Event]:
    """Group fills by identity, preserving first-appearance order."""
    if identity not in ("primary", "alternative"):
        raise AnalyserError(f"unknown identity {identity!r}")
    order: list[tuple] = []
    groups: dict[tuple, list[Fill]] = {}
    for fill in fills:
        key = fill.primary_key if identity == "primary" else fill.alternative_key
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(fill)
    return [Event(key=k, identity=identity, fills=tuple(groups[k])) for k in order]


def event_stats(events: list[Event]) -> dict:
    total = len(events)
    wins = sum(1 for e in events if e.is_win)
    mixed = sum(1 for e in events if e.is_mixed)
    multi = [e for e in events if e.size > 1]
    fills_in_multi = sum(e.size for e in multi)
    total_fills = sum(e.size for e in events)
    stats = {
        "events": total,
        "winning_events": wins,
        "mixed_outcome_events": mixed,
        "multi_fill_events": len(multi),
        "largest_cluster": max((e.size for e in events), default=0),
        "fills_in_multi_fill_events": fills_in_multi,
        "share_fills_in_multi_fill_events": (
            round(fills_in_multi / total_fills, 6) if total_fills else 0.0
        ),
        "win_rate": round(wins / total, 6) if total else None,
    }
    if total:
        low, high = clopper_pearson(wins, total)
        stats["win_rate_ci95"] = [round(low, 6), round(high, 6)]
    else:
        stats["win_rate_ci95"] = None
    return stats


def analyse(cells: list[Cell], window: Window, artifact_path: str | None = None) -> dict:
    """Produce the full pre-registered report. Mechanical; selects nothing."""
    if not cells:
        raise AnalyserError("no cells supplied")

    seen = [c.key for c in cells]
    if len(seen) != len(set(seen)):
        raise AnalyserError(f"duplicate cell supplied: {sorted(seen)}")
    for key in seen:
        if key not in EXPECTED_CELLS:
            raise AnalyserError(f"unexpected cell {key}")

    fills: list[Fill] = []
    for cell in cells:
        fills.extend(cell.fills)
    for fill in fills:
        if not window.contains(fill.entry_ts_ms):
            raise AnalyserError(
                f"fill at {fill.entry_ts} is outside the {window.label} window "
                f"[{fill.source_file}]"
            )

    ordered = sorted(fills, key=lambda f: (f.exit_ts_ms, f.instrument, f.direction,
                                           f.ltf, f.entry_ts_ms, f.entry_price))
    execution = {
        "fills": len(fills),
        "wins": sum(1 for f in fills if f.outcome == "WIN"),
        "losses": sum(1 for f in fills if f.outcome == "LOSS"),
        "stops": sum(1 for f in fills if f.exit_reason == "stop"),
        "targets": sum(1 for f in fills if f.exit_reason == "target"),
        "timeouts": sum(1 for f in fills if f.exit_reason == "timeout"),
        "total_r": round(sum(f.r_multiple for f in fills), 6),
        "mean_r": round(sum(f.r_multiple for f in fills) / len(fills), 6) if fills else None,
        "total_usd": round(sum(f.pnl_usd for f in fills), 6),
        "max_drawdown_r": round(max_drawdown([f.r_multiple for f in ordered]), 6),
        "max_drawdown_usd": round(max_drawdown([f.pnl_usd for f in ordered]), 6),
        "drawdown_ordering": "by derived exit time (entry + bars x 5m), then cell, then entry",
    }
    if fills:
        low, high = clopper_pearson(execution["wins"], len(fills))
        execution["win_rate"] = round(execution["wins"] / len(fills), 6)
        execution["win_rate_ci95"] = [round(low, 6), round(high, 6)]
    else:
        execution["win_rate"] = None
        execution["win_rate_ci95"] = None

    primary = build_events(fills, "primary")
    alternative = build_events(fills, "alternative")

    funnel_total: dict[str, int] = {}
    for cell in cells:
        for name, value in cell.funnel.items():
            if value is None:
                continue
            funnel_total[name] = funnel_total.get(name, 0) + value
    if funnel_total.get("fills", 0) != len(fills):
        raise AnalyserError(
            f"funnel fills {funnel_total.get('fills')} != ledger rows {len(fills)}"
        )

    report = {
        "analyser": {
            "file": "trader_v2/p16/p16_analyze.py",
            "version": ANALYSER_VERSION,
            "sha256": file_sha256(__file__),
        },
        "window": {
            "label": window.label, "is_oos": window.is_oos,
            "start_ms": window.start_ms, "end_ms": window.end_ms,
            "start_utc": _fmt(window.start_ms), "end_utc": _fmt(window.end_ms),
        },
        "cells": [
            {
                "instrument": c.instrument, "direction": c.direction, "ltf": c.ltf,
                "fold_label": c.fold, "source_file": c.source_file,
                "coverage": [c.coverage_start, c.coverage_end],
                "funnel": c.funnel, "asserts": c.asserts_raw,
                "fills": len(c.fills),
            }
            for c in sorted(cells, key=lambda c: c.key)
        ],
        "cells_present": len(cells),
        "cells_expected": len(EXPECTED_CELLS),
        "funnel_total": funnel_total,
        "execution_level": execution,
        "primary_identity": event_stats(primary),
        "alternative_identity": event_stats(alternative),
        "event_outcome_rule": (
            "an event is a WIN only if EVERY fill in it is a WIN (exit reason "
            "'target'); any LOSS, any timeout or any mixture is NON-WIN "
            "(PHASE16_PROTOCOL.md section 5)"
        ),
        "hypothesis": {
            "p_star": P_STAR, "alpha": ALPHA,
            "alternative_p1": P1_ALTERNATIVE, "min_events": MIN_EVENTS,
            "primary_unit": "alternative-identity events",
            "family_wise_note": (
                "two one-sided tests at alpha=0.05 each; each verdict is "
                "controlled at 5%, the probability of some rejection under H0 "
                "is up to 10%"
            ),
        },
    }
    if artifact_path:
        report["artifact"] = verify_artifact(artifact_path)

    n = report["alternative_identity"]["events"]
    k = report["alternative_identity"]["winning_events"]
    supportive, against = critical_values(n)
    report["test"] = {
        "n_events": n, "winning_events": k,
        "supportive_threshold": supportive, "against_threshold": against,
        "p_value_upper": round(binom_sf(k, n, P_STAR), 8) if n else None,
        "p_value_lower": round(binom_cdf(k, n, P_STAR), 8) if n else None,
        "power_vs_p1": round(binom_sf(supportive, n, P1_ALTERNATIVE), 6)
        if (n and supportive is not None) else None,
    }
    report["decision"] = decide(report)
    return report


def decide(report: dict) -> dict:
    """The pre-registered three-way verdict. Refuses on a non-OOS window."""
    if not report["window"]["is_oos"]:
        return {
            "verdict": "NOT APPLICABLE",
            "reason": (
                f"window {report['window']['label']!r} is not the pre-registered "
                f"OOS window; no Phase 16 verdict may be produced from it"
            ),
        }
    n = report["test"]["n_events"]
    k = report["test"]["winning_events"]
    supportive = report["test"]["supportive_threshold"]
    against = report["test"]["against_threshold"]

    if n < MIN_EVENTS:
        return {
            "verdict": "EVIDENCE INSUFFICIENT / INCONCLUSIVE",
            "reason": (
                f"realized alternative events {n} < power floor {MIN_EVENTS}; "
                f"the primary test is not run, in either direction"
            ),
        }
    if supportive is not None and k >= supportive:
        return {
            "verdict": "EVIDENCE SUPPORTIVE OF AN EDGE",
            "reason": f"{k} winning events >= threshold {supportive} at N={n}",
            "caveat": (
                "powered against a large edge (p1=0.30) only; must also survive "
                "the breakdown check in protocol section 7.1, which is reported, "
                "not applied by removing anything"
            ),
        }
    if against is not None and k <= against:
        return {
            "verdict": "EVIDENCE AGAINST AN EDGE",
            "reason": f"{k} winning events <= threshold {against} at N={n}",
        }
    return {
        "verdict": "EVIDENCE INSUFFICIENT / INCONCLUSIVE",
        "reason": (
            f"{k} winning events at N={n} rejects H0 in neither direction; "
            f"failure to reject means 'no large edge detected', never 'no edge'"
        ),
    }


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_artifact(path: str | Path) -> dict:
    """Hard-check the execution artifact's hash. Raises on mismatch."""
    actual = file_sha256(path)
    if actual != ARTIFACT_SHA:
        raise AnalyserError(
            f"artifact SHA mismatch for {path}: got {actual}, expected "
            f"{ARTIFACT_SHA}. Protocol section 8 invalidates the accumulation "
            f"period on any change to this file."
        )
    return {"path": str(path), "sha256": actual, "expected": ARTIFACT_SHA, "match": True}


def _fmt(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M")


def dumps(report: dict) -> str:
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 16 analyser (pre-registered). Read-only."
    )
    parser.add_argument("run_files", nargs="+", help="Phase 16 capture files")
    parser.add_argument("--artifact", default=ARTIFACT_PATH,
                        help="execution artifact whose SHA-256 is asserted")
    args = parser.parse_args(argv[1:])
    cells = [parse_run_file(p) for p in args.run_files]
    print(dumps(analyse(cells, Window.oos(), artifact_path=args.artifact)), end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except AnalyserError as exc:
        print(f"ANALYSER HARD STOP: {exc}", file=sys.stderr)
        raise SystemExit(2)

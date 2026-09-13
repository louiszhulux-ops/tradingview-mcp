"""Render a Gate 1 run as `bot/reports/gate1.md`.

Deterministic apart from the two pieces of run metadata it records explicitly:
the run timestamp and the repository commit. Everything else — cell order, row
order, counter order, divergence order — is fixed by the modules that produce
it, so two runs at the same commit differ only in those two lines.

The report never states a PASS or a FAIL for the gate when the evidence does
not support one. `NOT ADJUDICABLE` is printed as itself.
"""

from __future__ import annotations

import sys
from pathlib import Path

from bot.replay.compare import (
    ASSERTIONS_MUST_BE_ZERO, ASSERTIONS_NOT_APPLICABLE, BEHAVIOUR_COUNTERS,
    COVERAGE_COUNTERS, DERIVED_LABEL, DERIVED_NO_COMPARAND, EXCLUDED_COUNTERS,
    NOT_APPLICABLE_LABEL,
)
from bot.replay.datasets import REPO_ROOT
from bot.replay.harness import CellRun, Gate1Run, run_gate1
from bot.replay.verdicts import PRECEDENCE, CellVerdict, GateResult

REPORT_PATH = REPO_ROOT / "bot" / "reports" / "gate1.md"

_WHY = {
    CellVerdict.NO_DATA:
        "a required input series does not exist in the repository",
    CellVerdict.PRECONDITION_FAIL:
        "the input series does not reproduce the recorded run's coverage; "
        "the engine was not started",
    CellVerdict.PROVISIONAL_PASS:
        "the comparison was clean, but the dataset is CANDIDATE and cannot "
        "carry a gate-passing verdict",
    CellVerdict.PROVISIONAL_FAIL:
        "the comparison diverged on CANDIDATE data, which names no defendant",
    CellVerdict.SOURCE_TRUNCATED:
        "compared on counters only under A2 §5",
    CellVerdict.PASS: "clean comparison on AUTHORITATIVE data",
    CellVerdict.FAIL: "the engine diverged on AUTHORITATIVE data",
}


def _cell_section(run: CellRun) -> list[str]:
    cell, result = run.cell, run.result
    out = [
        f"### {cell.cell_id} — `{result.verdict.value}`",
        "",
        f"- **verdict** `{result.verdict.value}` — {_WHY[result.verdict]}",
        f"- **dataset status** `{result.status.value}`",
        f"- **engine ran** {'yes' if run.engine_ran else 'NO'}",
        f"- **comparison mode** "
        f"{run.comparison.mode if run.comparison else 'not reached'}",
        "",
    ]
    if run.error:
        out += ["```", run.error, "```", ""]

    out.append("**Dataset provenance**")
    out.append("")
    out.append("```")
    out += list(run.dataset.provenance_lines()) if run.dataset else ["  (not resolved)"]
    out += ["```", ""]

    out.append("**Coverage precondition**")
    out.append("")
    out.append("```")
    if run.coverage is not None:
        out += list(run.coverage.report_lines())
    else:
        out.append("  not evaluated — the cell had no dataset to count")
    out += ["```", ""]

    out.append("**Behaviour counters**")
    out.append("")
    if run.funnel is None:
        out += ["_not produced — the engine did not run._", ""]
    else:
        out += ["| counter | expected | actual |", "|---|---|---|"]
        from bot.fixtures.loader import load_fixture
        expected = load_fixture(cell.fixture_id)["funnel"]
        for name in BEHAVIOUR_COUNTERS:
            mark = "" if expected[name] == run.funnel[name] else "  **MISMATCH**"
            out.append(f"| `{name}` | {expected[name]} | {run.funnel[name]}{mark} |")
        out.append("")
        out.append("Not parity counters:")
        out.append("")
        for name in COVERAGE_COUNTERS:
            out.append(f"- `{name}` = {run.funnel[name]} — input precondition, "
                       f"checked before the engine ran")
        for name in EXCLUDED_COUNTERS:
            out.append(f"- `{name}` = {run.funnel[name]} — chart-wide, not "
                       f"fold-scoped; informational only, never compared")
        out.append("")

    out.append("**Assertion counters**")
    out.append("")
    if run.assertions is None:
        out.append("_not produced — the engine did not run._")
    else:
        for index in ASSERTIONS_MUST_BE_ZERO:
            value = run.assertions[index]
            out.append(f"- `K{index}` = {value}"
                       f"{'' if value == 0 else '  **NON-ZERO — FAILURE**'}")
    for index in ASSERTIONS_NOT_APPLICABLE:
        out.append(f"- `K{index}` — **{NOT_APPLICABLE_LABEL}**: it cross-checks "
                   f"V53's hand-rolled pivot against Pine's built-in, and Python "
                   f"has no built-in comparand. A structurally absent check is "
                   f"not a passing check.")
    out.append("")

    out.append("**Ledger comparison**")
    out.append("")
    out.append("```")
    if run.comparison is None:
        out.append("  not reached")
    else:
        out += list(run.comparison.report_lines())
    out += ["```", ""]

    out.append("**Derived diagnostics**")
    out.append("")
    for name in DERIVED_NO_COMPARAND:
        out.append(f"- `{name}` — {DERIVED_LABEL}; computed by the engine, "
                   f"never compared, never affecting this verdict")
    out.append("")
    return out


def render(run: Gate1Run) -> str:
    report = run.report
    census = report.census
    lines = [
        "# Gate 1 report",
        "",
        "**Generated by `bot/replay/report.py`. Do not edit by hand.**",
        "",
        f"- **run timestamp** {run.started_utc}",
        f"- **repository commit** `{run.commit}`",
        f"- **cells evaluated** {run.cells_evaluated} of 24",
        f"- **acceptance model** `bot/GATE1_ACCEPTANCE.md`",
        "",
        "---",
        "",
        "## Result",
        "",
        f"# {report.result.value}",
        "",
    ]

    if report.result is GateResult.NOT_ADJUDICABLE_INSUFFICIENT:
        lines += [
            "Gate 1 has **not** passed and has **not** failed. Neither verdict is "
            "available on the evidence in this repository, and the gate says so "
            "rather than rounding to one of them.",
            "",
            "Gate 1 passes if and only if all 24 cells are `PASS` or "
            "`SOURCE-TRUNCATED`. No cell reached either, for three distinct "
            "reasons that the repaired vocabulary keeps separate:",
            "",
            f"- **{census[CellVerdict.NO_DATA]} cells `NO-DATA`** — the 3m series "
            "does not exist in the repository. Not a truncation downgrade: the "
            "run cannot be attempted at all, so there is nothing to compare, on "
            "counters or otherwise.",
            f"- **{census[CellVerdict.PRECONDITION_FAIL]} cells "
            "`PRECONDITION-FAIL`** — 1m fold A. The input series does not "
            "reproduce the recorded `fold_bars_with_ltf`, so the engine was "
            "never started. This is a hole in the data, and reporting it as a "
            "strategy divergence would blame the engine for it.",
            f"- **{census[CellVerdict.PROVISIONAL_PASS]} cells "
            "`PROVISIONAL-PASS`** — 1m folds B and C. These ran to completion "
            "and compared clean, but every one of them sits on a `CANDIDATE` "
            "dataset, which cannot carry a gate-passing verdict.",
            "",
            "**A clean comparison on candidate data is not parity with V53.** "
            "No historical LTF value artifact was ever recorded, so the values "
            "V53 consumed in 2026 cannot be recovered for comparison, and no "
            "rerun may manufacture them. Nothing in this report should be read "
            "as validating the strategy or the engine.",
            "",
        ]
    elif report.result is GateResult.NOT_ADJUDICABLE_DIVERGENCE:
        diverged = [c.cell_id for c in report.cells_with(CellVerdict.PROVISIONAL_FAIL)]
        lines += [
            "Gate 1 has **not** passed and has **not** failed.",
            "",
            f"{len(diverged)} cell(s) diverged on a `CANDIDATE` dataset: "
            + ", ".join(f"`{cid}`" for cid in diverged) + ".",
            "",
            "**A divergence on candidate data names no defendant.** Neither the "
            "engine nor the dataset is established, so the difference could be "
            "either, and the gate refuses to guess. This is not a `FAIL` — that "
            "verdict is reserved for a divergence against an `AUTHORITATIVE` "
            "dataset — and it is emphatically not a pass. **It may not be closed "
            "by re-running.** It requires a written disposition naming the first "
            "divergent bar and slot, recorded in the per-cell detail below.",
            "",
            "The remaining cells are blocked for reasons the vocabulary keeps "
            "separate:",
            "",
            f"- **{census[CellVerdict.NO_DATA]} cells `NO-DATA`** — the 3m series "
            "does not exist in the repository. Not a truncation downgrade: the "
            "run cannot be attempted at all.",
            f"- **{census[CellVerdict.PRECONDITION_FAIL]} cells "
            "`PRECONDITION-FAIL`** — 1m fold A. The input does not reproduce the "
            "recorded `fold_bars_with_ltf`, so the engine was never started.",
            f"- **{census[CellVerdict.PROVISIONAL_PASS]} cells "
            "`PROVISIONAL-PASS`** — compared clean, but on `CANDIDATE` data, "
            "which cannot carry a gate-passing verdict.",
            "",
            "**A clean comparison on candidate data is not parity with V53.** No "
            "historical LTF value artifact was ever recorded, so the values V53 "
            "consumed cannot be recovered for comparison, and no rerun may "
            "manufacture them. Nothing in this report validates the strategy or "
            "the engine.",
            "",
        ]

    for note in report.notes:
        lines += [f"> {note}", ""]

    lines += ["## Census", "", "| verdict | cells |", "|---|---|"]
    for verdict in PRECEDENCE:
        lines.append(f"| `{verdict.value}` | {census[verdict]} |")
    lines += ["", "## Cell verdicts", "",
              "| cell | verdict | status | engine ran | reason |",
              "|---|---|---|---|---|"]
    for cell_run in run.runs:
        lines.append(
            f"| `{cell_run.cell.cell_id}` | `{cell_run.result.verdict.value}` | "
            f"`{cell_run.result.status.value}` | "
            f"{'yes' if cell_run.engine_ran else 'no'} | "
            f"{cell_run.result.reason} |")
    lines += ["", "---", "", "## Per-cell detail", ""]
    for cell_run in run.runs:
        lines += _cell_section(cell_run)
        lines += ["---", ""]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    run = run_gate1()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render(run), encoding="utf-8")
    print(run.report.result.value)
    for verdict in PRECEDENCE:
        count = run.report.census[verdict]
        if count:
            print(f"  {verdict.value:<20} {count}")
    print(f"report: {REPORT_PATH}")
    return 0 if run.report.result is not GateResult.FAIL else 1


if __name__ == "__main__":
    raise SystemExit(main())

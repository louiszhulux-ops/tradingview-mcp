#!/usr/bin/env python3
"""Static guard check for the bot/ tree.

Run with no arguments to check the repository's own ``bot/`` tree:

    python3 bot/tools/check_guards.py

Exits non-zero and prints every violation if any check fails. Four checks:

1. **No Phase 16 dependency.** No file under ``bot/`` may reference the
   Phase 16 research tree, its protocol/derivation/audit files, or its
   out-of-sample build artifact.

2. **Single FE definition.** The Phase 16 boundary literal may appear only in
   ``bot/guards.py``. Anywhere else it is a second, drift-prone definition.

3. **Loaders require the guard.** Every module under ``bot/data/`` and
   ``bot/fixtures/`` must import from ``bot.guards``, so no data path can be
   written that silently accepts a post-FE timestamp.

4. **No live TradingView data in development code.** Files under ``bot/tests/``
   and ``bot/fixtures/`` may not reference the MCP/CDP chart surface. Live
   chart reads return *recent* bars, which are inside the Phase 16 window.
   (This check is deliberately scoped to development/test paths. A production
   data adapter — roadmap task D2 — legitimately talks to that surface and is
   governed by its own Phase 16 interlock, not by this check.)

**Escape hatch.** A line carrying the allow marker (see ``ALLOW_MARKER``
below) is exempt from checks 1, 2 and 4. Every such line is printed in this tool's output, so
exemptions are visible rather than silent. Use it only for pattern definitions
(this file) and negative-test fixtures.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOW_MARKER = "GUARD-ALLOW"

# --- check 1 -----------------------------------------------------------------
# Phase 16 artifacts. Note the research tree as a whole is NOT forbidden:
# roadmap task A2 legitimately reads the already-consumed fold A/B/C run files.
PHASE16_PATTERNS: list[tuple[str, str]] = [
    (r"trader_v2[/\\.]p16", "Phase 16 tree"),                     # GUARD-ALLOW: pattern definition
    (r"\bp16[/\\.]", "Phase 16 tree"),                            # GUARD-ALLOW: pattern definition
    (r"PHASE16_PROTOCOL", "Phase 16 protocol"),                   # GUARD-ALLOW: pattern definition
    (r"P16_DERIVATION_AUDIT", "Phase 16 derivation audit"),       # GUARD-ALLOW: pattern definition
    (r"V53_P16_OOS_BUILD", "Phase 16 OOS build artifact"),        # GUARD-ALLOW: pattern definition
    (r"(derive|verify)_p16_oos", "Phase 16 derivation script"),   # GUARD-ALLOW: pattern definition
    (r"\bOOS\b", "out-of-sample dataset reference"),              # GUARD-ALLOW: pattern definition
]

# --- check 2 -----------------------------------------------------------------
FE_LITERAL = re.compile(r"\b1788134400000\b")  # GUARD-ALLOW: pattern definition
FE_HOME = "guards.py"

# --- check 3 -----------------------------------------------------------------
GUARDED_DIRS = ("data", "fixtures")
GUARD_IMPORT = re.compile(r"from\s+(bot\.guards|\.+guards)\s+import|import\s+bot\.guards")

# --- check 4 -----------------------------------------------------------------
DEV_DIRS = ("tests", "fixtures")
LIVE_TV_PATTERNS: list[tuple[str, str]] = [
    (r"mcp__f__", "MCP TradingView tool"),                        # GUARD-ALLOW: pattern definition
    (r"remote-debugging-port", "CDP launch flag"),                # GUARD-ALLOW: pattern definition
    (r"\b9222\b", "CDP port"),                                    # GUARD-ALLOW: pattern definition
    (r"\bchart_get_\w+", "live chart read"),                      # GUARD-ALLOW: pattern definition
    (r"\bdata_get_\w+", "live chart read"),                       # GUARD-ALLOW: pattern definition
    (r"\bquote_get\b", "live quote read"),                        # GUARD-ALLOW: pattern definition
    (r"\btv_(launch|health_check|discover)\b", "TradingView control"),  # GUARD-ALLOW: pattern definition
]


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _in_dir(rel: str, names: tuple[str, ...]) -> bool:
    parts = Path(rel).parts
    return len(parts) > 1 and parts[0] in names


def check(root: Path) -> tuple[list[str], list[str]]:
    """Return (violations, allow_marked_lines) for the tree at ``root``."""
    violations: list[str] = []
    allowed: list[str] = []

    files = sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)

    for path in files:
        rel = _rel(path, root)
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        imports_guard = bool(GUARD_IMPORT.search(text))

        for lineno, line in enumerate(lines, 1):
            if ALLOW_MARKER in line:
                allowed.append(f"{rel}:{lineno}: {line.strip()}")
                continue

            for pattern, label in PHASE16_PATTERNS:
                if re.search(pattern, line):
                    violations.append(
                        f"{rel}:{lineno}: forbidden Phase 16 dependency "
                        f"({label}) matching /{pattern}/"
                    )

            if FE_LITERAL.search(line) and path.name != FE_HOME:
                violations.append(
                    f"{rel}:{lineno}: FE boundary literal outside bot/{FE_HOME}; "
                    f"import FE_MS from bot.guards instead"
                )

            if _in_dir(rel, DEV_DIRS):
                for pattern, label in LIVE_TV_PATTERNS:
                    if re.search(pattern, line):
                        violations.append(
                            f"{rel}:{lineno}: live TradingView data reference "
                            f"({label}) in development code matching /{pattern}/"
                        )

        if _in_dir(rel, GUARDED_DIRS) and path.name != "__init__.py" and not imports_guard:
            violations.append(
                f"{rel}: data/fixture module does not import from bot.guards; "
                f"every loader must apply assert_pre_fe"
            )

    return violations, allowed


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[1]
    if not root.is_dir():
        print(f"check_guards: no such directory: {root}", file=sys.stderr)
        return 2

    violations, allowed = check(root)

    if allowed:
        print(f"check_guards: {len(allowed)} {ALLOW_MARKER} exemption(s) in {root}:")
        for entry in allowed:
            print(f"  - {entry}")

    if violations:
        print(f"\ncheck_guards: FAIL — {len(violations)} violation(s):", file=sys.stderr)
        for entry in violations:
            print(f"  ! {entry}", file=sys.stderr)
        return 1

    print(f"check_guards: PASS — {root} is clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

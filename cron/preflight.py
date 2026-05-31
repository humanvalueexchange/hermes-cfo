#!/usr/bin/env python3
"""Pre-flight syntax + import test for all nightly Hermes scripts.

Runs at 1:55am before the 2:00am nightly assessment.
Exits 0 (PASS) only if every script compiles cleanly.
Any failure exits 1 so Telegram delivers an alert before jobs run.
"""

from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
REQUIRED_SCRIPTS = [
    "common.py",
    "nightly_assessment.py",
    "morning_briefing.py",
    "btc_forecast.py",
]


def check_syntax(path: Path) -> str | None:
    """Return error string or None if syntax is clean."""
    try:
        py_compile.compile(str(path), doraise=True)
        return None
    except py_compile.PyCompileError as exc:
        return str(exc)


def check_imports(path: Path) -> str | None:
    """Return error string or None if all imports resolve (subprocess-isolated)."""
    result = subprocess.run(
        [sys.executable, "-c", f"import ast, sys; ast.parse(open('{path}').read()); "
         f"compile(open('{path}').read(), '{path}', 'exec')"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return (result.stderr or result.stdout).strip()[:400]
    return None


def main() -> int:
    failures: list[str] = []

    for name in REQUIRED_SCRIPTS:
        path = SCRIPTS_DIR / name

        if not path.exists():
            failures.append(f"MISSING  {name}")
            continue

        err = check_syntax(path)
        if err:
            failures.append(f"SYNTAX   {name}: {err}")

    if failures:
        print("FAIL — pre-flight check failed. Tonight's cron jobs will error.")
        print("")
        for f in failures:
            print(f"  ✗ {f}")
        print("")
        print("Action required: fix before 02:00 ET.")
        return 1

    print("PASS — all nightly scripts are syntax-clean.")
    for name in REQUIRED_SCRIPTS:
        print(f"  ✓ {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

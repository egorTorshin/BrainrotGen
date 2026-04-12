#!/usr/bin/env python3
"""
Fail if any function/method has cyclomatic complexity >= *max* (default 10).

QP requires complexity strictly below 10 per function; ``radon cc --min C`` only
flags rank C+ (typically CC >= 11), so rank B with CC exactly 10 would pass.
This script parses ``radon cc -j`` and enforces the numeric ceiling.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def max_complexity(radon_json: dict) -> tuple[int, str | None, str | None]:
    """Return (max_cc, location_path, name) from radon cc -j output."""
    max_cc = 0
    worst_loc = None
    worst_name = None
    for path, blocks in radon_json.items():
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict):
                continue
            cc = block.get("complexity")
            if cc is None:
                continue
            cc = int(cc)
            if cc > max_cc:
                max_cc = cc
                line = block.get("lineno", "?")
                worst_loc = f"{path}:{line}"
                worst_name = block.get("name", "?")
    return max_cc, worst_loc, worst_name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="+",
        type=Path,
        help="Files or directories to analyze (passed to radon cc -j)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=10,
        metavar="N",
        help="Fail if any block has complexity >= N (default: 10)",
    )
    args = parser.parse_args()

    radon_targets = [str(p) for p in args.path]
    proc = subprocess.run(
        [sys.executable, "-m", "radon", "cc", "-j", *radon_targets],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout, file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        return proc.returncode

    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as e:
        print(f"Invalid radon JSON: {e}", file=sys.stderr)
        return 1

    max_cc, worst_loc, worst_name = max_complexity(data)
    if max_cc >= args.max:
        print(
            f"::error::Cyclomatic complexity {max_cc} >= {args.max} "
            f"at {worst_loc} ({worst_name})",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK: max cyclomatic complexity {max_cc} < {args.max} "
        f"({', '.join(radon_targets)})",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

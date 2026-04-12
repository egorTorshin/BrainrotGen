#!/usr/bin/env python3
"""
Local quality checks aligned with .github/workflows/ci.yml (without pytest).

Pre-commit scope is black / flake8 / bandit; CI also runs radon — included here.
Run full test suites in CI or manually: ``poetry run pytest`` in backend/ and worker/.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MI_BAD = re.compile(r"^\s*\S+ - [CDF]", re.MULTILINE)


def _clean_env_for_poetry_subprocess() -> dict[str, str]:
    """
    Environment for ``poetry run`` in backend/worker/frontend.

    Pre-commit runs this script inside its own virtualenv (``language: python``).
    If ``VIRTUAL_ENV`` is inherited, Poetry can pick the wrong interpreter and
    fail to find ``black``, ``flake8``, etc. in the subproject venv.
    """
    env = os.environ.copy()
    for key in (
        "VIRTUAL_ENV",
        "PYTHONHOME",
        "__PYVENV_LAUNCHER__",
    ):
        env.pop(key, None)
    return env


def _poetry_cmd(*parts: str) -> list[str]:
    """Invoke Poetry via the same interpreter as this script (Windows-friendly)."""
    return [sys.executable, "-m", "poetry", *parts]


def _ensure_poetry_available() -> None:
    """Fail fast with a clear message if Poetry cannot be run."""
    try:
        proc = subprocess.run(
            _poetry_cmd("--version"),
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            env=_clean_env_for_poetry_subprocess(),
        )
    except OSError as e:
        raise SystemExit(
            "Cannot run Poetry. Install it (https://python-poetry.org/docs/#installation) "
            "or use a pre-commit hook venv that includes the ``poetry`` package.",
        ) from e
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise SystemExit(
            "Poetry is not available for this Python interpreter.\n"
            f"{stderr}\n"
            "Install: pip install pre-commit && pre-commit install "
            "(hook bundles poetry) or: pip install poetry",
        )


def run_poetry(args: list[str], cwd: Path) -> None:
    cmd = _poetry_cmd(*args)
    print(f"+ ({cwd.relative_to(ROOT)}) {' '.join(cmd)}")
    subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        env=_clean_env_for_poetry_subprocess(),
    )


def check_radon_cc_strict(cwd: Path, *rel_paths: str) -> None:
    """Enforce max cyclomatic complexity < 10 (see scripts/check_radon_cc_threshold.py)."""
    script = ROOT / "scripts" / "check_radon_cc_threshold.py"
    cmd = _poetry_cmd("run", "python", str(script), *rel_paths)
    print(f"+ ({cwd.relative_to(ROOT)}) {' '.join(cmd)}")
    subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        env=_clean_env_for_poetry_subprocess(),
    )


def check_radon_mi(cwd: Path, *paths: str) -> None:
    proc = subprocess.run(
        _poetry_cmd("run", "radon", "mi", "-s", *paths),
        cwd=cwd,
        capture_output=True,
        text=True,
        env=_clean_env_for_poetry_subprocess(),
    )
    if proc.returncode != 0:
        print(proc.stdout or "", file=sys.stderr)
        print(proc.stderr or "", file=sys.stderr)
        proc.check_returncode()
    if MI_BAD.search(proc.stdout):
        print(proc.stdout, file=sys.stderr)
        raise SystemExit(
            "Maintainability Index below threshold (grade C/D/F found)",
        )


def backend_checks() -> None:
    d = ROOT / "backend"
    run_poetry(["run", "black", "--check", "src/", "tests/"], d)
    run_poetry(["run", "flake8", "src/"], d)
    check_radon_cc_strict(d, "src/")
    check_radon_mi(d, "src/")
    run_poetry(["run", "bandit", "-r", "src/", "-ll"], d)


def worker_checks() -> None:
    d = ROOT / "worker"
    run_poetry(["run", "black", "--check", "src/", "tests/"], d)
    run_poetry(["run", "flake8", "src/"], d)
    check_radon_cc_strict(d, "src/")
    check_radon_mi(d, "src/")
    run_poetry(["run", "bandit", "-r", "src/", "-ll"], d)


def frontend_checks() -> None:
    d = ROOT / "frontend"
    files = ["app.py", "api.py", "duration.py", "state.py"]
    run_poetry(["run", "black", "--check", *files], d)
    run_poetry(["run", "flake8", *files], d)
    check_radon_cc_strict(d, *files)
    check_radon_mi(d, *files)
    run_poetry(["run", "bandit", "-ll", *files], d)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-pytest",
        action="store_true",
        help="Also run pytest in backend/ and worker/ (slower; CI always runs these).",
    )
    args = parser.parse_args()

    os.chdir(ROOT)
    _ensure_poetry_available()
    backend_checks()
    worker_checks()
    frontend_checks()

    if args.with_pytest:
        run_poetry(["run", "pytest"], ROOT / "backend")
        run_poetry(["run", "pytest"], ROOT / "worker")

    print("OK: pre-commit quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

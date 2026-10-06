"""Run the tests your change can break, in parallel (2026-10-05). land.ps1 runs its tests through here.

    python scripts/run_tests.py               # what the edits on disk can break, uncommitted ones included
    python scripts/run_tests.py --full        # everything
    python scripts/run_tests.py -- -x -k dossier   # anything after -- goes to pytest as is

A Preview edit runs Preview's tests, Preview's golden slice and the core every view shares (the
build, lint, syntax, budgets), about 15 s; a bare `pytest` runs all of it, one test at a time.
scripts/impact.py picks the files: a path no area claims, shared CSS or shared test setup still
runs everything. Exits with pytest's code.
"""
import argparse
import importlib.util
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import impact  # noqa: E402


def parallel(extra):
    """xdist flags, or none: --update-golden rewrites one file from every area, so it runs alone."""
    if "--update-golden" in extra:
        return []
    if importlib.util.find_spec("xdist") is None:
        print("  pytest-xdist missing (pip install pytest-xdist) -- running serially", file=sys.stderr)
        return []
    return ["-n", "auto", "--dist", "loadgroup"]


def selection(pick):
    """pytest arguments for impact.select's answer: the files and the golden areas, or nothing for all."""
    if pick["all"]:
        print(f"  whole suite: {'; '.join(pick['why'])}")
        return []
    args = list(pick["files"])
    if pick["areas"]:
        args += ["--areas", ",".join(pick["areas"])]
    return args


def command(full, base, committed, extra):
    picked = []
    if not full:
        paths, golden = impact.changed(base, worktree=not committed)
        picked = selection(impact.select(paths, golden=golden))
    return [sys.executable, "-m", "pytest", *parallel(extra), *picked, *extra]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    ours = argv[:argv.index("--")] if "--" in argv else argv
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--full", action="store_true", help="every test, not only what the change can break")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--committed", action="store_true", help="HEAD only, not the files on disk (land.ps1)")
    ap.add_argument("--dry-run", action="store_true", help="print the pytest command, run nothing")
    a = ap.parse_args(ours)
    cmd = command(a.full, a.base, a.committed, extra)
    print("  python -m pytest " + " ".join(cmd[3:]), flush=True)
    if a.dry_run:
        return 0
    return subprocess.run(cmd, cwd=ROOT).returncode


if __name__ == "__main__":
    sys.exit(main())

"""The weekly flake run caps its pytest workers (2026-10-23: `-n auto` took 20 workers and ~190 browsers)."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAX_WORKERS = 8


def test_flake_args_pin_a_worker_count_of_at_most_eight():
    args = json.loads((ROOT / ".testing.json").read_text())["flake"]["args"]
    n = args[args.index("-n") + 1]
    assert n.isdigit(), f"-n {n!r} is not a fixed count"
    assert 1 <= int(n) <= MAX_WORKERS

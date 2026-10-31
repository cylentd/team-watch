"""The flake run and the Actions full run cap their pytest workers (2026-10-23: `-n auto` took 20 workers and ~190 browsers)."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAX_WORKERS = 8


def test_flake_args_pin_a_worker_count_of_at_most_eight():
    args = json.loads((ROOT / ".testing.json").read_text())["flake"]["args"]
    n = args[args.index("-n") + 1]
    assert n.isdigit(), f"-n {n!r} is not a fixed count"
    assert 1 <= int(n) <= MAX_WORKERS


def test_the_full_run_on_actions_pins_a_worker_count_of_at_most_eight():
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text()
    pinned = re.search(r"run_tests\.py --full -- .*-n (\d+)", workflow)
    assert pinned, "the full run leaves its workers to loadgate's 8-worker default"
    assert 1 <= int(pinned[1]) <= MAX_WORKERS

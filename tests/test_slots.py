"""scripts/worker_slots.py: the machine-wide worker budget (2026-10-07).

The decision is a pure function of the state dir, so every case runs on a tmp dir with a fake
`alive`: no pytest spawned, no real processes. The two-claims-at-once case uses threads with distinct pids.
"""
import json
import os
import pathlib
import sys
import threading
import time

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import worker_slots as slots  # noqa: E402

BUDGET = 14


def everyone_alive(rec):
    return True


def only(*pids):
    return lambda rec: rec["pid"] in pids


def hold(state, pid, workers, worktree="other"):
    """A claim file as another run would have left it."""
    path = pathlib.Path(state) / f"{pid:020d}-{pid}.claim"
    path.write_text(json.dumps({"pid": pid, "workers": workers, "worktree": worktree, "since": time.time()}),
                    encoding="utf-8")
    return path


def test_a_run_on_an_empty_machine_gets_everything_it_wants(tmp_path):
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive)
    assert c.got == 14
    assert pathlib.Path(c.path).is_file()
    assert json.loads(pathlib.Path(c.path).read_text())["workers"] == 14


def test_a_run_gets_what_is_free_when_others_hold_part_of_the_budget(tmp_path):
    hold(tmp_path, 100, 9)
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive)
    assert c.got == 5
    assert [h["pid"] for h in c.holders] == [100]


def test_a_run_that_finds_the_budget_full_still_gets_the_floor_of_two(tmp_path):
    hold(tmp_path, 100, 14)
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive)
    assert c.got == 2


def test_a_run_over_a_full_budget_does_not_go_negative(tmp_path):
    hold(tmp_path, 100, 14)
    hold(tmp_path, 101, 2)
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive)
    assert c.got == 2


def test_a_land_behind_one_full_dev_run_gets_half_the_budget_not_the_floor(tmp_path):
    hold(tmp_path, 100, 14)
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive, kind="land")
    assert c.got == 7


def test_a_land_behind_three_runs_gets_a_quarter_of_the_budget(tmp_path):
    for pid in (100, 101, 102):
        hold(tmp_path, pid, 5)
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive, kind="land")
    assert c.got == 3      # 14 // (3 holders + 1); the 14 - 15 free is negative


def test_a_land_takes_what_is_free_when_that_beats_its_fair_share(tmp_path):
    hold(tmp_path, 100, 2)
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive, kind="land")
    assert c.got == 12


def test_a_land_never_gets_more_than_it_wants(tmp_path):
    hold(tmp_path, 100, 14)
    c = slots.claim(tmp_path, 4, BUDGET, "wt-a", pid=1, alive=everyone_alive, kind="land")
    assert c.got == 4


def test_a_dev_run_behind_a_full_budget_stays_on_the_floor_of_two(tmp_path):
    hold(tmp_path, 100, 14)
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive, kind="dev")
    assert c.got == 2


def test_acquire_reads_the_run_kind_from_tw_run_kind(tmp_path, monkeypatch):
    monkeypatch.setattr(slots, "state_dir", lambda repo: tmp_path)
    hold(tmp_path, os.getpid(), 14)       # a live process, since acquire asks the OS who is alive
    env = {"PYTEST_XDIST_AUTO_NUM_WORKERS": "14", "TW_RUN_KIND": "land"}
    c = slots.acquire(tmp_path, 14, environ=env, worktree="wt-a")
    slots.release(c)
    assert c.got == 7


def test_a_serial_run_holds_one_even_when_the_budget_is_full(tmp_path):
    hold(tmp_path, 100, 14)
    c = slots.claim(tmp_path, 1, BUDGET, "wt-a", pid=1, alive=everyone_alive)
    assert c.got == 1


def test_a_run_never_gets_more_than_it_wants(tmp_path):
    c = slots.claim(tmp_path, 3, BUDGET, "wt-a", pid=1, alive=everyone_alive)
    assert c.got == 3


def test_a_claim_whose_process_is_dead_is_reaped_and_its_workers_are_free(tmp_path):
    dead = hold(tmp_path, 100, 12)
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=only(1))
    assert c.got == 14
    assert not dead.exists()
    assert c.holders == []


def test_a_claim_with_unreadable_contents_is_reaped(tmp_path):
    junk = tmp_path / "00000000000000000001-5.claim"
    junk.write_text("not json", encoding="utf-8")
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive)
    assert c.got == 14
    assert not junk.exists()


def test_a_claim_older_than_the_stale_limit_is_reaped_even_if_its_pid_is_alive(tmp_path):
    old = hold(tmp_path, 100, 12)
    later = lambda: time.time() + (slots.CLAIM_STALE_H + 1) * 3600
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive, now=later)
    assert c.got == 14
    assert not old.exists()


def test_releasing_a_claim_frees_its_workers_for_the_next_run(tmp_path):
    first = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive)
    slots.release(first)
    second = slots.claim(tmp_path, 14, BUDGET, "wt-b", pid=2, alive=everyone_alive)
    assert second.got == 14
    assert list(tmp_path.glob("*.claim")) == [pathlib.Path(second.path)]


def test_releasing_twice_is_harmless(tmp_path):
    c = slots.claim(tmp_path, 4, BUDGET, "wt-a", pid=1, alive=everyone_alive)
    slots.release(c)
    slots.release(c)
    assert list(tmp_path.glob("*.claim")) == []


def test_a_dry_look_writes_no_claim(tmp_path):
    hold(tmp_path, 100, 9)
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive, write=False)
    assert c.got == 5
    assert c.path is None
    assert len(list(tmp_path.glob("*.claim"))) == 1


def test_the_line_names_who_holds_the_rest_when_a_run_gets_fewer_than_it_wanted(tmp_path):
    hold(tmp_path, 100, 12, worktree="agent-b")
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive)
    assert c.line() == "  test slots: 2 of 14 workers, budget 14 is held by agent-b 12 (pid 100)"


def test_the_line_is_short_when_a_run_gets_all_it_wanted(tmp_path):
    c = slots.claim(tmp_path, 14, BUDGET, "wt-a", pid=1, alive=everyone_alive)
    assert c.line() == "  test slots: 14 workers (budget 14, 0 held by others)"


@pytest.mark.integration      # threads racing for a file lock
def test_two_runs_starting_together_never_take_more_than_the_budget_plus_the_floor(tmp_path):
    got = {}
    barrier = threading.Barrier(2)

    def run(pid):
        barrier.wait()
        got[pid] = slots.claim(tmp_path, BUDGET, BUDGET, f"wt-{pid}", pid=pid, alive=everyone_alive).got

    threads = [threading.Thread(target=run, args=(pid,)) for pid in (1, 2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(got.values()) == [slots.FLOOR, BUDGET]


@pytest.mark.integration      # threads racing for a file lock
def test_a_burst_of_runs_each_gets_its_share_with_only_the_floor_over_budget(tmp_path):
    wanted, runs = 4, 6
    got = []
    barrier = threading.Barrier(runs)

    def run(pid):
        barrier.wait()
        got.append(slots.claim(tmp_path, wanted, 8, f"wt-{pid}", pid=pid, alive=everyone_alive).got)

    threads = [threading.Thread(target=run, args=(pid,)) for pid in range(runs)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # first two take 4 + 4 = the whole budget of 8; each of the other four is on the floor of 2
    assert sorted(got) == [2, 2, 2, 2, 4, 4]


def test_a_lock_left_by_a_dead_claimer_is_taken_over(tmp_path):
    lock = tmp_path / ".lock"
    lock.write_text("", encoding="utf-8")
    old = time.time() - slots.LOCK_STALE_S - 5
    os.utime(lock, (old, old))
    c = slots.claim(tmp_path, 4, BUDGET, "wt-a", pid=1, alive=everyone_alive)
    assert c.got == 4


def test_a_lock_that_stays_busy_lets_the_run_go_unclaimed_and_says_so(tmp_path):
    (tmp_path / ".lock").write_text("", encoding="utf-8")    # fresh, so not stale: someone holds it
    c = slots.claim(tmp_path, 7, BUDGET, "wt-a", pid=1, alive=everyone_alive, lock_wait=0)
    assert (c.got, c.path) == (7, None)
    assert "running unclaimed" in c.line()


def test_a_lock_file_that_refuses_creation_with_permission_denied_is_waited_on_not_raised(tmp_path, monkeypatch):
    # Windows answers PermissionError, not FileExistsError, while the file is being deleted.
    real_open, refused = os.open, []

    def open_(path, flags, *a, **k):
        if str(path).endswith(".lock") and not refused:
            refused.append(path)
            raise PermissionError(13, "Permission denied")
        return real_open(path, flags, *a, **k)

    monkeypatch.setattr(slots.os, "open", open_)
    c = slots.claim(tmp_path, 4, BUDGET, "wt-a", pid=1, alive=everyone_alive)
    assert (c.got, len(refused)) == (4, 1)
    assert c.note == ""


def test_tw_slots_off_bypasses_the_budget(tmp_path):
    assert slots.acquire(tmp_path, 14, environ={"TW_SLOTS": "off"}) is None


@pytest.mark.parametrize("value", ["", "on", "1"])
def test_any_other_tw_slots_value_leaves_the_budget_on(value):
    assert slots.enabled({"TW_SLOTS": value}) is True


def test_the_budget_is_what_xdists_auto_resolves_to_here(pytestconfig):
    import xdist.plugin as xdist
    assert slots.budget({}) == xdist.pytest_xdist_auto_num_workers(pytestconfig)


def test_the_budget_follows_xdists_own_environment_override():
    assert slots.budget({"PYTEST_XDIST_AUTO_NUM_WORKERS": "6"}) == 6


@pytest.mark.integration      # a real git rev-parse
def test_the_state_dir_is_in_the_git_common_dir_shared_by_every_worktree():
    d = slots.state_dir(ROOT)
    assert d.name == "test-slots"
    assert d.parent.name == ".git"
    assert d.is_dir()

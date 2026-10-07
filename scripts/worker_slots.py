"""A machine-wide worker budget for test runs (2026-10-07).

Several sessions test this repo at once, each in its own worktree. Every run used `-n auto`, so N runs
meant N x cores workers and browser tests timing out under the load. A run now claims its workers
here first: the budget is what `-n auto` resolves to on this machine, and what other live runs hold
comes off it. A run that finds it full still gets 2 (a small oversubscription beats waiting), a
serial run holds 1. A land (env TW_RUN_KIND=land, set by land.ps1) is owed a fair share of the budget
instead, so a dev run holding it all cannot leave a land on 2 workers.

State is one file per claiming run in `<git common dir>/test-slots/`, shared by every worktree:
`<ticks>-<pid>.claim` holds pid, workers, worktree and start. A claim whose process is gone is reaped
by the next claimer (the dead-process rule of scripts/land-queue.ps1). A `.lock` file made with
O_EXCL serializes the read-reap-write, so two runs starting together cannot both take everything.

Only `decide` (the worker count), `enabled` and `budget` are pure. `state_dir` runs git; `locked`,
`live_claims`, `claim` and `release` read and write files; `process_alive` asks the OS; `acquire`
registers an atexit release. `TW_SLOTS=off` bypasses all of it.
"""
import atexit
import contextlib
import json
import os
import pathlib
import subprocess
import time

FLOOR = 2            # workers a run gets when the budget is full
LOCK_WAIT_S = 10     # give up on the lock after this, and run unclaimed
LOCK_STALE_S = 10    # a lock this old belongs to a dead claimer
CLAIM_STALE_H = 12   # a claim this old is dead whatever its pid says (pid reuse)


def enabled(environ=None):
    environ = os.environ if environ is None else environ
    return environ.get("TW_SLOTS", "").strip().lower() not in ("off", "0", "false", "no")


def budget(environ=None):
    """What xdist's `-n auto` resolves to here: PYTEST_XDIST_AUTO_NUM_WORKERS, else psutil's physical
    cores, else the logical count."""
    environ = os.environ if environ is None else environ
    try:
        if environ.get("PYTEST_XDIST_AUTO_NUM_WORKERS"):
            return max(1, int(environ["PYTEST_XDIST_AUTO_NUM_WORKERS"]))
    except ValueError:
        pass
    try:
        import psutil
        n = psutil.cpu_count(logical=False) or psutil.cpu_count()
        if n:
            return n
    except ImportError:
        pass
    return os.cpu_count() or 1


def state_dir(repo):
    """<git common dir>/test-slots, created: the one place every worktree of `repo` shares."""
    out = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=repo,
                         capture_output=True, encoding="utf-8", check=True).stdout.strip()
    d = pathlib.Path(out) / "test-slots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def process_alive(rec):
    """Is the process a claim names still running (and the same one, not a reused pid)?"""
    pid = int(rec.get("pid", 0))
    try:
        import psutil
        if not psutil.pid_exists(pid):
            return False
        started = rec.get("started")
        return started is None or abs(psutil.Process(pid).create_time() - started) < 5
    except ImportError:
        pass
    except Exception:    # psutil.NoSuchProcess, AccessDenied: gone or not ours to ask
        return False
    import ctypes       # no psutil: ask Windows. os.kill(pid, 0) would terminate the process there.
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    code = ctypes.c_ulong()
    ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
    ctypes.windll.kernel32.CloseHandle(handle)
    return code.value == 259    # STILL_ACTIVE


@contextlib.contextmanager
def locked(state, wait=LOCK_WAIT_S, stale=LOCK_STALE_S, sleep=time.sleep):
    """Hold `state`/.lock (created O_EXCL) for the block. TimeoutError after `wait` seconds; a lock older
    than `stale` seconds is its dead holder's and is taken over."""
    path = pathlib.Path(state) / ".lock"
    deadline = time.monotonic() + wait
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except (FileExistsError, PermissionError):    # Windows: PermissionError while the file is being deleted
            try:
                if time.time() - path.stat().st_mtime > stale:
                    path.unlink()
                    continue
            except OSError:
                pass
            if time.monotonic() > deadline:
                raise TimeoutError(f"test-slots lock busy for {wait} s")
            sleep(0.02)
    try:
        yield
    finally:
        with contextlib.suppress(OSError):
            path.unlink()


def live_claims(state, alive=process_alive, now=time.time):
    """[claim dict + 'path'], oldest first, after deleting the dead ones. Call under the lock."""
    out = []
    for f in sorted(pathlib.Path(state).glob("*.claim")):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
            rec["workers"] = int(rec["workers"])
            ok = alive(rec) and now() - rec["since"] < CLAIM_STALE_H * 3600
        except (OSError, ValueError, KeyError, TypeError):
            ok = False
        if not ok:
            with contextlib.suppress(OSError):
                f.unlink()
            continue
        rec["path"] = str(f)
        out.append(rec)
    return out


def decide(wanted, budget_, held, holders=0, kind="dev"):
    """Workers a run gets: min(wanted, free), never under min(FLOOR, wanted). A serial run (wanted 1) gets 1.
    A land (kind "land") is also owed a fair share, budget // (holders + 1), so it is not stuck on the
    floor behind a dev run that took everything."""
    got = max(min(wanted, budget_ - held), min(FLOOR, wanted))
    if kind == "land":
        got = max(got, min(wanted, budget_ // (holders + 1)))
    return got


class Claim:
    def __init__(self, got, wanted, budget_, holders, path=None, note=""):
        self.got, self.wanted, self.budget, self.holders, self.path, self.note = got, wanted, budget_, holders, path, note

    def line(self):
        """One line: what this run got, and who holds the rest when it got fewer than it wanted."""
        if self.note:
            return f"  test slots: {self.note}"
        if self.got >= self.wanted:
            return f"  test slots: {self.got} workers (budget {self.budget}, {sum(h['workers'] for h in self.holders)} held by others)"
        who = ", ".join(f"{h.get('worktree', '?')} {h['workers']} (pid {h['pid']})" for h in self.holders)
        return f"  test slots: {self.got} of {self.wanted} workers, budget {self.budget} is held by {who}"


def claim(state, wanted, budget_, worktree="", pid=None, alive=process_alive, write=True, now=time.time,
          lock_wait=LOCK_WAIT_S, kind="dev"):
    """Take `decide`'s workers under the lock and write the claim file (write=False only looks: a dry run).
    If the lock cannot be had the run goes on unclaimed with what it wanted, and the line says so."""
    pid = os.getpid() if pid is None else pid
    try:
        with locked(state, wait=lock_wait):
            holders = live_claims(state, alive, now)
            got = decide(wanted, budget_, sum(h["workers"] for h in holders), len(holders), kind)
            path = None
            if write:
                started = None
                with contextlib.suppress(Exception):
                    import psutil
                    started = psutil.Process(pid).create_time()
                path = pathlib.Path(state) / f"{time.time_ns()}-{pid}.claim"
                path.write_text(json.dumps({"pid": pid, "workers": got, "worktree": worktree, "since": now(),
                                            "started": started}), encoding="utf-8")
            return Claim(got, wanted, budget_, holders, str(path) if path else None)
    except TimeoutError as e:
        return Claim(wanted, wanted, budget_, [], note=f"{e}; running unclaimed with {wanted}")


def release(c):
    """Drop a claim's file; safe to call twice."""
    if c is not None and c.path:
        with contextlib.suppress(OSError):
            os.remove(c.path)
        c.path = None


def acquire(repo, wanted, environ=None, worktree=None, write=True):
    """The caller's one call: a Claim for `wanted` workers, released at exit. None when TW_SLOTS=off."""
    environ = os.environ if environ is None else environ
    if not enabled(environ):
        return None
    c = claim(state_dir(repo), wanted, budget(environ), worktree or pathlib.Path(repo).name, write=write,
              kind=environ.get("TW_RUN_KIND", "dev"))
    atexit.register(release, c)
    return c

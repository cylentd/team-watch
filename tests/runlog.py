"""Records every pytest run into the test history (scripts/testlog.py reads it back), and prints the
layers line and how this run compares with the recent full runs.

One JSON line per run, written by the controller only (an xdist worker sees a fraction of the run):
when, what kind (TW_RUN_KIND: dev unless a script says land, flake or scheduled), the commit, the
wall time, the outcome counts (`outcomes`), each layer's tests and worker seconds, each file's, the 15 slowest
tests, and every failed test's id. Recording never fails a run: an error is one warning line.

Since 2026-10-07 the line also carries a `profile` block (see `Profile` below; `python scripts/testlog.py
--profile` prints it): the run's worker time split into harness and tests, the fixtures, the workers.
"""
import datetime as dt
import importlib.util
import os
import pathlib
import subprocess
import time

import pytest

# Loaded by path, never by putting scripts/ on sys.path: scripts/ holds modules (clips.py) that would
# shadow design/'s of the same name for every test that imports after this.
_spec = importlib.util.spec_from_file_location(
    "testlog", pathlib.Path(__file__).resolve().parents[1] / "scripts" / "testlog.py")
testlog = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(testlog)

LAYERS = ("python", "node", "integration", "component", "build", "browser")


def git(*args):
    out = subprocess.run(["git", "-C", str(testlog.REPO), *args], capture_output=True, text=True)
    return out.stdout.strip()


# --- the profile (2026-10-07): where one run's worker time went, harness as well as tests ----------
# Summing setup + call + teardown charges a session fixture's build to whichever test ran first and
# never sees process startup, collection, pytest's own work between tests or a worker waiting for
# work. A Profile watches one process (an xdist worker, or the whole serial run) and splits its wall
# time into disjoint parts that add up to it: startup | collection | tests | shared fixtures |
# pytest overhead | idle. Under xdist every worker sends its block home in `workeroutput`.
_EPOCH, _PERF = time.time(), time.perf_counter()
TOP_TESTS = 30
SHARED_BUCKET = {"session": "session", "package": "module", "module": "module", "class": "module"}


def _now():
    """The wall clock at perf_counter's resolution (time.time() ticks coarsely on some systems)."""
    return _EPOCH + (time.perf_counter() - _PERF)


def process_start():
    """When this process was created, or when this module was imported if psutil is missing."""
    try:
        import psutil
        return psutil.Process().create_time()
    except Exception:
        return _EPOCH


class Profile:
    def __init__(self, wid, start):
        self.wid, self.start = wid, start
        self.started = self.collect_begin = None  # pytest_sessionstart; the start of collection
        self.collect, self.last_end = 0.0, None
        self.busy = self.idle = self.overhead = 0.0
        self.fixtures = {}                        # (name, scope) -> [count, setup s, teardown s]
        self.shared = dict.fromkeys(("session_setup", "session_teardown", "module_setup", "module_teardown"), 0.0)
        self.tests = {}                           # nodeid -> [setup, call, teardown, function fixtures in setup]
        self.phase, self.phase_shared, self.phase_fx = None, 0.0, 0.0
        self.begun, self.reported, self.frames = None, 0.0, []

    def sessionstart(self, now):
        self.started = now

    def collected(self, begin, end):
        self.collect_begin, self.collect, self.last_end = begin, end - begin, end

    def enter(self):
        """A fixture starts: what runs inside it is charged to the inner fixture, not to this one."""
        self.frames.append(0.0)

    def leave(self, total):
        """The fixture ends after `total` s; its own time is what the fixtures inside it did not take."""
        inner = self.frames.pop()
        if self.frames:
            self.frames[-1] += total
        return total - inner

    def begin(self, when):
        self.phase, self.phase_shared, self.phase_fx = when, 0.0, 0.0

    def _fixture(self, name, scope, secs, which):
        row = self.fixtures.setdefault((name, scope), [0, 0.0, 0.0])
        row[1 if which == "setup" else 2] += secs
        row[0] += which == "setup"
        if scope in SHARED_BUCKET:
            self.shared[f"{SHARED_BUCKET[scope]}_{which}"] += secs
            self.phase_shared += secs if self.phase == which else 0.0
        elif which == "setup":
            self.phase_fx += secs

    def fixture_setup(self, name, scope, secs):
        self._fixture(name, scope, secs, "setup")

    def fixture_teardown(self, name, scope, secs):
        self._fixture(name, scope, secs, "teardown")

    def report(self, report):
        """One phase's report. A session or module fixture built or torn down inside it is harness,
        so it leaves the test's own setup or teardown."""
        row = self.tests.setdefault(report.nodeid, [0.0, 0.0, 0.0, 0.0])
        own = max(report.duration - self.phase_shared, 0.0)
        if report.when == "setup":
            row[0] += own
            row[3] += self.phase_fx
        elif report.when == "call":
            row[1] += report.duration
        else:
            row[2] += own
        self.reported += report.duration
        self.phase = None

    def protocol_begin(self, now):
        base = self.last_end if self.last_end is not None else self.started
        self.idle += now - base if base is not None else 0.0
        self.begun, self.reported = now, 0.0

    def protocol_end(self, now):
        self.busy += now - self.begun
        self.overhead += (now - self.begun) - self.reported
        self.last_end = now

    def finish(self, now):
        tail = now - self.last_end if self.last_end is not None else 0.0
        tests = list(self.tests.items())
        top = sorted(tests, key=lambda kv: -sum(kv[1][:3]))[:TOP_TESTS]
        scopes = {}
        for name, scope in self.fixtures:
            scopes.setdefault(name, []).append(scope)
        r = lambda x: round(x, 3)
        return {
            "id": self.wid, "wall": r(now - self.start),
            # process start to the first collected item: Python, conftest imports, configure, the session-start hooks
            "startup": r((self.collect_begin or self.started or self.start) - self.start), "collect": r(self.collect),
            "busy": r(self.busy), "idle": r(self.idle + tail), "overhead": r(self.overhead),
            "tests": {"setup": r(sum(v[0] for _, v in tests)), "call": r(sum(v[1] for _, v in tests)),
                      "teardown": r(sum(v[2] for _, v in tests)), "n": len(tests)},
            "shared": {k: r(v) for k, v in self.shared.items()},
            "fixtures": {(n if len(scopes[n]) == 1 else f"{n}@{s}"): [s, c, r(su), r(td)]
                         for (n, s), (c, su, td) in sorted(self.fixtures.items())},
            "top": [[k, r(sum(v[:3])), r(v[0]), r(v[1]), r(v[2]), r(v[3])] for k, v in top],
        }


def build_profile(workers, controller_wall):
    """The run's profile block from every worker's finish(): sums, the fixtures by name, the costliest
    tests, and `unaccounted`, the worker time no part claims (the check that the parts add up)."""
    s = lambda f: sum(f(w) for w in workers)
    harness = {"startup": s(lambda w: w["startup"]), "collect": s(lambda w: w["collect"]),
               "overhead": s(lambda w: w["overhead"]), "idle": s(lambda w: w["idle"]),
               **{k: s(lambda w, k=k: w["shared"][k]) for k in workers[0]["shared"]}} if workers else {}
    tests = {k: s(lambda w, k=k: w["tests"][k]) for k in ("setup", "call", "teardown", "n")}
    worker_s = s(lambda w: w["wall"])
    fixtures = {}
    for w in workers:
        for key, (scope, n, setup, teardown) in w["fixtures"].items():
            row = fixtures.setdefault((key.removesuffix("@" + scope), scope), [0, 0.0, 0.0])
            row[0] += n
            row[1] += setup
            row[2] += teardown
    names = [n for n, _ in fixtures]
    top = sorted((t for w in workers for t in w["top"]), key=lambda t: -t[1])[:TOP_TESTS]
    r = lambda x: round(x, 2)
    return {
        "v": 1, "worker_s": r(worker_s),
        "controller": r(max(controller_wall - max((w["wall"] for w in workers), default=0.0), 0.0)),
        "unaccounted": r(worker_s - sum(harness.values()) - tests["setup"] - tests["call"] - tests["teardown"]),
        "harness": {k: r(v) for k, v in harness.items()},
        "tests": {k: (r(v) if k != "n" else v) for k, v in tests.items()},
        "workers": [[w["id"], r(w["wall"]), r(w["busy"]), r(w["idle"]), w["tests"]["n"]] for w in workers],
        "fixtures": {(n if names.count(n) == 1 else f"{n}@{sc}"): [sc, c, r(su), r(td)]
                     for (n, sc), (c, su, td) in sorted(fixtures.items())},
        "top": [[t[0], *(r(x) for x in t[1:])] for t in top],
    }


class ProfilePlugin:
    """Feeds a Profile from pytest's hooks, in every process that runs tests: the serial run, or each
    xdist worker (which sends its block home); the xdist controller runs none, it collects them."""

    def __init__(self, config, runlog):
        self.config, self.runlog, self.prof, self.restore = config, runlog, None, None

    def pytest_sessionstart(self, session):
        if self.config.pluginmanager.hasplugin("dsession"):      # the xdist controller: workers do the work
            return
        wid = getattr(self.config, "workerinput", {}).get("workerid", "main")
        self.prof = Profile(wid, process_start())
        self.prof.sessionstart(_now())
        self.time_teardowns()

    def time_teardowns(self):
        """Wrap FixtureDef.finish to time fixture teardowns. pytest's private API: a version without it,
        or one that refuses the patch, loses the teardown timing and nothing else."""
        from _pytest.fixtures import FixtureDef
        orig, prof = getattr(FixtureDef, "finish", None), self.prof
        if orig is None:
            return

        def finish(fd, request):
            try:
                prof.enter()
                t0 = _now()
            except Exception:
                return orig(fd, request)
            try:
                return orig(fd, request)
            finally:
                try:
                    prof.fixture_teardown(fd.argname, fd.scope, prof.leave(_now() - t0))
                except Exception:       # recording never fails a run
                    pass
        try:
            FixtureDef.finish = finish
        except Exception:
            return
        self.restore = lambda: setattr(FixtureDef, "finish", orig)

    @pytest.hookimpl(wrapper=True)
    def pytest_collection(self):
        t0 = _now()
        try:
            return (yield)
        finally:
            if self.prof:
                self.prof.collected(t0, _now())

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_protocol(self, item, nextitem):
        if not self.prof:
            return (yield)
        self.prof.protocol_begin(_now())
        try:
            return (yield)
        finally:
            self.prof.protocol_end(_now())

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(self, fixturedef, request):
        if not self.prof:
            return (yield)
        self.prof.enter()
        t0 = _now()
        try:
            return (yield)
        finally:
            self.prof.fixture_setup(fixturedef.argname, fixturedef.scope, self.prof.leave(_now() - t0))

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item):
        self.prof and self.prof.begin("setup")

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_call(self, item):
        self.prof and self.prof.begin("call")

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_teardown(self, item, nextitem):
        self.prof and self.prof.begin("teardown")

    def pytest_runtest_logreport(self, report):
        self.prof and self.prof.report(report)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session):
        if not self.prof:
            return
        if self.restore:
            self.restore()
        out = self.prof.finish(_now())
        if hasattr(self.config, "workeroutput"):                 # xdist: the controller reads it in testnodedown
            self.config.workeroutput["tw_profile"] = out
        elif self.runlog:
            self.runlog.profiles.append(out)

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodedown(self, node, error):
        out = getattr(node, "workeroutput", {}).get("tw_profile")
        if out and self.runlog:
            self.runlog.profiles.append(out)


class RunLog:
    def __init__(self, config):
        self.config = config
        self.start = time.time()
        self.proc_start = process_start()
        self.profiles = []                     # each worker's finish(), or the serial run's
        self.layers, self.files, self.tests = {}, {}, {}
        self.failed, self.counts = [], {"passed": 0, "failed": 0, "skipped": 0, "error": 0}

    def pytest_runtest_logreport(self, report):
        """Every phase's time, setup included: a module's page load is charged to its first test."""
        layer = dict(report.user_properties).get("layer")
        if not layer:
            return
        f = report.nodeid.split("::")[0].split("/")[-1]
        n_add = report.when == "call"
        n, s = self.layers.get(layer, (0, 0.0))
        self.layers[layer] = (n + n_add, s + report.duration)
        n, s, was = self.files.get(f, (0, 0.0, layer))
        costliest = max(was, layer, key=LAYERS.index)     # a file of python and browser tests is a browser file
        self.files[f] = (n + n_add, s + report.duration, costliest)
        self.tests[report.nodeid] = self.tests.get(report.nodeid, 0.0) + report.duration
        if report.failed:
            self.failed.append(report.nodeid)
            self.counts["failed" if report.when == "call" else "error"] += 1
        elif report.skipped:
            self.counts["skipped"] += 1
        elif report.when == "call":
            self.counts["passed"] += 1

    def record(self):
        slow = sorted(self.tests.items(), key=lambda x: -x[1])[:15]
        return {
            "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "kind": os.environ.get("TW_RUN_KIND", "dev"),
            "sha": git("rev-parse", "HEAD"), "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            # tracked edits, or a new file where the suite reads (tests/, design/, api/, scripts/): this
            # run tested something no commit names. A stray screenshot at the root does not count, or
            # every nightly run in the main checkout would read as dirty and never count toward flakes.
            "dirty": any(not ln.startswith("??") or ln[3:].startswith(("tests/", "design/", "api/", "scripts/"))
                         for ln in git("status", "--porcelain").splitlines() if ln),
            "args": list(self.config.invocation_params.args),
            "wall": round(time.time() - self.start, 1),
            "outcomes": self.counts,
            "n_files": len(self.files),
            "layers": {k: [self.layers[k][0], round(self.layers[k][1], 1)] for k in LAYERS if k in self.layers},
            "files": {f: [n, round(s, 2), layer] for f, (n, s, layer) in sorted(self.files.items())},
            "slow": [[k, round(v, 2)] for k, v in slow],
            "failed": sorted(set(self.failed)),
            **({"profile": build_profile(self.profiles, time.time() - self.proc_start)} if self.profiles else {}),
        }

    def pytest_terminal_summary(self, terminalreporter):
        if not self.layers:
            return
        w = terminalreporter.write_line
        w("layers (worker time): " + " | ".join(f"{k} {n} tests {s:.1f} s" for k in LAYERS
                                                  if k in self.layers for n, s in [self.layers[k]]))
        try:
            rec = self.record()
            before = testlog.read("runs.jsonl", days=30)
            path = testlog.append("runs.jsonl", rec)
            fulls = testlog.full_runs(before + [rec])
            if path and fulls and fulls[-1] is rec and len(fulls) > 1:
                prev = [sum(s for _, s in r["layers"].values()) for r in fulls[-6:-1]]
                now = sum(s for _, s in rec["layers"].values())
                w(f"history: {now:.0f} worker s, median of the last {len(prev)} full runs "
                  f"{sorted(prev)[len(prev) // 2]:.0f} s (python scripts/testlog.py)")
            week = testlog.flaky(testlog.read("runs.jsonl", days=7))
            flakes = [k for k in week if k in rec["failed"]]
            if flakes:
                w(f"history: {len(flakes)} of these failures passed before on this commit (flaky): {flakes[:3]}")
            elif week:
                w(f"history: {len(week)} flaky test(s) this week, e.g. {next(iter(week))} (python scripts/testlog.py)")
        except Exception as e:  # the history is a record, never a reason to fail a run
            w(f"history: not recorded ({type(e).__name__}: {e})")


def register(config):
    log = None
    if not hasattr(config, "workerinput"):     # the controller, or a run without xdist
        log = RunLog(config)
        config.pluginmanager.register(log, "runlog")
    config.pluginmanager.register(ProfilePlugin(config, log), "runprofile")     # a worker profiles itself too

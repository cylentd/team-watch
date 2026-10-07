"""Records every pytest run into the test history (scripts/testlog.py reads it back), and prints the
layers line and how this run compares with the recent full runs.

One JSON line per run, written by the controller only (an xdist worker sees a fraction of the run):
when, what kind (TW_RUN_KIND: dev unless a script says land, flake or scheduled), the commit, the
wall time, the outcome counts (`outcomes`), each layer's tests and worker seconds, each file's, the 15 slowest
tests, and every failed test's id. Recording never fails a run: an error is one warning line.
"""
import datetime as dt
import importlib.util
import os
import pathlib
import subprocess
import time

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


class RunLog:
    def __init__(self, config):
        self.config = config
        self.start = time.time()
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
    if not hasattr(config, "workerinput"):     # the controller, or a run without xdist
        config.pluginmanager.register(RunLog(config), "runlog")

"""Layer 2: the page's pure JavaScript in Node, with no build and no browser (2026-10-05).

A browser test pays for a build and a page load (about 1 s) before its first assertion. A function
from data to data (a scan, a sort, a wording) needs neither: load the files that define it into a
Node sandbox and call it, in about a millisecond. The `node_js` fixture (tests/conftest.py) does it:

    @pytest.fixture(scope="module")
    def hurt(node_js):
        return node_js("surface/live/nflnow.js", "data/gameday/hurt.js", globals={"GD_ALIAS": {}})

    def test_x(hurt):
        assert hurt("gdHurtScan", summary, names) == [...]
        assert hurt("muVs({team: 'DAL', opp: 'BAL', home: true})") == "DAL vs BAL"

Files are named from design/src/js and run in the order given, as classic scripts sharing one
scope, the way the page runs them. lib/escape.js and COPY (content.json) are always loaded first,
so esc() and t() work as on the page. A global another file would define (LIVE_*, GD_ALIAS) is
passed in `globals` instead of loading that file. Listing the files is the point: a test shows what
the code under it really depends on, and a dependency the list lacks fails as a ReferenceError.

Each node_js(...) is a sandbox of its own (a separate vm context: no global, built-in or planted value
is shared with another), inside one node process that a Python process starts once and reuses, so a
call costs milliseconds, not a node start-up (2026-10-06).

Synchronous code only; a Promise comes back as {}. Anything that reads `document` belongs in a
browser test.
"""
import atexit
import itertools
import json
import pathlib
import queue
import shutil
import subprocess
import threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
JS = ROOT / "design" / "src" / "js"
HOST = ROOT / "tests" / "jsunit_host.js"
COPY = json.loads((ROOT / "design" / "src" / "content.json").read_text(encoding="utf-8"))
ALWAYS = ("lib/escape.js",)
TIMEOUT = 10


class JSError(AssertionError):
    """The JavaScript threw; the message is its stack."""


class _Host:
    """The one node process of this Python process (a pytest worker). Starting node costs about
    0.4 s under load, a sandbox about 5 ms, so every NodeJS is a sandbox of this process and none
    starts its own. A host that died or hung is replaced on the next call (see `kill_host`)."""

    def __init__(self):
        node = shutil.which("node")
        # Not a skip: a unit layer that quietly stops running looks exactly like one that passes.
        assert node, "node is not on PATH: the JS unit tests need it (https://nodejs.org)"
        self.proc = subprocess.Popen([node, str(HOST)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     text=True, encoding="utf-8", bufsize=1)
        self.lines = queue.Queue()
        self.next_id = 0
        threading.Thread(target=self._read, args=(self.proc, self.lines), daemon=True).start()

    @staticmethod
    def _read(proc, lines):
        for line in proc.stdout:
            lines.put(line)
        lines.put(None)

    @property
    def alive(self):
        return self.proc.poll() is None

    def ask(self, request):
        self.next_id += 1
        request = {**request, "id": self.next_id}
        what = request.get("src", request["op"])
        try:
            self.proc.stdin.write(json.dumps(request) + "\n")
            self.proc.stdin.flush()
            line = self.lines.get(timeout=TIMEOUT)
        except queue.Empty:
            self.kill()             # hung (an endless loop): nothing else can use this process
            raise JSError(f"node gave no answer in {TIMEOUT} s: {what}") from None
        except OSError:
            line = None
        if line is None:
            self.kill()
            raise JSError("node exited")
        answer = json.loads(line)
        if not answer["ok"]:
            raise JSError(answer["error"])
        return answer["value"]

    def kill(self):
        self.proc.kill()
        self.proc.wait(timeout=TIMEOUT)

    def stop(self):
        """Ask node to leave by closing its stdin, which it reads to the end."""
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=TIMEOUT)
        except (OSError, subprocess.TimeoutExpired):
            self.kill()


_host = None
_ids = itertools.count(1)


def host():
    """The live host, started on first use and again after it died."""
    global _host
    if _host is None or not _host.alive:
        _host = _Host()
    return _host


def kill_host():
    """Kill the node process now. The next call starts a new one; a sandbox that was in the old one
    is loaded again, fresh, by its next call."""
    if _host is not None:
        _host.kill()


@atexit.register
def _stop_host():
    if _host is not None and _host.alive:
        _host.stop()


class NodeJS:
    """A sandbox of the given files in the shared node process."""

    def __init__(self, *files, globals=None):
        paths = [JS / f for f in (*ALWAYS, *files)]
        missing = [str(p) for p in paths if not p.is_file()]
        assert not missing, f"no such file: {missing}"
        self.ctx = next(_ids)
        self._load = {"op": "load", "ctx": self.ctx, "files": [str(p) for p in paths],
                      "globals": {"COPY": COPY, **(globals or {})}}
        self._host = None
        self._ready()

    def _ready(self):
        """The live host, with this sandbox loaded in it (again, fresh, when the host is a new one)."""
        h = host()
        if h is not self._host:
            h.ask(self._load)
            self._host = h
        return h

    @property
    def pid(self):
        return self._ready().proc.pid

    def __call__(self, src, *args):
        """src is a function name or an expression. A function is called with args (JSON values);
        anything else is returned as it is. The value comes back through JSON."""
        return self._ready().ask({"op": "eval", "ctx": self.ctx, "src": src, "args": list(args)})

    def close(self):
        """Forget the sandbox; the node process stays for the next one."""
        if self._host is not None and self._host.alive:
            self._host.ask({"op": "drop", "ctx": self.ctx})
        self._host = None

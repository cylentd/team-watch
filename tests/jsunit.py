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

Synchronous code only; a Promise comes back as {}. Anything that reads `document` belongs in a
browser test.
"""
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


class NodeJS:
    def __init__(self, *files, globals=None):
        node = shutil.which("node")
        # Not a skip: a unit layer that quietly stops running looks exactly like one that passes.
        assert node, "node is not on PATH: the JS unit tests need it (https://nodejs.org)"
        paths = [JS / f for f in (*ALWAYS, *files)]
        missing = [str(p) for p in paths if not p.is_file()]
        assert not missing, f"no such file: {missing}"
        self.proc = subprocess.Popen([node, str(HOST)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     text=True, encoding="utf-8", bufsize=1)
        self.lines = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()
        self._ask({"op": "load", "files": [str(p) for p in paths], "globals": {"COPY": COPY, **(globals or {})}})

    def _read(self):
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def _ask(self, request):
        self.proc.stdin.write(json.dumps(request) + "\n")
        self.proc.stdin.flush()
        try:
            line = self.lines.get(timeout=TIMEOUT)
        except queue.Empty:
            raise JSError(f"node gave no answer in {TIMEOUT} s: {request.get('src', 'load')}") from None
        if line is None:
            raise JSError("node exited")
        answer = json.loads(line)
        if not answer["ok"]:
            raise JSError(answer["error"])
        return answer["value"]

    def __call__(self, src, *args):
        """src is a function name or an expression. A function is called with args (JSON values);
        anything else is returned as it is. The value comes back through JSON."""
        return self._ask({"op": "eval", "src": src, "args": list(args)})

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=TIMEOUT)

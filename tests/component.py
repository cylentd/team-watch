"""The component layer: one surface on a page cut down to what it can show (2026-10-05).

    from component import mount

    def test_x(mount):
        page, errors = mount("ranks")                                # Ranks at 360x740, the suite's seed
        page, errors = mount("ranks", size=(390, 844), init=(NO_TEAM,))
        page, errors = mount("roster", heads=True)                   # the fixture's headshot files beside the page

A full-page browser test opens a new context and loads the whole fixture page into it (`open_at`).
`mount` loads a page assembled for one view, on a context its module keeps per (surface, size,
init), reloaded for every call. Measured 2026-10-05 on a quiet machine, Ranks at 360x740, one
Chromium, warm, median of 8-10 (`python tests/component.py` measures the first two again):

    full page, new context (open_at)        148 ms
    full page, kept context, reloaded         64 ms
    mount (kept context, view's CSS only)     53 ms

The first load of a page in a browser costs ~1 s either way; both pay it once per worker. A mount pays
it in the fixture's setup (`Mounter.warm`), and since the app is one script file that every surface
loads, a surface or a build the worker has not mounted yet costs ~0.2 s, not ~1.2 s (2026-10-06).
The same setup fences every CSS part once (`css_part`), and the fixture opens each key its module's tests
name (`module_keys`, `Mounter.prepare`), so neither lands in a test's call.

What the page holds, and why the cut is honest:

- **JS: all of it.** A truly partial page is infeasible. Every part shares one script scope, and the
  core names the views at load, not only when one draws: nav.js calls lbKeys() (surface/lboard/) to
  decide its row, and chrome/render.js builds its `plain` table of every view's draw function each
  time it renders, so a page without matchupsHTML throws while drawing Ranks. Following the
  references from Ranks and the core kept 214 of 243 parts before that table needed the rest.
- **CSS: the view's.** Every file outside css/surface/, plus each css/surface file that scope.json
  leaves shared or fences to this view or to an overlay (`#modal`, `.stpanel`). A file fenced only
  to other views is dropped: scope_css.fence() already stops its rules matching inside this view,
  so dropping it changes nothing the view can show. Fences are applied as the build applies them.
- **Data: a real build's.** The injected section of the session's build of tests/fixtures (the
  `built` fixture, shared with every full-page test on the worker), never re-derived.
- **Scripts as files.** The data and the JS are two `<script src>` files where the build inlines one
  `<script>`, in the same order and the same global scope, so the page runs the same code.
- **No headshots** are copied beside the page, so a face draws its initials, unless a test asks with
  `heads=True`: the build's headshot files go in a folder of their own (once per worker) and the page
  loads from there.

Where the time goes: most of the saving is the kept context (no context to create, the compiled
script reused); the cut CSS is the rest, less to match on every style pass. The trade-off: a link to another view does land there (all JS is present), but that
view is drawn without its CSS, so a journey between views, the hash, Back and the nav row stay
full-page tests.

Each call clears storage and loads the page again, so no test inherits another's state and no reset
script has to know what a test changed. A page error while loading fails the test at once.
"""
import ast
import functools
import hashlib
import inspect
import pathlib
import re
import shutil
import statistics
import sys
import textwrap
import time

import pytest

from conftest import SharedPages
from test_render import LOAD_MS, SEED, watch_errors

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "design"))
import assemble  # noqa: E402
import scope_css  # noqa: E402

# a mountable surface -> the leaf (hash and #view[data-view]) it draws. An overlay (the profile, a
# game's strip) has no leaf of its own: its tests mount the view that opens it.
SURFACES = {"ranks": "ranks", "digest": "digest", "roster": "roster", "parlay": "parlay", "build": "build",
            "live": "live", "teams": "teams", "weekrecap": "weekrecap", "trades": "trades", "records": "records",
            "preview": "preview", "schedule": "schedule", "recap": "recap",
            "waivers": "waivers", "weather": "weather", "news": "news",
            "board": "board", "movers": "movers", "usage": "usage", "dfs": "dfs"}
DRAWN = "document.getElementById('view').children.length > 0"


def css_parts(leaf):
    """Every CSS part but those scope.json fences only to other views."""
    fenced = _fences()
    return [rel for rel in assemble.manifest("css")
            if rel not in fenced or leaf in fenced[rel] or any(r[0] in "#." for r in fenced[rel])]


def injected(fragment):
    """The `const NAME = ...;` lines a build injected (its fragment's `/*__HEADS__*/`), as one string."""
    return fragment.rsplit("<script>\n", 1)[1].split("\nconst COPY = ", 1)[0]


# The shell's one script: the build's data, then the app. A mounted page loads both as files instead.
SCRIPT_BLOCK = re.compile(r"<script>\s*/\*__HEADS__\*/\s*/\*\{\{js\}\}\*/\s*</script>")


@functools.lru_cache(maxsize=None)
def app_js():
    """Every JS part, COPY first: the same text for every surface and every build."""
    return assemble.concat("js", banners=False)


@functools.lru_cache(maxsize=None)
def _fences():
    return scope_css.load(assemble.SCOPE)["fenced"]


# Fencing a CSS part costs ~2 ms and a surface loads ~80 of them, so a surface's first page cost ~200 ms
# (2026-10-06). A part fences the same way for every surface and every build: fenced once per worker, in
# Mounter.warm, and only joined here.
@functools.lru_cache(maxsize=None)
def css_part(rel):
    return assemble.part_text("css", rel, _fences())


@functools.lru_cache(maxsize=None)
def component_html(surface, srcs):
    """The document one mounted surface loads: its CSS inline, the scripts by URL (`srcs`, in order)."""
    import build
    css = "".join(css_part(rel) for rel in css_parts(SURFACES[surface]))
    shell = assemble.shell_html()
    if len(SCRIPT_BLOCK.findall(shell)) != 1:
        raise RuntimeError("shell.html no longer ends in one <script> of /*__HEADS__*/ then /*{{js}}*/; "
                           "tests/component.py splits that block into script files")
    tags = "\n".join(f'<script src="{src}"></script>' for src in srcs)
    body = SCRIPT_BLOCK.sub(lambda _: tags, shell.replace(assemble.PLACEHOLDER["css"], css, 1), count=1)
    return f"{build.document_head()}\n{body}\n</body>\n</html>\n"


# Chromium keeps a script's compiled code by its URL, for every context of the browser. The first page
# to run the 1.5 MB app takes ~1.1 s; a page that loads the same file later takes ~0.2 s, whatever its
# surface or context (2026-10-06, this machine). So the data and the app are files of their own, named by
# their content and shared by every Mounter on the worker, and only each surface's CSS is in its page.
_SCRIPTS = {}   # sha of a script's text -> its file
_FILES = {}     # (surface, folder, heads, scripts) -> the page's URL
_WARM = set()   # (browser, app URL): browsers that have compiled the app


def script_file(text, folder):
    """The URL of a file holding `text`, written into `folder` the first time the worker needs it."""
    sha = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
    path = _SCRIPTS.get(sha)
    if path is None or not path.exists():
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"mount-{sha}.js"
        path.write_text(text, encoding="utf-8")
        _SCRIPTS[sha] = path
    return path.as_uri()


class Mounter:
    """`mount(surface, size=(w, h), init=(script, ...), touch=False)` -> (page, errors)."""

    def __init__(self, browser, folder, fragment):
        self.browser, self.folder, self.data, self.pages = browser, pathlib.Path(folder), injected(fragment), SharedPages()
        self.srcs = (script_file(self.data, self.folder), script_file(app_js(), self.folder))
        self.warm()

    def warm(self):
        """Load one page in a context of its own and close it, so the browser compiles the app here, in
        the fixture's setup, and not in the first test that mounts. Once per browser; a page that fails
        to load here fails again, with its message, in the test that mounts it."""
        key = (id(self.browser), self.srcs[1])
        if key in _WARM:
            return
        _WARM.add(key)
        for rel in assemble.manifest("css"):
            css_part(rel)
        ctx = None
        try:
            ctx, page, errors = self._open((360, 740), (), False)
            page.goto(self.url("ranks"), timeout=LOAD_MS)
            if not errors:                  # a page that raised is the test's to report, not worth a wait here
                page.wait_for_function(DRAWN, timeout=LOAD_MS)
        except Exception:
            pass
        finally:
            if ctx is not None:
                ctx.close()

    def url(self, surface, heads=False):
        key = (surface, str(self.folder), heads, self.srcs)
        if key not in _FILES:
            folder = self.folder / "heads" if heads else self.folder     # the headshots beside the page, as served
            folder.mkdir(parents=True, exist_ok=True)
            import build
            build.write_avatars(folder)                   # the team avatars beside the page (two small files)
            if heads:
                build.write_heads(folder)
            p = folder / f"{surface}-{self.srcs[0][-19:-3]}.html"      # the data's sha: one page per build
            p.write_text(component_html(surface, self.srcs), encoding="utf-8")
            _FILES[key] = p.as_uri() + "#" + SURFACES[surface]
        return _FILES[key]

    def _open(self, size, init, touch):
        ctx = self.browser.new_context(viewport={"width": size[0], "height": size[1]},
                                       reduced_motion="reduce", has_touch=touch)
        page = ctx.new_page()
        page.set_default_timeout(5000)      # a missing control is a bug, not a slow load
        errors = watch_errors(page)
        page.route(re.compile(r"^https?://"), lambda route: route.abort())
        page.add_init_script(SEED)
        for script in init:
            page.add_init_script(script)
        return ctx, page, errors

    def _page(self, surface, size, init, touch, heads):
        return self.pages.get((surface, tuple(size), tuple(init), touch, heads),
                              lambda: self._open(size, init, touch))

    def prepare(self, surface, size=(360, 740), init=(), touch=False, heads=False):
        """Open a key's context and load its page once, unless the module has it already: the first
        mount of a key costs a context and a cold first load (~100 ms quiet, ~250 ms loaded, 2026-10-06),
        and that is the module's setup, not its first test's. A failure here is the test's to report."""
        key = (surface, tuple(size), tuple(init), touch, heads)
        if key in self.pages.items or key in self.pages.failed:
            return
        try:
            _, page, errors = self._page(surface, size, init, touch, heads)
            page.goto(self.url(surface, heads), timeout=LOAD_MS)
            if not errors:
                page.wait_for_function(DRAWN, timeout=LOAD_MS)
        except Exception:
            pass

    def __call__(self, surface, size=(360, 740), init=(), touch=False, heads=False):
        url = self.url(surface, heads)
        _, page, errors = self._page(surface, size, init, touch, heads)
        if page.url.startswith("file:"):
            # The hop is what makes the next goto a new document: from the same file, a goto that only
            # differs in its #hash (or not at all) is a same-document navigation, which keeps the old
            # page. It costs ~7 ms; a reload after history.replaceState was no faster (2026-10-06).
            page.evaluate("() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} }")
            page.goto("about:blank")
        errors.clear()
        page.goto(url, timeout=LOAD_MS)
        page.wait_for_function(DRAWN, timeout=LOAD_MS)
        if errors:
            pytest.fail(f"the {surface} component raised while loading: {errors[:3]}", pytrace=False)
        return page, errors


# Which keys a module will mount, read from its tests' own source: every `mount(...)` call whose arguments
# are literals, the module's constants or the test's parameters. A call through a helper or with a
# computed argument is not seen, and mounts as before. At most MAX_PREPARED keys, so a wrong guess can
# never push the module past conftest's MAX_CONTEXTS.
MAX_PREPARED = 4
_ARGS = ("surface", "size", "init", "touch", "heads")
_NONE = object()


@functools.lru_cache(maxsize=None)
def _mount_calls(func):
    """(calls, local names) of one test function: its `mount(...)` call nodes, and the names it binds."""
    try:
        tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    except (OSError, TypeError, SyntaxError):
        return (), frozenset()
    calls = tuple(n for n in ast.walk(tree) if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Name) and n.func.id == "mount")
    local = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    local |= {a.arg for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.Lambda)) for a in
              (*n.args.posonlyargs, *n.args.args, *n.args.kwonlyargs)}
    return calls, frozenset(local)


def _value(node, names):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return names.get(node.id, _NONE)
    if isinstance(node, (ast.Tuple, ast.List)):
        vals = tuple(_value(e, names) for e in node.elts)
        return _NONE if _NONE in vals else vals
    return _NONE


def mount_keys(item):
    """The (surface, size, init, touch, heads) keys a test's own `mount(...)` calls name."""
    calls, local = _mount_calls(getattr(item, "function", None))
    if not calls:
        return []
    params = dict(getattr(getattr(item, "callspec", None), "params", {}))
    module = getattr(item, "module", None)
    names = {k: v for k, v in (vars(module).items() if module else ()) if k not in local}
    names.update(params)
    keys = []
    for call in calls:
        if len(call.args) > len(_ARGS) or any(isinstance(a, ast.Starred) for a in call.args) \
                or any(k.arg not in _ARGS for k in call.keywords):
            continue
        got = {"size": (360, 740), "init": (), "touch": False, "heads": False}
        got.update({_ARGS[i]: _value(a, names) for i, a in enumerate(call.args)})
        got.update({k.arg: _value(k.value, names) for k in call.keywords})
        s, size, init, touch, heads = (tuple(v) if isinstance(v, list) else v
                                       for v in (got.get(a, _NONE) for a in _ARGS))
        if (isinstance(s, str) and s in SURFACES and isinstance(size, tuple) and len(size) == 2
                and all(isinstance(v, int) for v in size) and isinstance(init, tuple)
                and all(isinstance(v, str) for v in init) and isinstance(touch, bool) and isinstance(heads, bool)):
            keys.append((s, size, init, touch, heads))
    return keys


def _group(item):
    return next((m.args[0] for m in item.iter_markers("xdist_group") if m.args), None)


def module_keys(request):
    """The keys of the tests this worker runs from the module, first use first: the whole module when
    serial, the requesting test's xdist group (conftest's run of CHUNK tests) under xdist."""
    first = request._pyfuncitem
    items = [i for i in request.session.items if i.path == first.path]
    if hasattr(request.config, "workerinput"):
        items = [i for i in items if _group(i) == _group(first)]
    keys = []
    for item in items:
        for key in mount_keys(item):
            if key not in keys:
                keys.append(key)
    return keys[:MAX_PREPARED]


@pytest.fixture(scope="module")
def mount(browser, built, tmp_path_factory, request):
    """One surface on its own page (module docstring). Its contexts are the module's, closed at its end;
    its file is the worker's, so every module loads the same URL. The keys its tests name are opened
    here, in setup (`module_keys`, `Mounter.prepare`)."""
    m = Mounter(browser, tmp_path_factory.getbasetemp() / "component", built.fragment)
    for key in module_keys(request):
        m.prepare(*key)
    yield m
    m.pages.close()


def measure(n=8, surface="ranks"):
    """Median ms of a full-page load in a new context (open_at) against a mount, each drawn."""
    import tempfile
    import build
    from playwright.sync_api import sync_playwright
    from test_render import open_at
    folder = pathlib.Path(tempfile.mkdtemp())
    full = folder / "index.html"
    made = build.render()
    full.write_text(made.page, encoding="utf-8")
    build.write_heads(folder)
    out = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        try:
            m = Mounter(b, folder, made.fragment)
            m(surface)                                   # warm: the first open of each pays once
            open_at(b, full, (360, 740), "#" + SURFACES[surface])[0].close()
            for name, run in (("full", lambda: open_at(b, full, (360, 740), "#" + SURFACES[surface])[0].close()),
                              ("mount", lambda: m(surface))):
                ts = []
                for _ in range(n):
                    t = time.perf_counter()
                    run()
                    ts.append((time.perf_counter() - t) * 1000)
                out[name] = round(statistics.median(ts))
            m.pages.close()
        finally:
            b.close()
            shutil.rmtree(folder, ignore_errors=True)
    return out


if __name__ == "__main__":      # python tests/component.py: the two costs, measured on this machine now
    import conftest  # noqa: F401  (points the build at tests/fixtures)
    print(measure())

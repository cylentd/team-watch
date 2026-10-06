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

The first load of a page in a browser costs ~1 s either way; both pay it once per worker.

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
import functools
import pathlib
import re
import shutil
import statistics
import sys
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
            "preview": "preview", "schedule": "schedule"}
DRAWN = "document.getElementById('view').children.length > 0"


def css_parts(leaf):
    """Every CSS part but those scope.json fences only to other views."""
    fenced = scope_css.load(assemble.SCOPE)["fenced"]
    return [rel for rel in assemble.manifest("css")
            if rel not in fenced or leaf in fenced[rel] or any(r[0] in "#." for r in fenced[rel])]


def injected(fragment):
    """The `const NAME = ...;` lines a build injected (its fragment's `/*__HEADS__*/`), as one string."""
    return fragment.rsplit("<script>\n", 1)[1].split("\nconst COPY = ", 1)[0]


@functools.lru_cache(maxsize=None)
def component_html(surface, data):
    """The document one mounted surface loads, assembled once per surface per worker."""
    import build
    fences = scope_css.load(assemble.SCOPE)["fenced"]
    css = "".join(assemble.part_text("css", rel, fences) for rel in css_parts(SURFACES[surface]))
    body = assemble.shell_html().replace(assemble.PLACEHOLDER["css"], css, 1)
    body = body.replace(assemble.PLACEHOLDER["js"], assemble.concat("js", banners=False), 1)
    body = body.replace("/*__HEADS__*/", data, 1)
    return f"{build.document_head()}\n{body}\n</body>\n</html>\n"


_FILES = {}     # surface -> its file's URL, one file per worker: a stable URL keeps Chromium's compiled script


class Mounter:
    """`mount(surface, size=(w, h), init=(script, ...), touch=False)` -> (page, errors)."""

    def __init__(self, browser, folder, fragment):
        self.browser, self.folder, self.data, self.pages = browser, pathlib.Path(folder), injected(fragment), SharedPages()

    def url(self, surface, heads=False):
        key = (surface, str(self.folder), heads)
        if key not in _FILES:
            folder = self.folder / "heads" if heads else self.folder     # the headshots beside the page, as served
            folder.mkdir(parents=True, exist_ok=True)
            if heads:
                import build
                build.write_heads(folder)
            p = folder / f"{surface}.html"
            p.write_text(component_html(surface, self.data), encoding="utf-8")
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

    def __call__(self, surface, size=(360, 740), init=(), touch=False, heads=False):
        url = self.url(surface, heads)
        _, page, errors = self.pages.get((surface, tuple(size), tuple(init), touch, heads),
                                         lambda: self._open(size, init, touch))
        if page.url.startswith("file:"):
            page.evaluate("() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} }")
            page.goto("about:blank")
        errors.clear()
        page.goto(url, timeout=LOAD_MS)
        page.wait_for_function(DRAWN, timeout=LOAD_MS)
        if errors:
            pytest.fail(f"the {surface} component raised while loading: {errors[:3]}", pytrace=False)
        return page, errors


@pytest.fixture(scope="module")
def mount(browser, built, tmp_path_factory):
    """One surface on its own page (module docstring). Its contexts are the module's, closed at its end;
    its file is the worker's, so every module loads the same URL."""
    m = Mounter(browser, tmp_path_factory.getbasetemp() / "component", built.fragment)
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

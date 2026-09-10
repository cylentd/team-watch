"""The rendered page, in Chromium, against a golden snapshot.

What one run captures, for every surface and its main toggles, at a desktop and a phone width:
`#view` and `#drawer` markup (headshot data URIs elided) and the computed style of the first
element carrying each class the CSS defines, over the properties a theme change would move.
A refactor that promises "no visual change" is proved here by an empty diff; an intended change
regenerates the golden with `pytest --update-golden` and the diff is the review.

Deterministic by construction: fixture inputs, Math.random seeded before load, external requests
(Google Fonts) blocked so fallback fonts always apply, reduced-motion so no animation is mid-flight.
"""
import json
import re

import pytest

pytestmark = pytest.mark.render

GOLDEN_FILE = "render.json"
VIEWPORTS = {"desk": (1400, 900), "phone": (390, 844)}
PROPS = ["color", "background-color", "border-top-color", "border-top-style", "border-top-width",
         "padding-top", "padding-left", "margin-top", "gap", "font-family", "font-size",
         "font-weight", "letter-spacing", "line-height", "opacity", "display", "grid-template-columns",
         "transition-duration"]

# (state name, how to reach it from a fresh load). Each is a list of steps: ("click", selector) or
# ("eval", js). The nav is clicked, not set, so the wiring is exercised too.
STATES = [
    ("teams-yahoo", []),
    ("teams-espn", [("eval", "VIEW='espn'; render()")]),
    ("teams-drawer", [("click", ".row")]),
    ("pool", [("click", ".navitem[data-s='pool']")]),
    ("pool-drawer", [("click", ".navitem[data-s='pool']"), ("click", "[data-pool]")]),
    ("parlay-underdog", [("click", ".navitem[data-s='parlay']")]),
    ("parlay-dk", [("click", ".navitem[data-s='parlay']"), ("click", "[data-parlaybook='dk']")]),
    ("parlay-dk-mine", [("click", ".navitem[data-s='parlay']"), ("click", "[data-parlaybook='dk']"),
                        ("click", "[data-preset='mine']")]),
    ("dfs-yahoo", [("click", ".navitem[data-s='dfs']")]),
    ("dfs-dk", [("click", ".navitem[data-s='dfs']"), ("click", "[data-dfssite='dk']")]),
    ("dfs-explain", [("click", ".navitem[data-s='dfs']"), ("click", "[data-explain]")]),
    ("news", [("click", ".navitem[data-s='news']")]),
]

SEED = """
(() => { let s = 0x2f6e2b1; Math.random = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; })();
"""

PROBE = """
(props) => {
  const classes = new Set();
  for (const sheet of document.styleSheets) {
    let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
    const walk = rs => { for (const r of rs) { if (r.selectorText) for (const m of r.selectorText.matchAll(/\\.([A-Za-z_][\\w-]*)/g)) classes.add(m[1]); if (r.cssRules) walk(r.cssRules); } };
    walk(rules);
  }
  const out = {};
  for (const c of [...classes].sort()) {
    const el = document.querySelector("." + CSS.escape(c));
    if (!el) continue;
    const cs = getComputedStyle(el);
    out[c] = props.map(p => cs.getPropertyValue(p)).join("|");
  }
  const strip = h => h.replace(/data:image\\/webp;base64,[A-Za-z0-9+/=]+/g, "data:webp");
  return {view: strip(document.getElementById("view").innerHTML),
          drawer: strip(document.getElementById("drawer").innerHTML),
          drawerOpen: document.getElementById("drawer").classList.contains("on"),
          styles: out};
}
"""


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        yield b
        b.close()


def open_page(browser, page_file, viewport):
    ctx = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)     # a missing control is a bug, not something to wait 30 s for
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    # Blocked externals (the font stylesheet) log "Failed to load resource"; that one is expected.
    page.on("console", lambda m: errors.append(m.text)
            if m.type == "error" and not m.text.startswith("Failed to load resource") else None)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED)
    page.goto(page_file.as_uri())
    page.wait_for_function("document.getElementById('view').children.length > 0")
    return ctx, page, errors


def drive(page, steps):
    for kind, arg in steps:
        if kind == "click":
            page.locator(arg).first.click()
        else:
            page.evaluate(arg)
    page.wait_for_timeout(50)


@pytest.fixture(scope="module")
def snapshot(browser, page_file):
    """{viewport: {state: probe}} plus every console/page error seen on the way."""
    out, errors = {}, {}
    for vp_name, vp in VIEWPORTS.items():
        out[vp_name] = {}
        for state, steps in STATES:
            ctx, page, errs = open_page(browser, page_file, vp)
            drive(page, steps)
            out[vp_name][state] = page.evaluate(PROBE, PROPS)
            if errs:
                errors[f"{vp_name}/{state}"] = errs
            ctx.close()
    return out, errors


def test_no_console_errors(snapshot):
    _, errors = snapshot
    assert errors == {}


@pytest.mark.parametrize("state", [s for s, _ in STATES])
def test_state_renders_something(snapshot, state):
    out, _ = snapshot
    for vp in VIEWPORTS:
        assert len(out[vp][state]["view"]) > 200, f"{vp}/{state}: #view is empty"
    if state.endswith("drawer"):
        assert out["desk"][state]["drawerOpen"], "drawer did not open"
        assert len(out["desk"][state]["drawer"]) > 100


def diff(golden, now, limit=25):
    lines = []
    for vp in VIEWPORTS:
        for state, _ in STATES:
            g, n = golden.get(vp, {}).get(state), now[vp][state]
            if g is None:
                lines.append(f"{vp}/{state}: no golden yet")
                continue
            for key in ("view", "drawer"):
                if g[key] != n[key]:
                    i = next((i for i, (a, b) in enumerate(zip(g[key], n[key])) if a != b), min(len(g[key]), len(n[key])))
                    lines.append(f"{vp}/{state}: #{key} differs at char {i}: ...{n[key][max(0, i-40):i+60]!r}")
            for cls in sorted(set(g["styles"]) | set(n["styles"])):
                a, b = g["styles"].get(cls), n["styles"].get(cls)
                if a != b:
                    if a is None or b is None:
                        lines.append(f"{vp}/{state}: .{cls} {'appeared' if a is None else 'vanished'}")
                    else:
                        for p, x, y in zip(PROPS, a.split("|"), b.split("|")):
                            if x != y:
                                lines.append(f"{vp}/{state}: .{cls} {p}: {x} -> {y}")
            if len(lines) > limit:
                return lines[:limit] + ["..."]
    return lines


def test_matches_golden(snapshot, update_golden):
    from conftest import GOLDEN
    out, _ = snapshot
    path = GOLDEN / GOLDEN_FILE
    if update_golden or not path.exists():
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(out, indent=0, sort_keys=True), encoding="utf-8", newline="\n")
        pytest.skip(f"golden written: {path.relative_to(GOLDEN.parents[1])}")
    golden = json.loads(path.read_text(encoding="utf-8"))
    d = diff(golden, out)
    assert d == [], "rendered page differs from tests/golden/render.json (pytest --update-golden if intended):\n" + "\n".join(d)

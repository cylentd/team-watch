"""The drive strip, rendered in Chromium against a real game's drives.

The strip's whole trick is that the field is a tilted 3D plane while every figure, ball and
goalpost is a FLAT sprite placed each frame from an invisible anchor inside that plane. Chromium
mis-sorts elements against each other in a nested preserve-3d context, so drawing the figures in
the scene slices them; measuring an anchor and drawing over the top is the only arrangement that
holds. That makes "is the man where the yard line says" a question no static reading of the code
can answer -- it is a question about what the browser did -- which is what this file asks.

The strongest check here fits a straight line. Every figure stands on the same lane across the
field, so screen-x must be an exact affine function of field position: x = a + b * pct, one (a, b)
for the whole drive. Sampling both ends of every play and fitting one line through all of it
catches a play drawn at the wrong scale, in the wrong direction, or off the absolute 0-100 scale
that api/game.py puts every drive on -- which is the bug class that cost a starting back his
headshot and a far-half drive its direction before either endpoint existed.

    pytest tests/test_strip.py          # ~8 s, needs a browser
"""
import importlib.util
import json
import pathlib
import re

import pytest

pytestmark = pytest.mark.render

REPO = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = REPO / "tests" / "fixtures" / "data" / "espn_summary.json"
PHONE = (360, 800)
DESK = (1400, 900)


def _game_module():
    spec = importlib.util.spec_from_file_location("game_fn", REPO / "api" / "game.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def shaped():
    return _game_module().shape(json.loads(FIXTURE.read_text(encoding="utf-8")))


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        yield b
        b.close()


MOUNT = """
([data, at]) => {
  const host = document.createElement("div");
  host.id = "striptest";
  document.getElementById("view").innerHTML = "";
  document.getElementById("view").appendChild(host);
  window.__ctl = stripMount(host, data, at);
  return window.__ctl.n;
}
"""

# Where the man with the ball is on screen, and where the field says he should be. The actor's box
# is already centred on its anchor (.stactor carries translate(-50%,-100%)), so its middle is the
# number to read.
PROBE = """
([i, f, hold]) => {
  window.__ctl.pose(i, f, hold, false);
  const q = s => document.querySelector("#striptest " + s);
  const turf = q(".stturf").getBoundingClientRect();
  const c = q(".stactor.carrier").getBoundingClientRect();
  return {x: c.left + c.width / 2, turfLeft: turf.left, turfWidth: turf.width};
}
"""


def open_strip(browser, page_file, shaped, drive, viewport=DESK):
    """One mounted strip, plus the page errors it logged. Externals are blocked: no fonts, no
    headshots -- the strip must place a figure whether or not his picture ever arrives."""
    ctx = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
    page = ctx.new_page()
    page.set_default_timeout(5000)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text)
            if m.type == "error" and not m.text.startswith("Failed to load resource") else None)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.goto(page_file.as_uri())
    page.evaluate(MOUNT, [shaped, drive])
    return page, ctx, errors


def fit(points):
    """Least-squares b for x = a + b*pct, and the worst residual in pixels."""
    n = len(points)
    mx = sum(p for p, _ in points) / n
    my = sum(x for _, x in points) / n
    var = sum((p - mx) ** 2 for p, _ in points)
    b = sum((p - mx) * (x - my) for p, x in points) / var
    a = my - b * mx
    return b, max(abs(x - (a + b * p)) for p, x in points)


@pytest.mark.parametrize("drive", range(5))
def test_the_figure_stands_where_the_yard_line_says(browser, page_file, shaped, drive):
    """One straight line through both ends of every play in the drive. A play drawn backwards, at
    the wrong scale, or off the absolute scale leaves the line and shows up as a residual."""
    d = shaped["drives"][drive]
    page, ctx, errors = open_strip(browser, page_file, shaped, drive)
    points = []
    for i, p in enumerate(d["plays"]):
        if p["k"] not in ("rush", "pass"):
            continue        # an incompletion and a kick both end past `to`, on purpose
        # Only spots the FEED states. A receiver does not stand on the line of scrimmage at the
        # snap -- he takes his release step while the passer drops -- so his f=0 is a choreography
        # number, and asserting on it would be asserting on the view's own arithmetic.
        if p["k"] == "rush":
            points.append((p["from"], page.evaluate(PROBE, [i, 0, 0])["x"]))
        points.append((p["to"], page.evaluate(PROBE, [i, 1, 0])["x"]))
    ctx.close()
    assert not errors, errors
    assert len(points) >= 4, f"drive {drive} gave only {len(points)} samples"
    b, worst = fit(points)
    # The drive's direction is in the SIGN: a home drive runs 0 -> 100 left to right, an away drive
    # runs the other way over the same fixed field, and `dir` is the only thing that says so.
    assert b > 0, f"screen x must grow with field position; got {b:.2f} px per percent"
    assert worst < 2.0, f"{worst:.1f}px off a straight line -- a play is drawn at the wrong spot"


def test_a_scaled_ancestor_does_not_move_the_figures_off_the_field(browser, page_file, shaped):
    """The strip opens in a dialog that grows from scale(.2), and getBoundingClientRect reports
    SCREEN pixels while the `translate` written back onto a sprite is applied in the element's own
    unscaled ones. A frame measured mid-transition therefore put every figure, goalpost and arc
    about a hundred pixels above the field -- and left them there, because nothing re-measured
    once the animation ended. Where a figure stands as a FRACTION of the field must not depend on
    what an ancestor is doing to the whole thing."""
    page, ctx, errors = open_strip(browser, page_file, shaped, 0)
    at = page.evaluate("""() => {
      const host = document.getElementById("striptest"), box = host.parentElement;
      box.style.transformOrigin = "0 0";
      const out = [];
      for (const s of [1, 0.5, 0.2]){
        box.style.transform = `scale(${s})`;
        window.__ctl.pose.bump();                       // the arc cache was measured at the old scale
        stRender(window.__ctl, 1);
        const t = document.querySelector("#striptest .stturf").getBoundingClientRect();
        const c = document.querySelector("#striptest .stactor.carrier").getBoundingClientRect();
        out.push([(c.left + c.width / 2 - t.left) / t.width, (c.bottom - t.top) / t.height]);
      }
      return out;
    }""")
    ctx.close()
    assert not errors, errors
    base = at[0]
    for s, (fx, fy) in zip((0.5, 0.2), at[1:]):
        assert abs(fx - base[0]) < .01, f"at scale {s} the figure moved {fx - base[0]:+.3f} across the field"
        assert abs(fy - base[1]) < .02, f"at scale {s} the figure moved {fy - base[1]:+.3f} up the field"
    # and he is standing ON the field, not above it -- the symptom the bug actually showed
    assert 0 < base[1] < 1.2, f"the figure's feet are at {base[1]:.2f} of the field's height"


def test_an_away_drive_runs_the_other_way(browser, page_file, shaped):
    """Same field, opposite direction. The field never flips between drives; the figures turn."""
    away = next(i for i, d in enumerate(shaped["drives"]) if d["dir"] == -1)
    p = next(q for q in shaped["drives"][away]["plays"] if q["k"] == "rush" and q["to"] != q["from"])
    i = shaped["drives"][away]["plays"].index(p)
    gained = (p["to"] - p["from"]) * -1 > 0
    page, ctx, errors = open_strip(browser, page_file, shaped, away)
    start = page.evaluate(PROBE, [i, 0, 0])["x"]
    end = page.evaluate(PROBE, [i, 1, 0])["x"]
    ctx.close()
    assert not errors, errors
    # An away drive gains ground by moving LEFT across the screen, because 0 is the home goal line.
    assert (end < start) == gained, f"{p['tx'][:60]!r} drew the wrong way"


def test_the_caption_box_never_changes_height(browser, page_file, shaped):
    """A box that grows for a two-line pass and shrinks for a one-line run makes the whole panel
    jump under the reader's thumb during a replay. Measured at 360px, where captions wrap."""
    page, ctx, errors = open_strip(browser, page_file, shaped, 0, PHONE)
    heights = set()
    for i in range(len(shaped["drives"][0]["plays"])):
        page.evaluate("i => stRender(window.__ctl, i + 1)", i)
        heights.add(round(page.evaluate('() => document.querySelector("#striptest .stcap").offsetHeight')))
    ctx.close()
    assert not errors, errors
    assert len(heights) == 1, f"the caption box took {sorted(heights)} across one drive"


def test_the_panel_fits_a_360px_phone(browser, page_file, shaped):
    """Nine readers in ten are on a phone. Two things in the strip scroll sideways on purpose --
    the drive chart and, in Pan, the field -- and nothing else may, the panel itself least of all.
    Measured against the strip's own host: the page around it has chrome of its own."""
    page, ctx, errors = open_strip(browser, page_file, shaped, 0, PHONE)
    over = page.evaluate("""() => {
      const bad = [], host = document.getElementById("striptest");
      for (const el of host.querySelectorAll("*")){
        if (el.closest(".stview") || el.closest(".stdrives")) continue;
        // Text hidden for sighted readers but kept for screen readers is a 1px box holding a
        // whole phrase on purpose. It is clipped, not scrollable, and clip-path is what says so.
        if (getComputedStyle(el).clipPath !== "none") continue;
        if (el.scrollWidth > el.clientWidth + 1) bad.push(el.className + " " + el.scrollWidth + ">" + el.clientWidth);
      }
      return {bad, wide: host.scrollWidth - host.clientWidth,
              right: Math.round(host.getBoundingClientRect().right)};
    }""")
    ctx.close()
    assert not errors, errors
    assert over["bad"] == [], over["bad"]
    assert over["wide"] <= 0, f"the panel scrolls {over['wide']}px sideways"
    assert over["right"] <= PHONE[0], f"the panel's right edge is at {over['right']}px"


def test_both_goalposts_are_drawn_with_a_measured_crossbar(browser, page_file, shaped):
    """The uprights are flat sprites; only the crossbar's direction comes from the scene. A post
    whose two anchors land in the same place draws a zero-length crossbar, which is the symptom of
    the anchors having been lost inside the 3D context."""
    page, ctx, errors = open_strip(browser, page_file, shaped, 0)
    page.evaluate("() => stRender(window.__ctl, 1)")
    posts = page.evaluate("""() => [...document.querySelectorAll("#striptest .stpost path")]
      .map(p => p.getAttribute("d"))""")
    depth = page.evaluate("""() => {
      const r = s => document.querySelector("#striptest " + s).getBoundingClientRect();
      return r(".a-fA").top - r(".a-nA").top;
    }""")
    ctx.close()
    assert not errors, errors
    assert len(posts) == 2 and all(d and d.startswith("M") for d in posts), posts
    # The far anchor sits deeper into the screen than the near one, so it renders HIGHER up.
    assert depth < -4, f"the two post anchors are {depth:.1f}px apart vertically; the crossbar is flat"


@pytest.mark.parametrize("drive", range(5))
def test_the_chevrons_run_from_the_ball_to_the_end_zone_being_attacked(browser, page_file, shaped, drive):
    """The ground still to cover. On an away drive that is the LEFT half of the same fixed field,
    so the band has to start at the left edge and stop at the ball, not the other way round."""
    d = shaped["drives"][drive]
    page, ctx, errors = open_strip(browser, page_file, shaped, drive)
    page.evaluate("() => stRender(window.__ctl, 1)")
    box = page.evaluate("""() => {
      const r = s => { const e = document.querySelector("#striptest " + s); return e && e.getBoundingClientRect(); };
      const a = r(".stahead"), turf = r(".stturf"), ball = r(".stactor.carrier");
      return {aL: a.left, aR: a.right, tL: turf.left, tR: turf.right, ball: ball.left + ball.width / 2};
    }""")
    ctx.close()
    assert not errors, errors
    # The band lives on the field's centre lane, which perspective draws ~30px narrower than the
    # turf's own bounding box (that box is the near touchline, the widest part). So the check is
    # "which side of the ball, and does it cover the ground", not "does it touch the edge".
    if d["dir"] > 0:
        assert box["aL"] > box["ball"], "the chevrons start behind the ball"
        assert box["aR"] - box["ball"] > (box["tR"] - box["ball"]) * .7, "the band stops short"
    else:
        assert box["aR"] < box["ball"], "the chevrons start ahead of the ball"
        assert box["ball"] - box["aL"] > (box["ball"] - box["tL"]) * .7, "the band stops short"


CLASS_RE = re.compile(r"^\.([A-Za-z_][\w-]*)((?::[\w-]+(?:\([^)]*\))?)*)$")


def test_no_class_the_strip_renders_is_styled_by_a_bare_rule_elsewhere(browser, page_file, shaped):
    """The strip is one component dropped into a page with its own CSS, and a bare `.x{}` rule
    anywhere reaches inside it however the strip's own selectors are scoped. This is not
    hypothetical: roster.css's `.nm` set grid-area on the caption's name and tore the play card's
    grid apart, and nothing but looking at it would have said so. Hence the st- prefix on every
    class the strip renders -- and hence this, which fails the moment one goes missing."""
    page, ctx, errors = open_strip(browser, page_file, shaped, 0)
    page.evaluate("() => stRender(window.__ctl, 1)")
    used = page.evaluate("""() => {
      const out = new Set();
      for (const el of document.getElementById("striptest").querySelectorAll("*"))
        for (const c of el.classList) out.add(c);
      return [...out];
    }""")
    ctx.close()
    assert not errors, errors
    src = REPO / "design" / "src" / "css"
    bare = {}
    for f in sorted(src.rglob("*.css")):
        if "surface/strip" in f.as_posix():
            continue
        for head in re.findall(r"^([^@{}/][^{}]*)\{", f.read_text(encoding="utf-8"), re.M):
            for one in head.split(","):
                m = CLASS_RE.match(one.strip())
                if m:
                    bare.setdefault(m.group(1), f.relative_to(src).as_posix())
    clash = sorted((c, bare[c]) for c in used if c in bare)
    assert clash == [], f"styled from outside the strip: {clash}"


SITE = "http://strip.test/"


def open_roster(page):
    """The nav is two levels, and the Teams group holds Roster and Waivers. Naming the leaf as
    well as the group is what keeps this test pointed at the roster when the group's default
    moves -- which it did, the day Waivers became tiered cards."""
    page.click(".navitem[data-s='teams']")
    page.click("[data-leaf='roster']")


def served(browser, page_file, shaped):
    """The page with a real origin and a real /api/game behind it, without running a server.

    Two things only happen over http: the fetch at all (from file:// the strip says so and stops,
    which is PAGE_SERVED's whole job), and the endpoint's own JSON. Both are routed here, so this
    exercises the same code path a deployed page takes."""
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(5000)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    html = page_file.read_text(encoding="utf-8")
    calls = []

    def handle(route):
        url = route.request.url
        if "/api/game" in url:
            calls.append(url)
            return route.fulfill(status=200, content_type="application/json", body=json.dumps(shaped))
        if url.rstrip("/") == SITE.rstrip("/"):
            return route.fulfill(status=200, content_type="text/html", body=html)
        route.abort()

    page.route(re.compile(r"^https?://"), handle)
    page.goto(SITE)
    return page, ctx, errors, calls


def test_a_week_in_the_game_log_opens_that_game_over_the_profile(browser, page_file, shaped):
    """The second way in. It opens OVER the profile rather than instead of it: the reader tapped a
    week while reading about a player, and closing the strip has to put him back where he was."""
    page, ctx, errors, calls = served(browser, page_file, shaped)
    open_roster(page)
    page.click(".row:has-text('Jahmyr Gibbs')")
    # The game log is the Log pane since the modal went to tabs (2026-09-22); it is one tap in,
    # not on screen at open.
    page.click("#modal [data-pftab='log']")
    week = page.locator("#modal .pf-wk").first
    assert week.count(), "no week in the game log opens a game"
    week.click()
    page.wait_for_selector("#stripmodal .stturf")
    state = page.evaluate("""() => ({
      strip: document.getElementById("stripmodal").classList.contains("on"),
      profile: document.getElementById("modal").classList.contains("on"),
      title: document.querySelector("#st-title").textContent,
      plays: document.querySelectorAll("#stripmodal .stdrives button").length,
    })""")
    page.keyboard.press("Escape")
    after = page.evaluate("""() => ({
      strip: document.getElementById("stripmodal").classList.contains("on"),
      profile: document.getElementById("modal").classList.contains("on"),
    })""")
    ctx.close()
    assert not errors, errors
    assert calls, "the strip never asked /api/game"
    assert state["strip"] and state["profile"], "the strip replaced the profile instead of stacking"
    assert state["plays"] == len(shaped["drives"])
    assert "at" in state["title"]
    # Escape closes the topmost dialog, not both: the reader is put back in the profile.
    assert after["profile"] and not after["strip"], "Escape closed the profile too"


# A board covering all three cases in the fixture schedule: clubs with a game that carries an
# ESPN id (DET and SEA play each other in week 2; SF hosts KC in week 3), a club whose only game
# has no id because its history row predates ff-jarvis carrying the column (LAR), and a club with
# no game at all (LAC). Planted rather than fetched: no /api/live behind this.
LIVE_REPLY = """
GD_DATA = {league:"espn", week:2, me:{team:"Mine", live:0, projected:0, winPct:.5, lineup:[
    {slot:"WR", starter:true, name:"Amon-Ra St. Brown", team:"DET", actual:31.5, projected:16, started:true, injury:"ACTIVE"},
    {slot:"QB", starter:true, name:"Brock Purdy", team:"SF", actual:null, projected:25, started:false, injury:"ACTIVE"},
    {slot:"RB", starter:true, name:"Kimani Vidal", team:"LAC", actual:null, projected:8, started:false, injury:"ACTIVE"}]},
  opponent:{team:"Theirs", live:0, projected:0, winPct:.5, lineup:[
    {slot:"WR", starter:true, name:"Jaxon Smith-Njigba", team:"SEA", actual:null, projected:15, started:false, injury:"ACTIVE"},
    {slot:"QB", starter:true, name:"Matthew Stafford", team:"LAR", actual:null, projected:19, started:false, injury:"ACTIVE"},
    {slot:"RB", starter:true, name:"Kyren Williams", team:"LAR", actual:null, projected:14, started:false, injury:"ACTIVE"}]}};
GD_AT = Date.now();
"""


def test_a_name_on_the_live_board_opens_his_clubs_game(browser, page_file, shaped):
    """The first way in. Only a club with a game the schedule has an ESPN id for gets the
    affordance -- a game with no id, and a club with no game, both stay plain rows rather than
    become a control that does nothing."""
    page, ctx, errors, calls = served(browser, page_file, shaped)
    page.evaluate(LIVE_REPLY)
    page.click(".navitem[data-s='gameday']")
    page.wait_for_selector(".gdcell")
    opens = page.evaluate("""() => [...document.querySelectorAll(".gdcell:not(.empty)")]
      .map(c => [c.querySelector(".gdclub") && c.querySelector(".gdclub").textContent,
                 c.hasAttribute("data-gdopen")])""")
    page.click("[data-gdopen='DET']")
    page.wait_for_selector("#stripmodal .stturf")
    drive = page.evaluate('() => document.querySelector("#stripmodal .stdrives [aria-selected=\\"true\\"]").textContent')
    ctx.close()
    assert not errors, errors
    assert calls, "the strip never asked /api/game"
    assert dict(opens) == {"DET": True, "SEA": True, "SF": True,   # a game, with an id
                           "LAR": False,                            # a game, but no id yet
                           "LAC": False}                            # no game at all
    # He is opened at the drive he was last on the field for, not at drive 1.
    assert drive.strip(), "no drive is selected"


def test_the_same_game_is_only_fetched_once(browser, page_file, shaped):
    """Re-opening a game the reader just looked at must not cost another ESPN read. The endpoint's
    edge cache is what protects ESPN from many readers; this is what protects it from one."""
    page, ctx, errors, calls = served(browser, page_file, shaped)
    open_roster(page)
    page.click(".row:has-text('Jahmyr Gibbs')")
    page.click("#modal [data-pftab='log']")      # the game log is the Log pane now
    for _ in range(2):
        page.locator("#modal .pf-wk").first.click()
        page.wait_for_selector("#stripmodal .stturf")
        page.keyboard.press("Escape")
        page.wait_for_timeout(50)
    ctx.close()
    assert not errors, errors
    assert len(calls) == 1, f"asked /api/game {len(calls)} times for one game"


def test_every_play_of_every_drive_draws(browser, page_file, shaped):
    """The whole fixture, start to finish: a home touchdown drive, an away drive, a sack that
    becomes a fumble recovery, and a field goal. Any of them throwing is the bug."""
    page, ctx, errors = open_strip(browser, page_file, shaped, 0)
    for d in range(len(shaped["drives"])):
        page.evaluate("d => stShowDrive(window.__ctl, d)", d)
        n = len(shaped["drives"][d]["plays"])
        for i in range(n):
            for f in (0, .35, .7, 1):
                page.evaluate("([i, f]) => stRender(window.__ctl, i + f, f >= 1 ? .5 : 1)", [i, f])
    ctx.close()
    assert not errors, errors

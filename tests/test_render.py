"""The rendered page, in Chromium, against a golden snapshot.

What one run captures, for every surface and its main toggles, at a desktop and a phone width:
`#view`, `#drawer` and `#modal` markup (headshot data URIs elided) and the computed style of the first
element carrying each class the CSS defines, over the properties a theme change would move.
A refactor that promises "no visual change" is proved here by an empty diff; an intended change
regenerates the golden with `pytest --update-golden` and the diff is the review.

Deterministic by construction: fixture inputs, Math.random seeded and Date.now pinned before load
(the gallery hides games that have kicked off), external requests
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
# A reply planted rather than fetched. No server runs in this test, and SEED pins Date.now(), so
# GD_AT is always fresh and gdEnsure() never reaches for the network. The rows are chosen to
# cover what the markup branches on: played against not-yet, a designation badge, and a bench.
LIVE_REPLY = """
GD_DATA = {
  league: "espn", week: 2, asof: "2026-09-20T17:04:00+00:00",
  me: {team: "Purdy Big in Japan", live: 31.5, projected: 131.7, winPct: 0.76, lineup: [
    {slot:"QB", starter:true,  name:"Brock Purdy",       team:"SF",  actual:null, projected:25.7, started:false, injury:"ACTIVE"},
    {slot:"WR", starter:true,  name:"Amon-Ra St. Brown", team:"DET", actual:31.5, projected:16.0, started:true,  injury:"ACTIVE"},
    {slot:"RB", starter:true,  name:"De'Von Achane",     team:"MIA", actual:null, projected:14.9, started:false, injury:"QUESTIONABLE"},
    {slot:"D/ST", starter:true,name:"Seahawks D/ST",     team:"SEA", actual:null, projected:9.2,  started:false, injury:"ACTIVE"},
    {slot:"BE", starter:false, name:"Jared Goff",        team:"DET", actual:37.8, projected:23.2, started:true,  injury:"ACTIVE"},
    {slot:"BE", starter:false, name:"Jordan Mason",      team:"MIN", actual:null, projected:0.0,  started:false, injury:"OUT"}]},
  opponent: {team: "TeamMinh", live: -2.0, projected: 92.7, winPct: 0.24, lineup: [
    {slot:"QB", starter:true,  name:"Justin Herbert",    team:"LAC", actual:null, projected:24.3, started:false, injury:"ACTIVE"},
    {slot:"WR", starter:true,  name:"Jaxon Smith-Njigba",team:"SEA", actual:null, projected:15.0, started:false, injury:"ACTIVE"},
    {slot:"RB", starter:true,  name:"Chase Brown",       team:"CIN", actual:null, projected:12.4, started:false, injury:"ACTIVE"},
    {slot:"D/ST", starter:true,name:"Lions D/ST",        team:"DET", actual:-2.0, projected:5.1,  started:true,  injury:"ACTIVE"},
    {slot:"BE", starter:false, name:"Drake Maye",        team:"NE",  actual:null, projected:22.4, started:false, injury:"ACTIVE"}]}
};
GD_AT = Date.now();
/* SEED pins Date.now, so these three points are the same every run -- enough for the trace to
   draw a shape without making the golden depend on when it was taken. */
GD_WP = [[Date.now() - 900000, 0.38], [Date.now() - 450000, 0.61], [Date.now(), 0.76]];
"""

# Points landing while you watch: the row lights and the delta takes the projection's slot.
LIVE_MOVED = "GD_PULSE = {'Amon-Ra St. Brown': 13.5, 'Lions D/ST': -2.0};"

# And the same news after time away, which is stated once instead of chipped onto every row.
LIVE_AWAY = """
GD_CATCHUP = {swing: {me: 21.5, opp: 3.0}, movers: [
  {name: "Amon-Ra St. Brown", delta: 13.5},
  {name: "Cam Skattebo", delta: 12.4},
  {name: "Lions D/ST", delta: -2.0}]};
"""

# The nav is two levels since 2026-09-21: a group, then the view. Reaching a view is therefore
# two clicks, not one, except in a group of one where no sub-row is drawn at all. Spelling both
# out here (rather than trusting the group button's "return me to where I was") keeps a state
# reachable in the same way no matter which state ran before it.
GROUP = {"roster": "teams", "waivers": "teams",
         "ranks": "scouting", "board": "scouting", "movers": "scouting", "matchups": "scouting", "usage": "scouting", "news": "scouting",
         "parlay": "bets", "build": "bets", "dfs": "bets", "live": "gameday"}


def go(leaf):
    steps = [("click", f".navitem[data-s='{GROUP[leaf]}']")]
    if len([k for k, g in GROUP.items() if g == GROUP[leaf]]) > 1:
        steps.append(("click", f"[data-leaf='{leaf}']"))
    return steps


def bdpick(q):
    """Fill a Board slot the way a reader does: the app's own search sheet, opened with a slot to
    fill instead of a profile to open. Driving it through searchOpen/searchPick rather than
    calling bdAdd is the point -- the handoff is the part that would break silently."""
    return [("click", "[data-bdadd]"),
            ("eval", f"document.getElementById('search-q').value = {q!r}; searchPaint()"),
            ("click", "#sr-0")]


MOVERS = go("movers")

STATES = [
    # The page opens on the Board since 2026-09-24, so the roster states navigate there.
    ("teams-yahoo", go("roster")),
    ("teams-espn", [("eval", "VIEW='espn'; render()")] + go("roster")),
    ("teams-modal", go("roster") + [("click", ".row")]),   # Joe Burrow: no matchup profile, the quiet state
    # One league at a time since v2: the team on screen picks the cards, tiers, hero and rail.
    # SEED is a Saturday, so these are wire-watch mode (the rail leads, every row shown).
    ("waivers-espn", [("eval", "VIEW='espn'; render()")] + go("waivers")),
    ("waivers-yahoo", go("waivers")),
    ("waivers-claimday", [("eval", 'Date.now = () => Date.parse("2026-09-22T12:00:00Z")')] + go("waivers")),
    # The first card that flips: on a phone the Must claim, on a desktop (where a Must claim lies
    # open with no flip) the first Worth a claim.
    ("waivers-flipped", [("eval", "VIEW='espn'; render()")] + go("waivers") + [("click", ".wvc-flip >> visible=true")]),
    ("waivers-folds", go("waivers") + [("click", "summary.wvfold-s >> nth=0"),
                                       ("click", "summary.wvfold-s >> nth=1")]),   # spec + stash open
    # The modal is panes since 2026-09-22, so each one is its own state: the tab bar only renders
    # the pane that is open, and a pane that renders nothing is dropped from the bar entirely (a
    # back has no target depth, a passer no red zone, a player with no pedigree no Bio). PF_TAB is
    # module state that survives an open, so every state below spells out the tab it wants rather
    # than trusting whichever one ran before it.
    ("profile-wr-modal", go("roster") + [("click", ".row:has-text('Amon-Ra St. Brown')"), ("click", "#modal [data-pftab='usage']")]),
    ("profile-wr-matchup-modal", go("roster") + [("click", ".row:has-text('Amon-Ra St. Brown')"), ("click", "#modal [data-pftab='matchup']")]),
    ("profile-wr-log-modal", go("roster") + [("click", ".row:has-text('Amon-Ra St. Brown')"), ("click", "#modal [data-pftab='log']")]),
    ("profile-rb-modal", go("roster") + [("click", ".row:has-text('Chase Brown')"), ("click", "#modal [data-pftab='matchup']")]),
    ("profile-rb-bio-modal", go("roster") + [("click", ".row:has-text('Chase Brown')"), ("click", "#modal [data-pftab='bio']")]),
    # SF's starters-out count is null (no snap-count release yet) -- the shape live data shows
    # until ff-jarvis lands its new fields -- so the line falls back to the plain injury-report
    # count instead of the starters-out cell DET and CIN cover. Kittle is SF only on the ESPN
    # roster fixture, so this is the one state that switches leagues before opening a profile.
    ("profile-te-matchup-modal", [("eval", "VIEW='espn'; render()")] + go("roster") +
                                 [("click", ".row:has-text('George Kittle')"),
                                  ("click", "#modal [data-pftab='matchup']")]),
    ("profile-bye-modal", go("roster") + [("click", ".row:has-text('Jahmyr Gibbs')")]),
    # The Board: the leaderboard it arrives as, the same board as a duel, and a WR board because
    # that position publishes the most elite bars -- the one mark that is drawn only on the lanes
    # whose axis has a published threshold.
    ("board", go("board")),
    # Chase Brown and Skattebo rather than two arbitrary backs: both are in the fixture's archetype
    # block, so this state is the only one that reviews a rendered role and style label. Skattebo
    # carries a null style with its reason ("career carries < 250") and a null role with his, which
    # is the path a blank would silently pass. Picking players the block does not cover renders the
    # lanes and nothing else, which is what this state did before.
    ("board-two", go("board") + bdpick("chase brown") + bdpick("skattebo")),
    # The quarterback label: a style with no role beside it, because role is not a field for the
    # position, and the reason has to render where the word would be. Burrow rather than the
    # fixture's flag-carrying passer: wanted_slugs deliberately excludes the usage grid (build.py),
    # and with no pool block in the fixture the only archetype records that survive the cut are
    # roster and prop players. The `goal_line_runner` flag is therefore not reachable from a
    # fixture-built page at all, and is checked against the live build instead.
    ("board-qb", go("board") + [("click", "[data-bdpos='QB']")] + bdpick("burrow")),
    ("board-wr", go("board") + [("click", "[data-bdpos='WR']")]),
    # The list's second page: the pager turns it in place (a list since 2026-09-26).
    ("board-wr-page2", go("board") + [("click", "[data-bdpos='WR']"), ("click", ".bd-pager [data-bdpage='2']")]),
    # Players > Ranks (2026-09-26): a position's tiers, and FLEX with its "RB3" per row.
    ("ranks", go("ranks")),
    ("ranks-flex", go("ranks") + [("click", "[data-rkpos='FLEX']")]),
    # Movers, the Board's second mode since 2026-09-25 (a view of its own before): the fixture
    # falls back to the sample pool, which has share moves, so it sorts on them; -wait blanks every
    # move to reach the week-1 path, where the list ranks by share under one line saying why.
    ("board-movers", MOVERS),
    ("board-movers-wait", [("eval", "POOL.forEach(r => { r.dShare = null; })")] + MOVERS),
    # A mover opens the player's profile, the same modal the Leaders board opens (2026-09-25).
    ("board-movers-modal", MOVERS + [("click", "[data-poolslug]")]),
    # The usage grid: the default RB level view on the newest week most teams have played, the
    # same grid as week-over-week change (the mode the level view cannot show; the week and the
    # reading sit in the panel the bar's last chip opens since 2026-09-25), a QB grid because its
    # columns are the ones with no counterpart anywhere else in the app, and the profile modal.
    # Matchups (2026-09-25): WR opens with a backed start (Higgins, whom Pitcher List says to sit),
    # a sit, and a sit's counter-evidence; QB is the unbacked call with Pitcher List agreeing; RB
    # carries the best spot; a row opens the profile; and a week with nothing yet (no calls, no
    # column, no graded week) says each of those in its own place. LIVE_STARTSIT is a const, so
    # the null block (no calls file) is pinned in tests/test_startsit.py instead.
    ("matchups", go("matchups")),
    ("matchups-qb", go("matchups") + [("click", "[data-mupos='QB']")]),
    ("matchups-rb", go("matchups") + [("click", "[data-mupos='RB']")]),
    ("matchups-modal", go("matchups") + [("click", "[data-muslug]")]),
    ("matchups-empty", [("eval", "Object.assign(LIVE_STARTSIT, {calls: [], pl: [], article: null, record: null})")]
                       + go("matchups")),
    ("usage", go("usage")),
    ("usage-panel", go("usage") + [("click", "[data-upanel]")]),
    ("usage-change", go("usage") + [("click", "[data-upanel]"), ("click", "[data-umode='change']")]),
    ("usage-qb", go("usage") + [("click", "[data-upos='QB']")]),
    ("usage-modal", go("usage") + [("click", "[data-usage]")]),
    # Bets since 2026-09-25: Slips (leaf `parlay`) and Build, the book in the settings panel the
    # bar's last chip opens, and the slip in a sheet the tray opens.
    ("parlay-underdog", go("parlay")),
    ("parlay-dk", go("parlay") + [("click", "[data-betspanel]"), ("click", "[data-parlaybook='dk']")]),
    ("parlay-dk-mine", go("parlay") + [("click", "[data-betspanel]"), ("click", "[data-parlaybook='dk']"),
                                       ("click", "[data-tray]"), ("click", "[data-preset='mine']")]),
    ("build-underdog", go("build")),
    ("build-panel", go("build") + [("click", "[data-betspanel]")]),
    ("parlay-sheet", go("parlay") + [("click", "[data-loadslip]"), ("click", "[data-tray]")]),
    ("dfs-yahoo", go("dfs")),
    # DFS since 2026-09-25: the strategy as the bar's chips, the site and "how this works" in the
    # panel its last chip opens.
    ("dfs-dk", go("dfs") + [("click", "[data-dfspanel]"), ("click", "[data-dfssite='dk']")]),
    ("dfs-contrarian", go("dfs") + [("click", "[data-topmode='contrarian']")]),
    ("dfs-explain", go("dfs") + [("click", "[data-dfspanel]"), ("click", "[data-explain]")]),   # the drawer
    ("news-injury", go("news") + [("click", "[data-newscat='injury']")]),
    ("news", go("news")),
    # A fresh browser has no saved passphrase, so this is the locked state: the form, not just
    # the composer. Deterministic because the day's counter starts at 0 in empty localStorage.
    ("chat-open", [("click", "#chatfab")]),
    ("chat-ready", [("eval", "chatSetPass('x')"), ("click", "#chatfab")]),
    # The reason it is a floating panel and not a tab: it stays open over another surface, so
    # you can read a player's row while asking about him. #view must still be Movers here.
    ("chat-over-movers", MOVERS + [("click", "#chatfab")]),
    # Player search: idle (the roster, since a fresh browser has no recents), and a query that
    # hits a typo, a hyphenated name and two leagues' tags at once.
    ("search-idle", [("click", "#navsearch")]),
    ("search-typed", [("click", "#navsearch"),
                      ("eval", "document.getElementById('search-q').value = 'brwon'; searchPaint()")]),
    ("live-board", [("eval", LIVE_REPLY)] + go("live")),
    ("live-moved", [("eval", LIVE_REPLY + LIVE_MOVED)] + go("live")),
    ("live-away", [("eval", LIVE_REPLY + LIVE_AWAY)] + go("live")),
    # Both states plant a reply so gdEnsure() finds it fresh and never reaches the network:
    # there is no server behind this test, and a failed fetch would land whenever it landed.
    # The expired-cookie message is the one failure worth seeing drawn, because it is the one
    # the reader can act on -- and it must appear OVER the last good board, not instead of it.
    ("live-expired", [("eval", LIVE_REPLY
                       + "GD_ERR = 'ESPN cookies have expired. Re-copy SWID and espn_s2.';")]
                     + go("live")),
    # Nothing has ever loaded and the first call failed: the one path where the board has no
    # numbers to keep, so the retry has to be drawn or a reload is the only way out.
    # A first-ever visit, before any reply has been stored: the skeleton holds the rows' space
    # so nothing jumps when the numbers land. GD_BUSY pins it, as below.
    ("live-skeleton", [("eval", "GD_DATA = null; GD_BUSY = true;")] + go("live")),
    # GD_BUSY pins it: with no data, gdEnsure() would otherwise start a fetch that fails
    # whenever it fails and overwrites the message mid-snapshot.
    ("live-cold-error", [("eval", "GD_BUSY = true;"
                          " GD_ERR = 'ESPN cookies have expired. Re-copy SWID and espn_s2.';")]
                         + go("live")),
    # The only state that lets gdFetch actually run. Every other live state pins GD_DATA or
    # GD_BUSY, so the fetch never fires and nothing here noticed that opening the page from a
    # file logged "URL scheme file is not supported" on every attempt. This suite runs over
    # file://, so without the PAGE_SERVED guard this state puts that error in
    # test_no_console_errors -- which is the point of it.
    ("live-unserved", [("eval", "GD_DATA = null; GD_ERR = ''; GD_BUSY = false; GD_AT = 0;")]
                      + go("live")),
]

SEED = """
(() => { let s = 0x2f6e2b1; Math.random = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; })();
Date.now = () => Date.parse("2026-09-12T12:00:00Z");   // before every fixture kickoff, forever
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
          modal: strip(document.getElementById("modal").innerHTML),
          modalOpen: document.getElementById("modal").classList.contains("on"),
          // The chat panel lives outside #view so it survives a surface change, which also means
          // the two probes above would never see it.
          chat: strip(document.getElementById("chatdock").innerHTML),
          chatOpen: document.getElementById("chatdock").classList.contains("on"),
          // The search sheet is outside #view for the same reason.
          search: strip(document.getElementById("search-list").innerHTML),
          searchOpen: !document.getElementById("search").hidden,
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


@pytest.mark.parametrize("leaf,group,label", [
    ("ranks", "scouting", "RANKS"),
    ("board", "scouting", "LEADERS"),  # the leaf is still `board`, so its bookmarks land
    ("movers", "scouting", "MOVERS"),  # a view beside Leaders since 2026-09-25
    ("pool", "scouting", "MOVERS"),    # the old Movers view's hash, kept for bookmarks
    ("usage", "scouting", "GRID"),
    ("matchups", "scouting", "MATCHUPS"),
    ("waivers", "teams", "WAIVERS"),
    ("parlay", "bets", "SLIPS"),        # the leaf is still `parlay`, so its bookmarks land
    ("build", "bets", "BUILD"),
])
def test_a_hash_opens_its_view(browser, page_file, leaf, group, label):
    """The view lives in the hash so a reload lands where you were reading. Renaming a leaf, or
    dropping the hash write, breaks bookmarks and the Back button silently -- the page still works,
    it just always opens on the roster. This is the only thing that would notice."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED)
    try:
        page.goto(f"{page_file.as_uri()}#{leaf}")
        page.wait_for_function("document.getElementById('view').children.length > 0")
        assert page.locator(".navitem[aria-current='true']").get_attribute("data-s") == group
        sub = page.locator("#subnav .mode-sub[aria-pressed='true']")
        assert sub.inner_text().strip().upper().startswith(label)
        # And navigating writes it back, so the next reload holds.
        page.locator(".navitem[data-s='teams']").first.click()
        page.wait_for_timeout(120)
        assert page.evaluate("location.hash") == "#roster"
    finally:
        ctx.close()


@pytest.mark.parametrize("hash", ["#movers", "#matchups", "#board"])
def test_a_head_fills_its_circle(browser, page_file, hash):
    """Every drawn headshot is exactly as tall as the circle that clips it. Until 2026-09-25 the
    `.xf-head`/`.bd-head` grid sized its implicit row to the img's default 150px, so a 36px circle
    showed the top of a 36x150 strip -- hair and background, no face -- in Movers, Matchups and
    Leaders alike. The golden probe measures no img, which is how it shipped."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    page = ctx.new_page()
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED)
    try:
        page.goto(page_file.as_uri() + hash)
        page.wait_for_function("document.getElementById('view').children.length > 0")
        page.wait_for_timeout(200)
        sizes = page.evaluate("""() => [...document.querySelectorAll('.xf-head img, .bd-head img')].map(i =>
            [Math.round(i.getBoundingClientRect().height), Math.round(i.parentElement.getBoundingClientRect().height)])""")
        assert sizes, f"no headshot drawn on {hash}; the check would pass on nothing"
        assert all(h == box for h, box in sizes), f"img height vs its circle: {sizes[:5]}"
    finally:
        ctx.close()


@pytest.mark.parametrize("hash", ["#movers", "#pool"])
def test_movers_hash_opens_movers(browser, page_file, hash):
    """Movers is a view beside Leaders (2026-09-25; a mode of the Board for a few hours before,
    and the `pool` view before that): its hash, old or new, must open it with its tab pressed, the
    Leaders tab must write #board, and Back must return to Movers."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED)
    try:
        page.goto(page_file.as_uri() + hash)
        page.wait_for_function("document.getElementById('view').children.length > 0")
        assert page.evaluate("[SURFACE, BD_MODE]") == ["movers", "movers"]
        assert page.locator("#subnav [data-leaf='movers'][aria-pressed='true']").count() == 1
        assert page.locator("[data-bdmode]").count() == 0, "the Leaders/Movers switch row is gone"
        assert page.locator("[data-bdadd]").count() == 0, "+ Compare belongs to Leaders only"
        page.locator("#subnav [data-leaf='board']").click()
        page.wait_for_timeout(120)
        assert page.evaluate("[location.hash, SURFACE, BD_MODE]") == ["#board", "board", "leaders"]
        page.go_back()
        page.wait_for_function("SURFACE === 'movers'")
        assert page.locator("[data-poolslug]").count() > 0
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    finally:
        ctx.close()


@pytest.mark.parametrize("w,h", [(360, 740), (1280, 1080)])
def test_leaders_page_fits_the_screen(browser, page_file, w, h):
    """Leaders opens on the #1's card with the list running on under it, and a page is one screen
    (board/fit.js, 2026-09-26): as it lands and after a turn, the card, pager included, ends above
    the bottom edge with no scroll, and a taller screen holds more rows than a phone. A 360x740
    phone showed five players before a tap until then; the hero plus the list must beat that."""
    ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED)
    fits = "(() => { const m = document.querySelector('.bd-card').getBoundingClientRect(); return scrollY === 0 && m.bottom <= innerHeight; })()"
    try:
        page.goto(page_file.as_uri() + "#board")
        page.wait_for_function("document.getElementById('view').children.length > 0")
        assert page.evaluate(fits)
        assert page.locator(".bd-card > .bd-hero").count() == 1, "the #1 keeps his card"
        rows = page.evaluate("document.querySelectorAll('.bd-card .bd-list:not(.bd-pinned) > .bd-row').length")
        assert rows == page.evaluate("BD_FIRST_SIZE") or page.locator(".bd-pager [data-bdpage='2']").count() == 0
        assert page.evaluate("BD_FIRST_SIZE") >= (15 if h >= 1000 else 6)
        if page.locator(".bd-pager [data-bdpage='2']:not([disabled])").count():
            page.locator(".bd-pager [data-bdpage='2']").click()
            assert page.evaluate(fits)
    finally:
        ctx.close()


TUESDAY = 'Date.now = () => Date.parse("2026-09-22T12:00:00Z");'   # a Tuesday in every zone -12..+11


@pytest.mark.parametrize("day,hash,surface,first", [
    ("tue", "", "waivers", "WAIVERS"),     # claims day: Waivers opens and leads its group
    ("tue", "#roster", "roster", "WAIVERS"),   # a hash still wins
    ("sat", "", "ranks", "RANKS"),         # any other day: Ranks leads, not Roster (Leaders until 2026-09-26)
])
def test_tuesday_opens_waivers(browser, page_file, day, hash, surface, first):
    """The day is read from Date.now(), so pinning it is the whole injection. SEED pins a
    Saturday; a Tuesday script added after it wins."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED)
    if day == "tue":
        page.add_init_script(TUESDAY)
    try:
        page.goto(page_file.as_uri() + hash)
        page.wait_for_function("document.getElementById('view').children.length > 0")
        assert page.evaluate("SURFACE") == surface
        subs = page.locator("#subnav .mode-sub")
        assert subs.first.inner_text().strip().upper().startswith(first)
        # No sideways scroll on a phone, whichever view opened.
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    finally:
        ctx.close()


@pytest.mark.parametrize("state", [s for s, _ in STATES])
def test_state_renders_something(snapshot, state):
    out, _ = snapshot
    for vp in VIEWPORTS:
        assert len(out[vp][state]["view"]) > 200, f"{vp}/{state}: #view is empty"
    if state.endswith("drawer"):
        assert out["desk"][state]["drawerOpen"], "drawer did not open"
        assert len(out["desk"][state]["drawer"]) > 100
    if state.endswith("modal"):
        assert out["desk"][state]["modalOpen"], "modal did not open"
        assert len(out["desk"][state]["modal"]) > 100
    if state.startswith("chat-"):
        for vp in VIEWPORTS:
            assert out[vp][state]["chatOpen"], f"{vp}/{state}: the chat panel did not open"
            assert len(out[vp][state]["chat"]) > 100


def test_chat_panel_survives_a_surface_change(snapshot):
    """The whole reason it is a floating panel: open it, switch surface, and it is still there
    with the page behind it changed. As a tab, asking about a player meant leaving his row."""
    out, _ = snapshot
    over_pool = out["desk"]["chat-over-movers"]
    assert over_pool["chatOpen"], "the panel closed when the surface changed"
    assert "chatinput" in over_pool["chat"], "the composer is gone"
    # #view is Movers, not the chat -- the panel is over the page, not instead of it.
    assert "data-poolslug" in over_pool["view"], \
        "#view is not Movers; the panel replaced the surface instead of floating over it"


def diff(golden, now, limit=25):
    lines = []
    for vp in VIEWPORTS:
        for state, _ in STATES:
            g, n = golden.get(vp, {}).get(state), now[vp][state]
            if g is None:
                lines.append(f"{vp}/{state}: no golden yet")
                continue
            for key in ("view", "drawer", "modal", "chat", "search"):
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

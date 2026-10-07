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

The strip has no leaf of its own, so its tests mount Live (tests/component.py) and mount the strip
into the page, as a dialog does, and read it through tests/pages/strip.py. The three that open a
game from a player's game log need the navigation and the profile: they are journeys on the full page.

    pytest tests/test_strip.py          # ~5 s, needs a browser
"""
import importlib.util
import json
import pathlib
import re

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.strip import DESK, PHONE, StripPage
from test_render import PICKED   # noqa: E402  (My teams asks whose team first; these pages are David's)

pytestmark = pytest.mark.render

REPO = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = REPO / "tests" / "fixtures" / "data" / "espn_summary.json"


def _game_module():
    spec = importlib.util.spec_from_file_location("game_fn", REPO / "api" / "game.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def shaped():
    return _game_module().shape(json.loads(FIXTURE.read_text(encoding="utf-8")))


def fit(points):
    """Least-squares b for x = a + b*pct, and the worst residual in pixels."""
    n = len(points)
    mx = sum(p for p, _ in points) / n
    my = sum(x for _, x in points) / n
    var = sum((p - mx) ** 2 for p, _ in points)
    b = sum((p - mx) * (x - my) for p, x in points) / var
    a = my - b * mx
    return b, max(abs(x - (a + b * p)) for p, x in points)


@pytest.mark.req("Live", ac="the strip draws every figure on the yard line the feed states")
@pytest.mark.parametrize("drive", range(5))
def test_the_figure_stands_where_the_yard_line_says(mount, shaped, drive):
    """One straight line through both ends of every play in the drive. A play drawn backwards, at
    the wrong scale, or off the absolute scale leaves the line and shows up as a residual."""
    d = shaped["drives"][drive]
    strip, errors = StripPage.open_on(mount, shaped, drive)
    spots, poses = [], []
    for i, p in enumerate(d["plays"]):
        if p["k"] not in ("rush", "pass"):
            continue        # an incompletion and a kick both end past `to`, on purpose
        # Only spots the FEED states. A receiver does not stand on the line of scrimmage at the
        # snap -- he takes his release step while the passer drops -- so his f=0 is a choreography
        # number, and asserting on it would be asserting on the view's own arithmetic.
        if p["k"] == "rush":
            spots.append(p["from"])
            poses.append((i, 0, 0))
        spots.append(p["to"])
        poses.append((i, 1, 0))
    points = list(zip(spots, strip.carrier_xs(poses)))
    assert len(points) >= 4, f"drive {drive} gave only {len(points)} samples"
    b, worst = fit(points)
    # The drive's direction is in the SIGN: a home drive runs 0 -> 100 left to right, an away drive
    # runs the other way over the same fixed field, and `dir` is the only thing that says so.
    assert b > 0, f"screen x must grow with field position; got {b:.2f} px per percent"
    assert worst < 2.0, f"{worst:.1f}px off a straight line -- a play is drawn at the wrong spot"
    assert errors == []


@pytest.mark.req("Live", ac="a scaled ancestor does not move the figures off the field")
def test_a_scaled_ancestor_does_not_move_the_figures_off_the_field(mount, shaped):
    """The strip opens in a dialog that grows from scale(.2), and getBoundingClientRect reports
    SCREEN pixels while the `translate` written back onto a sprite is applied in the element's own
    unscaled ones. A frame measured mid-transition therefore put every figure, goalpost and arc
    about a hundred pixels above the field -- and left them there, because nothing re-measured
    once the animation ended. Where a figure stands as a FRACTION of the field must not depend on
    what an ancestor is doing to the whole thing."""
    strip, errors = StripPage.open_on(mount, shaped, 0)
    at = []
    for s in (1, 0.5, 0.2):
        strip.scale_ancestor(s)
        at.append(strip.carrier_on_field())
    base = at[0]
    moved = [f"at scale {s} the figure moved {fx - base[0]:+.3f} across and {fy - base[1]:+.3f} up the field"
             for s, (fx, fy) in zip((0.5, 0.2), at[1:])
             if not (abs(fx - base[0]) < .01 and abs(fy - base[1]) < .02)]
    assert moved == []
    # and he is standing ON the field, not above it -- the symptom the bug actually showed
    assert 0 < base[1] < 1.2, f"the figure's feet are at {base[1]:.2f} of the field's height"
    assert errors == []


@pytest.mark.req("Live", ac="an away drive runs the other way over the same field")
def test_an_away_drive_runs_the_other_way(mount, shaped):
    """Same field, opposite direction. The field never flips between drives; the figures turn."""
    away = next(i for i, d in enumerate(shaped["drives"]) if d["dir"] == -1)
    p = next(q for q in shaped["drives"][away]["plays"] if q["k"] == "rush" and q["to"] != q["from"])
    i = shaped["drives"][away]["plays"].index(p)
    gained = (p["to"] - p["from"]) * -1 > 0
    strip, errors = StripPage.open_on(mount, shaped, away)
    start = strip.carrier_x_at(i, 0)
    end = strip.carrier_x_at(i, 1)
    # An away drive gains ground by moving LEFT across the screen, because 0 is the home goal line.
    assert (end < start) == gained, f"{p['tx'][:60]!r} drew the wrong way"
    assert errors == []


@pytest.mark.req("Live", ac="every figure faces the end zone his drive attacks")
def test_every_figure_faces_the_way_his_drive_says(mount, shaped):
    """The rig is drawn facing right. Until 2026-09-26 only the chevrons knew the drive's
    direction, and an away offense ran left facing right. The ball carrier faces the end zone his
    drive attacks; the tackler faces him."""
    out, errs = {}, {}
    for dirn in (1, -1):
        # the ESPN fixture names no tacklers, so one is added to a copy of the play being drawn
        data = json.loads(json.dumps(shaped))
        d, i = next((a, j) for a, x in enumerate(data["drives"]) if x["dir"] == dirn
                    for j, p in enumerate(x["plays"]) if p["k"] == "rush")
        data["drives"][d]["plays"][i]["tk"] = "A. Tackler"
        strip, errors = StripPage.open_on(mount, data, d)
        strip.render(i + .5)
        out[dirn] = strip.facing()
        errs[dirn] = list(errors)
    assert errs == {1: [], -1: []}
    assert out[1] == ["1", "-1"], f"home drive: carrier, tackler facing {out[1]}"
    assert out[-1] == ["-1", "1"], f"away drive: carrier, tackler facing {out[-1]}"


def _with(shaped, fn):
    data = json.loads(json.dumps(shaped))
    fn(data)
    return data


@pytest.mark.req("Motion", ac="a hit stops time and a turnover freezes it")
def test_a_hit_stops_time_and_a_turnover_freezes_it(mount, shaped):
    """moments.js stWarp: contact holds its frame for 70ms (a sack 110), a big play runs its break
    at 30%, an interception freezes on the ball for 260ms. Wall time in, play time out. stWarp is a
    pure function in the surface, not in js/data, and its file reads matchMedia at load, so Node's
    loader cannot take it: it runs in the page, with motion on."""
    strip, errors = StripPage.open_on(mount, shaped, 0)
    out = strip.time_warp()
    assert out["extra"] == 70
    assert abs(out["held"][0] - out["held"][1]) < 1e-6, "the hit-stop did not hold the frame"
    assert out["pick"] == [260, 1000]
    assert out["big"], "a 25-yard run got no slow motion"
    assert errors == []


@pytest.mark.req("Live", ac="the offense wears the drive's club colours, the defence the other's")
def test_team_kits_colour_the_figures(mount, shaped):
    """The offense wears the drive's club and the defence the other; a game with no kits keeps
    the house blue and grey."""
    def kit(d):
        d["home"]["kit"] = {"jersey": "#aa0000", "trim": "#b3995d", "dark": False}
        d["away"]["kit"] = {"jersey": "#003594", "trim": "#ffd100", "dark": False}
        for dr in d["drives"]:
            dr["team"] = d["home"]["abbr"] if dr["dir"] > 0 else d["away"]["abbr"]
    data = _with(shaped, kit)
    d = next(i for i, x in enumerate(data["drives"]) if x["dir"] > 0)
    strip, errors = StripPage.open_on(mount, data, d)
    assert strip.jerseys() == ["#aa0000", "#003594"]
    assert errors == []


@pytest.mark.req("Live", ac="a second tackler piles on and is named")
def test_a_second_tackler_piles_on_and_is_named(mount, shaped):
    """An assisted tackle (tk2) draws a second defender arriving, and the finished play is tagged
    as a pile. It is the per-play fact behind "running through people"."""
    def pile(d):
        p = next(p for x in d["drives"] for p in x["plays"] if p["k"] == "rush" and p["to"] != p["from"])
        p["tk"], p["tk2"] = "A. One", "B. Two"
    data = _with(shaped, pile)
    d, i = next((a, j) for a, x in enumerate(data["drives"]) for j, p in enumerate(x["plays"]) if p.get("tk2"))
    strip, errors = StripPage.open_on(mount, data, d)
    strip.render(i + 1, .8)
    got = strip.pile_on()
    assert got["shown"] != "none" and got["down"], got
    assert got["tag"] == "2 tacklers", got
    assert errors == []


@pytest.mark.req("Live", ac="a turnover swings the chevrons round, in red")
def test_a_turnover_swings_the_chevrons_round(mount, shaped):
    """After an interception the chevrons run toward the end the defence now attacks, in red,
    instead of vanishing."""
    def pick(d):
        p = next(p for x in d["drives"] if x["dir"] > 0 for p in x["plays"] if p["k"] in ("pass", "inc"))
        p.update(k="int", ret=5)
    data = _with(shaped, pick)
    d, i = next((a, j) for a, x in enumerate(data["drives"]) for j, p in enumerate(x["plays"]) if p["k"] == "int")
    strip, errors = StripPage.open_on(mount, data, d)
    strip.render(i + .5)
    before = strip.stage_classes()
    strip.render(i + 1, 1)
    after = strip.stage_classes()
    assert "chevback" not in before and "chevback" in after and "turnover" in after, (before, after)
    assert strip.chevrons_shown()
    assert errors == []


@pytest.mark.req("Live", ac="the card says the game's broken tackles")
def test_the_card_says_the_games_broken_tackles(mount, shaped):
    """PFR counts broken tackles per game, never per play: the card says the game total for the
    man it names, and nothing for a man with none."""
    who = next(p["who"] for x in shaped["drives"] for p in x["plays"] if p["k"] == "rush" and p.get("who"))
    data = _with(shaped, lambda d: d.update(brk={who: 4}))
    d, i = next((a, j) for a, x in enumerate(data["drives"]) for j, p in enumerate(x["plays"]) if p.get("who") == who)
    strip, errors = StripPage.open_on(mount, data, d)
    strip.render(i + .5)
    assert strip.broke_line() == "broke 4 tackles this game"
    assert errors == []


@pytest.mark.req("Live", ac="the caption box never changes height")
def test_the_caption_box_never_changes_height(mount, shaped):
    """A box that grows for a two-line pass and shrinks for a one-line run makes the whole panel
    jump under the reader's thumb during a replay. Measured at 360px, where captions wrap."""
    strip, errors = StripPage.open_on(mount, shaped, 0, PHONE)
    heights = {round(h) for h in strip.caption_heights_after(i + 1 for i in range(len(shaped["drives"][0]["plays"])))}
    assert len(heights) == 1, f"the caption box took {sorted(heights)} across one drive"
    assert errors == []


@pytest.mark.req("Live", ac="the panel fits a 360px phone")
def test_the_panel_fits_a_360px_phone(mount, shaped):
    """Nine readers in ten are on a phone. One thing in the strip scrolls sideways on purpose --
    in Pan, the field -- and nothing else may, the panel itself least of all. The filter row holds
    Game, the quarters and the player chip on one line. Measured against the strip's own host: the
    page around it has chrome of its own."""
    strip, errors = StripPage.open_on(mount, shaped, 0, PHONE, "J. Goff")
    over = strip.sideways()
    assert over["bad"] == [], over["bad"]
    assert over["wide"] <= 0, f"the panel scrolls {over['wide']}px sideways"
    assert over["right"] <= PHONE[0], f"the panel's right edge is at {over['right']}px"
    assert errors == []


@pytest.mark.req("Live", ac="both goalposts are drawn with a measured crossbar")
def test_both_goalposts_are_drawn_with_a_measured_crossbar(mount, shaped):
    """The uprights are flat sprites; only the crossbar's direction comes from the scene. A post
    whose two anchors land in the same place draws a zero-length crossbar, which is the symptom of
    the anchors having been lost inside the 3D context."""
    strip, errors = StripPage.open_on(mount, shaped, 0)
    strip.render(1)
    posts = strip.goalposts()
    depth = strip.post_depth()
    assert len(posts) == 2 and all(d and d.startswith("M") for d in posts), posts
    # The far anchor sits deeper into the screen than the near one, so it renders HIGHER up.
    assert depth < -4, f"the two post anchors are {depth:.1f}px apart vertically; the crossbar is flat"
    assert errors == []


@pytest.mark.req("Live", ac="the chevrons run from the ball to the end zone being attacked")
@pytest.mark.parametrize("drive", range(5))
def test_the_chevrons_run_from_the_ball_to_the_end_zone_being_attacked(mount, shaped, drive):
    """The ground still to cover. On an away drive that is the LEFT half of the same fixed field,
    so the band has to start at the left edge and stop at the ball, not the other way round."""
    d = shaped["drives"][drive]
    strip, errors = StripPage.open_on(mount, shaped, drive)
    strip.render(1)
    box = strip.chevron_box()
    # The band lives on the field's centre lane, which perspective draws ~30px narrower than the
    # turf's own bounding box (that box is the near touchline, the widest part). So the check is
    # "which side of the ball, and does it cover the ground", not "does it touch the edge".
    checks = ([("the chevrons start behind the ball", box["aL"] > box["ball"]),
               ("the band stops short", box["aR"] - box["ball"] > (box["tR"] - box["ball"]) * .7)]
              if d["dir"] > 0 else
              [("the chevrons start ahead of the ball", box["aR"] < box["ball"]),
               ("the band stops short", box["ball"] - box["aL"] > (box["ball"] - box["tL"]) * .7)])
    assert [why for why, ok in checks if not ok] == []
    assert errors == []


CLASS_RE = re.compile(r"^\.([A-Za-z_][\w-]*)((?::[\w-]+(?:\([^)]*\))?)*)$")


@pytest.mark.req("Live", ac="no class the strip renders is styled by a bare rule elsewhere")
def test_no_class_the_strip_renders_is_styled_by_a_bare_rule_elsewhere(mount, shaped):
    """The strip is one component dropped into a page with its own CSS, and a bare `.x{}` rule
    anywhere reaches inside it however the strip's own selectors are scoped. This is not
    hypothetical: roster.css's `.nm` set grid-area on the caption's name and tore the play card's
    grid apart, and nothing but looking at it would have said so. Hence the st- prefix on every
    class the strip renders -- and hence this, which fails the moment one goes missing."""
    strip, errors = StripPage.open_on(mount, shaped, 0)
    strip.render(1)
    used = strip.classes_used()
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
    assert errors == []


SITE = "http://strip.test/"


@pytest.fixture
def served(browser, page_file, shaped):
    """The page with a real origin and a real /api/game behind it, without running a server:
    (StripPage, the page's errors, the /api/game calls it made). Closed when the test ends.

    Two things only happen over http: the fetch at all (from file:// the strip says so and stops,
    which is PAGE_SERVED's whole job), and the endpoint's own JSON. Both are routed here, so this
    exercises the same code path a deployed page takes."""
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.add_init_script(PICKED)
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
    strip = StripPage(page)
    strip.visit(SITE)
    yield strip, errors, calls
    ctx.close()


@pytest.mark.journey
@pytest.mark.req("Live", ac="a week in the game log opens that game over the profile")
def test_a_week_in_the_game_log_opens_that_game_over_the_profile(served, shaped):
    """The second way in. It opens OVER the profile rather than instead of it: the reader tapped a
    week while reading about a player, and closing the strip has to put him back where he was."""
    strip, errors, calls = served
    strip.open_roster()
    strip.open_profile("Jahmyr Gibbs")
    # The game log is the Season pane, the one the profile opens on (2026-09-28).
    assert strip.weeks_in_game_log(), "no week in the game log opens a game"
    strip.tap_week()
    strip.wait_for_game()
    state = strip.dialogs()
    title, plays, field = strip.game_title(), strip.game_plays(), strip.field_height()
    strip.close_game()
    after = strip.dialogs()
    assert errors == []
    assert calls, "the strip never asked /api/game"
    assert state["strip"] and state["profile"], "the strip replaced the profile instead of stacking"
    # the whole game, one row per play, and the field scaled up to use the dialog: its box is
    # 138px unscaled. Layout height, since the dialog is still growing out of scale(.2) here.
    assert plays == sum(len(d["plays"]) for d in shaped["drives"])
    assert field > 200, f"the field's box is {field}px tall in a 1400x900 dialog"
    assert "at" in title
    # Escape closes the topmost dialog, not both: the reader is put back in the profile.
    assert after["profile"] and not after["strip"], "Escape closed the profile too"


@pytest.mark.journey
@pytest.mark.req("Live", ac="anywhere on a week row opens that game")
def test_anywhere_on_a_week_row_opens_that_game(served):
    """The week number alone was a target nobody found (2026-09-26); the whole row opens the game.
    Clicked on a stat cell at the far end of the row, not on the week."""
    strip, errors, calls = served
    strip.open_roster()
    strip.open_profile("Jahmyr Gibbs")
    strip.tap_far_cell_of_a_week_row()
    strip.wait_for_game()
    assert strip.dialogs()["strip"], "a click on the row did not open the game"
    assert errors == []


@pytest.mark.journey
@pytest.mark.req("Live", ac="the same game is only fetched once")
def test_the_same_game_is_only_fetched_once(served):
    """Re-opening a game the reader just looked at must not cost another ESPN read. The endpoint's
    edge cache is what protects ESPN from many readers; this is what protects it from one."""
    strip, errors, calls = served
    strip.open_roster()
    strip.open_profile("Jahmyr Gibbs")
    for _ in range(2):
        strip.tap_week()
        strip.wait_for_game()
        strip.close_game()
    assert errors == []
    assert len(calls) == 1, f"asked /api/game {len(calls)} times for one game"


@pytest.mark.req("Live", ac="the player chip and a quarter narrow the reel to his plays")
def test_the_player_chip_and_a_quarter_narrow_the_reel_to_his_plays(mount, shaped):
    """The reader came from a player's game log, and asks for three things: the game, a quarter,
    and every play that player was in. The chip stacks with a quarter, and the list and the
    transport both run over exactly the plays chosen -- as the passer or as the man with the ball."""
    who = "J. Goff"
    mine = [p for d in shaped["drives"] for p in d["plays"] if who in (p.get("who"), p.get("qb"))]
    q2 = [p for p in mine if p["clock"].startswith("Q2")]
    strip, errors = StripPage.open_on(mount, shaped, None, DESK, who)
    game = strip.reel()
    strip.follow_player()
    his = strip.reel()
    strip.pick_quarter(2)
    his_q2 = strip.reel()
    total = sum(len(d["plays"]) for d in shaped["drives"])
    assert game == {"rows": total, "max": total, "chip": str(len(mine))}, game
    assert his == {"rows": len(mine), "max": len(mine), "chip": str(len(mine))}, his
    assert his_q2 == {"rows": len(q2), "max": len(q2), "chip": str(len(q2))}, his_q2
    assert errors == []


@pytest.mark.req("Live", ac="the ring is under the man the reader follows")
def test_the_ring_is_under_the_man_the_reader_follows(mount, shaped):
    """The field has no faces (2026-09-26); the lime ring says who to watch. In the game view it is
    the man the play card names; narrowed to a passer, it moves to the passer on his throws."""
    who = "J. Goff"
    strip, errors = StripPage.open_on(mount, shaped, None, DESK, who)
    strip.seek_into_throw_by(who)
    game = strip.ringed()
    strip.follow_player()
    strip.seek(.5)
    his = strip.ringed()
    his_rings = strip.ring_count()
    assert game == ["carrier"], game
    assert his == ["passer"], his
    assert his_rings == len(his), f"{his_rings} actors ringed, {len(his)} of them named"
    assert strip.faces_on_field() == 0, "a headshot is back on the field"
    assert errors == []


@pytest.mark.req("Motion", ac="nothing on the field animates while paused")
def test_nothing_on_the_field_animates_while_paused(mount, shaped):
    """The chevrons and a standing figure's breathing used to loop forever, repainting the tilted
    field for nobody (STYLE.md, Motion 1). Paused, no looping animation in the strip is running;
    a one-off fade (the lit row's) ends by itself."""
    strip, errors = StripPage.open_on(mount, shaped, None)
    running = strip.looping_animations()
    assert running == [], f"still animating while paused: {running}"
    assert errors == []


@pytest.mark.req("Motion", ac="the legs run on the replay's clock")
def test_the_legs_run_on_the_replays_clock(mount, shaped):
    """The run cycle is a paused animation positioned by the replay's own clock (field.css,
    --clock), so it moves only on frames the replay draws. Playing, a runner's legs move; the
    moment the replay stops, they stop too."""
    strip, errors = StripPage.open_on(mount, shaped, None)
    # Waits are on what the page draws, not on a clock: under the full suite's load a fixed 120ms
    # sometimes held no new replay frame, and the legs read "did not move" (2026-09-26). The page's
    # clock is moved on by hand (frames count as 17 ms), so the waits take as long as the frames take to draw.
    strip.fake_time()
    strip.toggle_play()
    strip.wait_for_a_runner()
    a = strip.leg_angle()
    b = strip.legs_after_moving(a)
    strip.toggle_play()                                 # pause
    strip.frames()                                      # let a frame already queued land
    c = strip.leg_angle()
    strip.frames(12)                                    # twelve more frames of the page's own clock (~200 ms at 60 Hz)
    d = strip.leg_angle()
    assert a is not None and b is not None and a != b, f"the legs did not move while playing: {a} -> {b}"
    assert c == d, f"the legs kept moving while paused: {c} -> {d}"
    assert errors == []


@pytest.mark.req("Live", ac="a row in the list plays that play")
def test_a_row_in_the_list_plays_that_play(mount, shaped):
    """Tapping a row runs its play from the snap to the beat after it, on its own drive's field,
    and lights that row."""
    strip, errors = StripPage.open_on(mount, shaped, None)
    strip.fake_time()           # the play's second runs on the page's clock, moved on by the wait below
    k = strip.row_count() - 3
    strip.tap_row(k)
    strip.wait_until_reel_at(k + 1)
    last = len(shaped["drives"]) - 1
    assert {"at": strip.drive_on_field(), "lit": strip.lit_row()} == {"at": last, "lit": str(k)}
    assert errors == []


@pytest.mark.req("Live", ac="the reel crosses every drive without a jump in the caption")
def test_the_reel_crosses_every_drive_without_a_jump_in_the_caption(mount, shaped):
    """Whole-game replay changes drive under the reader. Every point on the reel draws on the
    right drive's field, and the caption box keeps one height across all of them."""
    strip, errors = StripPage.open_on(mount, shaped, None, PHONE)
    seen = strip.walk_reel()
    assert seen["ok"], "a point on the reel drew on another drive's field"
    assert len(seen["heights"]) == 1, f"the caption box took {seen['heights']} across the game"
    assert errors == []


@pytest.mark.req("Live", ac="every play of every drive draws")
def test_every_play_of_every_drive_draws(mount, shaped):
    """The whole fixture, start to finish: a home touchdown drive, an away drive, a sack that
    becomes a fumble recovery, and a field goal. Any of them throwing is the bug."""
    strip, errors = StripPage.open_on(mount, shaped, 0)
    drawn = strip.draw_every_frame()
    assert drawn == 4 * sum(len(d["plays"]) for d in shaped["drives"])
    assert errors == []

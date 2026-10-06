"""This week > Preview (2026-09-29, storyboard option A): a slate of every game by kickoff window,
and a tap opens the game's dossier. Rendered from the fixture build. Since 2026-10-05 (storyboard
https://claude.ai/artifact/NTeV8W2N9mFnYgftfbuqPV, picks 1A 2A 3A 4A) a game that is over leaves the slate
for Past games, which heads with Claude's season by bet, and the dossier's answer is one row per bet.

The fixture (tests/fixtures/data/game_previews.json) holds five games, one per window: PIT @ CLE on
Thursday (both on a short week), JAX @ LA on Sunday morning at Wembley (neutral site, wind 17 mph,
LA off a bye, Claude picks the underdog), DET @ CAR at 1:00 (rain 56%, Coker out, St. Brown
questionable, the only game with defense ranks), SF @ NYJ late (SF flew 3 zones east; the line
flipped), and ATL @ NO on Monday in a dome with no take, no rest, travel or site. SEED pins the clock
before all five.
"""
import json
import pathlib
import re

import pytest

import contract
from preview import _ats, _base, _blind, _total, live_preview
from test_render import LOAD_MS, PICKED, SEED, watch_errors  # noqa: F401

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "data" / "game_previews.json"


def slug(n):
    return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")


@pytest.fixture(scope="module")
def block():
    return live_preview(json.loads(FIXTURE.read_text(encoding="utf-8")), slug)


def by_key(block):
    return {g["key"].split("_", 2)[2]: g for g in block["games"]}


def test_the_block_sorts_by_kickoff_into_windows(block):
    assert [(g["key"], g["slot"], g["et"]) for g in block["games"]] == [
        ("2026_02_PIT_CLE", "thu", "8:15 PM"), ("2026_02_JAX_LA", "sunam", "9:30 AM"),
        ("2026_02_DET_CAR", "sun1", "1:00 PM"), ("2026_02_SF_NYJ", "sunlate", "4:25 PM"),
        ("2026_02_ATL_NO", "mon", "8:15 PM")]


def test_the_line_is_a_favourite_and_a_margin_never_a_signed_spread(block):
    g = by_key(block)
    assert g["PIT_CLE"]["line"]["fav"] == "PIT" and g["PIT_CLE"]["line"]["by"] == 2.5   # spread_home +2.5: away favoured
    assert g["SF_NYJ"]["line"]["fav"] == "NYJ" and g["SF_NYJ"]["line"]["open"] == {"fav": "SF", "by": 3.0, "total": 43.5}
    assert g["ATL_NO"]["line"]["open"] is None                                           # no first line seen


def test_flags_are_at_most_two_in_priority_order(block):
    g = by_key(block)
    assert g["PIT_CLE"]["flags"] == [{"k": "short", "teams": ["CLE", "PIT"]}]
    assert g["JAX_LA"]["flags"] == [{"k": "upset"}, {"k": "wx", "wind": 17}]
    assert g["DET_CAR"]["flags"] == [{"k": "wx", "rain": 56}, {"k": "out", "n": "Jalen Coker", "slug": "jalen-coker"}]
    assert g["SF_NYJ"]["flags"] == [{"k": "upset"}, {"k": "moved", "flip": True, "by": 4.5}]
    assert g["ATL_NO"]["flags"] == []


def test_injuries_rest_travel_and_matchup(block):
    g = by_key(block)
    assert g["DET_CAR"]["inj"] == {"CAR": [{"n": "Jalen Coker", "slug": "jalen-coker", "pos": "WR", "s": "out", "avg": 14.4}],
                                   "DET": [{"n": "Amon-Ra St. Brown", "slug": "amon-ra-st-brown", "pos": "WR", "s": "q", "avg": None}]}
    assert g["DET_CAR"]["matchup"]["DET"]["pos"]["RB"] == {"pts": 29.4, "rank": 31}   # keyed by the offense
    assert g["SF_NYJ"]["travel"]["SF"] == {"zones": 3, "body": "13:25", "miles": 2570}
    assert g["JAX_LA"]["rest"]["LA"] == {"days": 13, "short": False, "bye": True}
    assert g["JAX_LA"]["site"] == {"stadium": "Wembley Stadium", "neutral": True}
    atl = g["ATL_NO"]
    assert (atl["rest"], atl["travel"], atl["site"], atl["matchup"], atl["take"]) == (None, None, None, None, None)
    gibbs = g["DET_CAR"]["take"]["players"][0]
    assert gibbs == {"n": "Jahmyr Gibbs", "slug": "jahmyr-gibbs", "pos": "RB", "team": "DET", "proj": 18.8,
                     "call": "up", "why": "The rain and the matchup both point to carries."}


def test_no_file_means_no_block():
    assert live_preview(None, slug) is None
    assert live_preview({"games": {}}, slug) is None


# Confidence and record (2026-09-29, storyboard option A). The fixture: PIT @ CLE no edge, JAX getting 3
# STRONG, DET giving 3.5 SOLID, SF getting 1.5 LEAN with no moneyline; ATL @ NO no take.
def test_the_confidence_fields_pass_through(block):
    g = by_key(block)
    jax = g["JAX_LA"]["take"]
    assert jax["win"] == {"JAX": 54} and jax["total"] == {"call": "under", "conf": "solid"}
    assert jax["ats"] == {"side": "JAX", "conf": "strong",
                          "edge": "Wind and eight time zones cut the Rams' passing; the line still prices a normal Stafford day."}
    assert g["PIT_CLE"]["take"]["ats"] == {"side": None, "conf": None, "edge": None}
    assert g["PIT_CLE"]["take"]["total"] == {"call": None, "conf": None}
    assert g["DET_CAR"]["market_win"] == {"DET": 64.4, "CAR": 35.6}
    assert g["DET_CAR"]["base"] == {"n": 1314, "wins": 67, "covers": 49, "home": None}
    assert g["SF_NYJ"]["market_win"] is None
    assert g["ATL_NO"]["take"] is None and g["ATL_NO"]["market_win"] == {"NO": 57.4, "ATL": 42.6}


def test_a_take_from_before_confidence_reads_null():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    g = raw["games"]["2026_02_DET_CAR"]
    for k in ("win", "ats", "total", "blind", "vs_blind", "notes"):
        del g["take"][k]
    for k in ("ml", "market_win", "base"):
        del g["facts"]["line"][k]
    det = by_key(live_preview(raw, slug))["DET_CAR"]
    assert (det["take"]["win"], det["take"]["ats"], det["take"]["total"], det["market_win"], det["base"]) == (None,) * 5
    assert (det["take"]["blind"], det["take"]["vs_blind"], det["take"]["notes"]) == (None, None, [])


def test_the_research_pass_blind_number_and_notes(block):
    """ff-jarvis preview-research (2026-09-29): the blind number said like the line, never signed;
    a note's source is a web link or "pbp", anything else is dropped."""
    det = by_key(block)["DET_CAR"]["take"]
    assert det["blind"] == {"fav": "DET", "by": 1.5, "total": 48.5}      # margin_home -1.5: the away side
    assert det["vs_blind"].startswith("The blind number had DET by 1.5")
    assert det["notes"] == [
        {"text": "Carolina has allowed 5.1 yards a carry since week 1.", "source": "https://www.espn.com/nfl/story/_/id/1"},
        {"text": "Gibbs took 11 of Detroit's 14 red-zone carries last week.", "source": "pbp"},
        {"text": "Coker was ruled out Friday.", "source": None}]
    jax = by_key(block)["JAX_LA"]["take"]
    assert (jax["blind"], jax["vs_blind"], jax["notes"]) == (None, None, [])
    assert _blind({"margin_home": 0, "total": 44}, "NO", "ATL") == {"fav": None, "by": 0, "total": 44}
    assert _blind({"margin_home": 3.5}, "NO", "ATL") == {"fav": "NO", "by": 3.5, "total": None}


def test_a_side_without_a_confidence_is_no_edge():
    assert _ats({"side": "IND", "conf": None, "edge": "x"}) == {"side": None, "conf": None, "edge": None}
    assert _ats({"side": None, "conf": "strong", "edge": "x"}) == {"side": None, "conf": None, "edge": None}
    assert _total({"call": "over", "conf": "huge"}) == {"call": None, "conf": None}


def test_the_base_rate_reads_the_producers_percentages():
    # ff-jarvis preview_market's real 3.5-6.5 bucket, 2011-2025.
    pct = {"bucket": "3.5-6.5", "n": 1314, "fav_wins": 66.8, "fav_covers": 48.9, "dog_wins": 33.0, "push": 0.8}
    assert _base(pct) == {"n": 1314, "wins": 67, "covers": 49, "home": None}
    pickem = {"bucket": "0", "n": 212, "home_wins": 52.4, "fav_wins": None, "fav_covers": None, "dog_wins": None, "push": None}
    assert _base(pickem) == {"n": 212, "wins": None, "covers": None, "home": 52}
    assert _base(None) is None and _base({"n": 0}) is None


RECORD = pathlib.Path(__file__).parent / "fixtures" / "data" / "preview_record.json"


def test_the_record_is_cut_newest_week_first(block):
    assert block["record"] is None                          # the module's block is built without the record file
    rec = live_preview(json.loads(FIXTURE.read_text(encoding="utf-8")), slug,
                       json.loads(RECORD.read_text(encoding="utf-8")))["record"]
    assert (rec["through"], rec["n"], rec["ats"], rec["by_conf"]["strong"]) == (2, 8, "4-2-1", "1-0-1")
    assert (rec["closer"], rec["graded"]) == (4, 7)        # TB @ ATL had no moneyline, so no market Brier
    assert (rec["fav"], rec["fav_of"], rec["covered"]) == (6, 8, 1)
    assert rec["blind"] == {"n": 7, "ats": "4-3-0", "mae_blind": 9.1, "mae_market": 8.4}
    assert [w["week"] for w in rec["weeks"]] == [2, 1]
    w2 = rec["weeks"][0]
    assert (w2["ats"], w2["strong"], w2["closer"], w2["graded"], w2["fav"], w2["fav_of"]) == ("1-2-1", "0-0-1", 2, 3, 3, 4)
    # Since 2026-10-05 (Past games, storyboard 2A) every graded game carries all three calls and their hits.
    assert w2["games"][1] == {"key": "2026_02_SEA_LA", "away": "SEA", "home": "LA", "pick": "LA", "side": "LA", "conf": "strong",
                              "spread_home": -3.0, "result": {"home": 27, "away": 24}, "hit": "push", "su": "hit",
                              "total_line": 46.5, "total_call": "over", "total_conf": "solid", "total_hit": "hit"}
    assert (rec["su"], rec["total"], w2["su"], w2["total"]) == ("5-3", "5-1-0", "2-2", "3-0-0")
    assert contract.problems("LIVE_PREVIEW", {**block, "record": rec}) == []


def test_before_a_final_week_the_record_is_empty():
    empty = json.loads(RECORD.read_text(encoding="utf-8"))
    empty.update(through_week=None, weeks=[])
    empty["totals"]["blind"] = {"n": 0, "ats": "0-0-0", "ats_pass": 0, "margin_mae": {"blind": None, "market": None, "final": None}}
    rec = live_preview(json.loads(FIXTURE.read_text(encoding="utf-8")), slug, empty)["record"]
    assert rec["weeks"] == [] and rec["through"] is None and (rec["closer"], rec["graded"]) == (0, 0)
    assert rec["blind"] is None
    assert live_preview(json.loads(FIXTURE.read_text(encoding="utf-8")), slug)["record"] is None


def open_preview(browser, page_file, w=360, h=800, errors=None):
    ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce", has_touch=True)
    pg = ctx.new_page()
    pg.set_default_timeout(5000)
    watch_errors(pg, errors)
    pg.route(re.compile(r"^https?://"), lambda route: route.abort())
    pg.add_init_script(SEED)
    pg.goto(page_file.as_uri() + "#preview", timeout=LOAD_MS)
    pg.wait_for_function("document.querySelector('.pv-row') !== null")
    return ctx, pg


PRISTINE_JS = """() => {
  const live = {LIVE_PREVIEW, PROPS};
  window.__pristine = {live, openProfile, galWin: GAL_WIN,
    snap: Object.fromEntries(Object.entries(live).map(([k, v]) => [k, structuredClone(v)]))};
}"""

# Puts the shared page back to what a fresh load shows: the preview block (tests edit it), the dossier,
# the record, the slip and its tray, localStorage, open layers and the view. Every test starts from
# here, whichever worker it lands on.
RESET_JS = """() => {
  'use strict';
  document.querySelectorAll('.modal.on').forEach(d => modalShut(d));
  LAYERS.length = 0; LAYER_SKIP.length = 0;
  const p = window.__pristine;
  for (const [k, v] of Object.entries(p.live)) {
    const s = structuredClone(p.snap[k]);
    if (Array.isArray(v)) { v.length = 0; v.push(...s); } else { for (const key of Object.keys(v)) delete v[key]; Object.assign(v, s); }
  }
  openProfile = p.openProfile; delete window.__opened;
  try { localStorage.clear(); } catch (e) {}
  %s
  SAVED = savedRead();
  SLIP.length = 0; SLIP_SIDE = {}; SL_CHIP = {}; SL_FOCUS = null; GAL_WIN = p.galWin;
  BETS_SHEET = false; BETS_PANEL = false; LEG_SHEET = null;
  PV_I = null; PV_OPEN = false; PV_Y = 0; PV_REC = false; PV_ENTER = ""; PV_ARC_WK = null; PV_ARC_G = null; PV_ARC = null;
  window.scrollTo(0, 0);
  navGo('preview');
}""" % PICKED


@pytest.fixture(scope="module")
def shared(browser, page_file):
    """One page for the module: page resets it, so a test never sees another's changes."""
    errors = []
    ctx, pg = open_preview(browser, page_file, errors=errors)
    pg.evaluate(PRISTINE_JS)
    assert errors == []                 # whatever the load or the snapshot raised fails here, not lost to a clear
    yield pg, errors
    ctx.close()


@pytest.fixture
def page(shared):
    """The shared page, reset. Any page error or console error during the test fails it."""
    pg, errors = shared
    left, errors[:] = list(errors), []  # an error raised or left over since the last test fails this one
    assert left == []
    pg.evaluate(RESET_JS)
    yield pg
    assert errors == [], errors


def is_open(pg):
    return pg.evaluate("document.querySelector('.pv').classList.contains('open')")


def match(pg):
    return pg.inner_text(".pv-mt")


@pytest.mark.render
def test_the_slate_lists_every_game_by_window(page):
    wins = page.evaluate("""() => [...document.querySelectorAll('.pv-win')].map(w => [
        w.querySelector('.pv-wh span').textContent, [...w.querySelectorAll('.pv-rm')].map(r => r.textContent)])""")
    assert wins == [["Thursday night", ["PIT @ CLE"]], ["Sunday morning", ["JAX @ LA"]], ["Sunday early", ["DET @ CAR"]],
                    ["Sunday late", ["SF @ NYJ"]], ["Monday night", ["ATL @ NO"]]]
    assert page.inner_text(".pv-wh em >> nth=0") == "5:15 PM"      # the reader's clock (Pacific here), no "ET"
    assert not is_open(page) and not page.is_visible(".pv-dz")


@pytest.mark.render
def test_a_row_is_the_call_then_the_headline(page):
    """Storyboard option C (2026-09-29, David: "super busy"): two lines, like a newspaper's index.
    Win %, the score and the total live in the game's box score, not on the slate. Option B (the
    same day, "too many things screaming for attention"): no flags, and lime only on the game on
    screen and a confident pick."""
    assert page.locator(".pv-slate .pv-pb, .pv-slate .pv-key, .pv-slate .pv-meta, .pv-slate .pv-f").count() == 0
    lime = page.evaluate("""() => { const lime = getComputedStyle(document.documentElement).getPropertyValue('--lime').trim();
        const probe = document.createElement('i'); probe.style.color = lime; document.body.append(probe);
        const rgb = getComputedStyle(probe).color; probe.remove();
        return [...document.querySelectorAll('.pv-slate *')].filter(e => e.children.length === 0 &&
          (getComputedStyle(e).color === rgb || getComputedStyle(e).backgroundColor === rgb)).map(e => e.innerText.trim()); }""")
    assert lime == ["Very confident", "Confident"]                      # the phone has no game on screen
    wh = page.evaluate("getComputedStyle(document.querySelector('.pv-wh')).fontFamily")
    assert wh.startswith("Newsreader")                                   # the day reads as a section head
    assert page.evaluate("getComputedStyle(document.querySelector('.pv-rh')).fontFamily").startswith("Newsreader")
    assert "Claude's call arrives" in page.inner_text("[data-pvopen='4']")


@pytest.mark.render
def test_the_slate_has_serif_type_in_the_site_ink_and_a_face_per_game(page):
    """David, 2026-09-29: "very clinical, so much black and white", then the brown ground was "too
    brown", then the cream type left "a weird brown glow". The serif stays; its colour is the site's
    own ink: the day heads and the matchup --ink, the headlines --ink-2. Each row leads with the face
    the headline is about."""
    colours = page.evaluate("""() => ['.pv-wh', "[data-pvopen='1'] .pv-rh", '.pv-rm']
        .map(s => getComputedStyle(document.querySelector(s)).color)""")
    ink = page.evaluate("""() => ['--ink', '--ink-2'].map(v => { const e = document.createElement('i');
        e.style.color = `var(${v})`; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; })""")
    assert colours == [ink[0], ink[1], ink[0]]                           # never the newsprint cream
    ground = page.evaluate("getComputedStyle(document.querySelector('.pv')).borderImageSource")
    assert ground == "none"                                              # no painted ground of its own
    faces = [page.locator(f"[data-pvopen='{i}'] .pv-hs img, [data-pvopen='{i}'] .pv-hs .fallback").count() for i in range(5)]
    assert faces == [1, 1, 1, 1, 0]                                      # ATL @ NO: no take, no face
    pick = page.evaluate("""() => [
        pvFacePlayer({head: "Dak outguns a Collins-less Texans team", players: [{n: "Nico Collins"}, {n: "Dak Prescott"}]}).n,
        pvFacePlayer({head: "Love's arm carries GB", players: [{n: "Josh Jacobs"}, {n: "Jordan Love"}]}).n,
        pvFacePlayer({head: "Defense rules the day", players: [{n: "Josh Jacobs"}, {n: "Jordan Love"}]}).n]""")
    assert pick == ["Dak Prescott", "Jordan Love", "Josh Jacobs"]       # first name, last name, else his first call


def texts(pg, sel):
    return pg.evaluate("s => [...document.querySelectorAll(s)].map(e => e.innerText.replace(/\\s+/g, ' ').trim())", sel)


@pytest.mark.render
def test_a_row_shows_only_a_confident_pick(page):
    """David, 2026-09-29: drop the "JAX getting 2.5" from the slate; only Confident and Very
    confident speak there. A slight pick, no pick and no take draw nothing right of the matchup."""
    has = [page.locator(f"[data-pvopen='{i}'] .pv-ats").count() for i in range(5)]
    assert has == [0, 1, 1, 0, 0]                                        # no pick, strong, solid, slight, no take
    assert texts(page, ".pv-ats") == ["Very confident", "Confident"]
    assert page.locator(".pv-row .pv-side").count() == 0


def open_game(pg, i):
    pg.evaluate(f"() => {{ PV_I = {i}; PV_OPEN = true; render(); }}")


def bet_rows(pg):
    return pg.evaluate("""() => [...document.querySelectorAll('.pv-bt tbody tr')].map(r =>
        [...r.children].map(c => c.innerText.replace(/\\s+/g, ' ').trim()))""")


@pytest.mark.render
def test_the_answer_is_one_row_per_bet_vegas_beside_claude(page):
    """Storyboard 3A (2026-10-05; David: "saying the same thing many times", "Are you saying PIT is covering?"):
    Claude's score, then Moneyline, Spread and Total, Vegas's number in its own column beside Claude's call."""
    open_game(page, 2)                                                   # DET @ CAR
    assert page.inner_text(".pvn-ans .pv-am") == "DET 30, CAR 19"
    assert texts(page, ".pv-bt thead th") == ["", "VEGAS", "CLAUDE"]
    assert bet_rows(page) == [["Moneyline", "DET 64%", "DET wins 74% chance"],
                              ["Spread", "DET by 3.5", "DET covers Confident wins by 4 or more"],
                              ["Total", "50.5", "Under Slight 50 points or fewer"]]
    open_game(page, 1)                                                   # JAX @ LA: Claude takes the underdog
    assert bet_rows(page)[1][1:] == ["LA by 3", "JAX covers Very confident wins, or loses by 2 or less"]   # 3 is a push
    # Gone with 3A: the market's score, the bar, "getting / giving", where a line opened.
    ans = page.inner_text(".pvn-ans")
    for gone in ("market", "getting", "giving", "opened"):
        assert gone not in ans, gone
    assert page.locator(".pvn-ans .pv-pb").count() == 0
    open_game(page, 4)                                                   # ATL @ NO: no take, Vegas only
    assert page.locator(".pvn-ans .pv-am").count() == 0
    assert [r[2] for r in bet_rows(page)] == ["–", "–", "–"]


@pytest.mark.render
def test_the_game_page_reads_like_a_newspaper(page):
    """Storyboard option C (2026-09-29): headline and dek, the call, the box score, then the rest of
    the story. Section names are run-in words and plain bold names, never all-caps label rows."""
    page.click("[data-pvopen='2']")                                      # DET @ CAR
    parts = page.evaluate("() => [...document.querySelector('.pvn').children].map(e => e.className)")
    # The answer first (2026-10-05, plan U3): pick, line, total and win chance above the headline.
    assert parts == ["pvn-ans", "pvn-head", "pvn-call", "pvn-box", "pvn-story"]
    assert page.evaluate("() => [...document.querySelectorAll('.pv-bt tbody tr')].map(e => e.className)") == ["ml", "spread", "total"]
    box =page.evaluate("() => [...document.querySelectorAll('.pva')].map(r => r.classList[1])")
    # "slip" since 2026-10-03: the take names Amon-Ra St. Brown, who has lines on the fixture's slate.
    assert box == ["matchup", "handoff", "inj", "wx", "rest"]
    assert page.evaluate("getComputedStyle(document.querySelector('.pv-head')).fontFamily").startswith("Newsreader")
    # The story's paragraphs (2026-09-30), every one set alike: one voice, not a dek and smaller body copy.
    assert texts(page, ".pvn-head .pv-dek") == ["Rain keeps it on the ground, and Carolina allows the second-most RB points.",
                                                "Gibbs gets the carries early and Detroit leans on him once it leads.",
                                                "With Coker out, Young has one target he trusts, and the passing game stalls."]
    sizes = page.evaluate("() => [...document.querySelectorAll('.pvn-head .pv-dek')].map(p => getComputedStyle(p).font)")
    assert len(set(sizes)) == 1
    # Each player call's first mention is bold and opens his profile (2026-09-30); St. Brown is not named.
    assert texts(page, ".pvn-head .pv-nm") == ["Gibbs", "Young"]
    assert page.evaluate("getComputedStyle(document.querySelector('.pv-nm')).fontWeight") == "700"
    call = page.inner_text(".pvn-call").replace("\n", " ")
    for want in ("The call.", "Carolina without Coker"):
        assert want in call, want
    ans = page.inner_text(".pvn-ans").replace("\n", " ")
    for want in ("DET covers", "Confident", "Under", "Slight", "50.5", "DET by 3.5"):
        assert want in ans, want
    assert page.inner_text(".pv-risk").startswith("What could go wrong.")
    # Show, don't tell (2026-09-30): no research notes, no before-the-line process, no footnotes.
    dz = page.inner_text(".pv-dz")
    for gone in ("before seeing the line", "moved it to 11", "Research notes", "5.1 yards a carry", "2011–2025",
                 "Opinion, not a tested model", "WR is faded", "1 gives up the fewest", "backtest"):
        assert gone not in dz, gone
    assert page.locator(".pv-dz .pv-note, .pv-foot").count() == 0
    caps = page.evaluate("""() => [...document.querySelectorAll('.pvn .pva-h, .pvn .pv-rin, .pvn .pv-k')]
        .filter(e => getComputedStyle(e).textTransform === 'uppercase').length""")
    assert caps == 0
    assert page.locator(".pv-score").count() == 0 and page.locator(".pv-vs").count() == 0
    page.click("[data-pvstep='-1']")
    page.click("[data-pvstep='-1']")                                     # PIT @ CLE: no edge
    assert page.locator(".pv-bt .spread .pv-conf.none").count() == 1 and page.locator(".pv-bt .total .pv-conf.none").count() == 1
    assert page.locator(".pvn-call").count() == 0                        # no edge, no reason to print


@pytest.mark.render
def test_the_answer_is_above_the_fold_on_a_phone_and_the_story_starts_below_it(browser, page_file):
    """Plan U3 (2026-10-05): the line, total, win chance and Claude's pick were under five paragraphs. At
    390x844 the whole block ends above the fold and the headline starts under it."""
    errors = []
    ctx, pg = open_preview(browser, page_file, 390, 844, errors)
    try:
        pg.click("[data-pvopen='2']")                                    # DET @ CAR: every cell
        box = pg.evaluate("""() => { const r = s => document.querySelector(s).getBoundingClientRect();
            return {ans: [r('.pvn-ans').top, r('.pvn-ans').bottom], head: r('.pvn-head').top, dek: r('.pv-dek').top, vh: innerHeight}; }""")
        assert box["ans"][1] <= box["vh"], box                           # the whole block is on the first screen
        assert box["head"] >= box["ans"][1] - 1 and box["dek"] > box["head"]
        assert pg.evaluate("document.documentElement.scrollWidth") <= 390
        assert errors == [], errors
    finally:
        ctx.close()


def open_record(pg, wk=None):
    """Past games, from its row under the slate (or straight to a week, as a slate row would)."""
    if wk is None:
        pg.click("[data-pvarcwk]")
    else:
        pg.evaluate(f"() => pvRecOpen({wk})")
    pg.wait_for_function("document.querySelector('.pv').classList.contains('rec')")


def end_games(pg, *idx):
    """Puts the given games 5 hours past kickoff, so pvOver counts them over (SCHED_GRACE_MS is 4 hours)."""
    pg.evaluate(f"""() => {{ const t = new Date(Date.now() - 5 * 3600e3).toISOString();
        {list(idx)}.forEach(i => LIVE_PREVIEW.games[i].kickoff = t); render(); }}""")


@pytest.mark.render
def test_past_games_opens_from_under_the_slate_and_back_closes_it(page):
    """Storyboard 1A and 2A (2026-10-05, https://claude.ai/artifact/NTeV8W2N9mFnYgftfbuqPV): the record left the
    top of the slate (David: "randomly placed", wordy). It heads Past games, one row per bet, reached from a
    row under the games. The fixture's record runs through week 2, the page's own week, so week 1 is past."""
    assert page.locator(".pv-rec, .pv-rec0").count() == 0                # no record card on the slate
    assert page.inner_text(".pv-title") == "Game previews · Week 2"
    assert texts(page, "[data-pvarcwk]") == ["Past weeks · Claude's record ›"]
    assert page.locator("[data-pvarcwk]").evaluate("e => e.getBoundingClientRect().top") > page.locator(".pv-win").last.evaluate(
        "e => e.getBoundingClientRect().bottom") - 1                     # under the games, not above them
    # Scrolled down to the row: a phone's bottom tab bar (2026-10-05) covers the screen's last 64px, so a
    # fixed scroll could leave the row under it and the click would scroll the page again before it opens.
    page.evaluate("document.querySelector('[data-pvarcwk]').scrollIntoView({block: 'center'})")
    y = page.evaluate("scrollY")
    assert y > 0
    open_record(page)
    assert not page.is_visible(".pv-slate") and page.is_visible(".pv-rz")
    assert page.evaluate("location.hash") == "#preview"
    assert page.inner_text(".pv-sk") == "CLAUDE THIS SEASON · THROUGH WEEK 2"
    rows = page.evaluate("() => [...document.querySelectorAll('.pv-st tr')].map(r => [...r.cells].map(c => c.innerText.trim()))")
    assert rows == [["Moneyline", "5–3", "63%"], ["Spread", "4–2–1", "67%"], ["Total", "5–1", "83%"]]
    assert page.inner_text(".pv-sc") == "Spread by confidence: Very confident 1–0–1 · Confident 1–1 · Slight 2–1"
    for gone in ("closer than the market", "Fav picks", "Blind number"):
        assert gone not in page.inner_text(".pv-rz"), gone
    assert page.inner_text(".pv-wstep .pv-mt") == "Week 1"
    assert page.locator(".pv-rg").count() == 4                           # week 1's graded games, from the record
    page.go_back()
    page.wait_for_function("!document.querySelector('.pv').classList.contains('rec')")
    page.wait_for_function(f"scrollY === {y} && !!document.querySelector('.pv-slate')")
    assert page.is_visible(".pv-slate") and page.evaluate("scrollY") == y


@pytest.mark.render
def test_the_back_button_closes_past_games(page):
    open_record(page)
    assert page.inner_text("[data-pvrecback]") == "‹ Preview"
    page.click("[data-pvrecback]")
    assert page.is_visible(".pv-slate") and page.locator(".pv-rz").count() == 0
    assert page.evaluate("LAYERS.length") == 0


@pytest.mark.render
def test_a_game_that_is_over_leaves_the_slate_for_past_games(page):
    """1A: once a game is over (final, or 4 hours past kickoff) the slate drops it; This week's Final row
    holds it, and its page opens from there with the final's calls, back to Past games."""
    end_games(page, 0, 1)
    assert "PIT @ CLE" not in texts(page, ".pv-rm") and "JAX @ LA" not in texts(page, ".pv-rm")
    assert texts(page, "[data-pvarcwk]")[0] == "Final · 2 games this week ›"
    open_record(page)                                                    # the first row: this week
    assert page.inner_text(".pv-wstep .pv-mt") == "Week 2"
    assert [t.split(" ")[0:3] for t in texts(page, ".pv-rg-m")] == [["PIT", "@", "CLE"], ["JAX", "@", "LA"]]
    page.click(".pv-rg >> nth=1")
    assert is_open(page) and match(page) == "JAX @ LA"
    assert page.inner_text("[data-pvback]") == "‹ Past games"
    assert page.locator(".pva.handoff").count() == 0                     # a finished game's lines are gone
    page.click("[data-pvback]")
    assert page.is_visible(".pv-rz") and page.inner_text(".pv-wstep .pv-mt") == "Week 2"


@pytest.mark.render
def test_every_game_over_says_so_on_the_slate(page):
    end_games(page, 0, 1, 2, 3, 4)
    assert page.locator(".pv-win").count() == 0
    assert page.inner_text(".pv-allover").startswith("Every game this week is over.")
    assert texts(page, "[data-pvarcwk]") == ["Final · 5 games this week ›", "Past weeks · Claude's record ›"]


@pytest.mark.render
def test_the_week_stepper_stays_in_range(page):
    """David asked how 2A scales to 18 weeks: a stepper, one row wide at any count, from week 1 to this week."""
    end_games(page, 0)
    open_record(page, 2)
    assert page.is_disabled("[data-pvarcstep='1']")
    page.click("[data-pvarcstep='-1']")
    assert page.inner_text(".pv-wstep .pv-mt") == "Week 1" and page.is_disabled("[data-pvarcstep='-1']")
    assert page.inner_text(".pv-wl") == "Moneyline 3–1 · Spread 3–0 · Total 2–1"


@pytest.mark.render
def test_an_earlier_weeks_game_opens_from_the_archive(page):
    """An earlier week's previews come from preview_archive.json (design/preview_archive.py), fetched on first
    open. Here the fetched document is set by hand: one week-1 game, drawn by the same dossier."""
    page.evaluate("""() => { const g = structuredClone(LIVE_PREVIEW.games[2]);
        Object.assign(g, {key: "2026_01_DET_CAR", week: 1, kickoff: "2026-09-14T17:00:00Z", matchup: null, inj: null,
          wx: null, rest: null, travel: null, site: null});
        g.take.players.forEach(p => p.proj = null);
        PV_ARC = {season: 2026, weeks: {"1": [g]}}; }""")
    open_record(page, 1)
    assert texts(page, ".pv-rg-m") == ["DET @ CAR"]
    page.click("[data-pvarcg]")
    assert is_open(page) and match(page) == "DET @ CAR"
    assert page.inner_text(".pv-ko").startswith("Week 1 · ")
    assert page.inner_text("[data-pvback]") == "‹ Past games"
    assert page.locator(".pva").count() == 0                             # an archived game keeps only its take
    assert all(t == "" for t in texts(page, ".pv-pj"))                  # no projection was archived
    page.click("[data-pvback]")
    assert page.is_visible(".pv-rz") and page.evaluate("PV_ARC_G") is None


@pytest.mark.render
def test_without_a_graded_week_there_is_no_season_block(page):
    page.evaluate("() => { LIVE_PREVIEW.record.weeks.splice(0); render(); }")
    assert page.locator("[data-pvarcwk]").count() == 0                   # nothing over, nothing graded
    page.evaluate("() => { LIVE_PREVIEW.record = null; render(); }")
    end_games(page, 0)
    open_record(page)
    assert page.locator(".pv-season").count() == 0 and page.locator(".pv-rg").count() == 1


@pytest.mark.render
def test_no_signed_spread_anywhere_in_the_preview(page):
    """David: never a signed spread. A line is "PIT by 2.5", a call "CLE covers"."""
    seen = [page.inner_text(".pv-slate")]
    for i in range(5):
        page.evaluate(f"() => {{ PV_I = {i}; PV_OPEN = true; render(); }}")
        seen += texts(page, ".pvn-ans, .pvn-head, .pvn-call")
    page.evaluate("() => { PV_OPEN = false; render(); }")
    open_record(page)
    seen.append(page.inner_text(".pv-rz"))
    signed = [m.group(0) for s in seen for m in re.finditer(r"(?<![\w.])[+\-−]\d+(\.\d)?", s)]
    assert signed == []
    assert " by " in " ".join(seen) and "covers" in " ".join(seen)


@pytest.mark.render
def test_a_tap_opens_the_dossier_and_back_returns_to_the_slate_where_it_was(page):
    page.evaluate("window.scrollTo(0, 120)")
    y = page.evaluate("scrollY")
    page.click("[data-pvopen='3']")
    assert is_open(page) and match(page) == "SF @ NYJ"
    assert not page.is_visible(".pv-slate")
    assert page.evaluate("location.hash") == "#preview"          # the game is not in the URL
    lines = page.inner_text(".pvn-ans")
    assert "NYJ by 1.5" in lines and "opened" not in lines              # storyboard 3A cut where a line opened
    assert "+3 zones east · kicks off at 1:25 PM body time" in page.inner_text(".pva.rest")
    page.go_back()
    page.wait_for_function("!document.querySelector('.pv').classList.contains('open')")
    page.wait_for_function(f"scrollY === {y}")
    assert page.evaluate("scrollY") == y
    assert page.evaluate("location.hash") == "#preview"


@pytest.mark.render
def test_the_all_games_button_closes_the_dossier(page):
    page.click("[data-pvopen='0']")
    page.click("[data-pvback]")
    assert not is_open(page)
    page.click("[data-pvopen='1']")                             # and opening again still works
    assert is_open(page) and match(page) == "JAX @ LA"


@pytest.mark.render
def test_optional_rows_are_absent_without_data(page):
    rows = lambda: page.evaluate("() => [...document.querySelectorAll('.pva')].map(r => r.classList[1])")
    page.click("[data-pvopen='4']")                              # ATL @ NO: dome, no take, no rest
    assert rows() == ["inj", "wx"]                               # no matchup or rest; a dome says Dome
    # The answer still gives Vegas on every bet: no take, so no score and no call.
    assert page.evaluate("() => [...document.querySelectorAll('.pv-bt tbody tr')].map(e => e.className)") == ["ml", "spread", "total"]
    assert page.locator(".pvn-ans .pv-am").count() == 0
    assert page.inner_text(".pva.wx .pv-fc") == "Dome" and "forecast" not in page.inner_text(".pva.wx").lower()
    assert page.locator(".pvn-call").count() == 0 and page.locator(".pvn-story").count() == 0
    assert "Claude's call on this game arrives" in page.inner_text(".pvn-head")
    assert page.locator(".pv-pl").count() == 0 and page.locator(".pv-risk").count() == 0
    page.click("[data-pvstep='-1']")
    page.click("[data-pvstep='-1']")                             # DET @ CAR: the one with defense ranks
    assert match(page) == "DET @ CAR" and page.locator(".pv-mx").count() == 1
    assert page.locator(".pv-mx tr.dim").inner_text().startswith("WR")
    assert "Rain" in page.inner_text(".pv-eff")                  # rain 56% is past the backtest's threshold
    assert "J. Coker" in page.inner_text(".pv-inj >> nth=1")


@pytest.mark.render
def test_neutral_site_and_short_week(page):
    page.click("[data-pvopen='1']")
    assert "Neutral site: Wembley Stadium" in page.inner_text(".pva.rest")
    assert "OFF A BYE" in page.inner_text(".pva.rest")
    page.click("[data-pvstep='-1']")
    assert page.locator(".pva.rest .pv-tag.short").count() == 2


def swipe(pg, dx):
    pg.evaluate("""dx => {
        const el = document.querySelector('[data-pvswipe]');
        const t = x => new Touch({identifier: 1, target: el, clientX: x, clientY: 300});
        el.dispatchEvent(new TouchEvent('touchstart', {touches: [t(200)], changedTouches: [t(200)], bubbles: true}));
        el.dispatchEvent(new TouchEvent('touchend', {touches: [], changedTouches: [t(200 + dx)], bubbles: true}));
    }""", dx)


@pytest.mark.render
def test_a_swipe_in_the_dossier_walks_the_games_and_stops_at_the_ends(page):
    page.click("[data-pvopen='0']")
    swipe(page, -120)
    assert match(page) == "JAX @ LA" and is_open(page)
    swipe(page, 120)
    assert match(page) == "PIT @ CLE"
    swipe(page, 120)                                  # past the first game: nothing
    assert match(page) == "PIT @ CLE"
    swipe(page, -20)                                  # a nudge is not a swipe
    assert match(page) == "PIT @ CLE"


@pytest.mark.render
def test_a_player_row_opens_his_profile(page):
    page.click("[data-pvopen='0']")
    page.evaluate("() => { window.__opened = []; openProfile = p => window.__opened.push(p.slug); }")
    page.click(".pv-p >> nth=0")
    assert page.evaluate("window.__opened") == ["dk-metcalf"]


@pytest.mark.render
def test_a_bold_name_in_the_story_opens_his_profile(page):
    page.click("[data-pvopen='2']")                                      # DET @ CAR
    page.evaluate("() => { window.__opened = []; openProfile = p => window.__opened.push(p.slug); }")
    page.click(".pv-nm >> text=Young")
    assert page.evaluate("window.__opened") == ["bryce-young"]


def test_a_shared_surname_is_never_bolded_alone(page):
    """IND @ WAS has two Warrens: "Warren" alone could be either, so only a full name marks one."""
    got = page.evaluate("""() => pvNamesHTML(["Warren runs. Tyler Warren catches. Then Warren again."],
        [{n: "Jaylen Warren"}, {n: "Tyler Warren"}])""")
    assert got == ['Warren runs. <button type="button" class="pv-nm" data-pvp="1">Tyler Warren</button> catches. Then Warren again.']


@pytest.mark.render
def test_a_desktop_shows_the_rail_beside_the_dossier(browser, page_file):
    errors = []
    ctx, pg = open_preview(browser, page_file, 1280, 900, errors)
    try:
        assert pg.is_visible(".pv-slate") and pg.is_visible(".pv-dz") and match(pg) == "PIT @ CLE"
        pg.click("[data-pvopen='2']")
        assert match(pg) == "DET @ CAR" and pg.locator(".pv-row.cur .pv-rm").inner_text() == "DET @ CAR"
        assert pg.evaluate("LAYERS.length") == 0 and not is_open(pg)   # a click on a desktop pushes no layer
        slate, dz = pg.evaluate("""() => [document.querySelector('.pv-slate'), document.querySelector('.pv-dz')]
            .map(e => e.getBoundingClientRect().left)""")
        assert slate < dz
        # The box score is a column right of the call, the two sharing a top edge (storyboard option C).
        call, box = pg.evaluate("""() => ['.pvn-call', '.pvn-box'].map(s => {
            const b = document.querySelector(s).getBoundingClientRect(); return [b.left, b.top, b.right]; })""")
        assert box[0] > call[2] and abs(box[1] - call[1]) < 2
        # Past games opens in the dossier's place, the rail stays; a game in the rail closes it.
        open_record(pg)
        assert pg.is_visible(".pv-slate") and pg.is_visible(".pv-rz") and pg.locator(".pv-dz").count() == 0
        assert pg.locator(".pv-fold.cur").count() == 1 and pg.locator(".pv-row.cur").count() == 0
        pg.click("[data-pvopen='1']")
        assert match(pg) == "JAX @ LA" and pg.locator(".pv-rz").count() == 0 and pg.evaluate("LAYERS.length") == 0
        assert errors == [], errors
    finally:
        ctx.close()


@pytest.mark.render
def test_nothing_scrolls_sideways_at_360(page):
    for i in range(5):
        page.evaluate(f"() => {{ PV_I = {i}; PV_OPEN = true; render(); }}")
        assert page.evaluate("document.documentElement.scrollWidth") <= 360, f"game {i}"
    page.evaluate("() => { PV_OPEN = false; PV_REC = true; PV_ARC_WK = 2; render(); }")
    assert page.locator(".pv-rz").count() == 1 and page.locator(".pv-rg").count() > 0
    assert page.evaluate("document.documentElement.scrollWidth") <= 360, "Past games"


# The fixture's preview games and its props slate are different games, so the hand-off test turns
# game 3 into the props slate's SEA @ SF and names Kittle in its take.
AS_SEA_SF = """() => { const g = LIVE_PREVIEW.games[3]; g.away = 'SEA'; g.home = 'SF';
  g.take.players = [{n: 'George Kittle', slug: 'george-kittle', pos: 'TE', team: 'SF', proj: 9.1, call: 'up',
                     why: 'Seattle allows the most TE points.'}];
  PV_I = 3; PV_OPEN = true; render(); }"""


@pytest.mark.render
def test_the_dossier_hands_its_players_to_the_slip(page):
    """From this game to your slip (2026-10-03): each player the take names with his lines in the
    player sheet's row; a side tapped lands in the same tray as Slips', and he is marked on slip;
    "All N players in Slips" opens Slips on the game's kickoff with its card."""
    assert page.locator(".pva.handoff").count() == 0, "no game of the props slate is open"
    page.evaluate(AS_SEA_SF)
    page.evaluate("pvClose(); pvOpen(3)")   # the real open: it pushes the dossier's history entry
    sec = page.locator(".pva.handoff")
    assert sec.locator(".pva-h").inner_text() == "From this game to your slip"
    assert sec.locator(".pv-sl").count() == 1 and sec.locator(".sl-ln").count() == 1, "one line each, his position's own (REC)"
    assert sec.locator(".sl-mk").inner_text().startswith("Rec yds"), "the primary line is his yards market"
    assert sec.locator("[data-slplayer]").inner_text().startswith("2 lines"), "TD and yards; LONG is no line"
    assert page.locator(".tray").count() == 0, "no tray on Preview until a pick is in it"
    rec = page.evaluate("PROPS.findIndex(p => p.slug === 'george-kittle' && p.mkt === 'REC')")
    sec.locator(f"[data-slpick='{rec}'][data-side='higher']").click()
    assert page.evaluate("SLIP") == [rec] and page.evaluate(f"slipSide({rec})") == "higher"
    assert page.locator(".tray .tray-n").inner_text() == "1"
    assert page.locator(".pva.handoff .sl-on").count() == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    go = page.locator("[data-pvslips]")
    n = page.evaluate("new Set(pvSlipRows(LIVE_PREVIEW.games[3]).map(([p]) => p.slug)).size")
    assert go.inner_text().startswith(f"All {n} players in Slips")
    go.click()
    assert page.evaluate("SURFACE") == "parlay" and page.evaluate("GAL_WIN") == "evening-sun"
    assert page.locator(".sl-game[data-slgamecard='SEA @ SF']").count() == 1
    assert page.locator(".sl-row[data-slplayer='george-kittle'] .sl-on").count() == 1
    # Back from Slips lands on the dossier it left, not the slate; Back again closes the dossier.
    page.go_back()
    page.wait_for_function("SURFACE === 'preview'")
    assert page.evaluate("PV_OPEN") is True and page.locator(".pva.handoff").count() == 1
    page.go_back()
    page.wait_for_function("PV_OPEN === false")

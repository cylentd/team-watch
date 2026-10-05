"""Left the game hurt (2026-10-04): the Digest's headline and Live's chip.

David: "the headline should change when something big happens, like an injury." Sleeper and the
scoreboard say nothing about an injury mid-game; the play-by-play does. nflverse's text (games/*.json)
reads "PHI-S.Barkley was injured during the play." and "** Injury Update: PHI-J.Hurts has returned to
the game." ESPN's summary is BELIEVED to carry the same text; UNVERIFIED until Monday's game (2026-10-05,
ATL @ NO), so the scan is pinned here against the nflverse wording and nothing else.

League-wide since the same evening (David: "The Digest is supposed to be GENERIC for the public. It
shouldn't hone on to my roster or their roster."): the players to watch are every QB/RB/WR/TE that
LIVE_RANKS projects at 8 points or more, every live game is scanned, and nothing drawn names a league or a
team of mine. The first version watched my starters only (8b91604) and is superseded.

The scan (data/gameday/hurt.js gdHurtScan) is pure; the render tests plant GD_HURT, since ESPN refuses
servers and headless browsers and the poller cannot be fed from a test's network."""
import json
import re

import pytest

from test_render import LIVE_PLANT, browser, drive, go, open_page, SEED  # noqa: F401  (the suite's one Chromium)

pytestmark = pytest.mark.render

# Two lines copied from games/2026_03_PHI_CHI.json and games/2026_02_PHI_TEN.json (nflverse wording).
REAL_INJURED = "S.Barkley left guard to PHI 28 for no gain (J.Simmons). PHI-S.Barkley was injured during the play."
REAL_RETURNED = "J.Hurts pass short right to D.Wicks pushed ob at PHI 46 for 13 yards (C.Lewis). ** Injury Update: PHI-J.Hurts has returned to the game."
# Real lines too: a defender hurt on a play my QB ran; and a trap, where the ball carrier's name sits just
# before the injured player's own ("M.Evans. SF-M.Evans").
REAL_DEFENDER = "J.Hurts scrambles left tackle to CHI 27 for 20 yards (X.Woods). CHI-C.Lewis was injured during the play."
REAL_TRAP = "B.Purdy pass incomplete short middle to M.Evans. SF-M.Evans was injured during the play."
REAL_STUKES = "O.Hampton up the middle to LV 26 for 7 yards (J.McCoy; T.Stukes). ** Injury Update: LV-T.Stukes has returned to the game."

HURTS_OUT = "J.Hurts pass incomplete short left to D.Smith. PHI-J.Hurts was injured during the play."


def me(slug, name, team):
    return {"slug": slug, "name": name, "team": team}


NAMES = {
    "s.barkley": [me("saquon-barkley", "Saquon Barkley", "PHI")],
    "j.hurts": [me("jalen-hurts", "Jalen Hurts", "PHI")],
    "t.stukes": [me("tre-stukes", "Tre Stukes", "LV")],
    "m.evans": [me("mike-evans", "Mike Evans", "SF")],
    "b.purdy": [me("brock-purdy", "Brock Purdy", "SF")],
    "j.williams": [me("jameson-williams", "Jameson Williams", "DET")],
}


def play(text, q=2, clock="9:41"):
    return {"text": text, "period": {"number": q}, "clock": {"displayValue": clock}}


def summary(clubs, plays):
    """ESPN's shape: drives.previous[] then drives.current, plays in order. The plays split across both."""
    k = max(len(plays) - 1, 0)
    return {"header": {"competitions": [{"competitors": [{"team": {"abbreviation": c}} for c in clubs]}]},
            "drives": {"previous": [{"plays": plays[:k]}], "current": {"plays": plays[k:]}}}


@pytest.fixture
def blank(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    yield page
    ctx.close()
    assert errors == []


def scan(page, clubs, plays, names=NAMES):
    return page.evaluate("([s, n]) => gdHurtScan(s, n)", [summary(clubs, plays), names])


def test_my_starter_is_flagged_and_a_defender_not_in_names_is_ignored(blank):
    got = scan(blank, ["PHI", "CHI"], [play(REAL_DEFENDER, 1, "3:02"), play(REAL_INJURED, 2, "9:41")])
    assert got == [{"slug": "saquon-barkley", "name": "Saquon Barkley", "team": "PHI", "q": 2, "clock": "9:41", "back": False}]
    # the QB named in the defender's line is not hurt: he only ran the ball
    assert scan(blank, ["PHI", "CHI"], [play(REAL_DEFENDER)]) == []


def test_a_return_clears_him_and_a_second_injury_flags_him_again(blank):
    got = scan(blank, ["PHI", "CHI"], [play(HURTS_OUT, 3, "4:12"), play(REAL_RETURNED, 3, "2:30")])
    assert got == [{"slug": "jalen-hurts", "name": "Jalen Hurts", "team": "PHI", "q": 3, "clock": "4:12", "back": True}]
    again = scan(blank, ["PHI", "CHI"], [play(HURTS_OUT), play(REAL_RETURNED), play(HURTS_OUT, 4, "1:00")])
    assert [(h["slug"], h["back"], h["q"]) for h in again] == [("jalen-hurts", False, 4)]
    # a return for someone never seen hurt in this summary is no news
    assert scan(blank, ["PHI", "CHI"], [play(REAL_RETURNED)]) == []


@pytest.mark.parametrize("text", [
    "LV-T.Stukes was injured during the play.",
    "T.Stukes was injured during the play.",
    "T. Stukes was injured during the play.",
    "LV-T. Stukes was injured during the play.",
    "O.Hampton up the middle to LV 26 for 7 yards (J.McCoy; T.Stukes). LV-T.Stukes was injured during the play.",
])
def test_both_spellings_of_an_abbreviated_name_match(blank, text):
    got = scan(blank, ["LV", "LAC"], [play(text)])
    assert [h["slug"] for h in got] == ["tre-stukes"]


def test_the_real_return_line_for_stukes_clears_him_in_either_spelling(blank):
    for spelled in (REAL_STUKES, REAL_STUKES.replace("LV-T.Stukes", "LV-T. Stukes")):
        got = scan(blank, ["LV", "LAC"], [play("LV-T.Stukes was injured during the play."), play(spelled)])
        assert [(h["slug"], h["back"]) for h in got] == [("tre-stukes", True)]


def test_the_name_before_the_injured_players_is_not_taken_for_his(blank):
    got = scan(blank, ["SF", "ARI"], [play(REAL_TRAP)])
    assert [h["slug"] for h in got] == ["mike-evans"]


def test_a_club_in_the_text_must_be_his_and_two_in_one_play_are_both_read(blank):
    # J.Williams on BUF is not my DET starter; with no club in the text he must play in this game
    assert scan(blank, ["BUF", "HOU"], [play("BUF-J.Williams was injured during the play.")]) == []
    assert scan(blank, ["DET", "BUF"], [play("DET-J.Williams was injured during the play.")])[0]["slug"] == "jameson-williams"
    assert scan(blank, ["BUF", "HOU"], [play("J.Williams was injured during the play.")]) == []
    both = scan(blank, ["PHI", "CHI"], [play("PHI-S.Barkley was injured during the play. PHI-J.Hurts was injured during the play.")])
    assert sorted(h["slug"] for h in both) == ["jalen-hurts", "saquon-barkley"]


def test_a_summary_without_plays_flags_nobody(blank):
    for s in (None, {}, {"drives": {}}, {"drives": {"previous": [{}], "current": {}}}, summary(["PHI", "CHI"], [])):
        assert blank.evaluate("([s, n]) => gdHurtScan(s, n)", [s, NAMES]) == []


# ---------------------------------------------------------------- the page

LEAD = {
    "7547": {"n": "Amon-Ra St. Brown", "pos": "WR", "team": "DET", "pts": 31.4, "s": {"rec": 10, "rec_yd": 180, "rec_td": 2}},
    "9226": {"n": "De'Von Achane", "pos": "RB", "team": "MIA", "pts": 27.1, "s": {"rush_att": 18, "rush_yd": 130, "rush_td": 1}},
    "8183": {"n": "Brock Purdy", "pos": "QB", "team": "SF", "pts": 24.0, "s": {"pass_cmp": 22, "pass_att": 30, "pass_yd": 290, "pass_td": 3}},
    "12481": {"n": "Cam Skattebo", "pos": "RB", "team": "NYG", "pts": 19.2, "s": {"rush_att": 20, "rush_yd": 90, "rush_td": 2}},
    "6801": {"n": "Tee Higgins", "pos": "WR", "team": "CIN", "pts": 17.8, "s": {"rec": 6, "rec_yd": 98}},
    "4217": {"n": "George Kittle", "pos": "TE", "team": "SF", "pts": 15.5, "s": {"rec": 6, "rec_yd": 85, "rec_td": 1}},
    "12526": {"n": "Tetairoa McMillan", "pos": "WR", "team": "CAR", "pts": 12.0, "s": {"rec": 5, "rec_yd": 70}},
}
SUN = "2026-10-04T12:00:00Z"
SF_CLOCK = {"SF": {"state": "in", "q": 3, "clock": "4:12", "half": False, "detail": "", "clubs": ["SF"]}}
PURDY = {"slug": "brock-purdy", "name": "Brock Purdy", "team": "SF", "q": 3, "clock": "5:00", "back": False}
ACHANE = {"slug": "devon-achane", "name": "De'Von Achane", "team": "MIA", "q": 3, "clock": "6:00", "back": False}
HUNTLEY = {"slug": "tyler-huntley", "name": "Tyler Huntley", "team": "BAL", "q": 2, "clock": "1:00", "back": False}

# The fixture's LIVE_RANKS holds five players. Planted beside them: Achane (starts for me), Huntley (in none of
# my lineups, the league-wide case) and Stukes (under the 8-point line).
RANKS = [
    {"slug": "devon-achane", "n": "De'Von Achane", "pos": "RB", "team": "MIA", "pts": 21.5},
    {"slug": "tyler-huntley", "n": "Tyler Huntley", "pos": "QB", "team": "BAL", "pts": 19.9},
    {"slug": "tre-stukes", "n": "Tre Stukes", "pos": "WR", "team": "LV", "pts": 5.0},
]

# Week 2 of both leagues, every club given a game of its own (Sunday's, ESPN id "E<club>"), SF on the clock.
PLANT = """(cfg) => {
  PLANT_LEAGUES
  for (const r of cfg.ranks) if (!LIVE_RANKS.rows.some(x => x.slug === r.slug)) LIVE_RANKS.rows.push({kick: null, ...r});
  const clubs = [...new Set([...GD.leagues.flatMap(lg => Object.values(lg.teams).flatMap(tm => tm.lineup.map(r => r.team))), 'BAL'])];
  const games = clubs.map(c => ({home: c, away: 'O' + c, kickoff: cfg.sun, week: 2, espn: 'E' + c}));
  GD_GAMES.splice(0, GD_GAMES.length, ...games);
  Date.now = () => Date.parse(cfg.at);
  GD_STATS.games = {};
  for (const g of games) for (const c of [g.home, g.away]) GD_STATS.games[c] = cfg.state;
  GD_STATS.lead = cfg.lead;
  GD_AT = Date.now(); GD_CLOCK = cfg.clock; GD_HURT = {};
  LIVE_DIGEST.hurt = []; LIVE_DIGEST.starters = [];
  DG_CUT = null; render();
}""".replace("PLANT_LEAGUES", LIVE_PLANT())


def cfg(**over):
    c = {"at": "2026-10-04T14:00:00Z", "sun": SUN, "state": "in_game", "lead": LEAD, "clock": SF_CLOCK, "ranks": RANKS}
    c.update(over)
    return c


def digest(browser, page_file, **over):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    drive(page, go("digest"))
    page.wait_for_selector(".dg")
    page.evaluate(PLANT, cfg(**over))
    return ctx, page, errors


def live(browser, page_file, **over):
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    page.evaluate(PLANT, cfg(**over))
    drive(page, go("live"))
    page.wait_for_selector(".gd-mirror .gd-mr")
    return ctx, page, errors


def personal_names(page):
    """Every league and team name the page holds (LIVE_GAMEDAY): none may reach the Digest."""
    names = page.evaluate("[...new Set(GD.leagues.flatMap(lg => [lg.name, ...Object.values(lg.teams).map(tm => tm.name)]))].filter(Boolean)")
    assert len(names) >= 10, names
    return names


def test_names_are_every_projected_8_plus_player_not_my_starters(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    names = page.evaluate("gdHurtNames()")
    mine = page.evaluate("GD.leagues.flatMap(lg => Object.values(lg.teams).flatMap(tm => tm.lineup.map(r => r.slug)))")
    ranked = page.evaluate("LIVE_RANKS.rows.map(r => [r.slug, r.pts, r.pos])")
    ctx.close()
    assert errors == []
    assert "tyler-huntley" not in mine                                # nobody of mine: he is watched all the same
    assert names["t.huntley"] == [{"slug": "tyler-huntley", "name": "Tyler Huntley", "team": "BAL"}]
    assert names["b.purdy"] == [{"slug": "brock-purdy", "name": "Brock Purdy", "team": "SF"}]
    assert names["a.st.brown"][0]["team"] == "DET"            # "A.St. Brown" in the play text
    assert "t.stukes" not in names                             # 5.0 projected: under the 8-point line
    # exactly the rankings' 8+ rows, which are QB/RB/WR/TE only: no defense, no kicker
    assert sorted(s for v in names.values() for s in [x["slug"] for x in v]) == sorted(s for s, p, _ in ranked if p >= 8)
    assert {pos for _, _, pos in ranked} <= {"QB", "RB", "WR", "TE"}


def test_hurt_starter_takes_the_headline_and_a_row_and_a_return_gives_it_back(browser, page_file):
    ctx, page, errors = digest(browser, page_file)
    assert page.locator(".dg-lead-h").inner_text() == "St. Brown ERUPTS: 10 catches, 180 yards, 2 TDs"
    rows = page.locator(".dg-now-r").count()
    page.evaluate("(h) => { GD_HURT = {[h.slug]: h}; paintDigestLive(); }", PURDY)
    assert page.locator(".dg-lead-h").inner_text() == "B. Purdy left the game hurt"
    assert page.locator(".dg-lead-fact").inner_text() == "SF · Q3 4:12"          # his club and the clock, no team of mine
    assert page.locator(".dg-lead").get_attribute("class").split()[1] == "out"
    # his own row leads Right now, in --down, and he is not in the five as well
    first = page.locator(".dg-now-r").first
    assert "hurt" in first.get_attribute("class") and "B. Purdy" in first.inner_text() and first.locator(".dg-now-p").text_content() == "Hurt"
    assert page.locator(".dg-now-r:not(.hurt)").count() == 5
    assert "Purdy" not in " ".join(page.locator(".dg-now-r:not(.hurt)").all_inner_texts())
    down = page.evaluate("(() => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.body).getPropertyValue('--down'); document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; })()")
    assert first.locator(".dg-now-p").evaluate("e => getComputedStyle(e).color") == down
    # a tap opens his profile, as every other row does
    first.click()
    assert "on" in page.locator("#modal").get_attribute("class")
    page.keyboard.press("Escape")
    # the band opens him too
    assert page.locator(".dg-lead-go").get_attribute("data-n") == "Brock Purdy"
    # he comes back: the top scorer is the headline again and the extra row is gone
    page.evaluate("(h) => { GD_HURT = {[h.slug]: {...h, back: true}}; paintDigestLive(); }", PURDY)
    assert page.locator(".dg-lead-h").inner_text() == "St. Brown ERUPTS: 10 catches, 180 yards, 2 TDs"
    assert page.locator(".dg-now-r.hurt").count() == 0 and page.locator(".dg-now-r").count() == rows
    ctx.close()
    assert errors == []


def test_with_several_hurt_the_best_projection_leads(browser, page_file):
    ctx, page, errors = digest(browser, page_file)
    page.evaluate("(hs) => { GD_HURT = Object.fromEntries(hs.map(h => [h.slug, h])); paintDigestLive(); }", [PURDY, ACHANE, HUNTLEY])
    order = page.evaluate("() => gdHurtNow().map(e => [e.slug, e.pts])")
    head = page.locator(".dg-lead-h").inner_text()
    rows = page.locator(".dg-now-r.hurt").all_inner_texts()
    ctx.close()
    assert errors == []
    assert order == [["devon-achane", 21.5], ["tyler-huntley", 19.9], ["brock-purdy", 18.1]]
    assert head == "D. Achane left the game hurt"
    assert len(rows) == 3 and "T. Huntley" in rows[1]              # Huntley is on nobody's team of mine, and a row all the same


def test_the_digest_names_no_league_or_team_of_mine_while_a_player_is_hurt(browser, page_file):
    """David, 2026-10-04: the Digest is generic for the public. The by-line is his club and the clock."""
    ctx, page, errors = digest(browser, page_file)
    names = personal_names(page)
    page.evaluate("(h) => { GD_HURT = {[h.slug]: h}; paintDigestLive(); }", ACHANE)
    fact = page.locator(".dg-lead-fact").inner_text()
    dg = page.evaluate("document.querySelector('.dg').outerHTML")
    ctx.close()
    assert errors == []
    assert fact == "MIA · Live"
    assert [n for n in names if n in dg] == []


def test_before_kickoff_nothing_changes(browser, page_file):
    ctx, page, errors = digest(browser, page_file, at="2026-10-04T08:00:00Z", state="pre_game", clock={})
    drawn = page.evaluate("document.querySelector('.dg').outerHTML")
    page.evaluate("(h) => { GD_HURT = {[h.slug]: h}; DG_CUT = null; render(); }", PURDY)
    assert page.evaluate("document.querySelector('.dg').outerHTML") == drawn
    assert page.locator(".dg-now-r.hurt").count() == 0
    ctx.close()
    assert errors == []


def test_between_games_the_banner_is_not_a_hurt_one(browser, page_file):
    """No game is on (every one final): GD_HURT is last Sunday's news and the top score keeps the banner."""
    ctx, page, errors = digest(browser, page_file, at="2026-10-04T23:30:00Z", state="complete", clock={})
    page.evaluate("(h) => { GD_HURT = {[h.slug]: h}; paintDigestLive(); }", PURDY)
    head = page.locator(".dg-lead-h").inner_text()
    ctx.close()
    assert errors == []
    assert "left the game hurt" not in head


def test_live_row_wears_a_hurt_chip_until_he_is_back(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    row = lambda: page.locator(".gd-mirror:not(.bn) .gd-mr", has=page.locator(".gd-h.l .gd-nb[data-gdn='Brock Purdy']"))
    assert row().count() == 1 and page.locator(".gd-hurt").count() == 0
    plain = page.evaluate("document.querySelector('.gd-mirror').innerHTML")
    page.evaluate("(h) => { GD_HURT = {[h.slug]: h}; paintLive(); }", PURDY)
    chip = row().locator(".gd-hurt")
    assert chip.count() == 1 and chip.inner_text().lower() == "hurt"
    assert chip.get_attribute("aria-label") == "Left the game hurt"
    assert page.locator(".gd-hurt").count() == 1
    # beside his name, inside the one name button, and the red is --down
    assert row().locator(".gd-nb .gd-nm .gd-hurt").count() == 1
    assert page.locator(".gd-mirror button button").count() == 0
    down = page.evaluate("(() => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.body).getPropertyValue('--down'); document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; })()")
    assert chip.evaluate("e => getComputedStyle(e).color") == down
    # a phone row stays one line of two
    assert row().evaluate("r => r.getBoundingClientRect().height") <= 52
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    # back in the game: the chip is cleared and the row is as it was
    page.evaluate("(h) => { GD_HURT = {[h.slug]: {...h, back: true}}; paintLive(); }", PURDY)
    assert page.locator(".gd-hurt").count() == 0
    assert page.evaluate("document.querySelector('.gd-mirror').innerHTML") == plain
    ctx.close()
    assert errors == []


def test_a_player_whose_game_has_not_started_draws_no_chip(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    # DET has not kicked off: a stale flag on St. Brown is not drawn
    page.evaluate("""() => { for (const c of gdCodes('DET')) GD_STATS.games[c] = 'pre_game'; GD_HURT = {'amonra-st-brown': {slug: 'amonra-st-brown', name: 'Amon-Ra St. Brown', team: 'DET', q: 1, clock: '', back: false}}; paintLive(); }""")
    assert page.locator(".gd-hurt").count() == 0
    ctx.close()
    assert errors == []


# ---------------------------------------------------------------- the poller

SERVED = "http://team-watch.test/"


def served(browser, page_file):
    """The page over http, so PAGE_SERVED() is true; every other request is refused."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    html = page_file.read_text(encoding="utf-8")
    page.route(re.compile(r"^http://team-watch\.test/?$"), lambda r: r.fulfill(status=200, content_type="text/html", body=html))
    page.route(re.compile(r"^https?://(?!team-watch\.test/?$)"), lambda r: r.abort())
    page.add_init_script(SEED)
    page.goto(SERVED)
    page.wait_for_function("document.getElementById('view').children.length > 0")
    return ctx, page, errors


STUB = """async (cfg) => {
  window.__calls = []; window.__open = 0; window.__max = 0;
  gsFetchSummary = async event => {
    window.__calls.push(event); window.__open++; window.__max = Math.max(window.__max, window.__open);
    await new Promise(r => setTimeout(r, 5));
    window.__open--;
    if (event === 'ENYG') throw new Error('ESPN is down');
    return window.__summary;
  };
  window.__summary = cfg.summary;
}"""


def test_the_poller_asks_every_live_game_one_at_a_time_every_three_minutes(browser, page_file):
    ctx, page, errors = served(browser, page_file)
    page.evaluate(PLANT, cfg(state="complete"))
    drive(page, go("live"))
    page.evaluate(STUB, {"summary": summary(["SF", "OSF"], [play("B.Purdy pass incomplete short middle to M.Evans. SF-B.Purdy was injured during the play.", 3, "5:00")])})
    page.evaluate("""() => {
      GD_STATS.games.SF = GD_STATS.games.NYG = 'in_game';              // two games with starters of mine; ESPN is down for NYG's
      GD_GAMES.push({home: 'ZZ', away: 'YY', kickoff: GD_GAMES[0].kickoff, week: 2, espn: 'EZZ'});
      GD_STATS.games.ZZ = GD_STATS.games.YY = 'in_game';              // a game none of my starters is in: asked all the same
    }""")
    page.evaluate("gdHurtPoll()")
    calls = page.evaluate("window.__calls")
    assert sorted(calls) == ["ENYG", "ESF", "EZZ"], calls                # every game that is on
    assert page.evaluate("window.__max") == 1                            # one request in flight at a time
    got = page.evaluate("GD_HURT")
    assert list(got) == ["brock-purdy"] and got["brock-purdy"]["back"] is False and got["brock-purdy"]["q"] == 3
    # inside the gap: nothing; a failed fetch (NYG) said nothing and left the last state
    page.evaluate("gdHurtPoll()")
    assert page.evaluate("window.__calls.length") == 3
    page.evaluate("() => { const t = Date.now() + 121000; Date.now = () => t; }")
    page.evaluate("gdHurtPoll()")
    assert page.evaluate("window.__calls.length") == 3                   # 121 s is not 180 s
    # 181 s after the first ask: all three again; the summary now says he is back, so the next paint clears him
    page.evaluate("""() => { const t = Date.now() + 60000; Date.now = () => t;
      window.__summary = {...window.__summary, drives: {previous: [{plays: [...window.__summary.drives.current.plays,
        {text: '** Injury Update: SF-B.Purdy has returned to the game.', period: {number: 3}, clock: {displayValue: '2:00'}}]}]}}; }""")
    page.evaluate("gdHurtPoll()")
    assert page.evaluate("window.__calls.length") == 6
    assert page.evaluate("GD_HURT['brock-purdy'].back") is True
    # no game is on any more: nothing is asked, whatever the clock says
    page.evaluate("""() => { for (const k of Object.keys(GD_STATS.games)) GD_STATS.games[k] = 'complete'; GD_CLOCK = {};
      const t = Date.now() + 600000; Date.now = () => t; }""")
    page.evaluate("gdHurtPoll()")
    assert page.evaluate("window.__calls.length") == 6
    ctx.close()
    assert errors == []


def test_from_a_file_it_never_asks(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate(PLANT, cfg(state="complete"))
    drive(page, go("live"))
    page.evaluate("GD_STATS.games.SF = 'in_game'")
    page.evaluate(STUB, {"summary": summary(["SF", "OSF"], [play("SF-B.Purdy was injured during the play.")])})
    assert page.evaluate("PAGE_SERVED()") is False
    page.evaluate("gdHurtPoll()")
    assert page.evaluate("window.__calls.length") == 0 and page.evaluate("GD_HURT") == {}
    ctx.close()
    assert errors == []


def test_a_view_that_does_not_show_live_numbers_never_asks(browser, page_file):
    ctx, page, errors = served(browser, page_file)
    page.evaluate(PLANT, cfg(state="complete"))
    drive(page, go("ranks"))
    page.evaluate("GD_STATS.games.SF = 'in_game'")
    page.evaluate(STUB, {"summary": summary(["SF", "OSF"], [play("SF-B.Purdy was injured during the play.")])})
    page.evaluate("gdHurtPoll()")
    assert page.evaluate("window.__calls.length") == 0
    ctx.close()
    assert errors == []

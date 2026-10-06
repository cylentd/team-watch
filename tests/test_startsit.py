"""Start/Sit's picker and matchup board (2026-10-03) and the best spot the board leads with
(design/startsit.py). The calls, record and last week are Start/Sit v3's: tests/test_startsit_v3.py."""
import json
import pathlib
import re
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "design"))
sys.path.insert(0, str(REPO / "api"))

from _espn import slugify  # noqa: E402
import contract  # noqa: E402
from sources import load_startsit  # noqa: E402
from startsit import live_startsit  # noqa: E402
from startsit_page import PRISTINE_JS, RESET_JS, open_view  # noqa: E402


def test_the_best_spots_are_the_only_thing_the_view_keeps_of_the_calls_file():
    """The matchup is a Ranks tag and the takes are v3's (2026-10-04); what stays is each position's
    best spot, for the board. The fixture's two: Gibbs (RB) and Kittle (TE)."""
    b = live_startsit(load_startsit(), slugify)
    contract.validate("LIVE_STARTSIT", b)
    assert sorted(b) == ["best", "generated", "week"]
    assert [(r["pos"], r["n"], r["slug"]) for r in b["best"]] == [("RB", "Jahmyr Gibbs", "jahmyr-gibbs"), ("TE", "George Kittle", "george-kittle")]
    assert b["best"][0]["home"] in (True, False) and b["best"][0]["why"]


def test_no_calls_file_is_no_block():
    assert live_startsit(None, slugify) is None
    assert live_startsit({"week": 3}, slugify) is None
    contract.validate("LIVE_STARTSIT", None)


# ---- Start / Sit (2026-10-03): the picker, the matchup board, the #startsit hash ----
# LIVE_SSB is another unit's block (design/startsit_board.py); these tests fill it through the page, so
# the view is proved on its own. The fixture's LIVE_RANKS holds five players, so a test that needs more
# of one position clones the first (picks_js).

BOARD = {"QB": ("DAL", "NYG"), "RB": ("CIN", "PIT"), "WR": ("DET", "CHI"), "TE": ("KC", "LV")}
CLEAR_SSB = """
      if (typeof LIVE_SSB === 'object' && LIVE_SSB) { for (const k of Object.keys(LIVE_SSB)) delete LIVE_SSB[k]; }"""


def _board():
    def row(team, opp, pts, rank):
        return {"team": team, "opp": opp, "pts": pts, "rank": rank}
    return {pos: {"avg": 18.9, "n": 3,
                  "best": [row(t, o, 26.1, 32), row("SF", "MIA", 24.0, 31), row("KC", "LV", 23.2, 30), row("BUF", "NE", 22.5, 29)],
                  "worst": [row("NYG", "SF", 12.4, 1), row("LV", "BUF", 13.0, 2), row("PIT", "CIN", 13.8, 3), row("CHI", "DET", 14.2, 4)]}
            for pos, (t, o) in BOARD.items()}


def picks_js(*pts, pos="QB"):
    """Pick len(pts) LIVE_RANKS players at `pos` with exactly these projections, cloning when short."""
    return f"""
      const rows = LIVE_RANKS.rows.filter(r => r.pos === '{pos}');
      while (rows.length < {len(pts)}) {{
        const c = Object.assign({{}}, rows[0], {{slug: 'test-{pos.lower()}-' + rows.length, n: 'Test Player ' + rows.length}});
        LIVE_RANKS.rows.push(c); rows.push(c);
      }}
      {json.dumps(list(pts))}.forEach((p, i) => {{
        rows[i].pts = p;
        LIVE_PROJECTIONS.players[rows[i].slug] = Object.assign(LIVE_PROJECTIONS.players[rows[i].slug] || {{}}, {{pts: p}});
      }});
      SS_PICKS = rows.slice(0, {len(pts)}).map(r => r.slug); SS_OPEN = false; SS_Q = ''; SS_BTAB = '';"""


def ssb_js():
    """Fill LIVE_SSB for the picks: the board, FantasyPros ranks, a teammate out for the first pick."""
    return """
      const pos = LIVE_RANKS.rows.find(r => r.slug === SS_PICKS[0]).pos;
      const stub = {week: LIVE_RANKS.week, board: %s,
        fp: {[SS_PICKS[0]]: {ecr: 14, pos}, [SS_PICKS[1]]: {ecr: 21, pos}},
        out: {[SS_PICKS[0]]: [{n: 'Jalen Coker', pos: 'WR', s: 'Out'}]}};
      if (typeof LIVE_SSB === 'object' && LIVE_SSB) { for (const k of Object.keys(LIVE_SSB)) delete LIVE_SSB[k]; Object.assign(LIVE_SSB, stub); }
      else window.LIVE_SSB = stub;""" % json.dumps(_board())


@pytest.fixture(scope="module")
def shared(browser, page_file):
    """One page for the module: ss() resets it, so a test never sees another's changes."""
    errors = []
    ctx, pg = open_view(browser, page_file, errors=errors)
    pg.evaluate(PRISTINE_JS)
    assert errors == []                 # whatever the load or the snapshot raised fails here, not lost to a clear
    yield pg, errors
    ctx.close()


@pytest.fixture
def ss(browser, page_file, shared):
    """ss(js) resets the shared page and applies js. A hash_ opens a fresh page, because the hash on load
    is what that test proves. Any page error or console error during the test fails it."""
    pg, errors = shared
    left, errors[:] = list(errors), []  # an error raised or left over since the last test fails this one
    assert left == []
    made = []

    def go(js="", w=360, h=800, hash_=None):
        if hash_ is not None:
            ctx, fresh = open_view(browser, page_file, js, w=w, h=h, hash_=hash_, errors=errors)
            made.append(ctx)
            return fresh
        pg.set_viewport_size({"width": w, "height": h})
        pg.evaluate(RESET_JS)
        if js:
            pg.evaluate("() => {" + js + "; render(); }")
        return pg
    yield go
    for c in made:
        c.close()
    assert errors == [], errors


def verdict(pg):
    return pg.evaluate("""() => { const v = document.querySelector('.ssv-verdict'); return v && {
        tag: v.querySelector('.mu-tag') && v.querySelector('.mu-tag').textContent,
        name: v.querySelector('b') && v.querySelector('b').textContent,
        gain: v.querySelector('.ssv-gain') && v.querySelector('.ssv-gain').textContent,
        flip: v.querySelector('.ssv-coin') && v.querySelector('.ssv-coin').textContent}; }""")


@pytest.mark.render
def test_the_higher_projection_starts_and_names_the_margin(ss):
    pg = ss(picks_js(12.0, 9.0))
    top = pg.evaluate("shortName(ssCols()[0].p.n)")
    assert verdict(pg) == {"tag": "START", "name": top, "gain": "+3.0", "flip": None}
    assert pg.locator(".ssv-who").count() == 2


@pytest.mark.render
def test_inside_half_a_point_is_a_coin_flip_with_no_start(ss):
    for pts in [(10.0, 9.6), (10.5, 10.0)]:                      # 0.4 and exactly 0.5
        pg = ss(picks_js(*pts))
        assert verdict(pg) == {"tag": None, "name": None, "gain": None, "flip": "Coin flip"}
        assert pg.locator(".ssv-verdict .mu-tag").count() == 0
    # a tenth past the line starts someone, whichever order the two were picked in
    pg = ss(picks_js(9.0, 9.6))
    v = verdict(pg)
    assert v["tag"] == "START" and v["gain"] == "+0.6"
    assert v["name"] == pg.evaluate("shortName(ssCols()[1].p.n)")


@pytest.mark.render
def test_the_verdict_judges_the_margin_as_shown_to_one_decimal(ss):
    """0.54 shows as 0.5, which is a coin flip (never a START at "+0.5"); 0.56 shows as 0.6, a START."""
    pg = ss(picks_js(10.0, 9.46))
    assert verdict(pg)["flip"] == "Coin flip" and pg.locator(".ssv-verdict .mu-tag").count() == 0
    pg = ss(picks_js(10.0, 9.44))
    assert verdict(pg)["tag"] == "START" and verdict(pg)["gain"] == "+0.6"
    pg = ss(picks_js(9.0, 9.56))
    v = verdict(pg)
    assert v["tag"] == "START" and v["gain"] == "+0.6"


@pytest.mark.render
def test_focus_lands_on_the_search_box_then_back_on_a_control(ss):
    pg = ss(ROSTER_JS % (17.0, 17.0))
    pg.click("[data-ssadd]")
    assert pg.evaluate("document.activeElement.id") == "ssv-q"
    pg.keyboard.press("Escape")
    assert pg.evaluate("document.activeElement.hasAttribute('data-ssadd')")
    # the third pick removes the Add button, so the first Remove takes focus (never the page body)
    pg.click("[data-ssadd]")
    pg.fill("#ssv-q", "Gibbs")
    pg.locator(".ssv-opt").first.click()
    assert pg.locator("[data-ssadd]").count() == 0
    assert pg.evaluate("document.activeElement.classList.contains('ssv-x')")


@pytest.mark.render
def test_one_player_or_none_is_a_prompt_not_a_verdict(ss):
    pg = ss(picks_js(11.0))
    assert pg.locator(".ssv-verdict").count() == 0
    assert pg.inner_text(".ssv-prompt") == "Add one more to see who starts."
    pg = ss("SS_PICKS = [];")
    assert pg.inner_text(".ssv-prompt") == "Pick two players to see who starts."
    assert pg.locator(".ssv-who, .ssv-row").count() == 0
    assert pg.locator("[data-ssadd]").count() == 1


@pytest.mark.render
def test_the_wr_note_rides_on_the_defense_row_only_when_a_wr_is_picked(ss):
    pg = ss(picks_js(12.0, 9.0, pos="WR"))
    row = pg.locator(".ssv-row", has=pg.locator(".ssv-lbl", has_text="Defense vs WR"))
    assert row.locator(".ssv-lbl em").inner_text() == "matters little for WRs"
    # a mixed pair names no one position, and still says it for the receiver
    pg = ss(picks_js(12.0, 9.0) + "; SS_PICKS[1] = 'amonra-st-brown'")
    assert pg.locator(".ssv-lbl span", has_text="Defense").text_content() == "Defense"
    # (the Projected row has its own note about the range, plan U5: the WR note is the defense row's)
    assert pg.locator(".ssv-row", has=pg.locator(".ssv-lbl", has_text="Defense")).locator(".ssv-lbl em").inner_text() == "matters little for WRs"
    for pos in ("QB", "RB"):
        pg = ss(picks_js(12.0, 9.0, pos=pos))
        assert pg.locator(".ssv-lbl", has_text=f"Defense vs {pos}").count() == 1
        assert pg.locator(".ssv-row", has=pg.locator(".ssv-lbl", has_text="Defense")).locator(".ssv-lbl em").count() == 0


@pytest.mark.render
def test_rows_read_the_blocks_and_drop_when_nobody_has_data(ss):
    pg = ss(picks_js(12.0, 9.0) + ssb_js() + """
      LIVE_PROJECTIONS.players[SS_PICKS[0]].wx = {adj: -1.06, cond: ['wind', 'precip']};
      LIVE_PROJECTIONS.players[SS_PICKS[1]].wx = null;""")
    rows = pg.evaluate("""() => Object.fromEntries([...document.querySelectorAll('.ssv-row')].map(r =>
        [r.querySelector('.ssv-lbl span').textContent, [...r.querySelectorAll('.ssv-v')].map(v => v.textContent)]))""")
    assert list(rows) == ["Projected", "Rank", "Defense vs QB", "FantasyPros", "Teammate out", "Weather", "Usage"]
    # the number, then its floor-ceiling (plan U5) in the same lane
    assert [re.match(r"\d+\.\d", v).group() for v in rows["Projected"]] == ["12.0", "9.0"]
    assert all("–" in v for v in rows["Projected"])
    assert rows["FantasyPros"] == ["QB14", "QB21"]
    assert rows["Teammate out"] == ["J. CokerWR · Out", "—"]
    assert rows["Weather"] == ["−1.1wind · rain", "—"]
    # with no block and no weather, FantasyPros, Teammate out and Weather are not drawn
    pg = ss(picks_js(12.0, 9.0) + CLEAR_SSB + "; for (const s of SS_PICKS) LIVE_PROJECTIONS.players[s].wx = null;")
    assert pg.evaluate("[...document.querySelectorAll('.ssv-lbl span')].map(e => e.textContent)") == [
        "Projected", "Rank", "Defense vs QB", "Usage"]


@pytest.mark.render
def test_the_defense_row_says_softest_or_toughest_with_the_opponent(ss):
    pg = ss(picks_js(12.0, 9.0))
    cells = pg.evaluate("""() => [...[...document.querySelectorAll('.ssv-row')].find(r => r.textContent.startsWith('Defense'))
        .querySelectorAll('.ssv-v')].map(v => v.textContent)""")
    assert len(cells) == 2
    for c in cells:
        assert re.search(r"(softest|toughest)(vs|@) [A-Z]+$", c) or re.match(r"—(vs|@) [A-Z]+$", c), c


@pytest.mark.render
def test_the_board_tabs_switch_position_in_place(ss):
    pg = ss(picks_js(12.0, 9.0) + ssb_js())
    assert pg.evaluate("[...document.querySelectorAll('[data-ssbpos]')].map(b => b.textContent)") == ["QB", "RB", "WR", "TE"]
    assert pg.locator(".ssv-board h3").text_content().startswith("QB matchups")          # opens on the first pick's position
    assert pg.locator("[data-ssbpos='QB']").get_attribute("aria-pressed") == "true"
    first = lambda: pg.evaluate("""() => [...document.querySelectorAll('.ssv-bl')].map(l =>
        [l.querySelector('h4').firstChild.textContent, l.querySelectorAll('.ssv-br').length, l.querySelector('.ssv-bt').textContent,
         l.querySelector('.ssv-bo').textContent, l.querySelector('em').textContent])""")
    assert first() == [["Best matchups", 4, "DAL", "vs NYG", "26.1"], ["Worst matchups", 4, "NYG", "vs SF", "12.4"]]
    pg.evaluate("window.__takes = document.querySelector('.mu-calls')")
    pg.click("[data-ssbpos='RB']")
    assert pg.locator(".ssv-board h3").text_content().startswith("RB matchups")
    assert pg.locator("[data-ssbpos='RB']").get_attribute("aria-pressed") == "true"
    assert first()[0][2:4] == ["CIN", "vs PIT"]
    assert pg.evaluate("window.__takes === document.querySelector('.mu-calls')")   # the calls were not redrawn
    assert pg.inner_text(".ssv-key").strip() == "League average 18.9"


SPOT_JS = """; LIVE_STARTSIT.best = [{n: 'Stefon Diggs', slug: 'stefon-diggs', pos: 'WR', team: 'WAS', opp: 'IND', home: true,
    pts: 9.6, why: ['24% target share']}];
  LIVE_SSB.out['stefon-diggs'] = [{n: 'Terry McLaurin', pos: 'WR', s: 'Out'}]; SS_BTAB = 'WR'"""


@pytest.mark.render
def test_the_board_names_the_best_spot_with_its_teammate_out(ss):
    # The Digest's Matchups card, back on Start / Sit (2026-10-03, David: "Diggs is a good start because Terry is out")
    pg = ss(picks_js(12.0, 9.0) + ssb_js() + SPOT_JS)
    spot = pg.locator(".ssv-board .ssv-spot")
    assert spot.locator(".mu-nm b").text_content() == "S. Diggs"
    meta = spot.locator(".mu-nm span").text_content()
    assert "24% target share" in meta and "T. McLaurin Out" in meta
    assert spot.locator("em").text_content() == "9.6"
    pg.click("[data-ssbpos='QB']")                                   # no best spot at QB: no row
    assert pg.locator(".ssv-spot").count() == 0
    assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.render
def test_a_board_row_has_a_bar_against_the_league_average(ss):
    pg = ss(picks_js(12.0, 9.0) + ssb_js())
    got = pg.evaluate("""() => { const b = document.querySelector('.ssv-bar'), r = b.getBoundingClientRect();
      const tick = getComputedStyle(b, '::after');
      return {fill: b.querySelector('i').getBoundingClientRect().width / r.width, avg: parseFloat(tick.left) / r.width}; }""")
    assert got["fill"] == pytest.approx(1.0, abs=0.01)          # the largest value fills its bar
    assert got["avg"] == pytest.approx(18.9 / 26.1, abs=0.01)   # the tick is the average on the same scale


@pytest.mark.render
def test_a_missing_block_draws_no_board_and_no_error(ss):
    pg = ss(picks_js(12.0, 9.0) + CLEAR_SSB)
    assert pg.locator(".ssv-board").count() == 0 and pg.locator(".ssv-pick").count() == 1
    pg = ss(picks_js(12.0, 9.0) + ssb_js() + "; LIVE_SSB.board.TE = null; LIVE_SSB.board.QB = {avg: 'x'};")
    assert pg.evaluate("[...document.querySelectorAll('[data-ssbpos]')].map(b => b.textContent)") == ["RB", "WR"]
    assert pg.locator(".ssv-board h3").text_content().startswith("RB matchups")          # the first pick's tab is gone


@pytest.mark.render
def test_startsit_hash_opens_the_view_under_its_new_name(ss):
    pg = ss(hash_="#startsit")
    assert pg.locator(".ssv-pick").count() == 1 and pg.locator(".mu-rec").count() == 1
    assert pg.evaluate("SURFACE") == "matchups"
    assert pg.inner_text(".mode-sub[aria-pressed='true']") == "Start/Sit"
    for old in ("#takes", "#matchups"):                                  # the old names still land
        assert ss(hash_=old).evaluate("SURFACE") == "matchups"


ROSTER_JS = """
      TEAMS.yahoo.roster = [P('Joe Burrow', 'QB', 'CIN', 'joe-burrow', {slot: 'QB', start: 1}),
        P('Chase Brown', 'RB', 'CIN', 'chase-brown', {slot: 'RB1', start: 1}),
        P('Brock Purdy', 'QB', 'SF', 'brock-purdy', {slot: 'BN'}), P('Test Back', 'RB', 'CIN', 'test-back', {slot: 'BN'})];
      LIVE_RANKS.rows.push({slug: 'test-back', n: 'Test Back', pos: 'RB', team: 'CIN', opp: 'NYJ', home: false, pts: %s, rank: 2});
      LIVE_PROJECTIONS.players['test-back'] = {pts: %s};
      SS_PICKS = null; try { localStorage.removeItem('tw-ss-picks'); } catch (e) {}"""


@pytest.mark.render
def test_it_opens_on_the_closest_call_the_roster_brief_names(ss):
    # the bench RB out-projects his starter by 0.8: that swap, bench player first, beats Purdy's 1.3 deficit
    pg = ss(ROSTER_JS % (17.0, 17.0))
    assert pg.evaluate("[...document.querySelectorAll('[data-ssx]')].map(b => b.dataset.ssx)") == ["test-back", "chase-brown"]
    # nobody on the bench gains on a starter: the smallest gap is the pair, bench first
    pg = ss(ROSTER_JS % (9.0, 9.0))
    assert pg.evaluate("[...document.querySelectorAll('[data-ssx]')].map(b => b.dataset.ssx)") == ["brock-purdy", "joe-burrow"]
    assert verdict(pg)["name"] == "J. Burrow"
    # a reader who kept picks gets them back, and one who cleared them keeps an empty card
    pg = ss(ROSTER_JS % (9.0, 9.0) + "; SS_PICKS = null; localStorage.setItem('tw-ss-picks', JSON.stringify({week: slateWeek(), picks: []}))")
    assert pg.locator(".ssv-who").count() == 0
    # last week's picks are dropped: the card opens on this week's closest call
    pg = ss(ROSTER_JS % (9.0, 9.0) + "; SS_PICKS = null; localStorage.setItem('tw-ss-picks', JSON.stringify({week: slateWeek() - 1, picks: []}))")
    assert pg.evaluate("[...document.querySelectorAll('[data-ssx]')].map(b => b.dataset.ssx)") == ["brock-purdy", "joe-burrow"]


NO_TEAM_JS = "TEAMS[VIEW].roster = []; SS_PICKS = null; SS_OPEN = false; try { localStorage.removeItem('tw-ss-picks'); } catch (e) {}"


@pytest.mark.render
def test_a_reader_with_no_team_opens_on_an_empty_card_with_the_search_open_and_focused(ss):
    """Plan U3 (2026-10-05): the first-time visitor was handed a pair he never chose (8 taps to his own).
    ssTeam is the team he picked; with none the card is empty and the cursor is already in the search."""
    pg = ss(NO_TEAM_JS)
    assert pg.locator(".ssv-who").count() == 0 and pg.locator("#ssv-box").count() == 1
    assert pg.evaluate("document.activeElement.id") == "ssv-q"
    assert pg.inner_text(".ssv-prompt") == "Pick two players to see who starts."


@pytest.mark.render
def test_the_search_stays_open_until_there_are_two_and_the_first_tap_is_a_name(ss):
    pg = ss(NO_TEAM_JS)
    pg.fill("#ssv-q", "Gibbs")
    pg.locator(".ssv-opt").first.click()                             # tap 1: a name
    assert pg.locator(".ssv-who").count() == 1 and pg.locator("#ssv-box").count() == 1
    assert pg.evaluate("document.activeElement.id") == "ssv-q"      # the cursor is back in it for the second
    assert pg.inner_text(".ssv-prompt") == "Add one more to see who starts."
    pg.fill("#ssv-q", "Chase Brown")
    pg.locator(".ssv-opt").first.click()                             # tap 2: the other
    assert pg.locator(".ssv-who").count() == 2 and pg.locator("#ssv-box").count() == 0
    assert pg.locator(".ssv-prompt").count() == 0                    # two is a comparison: no prompt left


@pytest.mark.render
def test_fantasypros_ranking_the_loser_ahead_says_why_the_call_differs(ss):
    """Plan U3: the FantasyPros row used to contradict our START with no word. It says whose rank it is."""
    pg = ss(picks_js(12.0, 9.0) + ssb_js())                          # ours: first starts; theirs: ECR 14 vs 21, agrees
    assert pg.locator(".ssv-lbl em", has_text="ahead of").count() == 0
    pg = ss(picks_js(12.0, 9.0) + ssb_js() + "; LIVE_SSB.fp[SS_PICKS[0]].ecr = 30")   # now FantasyPros has the second ahead
    note = pg.locator(".ssv-row", has=pg.locator(".ssv-lbl", has_text="FantasyPros")).locator(".ssv-lbl em").inner_text()
    first, second = pg.evaluate("ssCols().map(c => shortName(c.p.n))")
    assert note == f"FantasyPros' experts rank {second} ahead of {first}. Our call is the projection, not expert opinion."
    assert verdict(pg)["tag"] == "START"                             # the call itself is untouched
    pg = ss(picks_js(10.0, 9.8) + ssb_js() + "; LIVE_SSB.fp[SS_PICKS[0]].ecr = 30")   # a coin flip has no call to contradict
    assert pg.locator(".ssv-lbl em", has_text="ahead of").count() == 0


@pytest.mark.render
def test_a_players_lane_links_to_his_row_in_the_usage_grid(ss):
    pg = ss(picks_js(12.0, 9.0) + ssb_js())
    slug = pg.evaluate("SS_PICKS[0]")
    link = pg.locator(f".ssv-go[data-ssgrid='{slug}']")
    assert link.count() == 1 and link.inner_text() == "Open row"
    assert link.bounding_box()["height"] >= 44
    link.click()
    assert pg.evaluate("SURFACE") == "usage"
    assert pg.evaluate(f"!!document.querySelector('[data-usage=\"{slug}\"].nav-hit')")


@pytest.mark.render
def test_the_picker_and_board_lead_and_the_calls_stay_under_them(ss):
    pg = ss()
    assert pg.evaluate("""() => { const q = s => document.querySelector(s);
      return [!!(q('.ssv').compareDocumentPosition(q('.mu-rec')) & 4), !!(q('.ssv').compareDocumentPosition(q('.mu-calls')) & 4)]; }""") == [True, True]
    assert pg.locator(".mu-calls [data-mukey^='t:']").count() == 9


@pytest.mark.render
def test_add_by_search_and_remove_keep_the_picks(ss):
    pg = ss(ROSTER_JS % (17.0, 17.0))                      # two picks: Test Back and Chase Brown
    pg.click("[data-ssadd]")
    assert pg.locator("#ssv-box").count() == 1 and pg.locator("[data-ssadd]").get_attribute("aria-expanded") == "true"
    # his roster at the first pick's position comes first, and neither pick is offered again
    assert pg.evaluate("[...document.querySelectorAll('.ssv-opt')].map(b => b.dataset.ssslug)") == []
    assert pg.inner_text(".ssv-none") == "Search for a player to add."
    pg.click("[data-ssx='test-back']")                     # one pick left: the other roster RB is offered, list still open
    assert pg.locator(".ssv-cap").text_content() == "Chat Take the Wheel · RB"
    assert pg.evaluate("[...document.querySelectorAll('.ssv-opt')].map(b => b.dataset.ssslug)") == ["test-back"]
    pg.click(".ssv-opt")                                   # a roster tap adds him and closes the list
    assert pg.locator("#ssv-box").count() == 0 and pg.locator(".ssv-who").count() == 2
    pg.click("[data-ssadd]")
    slug = pg.evaluate("searchFind('Gibbs', 8)[0].e.slug")
    pg.fill("#ssv-q", "Gibbs")
    pg.locator(f".ssv-opt[data-ssslug='{slug}']").click()
    assert pg.evaluate("[...document.querySelectorAll('[data-ssx]')].map(b => b.dataset.ssx)") == ["chase-brown", "test-back", slug]
    assert pg.locator("#ssv-box").count() == 0 and pg.locator("[data-ssadd]").count() == 0   # three is the most
    assert pg.evaluate("JSON.parse(localStorage.getItem('tw-ss-picks')).picks") == ["chase-brown", "test-back", slug]
    pg.click(f"[data-ssx='{slug}']")
    assert pg.locator(".ssv-who").count() == 2 and pg.locator("[data-ssadd]").count() == 1
    assert pg.evaluate("JSON.parse(localStorage.getItem('tw-ss-picks')).picks") == ["chase-brown", "test-back"]
    pg.click("[data-ssadd]")
    pg.keyboard.press("Escape")
    assert pg.locator("#ssv-box").count() == 0


@pytest.mark.render
def test_nothing_scrolls_sideways_at_360_with_three_players_and_every_row(ss):
    pg = ss(picks_js(12.0, 9.0, 8.0) + ssb_js() + """
      LIVE_PROJECTIONS.players[SS_PICKS[0]].wx = {adj: -1.06, cond: ['wind', 'precip']};
      LIVE_SSB.out[SS_PICKS[1]] = [{n: 'Jalen Coker', pos: 'WR', s: 'Out'}, {n: 'Tetairoa McMillan', pos: 'WR', s: 'Doubtful'}];""")
    assert pg.locator(".ssv-who").count() == 3
    assert pg.evaluate("document.documentElement.scrollWidth") <= 360
    pg.click("[data-ssbpos='TE']")
    assert pg.evaluate("document.documentElement.scrollWidth") <= 360
    pg.evaluate("SS_PICKS.pop(); SS_OPEN = true; render()")
    assert pg.evaluate("document.documentElement.scrollWidth") <= 360


@pytest.mark.render
def test_desktop_puts_the_picker_and_board_side_by_side_on_shared_edges(ss):
    pg = ss(picks_js(12.0, 9.0) + ssb_js(), w=1400, h=900)
    box = pg.evaluate("""() => ['.ssv-pick', '.ssv-board'].map(s => { const r = document.querySelector(s).getBoundingClientRect();
        return [Math.round(r.top), Math.round(r.bottom), Math.round(r.left)]; })""")
    assert box[0][0] == box[1][0] and box[0][1] == box[1][1] and box[0][2] < box[1][2]
    lists = pg.evaluate("[...document.querySelectorAll('.ssv-bl')].map(l => Math.round(l.getBoundingClientRect().left))")
    assert len(set(lists)) == 2                                   # Best and Worst side by side in a half-width card

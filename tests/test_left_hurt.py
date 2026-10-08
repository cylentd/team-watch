"""Left the game hurt (2026-10-04): the Digest's headline and Live's chip.

David: "the headline should change when something big happens, like an injury." Sleeper and the
scoreboard say nothing about an injury mid-game; the play-by-play does. nflverse's text (games/*.json)
reads "PHI-S.Barkley was injured during the play." and "** Injury Update: PHI-J.Hurts has returned to
the game." ESPN's summary is BELIEVED to carry the same text; UNVERIFIED until Monday's game (2026-10-05,
ATL @ NO), so the scan is pinned against the nflverse wording and nothing else (test_js_hurt.py).

League-wide since the same evening (David: "The Digest is supposed to be GENERIC for the public. It
shouldn't hone on to my roster or their roster."): the players to watch are every QB/RB/WR/TE that
LIVE_RANKS projects at 8 points or more, every live game is scanned, and nothing drawn names a league or a
team of mine. The first version watched my starters only (8b91604) and is superseded.

The scan (data/gameday/hurt.js gdHurtScan) is pure and is tested in Node (test_js_hurt.py, since
2026-10-05); so are who the players to watch are and the order of who is hurt (here, 2026-10-06). This file
is what the page draws: component tests (the Digest and Live mounted, tests/component.py; every locator in
tests/pages/hurt.py, which composes the Digest's and Live's page objects). The tests plant GD_HURT, since
ESPN refuses servers and headless browsers and the poller cannot be fed from a test's network. The two that
run the poller need the page over http (PAGE_SERVED), which a mounted page, a file, is not: they stay
journeys on the whole page."""
import json
import pathlib
import re

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.hurt import RANKS, HurtPage, served
from test_js_hurt import play, summary
from wording import words

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"

PURDY = {"slug": "brock-purdy", "name": "Brock Purdy", "team": "SF", "q": 3, "clock": "5:00", "back": False}
ACHANE = {"slug": "devon-achane", "name": "De'Von Achane", "team": "MIA", "q": 3, "clock": "6:00", "back": False}
HUNTLEY = {"slug": "tyler-huntley", "name": "Tyler Huntley", "team": "BAL", "q": 2, "clock": "1:00", "back": False}


# ESPN's summary for a game, as the stub of gsFetchSummary hands it back; ENYG is down. It takes 5 ms, so two
# requests could overlap: that latency is what lets the test see one at a time.
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


@pytest.fixture(scope="module")
def ranks(built):
    """The rows the page holds once the game day is planted: the build's own LIVE_RANKS (the fixture's), then RANKS' that
    are not in it, as the page's plant adds them."""
    rows = json.loads(re.search(r"const LIVE_RANKS = (.*?);\n", built.fragment).group(1))["rows"]
    return rows + [r for r in RANKS if not any(x["slug"] == r["slug"] for x in rows)]


@pytest.fixture(scope="module")
def ranked(node_js, ranks):
    """hurt.js with those rankings: who is watched, and who is hurt now."""
    return node_js("data/gameday/hurt.js", globals={"LIVE_RANKS": {"rows": ranks}})


# ---------------------------------------------------------------- the logic, in Node

def test_names_are_every_projected_8_plus_player_not_my_starters(ranked, ranks):
    names = ranked("gdHurtNames")
    fix = json.loads((FIXTURES / "gameday.json").read_text(encoding="utf-8"))
    mine = [r["slug"] for lg in (fix["espn"], fix["yahoo"]) for tm in lg["teams"].values() for r in tm["lineup"]]
    ranked_rows = [[r["slug"], r["pts"], r["pos"]] for r in ranks]
    assert "tyler-huntley" not in mine                                # nobody of mine: he is watched all the same
    assert names["t.huntley"] == [{"slug": "tyler-huntley", "name": "Tyler Huntley", "team": "BAL"}]
    assert names["b.purdy"] == [{"slug": "brock-purdy", "name": "Brock Purdy", "team": "SF"}]
    assert names["a.st.brown"][0]["team"] == "DET"        # "A.St. Brown" in the play text
    assert "t.stukes" not in names                             # 5.0 projected: under the 8-point line
    # exactly the rankings' 8+ rows, which are QB/RB/WR/TE only: no defense, no kicker
    assert sorted(s for v in names.values() for s in [x["slug"] for x in v]) == sorted(s for s, p, _ in ranked_rows if p >= 8)
    assert {pos for _, _, pos in ranked_rows} <= {"QB", "RB", "WR", "TE"}


# ---------------------------------------------------------------- the Digest

@pytest.mark.render
def test_hurt_starter_takes_the_headline_and_a_row_and_a_return_gives_it_back(mount):
    hurt, errors = HurtPage.on_digest(mount)
    digest = hurt.digest
    assert digest.headline() == "St. Brown ERUPTS: 10 catches, 180 yards, 2 TDs"
    rows = digest.now_rows()
    hurt.leave_hurt(PURDY)
    assert digest.headline() == "B. Purdy left the game hurt"
    assert digest.lead_fact() == "SF · Q3 4:12"          # his club and the clock, no team of mine
    assert hurt.lead_tone() == "out"
    # his own row leads Right now, in --down, and he is not in the five as well
    first = hurt.first_now_row()
    assert "hurt" in first["cls"] and "B. Purdy" in first["text"] and first["pill"] == "Hurt"
    assert digest.now_rows() == 3 and hurt.plain_now_row_count() == 2   # three rows, he is one
    digest.tap_now_more()
    assert hurt.plain_now_row_count() == 5
    assert "Purdy" not in " ".join(hurt.plain_now_row_texts())
    assert hurt.first_now_pill_colour() == hurt.down_colour()
    # a tap opens his profile, as every other row does
    hurt.tap_first_now_row()
    assert digest.profile_open()
    digest.close_profile()
    # the band opens him too
    assert hurt.lead_name() == "Brock Purdy"
    # he comes back: the top scorer is the headline again and the extra row is gone
    hurt.return_to_game(PURDY)
    assert digest.headline() == "St. Brown ERUPTS: 10 catches, 180 yards, 2 TDs"
    assert hurt.hurt_now_row_count() == 0 and digest.now_rows() == 5   # More stays open until it is closed
    digest.tap_now_more()
    assert digest.now_rows() == rows == 3
    assert errors == []


@pytest.mark.render
def test_with_several_hurt_the_best_projection_leads(mount, ranked):
    hurt, errors = HurtPage.on_digest(mount)
    hurt.leave_hurt(PURDY, ACHANE, HUNTLEY)
    order = ranked("(hs) => { GD_HURT = Object.fromEntries(hs.map(h => [h.slug, h])); return gdHurtNow().map(e => [e.slug, e.pts]); }",
                   [PURDY, ACHANE, HUNTLEY])
    head = hurt.digest.headline()
    rows = hurt.hurt_now_row_texts()
    assert errors == []
    assert order == [["devon-achane", 21.5], ["tyler-huntley", 19.9], ["brock-purdy", 18.1]]
    assert head == "D. Achane left the game hurt"
    assert len(rows) == 3 and "T. Huntley" in rows[1]              # Huntley is on nobody's team of mine, and a row all the same


@pytest.mark.render
def test_the_digest_names_no_league_or_team_of_mine_while_a_player_is_hurt(mount):
    """David, 2026-10-04: the Digest is generic for the public. The by-line is his club and the clock."""
    hurt, errors = HurtPage.on_digest(mount)
    names = hurt.personal_names()
    assert len(names) >= 10, names
    hurt.leave_hurt(ACHANE)
    fact = hurt.digest.lead_fact()
    dg = hurt.digest.html()
    assert errors == []
    assert fact == "MIA · Live"
    assert [n for n in names if n in dg] == []


@pytest.mark.render
def test_before_kickoff_nothing_changes(mount):
    hurt, errors = HurtPage.on_digest(mount, at="2026-10-04T08:00:00Z", state="pre_game", clock={})
    drawn = hurt.digest.html()
    hurt.leave_hurt_and_render(PURDY)
    assert hurt.digest.html() == drawn
    assert hurt.hurt_now_row_count() == 0
    assert errors == []


@pytest.mark.render
def test_between_games_the_banner_is_not_a_hurt_one(mount):
    """No game is on (every one final): GD_HURT is last Sunday's news and the top score keeps the banner."""
    hurt, errors = HurtPage.on_digest(mount, at="2026-10-04T23:30:00Z", state="complete", clock={})
    hurt.leave_hurt(PURDY)
    head = hurt.digest.headline()
    assert errors == []
    assert "left the game hurt" not in head


# ---------------------------------------------------------------- Live

@pytest.mark.render
def test_live_row_wears_a_hurt_chip_until_he_is_back(mount):
    hurt, errors = HurtPage.on_live(mount)
    assert hurt.purdy_rows() == 1 and hurt.chip_count() == 0
    plain = hurt.lineups_html()
    hurt.leave_hurt_on_live(PURDY)
    assert hurt.purdy_chip_count() == 1 and hurt.purdy_chip_text().lower() == "hurt"
    assert hurt.purdy_chip_label() == words("live.hurt.label")
    assert hurt.chip_count() == 1
    # beside his name, inside the one name button, and the red is --down
    assert hurt.purdy_chip_in_name_count() == 1
    assert hurt.live.nested_buttons() == 0
    assert hurt.purdy_chip_colour() == hurt.down_colour()
    # a phone row stays one line of two
    assert hurt.purdy_row_height() <= 52
    assert hurt.scroll_width() <= 360
    # back in the game: the chip is cleared and the row is as it was
    hurt.return_to_game_on_live(PURDY)
    assert hurt.chip_count() == 0
    assert hurt.lineups_html() == plain
    assert errors == []


@pytest.mark.render
def test_a_player_whose_game_has_not_started_draws_no_chip(mount):
    hurt, errors = HurtPage.on_live(mount)
    # DET has not kicked off: a stale flag on St. Brown is not drawn
    hurt.flag_before_his_game_starts("DET", {"slug": "amonra-st-brown", "name": "Amon-Ra St. Brown", "team": "DET", "q": 1, "clock": "", "back": False})
    assert hurt.chip_count() == 0
    assert errors == []


# ---------------------------------------------------------------- the poller

@pytest.mark.render
@pytest.mark.journey
def test_the_poller_asks_every_live_game_one_at_a_time_every_three_minutes(browser, page_file):
    ctx, page, errors = served(browser, page_file)
    hurt = HurtPage(page)
    hurt.plant(state="complete")
    hurt.open_view("live")
    hurt.stub_espn(STUB, summary(["SF", "OSF"], [play("B.Purdy pass incomplete short middle to M.Evans. SF-B.Purdy was injured during the play.", 3, "5:00")]))
    hurt.start_games()                          # two games with starters of mine, ESPN down for NYG's, and a game none of mine is in: asked all the same
    hurt.poll()
    calls = hurt.asked()
    assert sorted(calls) == ["ENYG", "ESF", "EZZ"], calls                # every game that is on
    assert hurt.most_in_flight() == 1                                    # one request in flight at a time
    got = hurt.who_is_hurt()
    assert list(got) == ["brock-purdy"] and got["brock-purdy"]["back"] is False and got["brock-purdy"]["q"] == 3
    # inside the gap: nothing; a failed fetch (NYG) said nothing and left the last state
    hurt.poll()
    assert hurt.ask_count() == 3
    hurt.move_clock(121000)
    hurt.poll()
    assert hurt.ask_count() == 3                                         # 121 s is not 180 s
    # 181 s after the first ask: all three again; the summary now says he is back, so the next paint clears him
    hurt.move_clock(60000)
    hurt.purdy_returns()
    hurt.poll()
    assert hurt.ask_count() == 6
    assert hurt.who_is_hurt()["brock-purdy"]["back"] is True
    # no game is on any more: nothing is asked, whatever the clock says
    hurt.finish_every_game()
    hurt.poll()
    assert hurt.ask_count() == 6
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_from_a_file_it_never_asks(mount):
    hurt, errors = HurtPage.on_live(mount, team=None, state="complete")
    hurt.start_sf_game()
    hurt.stub_espn(STUB, summary(["SF", "OSF"], [play("SF-B.Purdy was injured during the play.")]))
    assert hurt.is_served() is False
    hurt.poll()
    assert hurt.ask_count() == 0 and hurt.who_is_hurt() == {}
    assert errors == []


@pytest.mark.render
@pytest.mark.journey
def test_a_view_that_does_not_show_live_numbers_never_asks(browser, page_file):
    ctx, page, errors = served(browser, page_file)
    hurt = HurtPage(page)
    hurt.plant(state="complete")
    hurt.open_view("ranks")
    hurt.start_sf_game()
    hurt.stub_espn(STUB, summary(["SF", "OSF"], [play("SF-B.Purdy was injured during the play.")]))
    hurt.poll()
    assert hurt.ask_count() == 0
    ctx.close()
    assert errors == []

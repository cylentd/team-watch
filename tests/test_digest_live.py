"""The Digest during a game and on Monday night is generic (2026-10-04).

David: "The Digest is supposed to be GENERIC for the public. It shouldn't hone on to my roster or their
roster." The first Monday card (2bf04c6) drew the reader's matchup per league and its headline said "You're
up 1.6 going into Monday night"; both are superseded. The card is now one block per game (2026-10-05, about
80px): the day and the clock, the score, and the game's top performer in yards and touchdowns while it is on.

Every state here plants a week with LIVE_GAMEDAY's leagues in the page, because that is what a public reader
also carries, and then asserts the Digest drew none of their league names, team names or opponents' names.
LIVE_RANKS holds five players in the fixtures, so the projections the card reads are planted beside them.
Component tests on `mount("digest")` (`DigestStoryPage.plant`, which holds the plant)."""
import re

import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.digest_story import MONDAY_EARLY, MONDAY_ON, MONDAY_SCORERS, SUNDAY, DigestStoryPage
from pages.live import LivePage

pytestmark = pytest.mark.render

PHONE = (390, 844)


def personal(dg):
    """Every league name and team name (mine and my opponents') the page holds in LIVE_GAMEDAY."""
    names = dg.league_names()
    assert len(names) >= 10, names
    return names


def assert_generic(dg):
    """Nothing the Digest drew names a league or a team of the reader's, or says "you"."""
    html, text = dg.html(), dg.text()
    assert [n for n in personal(dg) if n in html] == []
    assert not re.search(r"going into|you're|your |yours|theirs to play|median", text, re.I), text


def digest(mount, **over):
    """The Digest mounted on a phone with the public week planted (`DigestStoryPage.plant`)."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestStoryPage(page)
    dg.plant(**over)
    return dg, errors


def test_during_a_game_the_digest_draws_no_league_team_or_opponent(mount):
    dg, errors = digest(mount, mon=[], clock={"DET": {"state": "in", "q": 3, "clock": "4:12", "half": False, "detail": "", "clubs": ["DET"]}})
    assert dg.headline() == "St. Brown ERUPTS: 60 yards"
    assert dg.now_rows() == 3      # three rows and More (2026-10-05)
    assert_generic(dg)
    # a player is hurt: the banner and a row name him, by his club, no team of mine
    dg.plant_hurt("bijan-robinson")
    assert dg.headline() == "B. Robinson left the game hurt"
    assert dg.lead_fact() == "ATL · Live"
    assert dg.now_hurt_rows() == 1
    assert_generic(dg)
    assert errors == []


def test_monday_before_kickoff_is_the_game_its_projections_and_a_generic_headline(mount):
    dg, errors = digest(mount, at=MONDAY_EARLY, sunState="complete")
    assert dg.mnf_cards() == 1 and "has-tn" in dg.ticker_classes()
    # one block: the day and the kickoff over the matchup, on line 1; no score and no top performer yet
    assert dg.mnf_block_count() == 1
    assert re.fullmatch(r"[A-Z]{3} \d{1,2}:\d\d [AP]M · NO @ ATL", dg.mnf_when())
    assert dg.mnf_parts() == {"score": 0, "top": 0}
    assert dg.mnf_box()["height"] <= 96
    # the projections left the card
    assert dg.mnf_retired_parts() == 0
    # the banner is the week's top scorer between windows, not a matchup
    assert dg.headline() == "St. Brown went off for 60 yards"
    assert dg.fits()
    assert_generic(dg)
    # a tap on the block opens that game's sheet
    dg.tap_mnf_block()
    LivePage(dg.page).wait_for_game_sheet()         # the sheet is Live's: its selector stays out of the Digest's page object
    assert errors == []


def test_monday_during_the_game_is_the_score_the_clock_and_the_games_top_scorers(mount):
    scorers = [[n, pos, team, pts] for team, rows in MONDAY_SCORERS.items() for n, pos, pts in rows]
    stats = {"ATL": {"pts_allow": 10}, "NO": {"pts_allow": 17}}      # a club's score is what the other's defense allowed
    dg, errors = digest(mount, at=MONDAY_ON, sunState="complete", monStates=["in_game"], stats=stats,
                        lead=[list(x) for x in SUNDAY] + scorers,
                        clock={"ATL": {"state": "in", "q": 2, "clock": "3:15", "half": False, "detail": "", "clubs": ["ATL", "NO"]}})
    assert dg.mnf_cards() == 1
    assert dg.mnf_block_count() == 1 and dg.mnf_box()["height"] <= 96
    # line 1: the day and the clock, no matchup once it is on
    assert re.fullmatch(r"[A-Z]{3} · Q2 3:15", dg.mnf_when_flat())
    # line 2: the score reads away then home: NO 10 (what ATL's defense allowed), ATL 17 (what NO's did)
    assert dg.mnf_score() == "NO 10 · ATL 17"
    # line 3: this game's best performer in yards and touchdowns, never Sunday's, never points
    assert dg.mnf_top() == "B. Robinson 60 yds"
    assert dg.headline() == "St. Brown went off for 60 yards"    # the week's top score, on any field; his game is final, so the past
    assert dg.fits()
    assert_generic(dg)
    # a poll repaints the block in place: the score moves, the page is not rebuilt
    dg.mark_root()
    dg.plant_pts_allowed("ATL", 13)
    assert dg.mnf_score() == "NO 13 · ATL 17"
    assert dg.root_is_marked()
    # a desktop: the block is at most 560px (STYLE.md, a label within 560px of its value) and the card as wide as its game
    dg.resize(1400, 900)
    try:
        w_block = dg.mnf_box()["width"]
        assert 360 <= w_block <= 560 and dg.mnf_card_box()["width"] <= w_block + 2
        assert dg.fits()
    finally:
        dg.resize(*PHONE)       # the kept context is the next test's
    assert errors == []


def test_two_late_games_each_have_their_own_line_and_a_finished_one_says_final(mount):
    stats = {"ATL": {"pts_allow": 7}, "NO": {"pts_allow": 24}}
    # before either kickoff by the clock, but Sleeper already calls the first one complete
    dg, errors = digest(mount, at=MONDAY_EARLY, sunState="complete", mon=[["NO", "ATL"], ["KC", "HOU"]],
                        monStates=["complete", "pre_game"], stats=stats)
    assert dg.mnf_block_count() == 2
    assert re.fullmatch(r"[A-Z]{3} · Final", dg.mnf_when(0)) and re.fullmatch(r"[A-Z]{3} \d{1,2}:\d\d [AP]M · KC @ HOU", dg.mnf_when(1))
    assert dg.mnf_score_numbers(0) == ["7", "24"]
    assert dg.mnf_state(0) == "final" and dg.mnf_state(1) == "pre"
    assert dg.mnf_parts(1) == {"score": 0, "top": 0}       # the one to come has no score and no performer
    assert dg.mnf_box(0)["height"] <= 96 and dg.mnf_box(1)["height"] <= 96
    assert dg.mnf_box(0)["y"] < dg.mnf_box(1)["y"]   # two games stack on a phone
    assert_generic(dg)
    assert errors == []


def test_before_the_week_reaches_its_last_day_there_is_no_card(mount):
    """Sunday's games still on: no Monday card, whatever Monday's slot holds."""
    dg, errors = digest(mount)
    assert dg.late_cards() == 0
    assert_generic(dg)
    assert errors == []


def test_the_digest_surface_reads_no_league_roster_or_matchup():
    """The rule, as a grep: nothing under surface/digest or data/digest.js touches a league, a roster, a
    matchup or Live's scorer. A view that does is personal, and the Digest is for the public."""
    import pathlib
    src = pathlib.Path(__file__).resolve().parents[1] / "design" / "src" / "js"
    files = sorted((src / "surface" / "digest").glob("*.js")) + [src / "data" / "digest.js"]
    bad = re.compile(r"\bGD\.leagues|\blg\.(me|teams|games|median)\b|\bgdSide\b|\bgdLeague\b|\bgdGame\b|\bgdMineIn\b|\bgdStarter\b|\bgdLadder\b")
    hits = []
    for f in files:
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", f.read_text(encoding="utf-8"), flags=re.S)
        hits += [f"{f.name}: {m.group(0)}" for m in bad.finditer(code)]
    assert hits == []
    hurt = (src / "data" / "gameday" / "hurt.js").read_text(encoding="utf-8")
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", hurt, flags=re.S)
    assert not bad.search(code), "hurt.js watches players league-wide: it reads LIVE_RANKS, not my lineups"

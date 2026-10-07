"""The Roster card backs of a kicker, a defense and a signed player, and the Sheet strip's room (David, 2026-10-07).

A kicker's and a defense's back were a different layout with cut labels ("OPP ...", "TEAM P..."): now the same
back as every other card, the matchup and kickoff on top, two facts and the projection in whole words centred
below, the button last. There are no weekly K or D/ST fantasy points on the page (the box score holds QB RB WR
TE only), so no bars. A signed card's back lost its three-line sentence: the signed week's bar wears a gold star
and its points in gold. The Sheet's strip took David's colour pick (his position's colour as a time ramp) and a
guaranteed gap before it. The pure parts are test_js_supportback.py and test_js_pointsbars.py. Component layer:
`mount`, `BackFacts` (tests/pages/roster_backs.py)."""
import re

import pytest

from component import Mounter, mount as base_mount
from pages.roster_backs import BackFacts
from pages.roster_motion import show_cards


REQ = "Phone layout"
PHONE = (360, 660)
# SF is home to ARI at Sun 1:05 PM Pacific, in a dome; CIN is away to ATL.
SCENE = {"games": [{"week": 5, "home": "SF", "away": "ARI", "kickoff": "2026-10-11T20:05:00Z"},
                   {"week": 5, "home": "ATL", "away": "CIN", "kickoff": "2026-10-11T17:00:00Z"}],
         "factors": {}, "form": {}, "weather": {"SF": {"roof": "dome"}}}
SF = {"implied": 24.8, "opp": "ARI", "spread": -7, "total": 42.5}
ARI = {"implied": 17.8, "opp": "SF", "spread": 7, "total": 42.5}
LINES = {"SF": SF, "ARI": ARI}
DST = [{"team": "SF", "weeks": [{"week": 5, "bye": False, "dst": {"dst_espn": 5.1, "dst_yahoo": 5.3}, "k": {"k_yahoo": 7.8}}]}]


@pytest.fixture(scope="module")
def mount(base_mount, built):
    """`mount` over the same build with an empty LIVE_SIGNED for week 3 (as test_roster_cards.py makes it) and
    an empty LIVE_LINES block to plant the books' lines into (the fixtures price no game: the build writes null).
    Its own folder, so its page is its own file; its context and cold first load are the module's setup."""
    text, n = re.subn(r"^const LIVE_SIGNED = .*;$", 'const LIVE_SIGNED = {"wk": 3, "players": {}};', built.fragment, count=1, flags=re.M)
    text, k = re.subn(r"^const LIVE_LINES = .*;$", 'const LIVE_LINES = {"teams": {}};', text, count=1, flags=re.M)
    assert (n, k) == (1, 1)
    m = Mounter(base_mount.browser, base_mount.folder / "backs", text)
    m.prepare("roster", size=PHONE)
    yield m
    m.pages.close()


def cards(mount):
    page, errors = mount("roster", size=PHONE)
    roster = BackFacts(page)
    assert show_cards(roster, "espn", "skip") == 1
    roster.plant(SCENE)
    return roster, errors


@pytest.mark.render
@pytest.mark.req(REQ, ac="a kicker's back is the matchup and kickoff, the roof, the team's points and the projection, in whole words")
def test_a_kickers_back_is_the_matchup_two_facts_and_the_projection(mount):
    roster, errors = cards(mount)
    got = roster.support("K", "SF", lines=LINES, dst=DST)
    assert (got["matchup"], got["kick"]) == ("vs ARI", "Sun 1:05 PM"), "the game, then its kickoff, like every other back"
    assert got["rows"] == [["Roof", "Dome"], ["Team pts", "24.8"], ["Proj pts", "7.8"]]
    assert "Kicking" not in got["head"] and got["whole"] and got["over"] <= 0
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a defense's back is the matchup and kickoff, the opponent's points, the spread with a real minus and the projection")
def test_a_defenses_back_is_the_matchup_two_facts_and_the_projection(mount):
    roster, errors = cards(mount)
    got = roster.support("DST", "SF", lines=LINES, dst=DST)
    assert (got["matchup"], got["kick"]) == ("vs ARI", "Sun 1:05 PM")
    assert got["rows"] == [["Opp pts", "17.8"], ["Spread", "−7"], ["Proj pts", "5.3"]]
    assert got["whole"] and got["over"] <= 0
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a kicker outdoors shows the wind in place of the roof; a league with no kicker slot has no projection row")
def test_an_outdoor_kicker_shows_the_wind_and_espn_has_no_kicker_projection(mount):
    roster, errors = cards(mount)
    windy = {"roof": "outdoor", "wind": "12 mph", "wind_dir": "SW"}
    got = roster.support("K", "SF", key="yahoo", lines=LINES, weather={"SF": windy}, dst=DST)
    assert [r[0] for r in got["rows"]] == ["Wind", "Team pts", "Proj pts"] and got["rows"][0][1] == "12 mph"
    espn = roster.support("K", "SF", key="espn", lines=LINES, weather={"SF": windy}, dst=DST)
    assert [r[0] for r in espn["rows"]] == ["Wind", "Team pts"], "ESPN has no K slot, so no cell to project"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="no label on a kicker's or a defense's back is cut, with the widest numbers they print")
@pytest.mark.parametrize("pos", ["K", "DST"])
def test_no_label_is_cut_with_the_widest_numbers(mount, pos):
    roster, errors = cards(mount)
    wide = {"SF": {"implied": 30.5, "opp": "ARI", "spread": -10.5, "total": 52.5}, "ARI": {"implied": 30.5, "opp": "SF", "spread": 10.5, "total": 52.5}}
    windy = {"roof": "outdoor", "wind": "25 mph", "wind_dir": "SW"}
    dst = [{"team": "SF", "weeks": [{"week": 5, "bye": False, "dst": {"dst_yahoo": 14.5}, "k": {"k_yahoo": 14.5}}]}]
    got = roster.support(pos, "SF", lines=wide, weather={"SF": windy}, dst=dst)
    assert len(got["rows"]) == 3 and got["whole"] and got["over"] <= 0, got
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a support back's facts centre between the kickoff line and the button")
@pytest.mark.parametrize("pos", ["K", "DST"])
def test_the_facts_centre_between_the_heading_and_the_button(mount, pos):
    roster, errors = cards(mount)
    got = roster.support(pos, "SF", lines=LINES, dst=DST)
    assert abs(got["above"] - got["below"]) <= 2 and got["above"] >= 4, got
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a signed card's back marks the signed week's bar with a gold star and gold points, and says nothing")
def test_a_signed_week_wears_a_gold_star_and_its_points_in_gold(mount):
    roster, errors = cards(mount)
    got = roster.signed_back()
    assert got["stars"] == [False, False, True, False, False] and got["golds"] == [False, False, True, False, False], "week 3's bar, only"
    assert "Signed for" not in got["text"] and got["kick"], "no sentence, and the kickoff line stays"
    assert got["over"] <= 0
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a row's bars are his position's colour, soft for played weeks, strong for the latest, a dashed outline for this week")
def test_the_strip_is_his_positions_colour_as_a_time_ramp(mount):
    page, errors = mount("roster", size=PHONE)
    roster = BackFacts(page)
    roster.show("espn")
    roster.plant_points("brock-purdy", {1: 10.4, 2: 27.0, 3: 20.6, 4: 9.5}, 18.6)
    roster.plant_points("chase-brown", {1: 5.0, 2: 14.0, 3: 9.0, 4: 11.0}, 10.0, pos="RB")
    roster.plant(SCENE)
    rows = {r["name"]: r["bars"] for r in roster.look()}
    qb, rb = rows["B. Purdy"], rows["C. Brown"]
    assert [b["bg"] for b in qb] == ["rgba(90, 180, 255, 0.4)"] * 3 + ["rgba(90, 180, 255, 0.95)", "rgba(90, 180, 255, 0.12)"]
    assert [b["bg"] for b in rb][-2:] == ["rgba(255, 157, 92, 0.95)", "rgba(255, 157, 92, 0.12)"], "a back is orange"
    assert [b["border"] for b in qb] == ["none"] * 4 + ["dashed"], "this week, not yet played: a dashed outline"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a starter's name block never reaches its strip: at least 6px stay between the text and the first bar")
def test_the_strip_keeps_a_gap_from_the_name_block_on_a_phone(mount):
    page, errors = mount("roster", size=PHONE)
    roster = BackFacts(page)
    roster.show("espn")
    roster.plant_points("brock-purdy", {1: 10.4, 2: 27.0, 3: 20.6, 4: 9.5}, 18.6)
    roster.plant(SCENE)
    rows = roster.room()
    assert rows, "the fixture's starters have strips"
    assert all(r["bar"] - r["text"] >= 6 for r in rows), [(r["text"], r["bar"]) for r in rows]
    assert all(r["strip"][0] >= r["track"][0] - 0.5 and r["strip"][1] <= r["track"][1] + 0.5 for r in rows), "the strip stays in its track"
    assert errors == []

"""The Roster's matchup line, on the Sheet and on a card's back (David's pick "B . Row + back", 2026-10-07).

A row says who he faces in two lines ("vs ARI 5th" with the stadium's roof, then "Sun 1:05 PM") where it said
"QB · SF vs ARI" over a rank hidden below 760px; his name is initials on a phone, so the row is ~65px, not 82.
A card's back leads with the same two lines, then his fantasy points week by week as bars (the row has the same
bars, smaller, and no usage numbers). The rank is the projection's own matchup number, 1st = the toughest defense; 1-8 read red, 9-24
neutral, 25-32 green. The pure parts (the band, the roof, the bars' model) are in test_js_matchupline.py and test_js_pointsbars.py; here is
what a 360px phone draws. Component layer: `mount`, `MatchupLine` (tests/pages/roster_matchup.py).
"""
import re

import pytest

from component import Mounter, mount as base_mount
from pages.roster_matchup import MatchupLine
from pages.roster_motion import show_cards
from pages.warm import warm
from wording import words

PHONE = (360, 660)
SUN = {"opening": "2026-10-11T20:05:00Z", "morning": "2026-10-11T17:00:00Z"}     # Sun 1:05 PM and 10:00 AM Pacific
GAMES = [{"week": 5, "home": "SF", "away": "ARI", "kickoff": SUN["opening"]},
         {"week": 5, "home": "ATL", "away": "CIN", "kickoff": SUN["morning"]}]
NEXT = lambda opp, home, rank: {"opp": opp, "home": home, "factor": {"rank": rank, "of": 32}}     # noqa: E731
FORM = {"ARI": {"current": {"TE": {"rank": 14, "pts_pg": 6.0}, "QB": {"rank": 3, "pts_pg": 14.0}}},
        "ATL": {"current": {"TE": {"rank": 2, "pts_pg": 3.0}}}, "XXX": {"current": {"TE": {"rank": 32, "pts_pg": 12.0}}}}
FACTORS = {"brock-purdy": NEXT("ARI", True, 5), "george-kittle": None, "chase-brown": NEXT("ATL", False, 25),
           "tee-higgins": NEXT("ATL", False, 8)}
SCENE = {"games": GAMES, "factors": FACTORS, "form": FORM, "weather": {"SF": {"roof": "dome"}, "ATL": {"roof": "retractable"}}}
BYE = {**SCENE, "games": GAMES[:1]}              # CIN has no game this week


@pytest.fixture(scope="module")
def mount(base_mount):
    """`mount`, with the phone's context opened once for the module (pages/warm.py)."""
    return warm(base_mount, ("roster", PHONE), ("roster", (1280, 900)))      # the desktop row test's size too: cold in a call otherwise


@pytest.fixture(scope="module")
def signed_mount(mount, built):
    """`mount` over the same build with an empty LIVE_SIGNED for week 3 (the fixtures log too few teams for any
    week to be complete, so the build writes null): the same swap test_roster_cards.py makes."""
    text, n = re.subn(r"^const LIVE_SIGNED = .*;$", 'const LIVE_SIGNED = {"wk": 3, "players": {}};', built.fragment,
                      count=1, flags=re.M)
    assert n == 1
    m = Mounter(mount.browser, mount.folder / "signed-matchup", text)
    m.prepare("roster", size=PHONE)       # its context and cold first load are the module's setup, not the first test's
    yield m
    m.pages.close()


def sheet(mount, scene=SCENE, size=PHONE):
    page, errors = mount("roster", size=size)
    roster = MatchupLine(page)
    roster.show("espn")
    roster.plant(scene)
    return roster, errors


def cards(mount, scene=SCENE, size=PHONE):
    """The ESPN roster's cards with the pack skipped; `scene` (None for none: a test that draws a made-up player
    needs no planted games, and the planting redraws the whole roster, ~40 ms) planted over it."""
    page, errors = mount("roster", size=size)
    roster = MatchupLine(page)
    assert show_cards(roster, "espn", "skip") == 1, "the fixture's schedule has a week ahead, so a pack waits"
    if scene:
        roster.plant(scene)
    return roster, errors


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="a Sheet row says the game, its rank and roof, then the kickoff in two lines")
def test_a_row_says_the_game_with_its_roof_and_the_kickoff_under_it(mount):
    roster, errors = sheet(mount)
    rows = roster.lines()
    purdy, kittle, brown, higgins = (rows[n] for n in ("B. Purdy", "G. Kittle", "C. Brown", "T. Higgins"))
    assert (purdy["game"], purdy["kick"], purdy["roof"], purdy["roofClass"]) == ("vs ARI 5th", "Sun 1:05 PM", "Dome", "ml-roof dome")
    assert (brown["game"], brown["kick"], brown["roof"], brown["roofClass"]) == ("@ ATL 25th", "RB · Sun 10:00 AM", words("teams.line.retractable"),"ml-roof retractable")
    assert (higgins["game"], higgins["kick"]) == ("@ ATL 8th", "WR · Sun 10:00 AM")      # the bench shows no slot, so it says WR
    assert (kittle["game"], kittle["kick"]) == ("vs ARI 14th", "Sun 1:05 PM"), "no factor of his own: the opponent's form rank"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="the rank is red for 1-8, neutral for 9-24 and green for 25-32, in the page's tokens")
def test_the_rank_is_red_neutral_or_green_by_its_band(mount):
    roster, errors = sheet(mount)
    rows, tok = roster.lines(), roster.tokens()
    got = {n: (rows[n]["cls"].split()[-1], rows[n]["color"]) for n in ("B. Purdy", "G. Kittle", "C. Brown", "T. Higgins")}
    assert got == {"B. Purdy": ("ml-hard", tok["down"]), "G. Kittle": ("ml-mid", tok["ink2"]),
                   "C. Brown": ("ml-easy", tok["up"]), "T. Higgins": ("ml-hard", tok["down"])}
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="a phone's row is one name line over two matchup lines, about 65px, with nothing cut")
def test_a_phone_row_is_two_short_lines_with_initials_and_nothing_cut(mount):
    roster, errors = sheet(mount)
    rows = roster.lines()
    assert sorted(rows) == ["B. Purdy", "C. Brown", "G. Kittle", "T. Higgins"]
    assert all(r["height"] <= 70 for r in rows.values()), {n: r["height"] for n, r in rows.items()}
    assert not any(r["cut"] for r in rows.values())
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="a bye is one line, 'Bye', with his position where the row does not show it")
def test_a_bye_is_one_line(mount):
    roster, errors = sheet(mount, BYE)
    rows = roster.lines()
    assert (rows["C. Brown"]["game"], rows["C. Brown"]["kick"], rows["C. Brown"]["rank"]) == ("RB · Bye", None, None)
    assert (rows["T. Higgins"]["game"], rows["T. Higgins"]["kick"]) == ("WR · Bye", None)
    assert rows["B. Purdy"]["kick"] == "Sun 1:05 PM", "a club that plays is untouched"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="a desktop row keeps the full name beside the same two lines")
def test_a_desktop_row_keeps_the_full_name(mount):
    roster, errors = sheet(mount, size=(1280, 900))
    rows = roster.lines()
    assert sorted(rows) == ["Brock Purdy", "Chase Brown", "George Kittle", "Tee Higgins"]
    assert (rows["Brock Purdy"]["game"], rows["Brock Purdy"]["kick"]) == ("vs ARI 5th", "Sun 1:05 PM")
    assert errors == []


PURDY = {1: 10.4, 2: 27.0, 3: 20.6, 4: 9.5}


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="a row's strip is one bar per completed week and a dashed one last, in his position's colour, with no numbers")
def test_a_row_draws_a_bar_a_week_and_a_hollow_one_for_the_projection(mount):
    page, errors = mount("roster", size=PHONE)
    roster = MatchupLine(page)
    roster.show("espn")
    roster.plant_points("brock-purdy", PURDY, 18.6)
    roster.plant_points("george-kittle", {1: 5.0, 3: 12.0, 4: 8.0}, 9.0, pos="TE")      # no row for week 2: he did not play
    roster.plant(SCENE)
    rows, tok = roster.lines(), roster.tokens()
    purdy, kittle = rows["B. Purdy"]["bars"], rows["G. Kittle"]["bars"]
    assert [b["proj"] for b in purdy] == [False, False, False, False, True], "four weeks, then the projection last"
    assert [round(b["h"], 2) for b in purdy] == [.39, 1.0, .76, .35, .69], "one scale, 0 to his largest of bars and projection"
    assert [b["gap"] for b in kittle] == [False, True, False, False, False], "the week he missed is a tick in its place"
    # David's pick V3 toned down, 2026-10-07: his position's colour (a QB's blue), played weeks faint, the latest stronger, this week's soft fill
    assert [b["color"] for b in purdy] == ["rgba(90, 180, 255, 0.22)"] * 3 + ["rgba(90, 180, 255, 0.55)", "rgba(90, 180, 255, 0.12)"]
    assert rows["B. Purdy"]["text"] == "", "no number and no label in the strip"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="a bench row draws the same strip")
def test_a_bench_row_draws_the_strip_too(mount):
    page, errors = mount("roster", size=PHONE)
    roster = MatchupLine(page)
    roster.show("espn")
    roster.plant_points("tee-higgins", {1: 6.0, 2: 14.0, 3: 9.0, 4: 11.0}, 10.0, pos="WR")
    roster.plant(SCENE)
    assert len(roster.lines()["T. Higgins"]["bars"]) == 5
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="a back leads with the matchup line and the kickoff, no rank heading, week line or usage")
def test_a_back_leads_with_the_matchup_line_and_the_kickoff(mount):
    roster, errors = cards(mount)
    roster.plant_points("brock-purdy", PURDY, 18.6)
    got = roster.back("brock-purdy")
    tok = roster.tokens()
    assert (got["matchup"], got["roof"], got["kick"], got["sub"]) == ("vs ARI 5th", "Dome", "Sun 1:05 PM", "Sun 1:05 PM")
    assert got["color"] == tok["down"]
    assert "#" not in got["text"] and "role" not in got["text"].lower() and "avg" not in got["text"].lower()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="the back's bars carry each week's points over them and its week under them, the projection last")
def test_a_back_draws_each_weeks_points_over_its_bar_and_the_week_under_it(mount):
    roster, errors = cards(mount)
    roster.plant_points("brock-purdy", PURDY, 18.6)
    got = roster.back("brock-purdy")
    assert got["pts"] == ["10", "27", "21", "10", "19"] and got["weeks"] == ["W1", "W2", "W3", "W4", "W5"]
    assert [b["proj"] for b in got["bars"]] == [False] * 4 + [True]
    assert [round(b["h"], 2) for b in got["bars"]] == [.39, 1.0, .76, .35, .69]
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="a back fits its card on a phone with the kickoff, an injury, the weather or an autograph")
@pytest.mark.parametrize("case", ["kickoff", "injury", "weather", "signed"])
def test_every_back_fits_its_card_at_360px(signed_mount, case):
    # The mount draws in the fallback fonts (its network is cut), a little wider than the page's own, so its
    # 360px card is 103x144; the 98x137 card of a desktop browser's 360px window was measured on the built page.
    roster, errors = cards(signed_mount, SCENE if case != "weather" else
                           {**SCENE, "weather": {"SF": {"roof": "outdoor", "wind": "22 mph", "precip_pct": 60, "short": "Rain"}}})
    roster.plant_points("brock-purdy", PURDY, 18.6)
    extra = {"injury": {"injury": {"s": "Q", "code": "Questionable", "note": "Hamstring"}},
             "signed": {"signed": {"rank": 2, "pts": 22.6}}}.get(case, {})
    got = roster.back("brock-purdy", **extra)
    assert got["over"] <= 0, f"{case}: the back's content is {got['over']}px taller than the back, card {got['w']}x{got['h']}"
    assert got["open"], f"{case}: the profile button sits inside the back"
    assert len(got["pts"]) == 5
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="an injury or the weather takes the second line from the kickoff")
def test_an_injury_replaces_the_kickoff_on_the_second_line(mount):
    roster, errors = cards(mount)
    got = roster.back("brock-purdy", injury={"s": "Q", "code": "Questionable", "note": "Hamstring"})
    assert got["kick"] is None and words("teams.inj.questionable").upper() in got["sub"].upper() and got["matchup"] == "vs ARI 5th"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="every position's back fits whole numbers and week labels with nothing cut, in week 5 and week 12")
@pytest.mark.parametrize("pos", ["QB", "RB", "WR", "TE"])
@pytest.mark.parametrize("week, weeks", [(5, ["W1", "W2", "W3", "W4", "W5"]), (12, ["W8", "W9", "10", "11", "12"])])
def test_no_number_or_week_label_on_a_back_is_cut(mount, pos, week, weeks):
    roster, errors = cards(mount, None)
    slug = f"test-{pos.lower()}-bars"
    roster.plant_points(slug, {wk: 44.5 for wk in range(1, week)}, 44.8, pos=pos, week=week)
    got = roster.made_up_back(pos, week)
    assert got["weeks"] == weeks and len(got["pts"]) == 5
    assert got["whole"], "a number or a week label is wider than its slot"
    assert got["over"] <= 0 and got["open"]
    assert errors == []

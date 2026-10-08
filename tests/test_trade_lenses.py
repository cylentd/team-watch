"""League > Trades, the lenses on an offer card (ledger #44, 2026-10-08; ff-jarvis 3cf9002): each side is judged on the lens
its standing weighs most (Now, Push, Playoff run, ROS), and the card says which, for both sides, with the partner's gain
as big as the reader's: the pitch. Then the nearest bye notes, and the four lenses one tap away.

The data is the fixture's ESPN league (tests/fixtures/data/trade_offers.json): Run It Back, a chaser, and his three offers
to Purdy Big in Japan, a contender. Only Run It Back's offers carry lenses; Purdy's are the shape from before them, which
the frozen finder and edit tests read. Which lens judges a side, its gain and which notes a card keeps are decided in
Node (test_js_finder.py); the contract is test_trade_offers.py; this file is what the screen draws. An offer without
lenses is the ROS card it was."""
import copy

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.finder import FIXTURE, FinderPage, builder, finder
from pages.finder_lens import FinderLens
from wording import words

READER = "espn-run-it-back"             # Run It Back's TEAMS key
PARTNER = "espn"                        # Purdy Big in Japan's


def lens_card(mount, size=(360, 740), body=None):
    """The finder filtered to Purdy for Run It Back: his three offers, best lens score first."""
    page, errors = finder(mount, READER, size=size, body=body)
    FinderPage(page).wait_offers()
    builder(page, PARTNER)
    return FinderLens(page), errors


def pts(n):
    return f"{n} {words('finder.side.pts')}"


def judge(tier, lens):
    return words("finder.judge").format(tier=words(f"finder.tier.{tier}"), lens=words(f"finder.lens.{lens}"))


@pytest.mark.req("Trade finder", ac="each side is judged on its own lens, the partner's gain as big as the reader's")
def test_each_side_shows_the_gain_on_the_lens_that_judges_it_and_its_tier(mount):
    f, errors = lens_card(mount)
    you, them = words("finder.side.me"), words("finder.side.them")
    assert f.sides() == [
        [{"who": you, "gain": pts("+21.2"), "judge": judge("chaser", "ros")},
         {"who": them, "gain": pts("+4.1"), "judge": judge("contender", "push")}],
        [{"who": you, "gain": pts("+20.3"), "judge": judge("chaser", "ros")},
         {"who": them, "gain": pts("+1.3"), "judge": judge("contender", "ros")}],
        [{"who": you, "gain": pts("+14.4"), "judge": judge("chaser", "ros")},
         {"who": them, "gain": pts("+4.2"), "judge": judge("contender", "playoffs")}],
    ], "Purdy gains 0.4 over the season on the first offer but 4.1 over the next 4 weeks; the third pays him in the playoffs"
    assert errors == []


def test_the_partners_gain_is_drawn_exactly_as_large_as_the_readers_on_the_same_line(mount):
    f, _ = lens_card(mount)
    looks = f.gain_looks()
    assert len(looks) == 3 and all(len(card) == 2 for card in looks)
    assert [mine == theirs for mine, theirs in looks] == [True, True, True], looks


def test_a_card_shows_its_nearest_two_bye_notes_in_plain_words_and_none_when_it_has_none(mount):
    f, errors = lens_card(mount)
    note = lambda key, **kw: words(f"finder.note.{key}").format(**kw)
    assert f.notes() == [
        [note("coversMe", name="C. Skattebo", week=6), note("coversThem", name="K. Williams", week=8)],
        [note("coversThem", name="B. Robinson", week=6), note("coversMeMany", name="J. Goff", n=2, week=7)],
        [],
    ], "weeks 5-8 only (the Push window from week 5), nearest first, two at most"
    assert errors == []


def test_the_four_lenses_are_one_tap_away_with_the_judging_cell_of_each_side_marked(mount):
    f, errors = lens_card(mount)
    assert not f.lenses_open(0), "the answer leads; the research waits for a tap"
    f.open_lenses(0)
    weeks = lambda n: words("finder.lens.weeks").format(n=n)
    assert f.lens_rows(0) == [
        {"lens": words("finder.lens.now"), "weeks": weeks(2), "me": "+0.8", "them": "+3.4", "on": [False, False]},
        {"lens": words("finder.lens.push"), "weeks": weeks(4), "me": "+2.9", "them": "+4.1", "on": [False, True]},
        {"lens": words("finder.lens.playoffs"), "weeks": weeks(3), "me": "+7.4", "them": "−1.2", "on": [False, False]},
        {"lens": words("finder.lens.ros"), "weeks": weeks(13), "me": "+21.2", "them": "+0.4", "on": [True, False]},
    ]
    assert not f.lenses_open(1), "one card's table opens alone"
    assert errors == []


def test_a_league_that_places_no_team_names_the_lens_without_a_tier(mount):
    body = copy.deepcopy(FIXTURE)
    del body["leagues"]["espn"]["standing"]
    f, errors = lens_card(mount, body=body)
    assert [s["judge"] for s in f.sides()[0]] == [words("finder.lens.ros"), words("finder.lens.push")]
    assert errors == []


def test_an_offer_from_before_the_lenses_is_the_rest_of_season_card(mount):
    body = copy.deepcopy(FIXTURE)
    for o in body["leagues"]["espn"]["teams"]["Run It Back"]:
        for k in ("lenses", "lens", "score", "notes"):
            del o[k]
    f, errors = lens_card(mount, body=body)
    assert f.sides() == [[], [], []] and f.notes() == [[], [], []] and not f.has_lenses()
    assert [c["gain"] for c in FinderPage(f.page).cards()] == [words("lboard.offer.gain").format(n=n) for n in ("+21.2", "+20.3", "+14.4")]
    assert errors == []


@pytest.mark.parametrize("size", [(360, 740), (1280, 900)])
def test_the_lens_card_fits_the_width_with_the_table_open(mount, size):
    f, errors = lens_card(mount, size=size)
    f.open_lenses(0)
    assert FinderPage(f.page).fits(), "nothing scrolls sideways"
    assert errors == []

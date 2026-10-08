"""This week > Digest, the night-game card (2026-10-07, TODO "Digest previews the night games"; DESIGN.md "Digest by day").

One preview card, two days: Wednesday's Digest previews Thursday night's game and Sunday's previews Sunday night's.
The card is Claude's take and the lines from Preview's dossier (LIVE_PREVIEW, design/preview.py); a tap opens Preview
on that game. Wednesday leads with Usage movers and Sunday with Need to know; Sunday's card goes at the night game's
kickoff; the card cap stays five. Which game and the order are Node tests (test_js_digest_night.py); this file proves
what the card draws and what a tap does, on `mount("digest")` (`DigestNightPage`).

The fixture preview's games are PIT @ CLE (a line, a take, Claude's pick PIT 58%) and JAX @ LA, replanted at the
clocks below: Wednesday noon Pacific 2026-10-07 (Thursday night kicks 00:15Z Oct 9) and Sunday noon 2026-09-27, a
day inside the fixture packet's week so Need to know draws (Sunday night kicks 00:20Z Sep 28). Expected values come from the fixture file and content.json, never the card's code.
"""
import json
import pathlib

import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.digest_night import DigestNightPage
from pages.preview import PreviewPage
from wording import words

pytestmark = pytest.mark.render

COPY = json.loads((pathlib.Path(__file__).resolve().parent.parent / "design" / "src" / "content.json").read_text(encoding="utf-8"))
PHONE = (360, 800)
WED, SUN, SUN_KICKED, THU, MON, TUE, SAT = ("2026-10-07T19:00:00Z", "2026-09-27T19:00:00Z", "2026-09-28T00:30:00Z",
                                            "2026-10-08T19:00:00Z", "2026-10-05T19:00:00Z", "2026-10-06T19:00:00Z", "2026-10-10T19:00:00Z")
TNF_KICK, SNF_KICK, EARLY = "2026-10-09T00:15:00Z", "2026-09-28T00:20:00Z", "2026-09-27T17:00:00Z"
HEAD = "Pittsburgh wins it through the air on a short week"
# PIT @ CLE is fixture game 0 (from=0); JAX @ LA (from=1) is the day's other game, first by kickoff.
THU_NIGHT = [{"from": 1, "kickoff": EARLY, "slot": "sun1"}, {"from": 0, "kickoff": TNF_KICK, "slot": "thu", "head": HEAD}]
SUN_NIGHT = [{"from": 1, "kickoff": EARLY, "slot": "sun1"}, {"from": 0, "kickoff": SNF_KICK, "slot": "sunnight", "head": HEAD}]


def night(mount):
    page, errors = mount("digest", size=PHONE)
    return DigestNightPage(page), errors


@pytest.mark.req("Digest", ac="Wednesday previews Thursday night's game, second after usage movers")
def test_wednesday_has_thursday_nights_card_after_usage_movers(mount):
    dg, errors = night(mount)
    dg.plant_night(WED, *THU_NIGHT)
    assert dg.card_ids()[:2] == ["usage", "night"]
    assert dg.title("night") == words("digest.card.night.titleThu")
    assert errors == []


@pytest.mark.req("Digest", ac="the card is Claude's take and the lines from Preview's dossier")
def test_the_card_names_the_game_and_says_claudes_headline_and_the_bets(mount):
    dg, errors = night(mount)
    dg.plant_night(WED, *THU_NIGHT)
    assert dg.night_game().startswith("PIT @ CLE")
    assert dg.night_head() == HEAD
    assert [(b["bet"], b["vegas"], b["claude"]) for b in dg.night_bets()] == [
        ("Winner", "PIT 56%", "PIT wins 58% chance"), ("Spread", "PIT by 2.5", "No pick"), ("Total", "38.5", "No pick")]
    assert dg.fits()
    assert errors == []


@pytest.mark.req("Digest", ac="Sunday previews Sunday night's game, second after Need to know, until it kicks off")
def test_sunday_has_sunday_nights_card_after_need_to_know_until_the_kickoff(mount):
    dg, errors = night(mount)
    dg.plant_night(SUN, *SUN_NIGHT)
    assert dg.order()[:2] == ["need", "night"], "Need to know is a section, not a card: the page order says it"
    assert dg.title("night") == words("digest.card.night.titleSun")
    dg.plant_night(SUN_KICKED, *SUN_NIGHT)
    assert not dg.has_card("night"), "kicked off: the card is gone"
    assert errors == []


@pytest.mark.req("Digest", ac="five cards at most")
def test_wednesday_with_every_card_drawing_stays_at_five(mount):
    dg, errors = night(mount)
    dg.plant_stub_cards()
    dg.plant_night(WED, *THU_NIGHT)
    assert dg.card_ids() == ["usage", "night", "gains", "defenses", "adds"]
    assert errors == []


@pytest.mark.req("Digest", ac="the night card is on Wednesday and Sunday only")
@pytest.mark.parametrize("at", [TUE, THU, MON, SAT])
def test_no_other_day_has_a_night_card(mount, at):
    dg, errors = night(mount)
    dg.plant_night(at, *THU_NIGHT)
    assert not dg.has_card("night")
    dg.plant_night(at, *SUN_NIGHT)
    assert not dg.has_card("night")
    assert errors == []


@pytest.mark.req("Digest", ac="a week with no night game has no card")
def test_a_week_with_no_night_game_has_no_card(mount):
    dg, errors = night(mount)
    dg.plant_night(WED, THU_NIGHT[0])
    assert not dg.has_card("night")
    assert errors == []


@pytest.mark.req("Digest", ac="a card with no data draws nothing")
def test_a_night_game_with_neither_a_line_nor_a_take_draws_no_card(mount):
    dg, errors = night(mount)
    dg.plant_night(WED, *THU_NIGHT)
    dg.plant_bare_games()
    assert not dg.has_card("night")
    assert errors == []


@pytest.mark.req("Digest", ac="a tap on the card opens Preview on that game")
def test_a_tap_opens_previews_dossier_on_the_night_game(mount):
    dg, errors = night(mount)
    dg.plant_night(WED, *THU_NIGHT)
    dg.tap_night()
    assert dg.view_leaf() == "#preview"
    pv = PreviewPage(dg.page)
    assert pv.is_open() and pv.dossier_visible()
    assert "PIT" in pv.match() and "CLE" in pv.match(), "the second game by kickoff, not the slate's first"
    assert errors == []


@pytest.mark.req("Digest", ac="a tap on the card opens Preview on that game")
def test_the_header_link_opens_the_same_game(mount):
    dg, errors = night(mount)
    dg.plant_night(SUN, *SUN_NIGHT)
    assert dg.more("night")["text"] == words("nav.tab.preview")
    dg.tap_night_more()
    assert dg.view_leaf() == "#preview"
    assert "CLE" in PreviewPage(dg.page).match()
    assert errors == []


@pytest.mark.req("Digest", ac="a card with no data draws nothing")
def test_the_card_with_every_block_missing_draws_nothing(mount):
    dg, errors = night(mount)
    assert dg.card_html_without_data("Night") == ""
    assert errors == []

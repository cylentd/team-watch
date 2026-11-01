"""S10, an untested number says so, as drawn: the Waivers lanes, the trade finder and history, Slips and Preview.

test_untested_marks_drawn.py proves the views whose fixture already holds the state. This file does the rest of the
market views: each puts `words(key)` on an element whose line also draws a number, the same check
(`drawn_beside_a_number`), at 360px. The words are read through `words`, never retyped.

Planted in the page after mount, never in tests/fixtures: a lane on every Waivers card (`SET_LANE`). The other views
need no plant: the finder's chip is drawn in the edit state, the Slips flag on an opened game, Preview's travel mark on
the dossier of a game with a time-zone change.

Not covered, findings for a later branch (see the report of 2026-11-01): dfs.tag.handcuffMark (its row's number is in a
sibling div of the tag's line), parlay.tag.cbTitle and parlay.tag.roleMark (Build's player line draws no number),
legsheet.matchup.mark (the leg sheet is outside `#view`, which `MarksPage.carriers` reads, and its mark is a line alone).
"""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.finder import FinderPage, finder
from pages.league_chip import pick_script
from pages.marks import MarksPage
from pages.preview import PreviewPage
from pages.slips import SlipsPage
from test_untested_marks_drawn import drawn_beside_a_number

SET_LANE = "lane => { LIVE_WAIVER.players.forEach(r => Object.values(r.leagues).forEach(l => { l.lane = lane; })); render(); }"
LANES = [("usage", "waiver.lane.usageMark"), ("starter", "waiver.lane.starterMark"),
         ("role", "waiver.lane.roleMark"), ("injured", "waiver.lane.injuredMark")]
SLIPS_GAME = "CIN @ NYJ"      # a morning game whose defense the fixture ranks, so its players draw the matchup chip
TRAVEL_GAME = 1               # LA at JAX in the fixture: both sides cross time zones


@pytest.mark.render
@pytest.mark.parametrize(("lane", "key"), LANES)
def test_a_waiver_lane_draws_its_mark_on_a_card_with_a_number(mount, lane, key):
    page, errors = mount("waivers", size=(360, 800))
    page.evaluate(SET_LANE, lane)
    assert drawn_beside_a_number(MarksPage(page), key), f"the Waivers {lane} lane does not draw {key} beside a number"
    assert errors == []


@pytest.mark.render
def test_the_finder_draws_the_offer_mark_on_a_line_with_a_number(mount):
    page, errors = finder(mount, "espn")
    FinderPage(page).wait_offers()
    assert drawn_beside_a_number(MarksPage(page), "lboard.offer.mark"), "the finder does not draw lboard.offer.mark beside a number"
    assert errors == []


@pytest.mark.render
def test_the_edit_page_draws_the_chip_mark_on_a_player_with_a_number(mount):
    page, errors = finder(mount, "espn")
    FinderPage(page).wait_offers()
    FinderPage(page).open_edit(0)
    assert drawn_beside_a_number(MarksPage(page), "lboard.chip.mark"), "the edit page does not draw lboard.chip.mark beside a number"
    assert errors == []


@pytest.mark.render
def test_trade_history_draws_the_due_mark_on_the_worst_traders_line(mount):
    page, errors = mount("tradehist", size=(360, 800), init=(pick_script("yahoo"),))
    assert drawn_beside_a_number(MarksPage(page), "trades.lead.dueMark"), "Trade history does not draw trades.lead.dueMark beside a number"
    assert errors == []


@pytest.mark.render
def test_an_opened_slips_game_draws_the_matchup_mark_on_a_player_with_a_number(mount):
    slips, errors = SlipsPage.open(mount, "morning")
    slips.toggle_game(SLIPS_GAME)
    assert drawn_beside_a_number(MarksPage(slips.page), "slips.flag.mark"), "Slips does not draw slips.flag.mark beside a number"
    assert errors == []


@pytest.mark.render
def test_a_dossier_draws_the_travel_mark_on_the_zones_line_with_a_number(mount):
    page, errors = mount("preview", size=(360, 800))
    PreviewPage(page).show_game(TRAVEL_GAME)
    assert drawn_beside_a_number(MarksPage(page), "preview.travel.mark"), "Preview does not draw preview.travel.mark beside a number"
    assert errors == []

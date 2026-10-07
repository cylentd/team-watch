"""A Watch card whose availability is unknown draws no blank proof stats (2026-10-07: it drew three "—"
cells). A stat with no value is not drawn; with none left the stats row is not drawn. The choice of
which stats to keep is test_js_proofshow.py. Component layer: `mount`, `WaiverCards`."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.waiver_cards import WaiverCards

pytestmark = pytest.mark.render


def test_a_card_whose_back_holds_nothing_new_does_not_flip(mount):
    page, errors = mount("waivers", size=(360, 660))
    got = WaiverCards(page).unknown_card_faces({"yahoo": {"status": "unknown", "lane": None}})
    assert got == {"backs": 0, "flips": 0, "opens": 1, "front_others": 0}
    assert errors == []


def test_leagues_that_repeat_the_headers_status_draw_no_line_and_no_back(mount):
    page, errors = mount("waivers", size=(360, 660))
    lg = {"status": "unknown", "lane": None}
    got = WaiverCards(page).unknown_card_faces({"yahoo": lg, "espn": lg, "ayo": lg})
    assert got == {"backs": 0, "flips": 0, "opens": 1, "front_others": 0}
    assert errors == []


def test_a_league_with_another_status_shows_alone_on_the_front(mount):
    page, errors = mount("waivers", size=(360, 660))
    lg = {"status": "unknown", "lane": None}
    got = WaiverCards(page).unknown_card_faces({"yahoo": lg, "espn": {"status": "rostered", "lane": None}, "ayo": lg})
    assert got == {"backs": 0, "flips": 0, "opens": 1, "front_others": 1}
    assert errors == []


def test_an_unknown_availability_card_draws_no_blank_stat(mount):
    page, errors = mount("waivers", size=(360, 660))
    got = WaiverCards(page).unknown_card_stats("WR", "nobody-with-usage")
    assert got == {"values": [], "row": 0}
    assert errors == []

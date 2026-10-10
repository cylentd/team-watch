"""Slips' Anytime TDs card at 360px (2026-10-09): where it sits, what a tap does, what is folded, when the wait strip
shows. The words and the order are Node-tested (test_js_tdcard.py); this file holds the drawing and the taps.
The fixture's morning tab is CIN @ NYJ: LOCK Brown, Higgins, Chase, Hall; VALUE Wilson; MORE Gesicki; LONG Iosivas.
Only Brown of those has an anytime-TD line in the fixture's props, so only his row has a +."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.slips_td import TdCard

pytestmark = pytest.mark.req("Parlay and DFS", ac="Anytime TDs card")

FIRST_SCREEN = 800


@pytest.fixture
def card(mount):
    c, errors = TdCard.open(mount, "morning")
    yield c
    assert errors == []


def test_the_card_leads_with_the_books_favourite_on_the_first_screen(card):
    assert card.visible()
    # LOCK shows three, then "1 more" (Breece Hall); VALUE's Wilson follows
    assert card.names() == ["Chase Brown", "Tee Higgins", "Ja'Marr Chase", "Garrett Wilson"]
    assert card.first_row_top() < FIRST_SCREEN
    assert card.record() == "Book 55%+ went 38-18 in weeks 1-4"
    assert card.slips.fits()


def test_the_plus_adds_his_anytime_td_and_again_takes_it_off(card):
    card.add(0)
    assert card.slips.slip() == [["Chase Brown", "TD", "higher"]]
    card.add(0)
    assert card.slips.slip() == []


def test_a_name_opens_the_sheet_with_the_checks_and_our_model_last(card):
    card.open_row(0)
    text = card.sheet_text().lower()   # section heads are set in capitals by CSS
    assert "why he could score · 3 of 6" in text
    assert text.index("second opinion") > text.index("his work, last 3 games")
    assert card.has_ours() and "our model: 58%" in text
    card.close_sheet()


def test_more_and_long_are_folded_until_tapped(card):
    assert card.expanded("MORE") == "false" and card.group_rows("MORE") == 0
    assert card.expanded("LONG") == "false" and card.group_rows("LONG") == 0
    card.unfold("MORE")
    assert card.expanded("MORE") == "true" and card.group_rows("MORE") == 1


def test_the_wait_strip_shows_only_while_claude_is_pending(card):
    assert card.wait_line().startswith("Our picks arrive about")
    card.drop_pending()
    assert card.wait_line() is None

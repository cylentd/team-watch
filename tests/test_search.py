"""Player search: the sheet, mounted over a view (component layer; every locator in tests/pages/search.py).

The index and the matcher (data/search.js) are tests/test_js_search.py, in Node. What is left here is what
the reader sees and does: `/` and Escape on a desktop, and the phone's flow from the bar's slot to a
profile and back. Search is not a view, so these mount Ranks and drive the sheet over it. The fixture
carries Tee Higgins (WR, CIN) on the rosters.
"""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.search import SearchPage

pytestmark = pytest.mark.render

PHONE = (360, 780)
DESK = (1280, 900)


def test_slash_opens_and_escape_closes_on_a_desktop(mount):
    page, errors = mount("ranks", size=DESK)
    search = SearchPage(page)
    search.press_slash()
    assert search.is_open()
    assert search.focused_id() == "search-q"
    assert search.query() == ""   # the slash opened it; it was not typed
    search.press_escape()
    assert search.is_closed()
    search.wait_history_clear()   # its history entry went with it
    assert search.history_state() is None
    assert errors == []


def test_the_phone_flow(mount):
    """Open from the nav bar, type, tap the best match, then Back twice: profile, then search."""
    page, errors = mount("ranks", size=PHONE)
    search = SearchPage(page)
    hash_before = search.hash()
    search.tap_nav_slot()
    assert search.focused_id() == "search-q"
    assert search.caption() == "YOUR ROSTER"

    search.type("higg")
    assert "Higgins" in search.row_text(0)
    # Best match sits right on top of the input, nearest the thumb; the rest stack upward.
    boxes = search.boxes()
    bar, rows = boxes["bar"], boxes["rows"]
    assert abs(rows[0]["y"] + rows[0]["height"] - bar["y"]) < 12
    assert all(r["y"] <= rows[0]["y"] for r in rows)
    assert search.fits_width()

    search.tap_row(0)
    assert "HIGGINS" in search.profile.title().upper()
    assert search.profile.is_open()

    search.go_back()
    search.wait_profile_closed()
    assert search.is_open()
    assert search.query() == "higg"   # the query survives the profile

    search.go_back()
    search.wait_closed()
    assert search.hash() == hash_before   # Back closed layers, not the view

    search.tap_nav_slot()   # and he is now the first recent
    assert search.caption() == "RECENT"
    assert "Higgins" in search.row_text(0)
    assert errors == []


def test_nothing_found_says_why(mount):
    page, errors = mount("ranks", size=PHONE)
    search = SearchPage(page)
    search.tap_nav_slot()
    search.type("zzqx")
    assert search.none_text() == "No “zzqx” in this week’s data"
    assert errors == []

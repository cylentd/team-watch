"""S16 (David approved 2026-10-31), the Search half: a reader's search finds the players of the league his team is in,
and the result opens that player.

The fixture's three leagues each hold one surname no other roster does (Yahoo's Chat Take the Wheel: Joe Burrow; ESPN's
Purdy Big in Japan: George Kittle; AYO's Taylor Made for Sundays: Justin Jefferson; espn_rosters.json, ayo_rosters.json,
league_rosters.json). The reader picks the team, searches the surname, and taps the top result."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.league_chip import pick_script
from pages.search import SearchPage

pytestmark = pytest.mark.render

# (reader's TEAMS key, the one surname only his league's roster holds)
LEAGUES = [("yahoo", "Burrow"), ("espn", "Kittle"), ("ayo", "Jefferson")]


@pytest.mark.parametrize("team,surname", LEAGUES)
def test_s16_search_finds_the_picked_leagues_player_and_opens_him(mount, team, surname):
    page, errors = mount("ranks", size=(360, 780), init=(pick_script(team),))
    search = SearchPage(page)
    search.tap_nav_slot()
    search.type(surname.lower())
    assert surname in search.row_text(0), f"{surname} is the top result for his own league's reader"
    search.tap_row(0)
    assert search.profile.title().upper().endswith(surname.upper())
    assert errors == []

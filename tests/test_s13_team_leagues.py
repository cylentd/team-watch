"""S13 (David approved 2026-10-31): a reader who has picked a team opens Roster or Trades, and the view draws that team's
own league; Trades' offers come from that reader's team, not another's.

The fixture holds three leagues with three different readers: Yahoo's Chat Take the Wheel (Joe Burrow), ESPN's Purdy Big in
Japan (George Kittle; offers to Run It Back), AYO's Taylor Made for Sundays (Justin Jefferson; offers to Don Wick). ESPN's
other team, Run It Back, has offers of its own, all to Purdy. Each expected name below is one of those fixture files'
rows (espn_rosters.json, ayo_rosters.json, league_rosters.json, trade_offers.json)."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.finder import FinderPage, finder
from pages.league_chip import LeagueChip, pick_script
from pages.roster import RosterRows

pytestmark = pytest.mark.render

# (reader's TEAMS key, the one surname only his league's roster holds, the other two leagues' surnames)
ROSTERS = [
    ("yahoo", "Burrow", ("Kittle", "Jefferson")),
    ("espn", "Kittle", ("Burrow", "Jefferson")),
    ("ayo", "Jefferson", ("Burrow", "Kittle")),
]
# (reader's TEAMS key, who every offer on his Trades page is with)
OFFERS = [
    ("espn", "Run It Back"),
    ("espn-run-it-back", "Purdy Big in Japan"),
    ("ayo", "Don Wick"),
]


@pytest.mark.parametrize("team,own,others", ROSTERS)
def test_s13_roster_draws_the_picked_teams_league_and_no_other(mount, team, own, others):
    page, errors = mount("roster", size=(390, 844), init=(pick_script(team),))
    text = " ".join(RosterRows(page).texts())
    assert own in text, f"the picked team's own player ({own}) is on his Roster"
    assert [name for name in others if name in text] == [], "no player only another league's team holds"
    assert errors == []


@pytest.mark.parametrize("team,partner", OFFERS)
def test_s13_trades_offers_are_the_picked_teams_own(mount, team, partner):
    page, errors = finder(mount, team)
    finder_page = FinderPage(page)
    finder_page.wait_offers()
    assert finder_page.partners() and set(finder_page.partners()) == {partner}
    assert LeagueChip(page).team_name() != partner, "the partner is the other side of the offer, never the reader"
    assert errors == []

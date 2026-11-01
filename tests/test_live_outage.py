"""S12: a game is in progress, a reader opens Live, and ESPN's scoreboard (the feed behind every game's
quarter and clock) goes down. Live keeps drawing and shows no broken value.

David kept S12 as must-never-break: scores, clock and the game sheet draw from the live feed, and the
sheet closes by X, scrim or Back (test_live_modal.py). The feed was always stubbed, so an outage had no
test. Two cases here: the feed down from the first load, and a feed that works and then dies mid-session.

The poll is made by calling `gdClockFetch()` and repainting (pages/live_outage.py says why), never by
waiting for a timer. Component tests (Live mounted, tests/component.py; every locator in tests/pages/).
"""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.live_outage import LiveFeedPage, event

pytestmark = pytest.mark.render

IN_A_GAME = "Date.now = () => Date.parse(LIVE_SCHEDULE.games[0].kickoff) + 3600e3"   # an hour after the first kickoff
OUTAGES = {"request fails": None, "ESPN answers 503": (503, "service unavailable"),
           "answer is not JSON": (200, "<html>maintenance</html>"), "answer has no events": (200, "{}")}


@pytest.fixture
def live(mount):
    """Live on the NFL tab, a game in progress, with the scoreboard route ours until the test ends."""
    page, errors = LiveFeedPage.on_games_tab(mount)
    page.page.evaluate(IN_A_GAME)
    yield page, errors
    page.release()


@pytest.mark.parametrize("how", OUTAGES)
@pytest.mark.req("Live", ac="a feed that is down from the first load leaves Live drawn")
def test_live_draws_with_the_feed_down_from_the_first_load(live, how):
    page, errors = live
    page.feed_answers(OUTAGES[how])
    page.poll()
    assert page.live_tile_count() == 1, "the game in progress is still a live tile"
    assert page.tile_scores() != [], "the scores still draw"
    assert page.broken_words() == []
    assert errors == []


@pytest.mark.req("Live", ac="the last good scores stay when the feed dies mid-session")
def test_the_last_good_clock_and_scores_stay_when_the_feed_dies(live):
    page, errors = live
    away, home = page.live_game()
    page.feed_works([event(away, home, quarter="3", clock="4:12")])
    page.poll()
    before = (page.first_live_tile_clock(), page.tile_scores())
    assert "Q3 4:12" in before[0], before
    page.feed_dies()
    page.poll()
    assert (page.first_live_tile_clock(), page.tile_scores()) == before
    assert page.broken_words() == []
    assert errors == []

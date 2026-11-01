"""Live while ESPN's scoreboard is down (S12): the feed that gives every game its quarter and clock.

`LiveFeedPage` is `LiveTabsPage` (pages/live_tabs.py) plus a scoreboard the test controls. `mount` aborts
every http(s) request, so the page's own poll never reaches ESPN; this page object answers the
scoreboard URL itself (a route added after mount's, which Playwright tries first) and makes the poll
by calling `gdClockFetch()`, the one function that reads the feed, then repainting the way `paintLive`
does after a poll. The poll's wiring (`gdFetch`) refuses a page opened from a file, which is why it is
not the entry point.

Reads return plain data; no method asserts.
"""
import json
import re

from pages.live_tabs import LiveTabsPage

SCOREBOARD = re.compile(r"^https://site\.api\.espn\.com/apis/site/v2/sports/football/nfl/scoreboard")
CORS = {"Access-Control-Allow-Origin": "*"}      # the page is a file: its origin is null
BROKEN_WORDS = re.compile(r"undefined|NaN|\bnull\b|\[object")
IN_GAME = {"DET": "in_game", "SEA": "in_game"}     # the first game of the planted week 2
POLL = "async () => { await gdClockFetch(); paintLive(); }"
VIEW_TEXT = "document.getElementById('view').innerText"


def event(away, home, quarter="3", clock="4:12"):
    """One game of ESPN's scoreboard, in play at `quarter` with `clock` left (the shape gdClockShape reads)."""
    club = lambda i, code: {"team": {"id": str(i), "abbreviation": code}}
    return {"competitions": [{"status": {"period": int(quarter), "displayClock": clock,
                                         "type": {"state": "in", "name": "STATUS_IN_PROGRESS", "shortDetail": ""}},
                              "competitors": [club(1, away), club(2, home)]}]}


class LiveFeedPage(LiveTabsPage):
    def __init__(self, page):
        super().__init__(page)
        self.answer = None                      # None: the request fails; a (status, body) pair: it is answered
        self._route = self._serve               # the same object to unroute

    @classmethod
    def on_games_tab(cls, mount, size=(390, 844)):
        """Live on the planted week 2, DET at SEA in progress (Sleeper says in_game), the NFL tab open.
        Returns (LiveFeedPage, the page's errors)."""
        live, errors = cls.open_league(mount, size=size, states=IN_GAME)
        live.page.route(SCOREBOARD, live._route)
        live.open_tab("games")
        live.tile_count()
        return live, errors

    def _serve(self, route):
        if self.answer is None:
            route.abort("failed")
        else:
            status, body = self.answer
            route.fulfill(status=status, headers=CORS, content_type="application/json", body=body)

    def release(self):
        """The test is over: the page is the module's, and the next mount must find no route of ours on it."""
        self.page.unroute(SCOREBOARD, self._route)

    # ---- the feed ----

    def feed_works(self, events):
        self.answer = (200, json.dumps({"events": events}))

    def feed_answers(self, answer):
        """`answer` is a (status, body) pair, or None for a request that fails."""
        self.answer = answer

    def feed_dies(self):
        self.feed_answers(None)

    def poll(self):
        """Live's scoreboard poll, then the repaint it ends in. Returns when the answer (or the failure) is handled."""
        self.page.evaluate(POLL)

    # ---- what a reader sees ----

    def view_text(self):
        return self.page.evaluate(VIEW_TEXT)

    def broken_words(self):
        """Every placeholder-looking word on the view (undefined, NaN, null, [object ...])."""
        return BROKEN_WORDS.findall(self.view_text())

    def first_live_tile_clock(self):
        """The first live tile's own text, the quarter and clock among it."""
        return self._tiles.and_(self.page.locator(".in")).first.inner_text()

    def live_game(self):
        """[away, home] of the first live tile's game."""
        return self._tiles.and_(self.page.locator(".in")).first.evaluate("e => e.dataset.gdnfl.split(',').slice(1)")

    def live_tile_count(self):
        return self._tiles.and_(self.page.locator(".in")).count()

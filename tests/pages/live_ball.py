"""Live's NFL tab, the tile of a game that is on: who has the ball, the down and distance, and the red-zone tag
(design/src/js/surface/live/nflnow.js, from the scoreboard's `situation`; verified live 2026-10-05).

`LiveBallPage` is `LiveTabsPage` (pages/live_tabs.py) with what a test of the ball and the red zone plants and reads.
Every locator is here, data-testid first (`live-ball`, `live-sit`, `live-sit-down`, `live-red-zone`, test hooks only);
the tile is the tabs' own (`live-tile`) with its state word `in` joined by `and_`.

Reads return plain data; no method asserts. A method that plants state draws again (`paintLive`).
"""
from pages.live_tabs import LiveTabsPage

# ESPN's scoreboard says SEA has the ball, 3rd & 4 at DET 15 (inside the 20), then 1st & 10 at SEA 35 (outside it)
RED_ZONE_SITUATION = """() => { const g = {state: 'in', q: 3, clock: '4:12', half: false, detail: '', clubs: ['DET', 'SEA'],
    sit: {ball: 'SEA', dd: '3rd & 4 at DET 15', short: '3rd & 4', red: true, ytez: 15}};
  GD_CLOCK = {DET: g, SEA: g}; }"""
OPEN_FIELD_SITUATION = "() => { GD_CLOCK.DET.sit = GD_CLOCK.SEA.sit = {ball: 'SEA', dd: '1st & 10 at SEA 35', short: '1st & 10', red: false, ytez: 65}; }"


class LiveBallPage(LiveTabsPage):
    # ---- NFL: who has the ball, and the red zone (the scoreboard's `situation`) ----

    def plant_ball_in_the_red_zone(self):
        """SEA has the ball, 3rd & 4 at DET 15, on both clubs' game; Live draws again."""
        self.page.evaluate(RED_ZONE_SITUATION)
        self.repaint()

    def plant_ball_outside_the_red_zone(self):
        """The same ball, 1st & 10 at SEA 35; Live draws again."""
        self.page.evaluate(OPEN_FIELD_SITUATION)
        self.repaint()

    def in_tile_ball_count(self):
        """Footballs on the tile of the game that is on."""
        return self._in_tile().get_by_test_id("live-ball").count()

    def in_tile_sit_count(self):
        """Down-and-distance lines on the tile of the game that is on."""
        return self._in_tile().get_by_test_id("live-sit").count()

    def in_tile_ball_by_club(self):
        """Footballs beside each club's row on that tile, top row first."""
        clubs = self._in_tile().get_by_test_id("live-tile-club")
        return [clubs.nth(0).get_by_test_id("live-ball").count(), clubs.nth(1).get_by_test_id("live-ball").count()]

    def in_tile_ball_label(self):
        return self._in_tile().get_by_test_id("live-ball").get_attribute("aria-label")

    def in_tile_down_text(self):
        return self._in_tile().get_by_test_id("live-sit-down").inner_text()

    def in_tile_down_fits(self):
        """The down is never cut off: its text is no wider than its box."""
        return self._in_tile().get_by_test_id("live-sit-down").evaluate("e => e.scrollWidth <= e.clientWidth")

    def in_tile_down_and_zone_boxes(self):
        """[the down's box, the red-zone tag's box], each {x, y, width, height}."""
        return [self._in_tile().get_by_test_id("live-sit-down").bounding_box(),
                self._in_tile().get_by_test_id("live-red-zone").bounding_box()]

    def in_tile_zone_text(self):
        return self._in_tile().get_by_test_id("live-red-zone").inner_text()

    def in_tile_zone_count(self):
        return self._in_tile().get_by_test_id("live-red-zone").count()

    def in_tile_box(self):
        return self._in_tile().bounding_box()

    def _in_tile(self):
        return self._tiles.and_(self.page.locator(".in"))


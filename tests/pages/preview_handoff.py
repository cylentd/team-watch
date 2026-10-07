"""Preview's hand-off to Slips (design/src/js/surface/preview/handoff.js): the dossier's "From this game to your slip"
section, its sides, and the button that opens Slips. `PreviewPage.handoff` is this class.

The section and its buttons are `preview-slip-*` data-testids; a line's own parts (`parlay-line-item`,
`parlay-line-market`, `parlay-side`) are drawn by Slips' line item and keep Slips' ids. The tray, the slip and the board
are `ParlayPage`'s (`slips()`, `tray_drawn()`): Preview draws Slips' tray under itself.
"""
from pages.parlay import ParlayPage

AS_SEA_SF = """() => { const g = LIVE_PREVIEW.games[3]; g.away = 'SEA'; g.home = 'SF';
  g.take.players = [{n: 'George Kittle', slug: 'george-kittle', pos: 'TE', team: 'SF', proj: 9.1, call: 'up',
                     why: 'Seattle allows the most TE points.'}];
  PV_I = 3; PV_OPEN = true; render(); }"""


class PreviewHandoff:
    def __init__(self, page):
        self.page = page
        self._section = page.get_by_test_id("preview-section").and_(page.locator(".handoff"))

    # ---- what a reader does ----

    def pick(self, i, side):
        """Tap `side` ("higher" or "lower") of PROPS line `i` in the section."""
        self._section.get_by_test_id("parlay-side").and_(
            self.page.locator(f"[data-slpick='{i}'][data-side='{side}']")).click()

    def tap_slip_all(self):
        self.page.get_by_test_id("preview-slip-all").click()

    # ---- what a test plants ----

    def plant_game_as_sea_sf(self):
        """Game 3 becomes the props slate's SEA @ SF, its take naming George Kittle, and its dossier is open."""
        self.page.evaluate(AS_SEA_SF)

    def open_game_for_real(self, i):
        """pvClose then pvOpen: the real open, which pushes the dossier's history entry."""
        self.page.evaluate(f"pvClose(); pvOpen({i})")

    # ---- what a reader sees ----

    def title(self):
        return self._section.get_by_test_id("preview-section-title").inner_text()

    def players(self):
        return self._section.get_by_test_id("preview-slip-player").count()

    def lines(self):
        return self._section.get_by_test_id("parlay-line-item").count()

    def market(self):
        return self._section.get_by_test_id("parlay-line-market").inner_text()

    def lines_label(self):
        return self._section.get_by_test_id("preview-slip-lines").inner_text()

    def marked_count(self):
        """Players in the section marked as on the slip."""
        return self._section.get_by_test_id("preview-slip-on").count()

    def props_index(self, slug, mkt):
        return self.page.evaluate("([s, m]) => PROPS.findIndex(p => p.slug === s && p.mkt === m)", [slug, mkt])

    def slip_all_text(self):
        return self.page.get_by_test_id("preview-slip-all").inner_text()

    def players_with_lines(self, i):
        """How many distinct players the Slips board holds for game `i`."""
        return self.page.evaluate(f"new Set(pvSlipRows(LIVE_PREVIEW.games[{i}]).map(([p]) => p.slug)).size")

    def tray_drawn(self):
        """The slip's tray is Slips' own, drawn under Preview once a pick is in it."""
        return ParlayPage(self.page).tray_drawn()

    def dossier_open_state(self):
        return self.page.evaluate("PV_OPEN")

    def wait_for_dossier_state_closed(self):
        self.page.wait_for_function("PV_OPEN === false")

    def slips(self):
        """The Slips side: its page object, for the tray, the slip and the board."""
        return ParlayPage(self.page)

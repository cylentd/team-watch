"""Stats > Ranks, boom and bust (design/src/js/surface/ranks/odds.js, 2026-11-13, density redo): the sort chips, each
sorted row's answer, and the one-line explainer with its ⓘ.

The rest of Ranks (positions, rows, tiers) is pages/ranks.py's; this object only adds what odds.js draws.
"""


class RanksOddsPage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._sorts, self._sort_row, self._rows = tid("ranks-sort"), tid("ranks-sort-row"), tid("ranks-row")
        self._sub, self._info, self._more = tid("ranks-sub"), tid("ranks-info"), tid("ranks-more")

    # ---- what a reader does ----

    def sort_by(self, sort):
        """Tap a sort chip: "pts" (Projection), "boom" (Upside) or "bust" (Safe)."""
        self._sorts.and_(self.page.locator(f"[data-rksort='{sort}']")).click()
        self.page.wait_for_selector(f"[data-rksort='{sort}'][aria-pressed='true']")

    def tap_info(self):
        self._info.click()

    def leave_and_come_back(self):
        """Open another view, then Ranks again, as the nav would."""
        self.page.evaluate("() => { navGo('board'); navGo('ranks'); }")

    def plant_no_odds(self):
        """Null every row's boom and bust, as a projections file from before them ships, and draw again."""
        self.page.evaluate("() => { [...LIVE_RANKS.rows, ...LIVE_RANKS.flex].forEach(r => { r.boom = null; r.bust = null; }); render(); }")

    # ---- what a reader sees ----

    def sorts(self):
        """The sort chips' labels, [] when the row is not drawn."""
        return [s.strip() for s in self._sorts.all_inner_texts()]

    def pressed(self):
        return self._sorts.and_(self.page.locator("[aria-pressed='true']")).inner_text().strip()

    def answers(self):
        """Each row in order: slug, the boom or bust percent it leads with (None on a Projection row), the small line."""
        return self._rows.evaluate_all("""rs => rs.map(r => {
          const a = r.querySelector('[data-testid="ranks-boom"], [data-testid="ranks-bust"]'), p = r.querySelector('[data-testid="ranks-ans-pts"]');
          return [r.dataset.rkopen, a ? a.textContent : null, p ? p.textContent : null];
        })""")

    def row_shape(self):
        """Per row: lines in the name column, and whether a range or a matchup delta is drawn."""
        return self._rows.evaluate_all("""rs => rs.map(r => [r.querySelector('.rk-who').children.length,
          !!r.querySelector('.rk-pts > .rk-rng:not([data-testid])'), !!r.querySelector('[data-testid="ranks-mx"]')])""")

    def line(self):
        """The explainer's one line, without its ⓘ."""
        return self._sub.evaluate("e => e.firstChild.textContent")

    def line_count(self):
        """How many lines the explainer's words take at this width."""
        return self._sub.evaluate("e => { const r = document.createRange(); r.selectNodeContents(e.firstChild); return r.getClientRects().length; }")

    def more(self):
        """The full definition behind the ⓘ, or None while it is closed."""
        return self._more.inner_text() if self._more.is_visible() else None

    def row_fit(self):
        """Every row at its width: no name cut by an ellipsis."""
        return self._rows.evaluate_all("rs => rs.every(r => { const nm = r.querySelector('.rk-nmt'); return nm.scrollWidth <= nm.clientWidth; })")

    def sort_row_fits(self):
        return self._sort_row.evaluate("e => e.scrollWidth <= e.clientWidth")

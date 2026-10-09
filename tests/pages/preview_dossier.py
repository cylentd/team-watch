"""Preview's game page after ledger #82 (design/src/js/surface/preview/dossier.js, 2026-10-09, storyboard draft A
"Ledger"): the players first, each with his yards and touchdown chance; the bets as Vegas, ours and the pick; the
story's first paragraph with the rest one tap away; the research under it.

`PreviewPage` (pages/preview.py) still opens and walks the games; this class reads what ledger #82 drew. Locators are
`preview-*` data-testids; the state a part wears (a closed `<details>`, a dim column) is read off the element."""


class PreviewDossier:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._article, self._bets, self._rows = tid("preview-article"), tid("preview-bets"), tid("preview-player-row")

    # ---- what a reader does ----

    def tap_yards(self, n):
        """Player `n`'s yards: the way to his lines."""
        self._rows.nth(n).get_by_test_id("preview-player-yds").click()

    def open_rest_of_story(self):
        self.page.get_by_test_id("preview-more").locator("summary").click()

    # ---- what a test plants ----

    def spy_on_lines_sheet(self):
        """The Slips player sheet is Bets' own: replace its opener with one that records the slug."""
        self.page.evaluate("() => { window.__sheet = []; playerSheetOpen = s => window.__sheet.push(s); }")

    # ---- what a reader sees ----

    def parts(self):
        """The classes of the article's children, in order."""
        return self._article.evaluate("a => [...a.children].map(c => c.className)")

    def player_rows(self):
        """[name, yards, touchdown chance] per player row, whitespace squashed."""
        return self._rows.evaluate_all("""rs => rs.map(r => ['preview-player-name', 'preview-player-yds-n', 'preview-player-td']
          .map(t => { const e = r.querySelector(`[data-testid="${t}"]`); return e ? e.innerText.replace(/\\s+/g, ' ').trim() : null; }))""")

    def yards_is_button(self, n):
        return self._rows.nth(n).get_by_test_id("preview-player-yds").evaluate("e => e.tagName") == "BUTTON"

    def sheets_opened(self):
        return self.page.evaluate("window.__sheet")

    def bet_heads(self):
        return self._bets.locator("thead th").evaluate_all("hs => hs.map(h => h.innerText.trim())")

    def bet_rows(self):
        """Each bet's cells: [label, Vegas, ours, pick], whitespace squashed."""
        return self._bets.get_by_test_id("preview-bet").evaluate_all(
            "rs => rs.map(r => [...r.children].map(c => c.innerText.replace(/\\s+/g, ' ').trim()))")

    def visible_deks(self):
        return self.page.get_by_test_id("preview-dek").evaluate_all(
            "ps => ps.filter(p => p.checkVisibility({contentVisibilityAuto: true})).map(p => p.innerText.trim())")

    def all_deks(self):
        return self.page.get_by_test_id("preview-dek").evaluate_all("ps => ps.map(p => p.textContent.trim())")

    def more_count(self):
        return self.page.get_by_test_id("preview-more").count()

    def risk_visible(self):
        return self.page.get_by_test_id("preview-risk").is_visible()

    def matchup_grid(self):
        """The defense table as rows of cells: the head row, then one row per offense."""
        return self.page.get_by_test_id("preview-matchup").locator("tr").evaluate_all(
            "rs => rs.map(r => [...r.children].map(c => c.innerText.replace(/\\s+/g, ' ').trim()))")

    def dim_heads(self):
        return self.page.get_by_test_id("preview-matchup").locator("th.dim").all_inner_texts()

    def slips_button_count(self):
        return self.page.get_by_test_id("preview-slip-all").count()

    def article_height(self):
        return self._article.evaluate("a => a.getBoundingClientRect().height")

    def game(self, i):
        """LIVE_PREVIEW's game `i`, the input the page draws."""
        return self.page.evaluate(f"LIVE_PREVIEW.games[{i}]")

    def lines_of(self, slug):
        """The PROPS rows (the input) for one player."""
        return self.page.evaluate("s => PROPS.filter(p => p.slug === s)", slug)

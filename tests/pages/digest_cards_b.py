"""The Digest's day cards, read one card at a time (2026-10-06, Digest by day): Claude vs Vegas, Start in this game,
SMASH, Bold calls, Top calls and Weather.

`DigestCardsPage` is `DigestDayPage` scoped to a card by its plan id (`data-dgcard`): its rows, its table, its
foot, its link. Locators by data-testid (`digest-card*`, `digest-r*`, `digest-vs*`, `digest-smash-more`); a card
holds its own rows, so a second card on the page never leaks into a read. Reads return plain data and never assert.
"""
from pages.digest_day import DigestDayPage

NORM = "e => e.textContent.replace(/\\s+/g, ' ').trim()"
ROWS = r"""rs => rs.map(r => { const q = id => r.querySelector('[data-testid="' + id + '"]'),
    norm = s => s.replace(/\s+/g, ' ').trim(), p = q('digest-r-pill'), b = q('digest-r-btn'), rt = r.querySelector('.dg-r-tile');
  return {name: q('digest-r-name').textContent, meta: norm(r.querySelector('.dg-r-m').textContent),
          answer: norm(q('digest-r-answer').innerText), pill: p ? p.textContent : null, mark: p ? p.getAttribute('title') : null,
          tile: rt ? rt.textContent : null, delta: (r.querySelector('.dg-r-d') || {className: ''}).className.split(' ').pop(),
          tag: b.tagName, expanded: b.getAttribute('aria-expanded'),
          research: [...r.querySelectorAll('[data-testid="digest-r-research"] dt')].map(dt => [dt.textContent, dt.nextElementSibling.textContent]),
          foot: (r.querySelector('.dg-r-foot') || {textContent: null}).textContent,
          open: !!r.querySelector('[data-testid="digest-r-research"]:not([hidden])')}; })"""
BETS = r"""rs => rs.map(r => { const c = r.querySelectorAll('th, td'), norm = s => s.replace(/\s+/g, ' ').trim();
  return {bet: norm(c[0].textContent), vegas: norm(c[1].textContent), claude: norm(c[2].textContent),
          claude_title: c[2].getAttribute('title'), chips: [...c[2].querySelectorAll('.pv-conf')].map(x => [x.textContent, x.getAttribute('title')])}; })"""
# The ctx a card is handed when the page holds none of its data: every block null.
NO_DATA = "{day: 'thu', plan: DG_PLAN[4], now: Date.now(), d: null, ss3: null, sos: null, def: null, preview: null, schedule: null, usage: null, ranks: null}"


class DigestCardsPage(DigestDayPage):

    def __init__(self, page):
        super().__init__(page)
        self._card = lambda cid: page.locator(f'[data-testid="digest-card"][data-dgcard="{cid}"]')

    # ---- planting (globals only; the clock is the page's, drawn again) ----

    def plant_game(self, at, away, home, kickoff):
        """The season schedule holds one game, `away` @ `home`, at the page's clock `at`."""
        self.plant_schedule(at, [{"away": away, "home": home, "kickoff": kickoff}])

    def plant_calm_week(self):
        """SEA's forecast made calm, so no game's weather moves scoring."""
        self.page.evaluate("() => { LIVE_WEATHER.teams.SEA.wind = '8 mph'; LIVE_WEATHER.teams.SEA.precip_pct = 10; render(); }")

    def plant_no_props(self):
        self.page.evaluate("() => { PROPS.length = 0; render(); }")

    def plant_no_preview_games(self):
        self.page.evaluate("() => { LIVE_PREVIEW.games = []; render(); }")

    def plant_bare_game(self):
        """The preview game of today holds neither a line nor a take: nothing to say, so no card."""
        self.page.evaluate("() => { LIVE_PREVIEW.games.forEach(g => { g.line = null; g.take = null; g.market_win = null; }); render(); }")

    def card_html_without_data(self, name):
        """What dgCard<name> returns for a ctx with every block null."""
        return self.page.evaluate(f"() => dgCard{name}({NO_DATA})")

    # ---- a card ----

    def has_card(self, cid):
        return self._card(cid).count() == 1

    def title(self, cid):
        return self._card(cid).get_by_test_id("digest-card-title").text_content().strip()

    def title_mark(self, cid):
        """The tooltip on the card's title word (SMASH carries its own mark), or None."""
        return self._card(cid).get_by_test_id("digest-card-title").evaluate("h => (h.querySelector('[title]') || {getAttribute: () => null}).getAttribute('title')")

    def more(self, cid):
        """The header link: the view it opens and its words, or None."""
        more = self._card(cid).get_by_test_id("digest-card-more")
        if not more.count():
            return None
        return {"leaf": more.get_attribute("data-dggo"), "text": more.inner_text().strip()}

    def foot(self, cid):
        foot = self._card(cid).get_by_test_id("digest-card-foot")
        return foot.evaluate(NORM) if foot.count() else None

    def rows(self, cid):
        """Per row: name, meta, answer as printed, pill word and mark, tile code, the change's direction, research pairs."""
        return self._card(cid).get_by_test_id("digest-r").evaluate_all(ROWS)

    def meta_cut(self, cid):
        """Per row: whether the meta line is cut short by the width it has (an ellipsis)."""
        return self._card(cid).locator(".dg-r-m").evaluate_all("ms => ms.map(m => m.scrollWidth > m.clientWidth)")

    def bets(self):
        """Claude vs Vegas: one entry per bet, Vegas beside Claude with the marks on Claude's side."""
        return self._card("vegas").get_by_test_id("digest-vs-bet").evaluate_all(BETS)

    def game_line(self):
        return self._card("vegas").get_by_test_id("digest-vs-game").inner_text().strip()

    def table_head(self):
        return self._card("vegas").locator("thead th").all_text_contents()

    # ---- taps ----

    def tap(self, cid, n):
        self._card(cid).get_by_test_id("digest-r-btn").nth(n).click()

    def tap_more(self, cid):
        self._card(cid).get_by_test_id("digest-card-more").click()

    def tap_foot_more(self, cid):
        self._card(cid).get_by_test_id("digest-smash-more").click()

    def foot_more(self, cid):
        """The foot's link to the rest of the list: {leaf, text}, or None."""
        link = self._card(cid).get_by_test_id("digest-smash-more")
        return {"leaf": link.get_attribute("data-dggo"), "text": link.inner_text().strip()} if link.count() else None

    def open_rows(self):
        """Every card's rows that show their research, as 'card:name'."""
        return self.page.evaluate("""() => [...document.querySelectorAll('[data-testid="digest-r"].open')]
          .map(r => r.closest('[data-dgcard]').dataset.dgcard + ':' + r.querySelector('[data-testid="digest-r-name"]').textContent)""")

    def view_leaf(self):
        return self.page.evaluate("() => location.hash")

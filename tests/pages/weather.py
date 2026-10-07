"""This week > Weather (design/src/js/surface/weather/): the games whose forecast moves scoring as cards, every
other game as one row.

Every Weather locator lives here, data-testid first (`weather-*`, test hooks only). `WeatherPage` is the view
mounted (tests/component.py). Reads return plain data; no method asserts.
"""

CARDS = r"""cs => cs.map(g => { const q = id => g.querySelector('[data-testid="' + id + '"]');
    const norm = s => s.replace(/\s+/g, ' ').trim();
    return {match: q('weather-card-match').textContent, cond: norm(q('weather-cond').textContent),
            fx: norm(q('weather-fx').textContent), text: g.textContent}; })"""
NORM_TEXT = r"es => es.map(e => e.textContent.replace(/\s+/g, ' ').trim())"
HIT_PARTS = """hs => hs.map(l => [...l.querySelectorAll('[data-testid="weather-hit-part"], [data-testid="weather-adj"]')]
    .map(s => s.textContent).join('|'))"""
PLANT = """([hits, gi]) => { const d = document.createElement('div'); d.dataset.testid = 'weather-probe';
    d.innerHTML = wtHitsHTML(hits, gi);
    document.querySelector('[data-testid="weather-view"]').appendChild(d); }"""
CALM_WEEK = """() => { const f = LIVE_WEATHER.teams.SEA, keep = [f.wind, f.precip_pct];
    f.wind = '8 mph'; f.precip_pct = 10; const h = wtViewHTML(); [f.wind, f.precip_pct] = keep; return h; }"""
ROSTER_CARD = """name => { const p = Object.values(TEAMS).flatMap(t => t.roster || []).find(x => x.n === name);
    return [cardWxAdj(p), cardBack(p, 9, 'espn', 0, cardGame(p.team))]; }"""
LOOPING = """() => document.getAnimations().filter(a => a.playState === 'running'
    && a.effect && a.effect.getTiming().iterations === Infinity).map(a => a.animationName)"""


class WeatherPage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._view, self._cards, self._rows = page.locator("#view"), tid("weather-card"), tid("weather-row")
        self._rule, self._hits, self._head = tid("weather-rule"), tid("weather-hit"), tid("weather-hits-head")
        self._probe, self._sky = tid("weather-probe"), tid("weather-sky")
        self._odds, self._tip, self._adj = tid("weather-odds"), tid("weather-odds-tip"), tid("weather-adj")

    # ---- what a reader sees ----

    def view_text(self):
        return self._view.inner_text()

    def details_count(self):
        return self._view.locator("details").count()

    def cards(self):
        """Each card: {match, cond, fx, text}, whitespace squeezed except in text."""
        return self._cards.evaluate_all(CARDS)

    def card_count(self):
        return self._cards.count()

    def row_count(self):
        return self._rows.count()

    def rows(self):
        """Every compact row's text on one line, in order drawn."""
        return self._rows.evaluate_all(NORM_TEXT)

    def rule_text(self):
        """The first section rule's heading and count, on one line."""
        return self._rule.first.inner_text().replace("\n", " ")

    def hits(self):
        """Who it hits, per card row: 'POS|name|TEAM|adj' joined by pipes."""
        return self._cards.get_by_test_id("weather-hit").evaluate_all(HIT_PARTS)

    def hits_head(self):
        return self._head.inner_text().replace("\n", " ")

    def calm_week_html(self):
        """wtViewHTML() with SEA's forecast set calm (wind 8 mph, 10% rain), the data put back after."""
        return self.page.evaluate(CALM_WEEK)

    def adj_html(self, wx):
        """wtAdjHTML(wx): the points a projection already moved for the weather, as markup."""
        return self.page.evaluate("wx => wtAdjHTML(wx)", wx)

    def roster_card_wx(self, name):
        """[cardWxAdj, cardBack] for a roster player: the Roster's card of him, which reads the same weather."""
        return self.page.evaluate(ROSTER_CARD, name)

    # ---- a planted hits list, to read a row the fixture's week does not hold ----

    def plant_hits(self, hits, gi):
        """Draw wtHitsHTML(hits, gi) under the view, in a probe of its own."""
        self.page.evaluate(PLANT, [hits, gi])

    def unplant(self):
        self.page.evaluate("document.querySelector('[data-testid=\"weather-probe\"]').remove()")

    def probe_hit(self, i):
        return self._probe.get_by_test_id("weather-hit").nth(i)

    def probe_odds_label(self, i):
        return self.probe_hit(i).get_by_test_id("weather-odds").inner_text()

    def probe_odds_count(self, i):
        return self.probe_hit(i).get_by_test_id("weather-odds").count()

    def probe_adj_count(self, i):
        return self.probe_hit(i).get_by_test_id("weather-adj").count()

    def odds_tip_visible(self):
        return self._probe.get_by_test_id("weather-odds-tip").is_visible()

    def open_odds_tip_by_keyboard(self, i):
        """Focus hit i's 'in the odds' label and press Enter."""
        self.probe_hit(i).get_by_test_id("weather-odds").focus()
        self.page.keyboard.press("Enter")

    def odds_tip_text(self):
        return self._probe.get_by_test_id("weather-odds-tip").inner_text()

    def press_escape(self):
        self.page.keyboard.press("Escape")

    # ---- the sky icon and its motion ----

    def sky_path_count(self, kind):
        """Strokes in the still icon of a kind: "wind" or "rain"."""
        return self._sky.and_(self.page.locator("." + kind)).locator("path").count()

    def first_sky_is_visible(self):
        return self._sky.first.is_visible()

    def looping_animations(self):
        """Names of the animations running forever (the wind's gusts, the rain's drops)."""
        return self.page.evaluate(LOOPING)

    def allow_motion(self):
        self.page.emulate_media(reduced_motion="no-preference")

    def reduce_motion(self):
        self.page.emulate_media(reduced_motion="reduce")

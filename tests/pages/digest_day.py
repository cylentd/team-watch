"""This week > Digest by day (2026-10-06): the day's banner, its cards and rows, and "Rest of the week".

`DigestDayPage` is `DigestPage` plus what a day plants (a clock, a preview game, a card that draws rows,
the recap's freshness) and reads (the banner's box and parts, the cards, a row's research, the strip).
Locators by data-testid (`digest-day`, `digest-card`, `digest-r*`, `digest-strip*`). See pages/digest.py.
"""
from pages.digest import DigestPage

# A Thursday game (Pacific) with Claude's take, planted into LIVE_PREVIEW for the clock's day.
PLANT_TNF = """(at) => { Date.now = () => Date.parse(at);
  LIVE_PREVIEW.games = [{...LIVE_PREVIEW.games[0], away: 'TB', home: 'DAL', kickoff: '2026-10-09T00:15:00Z',
    take: {...LIVE_PREVIEW.games[0].take, head: "Dallas wins, but Tampa's rookie keeps it close",
           pick: {winner: 'DAL', score: {DAL: 28, TB: 21}}}}];
  DG_CUT = null; render(); }"""

# One card (Tuesday's Top adds) drawn with three rows: two with research, one without. Replaces the stub.
# The first row is the packet's first hurt player, so his profile opens from the page's own lists.
PLANT_CARD = """() => { const p = LIVE_DIGEST.hurt[0];
  dgCardAdds = ctx => dgCardHTML({id: 'adds', title: 'Top adds', more: {leaf: 'waivers'}, foot: 'A foot.',
    body: [dgRowHTML('adds', {slug: p.slug, n: p.n, meta: 'BUF · vs LA',
             answer: {num: '23%', change: '+16 targets', dir: 'up'}, research: [['Snaps', '48% → 78%'], ['Week 4', '7 tgt']], foot: 'Untested'}),
           dgRowHTML('adds', {slug: 'trey-mcbride', n: 'Trey McBride', meta: 'ARI · vs DET', answer: {pill: 'SMASH', sub: 'TE1'},
             research: [['Our rank', 'TE1']]}),
           dgRowHTML('adds', {tile: 'DET', n: 'Detroit', meta: 'vs TEs', answer: {pill: 'OUT'}})].join('')});
  render(); }"""

# The recap at a clock after `edit` (a JS statement); every call starts from the fixture's recap and schedule.
PLANT_RECAP = """([at, js]) => { window.__r = window.__r ?? JSON.stringify(LIVE_RECAP); window.__s = window.__s ?? LIVE_SCHEDULE.games;
  Object.assign(LIVE_RECAP, JSON.parse(window.__r)); LIVE_SCHEDULE.games = window.__s;
  Date.now = () => Date.parse(at); DG_CUT = null; eval(js); render(); }"""


class DigestDayPage(DigestPage):

    def __init__(self, page):
        super().__init__(page)
        tid = page.get_by_test_id
        self._bn, self._strip, self._cards, self._rows = tid("digest-lead"), tid("digest-strip"), tid("digest-card"), tid("digest-r")

    # ---- planting ----

    def at(self, iso):
        """The page's clock at an ISO instant, drawn again."""
        self.page.evaluate("(at) => { Date.now = () => Date.parse(at); DG_CUT = null; render(); }", iso)

    def plant_tnf(self, at):
        self.page.evaluate(PLANT_TNF, at)

    def plant_card(self):
        self.page.evaluate(PLANT_CARD)

    def plant_hurt_across_positions(self):
        """Two hurt rows: a QB the packet lists first and a WR whose healthy projection is the higher (LIVE_RANKS has a
        row for each)."""
        self.page.evaluate("""() => { const base = LIVE_DIGEST.hurt[0];
          LIVE_RANKS.rows.push({slug: 'terry-qb', n: 'Terry Qb', pos: 'QB', team: base.team, pts: 12, rank: 9, tier: 3},
                               {slug: 'walt-wr', n: 'Walt Wr', pos: 'WR', team: base.team, pts: 18, rank: 2, tier: 1});
          LIVE_DIGEST.hurt = [{...base, slug: 'terry-qb', n: 'Terry Qb', pos: 'QB', rank: 1, status: 'Questionable'},
                              {...base, slug: 'walt-wr', n: 'Walt Wr', pos: 'WR', rank: 2, status: 'Doubtful'}];
          DG_CUT = null; render(); }""")

    def plant_recap(self, at, edit=""):
        self.page.evaluate(PLANT_RECAP, [at, edit])

    # ---- the banner ----

    def banner(self):
        """The banner's day label, its box at the page's size, and what sits at its right edge."""
        box = self._bn.bounding_box()
        side = "face" if self._bn.get_by_test_id("digest-lead-face").count() else "vs" if self._bn.get_by_test_id("digest-lead-vs").count() else ""
        return {"day": self.page.get_by_test_id("digest-day").inner_text(), "h": round(box["height"]),
                "w": round(box["width"]), "side": side, "day_attr": self._bn.get_attribute("data-dgday")}

    def lead_label(self):
        """The accessible name of the button laid over the banner (it opens the player's profile)."""
        return self.page.get_by_test_id("digest-lead-go").get_attribute("aria-label")

    def banner_vs(self):
        return self._bn.get_by_test_id("digest-lead-vs").inner_text().split()

    def banner_marks(self):
        """The tooltips on the headline and the fact line (an untested call says so), or None."""
        return {"head": self._head.get_attribute("title"),
                "fact": self.page.get_by_test_id("digest-lead-fact").get_attribute("title")}

    # ---- the cards and their rows ----

    def card_ids(self):
        return self._cards.evaluate_all("cs => cs.map(c => c.dataset.dgcard)")

    def card_title(self, n=0):
        return self._cards.nth(n).get_by_test_id("digest-card-title").text_content()

    def card_more(self, n=0):
        more = self._cards.nth(n).get_by_test_id("digest-card-more")
        return {"leaf": more.get_attribute("data-dggo"), "text": more.inner_text().strip()}

    def rows(self):
        """Per row: name, the answer as printed, the pill's tooltip, whether it opens research, and how."""
        return self._rows.evaluate_all("""rs => rs.map(r => { const b = r.querySelector('[data-testid="digest-r-btn"]'),
          p = r.querySelector('[data-testid="digest-r-pill"]');
          return {name: r.querySelector('[data-testid="digest-r-name"]').textContent,
                  answer: r.querySelector('[data-testid="digest-r-answer"]').innerText.replace(/\\s+/g, ' ').trim(),
                  mark: p ? p.getAttribute('title') : null, tag: b.tagName, expanded: b.getAttribute('aria-expanded'),
                  slug: b.dataset.dgslug || null}; })""")

    def tap_row(self, n):
        self._rows.nth(n).get_by_test_id("digest-r-btn").click()

    def key_row(self, n, key="Enter"):
        """Focus a row's button and press a key, as a keyboard reader would."""
        btn = self._rows.nth(n).get_by_test_id("digest-r-btn")
        btn.focus()
        self.page.keyboard.press(key)

    def research_open(self):
        """For each row with research: whether it is showing."""
        return self._rows.get_by_test_id("digest-r-research").evaluate_all("ds => ds.map(d => !d.hidden && d.offsetHeight > 0)")

    def research_text(self, n):
        return self._rows.nth(n).get_by_test_id("digest-r-research").inner_text()

    def tap_research_profile(self, n):
        self._rows.nth(n).get_by_test_id("digest-r-profile").click()

    def plant_schedule(self, at, games):
        """The season schedule holds only `games` ({away, home, kickoff, final}), at a clock."""
        self.page.evaluate("""([at, games]) => { Date.now = () => Date.parse(at);
          LIVE_SCHEDULE.games = games.map(g => ({week: LIVE_SCHEDULE.week, id: g.home, espn: '', final: false, ...g}));
          DG_CUT = null; render(); }""", [at, games])

    def plant_usage_movers(self, at, rows):
        """The usage movers block's rows (LIVE_USAGE_MOVERS is a const: its rows are replaced, not the block)."""
        self.page.evaluate("([at, rows]) => { Date.now = () => Date.parse(at); LIVE_USAGE_MOVERS.rows = rows; DG_CUT = null; render(); }", [at, rows])

    def first_hurt_name(self):
        return self.page.evaluate("LIVE_DIGEST.hurt[0].n")

    # ---- rest of the week ----

    def strip(self):
        """The strip's chips: the view each opens and its label."""
        if not self._strip.count():
            return []
        return self._strip.get_by_test_id("digest-strip-chip").evaluate_all("cs => cs.map(c => [c.dataset.dggo, c.textContent.trim()])")

    def tap_chip(self, leaf):
        self._strip.locator(f"[data-dggo='{leaf}']").click()

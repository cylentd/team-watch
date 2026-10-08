"""This week > Digest by day, the five cards of unit T3a (2026-10-06): Top adds, Out and who gains, Usage movers,
Defenses giving up the most, Game status / Injury watch.

`DigestCardsPage` is `DigestDayPage` plus a clock per weekday that lands inside the fixture packet's week, the
rows of one card by its id, and the plants these cards need (gains with nobody behind the starter, a news line,
Sleeper's adds). Locators by data-testid; the sparkline and the practice marks are found by class, because the
card draws them itself and gives them no test id of its own.
"""
from pages.digest_day import DigestDayPage

# A Pacific noon on each weekday: Tuesday and Wednesday of week 5 for the data that is not time-cut, and a Thursday
# and a Friday inside the fixture packet's week (Sep 27 kickoffs), so the hurt list is still whole.
CLOCK = {"tue": "2026-10-06T19:00:00Z", "wed": "2026-10-07T19:00:00Z",
         "thu": "2026-09-24T19:00:00Z", "fri": "2026-09-18T19:00:00Z"}

ROWS_JS = """rs => rs.map(r => { const q = s => r.querySelector(s), nm = q('[data-testid="digest-r-name"]'),
  a = q('[data-testid="digest-r-answer"]'), m = q('.dg-r-m'), mid = q('.dg-r-mid'), d = q('.dg-r-d'),
  p = q('[data-testid="digest-r-pill"]'), tile = q('.dg-r-tile');
  const dirs = d ? [...d.classList].filter(c => ['up', 'down', 'flat'].includes(c)) : [];
  return {name: nm.textContent, meta: m.textContent.trim(), answer: a.innerText.replace(/\\s+/g, ' ').trim(),
          dir: dirs[0] || null, pill: p ? p.textContent : null, tile: tile ? tile.textContent : null,
          right: a.getBoundingClientRect().left >= nm.getBoundingClientRect().right - 1,
          mid: mid ? mid.innerText.replace(/\\s+/g, ' ').trim() : '', spark: !!(mid && mid.querySelector('svg')),
          marks: mid ? [...mid.querySelectorAll('i')].map(i => i.textContent) : [],
          opens: !!q('[data-testid="digest-r-research"]')}; })"""

# The ctx the Digest itself builds for the card at the page's clock (the card must be in that day's plan), then
# the card drawn again from it after `patch`, a JS statement on `ctx`.
DRAW = """([name, patch]) => { const real = window[name]; let ctx = null;
  window[name] = c => { ctx = c; return real(c); };
  try { render(); } finally { window[name] = real; }
  if (!ctx) throw new Error(name + " is not in this day's plan");
  eval(patch); return real(ctx); }"""


class DigestCardsPage(DigestDayPage):

    def on(self, day):
        """The page's clock at that weekday (tue, wed, thu, fri), drawn again."""
        self.at(CLOCK[day])

    def card(self, card_id):
        return self.page.locator(f"[data-dgcard='{card_id}']")

    def card_rows(self, card_id):
        return self.card(card_id).locator("[data-testid='digest-r']").evaluate_all(ROWS_JS)

    def card_head(self, card_id):
        c = self.card(card_id)
        more = c.get_by_test_id("digest-card-more")
        return {"title": c.get_by_test_id("digest-card-title").text_content(),
                "more": more.get_attribute("data-dggo") if more.count() else None}

    def card_foot(self, card_id):
        foot = self.card(card_id).get_by_test_id("digest-card-foot")
        return foot.text_content() if foot.count() else None

    def card_foot_tip(self, card_id):
        """The foot's tooltip, where a test code or METHODOLOGY id lives (Home draft B), or None."""
        foot = self.card(card_id).get_by_test_id("digest-card-foot")
        return foot.get_attribute("title") if foot.count() else None

    def title_fits(self, card_id):
        """The card's title is one line: no taller than its own line-height."""
        return self.card(card_id).get_by_test_id("digest-card-title").evaluate(
            "h => { const lh = parseFloat(getComputedStyle(h).lineHeight); return lh > 0 && h.getBoundingClientRect().height <= lh * 1.2; }")

    def open_row(self, card_id, n):
        self.card(card_id).locator("[data-testid='digest-r-btn']").nth(n).click()

    def open_research(self, card_id):
        """Per row with research: whether it shows."""
        return self.card(card_id).get_by_test_id("digest-r-research").evaluate_all("ds => ds.map(d => !d.hidden && d.offsetHeight > 0)")

    def research(self, card_id, n):
        return self.card(card_id).get_by_test_id("digest-r-research").nth(n).inner_text().replace("\n", " | ")

    def drawn(self, name, patch=""):
        """What a card function returns for the ctx the Digest built for it after `patch` (a JS statement on `ctx`)."""
        return self.page.evaluate(DRAW, [name, patch])

    # ---- plants ----

    def plant(self, js):
        """Run a JS statement on the page and draw again (every plant starts from what it read)."""
        self.page.evaluate("(js) => { eval(js); DG_CUT = null; render(); }", js)

    def plant_sleeper_adds(self):
        self.plant("LIVE_DIGEST.adds_source = 'sleeper'; LIVE_DIGEST.adds_hours = 24; "
                   "LIVE_DIGEST.adds.forEach((a, i) => { a.count = 4039301 - i * 1000; });")

    def plant_a_shrinking_add(self):
        """The top add's role fell: Usage movers has him at 41% of snaps, down 12."""
        self.plant("LIVE_USAGE_MOVERS.rows = [{slug: LIVE_DIGEST.adds[0].slug, name: LIVE_DIGEST.adds[0].n, "
                   "team: 'CLE', metric: 'snap', was: 53, now: 41, change: -12, spark: [60, 53, 41], targets: 2, carries: 0, "
                   "teammate: null, line: 'Down.'}]")

    def plant_gains_without_a_backup(self):
        self.plant("LIVE_DIGEST.gains = [{out: LIVE_DIGEST.gains[0].out, next: null}]")

    def plant_news_for(self, slug, headline):
        self.plant(f"LIVE_DIGEST.news = [{{when: 'Fri 7:31 AM', headline: {headline!r}, n: 'x', rest: 'x', slugs: [{slug!r}]}}]")

    def plant_practice_missing(self):
        self.plant("LIVE_DIGEST.hurt.forEach(h => { h.practice = []; })")

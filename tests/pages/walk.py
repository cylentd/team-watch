"""Reads for the 2026-10-08 polish walk (ledger #37), one class per surface, kept apart from those surfaces' own
page objects because those are frozen. Class selectors where a surface has no test ids yet (League > Recap's
lead, the picker's grid), as in pages/league_chip.py. Reads return plain data; no method asserts."""

LINE = """() => {
  const lead = document.querySelector('.lg-league .bp2-lead'), line = lead.querySelector('.bp2-score');
  const mid = e => { const r = e.getBoundingClientRect(); return Math.round((r.top + r.bottom) / 2); };
  const words = [...line.querySelectorAll('.bp2-w > b, .bp2-w > .bp2-n, .bp2-d, .bp2-l > b, .bp2-l > .bp2-n')];
  const box = lead.getBoundingClientRect(), pad = parseFloat(getComputedStyle(lead).paddingRight);
  return {mids: words.map(mid), stamps: [...line.querySelectorAll('.lg-stamp')].map(mid),
          scores_whole: [...line.querySelectorAll('.bp2-n')].every(n => n.scrollWidth <= n.clientWidth + 0.5),
          past_card: Math.round(Math.max(...[...line.children].map(e => e.getBoundingClientRect().right)) - (box.right - pad))};
}"""


class LeadLine:
    """League > Recap: the lead game's score line (surface/league/lead.js `lgScoreLineHTML`)."""

    def __init__(self, page):
        self.page = page

    def rename(self, winner, loser):
        """Put other managers' names in the line, as a later week's lead would carry."""
        self.page.evaluate("""([w, l]) => { const s = document.querySelector('.lg-league .bp2-lead .bp2-score');
          s.querySelector('.bp2-w > b').textContent = w; s.querySelector('.bp2-l > b').textContent = l; }""", [winner, loser])

    def stamp_winner(self, label):
        """Hang an award stamp after the winner's score, where lgScoreLineHTML puts one."""
        self.page.evaluate("""t => document.querySelector('.lg-league .bp2-lead .bp2-w')
          .insertAdjacentHTML('beforeend', `<span class="lg-stamp g">${t}</span>`)""", label)

    def read(self):
        """{mids: vertical centre of each name, score and "beat", stamps: each stamp's centre,
        scores_whole: no score is cut, past_card: px the line runs past the card's inner edge}."""
        return self.page.evaluate(LINE)


class WeeksChips:
    """Players > Schedule: the weeks chips (Next 4, Rest, Playoffs), test id `schedule-win-chip`."""

    def __init__(self, page):
        self._chips = page.get_by_test_id("schedule-win-chip")

    def paint(self):
        """Every chip: {pressed, fill, edge}, as the browser paints them."""
        return self._chips.evaluate_all("""cs => cs.map(c => { const s = getComputedStyle(c);
          return {pressed: c.getAttribute('aria-pressed'), fill: s.backgroundColor, edge: s.borderTopColor}; })""")


class PickerGrid:
    """The team picker a reader with no team sees (chrome/teamswitch.js `pickHTML`), per league."""

    def __init__(self, page):
        self.page = page

    def leagues(self):
        """Per league list: {n: teams, rows: distinct button tops, widest: widest button, w: list width,
        min_h: shortest button}."""
        return self.page.evaluate("""() => [...document.querySelectorAll('[data-testid="teamswitch-pick-league"]')].map(lg => {
          const bs = [...lg.querySelectorAll('[data-testid="teamswitch-pick"]')].map(b => b.getBoundingClientRect());
          return {n: bs.length, rows: new Set(bs.map(r => Math.round(r.top))).size,
                  widest: Math.round(Math.max(...bs.map(r => r.width))), w: Math.round(lg.querySelector('ul').getBoundingClientRect().width),
                  min_h: Math.min(...bs.map(r => Math.round(r.height)))}; })""")

    def overflow(self):
        """Px the page is wider than the screen."""
        return self.page.evaluate("document.scrollingElement.scrollWidth - innerWidth")


class StuckColumn:
    """A view's own sticky column on a desktop (Preview's slate, `preview-slate`), against the tab row over it."""

    def __init__(self, page):
        self.page = page

    def stuck_gap_under_tab_row(self):
        """Px from the tab row's bottom edge down to where the slate sticks, its `top` (negative: behind the row)."""
        return self.page.evaluate("""() => Math.round(parseFloat(getComputedStyle(document.querySelector('[data-testid="preview-slate"]')).top)
          - document.querySelector('[data-testid="chrome-tabrow"]').getBoundingClientRect().bottom)""")

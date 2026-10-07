"""The Roster's Sheet (design/src/js/surface/teams/board.js): the lineup rows, their usage and projection, and the
two columns of them (the starters, then the bench and the out).

Locators are `roster-row*` / `roster-sheet-col` data-testids (test hooks only: no CSS or JS reads them). The
projection and the TD chance under it are drawn by `projNumHTML` in ui/player.js, outside surface/teams/, so
those two are read by their classes (`.rtd`, `.rstage`, `.trend`, `.spark`).
"""
from pages.roster import RosterPage

WIDTHS = "els => els.map(e => e.getBoundingClientRect().width)"
# A name cell's text is cut when it runs past the cell, or a third line is clamped away: scrollHeight past the box
# by more than a descender's 2px says so.
CUT = """nms => nms.filter(nm => {
  const b = nm.querySelector('.nm-1 b'), r = document.createRange(); r.selectNodeContents(b);
  return r.getBoundingClientRect().width > nm.getBoundingClientRect().width + 0.5 || b.scrollHeight > b.clientHeight + 2;
}).map(nm => nm.querySelector('.nm-1 b').innerText)"""
STAGES = """slugs => Object.fromEntries(slugs.map(slug => {
  const el = document.createElement('div');
  el.innerHTML = projNumHTML({slug});
  const tag = el.querySelector('.rstage');
  return [slug, {stage: projStage({slug}), tag: tag ? tag.textContent : null, tip: tag ? tag.title : null,
                 rowTip: el.firstElementChild.title}];
}))"""
TD_CHANCES_DRAWN = """TEAMS.espn.roster.every(p => { const n = tdChanceFor(p); return n === null || n < 25 || projFor(p) === null
  || !!document.querySelector(`.row[data-i='${briefOrder(TEAMS.espn).indexOf(p)}'] .rtd`); })"""
PLANT_TD = """percents => {
  const who = TEAMS.espn.roster.filter(p => p.slug && projFor(p) !== null).slice(0, percents.length);
  who.forEach((p, i) => {
    for (let j = PROPS.length - 1; j >= 0; j--) if (PROPS[j].slug === p.slug && PROPS[j].mkt === 'TD') PROPS.splice(j, 1);
    PROPS.push({slug: p.slug, n: p.n, mkt: 'TD', model: percents[i]});
  });
  render();
  return who.map(p => p.slug);
}"""


class RosterSheet:
    def __init__(self, page, team="espn"):
        """The roster as the Sheet, `team`'s (the ESPN fixture is the one with a bench)."""
        self.page = page
        self.roster = RosterPage(page)
        self.roster.show(team)
        tid = page.get_by_test_id
        self._rows = tid("roster-row")
        self._starts = self._rows.and_(page.locator(".start"))
        self._cols = tid("roster-sheet-col")

    # ---- rows ----

    def head_widths(self):
        """The width of every row's headshot (or its initials, when it has none)."""
        return self.page.get_by_test_id("roster-row-head").locator("img, .fallback").evaluate_all(WIDTHS)

    def starter_slots(self):
        """What each starter's slot prints (RB1 prints RB, FLX2 prints FLX)."""
        return self._starts.get_by_test_id("roster-row-slot").evaluate_all("els => els.map(e => e.textContent)")

    def row_widths(self):
        """The distinct widths, in whole pixels, of every row drawn."""
        return self._rows.evaluate_all("els => [...new Set(els.map(e => Math.round(e.getBoundingClientRect().width)))]")

    def names_drawn(self):
        """How many name cells are drawn: the number `names_cut` measures."""
        return self.page.get_by_test_id("roster-row-name").count()

    def names_cut(self):
        """The names that end in a clamp or run past their cell: none, when every name wraps whole."""
        return self.page.get_by_test_id("roster-row-name").evaluate_all(CUT)

    # ---- usage and the projection ----

    def trend_lines(self):
        """The retired snap-share line (`.trend`, `.spark`) in any row."""
        return self._rows.locator(".trend, .spark").count()

    def usage_words(self):
        """The word under each starter's usage number."""
        return self._starts.get_by_test_id("roster-row-usage").locator("small").evaluate_all("els => els.map(e => e.textContent)")

    def plant_td_chances(self, percents):
        """Give the first projected roster players a TD line at these model percents (one each, in order), and
        redraw. The fixture's props carry none for the roster, so no chip is drawn until one is planted."""
        return self.page.evaluate(PLANT_TD, list(percents))

    def td_chances(self):
        """Every TD chance drawn, as a number of percent."""
        return self.page.locator(".rtd").evaluate_all("els => els.map(e => parseInt(e.textContent.replace(/\\D/g, '')))")

    def every_td_chance_from_25_is_drawn(self):
        """Whether each roster player with a TD chance of 25% or more and a projection has the tag on his row."""
        return self.page.evaluate(TD_CHANCES_DRAWN)

    def stages(self, slugs):
        """For each slug: {stage, tag: the EARLY tag's text, tip: its note, rowTip: the number's hover note}."""
        return self.page.evaluate(STAGES, list(slugs))

    def early_tags_drawn(self):
        return self._rows.locator(".rstage").count()

    def early_projections(self):
        """How many roster players ESPN's feed stamps "early" and who have a projection: the tags a row should wear."""
        return self.page.evaluate("TEAMS.espn.roster.filter(p => projStage(p) === 'early' && projFor(p) !== null).length")

    # ---- the two columns ----

    def column_corners(self):
        """Each column's top and left, in whole pixels."""
        return self._cols.evaluate_all("""els => els.map(e => { const r = e.getBoundingClientRect();
          return {top: Math.round(r.top), left: Math.round(r.left)}; })""")

"""Signed weeks as gold bars, on a Sheet row and a card's back (design/src/js/surface/teams/pointsbars.js,
2026-10-07). `GoldBars` extends the card-backs page object (tests/pages/roster_backs.py): it plants
LIVE_SIGNED.weeks, and reads which bars are gold."""
from pages.roster_backs import BackFacts

# LIVE_SIGNED is a const object, so its parts are set; a planted list replaces the whole `weeks` map.
PLANT = """weeks => { LIVE_SIGNED.weeks = weeks; render(); }"""

# One row's strip: per bar, is it marked signed and does it paint the gold token.
ROW = """name => {
  const gold = (() => { const e = document.createElement('i'); e.style.color = 'var(--gold-2)'; document.body.appendChild(e);
    const c = getComputedStyle(e).color; e.remove(); return c; })();
  const row = [...document.querySelectorAll('[data-testid="roster-row"]')].find(r =>
    [...r.querySelectorAll('.nm-1 b > span')].find(s => s.offsetParent !== null).textContent === name);
  const bars = [...row.querySelectorAll('.pb-b')];
  return {signed: bars.map(b => b.classList.contains('signed')),
          painted: bars.map(b => getComputedStyle(b).backgroundColor === gold)};
}"""

# A made-up player's back at page week 5 (weeks 1-4 of points), his signed weeks planted first.
BACK = """([slug, pos, weeks]) => {
  LIVE_GAMELOG.rows = LIVE_GAMELOG.rows.filter(r => r.slug !== slug);
  [10, 22, 14, 9].forEach((pts, i) => LIVE_GAMELOG.rows.push({slug, n: slug, pos, wk: i + 1, pts}));
  LIVE_PROJECTIONS.players[slug] = {...(LIVE_PROJECTIONS.players[slug] || {}), pts: 12, out: null, done: null};
  LIVE_SCHEDULE.week = 5;
  LIVE_SIGNED.weeks = {[slug]: weeks};
  const grid = document.querySelector('[data-testid="roster-cardgrid"]');
  grid.insertAdjacentHTML('beforeend', cardHTML({n: 'Test Gold', pos, team: 'SF', slot: pos, start: true, slug}, 0, 'espn'));
  const card = grid.lastElementChild, slots = [...card.querySelectorAll('.pb-s')];
  const gold = (() => { const e = document.createElement('i'); e.style.color = 'var(--gold-2)'; document.body.appendChild(e);
    const c = getComputedStyle(e).color; e.remove(); return c; })();
  return {signed: slots.map(s => s.querySelector('.pb-b').classList.contains('signed')),
          painted: slots.map(s => getComputedStyle(s.querySelector('.pb-b')).backgroundColor === gold),
          points: slots.map(s => getComputedStyle(s.querySelector('.pb-n')).color === gold),
          stars: card.querySelectorAll('.pb-star').length};
}"""


class GoldBars(BackFacts):
    def plant_weeks(self, weeks):
        """Set LIVE_SIGNED.weeks ({slug: [week]}) and draw the Sheet again."""
        self.page.evaluate(PLANT, weeks)

    def row_gold(self, name):
        """The strip of the Sheet row showing `name`: {signed [bool per bar], painted [bool per bar: the bar is the gold token]}."""
        return self.page.evaluate(ROW, name)

    def gold_back(self, weeks, slug="test-gold-wr", pos="WR"):
        """A made-up player's back (weeks 1-4 played, page week 5) with these signed weeks: {signed, painted, points, stars}
        per slot (four weeks, then the projection)."""
        return self.page.evaluate(BACK, [slug, pos, weeks])

"""The Roster card backs of a kicker, a defense and a signed player, and the Sheet strip's room
(design/src/js/surface/teams/cardsupport.js, pointsbars.js; 2026-10-07).

`BackFacts` extends the matchup page object (tests/pages/roster_matchup.py): it plants lines, a D/ST
projection block and a roof, draws one card by `cardHTML` into the starters' grid, and reads its back."""
from pages.roster_matchup import MatchupLine

# A club's game: SF is home to ARI (a dome in the scene), CIN is away to ATL (a retractable roof).
SUPPORT = """([pos, team, key, plant]) => {
  LIVE_LINES.teams = {...LIVE_LINES.teams, ...plant.lines};
  LIVE_WEATHER.teams = {...LIVE_WEATHER.teams, ...plant.weather};
  LIVE_DST.weeks = [5];
  LIVE_DST.leagues = {espn: {dst: 'dst_espn', k: null}, yahoo: {dst: 'dst_yahoo', k: 'k_yahoo'}};
  LIVE_DST.teams = plant.dst;
  const grid = document.querySelector('[data-testid="roster-cardgrid"]');
  grid.insertAdjacentHTML('beforeend', cardHTML({n: 'Test Support', pos, team, slot: pos, start: true, slug: null}, 0, key));
  const card = grid.lastElementChild, back = card.querySelector('[data-testid="roster-card-back"]');
  const q = id => card.querySelector('[data-testid="' + id + '"]'), box = e => e.getBoundingClientRect();
  const why = box(q('roster-back-why')), facts = box(q('roster-back-facts')), open = box(q('roster-back-open'));
  const parts = [...card.querySelectorAll('[data-testid="roster-back-fact"]')].map(r => [...r.children]);
  return {over: back.scrollHeight - back.clientHeight, head: q('roster-back-why').textContent,
    matchup: q('roster-back-matchup').textContent.replace(/\\s+/g, ' ').trim(),
    kick: q('roster-back-kick') ? q('roster-back-kick').textContent : null,
    rows: parts.map(([l, v]) => [l.textContent, v.textContent]),
    whole: parts.every(cells => cells.every(e => e.scrollWidth <= e.clientWidth)) && q('roster-back-facts').scrollWidth <= q('roster-back-facts').clientWidth,
    above: Math.round(facts.top - why.bottom), below: Math.round(open.top - facts.bottom)};
}"""

# A made-up signed player's back at page week 5 with weeks 1-4 of points, signed for week 3.
SIGNED = """([slug, pos]) => {
  LIVE_GAMELOG.rows = LIVE_GAMELOG.rows.filter(r => r.slug !== slug);
  [10, 22, 14, 9].forEach((pts, i) => LIVE_GAMELOG.rows.push({slug, n: slug, pos, wk: i + 1, pts}));
  LIVE_PROJECTIONS.players[slug] = {...(LIVE_PROJECTIONS.players[slug] || {}), pts: 12, out: null, done: null};
  LIVE_SCHEDULE.week = 5;
  LIVE_SIGNED.players[slug] = {rank: 1, pts: 14};
  const grid = document.querySelector('[data-testid="roster-cardgrid"]');
  grid.insertAdjacentHTML('beforeend', cardHTML({n: 'Test Signed', pos, team: 'SF', slot: pos, start: true, slug}, 0, 'espn'));
  delete LIVE_SIGNED.players[slug];
  const card = grid.lastElementChild, back = card.querySelector('[data-testid="roster-card-back"]');
  const slots = [...card.querySelectorAll('.pb-s')];
  const gold = (() => { const e = document.createElement('i'); e.style.color = 'var(--gold-2)'; document.body.appendChild(e);
    const c = getComputedStyle(e).color; e.remove(); return c; })();
  return {over: back.scrollHeight - back.clientHeight, text: back.textContent,
    stars: slots.map(s => !!s.querySelector('[data-testid="roster-back-signed"]')),
    golds: slots.map(s => getComputedStyle(s.querySelector('.pb-n')).color === gold),
    kick: !!card.querySelector('[data-testid="roster-back-kick"]')};
}"""

# Every starter row's strip against the name block: how far the text reaches and where the first bar starts.
ROOM = """() => [...document.querySelectorAll('[data-testid="roster-row"].start')].map(r => {
  const bars = [...r.querySelectorAll('.pb-b')]; if (!bars.length) return null;
  let right = 0;
  r.querySelectorAll('.nm *').forEach(e => { if (!e.children.length && e.textContent.trim()) {
    const g = document.createRange(); g.selectNodeContents(e); const b = g.getBoundingClientRect(); if (b.width) right = Math.max(right, b.right); } });
  const strip = r.querySelector('.rbars .pb').getBoundingClientRect(), track = r.querySelector('.rbars').getBoundingClientRect();
  return {text: right, bar: bars[0].getBoundingClientRect().left, strip: [strip.left, strip.right], track: [track.left, track.right],
    row: r.getBoundingClientRect().height};
}).filter(Boolean)"""

# The bars of one row: colour per bar and the projection bar's border style.
LOOK = """() => [...document.querySelectorAll('[data-testid="roster-row"]')].map(r => ({
  name: [...r.querySelectorAll('.nm-1 b > span')].find(s => s.offsetParent !== null).textContent,
  bars: [...r.querySelectorAll('.pb-b')].map(b => ({bg: getComputedStyle(b).backgroundColor, border: getComputedStyle(b).borderTopStyle}))}))"""


class BackFacts(MatchupLine):
    def support(self, pos, team, key="yahoo", lines=None, weather=None, dst=None):
        """A `pos` ("K" or "DST") card of `team` drawn into the starters' grid for the `key` league, with these
        planted lines ({team: {implied, opp, spread, total}}), weather ({team: row}) and D/ST rows (the file's
        `teams`); its back as {over, head, matchup, kick, rows [[label, value]], whole, above, below}."""
        return self.page.evaluate(SUPPORT, [pos, team, key, {"lines": lines or {}, "weather": weather or {}, "dst": dst or []}])

    def signed_back(self, slug="test-signed-wr", pos="WR"):
        """A signed player's back, signed for week 3 (the signed fixture's LIVE_SIGNED.wk): {over, text, stars, golds, kick}."""
        return self.page.evaluate(SIGNED, [slug, pos])

    def room(self):
        """Every starter row's {text, bar, strip, track, row}: the name text's right edge, the first bar's left."""
        return self.page.evaluate(ROOM)

    def look(self):
        """Every Sheet row's name and each bar's {bg, border}."""
        return self.page.evaluate(LOOK)

"""The Roster's matchup line and points bars (design/src/js/surface/teams/matchupline.js, pointsbars.js): on a
Sheet row, two lines under the name (the game with its rank and roof, then the kickoff) and a strip of bars,
one per week of his fantasy points and a hollow one for this week's projection; on a card's back, the same two
lines over bigger bars, each with its points over it and its week under it.

`MatchupLine` plants a week's games, ranks, roofs and points into the mounted page and reads what the rows and
the card backs draw. A back is drawn by `cardHTML` into the starters' grid (as pages/roster.py's
`add_support_and_signed_cards` does), so its size is the card's at the mounted width.
"""
from pages.roster import RosterPage

PLANT = """s => {
  window.KICK_TZ = 'America/Los_Angeles';
  LIVE_SCHEDULE.week = 5;
  LIVE_SCHEDULE.games = s.games;
  for (const [slug, next] of Object.entries(s.factors)) {
    const row = LIVE_PROFILES.players[slug] || {};
    LIVE_PROFILES.players[slug] = next ? {...row, next} : {...row, next: null};
  }
  LIVE_WEATHER.teams = s.weather;
  LIVE_DEFENSE.form = s.form;
  LIVE_INJURY.players = {};
  for (const p of TEAMS.espn.roster) p.status = null;
  render();
}"""

# One player's weeks of points (week -> points) and this week's projection, on the box score and the projections.
POINTS = """s => {
  LIVE_GAMELOG.rows = LIVE_GAMELOG.rows.filter(r => r.slug !== s.slug);
  Object.entries(s.pts).forEach(([wk, pts]) => LIVE_GAMELOG.rows.push({slug: s.slug, n: s.slug, pos: s.pos, wk: +wk, pts}));
  LIVE_PROJECTIONS.players[s.slug] = {...(LIVE_PROJECTIONS.players[s.slug] || {}), pts: s.proj, out: null, done: null};
  if (s.week) LIVE_SCHEDULE.week = s.week;
}"""

# A made-up player's back at a page week, and whether every number and week label is whole (not cut).
MADE_UP = """([pos, slug, week]) => {
  const grid = document.querySelector('[data-testid="roster-cardgrid"]');
  grid.insertAdjacentHTML('beforeend', cardHTML({n: 'Test Player', pos, team: 'SF', slug, slot: pos, start: true}, 0, 'espn'));
  const card = grid.lastElementChild, back = card.querySelector('[data-testid="roster-card-back"]');
  const whole = el => el.scrollWidth <= el.clientWidth;
  const labels = [...card.querySelectorAll('[data-testid="roster-back-pts"], [data-testid="roster-back-week"]')];
  return {over: back.scrollHeight - back.clientHeight, weeks: [...card.querySelectorAll('[data-testid="roster-back-week"]')].map(e => e.textContent),
    pts: [...card.querySelectorAll('[data-testid="roster-back-pts"]')].map(e => e.textContent), whole: labels.every(whole),
    open: card.querySelector('[data-testid="roster-back-open"]').getBoundingClientRect().bottom <= back.getBoundingClientRect().bottom + 0.5};
}"""

TOKENS = """() => { const probe = c => { const e = document.createElement('i'); e.style.color = `var(${c})`;
  document.body.appendChild(e); const v = getComputedStyle(e).color; e.remove(); return v; };
  return {down: probe('--down'), up: probe('--up'), ink: probe('--ink'), ink2: probe('--ink-2'), ink3: probe('--ink-3')}; }"""

BARS = """root => [...root.querySelectorAll('.pb-b')].map(b => ({proj: b.classList.contains('proj'), gap: b.classList.contains('gap'),
  h: parseFloat(b.style.getPropertyValue('--h')), color: getComputedStyle(b).backgroundColor, outline: getComputedStyle(b).boxShadow,
  px: b.getBoundingClientRect().height}))"""

ROW = """r => { const q = id => r.querySelector('[data-testid="' + id + '"]'), rank = q('roster-rank'), roof = q('roster-roof'),
  kick = q('roster-row-kick'), nm = r.querySelector('.nm');
  return {name: [...r.querySelectorAll('.nm-1 b > span')].find(s => s.offsetParent !== null).textContent,
    game: q('roster-row-game').textContent.replace(/\\s+/g, ' ').trim(), rank: rank ? rank.textContent : null,
    cls: rank ? rank.className : null, color: rank ? getComputedStyle(rank).color : null, title: rank ? rank.title : null,
    roof: roof ? roof.getAttribute('aria-label') : null, roofClass: roof ? roof.getAttribute('class') : null,
    kick: kick ? kick.textContent : null, height: r.getBoundingClientRect().height,
    projection_visible: !!r.querySelector('.rproj') && r.querySelector('.rproj').offsetParent !== null,
    cut: nm.scrollWidth > nm.clientWidth + 1 || q('roster-row-game').scrollWidth > q('roster-row-game').clientWidth + 1,
    bars: (%s)(r), text: r.querySelector('.rbars').textContent.trim()}; }""" % BARS

BACK = """([p, who]) => {
  const grid = document.querySelector('[data-testid="roster-cardgrid"]');
  const sk = TEAMS.espn.roster.find(x => x.slug === p);
  if (who.injury) LIVE_INJURY.players[p] = who.injury;
  if (who.signed) LIVE_SIGNED.players[p] = who.signed;
  grid.insertAdjacentHTML('beforeend', cardHTML(sk, 0, 'espn'));
  const card = grid.lastElementChild, back = card.querySelector('[data-testid="roster-card-back"]');
  const q = id => card.querySelector('[data-testid="' + id + '"]'), rank = q('roster-rank'), kick = q('roster-back-kick');
  const size = card.getBoundingClientRect(), txt = id => [...card.querySelectorAll('[data-testid="' + id + '"]')].map(e => e.textContent);
  return {w: Math.round(size.width), h: Math.round(size.height), over: back.scrollHeight - back.clientHeight,
    matchup: q('roster-back-matchup').textContent.replace(/\\s+/g, ' ').trim(), rank: rank ? rank.textContent : null,
    color: rank ? getComputedStyle(rank).color : null, cls: rank ? rank.className : null,
    roof: q('roster-roof') ? q('roster-roof').getAttribute('aria-label') : null,
    sub: q('roster-back-why').lastElementChild.textContent.trim(), kick: kick ? kick.textContent : null,
    text: back.textContent, pts: txt('roster-back-pts'), weeks: txt('roster-back-week'), bars: (%s)(back),
    open: q('roster-back-open').getBoundingClientRect().bottom <= back.getBoundingClientRect().bottom + 0.5};
}""" % BARS


# A made-up player's card, planted at a rank and signed: what the back's first line, kickoff and signed row say,
# and what the front and the back print in all.
FACTS = """([p, rank, sg]) => {
  LIVE_PROJECTIONS.players[p.slug] = {pts: 12, rank};
  LIVE_SIGNED.players[p.slug] = sg;
  const d = document.createElement('div'); d.innerHTML = cardHTML(p, 0, 'espn');
  delete LIVE_SIGNED.players[p.slug];
  const q = id => d.querySelector('[data-testid="' + id + '"]');
  return {matchup: q('roster-back-matchup').textContent.replace(/\\s+/g, ' ').trim(), kick: q('roster-back-kick') ? q('roster-back-kick').textContent : null,
    signed: q('roster-back-signed') ? q('roster-back-signed').textContent : null, front: q('roster-card-front').textContent,
    back: q('roster-card-back').textContent};
}"""


class MatchupLine(RosterPage):
    def back_facts_of(self, player, rank, signed):
        """A card drawn off screen for `player`, planted at `rank` and signed (rank, pts): {matchup, kick, signed, front, back}."""
        return self.page.evaluate(FACTS, [player, rank, signed])

    def set_week(self, week):
        """The page's week, as the schedule says it."""
        self.page.evaluate("w => { LIVE_SCHEDULE.week = w; }", week)

    def plant(self, scene):
        """Plant a scene {games, factors: slug -> next|None, weather, form} and draw the Sheet again."""
        self.page.evaluate(PLANT, scene)

    def tokens(self):
        """The computed colours of --down, --up, --ink, --ink-2 and --ink-3, as the page paints them."""
        return self.page.evaluate(TOKENS)

    def lines(self):
        """Every Sheet row's matchup lines and bars, in order, keyed by the name the row shows."""
        got = self.page.get_by_test_id("roster-row").evaluate_all(f"rs => rs.map({ROW})")
        return {r["name"]: r for r in got}

    def plant_points(self, slug, pts, proj, pos="QB", week=None):
        """Give `slug` these weeks of points ({week: points}) and this week's projection, on the page's box score."""
        self.page.evaluate(POINTS, {"slug": slug, "pts": {str(k): v for k, v in pts.items()}, "proj": proj, "pos": pos, "week": week})

    def redraw(self):
        self.page.evaluate("render()")

    def made_up_back(self, pos, week):
        """A made-up `pos` player's back at page week `week`: {over, weeks, pts, whole, open}. Plant his points first."""
        return self.page.evaluate(MADE_UP, [pos, f"test-{pos.lower()}-bars", week])

    def back(self, slug, injury=None, signed=None):
        """Draw `slug`'s card into the starters' grid and read its back (see BACK)."""
        return self.page.evaluate(BACK, [slug, {"injury": injury, "signed": signed}])

"""The points bars of a kicker and a defense, on a card's back and in a Sheet row (2026-10-07;
design/src/js/surface/teams/pointsbars.js, data/kdst.js). `KdstBars` plants a LIVE_KDST and a D/ST projection
block, draws one K or DST card (or row) for a league and reads its bars."""
from pages.roster_matchup import MatchupLine

# Page week 5; the planted files replace the fixtures' teams (LIVE_KDST is a const, so its parts are set).
SETUP = """
  LIVE_SCHEDULE.week = 5;
  LIVE_KDST.teams = kd.teams;
  LIVE_DST.weeks = [5];
  LIVE_DST.leagues = {espn: {dst: 'dst_espn', k: null}, yahoo: {dst: 'dst_yahoo', k: 'k_yahoo'}, ayo: {dst: 'dst_yahoo', k: 'k_ayo'}};
  LIVE_DST.teams = [{team, weeks: [{week: 5, bye: false, dst: {dst_espn: proj, dst_yahoo: proj}, k: {k_yahoo: proj, k_ayo: proj}}]}];
  const bar = b => ({proj: b.classList.contains('proj'), gap: b.classList.contains('gap'), faded: b.classList.contains('faded')});
"""

BACK = """([pos, team, key, name, kd, proj]) => {""" + SETUP + """
  const grid = document.querySelector('[data-testid="roster-cardgrid"]');
  grid.insertAdjacentHTML('beforeend', cardHTML({n: name, pos, team, slot: pos, start: true, slug: null}, 0, key));
  const card = grid.lastElementChild, back = card.querySelector('[data-testid="roster-card-back"]');
  const labels = [...card.querySelectorAll('.pb-n, .pb-w')];
  return {over: back.scrollHeight - back.clientHeight, whole: labels.every(e => e.scrollWidth <= e.clientWidth),
    facts: card.querySelectorAll('[data-testid="roster-back-fact"]').length, kick: !!card.querySelector('[data-testid="roster-back-kick"]'),
    bars: [...card.querySelectorAll('.pb-b')].map(bar), pts: [...card.querySelectorAll('.pb-n')].map(e => e.textContent)};
}"""

ROW = """([pos, team, key, name, kd, proj]) => {""" + SETUP + """
  const host = document.createElement('div');
  host.innerHTML = rowHTML({n: name, pos, team, slot: pos, start: true, slug: null}, 0, key);
  document.body.appendChild(host);
  const num = host.querySelector('.rproj');
  const out = {bars: [...host.querySelectorAll('.pb-b')].map(bar), num: num ? num.textContent : null};
  host.remove();
  return out;
}"""


class KdstBars(MatchupLine):
    def back(self, pos, team, key, kd, name="Test Support", proj=7.0):
        """A `pos` card of `team` for league `key` with this LIVE_KDST: {over, whole, facts, kick, bars [{proj, gap, faded}], pts}."""
        return self.page.evaluate(BACK, [pos, team, key, name, kd, proj])

    def row(self, pos, team, key, kd, name="Test Support", proj=7.0):
        """The Sheet row's bars for the same: {bars [{proj, gap, faded}]}."""
        return self.page.evaluate(ROW, [pos, team, key, name, kd, proj])

/* ============================== SCHEDULE: THE CUT ==============================
   Stats > Schedule (leaf `schedule`, 2026-10-05, plan U7). LIVE_SOS is ff-jarvis's sos.json passed through
   (design/sos.py): per team and position, what the defenses it faces allow, over the next 4 weeks, the rest
   of the season and the fantasy playoff weeks. Context, not backtested; the file's own `label` says so.
   This file only orders and lays out. It computes no number: the rank is the file's (1 = easiest), the
   points allowed per game are the file's `pts_pg`, the games are the file's count, and a bye is the file's
   `bye` list. A team with no game in the window has a null rank and goes last. Pinned by tests/test_js_sos.py. */

const SOS_POS = ["QB", "RB", "WR", "TE"];
const SOS_WINDOWS = ["next4", "ros", "playoffs"];

/* "5–8" for a run of weeks, else "5, 7". */
function sosSpan(weeks){
  const w = (weeks || []).slice().sort((a, b) => a - b);
  if (!w.length) return "";
  return w.length > 1 && w.every((x, i) => i === 0 || x === w[i - 1] + 1) ? `${w[0]}–${w[w.length - 1]}` : w.join(", ");
}

/* One cell per week of the window: the opponent, or a bye. A week that is neither (the file never has one)
   is drawn as a bye too rather than invented as a game. */
function sosCells(weeks, sched){
  const opp = {};
  ((sched && sched.opps) || []).forEach(o => { opp[o.week] = o.opp; });
  return weeks.map(week => (opp[week] ? {week, opp: opp[week], bye: false} : {week, opp: null, bye: true}));
}

/* The page's view of LIVE_SOS for one position and window: {label, weeks, span, rows} with the teams
   easiest first, or null with no file, no team, or a position or window the file does not carry. Ties share
   the file's rank and sort by team code, so the order never shifts between two draws. */
function sosView(raw, pos, win){
  if (!raw || !raw.teams || !SOS_POS.includes(pos) || !SOS_WINDOWS.includes(win)) return null;
  const weeks = (raw.windows && raw.windows[win]) || [];
  const rows = Object.entries(raw.teams).filter(([, e]) => e[pos] && e[pos][win]).map(([team, e]) => {
    const s = e[pos][win];
    return {team, rank: s.rank == null ? null : s.rank, pts: s.pts_pg == null ? null : s.pts_pg, games: s.games,
      current: s.current == null ? null : s.current, prior: s.prior == null ? null : s.prior,
      cells: sosCells(weeks, e.schedule && e.schedule[win])};
  });
  if (!rows.length) return null;
  const key = r => (r.rank === null ? Infinity : r.rank);
  rows.sort((a, b) => key(a) - key(b) || (a.team < b.team ? -1 : 1));
  return {label: raw.label || "", weeks, span: sosSpan(weeks), rows};
}

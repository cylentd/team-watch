/* D/ST and K streaming, as rows (2026-10-05, plan U6c). Pure and DOM-free, so Node tests it
   (tests/test_js_dst.py). The numbers are ff-jarvis's (LIVE_DST via design/dst.py, METHODOLOGY 12.85):
   per team and week, the D/ST points on each league's scoring, the K points on each Yahoo league's,
   the file's own rank and streamer flag. This only picks the league's cell, orders the rows by the
   file's rank, and carries who rosters each team. The page computes no points.

   The league's cells are named by `block.leagues[lg]`: {dst: "dst_espn", k: null} for ESPN (no K slot),
   {dst: "dst_yahoo", k: "k_yahoo"} for The Madden Curse, {dst: "dst_yahoo", k: "k_ayo"} for AYO. */

/* The league the board reads: the reader's team's (lgFocusKey) once a team is picked, else ESPN. A league
   the file lacks reads ESPN's too. */
function dstLeagueKey(focus, picked, block){
  return picked && focus && block && block.leagues && block.leagues[focus] ? focus : "espn";
}

/* The positions this league adds beside QB RB WR TE FLEX: D/ST always, K only where the league has a K cell. */
function dstTabs(block, lg){
  const L = block && block.leagues && block.leagues[lg];
  return !L ? [] : L.k ? ["DST", "K"] : ["DST"];
}

/* The position to draw: the picked one, or RB when it is a D/ST or K tab this league does not have. */
function dstPos(pos, block, lg){
  return (pos === "DST" || pos === "K") && !dstTabs(block, lg).includes(pos) ? "RB" : pos;
}

/* One cell of one team's week: the points, the opponent, whether the week is an estimate (no posted line
   yet) and whether the file calls it a streamer in this league. */
function dstCell(w, cell, lg, pos){
  if (w.bye) return {week: w.week, bye: true, opp: null, home: null, pts: null, rating: false, streamer: false};
  const flags = (pos === "K" ? w.k_streamer : w.streamer) || {};
  return {
    week: w.week, bye: false, opp: w.opp, home: w.home, rating: w.line === "rating", streamer: !!flags[lg],
    pts: ((pos === "K" ? w.k : w.dst) || {})[cell],
  };
}

/* A club spelled as the file spells it: a roster says LAR, JAC and WSH where the file says LA, JAX and WAS. */
const DST_CLUB = {LAR: "LA", JAC: "JAX", WSH: "WAS"};
const dstClub = c => DST_CLUB[c] || c;

/* The clubs whose D/ST (pos "DST") or K (pos "K") the reader holds in this league (2026-10-06): the players of that
   position on the rosters of the teams they follow (`keys`, tsFollowed()) that play in `lg`, spelled as the file
   spells them. The file's own `mine` flag is David's holdings for every reader, so the board never reads it. A
   connected league's team is no part of David's leagues, whose holders the file lists. */
function dstHeld(teams, keys, lg, pos){
  const out = new Set();
  keys.forEach(k => {
    const tm = teams[k];
    if (!tm || tm.connected || (tm.mate ? tm.league : k) !== lg) return;
    (tm.roster || []).forEach(p => { if (p.pos === pos && p.team) out.add(dstClub(p.team)); });
  });
  return [...out];
}

/* The board for one position in one league: the first week's rows in the file's rank order (a bye after
   every game, by team), each with the next weeks as small cells. null when there is no file or the league
   has no such position (ESPN has no K). A team that has already kicked off is no streamer. `held` is the
   clubs the reader holds (dstHeld): a row is MINE when its club is one. */
function dstBoard(block, lg, pos, held = []){
  const L = block && block.leagues && block.leagues[lg];
  const cell = L && (pos === "K" ? L.k : L.dst);
  if (!cell) return null;
  const mine = new Set(held.map(dstClub));
  const rows = (block.teams || []).map(tm => {
    const [first, ...rest] = tm.weeks, c = dstCell(first, cell, lg, pos);
    const owned = (pos === "K" ? tm.k_rostered : tm.rostered) || {}, h = owned[lg];
    return {
      ...c, team: tm.team, kickoff: first.kickoff || null, kicked_off: !!first.kicked_off,
      rank: first.bye ? null : (first.rank || {})[cell],
      streamer: c.streamer && !first.kicked_off,
      // On waivers (ESPN's flag) he is nobody's yet, but not Free: he can only be claimed.
      waiver: h ? !!h.waiver : false, free: h ? h.pct < 50 && !h.waiver : null,
      owner: h ? h.owner : null, mine: mine.has(dstClub(tm.team)),
      next: rest.map(w => dstCell(w, cell, lg, pos)),
    };
  });
  // Byes last; a team that has played sits after every team still to play (Monday: the board leads with
  // the games left), each group in the file's rank order.
  rows.sort((a, b) => (a.bye - b.bye) || (a.kicked_off - b.kicked_off) || (a.bye ? a.team.localeCompare(b.team) : a.rank - b.rank || a.team.localeCompare(b.team)));
  const weeks = block.weeks || [];
  return {
    pos, lg, cell, rows, weeks, week: weeks[0], source: (block.source || {})[cell] || "model",
    estimate: rows.some(r => r.rating || r.next.some(c => c.rating)),
  };
}

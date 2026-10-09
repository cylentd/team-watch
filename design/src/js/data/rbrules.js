/* ------------------------------------------------------------------
   RUNNING BACKS IN THE START/SIT PICKER (2026-10-05; ff-jarvis METHODOLOGY 12.86)

   The books' implied points for a back (`rank_pts`) call two or more priced backs better than our
   projection but read about 0.5 high in level, so the picker calls on them and never prints them.
   Ranks no longer uses them: every list orders and tiers by `pts` (ledger #96, 2026-10-09), and the
   "No line" tag and the books note are gone.

   Pure functions of rows: Node-tested (tests/test_js_rbrules.py).
------------------------------------------------------------------ */

/* One call from a set of lanes {pos, pts, rp}: who starts and by how much. The key is the books'
   number when EVERY lane is a back with one (a mixed set, or a back the books skipped, would compare
   two different scales), else points. The gap printed is always points, never the books' number.
   `books`: the books made the call; `moved`: it differs from what points alone would say.
   Null under two lanes with points. */
function rbCall(lanes, key, flipAt){
  const by = lanes.slice().sort((a, b) => key(b) - key(a));
  const gap = +(key(by[0]) - key(by[1])).toFixed(1);   // rounded to the one decimal shown: 0.54 is a coin flip, never "+0.5"
  return gap <= flipAt ? {flip: true, gap, by} : {flip: false, win: by[0], gap, by};
}
function rbVerdict(cols, flipAt){
  const lanes = cols.filter(c => typeof c.pts === "number");
  if (lanes.length < 2) return null;
  const byPts = rbCall(lanes, c => c.pts, flipAt);
  const {by, ...plain} = byPts;
  if (!lanes.every(c => c.pos === "RB" && typeof c.rp === "number")) return {...plain, books: false, moved: false};
  const call = rbCall(lanes, c => c.rp, flipAt);
  const moved = call.flip !== byPts.flip || (!call.flip && call.win !== byPts.win);
  // The gap printed is the points between the two the books put first, which can be under zero.
  const gap = call.flip ? call.gap : +(call.by[0].pts - call.by[1].pts).toFixed(1);
  return call.flip ? {flip: true, gap, books: true, moved} : {flip: false, win: call.win, gap, books: true, moved};
}

/* A tier's printed range: its highest and lowest points, which are not its first and last row's when
   the shown number does not step down the list. */
function rbTierSpan(rows){
  const pts = rows.map(r => r.pts);
  return {hi: Math.max(...pts).toFixed(1), lo: Math.min(...pts).toFixed(1)};
}

/* The projections row for a slug (the picker's fallback for his books number), or null. */
function rbProjRow(slug){
  return typeof LIVE_PROJECTIONS !== "undefined" && LIVE_PROJECTIONS ? LIVE_PROJECTIONS.players[slug] || null : null;
}

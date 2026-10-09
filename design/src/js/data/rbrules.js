/* ------------------------------------------------------------------
   THE START/SIT CALL AND A TIER'S RANGE

   The call is our own points at every position (ledger #94, 2026-10-09; VISION 2026-10-08, David: "the rank
   was always supposed to be our own ranking system"). Running backs were called on the books' implied points
   from 2026-10-05 (ff-jarvis METHODOLOGY 12.86); no longer. Ranks orders and tiers by `pts` too (ledger #96).

   Pure functions of rows: Node-tested (tests/test_js_rbrules.py).
------------------------------------------------------------------ */

/* One call from a set of lanes {pos, pts}: who starts and by how much, keyed on `key`. */
function rbCall(lanes, key, flipAt){
  const by = lanes.slice().sort((a, b) => key(b) - key(a));
  const gap = +(key(by[0]) - key(by[1])).toFixed(1);   // rounded to the one decimal shown: 0.54 is a coin flip, never "+0.5"
  return gap <= flipAt ? {flip: true, gap, by} : {flip: false, win: by[0], gap, by};
}
/* The picker's and the lineup card's call: the higher points start, inside `flipAt` a coin flip. Null under two
   lanes with points. */
function rbVerdict(cols, flipAt){
  const lanes = cols.filter(c => typeof c.pts === "number");
  if (lanes.length < 2) return null;
  const {by, ...plain} = rbCall(lanes, c => c.pts, flipAt);
  return plain;
}

/* A tier's printed range: its highest and lowest points, which are not its first and last row's when
   the shown number does not step down the list. */
function rbTierSpan(rows){
  const pts = rows.map(r => r.pts);
  return {hi: Math.max(...pts).toFixed(1), lo: Math.min(...pts).toFixed(1)};
}

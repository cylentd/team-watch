/* ------------------------------------------------------------------
   BOOM AND BUST (Ranks, 2026-11-13). ff-jarvis b064481 (METHODOLOGY 12.136) writes `boom` and `bust` on every
   player_projections row: the chance, 0-1 with 2 decimals, that he scores at or above his position's boom bar, or
   under its bust bar, if he plays. The bars are the file's `ranges.bars` block, carried as LIVE_RANKS.bars. The page
   sorts by the two numbers and prints them; it computes none.

   Projection is the build's order (tiers and all). Upside: boom high to low. Safe: bust low to high. A tie goes to the
   higher number the row prints. A row without both numbers sorts last, in the build's order.
------------------------------------------------------------------ */
const OUTCOME_SORTS = ["pts", "boom", "bust"];
const OUTCOME_PCT = 100;   // a 0-1 chance as the whole percent a row prints

const outcomeHas = r => !!r && typeof r.boom === "number" && typeof r.bust === "number";
const outcomeOf = r => outcomeHas(r) ? {boom: Math.round(r.boom * OUTCOME_PCT), bust: Math.round(r.bust * OUTCOME_PCT)} : null;
const outcomeSorts = list => list.some(outcomeHas) ? OUTCOME_SORTS : OUTCOME_SORTS.slice(0, 1);
const outcomePts = r => typeof r.shown === "number" ? r.shown : r.pts;

function outcomeSort(list, mode){
  if (mode !== "boom" && mode !== "bust") return list.slice();
  const byPts = (a, b) => outcomePts(b) - outcomePts(a);
  const cmp = mode === "boom" ? (a, b) => b.boom - a.boom || byPts(a, b) : (a, b) => a.bust - b.bust || byPts(a, b);
  return [...list.filter(outcomeHas).sort(cmp), ...list.filter(r => !outcomeHas(r))];
}

/* The bars for the positions in view, positions that share a pair grouped, the largest group first (FLEX: RB and WR,
   then TE). Null when the file has no bar for one of them: the note is not drawn. */
function outcomeBars(bars, positions){
  const boom = (bars || {}).boom || {}, bust = (bars || {}).bust || {};
  if (!positions.every(p => typeof boom[p] === "number" && typeof bust[p] === "number")) return null;
  const groups = [];
  positions.forEach(p => {
    const g = groups.find(x => x.boom === boom[p] && x.bust === bust[p]);
    if (g) g.pos.push(p); else groups.push({pos: [p], boom: boom[p], bust: bust[p]});
  });
  return groups.sort((a, b) => b.pos.length - a.pos.length);
}

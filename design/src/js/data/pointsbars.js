/* The fantasy-points bars (2026-10-07, David: no usage numbers on the Roster row or the card back; usage is
   noisy and only matters as a spike or a sustained trend, which a glance cannot show). One model, drawn by
   the row and the back (surface/teams/pointsbars.js): a slot for each NFL week this season up to the page's
   week, each his points that week, then this week's projection last, drawn hollow, on the same scale.

   The points are LIVE_GAMELOG's `pts` (ff-jarvis's box score in half-PPR) and the projection is
   LIVE_PROJECTIONS' `pts`, also plain half-PPR, so a bar and the hollow one beside it are in one scoring and
   neither follows a league's rules. The page computes none of it. A week he did not play (a bye, an injury,
   a row with no points) keeps its slot, empty, so a gap reads as a gap. The scale is 0 to the largest of the
   bars and the projection, per player: a shape to see at a glance, not a number to compare across rows. */

/* {slots: [{wk, pts, h}], proj: {wk, pts, h}, max} for `rows` ([{wk, pts}]), his projection (or null) and the
   page's week (the week of the projection). `h` is the height as 0..1 of the scale, null for an empty slot;
   a negative week keeps its points and has height 0. `limit`, when given, is how many slots fit including the
   projection: only the latest weeks stay, and the scale is theirs. null when there is nothing to draw. */
function pbModel(rows, proj, pageWeek, limit){
  const by = new Map();
  rows.forEach(r => { if (!by.has(r.wk)) by.set(r.wk, r); });
  const first = limit ? Math.max(1, pageWeek - (limit - 1)) : 1;
  const slots = [];
  for (let wk = first; wk < pageWeek; wk++){
    const r = by.get(wk), pts = r && typeof r.pts === "number" ? r.pts : null;
    slots.push({wk, pts, h: null});
  }
  const pp = typeof proj === "number" ? proj : null;
  const have = slots.map(s => s.pts).filter(x => x !== null).concat(pp === null ? [] : [pp]);
  if (!have.length) return null;
  const max = Math.max(0, ...have);
  const h = pts => pts === null ? null : max > 0 ? Math.max(0, pts) / max : 0;
  slots.forEach(s => { s.h = h(s.pts); });
  return {slots, proj: {wk: pageWeek, pts: pp, h: h(pp)}, max};
}

/* Is this slot the week a signed card was signed for (LIVE_SIGNED.wk)? A played week only: the projection is
   never one, an empty slot has no points to mark. */
const pbIsSigned = (slot, signedWk) => typeof signedWk === "number" && slot.wk === signedWk && slot.pts !== null && slot.pts !== undefined;

/* Every week this player finished top 3 at his position (David, 2026-10-07): LIVE_SIGNED.weeks[slug] (design/signed.py)
   plus the autograph's own week, so a block without the list still marks the one it knows. Ascending, [] for none. */
function pbSignedWeeks(signed, slug){
  if (!signed || !slug) return [];
  const own = signed.players && signed.players[slug] ? [signed.wk] : [];
  const all = (signed.weeks && signed.weeks[slug] || []).concat(own);
  return [...new Set(all)].sort((a, b) => a - b);
}

/* The model with `signed: true` on each played slot whose week is in `weeks`: a gold bar. The projection is never
   one; null passes through. */
function pbMarkSigned(m, weeks){
  if (!m) return m;
  m.slots.forEach(s => { if (weeks.includes(s.wk) && s.pts !== null) s.signed = true; });
  return m;
}

/* "W5" under a bar; once the week has two digits the W goes, so the label still fits its slot. */
const pbWeekText = wk => wk < 10 ? t("teams.pb.week", {n: wk}) : String(wk);

/* A bar's points above it, whole: the back's slots are ~15px wide. "" for an empty slot. */
const pbPtsText = pts => pts === null || pts === undefined ? "" : String(Math.round(pts));

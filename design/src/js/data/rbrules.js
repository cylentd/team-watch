/* ------------------------------------------------------------------
   RUNNING BACKS, ORDERED BY THE BOOKS (2026-10-05; ff-jarvis METHODOLOGY 12.86 and 12.87)

   12.86: the books' implied points for a back (`rank_pts`) order running backs better than our
   projection (weekly Spearman 0.527 -> 0.551, 2024-2025 closing lines) but read about 0.5 high in
   level, so they ORDER and are never shown. Only running backs were tested, against running backs:
   every other position, and FLEX, still order by `pts`. design/ranks.py cuts the RB list, its tiers
   and its rank on this key at build time (projections.order_key); this file is the same rule for the
   two places the page decides by itself, the Start/Sit picker and the note that says why.
   12.87: a back the books leave unpriced beside a priced teammate scores about a third of his
   projection; ff-jarvis cuts his `pts` to 30% and flags him `unlined_backup`, and the page tags him.

   Pure functions of rows: Node-tested (tests/test_js_rbrules.py). A row is a Ranks row or a
   LIVE_PROJECTIONS row: {pos, pts, rank_pts, unlined_backup}.
------------------------------------------------------------------ */

/* The number a row is ordered by: a back's books number where he has one, else his points. */
function rbOrderPts(row){
  if (!row || typeof row.pts !== "number") return null;
  return row.pos === "RB" && typeof row.rank_pts === "number" ? row.rank_pts : row.pts;
}

/* One call from a set of lanes {pos, pts, rp}: who starts and by how much. The key is the books'
   number when EVERY lane is a back with one (a mixed set, or a back the books skipped, would compare
   two different scales), else points. The gap printed is always points, never the books' number.
   `books`: the books made the call; `moved`: it differs from what points alone would say, which is
   when the page owes the reader a reason. Null under two lanes with points. */
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

/* Does a list sit in an order its printed points would not give: a row above one with more points?
   Only then does the page say why (the books ordered it). Compared at the one decimal shown. */
function rbReordered(rows){
  const tenth = r => Math.round(r.pts * 10);
  return rows.some((r, i) => i && tenth(rows[i - 1]) < tenth(r));
}

/* A tier's printed range: its highest and lowest points, which are not its first and last row's once
   the order follows the books. */
function rbTierSpan(rows){
  const pts = rows.map(r => r.pts);
  return {hi: Math.max(...pts).toFixed(1), lo: Math.min(...pts).toFixed(1)};
}

/* The tag on a back the books left unpriced: {word, tip}, or null for any other row. */
function rbNoLine(row){
  return row && row.unlined_backup === true ? {word: t("ranks.noline.word"), tip: t("ranks.noline.tip")} : null;
}
/* The tag as markup: `cls` is the view's own class (each view's CSS file is fenced to its own views, so
   the three styles cannot share one rule). Hover and screen readers get the tip; a view with room also
   says it in words once (Ranks' heading, the profile strip, the picker). */
function rbNoLineHTML(row, cls){
  const tag = rbNoLine(row);
  return tag ? `<span class="${cls}" title="${tag.tip}" aria-label="${tag.word}. ${tag.tip}">${tag.word}</span>` : "";
}

/* The notes under a call, one paragraph each and only when they apply: `why` (why the call is not the higher
   points: the books ordered two backs) and what "No line" means for the first back in `rows` that wears it. */
function rbWhyHTML(rows, why, cls, tagCls){
  const row = rows.find(rbNoLine);
  return [why, row ? `${rbNoLineHTML(row, tagCls)}${rbNoLine(row).tip}` : ""].filter(Boolean).map(h => `<p class="${cls}">${h}</p>`).join("");
}

/* The projections row for a slug (the profile strip and the picker's fallback), or null. */
function rbProjRow(slug){
  return typeof LIVE_PROJECTIONS !== "undefined" && LIVE_PROJECTIONS ? LIVE_PROJECTIONS.players[slug] || null : null;
}

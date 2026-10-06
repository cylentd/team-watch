/* Deep link into a research row (2026-10-05, unit U8; David: A + C). Grid (leaf `usage`) and Role
   (leaf `movers`) hold the deepest data, two taps down, so a profile, a Digest line or a Start/Sit
   call can name the player and land on his row: navGoRow(leaf, slug) in chrome/nav.js.

   This file is the part that is data: where each view must stand so his row is drawn. Grid shows one
   position and one week; Role shows RB/WR/TE ranked, twenty rows to a page and a position filter. */

/* `rows` is the view's own rows (USAGE.rows, LIVE_ROLE.rows), `cur` its state: {week} for Grid,
   {pos, first} for Role (`first` = the rows before Show all). Returns what to set, or null when the
   view has no row for him (the caller then opens the view alone).
   Grid: the week on screen if he has a row in it, else his newest, and his position.
   Role: the position filter stays when it holds him, else All; `all` says he is past the first page. */
function navRowPlan(leaf, slug, rows, cur){
  if (!slug || !Array.isArray(rows)) return null;
  if (leaf === "usage"){
    const his = rows.filter(r => r.slug === slug);
    if (!his.length) return null;
    const r = his.find(x => x.wk === cur.week) || his.reduce((a, b) => b.wk > a.wk ? b : a);
    return {leaf, slug, pos: r.pos, week: r.wk};
  }
  if (leaf === "movers"){
    const r = rows.find(x => x.slug === slug);
    if (!r) return null;
    const pos = cur.pos === "ALL" || cur.pos === r.pos ? cur.pos : "ALL";
    const list = pos === "ALL" ? rows : rows.filter(x => x.pos === pos);
    return {leaf, slug, pos, all: list.findIndex(x => x.slug === slug) >= cur.first};
  }
  return null;
}

/* The profile head's second line (2026-09-25): watch's verdict word with its reason, and which of
   my teams he is on when that is more than one. Both used to be tags on the roster row; the row
   became "who, which way, one number" and the storyboard sent them here.

   Looked up by slug, never read off the object that opened the sheet. A roster row carries both,
   but search, Waivers and Movers open the sheet with their own objects, and the line has to say the
   same thing whichever way you arrived. The verdict word is watch's own: the page adds none, and
   NEW and hold are dropped as they were on the row (data/signals.js). */
function sheetTagsHTML(p){
  const slug = p.slug || slugOf(p.n);
  const sig = signalsFor({slug});
  const mine = Object.values(TEAMS).filter(tm => tm.roster && tm.roster.some(r => (r.slug || slugOf(r.n)) === slug));
  const parts = [];
  if (sig.verdict) parts.push(`<span class="tag verdict">${esc(sig.verdict)}</span>`
    + (sig.why ? `<span class="pf-why">${esc(sig.why)}</span>` : ""));
  if (mine.length > 1) parts.push(`<span class="pf-mine">${t("profile.tag.teams", {n: mine.length})}</span>`);
  return parts.length ? `<div class="pf-tags">${parts.join("")}</div>` : "";
}

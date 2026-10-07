/* ============================== DIGEST: SHARED PARTS ==============================
   What Need to know and Tonight's card draw with. The ticker rows' bodies (Matchups, Waiver adds, Gems,
   News) left with the ticker on 2026-10-06 (Digest by day): the day's cards (card.js, row.js, cards/)
   replaced them, and News is a strip link. */

/* A foot: where the numbers come from, and a link to the view that holds all of them. */
function dgFootHTML(text, leaf, label){
  const go = leaf ? `<button type="button" class="dg-go" data-testid="digest-go" data-dggo="${leaf}">${label}${DG_ARROW}</button>` : "";
  return `<div class="dg-foot" data-testid="digest-foot"><span data-testid="digest-foot-text">${text}</span>${go}</div>`;
}

const DG_TAG = {Out: ["out", () => t("digest.tag.out")], IR: ["out", () => t("digest.tag.ir")],
                Doubtful: ["d", () => t("digest.tag.d")], Questionable: ["q", () => t("digest.tag.q")]};

/* Starters (2026-09-29, storyboard JBN1kirnN6jMZNdZK7EmbF): "QB1 over Sanders", "MIN → NYG", or both
   when a traded player starts. `name` shortens the old #1 as the line around it does; `bare` leaves
   out his status. Need to know (need.js) draws them since 2026-09-29. */
function dgStartWhat(r, name, bare){
  const o = r.over;
  const v = o && {pos: esc(r.pos), name: esc(name(o.n)), status: esc(o.status || "")};
  const over = !o ? "" : o.status && !bare ? t("digest.start.overStatus", v) : t("digest.start.over", v);
  // A move says where he stands on the new chart (McCarthy: the Giants' QB3); a new #1 already said it.
  const m = {from: esc(r.from), team: esc(r.team), pos: esc(r.pos), depth: r.depth};
  const moved = !r.from ? "" : !o && r.depth ? t("digest.start.movedDepth", m) : t("digest.start.moved", m);
  return [over, moved].filter(Boolean).join(", ");
}

/* One short list: a head, then "K. Mumpfield" and one number per line (Tonight's lists). */
function dgResList(title, rows, num){
  return rows.length ? `<div><h4>${title}</h4><ol>${rows.map(r => `<li><span class="dg-hd sm">${avatarHTML(r)}</span>`
    + `<span>${esc(dgShort(r.n))}</span>${num(r)}</li>`).join("")}</ol></div>` : "";
}

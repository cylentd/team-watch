/* A pick drawn the way a slip prints it, shared by the deal table (table.js), the pool and the leg
   sheet. The gallery of ready-made slips that gave this file its name was replaced by the deal
   table on 2026-09-29. */
/* A leg read as a sentence, the way the book's own app prints it: "Lower 4.5 Receptions". The
   direction is a small tinted chip (2026-09-25), the way every pick'em slip marks it; nothing is
   in capitals. */
function legCall(l, book){
  if (book === "underdog"){
    const u = udPick(l);
    const dir = u.pick === "higher" ? t("parlay.slip.higher") : u.pick === "lower" ? t("parlay.slip.lower") : "";
    // A model-read TD says so in the pick's details (legRowHTML), not on the call.
    return `${dir ? `<em class="tk-dir ${u.pick}">${dir}</em> ` : ""}${u.line !== null ? `${u.line} ${esc(MKT[l.mkt])}` : esc(MKT.TD)}`;
  }
  return l.line === null ? esc(MKT[l.mkt]) : `<em class="tk-dir higher">${t("parlay.slip.over")}</em> ${l.line} ${esc(MKT[l.mkt])}`;
}

/* The verdict as words, so nobody does the arithmetic (the cart's pay box, slip.js): the slip's
   graded chance (udChance) against what its payout needs, 1/x. A ratio under 1.25 is "near",
   since a rate a few points off erases it. Its title shows both numbers. */
const verdictTone = ratio => ratio >= 1.25 ? "up" : ratio >= 1 ? "near" : "down";
function slipVerdict(ratio, what, model, needs){
  const tone = verdictTone(ratio);
  const text = tone === "up" ? t("parlay.slip.beats", {what}) : tone === "near" ? t("parlay.slip.close", {what}) : t("parlay.slip.short", {what});
  return `<span class="tk-flag ${tone === "near" ? "" : tone}" title="${esc(t("parlay.slip.verdictTip", {model, needs}))}">${text}</span>`;
}

/* One row per pick: his face on his team's colour, his name, the call, the one number (Underdog:
   the model's confidence; DK: the price). A tap opens the leg sheet (legsheet.js, 2026-09-27).
   `tail` is what the row ends in (the deal table's lock); `locked` marks a pick that stays on a
   redeal, so its row does not drop in with the dealt ones. */
function legRowHTML(l, book, i, tail = "", locked = false){
  const ud = book === "underdog", u = ud ? udPick(l) : null;
  const team = (TEAM_COLOURS[l.team] || [])[0];
  return `<div class="tk-leg${locked ? " locked" : ""}" role="button" tabindex="0" aria-haspopup="dialog" data-legsheet="${i}">
      <span class="tk-face" data-slug="${esc(l.slug)}"${team ? ` style="--team:${team}"` : ""}>${avatarHTML(l)}</span>
      <div class="tk-who"><b>${esc(nameInitial(l.n))}</b><span class="tk-call">${legCall(l, book)}</span></div>
      <span class="tk-num">${ud ? `${u.conf}<i>%</i>` : esc(fmtAm(overPrice(l)))}</span>${tail}
    </div>`;
}

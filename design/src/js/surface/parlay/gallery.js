/* A pick read as words, shared by the leg sheet's header and the slip's pay box. The gallery of
   ready-made slips that gave this file its name was replaced by the deal table on 2026-09-29, and
   the deal table by the research board on 2026-10-03 (board.js). */
/* A leg read as a sentence, the way the book's own app prints it: "Lower 4.5 Receptions". The
   direction is a small tinted chip (2026-09-25), the way every pick'em slip marks it; nothing is
   in capitals. A line the model does not call (Longest reception) is the line and its market. */
function legCall(l, book){
  if (book === "underdog"){
    const u = udPick(l), line = slLine(l);
    const dir = u && u.pick === "higher" ? t("parlay.slip.higher") : u && u.pick === "lower" ? t("parlay.slip.lower") : "";
    // A model-read TD says so in the sheet's details, not on the call.
    return `${dir ? `<em class="tk-dir ${u.pick}">${dir}</em> ` : ""}${l.mkt !== "TD" && line != null ? `${line} ${esc(MKT[l.mkt])}` : esc(MKT[l.mkt])}`;
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

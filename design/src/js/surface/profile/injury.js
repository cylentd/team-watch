/* His injury status on the profile (2026-09-30, David: "should injured players have their status on
   the player profile? There's actually nice area to put it"). The level in the tag colours the page
   already uses (filled red out, outlined red doubtful, amber questionable) and Sleeper's reason
   beside it. The same injFor() the roster cards and Need to know read, so the three never disagree.
   A healthy player draws nothing. A line of the name block, under "WR · LV · BYE 13", at every width:
   it is a fact about him, and alone in the head's middle it read as a stray (2026-09-30, David: "this
   placement looks awkward"). */
const PF_INJ_CLS = {OUT: "out", D: "d", Q: "q"};

function pfInjuryHTML(p){
  const r = injFor(p);
  if (!r) return "";
  // IR, PUP and suspension say more than "out", so Sleeper's own code leads when it is not plain Out.
  const word = r.s === "OUT" && r.code && !/^out$/i.test(r.code) ? esc(r.code).toUpperCase() : INJ_WORD[r.s]();
  return `<div class="pf-inj ${PF_INJ_CLS[r.s]}">
    <span class="pf-inj-s">${word}</span>${r.note ? `<span class="pf-inj-n">${esc(r.note)}</span>` : ""}</div>`;
}

/* The wait (2026-09-29, David chose option B of https://claude.ai/artifact/UDoWgLMrzUHup5tX53zaue).
   Once every game of the packet's week has kicked off, the week's preview sections have nothing
   left to say -- Hurt, Matchups, Weather and Top 5 each drop a row the moment its game starts
   (data/digest.js dgCut) -- and next week's are not written until Tuesday's run. Four panels saying
   "Nothing new" read as broken and cost a desktop about 1,000px, so they leave the wall together
   and one card says why, with Blip minding it and one line per section.

   The card is not a row: it has no count and does not open. Tonight's card, while it shows, still
   holds the last game's rows, so the wait waits for it (dgWaiting, data/digest.js). */

function dgWaitLine(id, d, next){
  if (id === "hurt") return t("digest.line.hurtNext", {week: next}) + ".";   // the ticker's line has no stop; a list of sentences does
  if (id === "wx") return t("digest.wait.wx");
  if (id === "t5") return t("digest.wait.t5");
  const r = d.record;
  const rec = r ? " " + t("digest.foot.mu", {us: r.ours.score == null ? "—" : r.ours.score.toFixed(2),
    pl: r.pl.score == null ? "—" : r.pl.score.toFixed(2), wk: r.through}) : "";
  return t("digest.wait.mu", {week: next}) + rec;
}

function dgWaitHTML(d){
  const next = d.week + 1;
  const lines = DG_WAIT_ROWS.map(id => `<li><b>${dgLabel(id)}</b><span>${dgWaitLine(id, d, next)}</span></li>`).join("");
  return `<section class="dg-wait" data-dgrow="wait" aria-labelledby="dg-wait-h">
    <h3 class="dg-wait-h" id="dg-wait-h">${t("digest.wait.title", {week: next})}</h3>
    <div class="dg-wait-blip">${blipSVG(t("digest.wait.blipName"))}<q>${t("digest.wait.blip")}</q></div>
    <ul class="dg-wait-l">${lines}</ul></section>`;
}

/* ------------------------------------------------------------------
   PREVIEW's slate (2026-09-29, storyboard option A): every game of the week, grouped by kickoff
   window, one row each: AWAY @ HOME and Claude's side against the spread with how sure he is, then
   the headline. Claude's record card heads the slate (record.js). A tap opens the game's dossier.
   On a desktop the slate is the rail beside the dossier.

   Quiet since 2026-09-29 (storyboard option B, https://claude.ai/artifact/MpjMnKmnJDKaJij6XLfiUc;
   David: "too many things screaming for attention"): the window heading and the matchup are the
   loud things; the rest is grey. No flags on the slate; the game page carries their facts.

   Colour map: --lime only the game on screen and a confident / very confident pick.
------------------------------------------------------------------ */
/* Every copy key literal (assemble.py --check scans for them). */
const pvWinLabel = w => ({
  thu: t("preview.win.thu"), sunam: t("preview.win.sunam"), sun1: t("preview.win.sun1"),
  sunlate: t("preview.win.sunlate"), sunnight: t("preview.win.sunnight"), mon: t("preview.win.mon"),
}[w.slot] || esc(w.day));

/* A row reads like a newspaper's index: the matchup and Claude's side with how sure he is, then the
   serif headline. A take from before confidence keeps its winner and score right of the matchup. */
function pvRowHTML(g, i, cur){
  const k = g.take, a = k && k.ats;
  const right = a ? `<span class="pv-ats">${pvAtsHTML(g, a)}</span>`
    : k ? `<span class="pv-rs"><i>${esc(k.pick.winner)}</i> ${k.pick.score[k.pick.winner]}–${
      k.pick.score[k.pick.winner === g.home ? g.away : g.home]}</span>` : "";
  return `<li><button class="pv-row${cur ? " cur" : ""}${pvDone(g) ? " done" : ""}" data-pvopen="${i}"${cur ? ` aria-current="true"` : ""}>
    <span class="pv-rm">${esc(g.away)} @ ${esc(g.home)}</span>${right}
    <span class="pv-rh">${k ? esc(k.head) : t("preview.slate.notake")}</span></button></li>`;
}

function pvSlateHTML(cur){
  const gs = pvGames();
  return `<nav class="pv-slate" aria-label="${t("preview.slate.label")}">${pvRecordHTML()}${pvWindows().map(w => `
    <section class="pv-win">
      <h3 class="pv-wh"><span>${pvWinLabel(w)}</span><em>${t("preview.win.times", {times: w.times.join(" · ")})}${
        w.idx.length > 1 ? " · " + t("preview.win.count", {n: w.idx.length}) : ""}</em></h3>
      <ul>${w.idx.map(i => pvRowHTML(gs[i], i, i === cur)).join("")}</ul>
    </section>`).join("")}</nav>`;
}

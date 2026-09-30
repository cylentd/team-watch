/* ------------------------------------------------------------------
   PREVIEW's slate (2026-09-29, storyboard option A): every game of the week, grouped by kickoff
   window, one row each: AWAY @ HOME, "Confident" / "Very confident" when Claude is, then the
   headline. Claude's record card heads the slate (record.js). A tap opens the game's dossier.
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

/* The face a row leads with (storyboard option C, 2026-09-29): the player the headline is about, the
   first of Claude's player calls whose first or last name the headline says ("Dak outguns ...",
   "Love's arm ..."); failing that, his first call. No take, no face: the slot stays empty. */
function pvFacePlayer(k){
  if (!k || !k.players.length) return null;
  const words = k.head.toLowerCase().match(/[a-z]+/g) || [];
  const at = p => { const ns = p.n.toLowerCase().match(/[a-z]+/g) || [];
    const hits = [ns[0], ns[ns.length - 1]].map(n => words.indexOf(n)).filter(i => i >= 0);
    return hits.length ? Math.min(...hits) : Infinity; };
  return k.players.reduce((best, p) => at(p) < at(best) ? p : best, k.players[0]);
}

/* A row reads like a newspaper's index: the matchup and a confident pick's word, then the serif
   headline. A take from before confidence keeps its winner and score right of the matchup. */
function pvRowHTML(g, i, cur){
  /* Only a confident pick speaks on the slate (David, 2026-09-29: drop the "JAX getting 2.5"): its
     word in lime. A slight pick or no pick draws nothing here; the game page says both. */
  const k = g.take, a = k && k.ats, sure = a && a.side && (a.conf === "solid" || a.conf === "strong");
  const right = a ? (sure ? `<span class="pv-ats">${pvConfHTML(a.conf)}</span>` : "")
    : k ? `<span class="pv-rs"><i>${esc(k.pick.winner)}</i> ${k.pick.score[k.pick.winner]}–${
      k.pick.score[k.pick.winner === g.home ? g.away : g.home]}</span>` : "";
  const face = pvFacePlayer(k);
  return `<li><button class="pv-row${cur ? " cur" : ""}${pvDone(g) ? " done" : ""}" data-pvopen="${i}"${cur ? ` aria-current="true"` : ""}>
    <span class="pv-hs" aria-hidden="true">${face ? headHTML(face) : ""}</span>
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

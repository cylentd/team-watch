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
  // A game being played says Live where the pick's word sits; the slate drops it once it is over (pvOver).
  const live = pvDone(g) ? `<span class="pv-live">${t("preview.live")}</span>` : right;
  return `<li><button class="pv-row${cur ? " cur" : ""}" data-pvopen="${i}"${cur ? ` aria-current="true"` : ""}>
    <span class="pv-hs" aria-hidden="true">${face ? headHTML(face) : ""}</span>
    <span class="pv-rm">${esc(g.away)} @ ${esc(g.home)}</span>${live}
    <span class="pv-rh">${k ? esc(k.head) : t("preview.slate.notake")}</span></button></li>`;
}

/* The two ways into Past games (storyboard 1A, 2026-10-05): this week's finals, then the earlier weeks with
   Claude's record. Each row is drawn only when it has something behind it. */
function pvFoldsHTML(){
  const fin = pvFinalIdx().length, wk = LIVE_PREVIEW.week, past = pvArcWeeks().some(w => w < wk);
  const row = (to, title, sub) => `<button type="button" class="pv-fold${PV_REC && PV_ARC_WK === to ? " cur" : ""}" data-pvarcwk="${to}">
    <span><b>${title}</b> · ${sub}</span><span aria-hidden="true">›</span></button>`;
  const rows = [fin ? row(wk, t("preview.arc.finals"), fin === 1 ? t("preview.arc.finalsOne") : t("preview.arc.finalsSub", {n: fin})) : "",
    past ? row(Math.max(...pvArcWeeks().filter(w => w < wk)), t("preview.arc.past"), t("preview.arc.pastSub")) : ""].join("");
  return rows ? `<div class="pv-folds">${rows}</div>` : "";
}

function pvSlateHTML(cur){
  const gs = pvGames(), wins = pvWindows();
  const empty = wins.length ? "" : `<p class="pv-allover">${t("preview.slate.done")}</p>`;
  return `<nav class="pv-slate" aria-label="${t("preview.slate.label")}">
    <h2 class="pv-title">${t("preview.slate.title", {n: LIVE_PREVIEW.week})}</h2>${empty}${wins.map(w => `
    <section class="pv-win">
      <h3 class="pv-wh"><span>${pvWinLabel(w)}</span><em>${esc(w.times.join(" · "))}${
        w.idx.length > 1 ? " · " + t("preview.win.count", {n: w.idx.length}) : ""}</em></h3>
      <ul>${w.idx.map(i => pvRowHTML(gs[i], i, i === cur)).join("")}</ul>
    </section>`).join("")}${pvFoldsHTML()}</nav>`;
}

/* ------------------------------------------------------------------
   PREVIEW's slate (2026-09-29, storyboard option A): every game of the week, grouped by kickoff
   window, one row each: AWAY @ HOME and Claude's side against the spread with its chip, then the
   headline and one flag (design/preview.py _flags). Claude's record card heads the slate
   (record.js). A tap opens the game's dossier. On a desktop the slate is the rail beside the dossier.

   Colour map: --lime Claude (the STRONG chip's fill, SOLID's outline) and UPSET; --amber a line
   that moved, --sky weather that moves scoring, --down a key player out; a short week is --ink-2.
   Every flag carries its word.
------------------------------------------------------------------ */
/* Every copy key literal (assemble.py --check scans for them). */
const pvWinLabel = w => ({
  thu: t("preview.win.thu"), sunam: t("preview.win.sunam"), sun1: t("preview.win.sun1"),
  sunlate: t("preview.win.sunlate"), sunnight: t("preview.win.sunnight"), mon: t("preview.win.mon"),
}[w.slot] || esc(w.day));

function pvFlagHTML(f){
  if (f.k === "upset") return `<b class="pv-f upset">${t("preview.flag.upset")}</b>`;
  if (f.k === "moved") return `<span class="pv-f moved">${f.flip ? t("preview.flag.flipped") : t("preview.flag.moved", {n: pvNum(f.by)})}</span>`;
  if (f.k === "wx") return `<span class="pv-f wx">${f.rain ? t("preview.rain", {n: f.rain}) : t("preview.flag.wind", {n: f.wind})}</span>`;
  if (f.k === "out") return `<span class="pv-f out">${t("preview.flag.out", {n: shortName(f.n)})}</span>`;
  if (f.k === "short") return `<span class="pv-f short">${t("preview.flag.short")}</span>`;
  return "";
}

/* A row reads like a newspaper's index (2026-09-29, storyboard option C; David: "super busy"): the
   matchup and Claude's side with its chip, then the serif headline and the one flag that matters most
   (the producer sorts them). Win %, the score and the total moved to the game's box score. A take
   from before confidence keeps its winner and score right of the matchup. */
function pvRowHTML(g, i, cur){
  const k = g.take, a = k && k.ats, f = g.flags[0];
  const right = a ? `<span class="pv-ats">${pvAtsHTML(g, a)}</span>`
    : k ? `<span class="pv-rs"><i>${esc(k.pick.winner)}</i> ${k.pick.score[k.pick.winner]}–${
      k.pick.score[k.pick.winner === g.home ? g.away : g.home]}</span>` : "";
  return `<li><button class="pv-row${cur ? " cur" : ""}${pvDone(g) ? " done" : ""}" data-pvopen="${i}"${cur ? ` aria-current="true"` : ""}>
    <span class="pv-rm">${esc(g.away)} @ ${esc(g.home)}</span>${right}
    <span class="pv-rh">${k ? esc(k.head) : t("preview.slate.notake")}${f ? ` <span class="pv-flag">${pvFlagHTML(f)}</span>` : ""}</span></button></li>`;
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

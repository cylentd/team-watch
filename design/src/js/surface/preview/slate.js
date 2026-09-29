/* ------------------------------------------------------------------
   PREVIEW's slate (2026-09-29, storyboard option A): every game of the week, grouped by kickoff
   window, one row each. A row says why to open it: AWAY @ HOME, Claude's winner and score, the
   headline, then the spread in words, the total and at most two flags (design/preview.py _flags).
   Since 2026-09-29 (confidence, storyboard option A) Claude's side against the spread and its chip
   sit right of the matchup, over his win % beside the market's; Claude's record card heads the slate
   (record.js). A tap opens the game's dossier. On a desktop the slate is the rail beside the dossier.

   Colour map: --lime Claude (the STRONG chip's fill, SOLID's outline, the bar's dot, his win %) and
   UPSET; grey the market (the bar's tick); --amber a line that moved, --sky weather that moves
   scoring, --down a key player out; a short week is --ink-2. Every flag carries its word.
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

/* Claude's winner and score, its win % beside the market's ("IND wins 27–19 · market 62% · Claude 71%"),
   then the bar: grey tick the market, lime dot Claude, the gap between them filled faintly. No market
   win % (a missing moneyline), no bar. A take from before confidence has no `win`, so no line. */
function pvOddsHTML(g){
  const k = g.take, w = k.pick.winner, lo = w === g.home ? g.away : g.home;
  const cl = k.win && k.win[w], mk = g.market_win && g.market_win[w];
  if (cl == null) return "";
  const pct = [mk != null ? `<span>${t("preview.odds.market", {n: Math.round(mk)})}</span>` : "",
    `<b>${t("preview.odds.claude", {n: cl})}</b>`].filter(Boolean).join(" · ");
  const key = `<span class="pv-key"><span>${t("preview.odds.wins", {team: esc(w), a: k.pick.score[w], b: k.pick.score[lo]})}</span><span>${pct}</span></span>`;
  if (mk == null) return key;
  const r1 = n => Math.round(n * 10) / 10;
  return key + `<span class="pv-pb" aria-hidden="true" style="--mk:${r1(mk)}%;--cl:${r1(cl)}%;--lo:${r1(Math.min(mk, cl))}%;--gap:${r1(Math.abs(cl - mk))}%">
    <i class="pv-pbt"></i><i class="pv-pbf"></i><i class="pv-pbm"></i><i class="pv-pbc"></i></span>`;
}

function pvRowHTML(g, i, cur){
  const k = g.take, l = g.line, a = k && k.ats;
  /* Right of the matchup: Claude's side against the spread and its chip; a take from before confidence
     keeps its winner and score there. The side already says the spread, so the meta drops it then. */
  const right = a ? `<span class="pv-ats">${pvAtsHTML(g, a)}</span>`
    : k ? `<span class="pv-rs"><i>${esc(k.pick.winner)}</i> ${k.pick.score[k.pick.winner]}–${
      k.pick.score[k.pick.winner === g.home ? g.away : g.home]}</span>` : "";
  const meta = [l && !(a && a.side) ? `<span>${pvSpread(l.fav, l.by)}</span>` : "",
    l && l.total != null ? `<span>${t("preview.line.total", {n: pvNum(l.total)})}</span>` : "",
    ...g.flags.map(pvFlagHTML)].join("");
  return `<li><button class="pv-row${cur ? " cur" : ""}${pvDone(g) ? " done" : ""}" data-pvopen="${i}"${cur ? ` aria-current="true"` : ""}>
    <span class="pv-rm">${esc(g.away)} @ ${esc(g.home)}</span>${right}
    ${a ? pvOddsHTML(g) : ""}
    <span class="pv-rh">${k ? esc(k.head) : t("preview.slate.notake")}</span>
    ${meta ? `<span class="pv-meta">${meta}</span>` : ""}</button></li>`;
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

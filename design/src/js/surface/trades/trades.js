/* ============================== LEAGUE > RECORDS > TRADE HISTORY (Yahoo) ==============================
   2026-09-28 as the Trades leaf, 2026-10-06 to 2026-10-08 the Trade history tab of Records, since 2026-10-08 its
   own League leaf `tradehist` (the Trades leaf is the finder), storyboard https://claude.ai/artifact/EhbDwDUZ7ERb2iNfAqaKjn. Who trades best and worst, each
   manager's trades, the heists, the trades that decided a season, and the curses. The same page for every
   reader. One basis per row (David, 2026-09-28): a manager's W-L, dot and trade list count only the weeks
   each team held a player; the trade tree decides the cards (cards.js), and a trade whose tree verdict
   differs says so in the list. */

/* The dot is the average PAR per trade, the line its 90% range, on one fixed scale so rows compare. */
const TR_LO = -70, TR_HI = 90;
const trX = v => (100 * (Math.max(TR_LO, Math.min(TR_HI, v)) - TR_LO) / (TR_HI - TR_LO)).toFixed(1);
/* W–L, and –T when a trade tied: a trade made with no weeks left scores 0.0 both ways (Andrew's 2021
   week-15 trade, David 2026-09-28: "how did Andrew make 5 trades and is 4-0?"). Closed trades only. */
const trWL = r => { const ties = r.trades - r.won - r.lost; return `${r.won}–${r.lost}${ties ? `–${ties}` : ""}`; };
const trSigned = n => `${n > 0 ? "+" : n < 0 ? "−" : ""}${trPar(Math.abs(n))}`;
let TR_OPEN = null;   // the manager whose trades are open; one at a time, kept for the session

/* Best and worst: the top and bottom of the ranking among managers with enough trades. The trade that
   defines each is the best manager's biggest win and the worst's biggest loss, on held weeks like the
   ranking's row. */
const TR_LEAD_ICON = {
  best: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 8.5 8 12.5 12 5l4 7.5 4.5-4-1.8 9.5H5.3z M5.5 20h13" fill="currentColor" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>`,
  worst: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7l6 6 4-4 8 8M21 11v6h-6" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
};
function trDefining(key, best){
  const mine = trData().trades.filter(x => !x.open && (x.win.m === key || x.lose.m === key) && (x.held.win === key) === best);
  if (!mine.length) return null;
  const tr = mine.reduce((a, b) => b.held.margin > a.held.margin ? b : a);
  const me = tr.win.m === key ? tr.win : tr.lose, them = tr.win.m === key ? tr.lose : tr.win;
  return {tr, them, side: best ? me : them};
}
/* The story is the headline, the number and record its deck, and the defining trade the proof, as the
   same two rows a heist has (so the top row's cards match by content, 2026-09-29). The worst trader's
   headline roots for the next trade (David: "trading is healthy, we should promote it"). */
function trLeadCardHTML(r, k){
  const best = k === "best", d = trDefining(r.m, best), cls = best ? "up" : "dn", m = trName(r.m);
  // "is due" is a forward claim nothing has tested: the tooltip says so (2026-10-06).
  const head = !best ? `<span title="${t("trades.lead.dueMark")}">${t("trades.lead.due", {m})}</span>` : r.lost ? t("trades.lead.wins", {m}) : t("trades.lead.clean", {m});
  const fv = d && {y: d.tr.season, n: trB(`${best ? "+" : "−"}${trPar(d.tr.held.margin)}`, cls)};
  const foot = d ? `<p>${best ? t("trades.lead.bestTrade", fv) : t("trades.lead.worstTrade", fv)}</p>` : "";
  return trBox(`tr-lead-card ${k}`, `<span class="tr-lead-ic">${TR_LEAD_ICON[k]}</span>${best ? t("trades.lead.best") : t("trades.lead.worst")}`,
    t("trades.lead.n", {n: r.trades}),
    trHead(head, t("trades.lead.deck", {n: trB(trSigned(r.per_trade), cls), wl: trB(trWL(r))})) + (d ? trScoreRows(d.tr) : ""), foot);
}
/* The ranking's order is the number it shows, PAR per trade (David, 2026-09-29: "sort by shown"); ff-jarvis
   sorts by the shrunk figure, which put David's +6.0 over Kearny's +6.3. The too-few divider keeps a
   one-trade manager from topping it. Best and worst read the same order. */
function trRanked(){
  const R = [...trData().ranking].sort((a, b) => b.per_trade - a.per_trade);
  return {main: R.filter(r => !r.few), few: R.filter(r => r.few)};
}
/* The top row: best, worst and the three heists, five cards across a desktop, one swipe row on a phone. */
function trTopHTML(){
  const rows = trRanked().main;
  const lead = rows.length ? trLeadCardHTML(rows[0], "best") + trLeadCardHTML(rows[rows.length - 1], "worst") : "";
  const n = (rows.length ? 2 : 0) + trData().heists.length;
  return n ? `<section class="tr-sec tr-top">${trPagerHTML(n)}<div class="tr-swipe tr-top-row">${lead}${trHeistCardsHTML()}</div></section>` : "";
}

function trTrackHTML(r){
  const kind = r.hi < 0 ? "dn" : r.lo > 0 ? "up" : "";
  return `<span class="tr-track ${kind}" aria-hidden="true" style="--z:${trX(0)}%;--lo:${trX(r.lo)}%;--hi:${trX(r.hi)}%;--x:${trX(r.per_trade)}%">
    <i class="tr-zero"></i><i class="tr-range"></i><i class="tr-dot"></i></span>`;
}

/* One manager's trades, wins first, each a small box score: the result, when and with whom, and by how
   much in the strip; what he got and gave as rows of faces; a flip or what it decided as the footnote. */
function trMineHTML(key){
  const mine = trData().trades.filter(x => x.win.m === key || x.lose.m === key)
    .map(tr => ({tr, won: tr.held.win === key})).sort((a, b) => (b.won - a.won) || (b.tr.held.margin - a.tr.held.margin));
  const rows = mine.map(({tr, won}, i) => {
    const me = tr.win.m === key ? tr.win : tr.lose, them = tr.win.m === key ? tr.lose : tr.win;
    const tie = !tr.open && !tr.held.margin;
    const res = tr.open ? `<span class="tr-res open">·</span>` : tie ? `<span class="tr-res open">${t("trades.res.t")}</span>`
      : `<span class="tr-res ${won ? "up" : "dn"}">${won ? t("trades.res.w") : t("trades.res.l")}</span>`;
    const tree = !tr.open && tr.win.m !== tr.held.win ? `<p class="tr-flip">${t("trades.row.tree", {m: trName(tr.win.m), n: trPar(tr.margin)})}</p>` : "";
    const when = tr.open ? t("trades.row.whenOpen", {y: tr.season, w: tr.week, m: trName(them.m)}) : t("trades.row.when", {y: tr.season, w: tr.week, m: trName(them.m)});
    return `<li style="--i:${Math.min(i, 8)}">${trBox("tr-row", `${res}${when}`, tie ? `<b>${trPar(0)}</b>` : `<b class="${tr.open ? "live" : won ? "up" : "dn"}">${won ? "+" : "−"}${trPar(tr.held.margin)}</b>`,
      `<table class="tr-sc tr-io"><tr><th scope="row">${t("trades.row.got")}</th><td>${trPlayersHTML(me.got, me.slugs)}</td></tr>
        <tr class="tr-l"><th scope="row">${t("trades.row.gave")}</th><td>${trPlayersHTML(them.got, them.slugs)}</td></tr></table>`,
      tree + trDecidedHTML(tr))}</li>`;
  }).join("");
  return `<ul class="tr-mine">${rows}</ul>`;
}

/* Each row: its place, the manager, the number beside the name, its likely range, the record beside it.
   Column heads name each part, so no legend paragraph (2026-09-29). Managers with too few trades sit
   under their own divider, unnumbered. */
function trRankHTML(){
  const {main, few} = trRanked();
  const row = (r, i) => {
    const open = TR_OPEN === r.m, kind = r.hi < 0 ? "dn" : r.lo > 0 ? "up" : "";
    return `<li class="${r.few ? "few" : ""}"><button type="button" class="tr-mgr" data-trmgr="${esc(r.m)}" aria-expanded="${open}"
        aria-label="${t("trades.rank.aria", {m: trName(r.m), n: trSigned(r.per_trade), wl: trWL(r)})}">
      <span class="tr-i">${r.few ? "" : i + 1}</span><b>${trName(r.m)}</b><span class="tr-v ${kind}">${trSigned(r.per_trade)}</span>${trTrackHTML(r)}<span class="tr-wl">${trWL(r)}</span><span class="tr-chev" aria-hidden="true">›</span></button>
      ${open ? trMineHTML(r.m) : ""}</li>`;
  };
  const cols = `<div class="tr-rkh" aria-hidden="true"><span>${t("trades.rank.colI")}</span><span>${t("trades.rank.colM")}</span><span>${t("trades.rank.colN")}</span><span>${t("trades.rank.colR")}</span><span>${t("trades.rank.colWL")}</span><span></span></div>`;
  const rows = main.map(row).join("") + (few.length ? `<li class="tr-fewhd">${t("trades.rank.few")}</li>${few.map(row).join("")}` : "");
  return `<section class="tr-sec tr-rank"><h2 class="tr-hd">${t("trades.rank.title")}</h2>
    ${cols}<ol class="tr-mgrs">${rows}</ol><p class="tr-note">${t("trades.rank.key")}</p></section>`;
}

/* League > Trade history: the same page for every reader. */
function trPageHTML(){
  const D = trData();
  if (!lgUsePicked()) return `<div class="wrap"><p class="tr-none">${t("trades.none")}</p></div>`;
  // A league ff-jarvis has not graded trades for (AYO, 2026-09-29) says so under the switch.
  if (!D) return `<div class="wrap">${lgChipHTML()}<div class="tr"><header class="tr-head"><h1>${esc(LG.league)}</h1></header>
    <p class="tr-none">${t("trades.empty")}</p></div></div>`;
  // What PAR means comes before the first number it explains (2026-09-29), then the answer (best, worst,
  // the heists). The sections are siblings in one grid, not two columns: on a desktop the ranking pairs
  // with the curses (trades.css places them) and the decided trades take the full width.
  return `<div class="wrap">${lgChipHTML()}<div class="tr"><header class="tr-head"><h1>${esc(LG.league)}</h1>
      <p class="tr-kick">${t("trades.page.kick", {a: D.since, b: D.through, n: D.n})}</p><p class="tr-what">${t("trades.page.what")}</p></header>
    ${trTopHTML()}
    <div class="tr-body">${trRankHTML()}${trDecidedBlockHTML()}${trCursesHTML()}</div></div></div>`;
}

/* A manager row opens their trades under it (closing any other); Show all opens the rest of the cards.
   Each redraws only its own section, so nothing beside it moves. */
function wireTrades(v){
  wireLgChip(v);
  const root = v.querySelector(".tr");
  if (!root || !trData()) return;
  root.addEventListener("click", e => {
    const b = e.target.closest("[data-trmgr],[data-trall],[data-trcurse]");
    if (!b) return;
    if (b.hasAttribute("data-trcurse")){
      b.classList.remove("stir");
      void b.offsetWidth;   // restart the animation on a second tap
      b.classList.add("stir");
    } else if (b.dataset.trmgr){
      TR_OPEN = TR_OPEN === b.dataset.trmgr ? null : b.dataset.trmgr;
      root.querySelector(".tr-rank").outerHTML = trRankHTML();
      root.querySelector(`[data-trmgr="${CSS.escape(b.dataset.trmgr)}"]`)?.focus();
      trWatchRows(root);
    } else {
      TR_ALL = true;
      root.querySelector(".tr-decided").outerHTML = trDecidedBlockHTML();
    }
  });
  trWatchRows(root);   // alive.js
  trShuffle(root);
  trSwipes(root);
}

/* ============================== LEAGUE > TRADES (Yahoo) ==============================
   2026-09-28, storyboard https://claude.ai/artifact/EhbDwDUZ7ERb2iNfAqaKjn. Who trades best and worst, each
   manager's trades, the heists, the trades that decided a season, and the curses. The same page for every
   reader. One basis per row (David, 2026-09-28): a manager's W-L, dot and trade list count only the weeks
   each team held a player; the trade tree decides the cards (cards.js), and a trade whose tree verdict
   differs says so in the list. */

/* The dot is the average PAR per trade, the line its 90% range, on one fixed scale so rows compare. */
const TR_LO = -70, TR_HI = 90;
const trX = v => (100 * (Math.max(TR_LO, Math.min(TR_HI, v)) - TR_LO) / (TR_HI - TR_LO)).toFixed(1);
const trWL = r => `${r.won}–${r.lost}`;
const trSigned = n => `${n > 0 ? "+" : n < 0 ? "−" : ""}${trPar(Math.abs(n))}`;
let TR_OPEN = null;   // the manager whose trades are open; one at a time, kept for the session

/* Best and worst: the top and bottom of the ranking among managers with enough trades, and whether
   either is proven (a range that stays clear of 0). */
function trLeadHTML(){
  const rows = trData().ranking.filter(r => !r.few);
  if (!rows.length) return "";
  const best = rows[0], worst = rows[rows.length - 1];
  const row = (r, k) => `<div class="tr-lead-row"><span class="tr-tag ${k}">${k === "best" ? t("trades.lead.best") : t("trades.lead.worst")}</span>
    <b>${trName(r.m)}</b><span class="tr-lead-n">${trSigned(r.per_trade)}<small>${t("trades.lead.per", {wl: trWL(r)})}</small></span></div>`;
  const proven = [best.lo > 0 && best, worst.hi < 0 && worst].filter(Boolean);
  const note = proven.length ? t("trades.lead.proven", {m: proven.map(r => trName(r.m)).join(" & ")}) : t("trades.lead.none");
  return `<section class="tr-lead">${row(best, "best")}${row(worst, "worst")}<p class="tr-note">${note}</p></section>`;
}

function trTrackHTML(r){
  const kind = r.hi < 0 ? "dn" : r.lo > 0 ? "up" : "";
  return `<span class="tr-track ${kind}" aria-hidden="true" style="--z:${trX(0)}%;--lo:${trX(r.lo)}%;--hi:${trX(r.hi)}%;--x:${trX(r.per_trade)}%">
    <i class="tr-zero"></i><i class="tr-range"></i><i class="tr-dot"></i></span>`;
}

/* One manager's trades, wins first, each one line: when and with whom, what they got and gave, by how much. */
function trMineHTML(key){
  const mine = trData().trades.filter(x => x.win.m === key || x.lose.m === key)
    .map(tr => ({tr, won: tr.held.win === key})).sort((a, b) => (b.won - a.won) || (b.tr.held.margin - a.tr.held.margin));
  const rows = mine.map(({tr, won}) => {
    const me = tr.win.m === key ? tr.win : tr.lose, them = tr.win.m === key ? tr.lose : tr.win;
    const res = tr.open ? `<span class="tr-res open">·</span>` : `<span class="tr-res ${won ? "up" : "dn"}">${won ? t("trades.res.w") : t("trades.res.l")}</span>`;
    const tree = !tr.open && tr.win.m !== tr.held.win ? `<span class="tr-flip">${t("trades.row.tree", {m: trName(tr.win.m), n: trPar(tr.margin)})}</span>` : "";
    return `<li class="tr-row">${res}<div>
      <p class="tr-when">${tr.open ? t("trades.row.whenOpen", {y: tr.season, w: tr.week, m: trName(them.m)}) : t("trades.row.when", {y: tr.season, w: tr.week, m: trName(them.m)})}</p>
      <p>${t("trades.row.got", {list: trList(me.got)})}</p><p class="tr-gave">${t("trades.row.gave", {list: trList(them.got)})}</p>
      ${tree}${trDecidedHTML(tr)}</div>
      <b class="tr-by ${tr.open ? "open" : won ? "up" : "dn"}">${won ? "+" : "−"}${trPar(tr.held.margin)}</b></li>`;
  }).join("");
  return `<ul class="tr-mine">${rows}</ul>`;
}

function trRankHTML(){
  const scale = `<div class="tr-scale" aria-hidden="true"><span></span><span class="tr-ticks">${[-50, 0, 50]
    .map(v => `<i style="--x:${trX(v)}%">${trSigned(v).replace(".0", "")}</i>`).join("")}</span><span></span></div>`;
  const rows = trData().ranking.map(r => {
    const open = TR_OPEN === r.m;
    return `<li class="${r.few ? "few" : ""}"><button type="button" class="tr-mgr" data-trmgr="${esc(r.m)}" aria-expanded="${open}"
        aria-label="${t("trades.rank.aria", {m: trName(r.m), n: trSigned(r.per_trade), wl: trWL(r)})}">
      <b>${trName(r.m)}</b>${trTrackHTML(r)}<span class="tr-wl">${trWL(r)}</span><span class="tr-chev" aria-hidden="true">›</span></button>
      ${open ? `${r.few ? `<p class="tr-note">${t("trades.rank.few")}</p>` : ""}${trMineHTML(r.m)}` : ""}</li>`;
  }).join("");
  return `<section class="tr-sec tr-rank"><h2 class="tr-hd">${t("trades.rank.title")}<span>${t("trades.rank.sub")}</span></h2>
    ${scale}<ol class="tr-mgrs">${rows}</ol>${scale}<p class="tr-note">${t("trades.rank.key")}</p></section>`;
}

/* League > Trades: the same page for every reader. */
function trPageHTML(){
  const D = trData();
  if (!D || !lgUseYahoo()) return `<div class="wrap"><p class="tr-none">${t("trades.none")}</p></div>`;
  // The answer first (best and worst), then what PAR means: the first data ends above ~200px on a phone.
  return `<div class="wrap"><div class="tr"><header class="tr-head"><h1>${esc(LG.league)}</h1>
      <p class="tr-kick">${t("trades.page.kick", {a: D.since, b: D.through, n: D.n})}</p></header>
    ${trLeadHTML()}<p class="tr-what">${t("trades.page.what")}</p><div class="tr-cols"><div class="tr-col">${trRankHTML()}</div>
    <div class="tr-col">${trHeistsHTML()}${trDecidedBlockHTML()}${trCursesHTML()}</div></div></div></div>`;
}

/* A manager row opens their trades under it (closing any other); Show all opens the rest of the cards.
   Each redraws only its own section, so nothing beside it moves. */
function wireTrades(v){
  const root = v.querySelector(".tr");
  if (!root) return;
  root.addEventListener("click", e => {
    const b = e.target.closest("[data-trmgr],[data-trall]");
    if (!b) return;
    if (b.dataset.trmgr){
      TR_OPEN = TR_OPEN === b.dataset.trmgr ? null : b.dataset.trmgr;
      root.querySelector(".tr-rank").outerHTML = trRankHTML();
      root.querySelector(`[data-trmgr="${CSS.escape(b.dataset.trmgr)}"]`)?.focus();
    } else {
      TR_ALL = true;
      root.querySelector(".tr-decided").outerHTML = trDecidedBlockHTML();
    }
  });
}

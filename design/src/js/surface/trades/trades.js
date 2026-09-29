/* ============================== LEAGUE > TRADES (Yahoo) ==============================
   2026-09-28, storyboard https://claude.ai/artifact/EhbDwDUZ7ERb2iNfAqaKjn. Who trades best and worst, each
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

/* Best and worst: the top and bottom of the ranking among managers with enough trades, as box scores
   (2026-09-28): the verdict icon and label in the strip, the manager with his number beside him, one
   sentence saying how sure (with its reason), and the trade that defines him as faces: the best
   manager's biggest win (what he got), the worst's biggest loss (what he gave). Held weeks, like his
   row. The ranking's track is not repeated here; it sits right below. */
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
/* The record sits in the strip; no luck sentence (David, 2026-09-28: "no need to say that"), the
   ranking's line under it already says how sure. */
function trLeadCardHTML(r, k){
  const best = k === "best", d = trDefining(r.m, best), cls = best ? "up" : "dn";
  const trade = d ? `<div class="tr-bx-ft tr-def"><p>${best ? t("trades.lead.bestTrade", {y: d.tr.season, m: trName(d.them.m)})
      : t("trades.lead.worstTrade", {y: d.tr.season, m: trName(d.them.m)})}</p>
    <div class="tr-def-row">${trPlayersHTML(d.side.got, d.side.slugs)}<b class="${cls}">${best ? "+" : "−"}${trPar(d.tr.held.margin)}</b></div></div>` : "";
  return trBox(`tr-lead-card ${k}`, `<span class="tr-lead-ic">${TR_LEAD_ICON[k]}</span>${best ? t("trades.lead.best") : t("trades.lead.worst")}`,
    t("trades.lead.n", {n: r.trades, wl: trWL(r)}),
    `<div class="tr-lead-in"><p class="tr-lead-who"><b>${trName(r.m)}</b><span class="${cls}">${trSigned(r.per_trade)}</span><small>${t("trades.lead.per")}</small></p></div>${trade}`);
}
/* The top row: best, worst and the three heists, five cards across a desktop, one swipe row on a phone. */
function trTopHTML(){
  const rows = trData().ranking.filter(r => !r.few);
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

function trRankHTML(){
  const scale = `<div class="tr-scale" aria-hidden="true"><span></span><span class="tr-ticks">${[-50, 0, 50]
    .map(v => `<i style="--x:${trX(v)}%">${trSigned(v).replace(".0", "")}</i>`).join("")}</span><span></span></div>`;
  // Managers with too few trades sit under their own divider (2026-09-28): the list is sorted with luck
  // taken out, so Larry's one-trade dot right of the leader's read as a mistake among the rest.
  const R = trData().ranking, few = R.filter(r => r.few);
  const row = r => {
    const open = TR_OPEN === r.m;
    return `<li class="${r.few ? "few" : ""}"><button type="button" class="tr-mgr" data-trmgr="${esc(r.m)}" aria-expanded="${open}"
        aria-label="${t("trades.rank.aria", {m: trName(r.m), n: trSigned(r.per_trade), wl: trWL(r)})}">
      <b>${trName(r.m)}</b>${trTrackHTML(r)}<span class="tr-wl">${trWL(r)}</span><span class="tr-chev" aria-hidden="true">›</span></button>
      ${open ? trMineHTML(r.m) : ""}</li>`;
  };
  const rows = R.filter(r => !r.few).map(row).join("")
    + (few.length ? `<li class="tr-fewhd">${t("trades.rank.few")}</li>${few.map(row).join("")}` : "");
  return `<section class="tr-sec tr-rank"><h2 class="tr-hd">${t("trades.rank.title")}<span>${t("trades.rank.sub")}</span></h2>
    ${scale}<ol class="tr-mgrs">${rows}</ol>${scale}<p class="tr-note">${t("trades.rank.key")}</p></section>`;
}

/* League > Trades: the same page for every reader. */
function trPageHTML(){
  const D = trData();
  if (!D || !lgUseYahoo()) return `<div class="wrap"><p class="tr-none">${t("trades.none")}</p></div>`;
  // The answer first (best, worst, the heists), then what PAR means. The sections are siblings in one
  // grid, not two columns: on a desktop the ranking pairs with the curses (trades.css places them) and
  // the decided trades take the full width, so no column runs on alone.
  return `<div class="wrap"><div class="tr"><header class="tr-head"><h1>${esc(LG.league)}</h1>
      <p class="tr-kick">${t("trades.page.kick", {a: D.since, b: D.through, n: D.n})}</p></header>
    ${trTopHTML()}<p class="tr-what">${t("trades.page.what")}</p>
    <div class="tr-body">${trRankHTML()}${trDecidedBlockHTML()}${trCursesHTML()}</div></div></div>`;
}

/* A manager row opens their trades under it (closing any other); Show all opens the rest of the cards.
   Each redraws only its own section, so nothing beside it moves. */
function wireTrades(v){
  const root = v.querySelector(".tr");
  if (!root) return;
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

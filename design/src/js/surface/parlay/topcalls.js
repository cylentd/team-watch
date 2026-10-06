/* TOP CALLS, the first section of Slips (2026-10-05, plan "Bets UX" change 1): "what should I bet" answered
   before the board. The model's strongest lines in games that have not kicked off, five of them, strongest
   first (data/topcalls.js does the choosing). Each row is a verdict you can read at a glance: the side and
   the line, the model's chance of that side with its tier word, and what that chance is over the book's
   break-even. The row opens the player's sheet; the round + puts that side on the slip in one tap, the same
   path as a side tapped on the sheet (lineitem.js slPick). Not a new view: it sits under the record strip. */
const SL_TOP_N = 5;

function slTopRowHTML(c, on){
  const p = PROPS[c.i], mkt = SL_MKT_WORD()[c.mkt] || c.mkt, side = t(c.side === "lower" ? "slips.side.lower" : "slips.side.higher");
  const agree = slClaudeAgrees(slClaude(p), {side: c.side, tier: c.tier}) ? slClaudeBadge(true) : "";
  const edge = c.edge === null ? t("slips.top.noEdge") : t("slips.top.edge", {edge: c.edge, be: c.be});
  return `<li class="tpc-row">
      <button type="button" class="tpc-main" data-slplayer="${esc(c.slug)}" aria-haspopup="dialog" aria-label="${t("slips.top.open", {name: esc(nameInitial(c.n))})}">
        <span class="tpc-who"><b>${esc(nameInitial(c.n))}</b><span class="tpc-pos">${esc(c.pos)} · ${esc(c.team)}</span></span>
        ${slTierHTML(c.tier, c.pct)}
        <span class="tpc-sub"><span class="tpc-pick">${t("slips.pick.label", {side, mkt})} <b>${c.line}</b>${agree}</span>
          <span class="tpc-edge${c.edge !== null && c.edge > 0 ? " up" : ""}">${edge}</span></span>
      </button>
      <button type="button" class="tpc-add${on ? " on" : ""}" data-slpick="${c.i}" data-side="${c.side}" aria-pressed="${on}"
        aria-label="${t("slips.top.add", {side, mkt, name: esc(nameInitial(c.n))})}"><i aria-hidden="true"></i></button>
    </li>`;
}

function slTopHTML(){
  const calls = topCalls(PROPS, {now: NOW, book: PARLAY_BOOK, limit: SL_TOP_N});
  if (!calls.length) return "";
  return `<section class="tpc" aria-labelledby="tpc-h">
      <header class="tpc-head"><h2 id="tpc-h">${t("slips.top.title")}</h2><span>${t("slips.top.sub")}</span></header>
      <ul class="tpc-rows">${calls.map(c => slTopRowHTML(c, SLIP.includes(c.i) && slipSide(c.i) === c.side)).join("")}</ul>
    </section>`;
}

/* The + puts the call's side on the slip, the same side again takes it off. */
function wireSlTop(v){
  v.querySelectorAll(".tpc [data-slpick]").forEach(b => b.addEventListener("click", () => slPick(b)));
}

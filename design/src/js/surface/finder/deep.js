/* ============================== LEAGUE > TRADES: WHO IS DEEP ==============================
   2026-10-06 (trade finder, unit U4). Under the offers: every other team in the league ranked by the chip's column
   (finder/logic.js tfDeep), the sum shown on the Teams cards' tint, and who starts there, as initials. Meant for a reader
   who wants to ask a team himself, not only take an offer: a row opens nothing, a team's NAME opens the finder filtered
   to him (finder.js). Not drawn in that filtered state. */
function tfDeepRowHTML(d){
  const rec = d.record ? ` <small>${d.record}</small>` : "";
  return `<li class="tf-d" data-testid="finder-deeprow"><button type="button" class="tf-dn" data-tfwho="${esc(d.key)}"
      aria-label="${t("finder.deep.with", {name: esc(d.name)})}" data-testid="finder-deepname"><b>${esc(d.name)}</b>${rec}</button>
    <span class="tf-dv ${d.tone}" data-testid="finder-deepval">${lbNum(d.val)}</span>
    <span class="tf-ds" data-testid="finder-deepstarters">${d.starters.length ? d.starters.map(esc).join(", ") : t("finder.deep.none")}</span></li>`;
}

function tfDeepHTML(lg, me){
  return `<section class="tf-deep" data-testid="finder-deep"><h2 class="tf-h">${t("finder.deep.title", {pos: TF.pos})}</h2>
    <ol class="tf-dl">${tfDeep(lg, TF.pos, me.key).map(tfDeepRowHTML).join("")}</ol></section>`;
}

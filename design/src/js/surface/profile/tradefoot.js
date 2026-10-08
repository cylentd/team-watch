/* ============================== PROFILE: THE FOOTER ==============================
   2026-10-08 (ledger #51, storyboard trades-pin frame 1). The profile's bottom edge, in the thumb's reach (STYLE.md
   "Overlays": a reading modal also closes from a footer on a phone): Close, and beside it the way to trade him.
   "Trade for him" when another team in the reader's league has him, "Shop him" when he is the reader's own; neither for
   a free agent, a player in another league, a kicker or a defense, or a reader with no team. Either opens his trade
   page (finder/tpage.js). On a desktop the ✕ closes and the footer keeps only the trade button, or is not drawn. */
function pfFootHTML(p){
  const slug = p.slug || slugOf(p.n), me = myTeamLoad(), lg = me && tbLeagueOf(me);
  const owner = lg && ownerOf(lg.key, slug), side = tpAction(p.pos, owner && owner.key, me);
  const go = side ? `<button type="button" class="pf-foot-go" data-pftrade="${side}" data-slug="${esc(slug)}" data-testid="profile-trade">${
    side === "get" ? t("profile.foot.get") : t("profile.foot.send")}</button>` : "";
  return `<nav class="pf-foot${go ? "" : " solo"}" aria-label="${t("profile.foot.label")}" data-testid="profile-foot">
    <button type="button" class="pf-foot-close" data-pfclose data-testid="profile-foot-close">${t("common.action.close")}</button>${go}</nav>`;
}

/* Bound once: openProfile refills #modal on every open, never replaces it. */
document.getElementById("modal").addEventListener("click", e => {
  if (e.target.closest("[data-pfclose]")) return closeModal(document.getElementById("modal"));
  const go = e.target.closest("[data-pftrade]");
  if (go) tpGo(go.dataset.pftrade, [go.dataset.slug]);
});

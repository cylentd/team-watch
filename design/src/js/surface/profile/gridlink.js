/* The profile's way to his row in the Usage grid, one tap (2026-10-05, plan U3; nav.js navGoRow). Drawn
   under the strip, only for a player the grid has a row for (data/navrow.js navRowPlan says so), so
   the link never opens a grid that does not show him.

   The profile closes first and the grid opens once the profile's history entry is gone, so Back from
   the grid lands where the reader was, the same order owners.js keeps for a team's roster. */
function pfGridLinkHTML(p){
  const slug = p.slug || slugOf(p.n);
  const rows = typeof USAGE !== "undefined" && USAGE ? USAGE.rows : null;
  const week = typeof USAGE_WEEK !== "undefined" ? USAGE_WEEK : null;
  if (!rows || !navRowPlan("usage", slug, rows, {week})) return "";
  return `<div class="pf-gl"><button type="button" class="pf-grid" data-testid="profile-grid-link" data-pfgrid="${esc(slug)}">${t("profile.grid.open")}${OWN_GO}</button></div>`;
}

function pfOpenGridRow(slug){
  layersUnwind(() => { morphLogo(); navGoRow("usage", slug); });   // the profile and any sheet under it close first
}

document.getElementById("modal").addEventListener("click", e => {
  const b = e.target.closest("[data-pfgrid]");
  if (b) pfOpenGridRow(b.dataset.pfgrid);
});

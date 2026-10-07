/* ============================== DIGEST: REST OF THE WEEK ==============================
   2026-10-06, Digest by day: one line of chips under the day's cards, each a view that is not today's
   job (data/digest.js DG_PLAN `strip`). It took the old rows' place: Recap (while its week is fresh,
   dgRecap), News, Top 5's Ranks and Gems' Usage are a chip here, not a row. A chip names its view by the
   nav's own label, so a rename there renames it here. */
function dgStripHTML(plan){
  const leaves = dgStripLeaves(plan, {recap: !!dgRecap()});
  if (!leaves.length) return "";
  return `<nav class="dg-strip" data-testid="digest-strip" aria-labelledby="dg-strip-h">
    <h3 class="dg-strip-h" id="dg-strip-h">${t("digest.strip.title")}</h3>
    ${leaves.map(leaf => `<button type="button" class="dg-chip" data-testid="digest-strip-chip" data-dggo="${esc(leaf)}">${navLabel(leaf)}</button>`).join("")}</nav>`;
}

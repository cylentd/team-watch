/* The chip for a defense missing starters (2026-10-06), drawn by Preview's box score (surface/preview/research.js)
   and the profile's Matchup pane (surface/profile/sections.js). The view is data/dstarters.js's; this only draws it:
   a closed <details> whose summary is the one line ("NO D: 2 front-seven starters out (Elliss, Granderson)"), and
   whose body names each starter with position, status and share of starter snaps, then the why (the file's own
   evidence line, which says it is unproven) and the note that it changes nothing. A fact, so no colour, no verdict. */
function dsChipHTML(v, rules, where){
  const rows = v.players.map(p => `<li><b>${esc(p.name)}</b><span>${esc(p.pos)} · ${esc(dsStatusWord(p.status))}${
    p.snap_share == null ? "" : " · " + t("ds.snaps", {pct: Math.round(p.snap_share * 100)})}</span></li>`).join("");
  return `<details class="ds" data-testid="${where}-ds" data-ds-team="${esc(v.team)}"><summary data-testid="${where}-ds-line">${dsChipText(v)}</summary>
    <ul data-testid="${where}-ds-names">${rows}</ul>
    <p class="ds-why" data-testid="${where}-ds-why">${esc(dsWhyText(rules))}</p><p class="ds-note">${t("ds.why.note")}</p></details>`;
}

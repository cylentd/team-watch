/* ============================== RECAP: THE BANNER ==============================
   The week's top scorer (LIVE_RECAP.top), called like an announcer on his real box line: "Gibbs rumbles
   for 164 yards and 3 TDs". It is the Digest's banner, so it is the Digest's own words and parts
   (digest/lead.js: dgCall, dgBoxPills, dgPhotoHTML, dgGhostChars) on the same `.dg-lead` panel
   (component/lead.css), washed in his club's colour with its code behind him on a wide screen.
   Yards and TDs, never fantasy points, in the headline (David, 2026-10-05: every league scores
   differently); the box line under it keeps its points pill, as the Digest's does.
   Without a box line (an old recap file) it says he led the week, with no number. */

/* Sleeper's code (LAR, WSH) is not always the colour table's (LA, WAS): take whichever spelling it has. */
const wrClubColour = club => (club && gdCodes(club).find(c => TEAM_COLOURS[c])) || "";

function wrBannerHTML(d){
  const r = d.top;
  if (!r) return "";
  const team = wrClubColour(r.team), photo = dgPhotoHTML(r.slug);
  const head = r.line ? dgCall(r, d.week) : t("weekrecap.banner.bare", {name: esc(dgSurname(r.n))});
  const fact = r.line ? `<span class="dg-lead-pills">${dgBoxPills(r)}</span>` : "";
  const kicker = d.complete ? t("weekrecap.banner.k", {week: d.week}) : t("weekrecap.banner.kSoFar", {week: d.week});
  const go = r.slug ? `<button type="button" class="wr-go" data-wrslug="${esc(r.slug)}"
    aria-label="${esc(t("weekrecap.banner.open", {n: r.n}))}"></button>` : "";
  return `<article class="dg-lead wr-lead go${team ? " team" : ""}${photo ? " has-photo" : ""}"${team ? " " + teamColourStyle(team) : ""}>
    ${go}${team ? `<span class="wr-ghost" aria-hidden="true">${dgGhostChars(esc(team))}</span>` : ""}
    <div class="dg-lead-txt"><p class="wr-when">${kicker}</p><h2 class="dg-lead-h">${head}</h2>
      <div class="dg-lead-fact">${fact}</div></div>
    ${photo}
  </article>`;
}

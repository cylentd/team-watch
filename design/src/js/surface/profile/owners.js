/* Who rosters him, one pill per league (2026-09-28, the profile's fourth question). Read from TEAMS
   by slug: David's own teams (three since 2026-09-29) plus every leaguemate's (data/mates.js), so a league whose twelve
   rosters are all here can also say "free agent". A league with only David's own team loaded (no
   LIVE_MATES) cannot, and draws no pill rather than a wrong one.

   "Yours" is the reader's: the team this browser picked (myTeamLoad), or David's own two in the
   browser that holds his link (isOwner). Everyone else reads the team's name, which is what the
   page already shows anyone (mates.js: only team names, on a public URL). A connected league is
   not counted: its rosters are the visitor's, fetched at runtime, and not here at build time. */
const OWN_LEAGUES = [
  {key: "yahoo", tag: () => t("profile.own.yahoo")},
  {key: "espn", tag: () => t("profile.own.espn")},
  {key: "ayo", tag: () => t("profile.own.ayo")},      // the third league, 2026-09-29
];

function ownerOf(league, slug){
  const teams = [TEAMS[league], ...mateKeys(league).map(k => TEAMS[k])].filter(Boolean);
  return teams.find(tm => tm.roster && tm.roster.some(r => (r.slug || slugOf(r.n)) === slug)) || null;
}

function ownIsMine(tm){
  const pick = myTeamLoad();
  return tm.key === pick || (isOwner() && !tm.mate && !tm.connected);
}

function ownersHTML(p){
  const slug = p.slug || slugOf(p.n);
  const pills = OWN_LEAGUES.filter(l => TEAMS[l.key]).map(l => {
    const tm = ownerOf(l.key, slug);
    if (!tm && !mateKeys(l.key).length) return "";
    const tag = `<i class="pf-own-l ${l.key}">${l.tag()}</i>`;
    if (!tm) return `<span class="pf-own free">${tag}${t("profile.own.free")}</span>`;
    const mine = ownIsMine(tm);
    return `<button type="button" class="pf-own${mine ? " mine" : ""}" data-ownteam="${esc(tm.key)}"
      aria-label="${esc(t("profile.own.open", {team: tm.name}))}">${tag}${mine ? t("profile.own.yours") : esc(tm.name)}${OWN_GO}</button>`;
  }).join("");
  return pills ? `<div class="pf-owners" role="group" aria-label="${t("profile.own.label")}">${pills}</div>` : "";
}

/* A team's pill opens that team's roster (2026-09-28, David: "good if people want to look up
   trades"). A look, not a pick: VIEW changes and myTeamSave does not, so "Yours", the team switch's
   own team and the next visit all stay the reader's. The profile closes first, and the roster opens
   once the profile's history entry is gone, so Back from the roster lands where the reader was
   rather than on a dead entry. */
const OWN_GO = '<svg class="pf-own-go" viewBox="0 0 6 10" aria-hidden="true"><path d="M1 1l4 4-4 4"/></svg>';

function ownOpenRoster(key){
  if (!TEAMS[key]) return;
  const go = () => { VIEW = key; SEARCH_INDEX = null; navGo("roster"); };
  const d = document.getElementById("modal");
  if (history.state && history.state.layer === d.id){
    window.addEventListener("popstate", () => setTimeout(go), {once: true});
    closeModal(d);
  } else { closeModal(d); go(); }
}

document.getElementById("modal").addEventListener("click", e => {
  const b = e.target.closest("[data-ownteam]");
  if (b) ownOpenRoster(b.dataset.ownteam);
});

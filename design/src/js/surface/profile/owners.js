/* Who rosters him, one pill per league (2026-09-28, the profile's fourth question). Read from TEAMS
   by slug: David's two teams plus every leaguemate's (data/mates.js), so a league whose twelve
   rosters are all here can also say "free agent". A league with only David's own team loaded (no
   LIVE_MATES) cannot, and draws no pill rather than a wrong one.

   "Yours" is the reader's: the team this browser picked (myTeamLoad), or David's own two in the
   browser that holds his link (isOwner). Everyone else reads the team's name, which is what the
   page already shows anyone (mates.js: only team names, on a public URL). A connected league is
   not counted: its rosters are the visitor's, fetched at runtime, and not here at build time. */
const OWN_LEAGUES = [
  {key: "yahoo", tag: () => t("profile.own.yahoo")},
  {key: "espn", tag: () => t("profile.own.espn")},
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
    const cls = !tm ? " free" : ownIsMine(tm) ? " mine" : "";
    const who = !tm ? t("profile.own.free") : ownIsMine(tm) ? t("profile.own.yours") : esc(tm.name);
    return `<span class="pf-own${cls}"><i class="pf-own-l ${l.key}">${l.tag()}</i>${who}</span>`;
  }).join("");
  return pills ? `<div class="pf-owners" role="group" aria-label="${t("profile.own.label")}">${pills}</div>` : "";
}

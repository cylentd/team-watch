/* ============================== LIVE: WHOSE TEAM IS "MINE" ==============================
   The reader's team in a league, as its team id there, or null (2026-10-04, David: "Make sure that
   the site registers the roster(s) that the user picks as the 'yours' or 'mine'. I don't want it to
   default to my personal rosters."). The page is public and David's three teams are three of ~36.

   The team the reader picked (tw-team, data/mates.js myTeamLoad) if it plays in this league, else a
   team they follow (tw-follow) that does; null when neither does, and every view that says "mine"
   then draws its neutral form. Never the league's `me` field: that is David's team, kept in the data
   for the build and its tests, and no view reads it as the reader's.

   A team is found by its `key`, the page's own TEAMS key, which design/gameday.py bakes in beside
   its name (David's own: the league's key; a leaguemate's: "espn-run-it-back"). */

/* The keys that say whose team, in order: the picked one, then the followed ones. The first that plays
   in a league here also decides Live's league (live.js gdLeague, data/gameday/strip.js, 2026-10-05). */
function gdKeys(){ return [myTeamLoad(), ...followLoad()]; }
function gdMine(lg){ return gdTeamId(lg, gdKeys()); }

/* The reader's lineup in this league: its rows, or none without a team there. */
const gdMineLineup = lg => { const id = gdMine(lg); return id ? lg.teams[id].lineup : []; };

/* ---------------------------------------------------------------- whose game are you watching?
   With no team of theirs in any league here, My league is this one card (2026-10-05, option 2A): every
   league by name and team count; a league lists its teams in the same spot, a back link returns. A
   pick is the team switch's own (teamswitch.js pickTeam): it saves tw-team and redraws, and the reader
   stays on Live, now on their matchup. It replaced a line that sent the reader to My teams to pick. */
let GD_WHO = null;   /* the league whose teams the card lists; null = the list of leagues */

/* A league's teams that the page knows by key, by name. */
const gdWhoTeams = lg => Object.values(lg.teams).map(tm => tm.key).filter(k => TEAMS[k]).sort(tsByName);

function gdWhoHTML(){
  const lg = GD_WHO && GD.leagues.find(l => l.key === GD_WHO);
  const body = lg
    ? `<button type="button" class="ts-back" data-gdwhoback>${TS_BACK}${t("live.who.back")}</button>
      <h4>${esc(lg.name)}</h4><ul class="gd-who-teams">${gdWhoTeams(lg).map(tpTeamHTML).join("")}</ul>`
    : GD.leagues.map(l => `<button type="button" class="ts-league" data-gdwho="${esc(l.key)}">
      <span class="ts-lg-name">${esc(l.name)}</span><span class="ts-lg-n">${t("live.who.teams", {n: gdWhoTeams(l).length})}</span>${TS_NEXT}</button>`).join("");
  return `<section class="gd-who gd-card"><h3>${t("live.who.title")}</h3>${body}</section>`;
}

function wireGdWho(host){
  host.querySelectorAll("[data-gdwho]").forEach(b => b.addEventListener("click", () => {
    GD_WHO = b.dataset.gdwho; paintLive();
    document.querySelector("[data-gdwhoback]")?.focus();
  }));
  host.querySelector("[data-gdwhoback]")?.addEventListener("click", () => {
    const from = GD_WHO;
    GD_WHO = null; paintLive();
    document.querySelector(`[data-gdwho="${CSS.escape(from)}"]`)?.focus();
  });
  host.querySelectorAll(".gd-who [data-pick]").forEach(b => b.addEventListener("click", () => {
    GD_WHO = null; GD_PICK = null;
    pickTeam(b.dataset.pick);
  }));
}

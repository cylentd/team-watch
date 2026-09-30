/* Every other team in David's two leagues (design/mates.py; leaguemates phase 1, 2026-09-25), so a
   leaguemate can open the page and follow their own team. Each joins TEAMS under its own key
   ("espn-run-it-back") with `mate: true` and draws through the same rows as David's. Anyone may
   pick any team (David, 2026-09-25: rosters are public inside the league, and a pick only changes
   the reader's own screen), and only team names are shown: the page is on a public URL.
   Waivers stay David's until ff-jarvis builds a packet per team (phase 3). */
const MATES = (typeof LIVE_MATES !== "undefined" && LIVE_MATES) ? LIVE_MATES.teams : [];

MATES.forEach(m => {
  const home = TEAMS[m.league];
  if (!home) return;   // a league whose own roster the build lacked (hydrate.js dropped it)
  TEAMS[m.key] = {
    key: m.key, plat: home.plat, tint: home.tint, slot: "", name: m.name, record: "",
    meta: home.meta.slice(), league: m.league, mate: true,
    roster: home.site === "yahoo" && !m.roster.every(p => p.slot) ? inferYahoo(m.roster) : espnRows(m.roster),
  };
});
const mateKeys = league => MATES.filter(m => m.league === league).map(m => m.key);
/* A team that is not one of David's two: a leaguemate's or a connected league's. Its claim advice
   (tiers, swaps, drops, needs) would be David's, so it never shows. */
const notMine = team => !!(team && (team.connected || team.mate));
/* Waivers per league, not per team (phase 2, 2026-09-26): a leaguemate reads their league's
   Breaking rail (who opened up, who was dropped, who is being added), which is the same for all
   twelve teams, with every line about David's roster taken out. A connected league has no packet
   at all. The packet and the rail are keyed by league ("espn"), so a leaguemate reads its own. */
const hasWaivers = team => !!team && !team.connected;
const waiverKey = team => team && team.mate ? team.league : team && team.key;

/* The reader's own team, remembered in this browser only; a key that no longer exists (a renamed
   team, a league gone) falls back to David's Yahoo team. Unset means the reader has not picked
   yet, and My teams asks first (teamswitch.js pickHTML). */
const MY_TEAM = "tw-team";
function myTeamLoad(){
  try { const k = localStorage.getItem(MY_TEAM); return k && TEAMS[k] ? k : null; }
  catch (e) { return null; }
}
function myTeamSave(k){
  try { localStorage.setItem(MY_TEAM, k); } catch (e) {}
}

/* The teams a reader follows (2026-09-26): the team switch lists only these, and every other team
   in David's leagues sits behind its league's row, one tap further. Kept in this browser. Unset, it
   is David's own teams (three since 2026-09-29), or the leaguemate's own team if they had already
   picked it. A connected league is always followed: adding it was the follow. */
const FOLLOW = "tw-follow";
let FOLLOW_MEM = null;        // this load's list, for a browser that refuses storage
function followLoad(){
  if (FOLLOW_MEM) return FOLLOW_MEM.filter(k => TEAMS[k]);
  try {
    const got = JSON.parse(localStorage.getItem(FOLLOW));
    if (Array.isArray(got)) return got.filter(k => TEAMS[k] && !TEAMS[k].connected);
  } catch (e) { /* unreadable: the default below */ }
  const mine = myTeamLoad();
  return mine && TEAMS[mine].mate ? [mine] : myLeagueKeys();
}
function followToggle(k){
  const now = followLoad(), next = now.includes(k) ? now.filter(x => x !== k) : [...now, k];
  FOLLOW_MEM = next;
  try { localStorage.setItem(FOLLOW, JSON.stringify(next)); } catch (e) { /* this load only */ }
}

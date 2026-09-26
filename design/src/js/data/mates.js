/* Every other team in David's two leagues (design/mates.py; leaguemates phase 1, 2026-09-25), so a
   leaguemate can open the page and follow their own team. Each joins TEAMS under its own key
   ("espn-run-it-back") with `mate: true` and draws through the same rows as David's. Anyone may
   pick any team (David, 2026-09-25: rosters are public inside the league, and a pick only changes
   the reader's own screen), and only team names are shown: the page is on a public URL.
   Waivers stay David's until ff-jarvis builds a packet per team (phase 3). */
const MATES = (typeof LIVE_MATES !== "undefined" && LIVE_MATES) ? LIVE_MATES.teams : [];

MATES.forEach(m => {
  const home = TEAMS[m.league];
  TEAMS[m.key] = {
    key: m.key, plat: home.plat, tint: home.tint, slot: "", name: m.name, record: "",
    meta: home.meta.slice(), league: m.league, mate: true,
    roster: m.league === "yahoo" && !m.roster.every(p => p.slot) ? inferYahoo(m.roster) : espnRows(m.roster),
  };
});
const mateKeys = league => MATES.filter(m => m.league === league).map(m => m.key);
/* A team this page has no waiver packet or Breaking rail for: a leaguemate's or a connected one. */
const notMine = team => !!(team && (team.connected || team.mate));

/* The reader's own team, remembered in this browser only; a key that no longer exists (a renamed
   team, a league gone) falls back to David's Yahoo team. Unset means the reader has not picked
   yet, and the roster's hero asks them to (heroPickHTML). */
const MY_TEAM = "tw-team";
function myTeamLoad(){
  try { const k = localStorage.getItem(MY_TEAM); return k && TEAMS[k] ? k : null; }
  catch (e) { return null; }
}
function myTeamSave(k){
  try { localStorage.setItem(MY_TEAM, k); } catch (e) {}
}

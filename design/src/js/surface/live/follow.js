/* Whose board Live draws (leaguemates phase 2, 2026-09-26; split from live.js for its budget).

   Live follows David's ESPN matchup, or a leaguemate's when their ESPN team is on screen
   (api/live.py ?team=). A Yahoo leaguemate gets no board: Live reads the ESPN league only. The
   key names the followed team in the memory keys (memory.js); David's is empty, so his memory is
   where it always was. */
const gdMate = () => { const tm = TEAMS[VIEW]; return tm && tm.mate ? tm : null; };
const gdTeamName = () => { const m = gdMate(); return m && m.league === "espn" ? m.name : null; };
const gdTeamKey = () => { const n = gdTeamName(); return n ? slugOf(n) : ""; };
const gdYahooMate = () => { const m = gdMate(); return !!m && m.league === "yahoo"; };

/* On every Live render: a team switch since the last one swaps in that team's remembered board
   and asks for a fresh one, so one team's numbers never sit under another's name. */
let GD_FOR = null;
function gdFollow(){
  const k = gdTeamKey();
  if (GD_FOR === null){ GD_FOR = k; return; }      // the first render: buildLive already loaded it
  if (k === GD_FOR) return;
  GD_FOR = k;
  GD_DATA = gdBoardLoad();
  GD_WP = GD_DATA ? ((gdMemLoad(GD_DATA.week) || {}).wp || []) : [];
  GD_ERR = ""; GD_CATCHUP = null; GD_PULSE = {}; GD_AT = 0;
}

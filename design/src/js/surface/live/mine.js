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

function gdMine(lg){
  if (!lg) return null;
  for (const k of [myTeamLoad(), ...followLoad()]){
    const id = k && Object.keys(lg.teams).find(i => lg.teams[i].key === k);
    if (id) return id;
  }
  return null;
}

/* The reader's lineup in this league: its rows, or none without a team there. */
const gdMineLineup = lg => { const id = gdMine(lg); return id ? lg.teams[id].lineup : []; };

/* One line over the score while the reader has no team in this league (board.js gdPickHTML): it opens
   My teams, whose picker or team switch (teamswitch.js tsPickFor) takes the pick. The switch it opens
   would be closed by nav.js's outside-click listener if the click carried on. */
function wireGdPick(host){
  host.querySelectorAll("[data-gdpick]").forEach(b => b.addEventListener("click", e => {
    e.stopPropagation();
    tsPickFor(b.dataset.gdpick);
  }));
}

/* LIVE_ESPN-shaped rows -> roster rows. ESPN starts two RB and two WR, so those slots are
   numbered; the singles are not. A connected league (data/connect.js) arrives in the same shape
   from api/league.py and goes through here too. */
function espnRows(rows){
  const seen = {};
  return rows.map(p => {
    let slot = p.slot;
    if (slot === "RB" || slot === "WR"){ seen[slot] = (seen[slot]||0)+1; slot += seen[slot]; }
    const row = {n:p.n, pos:p.pos, team:p.team, slug:p.slug, slot,
      start: !["BN", "OUT", "IR"].includes(slot), status: p.status || null};   // IR is a bench spot
    return Object.assign(row, signalsFor(row));
  });
}

function hydrateEspn(){
  if (typeof LIVE_ESPN === "undefined" || !LIVE_ESPN) return;
  TEAMS.espn.name = LIVE_ESPN.name;
  TEAMS.espn.meta = ["12-team","half PPR","no kicker · 2 FLEX", LIVE_ESPN.league];
  TEAMS.espn.roster = espnRows(LIVE_ESPN.roster);
}
hydrateEspn();

/* Yahoo's scrape carries each player's real lineup slot (build.py maps W/R/T to FLEX, DEF to
   DST), and then the rows go through the same path as ESPN's. Only a scrape without slots falls
   back to inferring them, by filling the league's 9-man lineup in roster order: QB, 2 RB, 2 WR,
   TE, one W/R/T flex, K, DST. */
const YAHOO_LINEUP = [["QB",1],["RB",2],["WR",2],["TE",1],["K",1],["DST",1]];
/* Each Yahoo league's roster block by league key (AYO's LIVE_AYO since 2026-09-29), named literally:
   a top-level const cannot be looked up by a string. A league's block is null when the build had none. */
const YAHOO_ROSTER_BLOCKS = {
  yahoo: (typeof LIVE_YAHOO !== "undefined" && LIVE_YAHOO) || null,
  ayo: (typeof LIVE_AYO !== "undefined" && LIVE_AYO) || null,
};
function hydrateYahoo(key){
  const L = YAHOO_ROSTER_BLOCKS[key], tm = TEAMS[key];
  if (!L || !tm) return;
  tm.name = L.name;
  tm.meta = ["12-team", "half PPR", ...(tm.slot ? [`slot ${tm.slot}`] : []), L.league];
  tm.roster = L.roster.every(p => p.slot) ? espnRows(L.roster) : inferYahoo(L.roster);
}
function inferYahoo(rows){
  const need = {}; YAHOO_LINEUP.forEach(([p,n]) => need[p] = n);
  const seen = {};
  let flexTaken = false;
  return rows.map(p => {
    let slot = "BN";
    if (need[p.pos] > 0){
      need[p.pos]--;
      seen[p.pos] = (seen[p.pos]||0) + 1;
      slot = (YAHOO_LINEUP.find(l=>l[0]===p.pos)[1] > 1) ? p.pos + seen[p.pos] : p.pos;
    } else if (!flexTaken && ["RB","WR","TE"].includes(p.pos)){
      flexTaken = true; slot = "FLEX";
    }
    const row = {n:p.n, pos:p.pos, team:p.team, slug:p.slug, slot, start: slot !== "BN", status:null};
    return Object.assign(row, signalsFor(row));
  });
}
if (!YAHOO_ROSTER_BLOCKS.yahoo)
  TEAMS.yahoo.roster.forEach(p => Object.assign(p, signalsFor(p)));   // the sample roster, same cells
Object.keys(YAHOO_ROSTER_BLOCKS).forEach(hydrateYahoo);
// A league the build had no roster for leaves TEAMS: no sample, so no team switch row, no owner pill.
Object.keys(YAHOO_ROSTER_BLOCKS).forEach(k => { if (k !== "yahoo" && !YAHOO_ROSTER_BLOCKS[k]) delete TEAMS[k]; });

/* A player on more than one of David's rosters gets `dual`, the count of his teams (2 or 3 since the
   third league, 2026-09-29) — computed, never hand-listed. */
(function markDual(){
  const mine = myLeagueKeys().map(k => TEAMS[k]), n = {};
  mine.forEach(tm => new Set(tm.roster.map(p => p.n)).forEach(name => { n[name] = (n[name] || 0) + 1; }));
  mine.forEach(tm => tm.roster.forEach(p => { if (n[p.n] > 1) p.dual = n[p.n]; }));
})();


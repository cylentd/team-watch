/* ESPN starts two RB and two WR, so those slots are numbered; the singles are not. */
function hydrateEspn(){
  if (typeof LIVE_ESPN === "undefined" || !LIVE_ESPN) return;
  const seen = {};
  TEAMS.espn.name = LIVE_ESPN.name;
  TEAMS.espn.meta = ["12-team","half PPR","no kicker · 2 FLEX", LIVE_ESPN.league];
  TEAMS.espn.roster = LIVE_ESPN.roster.map(p => {
    let slot = p.slot;
    if (slot === "RB" || slot === "WR"){ seen[slot] = (seen[slot]||0)+1; slot += seen[slot]; }
    return Object.assign({
      n:p.n, pos:p.pos, team:p.team, slug:p.slug, slot,
      start: slot !== "BN", status: p.status || null,
      trend:null, d:null, rank:[null,0,null,null], news:0,
    }, SIGNALS[p.n] || {});
  });
}
hydrateEspn();

/* Yahoo comes from a website scrape with no lineup slot, so the slots below are inferred by
   filling the league's lineup in roster order. The board labels them as inferred. */
const YAHOO_LINEUP = [["QB",1],["RB",2],["WR",3],["TE",1]];
function hydrateYahoo(){
  if (typeof LIVE_YAHOO === "undefined" || !LIVE_YAHOO) return;
  const need = {}; YAHOO_LINEUP.forEach(([p,n]) => need[p] = n);
  const seen = {};
  let flexTaken = false;
  const roster = LIVE_YAHOO.roster.map(p => {
    const sig = SIGNALS[p.n] || {};
    let slot = "BN";
    if (sig.status === "OUT"){
      slot = "OUT";                       // an unavailable player never fills a lineup slot
    } else if (need[p.pos] > 0){
      need[p.pos]--;
      seen[p.pos] = (seen[p.pos]||0) + 1;
      slot = (YAHOO_LINEUP.find(l=>l[0]===p.pos)[1] > 1) ? p.pos + seen[p.pos] : p.pos;
    } else if (!flexTaken && ["RB","WR","TE"].includes(p.pos)){
      flexTaken = true; slot = "FLEX";
    }
    return Object.assign({
      n:p.n, pos:p.pos, team:p.team, slug:p.slug, slot,
      start: slot !== "BN" && slot !== "OUT", status:null,
      trend:null, d:null, rank:[null,0,null,null], news:0,
    }, sig);
  });
  TEAMS.yahoo.name = LIVE_YAHOO.name;
  TEAMS.yahoo.meta = ["12-team","half PPR","slot 12", LIVE_YAHOO.league];
  TEAMS.yahoo.roster = roster;
}
hydrateYahoo();

/* A player on both rosters gets the "2 leagues" tag — computed, never hand-listed. */
(function markDual(){
  const y = new Set(TEAMS.yahoo.roster.map(p=>p.n));
  const e = new Set(TEAMS.espn.roster.map(p=>p.n));
  TEAMS.yahoo.roster.forEach(p=>{ if (e.has(p.n)) p.dual = 1; });
  TEAMS.espn.roster.forEach(p=>{ if (y.has(p.n)) p.dual = 1; });
})();


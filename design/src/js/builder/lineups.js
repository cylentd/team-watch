const DFS_DK = [
  {slot:"QB",   n:"Jared Goff",        slug:"jared-goff",       sal:6200, proj:18.4, own:14},
  {slot:"RB",   n:"De'Von Achane",     slug:"devon-achane",     sal:8400, proj:21.1, own:32},
  {slot:"RB",   n:"Chase Brown",       slug:"chase-brown",      sal:5900, proj:14.2, own:19},
  {slot:"WR",   n:"Amon-Ra St. Brown", slug:"amonra-st-brown",  sal:8100, proj:19.8, own:27},
  {slot:"WR",   n:"Tee Higgins",       slug:"tee-higgins",      sal:6800, proj:15.4, own:16},
  {slot:"WR",   n:"Jalen Coker",       slug:"jalen-coker",      sal:3600, proj:9.8,  own:6},
  {slot:"TE",   n:"Isaiah Likely",     slug:"isaiah-likely",    sal:4200, proj:11.2, own:11},
  {slot:"FLEX", n:null},
  {slot:"DST",  n:"Seahawks",          slug:null, abbr:"SEA",   sal:2700, proj:7.4,  own:9},
];
const CAP_DK = 50000;
/* Yahoo's own slate: no curated sample lineup to seed it with, so every slot starts vacant
   whichever way DFS_SITE points. */
const DFS_YAHOO = ["QB","RB","RB","WR","WR","WR","TE","FLEX","DST"].map(slot => ({slot, n:null}));
const CAP_YAHOO = 200;
/* Slot order the optimizer fills and the "My lineup" card renders, one classic DK/Yahoo
   NFL roster: 1 QB, 2 RB, 3 WR, 1 TE, 1 FLEX (RB/WR/TE), 1 DST. */
const LINEUP_SLOTS = ["QB","RB","RB","WR","WR","WR","TE","FLEX","DST"];
const slotEligible = (slot, pos) => slot === "FLEX" ? ["RB","WR","TE"].includes(pos) : slot === pos;

/* The custom lineup cart: which slot (index into site.lineup) is currently being filled, or
   null when no slot is selected -- a tap on the pool then auto-picks the first open slot the
   player fits. Set by tapping a slot (vacant, to fill it; filled, to swap it); cleared on a
   successful pick, Cancel, or a DFS_SITE/pool-position change (a stale index into a different
   site's lineup array is worse than just dropping the selection). */
let ACTIVE_SLOT = null;
let PICK_ERR = null;

/* Which book the DFS tab shows -- Yahoo or DraftKings. */
let DFS_SITE = "yahoo";
function dfsSite(){
  return DFS_SITE === "dk"
    ? {key:"dk", label:"DraftKings", cap:CAP_DK, pool:DFSPOOL_DK, lineup:DFS_DK, when:null}
    : {key:"yahoo", label:"Yahoo", cap:CAP_YAHOO, pool:DFSPOOL_YAHOO, lineup:DFS_YAHOO,
       when: LIVE_YAHOO_DFS ? LIVE_YAHOO_DFS.fetched : null};
}

const TOP_COUNT = 3;
/* How chalky a player is, 0 (contrarian) to 1 (chalk), keyed by player object. Real ownership
   when the site has it (DraftKings sample); otherwise a proxy — rank by projection within
   position, since Yahoo's export carries no ownership column and the highest-projected player at
   a position is exactly who a max-points build (and most of the field) rosters anyway. */
function chalkMap(pool){
  const m = new Map();
  if (pool.some(p=>typeof p.own==="number")){
    const max = Math.max(1, ...pool.map(p=>p.own||0));
    pool.forEach(p=>m.set(p, (p.own||0)/max));
    return m;
  }
  const byPos = {};
  pool.forEach(p=>(byPos[p.pos] ||= []).push(p));
  Object.values(byPos).forEach(list=>{
    const sorted = [...list].sort((a,b)=>b.proj-a.proj);
    const n = sorted.length;
    sorted.forEach((p,i)=>m.set(p, n>1 ? 1-i/(n-1) : 1));
  });
  return m;
}
/* Top-lineups optimizer. No solver library (the page has to work offline as a data URI), so it's
   randomized-greedy: fill each slot from its eligible pool, biased toward the mode's score but with
   enough noise that repeated fills land on different rosters, keep every valid one under cap, then
   greedily keep the best-scoring lineups that each swap out 3+ players from every one kept already
   (two 8-of-9-shared lineups tell you nothing a single one doesn't).
   mode "greedy": pure projection — the highest-projected player at a position wins that slot in
   every lineup, same as any optimizer would build it. mode "contrarian": the single most-chalky
   player at each position (QB, RB, WR, TE, DST — not per slot, so FLEX can't re-admit a benched RB/WR/TE
   through the back door) is sat outright (that IS what non-chalk means — it can't just softly
   discourage him and then pick him anyway), and what's left is scored on projection minus a chalk
   penalty, so the build actively trades some projection for one the field isn't all rostering —
   the point of a small-field or single-entry GPP, where "greedy" x N all cashing or all missing
   together is the actual risk. */
function chalkiestPerPosition(pool, chalk){
  const byPos = {};
  pool.forEach(p=>(byPos[p.pos] ||= []).push(p));
  const banned = new Set();
  Object.values(byPos).forEach(list=>{
    if (list.length < 2) return;
    const top = list.reduce((a,b)=> chalk.get(b) > chalk.get(a) ? b : a);
    banned.add(top.n);
  });
  return banned;
}
function fillOneLineup(pool, cap, mode, chalk, banned){
  const minSal = Math.min(...pool.map(p=>p.sal));
  const order = [...LINEUP_SLOTS.keys()].sort(()=>Math.random()-0.5);
  const chosen = new Array(LINEUP_SLOTS.length);
  const used = new Set();
  let spent = 0;
  for (const i of order){
    const slot = LINEUP_SLOTS[i];
    const eligible = slot === "FLEX" ? p => ["RB","WR","TE"].includes(p.pos) : p => p.pos === slot;
    const remaining = LINEUP_SLOTS.length - chosen.filter(Boolean).length - 1;
    const budget = cap - spent - remaining * minSal;
    let candidates = pool.filter(p => eligible(p) && !used.has(p.n) && p.sal <= budget);
    if (!candidates.length) candidates = pool.filter(p => eligible(p) && !used.has(p.n) && p.sal <= cap - spent);
    if (!candidates.length) return null;
    if (mode === "contrarian"){
      const sat = candidates.filter(p => !banned.has(p.n));
      if (sat.length) candidates = sat;
    }
    const score = p => mode === "contrarian" ? p.proj - chalk.get(p)*10 : p.proj;
    const ranked = candidates.map(p => ({p, s: Math.max(0.05, score(p)) * (0.55 + Math.random())}))
      .sort((a,b) => b.s - a.s);
    const pick = ranked[0].p;
    chosen[i] = {slot, ...pick, _chalk: chalk.get(pick)};
    used.add(pick.n);
    spent += pick.sal;
  }
  if (spent > cap) return null;
  const own = chosen.some(d=>typeof d.own === "number") ? chosen.reduce((a,d)=>a+(d.own||0),0) : null;
  const avgChalk = chosen.reduce((a,d)=>a+d._chalk,0) / chosen.length;
  return {players: chosen, spent, proj: chosen.reduce((a,d)=>a+d.proj,0), own, chalk: avgChalk};
}
function bestLineups(pool, cap, mode, count){
  // OUT/IR players stay in the pool table (so their tag is visible) but can't score points, so
  // the optimizer never gets to roster them -- a stale-but-real-looking proj (like a $10 Yahoo
  // row for a guy who's since changed teams) would otherwise win a slot on "value" alone.
  pool = pool.filter(p => p.status !== "OUT" && p.status !== "IR");
  const chalk = chalkMap(pool);
  const banned = mode === "contrarian" ? chalkiestPerPosition(pool, chalk) : null;
  const seen = new Set(), found = [];
  for (let i = 0; i < 400 && found.length < 40; i++){
    const l = fillOneLineup(pool, cap, mode, chalk, banned);
    if (!l) continue;
    const key = l.players.map(p=>p.n).sort().join("|");
    if (seen.has(key)) continue;
    seen.add(key);
    found.push(l);
  }
  found.sort((a,b) => mode === "contrarian"
    ? (b.proj - b.chalk*10) - (a.proj - a.chalk*10)
    : b.proj - a.proj);
  const picked = [];
  for (const l of found){
    if (picked.length >= count) break;
    const tooClose = picked.some(k => k.players.filter(x => l.players.some(y=>y.n===x.n)).length > 6);
    if (!tooClose) picked.push(l);
  }
  return picked;
}
let TOP_MODE = "greedy";
const TOP_CACHE = new Map(); // key (site|mode|poolSize) -> lineups, so toggling modes doesn't re-roll a mode already built
function topLineups(){
  const site = dfsSite();
  const key = `${site.key}|${TOP_MODE}|${site.pool.length}`;
  if (!TOP_CACHE.has(key)) TOP_CACHE.set(key, bestLineups(site.pool, site.cap, TOP_MODE, TOP_COUNT));
  return TOP_CACHE.get(key);
}


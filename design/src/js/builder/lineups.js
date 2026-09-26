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
/* Same-team skill players (RB/WR/TE) chase the same finite carries and targets, so two of them
   together usually cost each other points -- except the well-known positive-correlation pairs:
   a QB stacked with his own pass-catcher (he feeds them, doesn't compete with them) and RB+DST
   (a team that's winning big feeds both). Reward a stack, penalize everything else that shares a
   team; two players on different teams are just two different Sundays, no adjustment either way. */
const SKILL_POS = new Set(["RB", "WR", "TE"]);
const STACK_BONUS = 2, CANNIBAL_PENALTY = 4;
function isStack(a, b){
  const pair = [a.pos, b.pos].sort().join("+");
  return pair === "QB+RB" || pair === "QB+TE" || pair === "QB+WR" || pair === "DST+RB";
}
function correlationAdj(players){
  let adj = 0;
  for (let i = 0; i < players.length; i++){
    for (let j = i + 1; j < players.length; j++){
      const a = players[i], b = players[j];
      if (!a.team || a.team !== b.team) continue;
      if (isStack(a, b)) adj += STACK_BONUS;
      else if (SKILL_POS.has(a.pos) && SKILL_POS.has(b.pos)) adj -= CANNIBAL_PENALTY;
    }
  }
  return adj;
}

/* A seeded PRNG, not Math.random(): the search below still needs randomness to land on different
   candidate rosters, but plain Math.random() made the "top 3" reroll on every page load with no
   data actually changing, which reads as broken ("didn't it already find the best 3?"). Seed
   from the pool and mode instead, so the same slate always searches the same way and only a real
   change to the pool (a new week, a scratched player) changes the result. */
function seedFromPool(pool, mode){
  const s = mode + "|" + pool.map(p => `${p.n}:${p.sal}:${p.proj}`).join(",");
  let h = 2166136261;
  for (let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}
function mulberry32(seed){
  let a = seed;
  return function(){
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

/* Top-lineups. The first is exact: solveLineup (solve.js) finds the lineup with the highest total
   score under the cap, which is what weighs points per dollar -- a cheap player wins a slot when
   the money he saves buys more points elsewhere. The rest come from re-solving with every score
   jittered by a seeded ±20%, then keeping the best-scoring lineups that each swap out 3+ players
   from every one kept already (two 8-of-9-shared lineups tell you nothing a single one doesn't).
   mode "greedy": pure projection, the most projected points the cap allows. mode "contrarian": the single most-chalky
   player at each position (QB, RB, WR, TE, DST — not per slot, so FLEX can't re-admit a benched RB/WR/TE
   through the back door) is sat outright (that IS what non-chalk means — it can't just softly
   discourage him and then pick him anyway), and what's left is scored on projection minus a chalk
   penalty, so the build actively trades some projection for one the field isn't all rostering —
   the point of a small-field or single-entry GPP, where "greedy" x N all cashing or all missing
   together is the actual risk. Every candidate's final score also carries correlationAdj, so a
   lineup that stacks or avoids cannibalizing itself outranks an otherwise-identical one that doesn't. */
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
const SOLVES = 30;   // one exact solve plus 29 jittered ones; ~1 ms each on Yahoo's 200-step cap
function lineupOf(chosen, chalkOf){
  const own = chosen.some(d=>typeof d.own === "number") ? chosen.reduce((a,d)=>a+(d.own||0),0) : null;
  const players = chosen.map(d => ({...d, _chalk: chalkOf.get(d.n)}));
  return {players, spent: players.reduce((a,d)=>a+d.sal,0), proj: players.reduce((a,d)=>a+d.proj,0), own,
    chalk: players.reduce((a,d)=>a+d._chalk,0) / players.length, corr: correlationAdj(players)};
}
function bestLineups(pool, cap, mode, count){
  // OUT/IR players stay in the pool table (so their tag is visible) but can't score points, so
  // the optimizer never gets to roster them -- a stale-but-real-looking proj (like a $10 Yahoo
  // row for a guy who's since changed teams) would otherwise win a slot on "value" alone.
  pool = pool.filter(p => p.status !== "OUT" && p.status !== "IR" && p.sal > 0);
  const chalk = chalkMap(pool);
  const chalkOf = new Map(pool.map(p => [p.n, chalk.get(p)]));
  if (mode === "contrarian"){
    const banned = chalkiestPerPosition(pool, chalk), sat = pool.filter(p => !banned.has(p.n));
    if (solveLineup(sat, cap, () => 1)) pool = sat;   // a pool too thin to fill without them keeps them
  }
  const score = p => Math.max(0.05, mode === "contrarian" ? p.proj - chalkOf.get(p.n)*10 : p.proj);
  const rand = mulberry32(seedFromPool(pool, mode));
  const seen = new Set(), found = [];
  for (let i = 0; i < SOLVES; i++){
    const jitter = new Map(pool.map(p => [p.n, i ? 0.8 + 0.4*rand() : 1]));
    const chosen = solveLineup(pool, cap, p => score(p) * jitter.get(p.n));
    if (!chosen) break;
    const key = chosen.map(p=>p.n).sort().join("|");
    if (seen.has(key)) continue;
    seen.add(key);
    found.push(lineupOf(chosen, chalkOf));
  }
  const rank = l => (mode === "contrarian" ? l.proj - l.chalk*10 : l.proj) + l.corr;
  found.sort((a,b) => rank(b) - rank(a));
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


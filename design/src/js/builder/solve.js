/* Exact DFS lineup solver: the nine players with the highest total score that fit under the cap.
   Replaced a slot-by-slot greedy fill on 2026-09-25, which took the top projection in whichever
   slot it filled first and left the rest of the lineup to what was left of the cap -- it never
   asked whether $10 saved on one slot bought more points on another, so it paid $18-20 for a DST.
   No solver library (the page works offline), so it is a knapsack: per position, the best k
   players at every exact cost; then the positions combined over cost for each legal roster
   shape (the FLEX is a 3rd RB, a 4th WR or a 2nd TE). Salaries are divided by their common
   factor first, so DraftKings' $50,000 cap is 500 steps, not 50,000. */
const ROSTER_SHAPES = [
  {QB:1, RB:3, WR:3, TE:1, DST:1},
  {QB:1, RB:2, WR:4, TE:1, DST:1},
  {QB:1, RB:2, WR:3, TE:2, DST:1},
];
const SHAPE_MAX = {QB:1, RB:3, WR:4, TE:2, DST:1};

function salaryUnit(pool){
  const gcd = (a, b) => b ? gcd(b, a % b) : a;
  return pool.reduce((u, p) => gcd(u, p.sal), 0) || 1;
}
/* f[k][c]: best total of exactly k of `players` costing exactly c units. take[i] marks where
   player i improved a cell, which is enough to walk the choice back from any (k, c). */
function positionTable(players, K, C){
  const f = Array.from({length: K + 1}, () => new Float64Array(C + 1).fill(-Infinity));
  f[0][0] = 0;
  const take = players.map(p => {
    const t = new Uint8Array((K + 1) * (C + 1));
    for (let k = K; k >= 1; k--){
      for (let c = C; c >= p.u; c--){
        const v = f[k - 1][c - p.u] + p.v;
        if (v > f[k][c]){ f[k][c] = v; t[k * (C + 1) + c] = 1; }
      }
    }
    return t;
  });
  return {f, take, players, C};
}
function walkBack(tab, k, c){
  const out = [];
  for (let i = tab.players.length - 1; i >= 0 && k > 0; i--){
    if (tab.take[i][k * (tab.C + 1) + c]){ out.push(tab.players[i]); k--; c -= tab.players[i].u; }
  }
  return out;
}
/* pool rows need {pos, sal}; value(p) is what to maximize. Returns the chosen players in
   LINEUP_SLOTS order (the FLEX is the shape's extra player with the lowest value), or null. */
function solveLineup(pool, cap, value){
  const unit = salaryUnit(pool), C = Math.floor(cap / unit);
  const tabs = {};
  for (const pos of Object.keys(SHAPE_MAX)){
    const players = pool.filter(p => p.pos === pos).map(p => ({p, u: p.sal / unit, v: value(p)}));
    tabs[pos] = positionTable(players, SHAPE_MAX[pos], C);
  }
  let best = null;
  for (const shape of ROSTER_SHAPES){
    const order = Object.keys(shape);
    let g = tabs[order[0]].f[shape[order[0]]].slice();
    const splits = [];
    for (const pos of order.slice(1)){
      const h = tabs[pos].f[shape[pos]], next = new Float64Array(C + 1).fill(-Infinity);
      const split = new Int32Array(C + 1);
      for (let a = 0; a <= C; a++){
        if (g[a] === -Infinity) continue;
        for (let b = 0; a + b <= C; b++){
          const v = g[a] + h[b];
          if (v > next[a + b]){ next[a + b] = v; split[a + b] = a; }
        }
      }
      splits.push(split);
      g = next;
    }
    let c = 0;
    for (let x = 1; x <= C; x++) if (g[x] > g[c]) c = x;
    if (g[c] === -Infinity || (best && g[c] <= best.v)) continue;
    const picks = {};
    for (let i = order.length - 1; i >= 1; i--){
      const a = splits[i - 1][c];
      picks[order[i]] = walkBack(tabs[order[i]], shape[order[i]], c - a);
      c = a;
    }
    picks[order[0]] = walkBack(tabs[order[0]], shape[order[0]], c);
    best = {v: g.reduce((m, x) => Math.max(m, x), -Infinity), shape, picks};
  }
  if (!best) return null;
  const byPos = {};
  for (const [pos, list] of Object.entries(best.picks)) byPos[pos] = list.sort((a, b) => b.v - a.v).map(x => x.p);
  const flexPos = ["RB", "WR", "TE"].find(pos => best.shape[pos] > {RB:2, WR:3, TE:1}[pos]);
  const flex = byPos[flexPos].pop();
  return LINEUP_SLOTS.map(slot => ({slot, ...(slot === "FLEX" ? flex : byPos[slot].shift())}));
}

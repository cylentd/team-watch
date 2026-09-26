// Runs the page's own DFS optimizer (src/js/builder/lineups.js) outside the browser, so the
// weekly backtest scores exactly what the page would have shown. Called by dfs_backtest.py:
//   node design/dfs_backtest.js <pool.json>   ->   {"greedy": [...], "contrarian": [...]} on stdout
const fs = require("fs"), path = require("path");
const src = ["solve.js", "lineups.js"]
  .map(f => fs.readFileSync(path.join(__dirname, "src/js/builder", f), "utf8")).join("\n");
const pool = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const run = new Function("pool",
  src + "\nreturn {greedy: bestLineups(pool, CAP_YAHOO, 'greedy', TOP_COUNT)," +
  " contrarian: bestLineups(pool, CAP_YAHOO, 'contrarian', TOP_COUNT)};");
const out = run(pool);
for (const mode of Object.keys(out)) {
  out[mode] = out[mode].map(l => ({spent: l.spent, proj: l.proj, corr: l.corr,
    players: l.players.map(p => ({slot: p.slot, n: p.n, pos: p.pos, team: p.team, sal: p.sal, proj: p.proj}))}));
}
process.stdout.write(JSON.stringify(out));

/* ============================== GAMEDAY: THE SCORER ==============================
   Every league scored the same way (2026-09-28): Sleeper's live stats through the league's own
   rules. The rules come from LIVE_GAMEDAY (design/gameday.py), worded by api/_scoring.py, which is
   the only table that knows ESPN's stat ids and Yahoo's labels. Scoring week 2 this way matched
   both leagues' official numbers to the hundredth; tests/test_gameday.py keeps that true.

   A term reads Sleeper keys summed, then one of: `lo`/`hi` (1 inside the range: a bonus, a
   points-allowed tier), `per` (whole units, truncated toward zero: ESPN's "every 20 yards"), or
   `frac` (the value over n: Yahoo's "25 yards per point"); times `p`. A missing stat is 0. */

function gdTermPts(tm, s){
  let v = 0;
  for (const k of tm.s) v += +(s[k] || 0);
  if (tm.lo !== undefined) v = v >= tm.lo && (tm.hi === null || tm.hi === undefined || v <= tm.hi) ? 1 : 0;
  else if (tm.per) v = Math.trunc(v / tm.per);
  else if (tm.frac) v = v / tm.frac;
  return v * tm.p;
}

/* A player's points under `rules`, or null with no stats (his game has not started). A defense
   scores by the D/ST rules, everyone else, kickers too, by the player rules. */
function gdPts(rules, row, s){
  if (!s) return null;
  let p = 0;
  for (const tm of rules[row.pos === "DEF" ? "dst" : "off"]) p += gdTermPts(tm, s);
  return Math.round(p * 100) / 100;
}

/* How he earned it, in the league's own vocabulary: "6/7 rec · 82 yds · 2 TD". Only what happened. */
function gdLine(row, s){
  if (!s) return "";
  const n = k => +(s[k] || 0), out = [];
  const td = n("rush_td") + n("rec_td");
  if (row.pos === "QB"){
    out.push(t("live.line.cmp", {c: n("pass_cmp"), a: n("pass_att")}), t("live.line.yds", {n: n("pass_yd")}));
    if (n("pass_td")) out.push(t("live.line.td", {n: n("pass_td")}));
    if (n("pass_int")) out.push(t("live.line.int", {n: n("pass_int")}));
    if (n("rush_att")) out.push(t("live.line.car", {n: n("rush_att"), y: n("rush_yd")}));
    if (n("rush_td")) out.push(t("live.line.rushTd", {n: n("rush_td")}));
  } else if (row.pos === "RB"){
    out.push(t("live.line.carries", {n: n("rush_att")}), t("live.line.yds", {n: n("rush_yd")}));
    if (n("rec_tgt")) out.push(t("live.line.recYds", {r: n("rec"), g: n("rec_tgt"), y: n("rec_yd")}));
    if (td) out.push(t("live.line.td", {n: td}));
  } else if (row.pos === "WR" || row.pos === "TE"){
    out.push(t("live.line.rec", {r: n("rec"), g: n("rec_tgt")}), t("live.line.yds", {n: n("rec_yd")}));
    if (td) out.push(t("live.line.td", {n: td}));
    if (n("rush_att")) out.push(t("live.line.car", {n: n("rush_att"), y: n("rush_yd")}));
  } else if (row.pos === "K"){
    out.push(t("live.line.fg", {m: n("fgm"), a: n("fga")}), t("live.line.xp", {m: n("xpm"), a: n("xpa")}));
  } else if (row.pos === "DEF"){
    out.push(t("live.line.allowed", {n: n("pts_allow")}));
    if (n("sack")) out.push(t("live.line.sacks", {n: n("sack")}));
    if (n("int")) out.push(t("live.line.int", {n: n("int")}));
    if (n("fum_rec") + n("def_st_fum_rec")) out.push(t("live.line.fr", {n: n("fum_rec") + n("def_st_fum_rec")}));
    if (n("def_td") + n("def_st_td")) out.push(t("live.line.td", {n: n("def_td") + n("def_st_td")}));
  }
  if (n("fum_lost")) out.push(t("live.line.fl", {n: n("fum_lost")}));
  return out.join(" · ");
}

const GD_BENCH = ["BE", "BN", "IR"];
const gdStarter = r => !GD_BENCH.includes(r.slot);

const gdSum = rows => Math.round(rows.reduce((a, r) => a + (r.pts || 0), 0) * 100) / 100;

/* A team scored: its starters and its bench as [{...row, pts, line, state}], the starters' total
   (the only one that counts) and the bench's. `states` is Sleeper's {team: pre_game|in_game|complete};
   a row whose team has no state yet reads as not started. */
function gdSide(league, id, stats, states){
  const all = league.teams[id].lineup.map(r => {
    const s = r.sid && stats ? stats[r.sid] : null, state = states[r.team] || "pre_game";
    const pts = state === "pre_game" ? null : gdPts(league.rules, r, s || {});
    return {...r, pts, line: state === "pre_game" ? "" : gdLine(r, s || {}), state};
  });
  const rows = all.filter(gdStarter), bench = all.filter(r => !gdStarter(r));
  const count = st => rows.filter(r => r.state === st).length;
  return {id, name: league.teams[id].name, rows, bench, total: gdSum(rows), benchTotal: gdSum(bench),
          done: count("complete"), playing: count("in_game"), left: count("pre_game")};
}

/* Where a side should finish: what the finished have, the projection of who hasn't played, and for a
   man mid-game the larger of the two (no game clock to prorate by, so he is taken to reach his
   projection unless he already passed it). `projOf(row)` is a number or null. */
function gdProj(side, projOf){
  const p = side.rows.reduce((a, r) => {
    const pr = projOf(r);
    if (r.state === "complete") return a + (r.pts || 0);
    if (r.state === "in_game") return a + Math.max(r.pts || 0, pr || 0);
    return a + (pr || 0);
  }, 0);
  return Math.round(p * 100) / 100;
}

/* Every team's total, best first, with the median between the two halves (ESPN's top-half win). */
function gdLadder(sides){
  const all = [...sides].sort((a, b) => b.total - a.total);
  const half = Math.floor(all.length / 2);
  const median = all.length ? (all.length % 2 ? all[half].total : (all[half - 1].total + all[half].total) / 2) : 0;
  return {median: Math.round(median * 100) / 100, rows: all.map((s, i) => ({...s, top: i < half}))};
}

/* DIGEST CARD: Softest defenses (Wednesday). One row per position, QB RB WR TE K: the defense that has
   allowed the most fantasy points a game to it this season (LIVE_DEFENSE, design/defense.py, rank 1 allows the
   fewest). Row: the team's tile, its city, "vs QBs - plays ARI", the points a game at the right over "most of 32".
   Research: the same defense against the other positions, and last season's number. The kicker row has no per-defense
   number in LIVE_DEFENSE: it is the defense with the most Yahoo kicker points a game allowed this season
   (LIVE_SOS.k_allowed, rank 32 = most), and the row is skipped when the file has none. Context, not a prediction:
   the foot carries the schedule's own result (METHODOLOGY 12.97, did not predict points). Interface: card.js. */

const DG_CODE_ALIAS = {LAR: "LA", WSH: "WAS", JAC: "JAX"};   // a spelling for the same club, not copy

/* Every club's city, spelled out so the copy check finds each key. */
const dgCity = code => ({
  ARI: () => t("digest.card.defenses.cityARI"), ATL: () => t("digest.card.defenses.cityATL"), BAL: () => t("digest.card.defenses.cityBAL"),
  BUF: () => t("digest.card.defenses.cityBUF"), CAR: () => t("digest.card.defenses.cityCAR"), CHI: () => t("digest.card.defenses.cityCHI"),
  CIN: () => t("digest.card.defenses.cityCIN"), CLE: () => t("digest.card.defenses.cityCLE"), DAL: () => t("digest.card.defenses.cityDAL"),
  DEN: () => t("digest.card.defenses.cityDEN"), DET: () => t("digest.card.defenses.cityDET"), GB: () => t("digest.card.defenses.cityGB"),
  HOU: () => t("digest.card.defenses.cityHOU"), IND: () => t("digest.card.defenses.cityIND"), JAX: () => t("digest.card.defenses.cityJAX"),
  KC: () => t("digest.card.defenses.cityKC"), LA: () => t("digest.card.defenses.cityLA"), LAC: () => t("digest.card.defenses.cityLAC"),
  LV: () => t("digest.card.defenses.cityLV"), MIA: () => t("digest.card.defenses.cityMIA"), MIN: () => t("digest.card.defenses.cityMIN"),
  NE: () => t("digest.card.defenses.cityNE"), NO: () => t("digest.card.defenses.cityNO"), NYG: () => t("digest.card.defenses.cityNYG"),
  NYJ: () => t("digest.card.defenses.cityNYJ"), PHI: () => t("digest.card.defenses.cityPHI"), PIT: () => t("digest.card.defenses.cityPIT"),
  SEA: () => t("digest.card.defenses.citySEA"), SF: () => t("digest.card.defenses.citySF"), TB: () => t("digest.card.defenses.cityTB"),
  TEN: () => t("digest.card.defenses.cityTEN"), WAS: () => t("digest.card.defenses.cityWAS"),
})[DG_CODE_ALIAS[code] || code];
const dgCityName = code => (dgCity(code) || (() => code))();

const dgDefPosWord = pos => ({QB: () => t("digest.card.defenses.posQB"), RB: () => t("digest.card.defenses.posRB"),
  TE: () => t("digest.card.defenses.posTE"), WR: () => t("digest.card.defenses.posWR"), K: () => t("digest.card.defenses.posK")})[pos]();
const dgDefToWord = pos => ({QB: () => t("digest.card.defenses.toQB"), RB: () => t("digest.card.defenses.toRB"),
  TE: () => t("digest.card.defenses.toTE"), WR: () => t("digest.card.defenses.toWR")})[pos]();

/* The kicker's: the defense that has allowed Yahoo kickers the most points a game this season (LIVE_SOS.k_allowed,
   rank 32 = most), {team, pts, of}, or null when the file has none or its numbers are null. */
function dgKickerTop(sos){
  const rows = Object.entries((sos && sos.k_allowed) || {}).map(([team, s]) => ({team, s})).filter(x => x.s && x.s.pts_pg != null);
  if (!rows.length) return null;
  rows.sort((a, b) => b.s.pts_pg - a.s.pts_pg || (a.team < b.team ? -1 : 1));
  return {team: rows[0].team, pts: rows[0].s.pts_pg, of: Math.max(rows.length, ...rows.map(x => x.s.rank || 0))};
}

/* "most" for the top of the league, "#2 most" for the next: the club's place in dgAllowed (data/dayplan.js), the one
   place that works the rank out. */
function dgDefRank(def, team, pos){
  const a = dgAllowed(def, team, pos);
  return !a ? "" : a.most === 1 ? t("digest.card.defenses.most") : t("digest.card.defenses.rankMost", {n: a.most});
}

/* Who the club plays this week (the page's week), or "". */
function dgDefOpp(ctx, team){
  const sch = ctx.schedule, code = schedCode(DG_CODE_ALIAS[team] || team);
  const g = ((sch && sch.games) || []).filter(x => x.week === sch.week).find(x => x.home === code || x.away === code);
  return g ? (g.home === code ? g.away : g.home) : "";
}

function dgDefenseResearch(def, team, pos){
  const f = def.form[team], cur = (f && f.current) || {}, prior = f && f.prior;
  const others = DG_DEF_POS.filter(p => p !== pos && cur[p] && cur[p].pts_pg != null).map(p => [dgDefToWord(p), cur[p].rank
    ? t("digest.card.defenses.aPoints", {pts: cur[p].pts_pg.toFixed(1), rank: dgDefRank(def, team, p)})
    : t("digest.card.defenses.kPoints", {pts: cur[p].pts_pg.toFixed(1)})]);
  const was = prior && prior[pos] && prior[pos].pts_pg != null
    ? [t("digest.card.defenses.prior", {pos: dgDefPosWord(pos)}), t("digest.card.defenses.kPoints", {pts: prior[pos].pts_pg.toFixed(1)})] : null;
  return was ? [...others, was] : others;
}

/* One position's row; `research` is the same defense against the other positions (none for K: the data has no
   per-position numbers for it). */
function dgDefenseRow(ctx, pos, top, research){
  const team = top.team, opp = dgDefOpp(ctx, team), v = {pos: dgDefPosWord(pos), opp: esc(opp)};
  return dgRowHTML("defenses", {tile: team, n: dgCityName(team),
    meta: opp ? t("digest.card.defenses.meta", v) : t("digest.card.defenses.metaBye", v),
    answer: {num: top.pts.toFixed(1), change: t("digest.card.defenses.mostOf", {of: top.of}), dir: "flat"}, research});
}

function dgCardDefenses(ctx){
  const form = ctx.def && ctx.def.form;
  const rows = DG_DEF_POS.map(pos => [pos, dgDefenseTop(form, pos)]).filter(([, top]) => top)
    .map(([pos, top]) => dgDefenseRow(ctx, pos, top, dgDefenseResearch(ctx.def, top.team, pos)));
  const k = dgKickerTop(ctx.sos);
  if (k) rows.push(dgDefenseRow(ctx, "K", k, []));
  if (!rows.length) return "";
  return dgCardHTML({id: "defenses", title: t("digest.card.defenses.title"), more: {leaf: "schedule"}, body: rows.join(""),
    foot: t("digest.card.defenses.foot")});
}

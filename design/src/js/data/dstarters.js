/* ============================== DEFENDERS OUT: THE CUT ==============================
   Preview's chips and the profile's Matchup note (2026-10-06). LIVE_D_STARTERS is ff-jarvis's d_starters block
   (design/d_starters.py): per defense, how many of its top-11 snap-takers are Out, Doubtful, IR, PUP, suspended or
   off the team this week, by unit (front seven, secondary), with their names. A displayed fact, never a price:
   nothing here touches a projection, a rank, an order or a call, and no word of it says start, sit, bet or fade.
   This file picks the unit a position reads (a back the front seven, a WR or TE the secondary, a QB all of it),
   treats a missing count as no data (a defense with no earlier game is null, not zero), and words the line.
   It computes no number: a count is the number of the file's own players. Pinned by tests/test_js_dstarters.py. */

/* The unit each position reads; "any" is every missing starter. K and D/ST read none. */
const DS_UNIT = {QB: "any", RB: "front7", WR: "secondary", TE: "secondary"};
const DS_NAMES = 3;

/* The defense by either spelling of its code (the block's `alias`: nflverse LA is the page's LAR). */
function dsTeam(block, code){
  if (!block || !block.teams || !code) return null;
  return block.teams[(block.alias && block.alias[code]) || code] || null;
}

/* "Will McDonald IV" -> "McDonald". */
const dsSurname = n => n.replace(/\s+(Jr|Sr|II|III|IV|V)\.?$/i, "").trim().split(/\s+/).pop();

/* A set of missing starters from one unit says its unit; a mix, or a starter with no unit, says "any". */
function dsKindOf(players){
  const units = new Set(players.map(p => p.unit));
  return units.size === 1 && !units.has(null) && !units.has(undefined) ? [...units][0] : "any";
}

/* One defense's view, {team, kind, n, players}, or null with nothing missing in `want` ("any", "front7",
   "secondary"), a null count (no earlier game) or no such defense. */
function dsView(block, code, want){
  const rec = dsTeam(block, code);
  if (!rec || !rec.n_missing) return null;
  const all = rec.players || [];
  const players = want === "any" ? all : all.filter(p => p.unit === want);
  return players.length ? {team: rec.team, kind: dsKindOf(players), n: players.length, players} : null;
}

/* The game's short defenses, away first: [] when neither is short, there is no block, or the block is for another
   week than `week` (the game's own: the block holds this week's starters, never an earlier game's). */
function dsGameViews(block, game, week){
  if (!block || block.week !== week) return [];
  return [game.away, game.home].map(code => dsView(block, code, "any")).filter(Boolean);
}

/* The defense a player faces, read by his position, only for the block's own week. */
function dsPlayerView(block, pos, week, opp){
  const want = DS_UNIT[pos];
  if (!want || !block || block.week !== week) return null;
  return dsView(block, opp, want);
}

/* "NO D: 2 front-seven starters out (Elliss, Granderson)"; past three names the rest are counted ("+2").
   HTML-safe: the team and the names are escaped. */
function dsChipText(v){
  const names = v.players.slice(0, DS_NAMES).map(p => esc(dsSurname(p.name))).join(", ")
    + (v.players.length > DS_NAMES ? " " + t("ds.more", {n: v.players.length - DS_NAMES}) : "");
  const vars = {team: esc(v.team), n: v.n, names};
  // Every copy key literal (assemble.py --check scans for them).
  const line = v.n === 1
    ? {front7: t("ds.chip.front7One", vars), secondary: t("ds.chip.secondaryOne", vars), any: t("ds.chip.anyOne", vars)}
    : {front7: t("ds.chip.front7Many", vars), secondary: t("ds.chip.secondaryMany", vars), any: t("ds.chip.anyMany", vars)};
  return line[v.kind] || line.any;
}

/* The status as the reader would say it; a status the page does not know is shown as it came. */
function dsStatusWord(s){
  const known = {out: t("ds.status.out"), doubtful: t("ds.status.doubtful"), ir: t("ds.status.ir"), pup: t("ds.status.pup"),
    sus: t("ds.status.sus"), suspended: t("ds.status.suspended"), offteam: t("ds.status.offteam")};
  return known[String(s).toLowerCase().replace(/\s+/g, "")] || s;
}

/* The why: the file's own evidence line, else the copy's. Both say it is unproven. */
const dsWhyText = rules => (rules && rules.evidence) || t("ds.why.fallback");

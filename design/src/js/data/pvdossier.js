/* ------------------------------------------------------------------
   PREVIEW dossier's numbers (ledger #82, 2026-10-09, storyboard draft A "Ledger"; David, 2026-10-07: the
   players are "the best part and buried", the Moneyline / Spread / Total rows "hard to read").

   pvPlayerLine: a player call's row leads with the yards our model expects (the line's `mu`) and his chance
   to score (the TD line's `model`), from his lines this week, never fantasy points. His position's own yards
   market first (PV_YDS), else any yards line he has. The page computes nothing: both numbers are the model's,
   only rounded to the yard.

   pvOurs: Claude's pick in Vegas's own units, so each bet reads number beside number ("CHI by 1.5" beside
   "CHI by 4", "45.5" beside "42") before the pick word. The margin and total are the take's own score.
------------------------------------------------------------------ */
const PV_YDS = {QB: "PASS", RB: "RUSH", WR: "REC", TE: "REC"};
const pvYdsUnit = m => ({PASS: t("preview.pl.pass"), RUSH: t("preview.pl.rush"), REC: t("preview.pl.rec")})[m] || "";

/* {yds, unit, td, n} from one player's PROPS rows: yards and unit, touchdown chance in %, and how many lines. */
function pvPlayerLine(pos, rows){
  const yd = r => pvYdsUnit(r.mkt) && r.mu != null;
  const y = rows.find(r => r.mkt === PV_YDS[pos] && yd(r)) || rows.find(yd) || null;
  const td = rows.find(r => r.mkt === "TD" && r.model != null) || null;
  return {yds: y ? Math.round(y.mu) : null, unit: y ? pvYdsUnit(y.mkt) : "", td: td ? td.model : null, n: rows.length};
}

/* {ml, spread, total} as Claude's own numbers, or null without a pick. */
function pvOurs(g){
  const p = g.take && g.take.pick;
  if (!p) return null;
  const w = p.winner, s = p.score, by = s[w] - s[w === g.home ? g.away : g.home];
  const chance = g.take.win ? g.take.win[w] : null;
  return {ml: chance != null ? `${esc(w)} ${chance}%` : "", spread: pvSpread(by ? w : null, by), total: String(s[g.home] + s[g.away])};
}

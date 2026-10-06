/* ============================== RECAP: CLAUDE'S WEEK ==============================
   The Claude tab: how Claude's calls did this week, from ff-jarvis's graded Preview takes. Three tiles
   (winners, against the spread, over/under), then the best call and the worst. The record is the week's
   own (LIVE_RECAP.preview_record); the link opens Preview's every-week record. A tile with no record
   is not drawn, so no zeros. */

/* The market's underdog is the side getting points: the home team when the home line is above zero,
   the away team when it is below (spread_home, ff-jarvis's preview_record, is the home side's line). */
const wrUnderdog = (g, side) => { const s = g.preview.spread_home; return s != null && s !== 0 && (side === g.home) === (s > 0); };
const wrLoser = (g, w) => (w === g.home ? g.away : g.home);
const wrPts = (g, side) => (side === g.home ? g.home_pts : g.away_pts);
const wrWon = g => g.preview && g.preview.su_hit !== null && g.preview.su_hit !== undefined
  && g.away_pts != null && g.home_pts != null && g.final;

/* Best call: a winner Claude picked, preferring one the market had as the underdog (the biggest line
   first); with no such pick, the winner he gave the lowest chance. Worst: a miss he was surest of. */
function wrBestCall(d){
  const hits = d.games.filter(g => wrWon(g) && g.preview.su_hit);
  const dogs = hits.filter(g => wrUnderdog(g, g.preview.winner));
  const pick = dogs.length ? dogs.reduce((a, b) => Math.abs(b.preview.spread_home) > Math.abs(a.preview.spread_home) ? b : a)
    : hits.reduce((a, b) => !a || (b.preview.win_pct || 100) < (a.preview.win_pct || 100) ? b : a, null);
  return pick ? {g: pick, dog: dogs.length > 0} : null;
}
function wrWorstCall(d){
  const misses = d.games.filter(g => wrWon(g) && !g.preview.su_hit && g.preview.win_pct != null);
  return misses.length ? misses.reduce((a, b) => b.preview.win_pct > a.preview.win_pct ? b : a) : null;
}

function wrCallRow(cls, label, head, sub){
  return `<div class="wr-call" data-testid="recap-call"><b class="wr-mk ${cls}">${label}</b><span>${head}</span><p>${sub}</p></div>`;
}
function wrCallsHTML(d){
  const best = wrBestCall(d), worst = wrWorstCall(d), score = (g, w) => ({ws: wrPts(g, w), ls: wrPts(g, wrLoser(g, w))});
  const b = best && best.g, w = worst;
  return (b ? wrCallRow("hit", t("weekrecap.claude.best"),
      t("weekrecap.claude.bestHead", {winner: esc(b.preview.winner), loser: esc(wrLoser(b, b.preview.winner)), ...score(b, b.preview.winner)}),
      best.dog ? t("weekrecap.claude.bestDog") : t("weekrecap.claude.bestPct", {pct: b.preview.win_pct})) : "")
    + (w ? wrCallRow("miss", t("weekrecap.claude.worst"),
      t("weekrecap.claude.worstHead", {team: esc(w.preview.winner), pct: w.preview.win_pct}),
      t("weekrecap.claude.worstSub", {winner: esc(wrLoser(w, w.preview.winner)), ...score(w, wrLoser(w, w.preview.winner))})) : "");
}

function wrClaudeHTML(d){
  const rec = wrRecord(d), calls = wrCallsHTML(d);
  if (!rec && !calls) return "";
  const tile = (s, label) => s ? `<div class="wr-tile"><b data-testid="recap-tile-value">${pvWL(s)}</b><span data-testid="recap-tile-label">${label}</span></div>` : "";
  const tiles = rec ? `<div class="wr-tiles">${tile(rec.su, t("weekrecap.claude.winners"))}${tile(rec.ats, t("weekrecap.claude.vsSpread"))}${
    tile(rec.total, t("weekrecap.claude.overUnder"))}</div>` : "";
  const every = pvRecord() && pvRecord().weeks.length
    ? `<button type="button" class="wr-link" data-testid="recap-every-week" data-wrrec>${t("weekrecap.claude.every")}${WR_ARROW}</button>` : "";
  return `<section class="wr-card wr-claude" data-testid="recap-claude"><div class="wr-chr"><h3 class="wr-ch">${t("weekrecap.claude.title")}</h3>${every}</div>
    ${tiles}${calls ? `<div class="wr-calls">${calls}</div>` : ""}</section>`;
}

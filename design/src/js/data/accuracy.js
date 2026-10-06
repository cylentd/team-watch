/* ============================== ACCURACY: THE CUT ==============================
   Recap > Accuracy (2026-10-05). LIVE_ACCURACY is ff-jarvis's accuracy.json passed through (design/accuracy.py):
   per week and position, our mean miss beside FantasyPros' on the players both projected, then the season to
   date with the scorecard's CI. This file only reorders and labels. It computes no number the file holds: a
   mean miss, a rank match, a hit rate, d and its range are printed as the file has them. The one comparison it
   makes is which of two printed misses is smaller, so a reader sees who was closer. A field the file has as null
   stays null, and the page says so, never a zero. Pinned by tests/test_accuracy_view.py. */

const AC_POS = ["QB", "RB", "WR", "TE"];

/* Who was closer, from two mean misses: "ours", "fp", "tie", or null when either is missing. */
function acCloser(ours, fp){
  if (typeof ours !== "number" || typeof fp !== "number") return null;
  return ours < fp ? "ours" : ours > fp ? "fp" : "tie";
}

const acNum = v => (typeof v === "number" ? v : null);
const acSide = s => ({mae: acNum(s && s.mae), rho: acNum(s && s.rho), hit: acNum(s && s.hit)});

function acWeekView(w){
  const rows = AC_POS.filter(p => w.by_pos && w.by_pos[p]).map(p => {
    const sh = w.by_pos[p].shared || {}, ours = acSide(sh.ours), fp = acSide(sh.fp);
    return {pos: p, n: acNum(sh.n), ours, fp, hit_n: acNum(sh.hit_n), rank_n: acNum(sh.rank_n), closer: acCloser(ours.mae, fp.mae)};
  });
  const ranked = rows.some(r => r.ours.rho !== null || r.fp.rho !== null || r.ours.hit !== null || r.fp.hit !== null);
  return {week: w.week, model: w.model || "", note: w.note || "", rows, ranked};
}

/* "1–3" for a run of weeks, else "1, 2, 4". */
function acRange(weeks){
  const w = (weeks || []).slice().sort((a, b) => a - b);
  if (!w.length) return "";
  return w.every((x, i) => i === 0 || x === w[i - 1] + 1) && w.length > 1 ? `${w[0]}–${w[w.length - 1]}` : w.join(", ");
}

/* d is our miss minus FantasyPros': above 0 means FantasyPros was closer (the file's rule). `clear` = its
   range leaves 0 out; no range means no claim. */
function acSeasonView(s){
  const by = s.by_pos || {};
  const rows = [...AC_POS, "ALL"].filter(p => by[p] && by[p].shared).map(p => {
    const sh = by[p].shared, d = acNum(sh.d);
    const ci = Array.isArray(sh.d_ci) && sh.d_ci.length === 2 ? sh.d_ci : null;
    return {pos: p, n: acNum(sh.n), maeOurs: acNum(sh.mae_ours), maeFp: acNum(sh.mae_fp), d, ci,
      closer: d === null ? null : d > 0 ? "fp" : d < 0 ? "ours" : "tie",
      clear: !!ci && (ci[0] > 0 || ci[1] < 0)};
  });
  return rows.length ? {range: acRange(s.weeks), stale: !!s.stale, rows} : null;
}

/* The page's view of LIVE_ACCURACY, or null with no file or no graded week. Newest week first. */
function acView(raw){
  if (!raw || !Array.isArray(raw.weeks) || !raw.weeks.length) return null;
  const level = raw.rules && raw.rules.ci_level;
  return {
    ciLevel: typeof level === "number" ? level : 95,
    weeks: raw.weeks.map(acWeekView).sort((a, b) => b.week - a.week),
    missing: (raw.missing_weeks || []).slice().sort((a, b) => a - b),
    season: raw.season_to_date ? acSeasonView(raw.season_to_date) : null,
  };
}

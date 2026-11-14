/* ============================== DEFENSE FORM ==============================
   TODO "Outcome ranges" (d), 2026-11-14. LIVE_SOS.defense_recent is ff-jarvis's: per defense and position its last 3
   games against its season (points allowed a game; a back's also rush yards) and a `trend`, "up" when the defense
   allowed more lately by the file's own margin, "down" when less, null otherwise. Before 3 games the last-3 numbers
   and the trend are null. The page computes nothing: a form is the file's two numbers and its word, or null.
   Context only: form failed as a price (ff-jarvis METHODOLOGY 12.73), so it moves no rank, order or call.
   Schedule draws the next opponent's (surface/sos/), Preview each side's (surface/preview/form.js). Pinned by
   tests/test_js_defform.py. */

const DF_POS = ["QB", "RB", "WR", "TE"];
const DF_TRENDS = ["up", "down"];

/* One defense against one position: {def, pos, kind, last3, season, trend}, or null when no trend fired, fewer than 3
   games were played, or the file has no such defense. A back reads rush yards when the run trend fired (yards are what
   a run defense gives up), else his points. */
function dfForm(raw, def, pos){
  const e = raw && raw.defense_recent && raw.defense_recent[def], p = e && e[pos];
  if (!p) return null;
  const pick = (kind, last3, season, trend) => (DF_TRENDS.includes(trend) && last3 != null && season != null)
    ? {def, pos, kind, last3, season, trend} : null;
  return (pos === "RB" && pick("rush", p.last3_rush_yds_pg, p.season_rush_yds_pg, p.rush_trend))
    || pick("pts", p.last3_pts_pg, p.season_pts_pg, p.trend);
}

/* A Schedule row's next game: the first week of the window that is not a bye, only when the window starts this week
   (the file's from_week). The playoff weeks start later, and today's form says nothing about them. */
function dfNext(raw, pos, weeks, cells){
  if (!raw || !weeks || !weeks.length || weeks[0] !== raw.from_week) return null;
  const next = (cells || []).find(c => !c.bye);
  return next ? dfForm(raw, next.opp, pos) : null;
}

/* A game's two offenses, away first, each with the forms of the defense it faces: [{off, def, forms}], a side with
   none left out. */
function dfSides(raw, away, home){
  return [[away, home], [home, away]]
    .map(([off, def]) => ({off, def, forms: DF_POS.map(p => dfForm(raw, def, p)).filter(Boolean)}))
    .filter(s => s.forms.length);
}

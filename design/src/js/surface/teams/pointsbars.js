/* The fantasy-points bars, drawn (2026-10-07). data/pointsbars.js says what each bar is; this draws it small
   on a Sheet row (no numbers, no label: the shape is the point) and bigger on a card's back (each bar's
   points over it, its week under it). Neutral ink, the projection a hollow bar in full ink: colour would
   say good or bad, and a bar is only a week's points. */

/* His model from the box score and this week's projection; null with neither. `limit` is the slots that fit. */
function pbFor(p, limit){
  if (!p.slug) return null;
  const wk = schedWeek() ?? (typeof LIVE_GAMELOG !== "undefined" && LIVE_GAMELOG ? (LIVE_GAMELOG.through || 0) + 1 : null);
  if (wk === null) return null;
  return pbModel(gamelogRows(p.slug), projFor(p), wk, limit);
}

/* A bar: a played week's, an empty slot's tick (a bye, an injury), or the projection's hollow one. */
function pbBarHTML(s, proj){
  const none = s.pts === null;
  const tip = proj ? (none ? "" : t("teams.pb.projected", {n: s.pts.toFixed(1), wk: s.wk}))
    : none ? t("teams.pb.weekOff", {wk: s.wk}) : t("teams.pb.pts", {n: s.pts.toFixed(1), wk: s.wk});
  return `<i class="pb-b${proj ? " proj" : ""}${none ? " gap" : ""}" style="--h:${none ? 0 : s.h}"${tip ? ` title="${tip}"` : ""} data-testid="${proj ? "roster-bar-proj" : "roster-bar"}"></i>`;
}

/* The row's: every week, then the projection, in one strip. */
function pbRowHTML(p){
  const m = pbFor(p);
  if (!m) return "";
  return `<div class="pb" data-testid="roster-row-bars">${m.slots.map(s => pbBarHTML(s, false)).join("")}${pbBarHTML(m.proj, true)}</div>`;
}

/* The back's: the latest weeks that fit, each bar with its points over it and its week under it. Null
   when he has nothing to draw. */
const PB_BACK_SLOTS = 5;
function pbBackHTML(p){
  const m = pbFor(p, PB_BACK_SLOTS);
  if (!m) return "";
  const slot = (s, proj) => `<div class="pb-s${proj ? " proj" : ""}"><span class="pb-n" data-testid="roster-back-pts">${pbPtsText(s.pts)}</span>${pbBarHTML(s, proj)}<span class="pb-w" data-testid="roster-back-week">${pbWeekText(s.wk)}</span></div>`;
  return `<div class="pb pb-back" data-testid="roster-back-bars">${m.slots.map(s => slot(s, false)).join("")}${slot(m.proj, true)}</div>`;
}

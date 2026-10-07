/* The fantasy-points bars, drawn (2026-10-07). data/pointsbars.js says what each bar is; this draws it small
   on a Sheet row (a phone: no numbers, no label, the shape is the point; a desktop adds each bar's points
   over it and its week under it) and bigger on a card's back (points over, week under). The bars' colours are
   css/surface/teams/pointsbars.css's: a bar is only a week's points, never a verdict. */

/* His model from the box score and this week's projection; null with neither. `limit` is the slots that fit. */
function pbFor(p, limit){
  if (!p.slug) return null;
  const wk = schedWeek() ?? (typeof LIVE_GAMELOG !== "undefined" && LIVE_GAMELOG ? (LIVE_GAMELOG.through || 0) + 1 : null);
  if (wk === null) return null;
  return pbModel(gamelogRows(p.slug), projFor(p), wk, limit);
}

/* A bar: a played week's, an empty slot's tick (a bye, an injury), or the projection's dashed one. `last`
   marks the latest week he played. `labels` puts its points and week on it as data for a desktop row, which
   draws them over and under the bar from CSS (a row holds no text: a phone shows the shape alone). */
function pbBarHTML(s, proj, last, labels){
  const none = s.pts === null;
  const tip = proj ? (none ? "" : t("teams.pb.projected", {n: s.pts.toFixed(1), wk: s.wk}))
    : none ? t("teams.pb.weekOff", {wk: s.wk}) : t("teams.pb.pts", {n: s.pts.toFixed(1), wk: s.wk});
  const tag = labels ? ` data-n="${pbPtsText(s.pts)}" data-w="${pbWeekText(s.wk)}"` : "";
  return `<i class="pb-b${proj ? " proj" : ""}${none ? " gap" : ""}${last ? " last" : ""}" style="--h:${none ? 0 : s.h}"${tip ? ` title="${tip}"` : ""}${tag} data-testid="${proj ? "roster-bar-proj" : "roster-bar"}"></i>`;
}

/* The index of the latest week he played, -1 when none. */
const pbLastPlayed = m => m.slots.reduce((at, s, i) => s.pts !== null ? i : at, -1);

/* The back's slot: the bar with its points over it and its week under it. `signed` is the week a signed card
   was signed for: a gold star over its points, no words. */
function pbSlotHTML(s, proj, last, signed){
  const star = signed ? '<i class="pb-star" aria-hidden="true" data-testid="roster-back-signed"></i>' : "";
  return `<div class="pb-s${proj ? " proj" : ""}${signed ? " signed" : ""}">${star}<span class="pb-n" data-testid="roster-back-pts">${pbPtsText(s.pts)}</span>${pbBarHTML(s, proj, last, false)}<span class="pb-w" data-testid="roster-back-week">${pbWeekText(s.wk)}</span></div>`;
}

/* The row's: every week, then the projection, in one strip of bars. */
function pbRowHTML(p){
  const m = pbFor(p);
  if (!m) return "";
  const last = pbLastPlayed(m);
  return `<div class="pb" data-pos="${esc(p.pos)}" data-testid="roster-row-bars">${m.slots.map((s, i) => pbBarHTML(s, false, i === last, true)).join("")}${pbBarHTML(m.proj, true, false, true)}</div>`;
}

/* The back's: the latest weeks that fit, each bar with its points over it and its week under it; a signed
   card's week has its star. Null when he has nothing to draw. */
const PB_BACK_SLOTS = 5;
function pbBackHTML(p){
  const m = pbFor(p, PB_BACK_SLOTS);
  if (!m) return "";
  const won = cardSigned(p), last = pbLastPlayed(m);
  const slots = m.slots.map((s, i) => pbSlotHTML(s, false, i === last, pbIsSigned(s, won ? LIVE_SIGNED.wk : null))).join("");
  return `<div class="pb pb-back" data-pos="${esc(p.pos)}" data-testid="roster-back-bars">${slots}${pbSlotHTML(m.proj, true, false, false)}</div>`;
}

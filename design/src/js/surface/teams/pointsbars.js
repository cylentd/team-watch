/* The fantasy-points bars, drawn (2026-10-07). data/pointsbars.js says what each bar is; this draws it small
   on a Sheet row (a phone: no numbers, no label, the shape is the point; a desktop adds each bar's points
   over it and its week under it) and bigger on a card's back (points over, week under). The bars' colours are
   css/surface/teams/pointsbars.css's: a bar is only a week's points, never a verdict. */

/* His model from the box score and this week's projection; null with neither. `limit` is the slots that fit. */
function pbFor(p, limit, lg){
  const wk = schedWeek() ?? (typeof LIVE_GAMELOG !== "undefined" && LIVE_GAMELOG ? (LIVE_GAMELOG.through || 0) + 1 : null);
  if (wk === null) return null;
  if (p.pos === "K" || p.pos === "DST") return pbSupportFor(p, limit, lg, wk);
  if (!p.slug) return null;
  const signed = typeof LIVE_SIGNED !== "undefined" ? LIVE_SIGNED : null;
  return pbMarkSigned(pbModel(gamelogRows(p.slug), projFor(p), wk, limit), pbSignedWeeks(signed, p.slug));
}

/* A kicker's or a defense's: the club's points under the league's scoring (LIVE_KDST, data/kdst.js), the
   projection the card back already showed (LIVE_DST). Null without the file or a cell for the position (ESPN has
   no K slot), and the back keeps its facts. A kicker's weeks that another kicker kicked are marked `faded`. */
function pbSupportFor(p, limit, lg, wk){
  const D = typeof LIVE_DST !== "undefined" ? LIVE_DST : null, K = typeof LIVE_KDST !== "undefined" ? LIVE_KDST : null;
  const rows = kdstRows(K, p.team, kdstKey(D, lg, p.pos));
  const m = rows && pbModel(rows, dstPointsFor(D, lg, p.pos, p.team, wk), wk, limit);
  if (m && p.pos === "K"){ const off = new Set(kdstFaded(K, p.team, p.n)); m.slots.forEach(s => { s.faded = off.has(s.wk); }); }
  return m;
}

/* The league a team's card or row is scored in: a leaguemate's team plays in its own, any other is its own key. */
function pbLeague(teamKey){
  const tm = typeof TEAMS !== "undefined" ? TEAMS[teamKey] : null;
  return tm && tm.mate ? tm.league : teamKey;
}

/* A K or D/ST row's right-hand number: the projection the card back shows (LIVE_DST), one decimal; "" when the
   league has none, and the row keeps projNumHTML's. */
function supportNumHTML(p, lg){
  if (p.pos !== "K" && p.pos !== "DST") return "";
  const v = dstPointsFor(typeof LIVE_DST !== "undefined" ? LIVE_DST : null, lg, p.pos, p.team, schedWeek());
  return typeof v === "number" ? `<div class="rproj" data-testid="roster-row-proj">${v.toFixed(1)}</div>` : "";
}

/* A bar: a played week's, an empty slot's tick (a bye, an injury), or the projection's dashed one. `last`
   marks the latest week he played. `labels` puts its points and week on it as data for a desktop row, which
   draws them over and under the bar from CSS (a row holds no text: a phone shows the shape alone). */
function pbBarHTML(s, proj, last, labels){
  const none = s.pts === null;
  const tip = proj ? (none ? "" : t("teams.pb.projected", {n: s.pts.toFixed(1), wk: s.wk}))
    : none ? t("teams.pb.weekOff", {wk: s.wk}) : t("teams.pb.pts", {n: s.pts.toFixed(1), wk: s.wk});
  const tag = labels ? ` data-n="${pbPtsText(s.pts)}" data-w="${pbWeekText(s.wk)}"` : "";
  return `<i class="pb-b${proj ? " proj" : ""}${none ? " gap" : ""}${last ? " last" : ""}${s.faded ? " faded" : ""}${s.signed ? " signed" : ""}" style="--h:${none ? 0 : s.h}"${tip ? ` title="${tip}"` : ""}${tag} data-testid="${proj ? "roster-bar-proj" : s.signed && !labels ? "roster-back-signed" : "roster-bar"}"></i>`;
}

/* The index of the latest week he played, -1 when none. */
const pbLastPlayed = m => m.slots.reduce((at, s, i) => s.pts !== null ? i : at, -1);

/* The back's slot: the bar with its points over it and its week under it. A signed week (s.signed, any week he
   finished top 3 at his position) is a gold bar with its points in gold: no words, no star. */
function pbSlotHTML(s, proj, last){
  return `<div class="pb-s${proj ? " proj" : ""}${s.signed ? " signed" : ""}"><span class="pb-n" data-testid="roster-back-pts">${pbPtsText(s.pts)}</span>${pbBarHTML(s, proj, last, false)}<span class="pb-w" data-testid="roster-back-week">${pbWeekText(s.wk)}</span></div>`;
}

/* The row's: every week, then the projection, in one strip of bars. */
function pbRowHTML(p, lg){
  const m = pbFor(p, undefined, lg);
  if (!m) return "";
  const last = pbLastPlayed(m);
  return `<div class="pb" data-pos="${esc(p.pos)}" data-testid="roster-row-bars">${m.slots.map((s, i) => pbBarHTML(s, false, i === last, true)).join("")}${pbBarHTML(m.proj, true, false, true)}</div>`;
}

/* The back's: the latest weeks that fit, each bar with its points over it and its week under it; a signed
   week is a gold bar. Null when he has nothing to draw. */
const PB_BACK_SLOTS = 5;
function pbBackHTML(p, lg){
  const m = pbFor(p, PB_BACK_SLOTS, lg);
  if (!m) return "";
  const last = pbLastPlayed(m);
  const slots = m.slots.map((s, i) => pbSlotHTML(s, false, i === last)).join("");
  return `<div class="pb pb-back" data-pos="${esc(p.pos)}" data-testid="roster-back-bars">${slots}${pbSlotHTML(m.proj, true, false)}</div>`;
}

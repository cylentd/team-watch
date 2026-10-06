/* ------------------------------------------------------------------
   RANKS > D/ST and K (2026-10-05, plan U6c: "Stream a D/ST: not possible today").

   Two more position tabs beside QB RB WR TE FLEX. A row is a team: its place and the game, this week's
   points, then one line of who holds it in the reader's league (or Free, or a Streamer tag) and the next
   three weeks as small cells. All of it is ff-jarvis's (LIVE_DST via design/dst.py, METHODOLOGY 12.85);
   data/dst.js picks the league's cell and orders by the file's own rank, this file only draws.

   The league is the reader's team's (data/league.js lgFocusKey, the one chip), ESPN with no team picked.
   D/ST points are on that league's scoring; K shows only in a Yahoo league, ESPN has no K slot. The
   model's extra inputs cut the average miss against the opponent's expected score alone by 0.02 to 0.04
   points a game for D/ST, about 0.01 for K (12.85), so the board says in one line that a close rank is a
   tie. A row on ESPN waivers says Waivers, not Free. A week with no posted line is an estimate: "~".
------------------------------------------------------------------ */
/* No block for another week: the D/ST and K tabs are not drawn, as with no file (data/schedule.js schedIsPageWeek). */
const rkDstBlock = () => {
  const b = typeof LIVE_DST !== "undefined" && LIVE_DST;
  return b && schedIsPageWeek((b.weeks || [])[0]) ? b : null;
};
const rkLeague = () => dstLeagueKey(lgFocusKey(), !!lgMine(), rkDstBlock());

/* The way in from another view: open Ranks on the D/ST tab. Its one caller today is the Waivers view's
   "Stream a D/ST" link (surface/teams/waiver.js wvDstLinkHTML, wired in wvmotion.js). */
function rkOpenDst(){
  RK_POS = "DST";
  RK_VIEW = "week";   // D/ST is a This week list; Rest of season has none (surface/ranks/ros.js)
  navGo("ranks");
}

/* The one link out of Ranks: the schedule's strength, a hidden leaf (NAV_HIDDEN) another view owns. */
const rkSchedHTML = () => `<button type="button" class="rk-sched" data-testid="ranks-schedule" data-rkgo="schedule">${t("ranks.link.schedule")}</button>`;

const rkVs = home => home === false ? "@" : "vs";
function rkDstGame(r){
  if (r.bye) return t("ranks.dst.bye");
  const when = r.kicked_off ? t("ranks.dst.played") : rkKick(r.kickoff);
  return `${rkVs(r.home)} ${esc(r.opp)}${when ? " · " + when : ""}`;
}

/* Who holds him in the reader's league: yours, free, or the manager's team name. */
function rkHoldHTML(r){
  if (r.mine) return `<i class="rk-dhold mine">${t("ranks.row.mine")}</i>`;
  if (r.waiver) return `<i class="rk-dhold waiver">${t("ranks.dst.waiver")}</i>`;
  if (r.free) return `<i class="rk-dhold free">${t("ranks.dst.free")}</i>`;
  return r.owner ? `<i class="rk-dhold" title="${esc(r.owner)}">${esc(r.owner)}</i>` : "";
}

/* A small cell for a later week: W6 and its points, "~" when estimated, BYE on a bye, lime on a streamer. */
function rkNextHTML(c){
  const val = c.bye ? t("ranks.dst.byeShort") : (c.rating ? "~" : "") + c.pts.toFixed(1);
  const tip = c.bye ? t("ranks.dst.cellBye", {week: c.week})
    : t("ranks.dst.cell", {week: c.week, vs: rkVs(c.home), opp: esc(c.opp)}) + (c.rating ? " " + t("ranks.dst.cellEst") : "");
  return `<span class="rk-dc${c.streamer ? " st" : ""}${c.rating ? " est" : ""}${c.bye ? " bye" : ""}" title="${tip}" aria-label="${tip}">
    <i>${t("ranks.dst.wk", {n: c.week})}</i><b>${val}</b></span>`;
}

function rkDstRowHTML(r){
  const pts = r.bye ? t("ranks.dst.byeShort") : (r.rating ? "~" : "") + r.pts.toFixed(1);
  const tag = r.streamer ? `<b class="rk-dtag" data-testid="ranks-dst-streamer">${t("ranks.dst.streamer")}</b>` : "";
  return `<div class="rk-d${r.bye ? " bye" : ""}${r.mine ? " mine" : ""}${r.kicked_off ? " done" : ""}" data-testid="ranks-dst-row" data-rkteam="${esc(r.team)}">
    <span class="rk-n">${r.bye ? "–" : r.rank}</span>
    <span class="rk-dwho"><b class="rk-dteam">${esc(r.team)}</b><span class="rk-dgame">${rkDstGame(r)}</span></span>
    <span class="rk-dpts${r.rating ? " est" : ""}">${pts}</span>
    <span class="rk-dline"><span class="rk-dtags">${tag || rkHoldHTML(r)}</span>
      <span class="rk-dnext">${r.next.map(rkNextHTML).join("")}</span></span>
  </div>`;
}

/* What this list's points are scored on, in the league's own words. */
function rkDstScoring(b){
  const say = {
    dst_espn: t("ranks.dst.scoring.espn"), dst_yahoo: t("ranks.dst.scoring.yahoo"),
    k_yahoo: t("ranks.dst.scoring.kYahoo"), k_ayo: t("ranks.dst.scoring.kAyo"),
  }[b.cell] || "";
  const league = TEAMS[b.lg] ? tsLeagueName(b.lg) : esc(b.lg);
  return t("ranks.dst.sub", {league, scoring: say});
}

/* The plain line on how much the model adds (12.85), or, when the file carries the baseline, that it is only that. */
const rkDstNote = b => b.source === "baseline" ? t("ranks.dst.noteBase") : b.pos === "K" ? t("ranks.dst.noteK") : t("ranks.dst.note");

function rkDstHTML(chips, b){
  const pos = b.pos === "K" ? "K" : t("ranks.filter.dst");
  return `<div class="wrap rk">
    ${chips}
    <div class="rk-headline"><div><h2>${t("ranks.head.title", {week: b.week, pos})}</h2>
      <p data-testid="ranks-sub">${rkDstScoring(b)}</p><p class="rk-dnote">${rkDstNote(b)}</p></div>${rkSchedHTML()}</div>
    <div class="rk-list"><section class="rk-group rk-dgroup">${b.rows.map(rkDstRowHTML).join("")}</section></div>
    ${b.estimate ? `<p class="rk-dfoot">${t("ranks.dst.est")}</p>` : ""}
  </div>`;
}

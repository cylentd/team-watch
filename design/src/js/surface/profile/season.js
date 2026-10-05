/* The Season pane: every week of his club's schedule in one table, the way Yahoo's game log reads
   (2026-09-28, David: "when someone goes to a player profile, they want to see 2 things right away:
   how many fantasy points did he score, and what is his upcoming matchup").

   One row per week, played or not, so the table is the same length in week 1 as in week 18 -- only
   the rows change state:

     played   his line and his points (LIVE_GAMELOG); a week with a replay opens it (history.js)
     next     the lime row: the kickoff and ff-jarvis's projection, with its rank at his position
     later    the opponent and the kickoff
     bye      the word, nothing else

   The opponent carries its rank against his position from LIVE_DEFENSE, points allowed per game
   this season, counted from the easy end: 1st allows the most. It is the one measure that exists
   for every week; the model's matchup factor (the Matchup pane) exists for next week only, and two
   measures in one column would disagree with each other row to row.

   Built as a grid of rows rather than a <table>: a phone reads each played week as one line of
   box-score shorthand ("24-144-3 · 1-19") where a desktop has room for a column per stat, and a
   future week's kickoff spans the stat columns. Grid areas do both from one DOM; a table would
   need a colspan across columns the phone does not draw. */
const SS_ROW = "row", SS_CELL = "cell";

/* The club's games by week, from the schedule, with the opponent and side from his club's view. */
function seasonGames(team){
  if (!schedOk() || !team) return {};
  const code = schedCode(team), by = {};
  LIVE_SCHEDULE.games.forEach(g => {
    if (g.home !== code && g.away !== code) return;
    const home = g.home === code;
    by[g.week] = {week: g.week, opp: home ? g.away : g.home, home, kickoff: g.kickoff};
  });
  return by;
}

/* [easiest rank, of] of a defence against one position, or null. LIVE_DEFENSE ranks 1 as the
   defence that allows the fewest, so the easy-end count is of - rank + 1. */
function seasonDefRank(opp, pos){
  if (typeof LIVE_DEFENSE === "undefined" || !LIVE_DEFENSE) return null;
  const row = schedTeamRow({teams: LIVE_DEFENSE.form}, opp);
  const cur = row && row.current;
  if (!cur || !cur[pos] || !cur[pos].rank) return null;
  // The field is the highest rank anyone holds, not the count of teams in the block: a block
  // missing a team would otherwise rank someone "0th".
  const of = Math.max(...Object.values(LIVE_DEFENSE.form).map(t => t.current && t.current[pos] ? t.current[pos].rank || 0 : 0));
  return of > 1 && cur[pos].rank <= of ? [of - cur[pos].rank + 1, of] : null;
}

function seasonOppHTML(g, pos){
  const rk = seasonDefRank(g.opp, pos);
  const where = g.home ? "" : t("profile.season.away");
  const cls = rk ? matchupClass(rk[0], rk[1]) : "";
  return `<span class="ss-opp">${where}${esc(g.opp)}</span>`
    + (rk ? `<span class="ss-rk ${cls}">${ordinal(rk[0])}</span>` : "");
}

/* The box-score shorthand: carries-yards-TDs then catches-yards for a back, catches-yards-TDs then
   targets for a receiver, completions are not published so a passer is yards-TDs. */
function seasonLine(pos, r){
  const n = k => r[k] ?? 0;
  if (pos === "QB") return t("profile.season.lineQb", {yds: n("pass_yds"), td: n("pass_td"), rush: n("rush_yds")});
  if (pos === "RB") return t("profile.season.lineRb", {car: n("car"), yds: n("rush_yds"), td: n("rush_td"), rec: n("rec"), ry: n("rec_yds")});
  return t("profile.season.lineWr", {rec: n("rec"), yds: n("rec_yds"), td: n("rec_td"), tgt: n("tgt")});
}

function seasonLineHead(pos){
  return pos === "QB" ? t("profile.season.headQb") : pos === "RB" ? t("profile.season.headRb") : t("profile.season.headWr");
}

const seasonKick = iso => MU_KICK_FMT.format(new Date(iso)).replace(",", "");
/* A played week's date, "Sep 14", in the same Pacific wall clock as the kickoffs, so the When
   column reads as one timeline down the season. */
const SS_DAY_FMT = new Intl.DateTimeFormat("en-US", {timeZone: "America/Los_Angeles", month: "short", day: "numeric"});
const seasonDay = iso => SS_DAY_FMT.format(new Date(iso));

/* One row. `kind` is ss-played / ss-next / ss-later / ss-bye / ss-total / ss-head. Prefixed: a bare
   `head` class picked up a global grid-row rule and put the header under week 1 (2026-09-28). */
function seasonRowHTML(kind, cells, attrs = ""){
  return `<div role="${SS_ROW}" class="ss-row ${kind}"${attrs}>${cells}</div>`;
}
const ssCell = (cls, html, role = SS_CELL) => `<div role="${role}" class="${cls}">${html}</div>`;
const ssHead = (cls, html) => ssCell(cls, html, "columnheader");

/* A played week with a replay opens it (panel.js delegates the click). history.js's weekRowAttrs
   spells a whole class attribute for its <tr>; a row here already has one, so the class goes on
   the kind and only the data attributes are borrowed. */
function seasonOpens(p, r){
  const club = r ? weekOpens(p, r) : null;
  return club ? {cls: " gl-open", attrs: ` data-stripclub="${esc(club)}" data-stripwk="${r.wk}" data-stripname="${esc(p.n)}"`}
    : {cls: "", attrs: ""};
}

/* The weeks the schedule has any game in, plus any week he has a line for, and which of them is his
   bye. A week with no game for his club is his bye only when it is the bye his pedigree names, or,
   with no pedigree, when most of the league plays that week (a real bye week has at least 24 clubs
   on the field); a week the schedule covers thinly is left out rather than called a bye it may not
   be. */
function seasonWeeks(p, rows){
  const clubs = {};
  (schedOk() ? LIVE_SCHEDULE.games : []).forEach(g => { (clubs[g.week] = clubs[g.week] || new Set()).add(g.home).add(g.away); });
  const shown = [...new Set([...Object.keys(clubs).map(Number), ...rows.map(r => r.wk)])].sort((a, b) => a - b);
  const ped = pedigreeFor(p), byeWk = ped && pedHas(ped.bye) ? Number(ped.bye) : null;
  return {shown, isBye: wk => byeWk !== null ? wk === byeWk : (clubs[wk] ? clubs[wk].size : 0) >= 24};
}

/* The projection and what it is. It is his next game's, so it only sits on that row when the
   profile agrees which week that is (a Monday game not yet in the log). Two homes for the label,
   one per layout: a phone hangs "proj · RB3" under the number (the small), a desktop writes it out
   across the stat columns that row has no numbers for (the note). */
function seasonProj(p, prof, pos, wk){
  const proj = projFor(p);
  const projWeek = prof && prof.next ? prof.next.week : null;
  if (proj === null || (projWeek !== null && projWeek !== wk)) return {pts: "", note: ""};
  const pr = typeof LIVE_PROJECTIONS !== "undefined" && LIVE_PROJECTIONS ? LIVE_PROJECTIONS.players[p.slug] : null;
  const rank = pr && pr.rank ? rankText(pos, [pr.rank]) : null;
  const sub = rank ? t("profile.season.projRank", {rank}) : t("profile.season.proj");
  const note = rank ? t("profile.season.projNote", {rank}) : t("profile.season.projNoteBare");
  return {pts: `${proj.toFixed(1)}<small>${sub}</small>`, note};
}

/* ------------------------------------------------------------------ this week, live (2026-10-04)
   LIVE_GAMELOG is cut at build time and lags until the nightly rebuild: on a Sunday his profile said
   "No stats" while Live had scored him. For the page's week, with no row in the log yet, the row is
   drawn from the poll Live already runs (live.js). His stats come from, in order: his own row in the
   poll (a player on one of my rosters, by Sleeper id), then the league-wide leaders (by name and
   club). No Sleeper id and no leader row means no stats, and the row stays as it was. */
const SEASON_LIVE_POS = ["QB", "RB", "WR", "TE"];
let SEASON_OPEN = null, SEASON_LAST = "";       // the profile on screen, and the table last drawn for it

const seasonNameKey = n => String(n || "").toLowerCase().replace(/\b(jr|sr|ii|iii|iv)\b/g, "").replace(/[^a-z]/g, "");
/* The standard half-PPR sum, for a row Sleeper sent no total for. */
const seasonHalfPpr = s => (s.pass_yd || 0) * 0.04 + (s.pass_td || 0) * 4 - (s.pass_int || 0) * 2
  + (s.rush_yd || 0) * 0.1 + (s.rush_td || 0) * 6 + (s.rec || 0) * 0.5 + (s.rec_yd || 0) * 0.1
  + (s.rec_td || 0) * 6 - (s.fum_lost || 0) * 2;

function seasonSid(slug){
  for (const lg of GD.leagues) for (const tm of Object.values(lg.teams)) for (const r of tm.lineup) if (r.slug === slug && r.sid) return r.sid;
  return null;
}

function seasonLiveStats(p, team){
  if (!GD_STATS) return null;
  const sid = seasonSid(p.slug), own = sid && GD_STATS.stats ? GD_STATS.stats[sid] : null;
  if (own && Object.keys(own).length) return {s: own};
  return Object.values(GD_STATS.lead || {}).find(v => seasonNameKey(v.n) === seasonNameKey(p.n) && gdSameClub(team, v.team)) || null;
}

/* His live line in the log's own columns, and his points in the log's own scoring: half-PPR. */
function seasonLiveShape(hit){
  const s = hit.s, n = k => +(s[k] || 0);
  const pts = s.pts_half_ppr ?? hit.pts ?? seasonHalfPpr(s);
  return {pts: Math.round(pts * 10) / 10, car: n("rush_att"), rush_yds: n("rush_yd"), rush_td: n("rush_td"),
    tgt: n("rec_tgt"), rec: n("rec"), rec_yds: n("rec_yd"), rec_td: n("rec_td"), pass_yds: n("pass_yd"), pass_td: n("pass_td")};
}

/* {wk, clock, row} for this week's game once it has kicked off, or null. `repaint` is a redraw from a
   poll: only an opened profile asks for the poll, so a failed one cannot loop through gd:stats. */
function seasonLive(p, team, pos, games, log, repaint){
  const wk = (GD.leagues[0] || {}).week || (GD_STATS && GD_STATS.week), g = games[wk];
  if (!g || log[wk] || !SEASON_LIVE_POS.includes(pos) || Date.parse(g.kickoff) > Date.now()) return null;
  if (!repaint && PAGE_SERVED()) gdEnsure();
  const clock = gdClockOf(team), hit = clock.state === "pre" ? null : seasonLiveStats(p, team);
  return hit ? {wk, clock, row: seasonLiveShape(hit)} : null;
}

/* In progress: lime, "Q3 4:12 · live", the label under the number on a phone. Final: a played row. */
function seasonLiveRowHTML(g, pos, live, stats){
  const ck = live.clock, r = live.row;
  const label = !ck.live || ck.label === t("live.clock.live") ? ck.label : t("profile.season.liveLabel", {clock: ck.label});
  return seasonRowHTML("ss-played" + (ck.live ? " ss-live" : ""),
    ssCell("ss-wk", g.week) + ssCell("ss-opp-c", seasonOppHTML(g, pos)) + ssCell("ss-date", esc(label))
    + ssCell("ss-pts", glNum(r.pts) + (ck.live ? `<small>${esc(label)}</small>` : ""))
    + ssCell("ss-line", seasonLine(pos, r)) + stats(c => glNum(r[c.id])));
}

/* Every poll redraws the open table in place; closed, or on another pane, it does nothing. */
function seasonRepaint(){
  const el = document.querySelector("#modal.on .pf-season");
  if (!el || !SEASON_OPEN) return;
  const was = SEASON_LAST, html = seasonHTML(SEASON_OPEN.p, SEASON_OPEN.prof, true);
  if (html && html !== was) el.outerHTML = html;
}
document.addEventListener("gd:stats", seasonRepaint);
/* Live and the Digest run the poll themselves; over any other view an open profile keeps it going. */
setInterval(() => {
  if (SEASON_OPEN && !gdOnScreen() && document.querySelector("#modal.on .pf-season") && PAGE_SERVED() && gdPlaying(Date.now())) gdEnsure();
}, 30000);

function seasonTotalHTML(pos, rows, stats){
  const tot = Object.fromEntries(["pts", "car", "rush_yds", "rush_td", "rec", "rec_yds", "rec_td", "tgt", "pass_yds", "pass_td"]
    .map(k => [k, glSum(rows, k)]));
  return seasonRowHTML("ss-total",
    ssCell("ss-wk", t("profile.history.total")) + ssCell("ss-opp-c", t("profile.history.games", {n: rows.length}))
    + ssCell("ss-date", "") + ssCell("ss-pts", tot.pts) + ssCell("ss-line", seasonLine(pos, tot)) + stats(c => tot[c.id]));
}

function seasonHeadHTML(pos, cols){
  return seasonRowHTML("ss-head",
    ssHead("ss-wk", t("profile.history.colWeek")) + ssHead("ss-opp-c", t("profile.season.colOpp", {pos: esc(pos)}))
    + ssHead("ss-date", t("profile.season.colWhen")) + ssHead("ss-pts", t("profile.history.colPts")) + ssHead("ss-line", seasonLineHead(pos))
    + cols.map(c => ssHead("ss-stat", c.label())).join(""));
}

function seasonHTML(p, prof, repaint){
  const pos = prof ? prof.pos : p.pos, team = prof ? prof.team : p.team;
  const games = seasonGames(team);
  const rows = gamelogRows(p.slug);
  if (!Object.keys(games).length && !rows.length) return "";
  SEASON_OPEN = {p, prof};
  const log = Object.fromEntries(rows.map(r => [r.wk, r]));
  const live = seasonLive(p, team, pos, games, log, repaint);
  const cols = gamelogCols(live ? [...rows, live.row] : rows);
  const {shown, isBye} = seasonWeeks(p, rows);
  const now = Date.now();
  const stats = get => cols.map(c => ssCell("ss-stat", get(c))).join("");
  const body = [];
  let nextDone = false;
  for (const wk of shown){
    const g = games[wk], r = log[wk];
    if (!g && !r){
      if (isBye(wk)) body.push(seasonRowHTML("ss-bye", ssCell("ss-wk", wk) + ssCell("ss-opp-c", t("profile.season.bye"))));
      continue;
    }
    if (live && wk === live.wk){ body.push(seasonLiveRowHTML(g, pos, live, stats)); continue; }
    const opp = g ? seasonOppHTML(g, pos) : `<span class="ss-opp">${esc(r.opp || "—")}</span>`;
    if (r || !g || Date.parse(g.kickoff) + SCHED_GRACE_MS < now){
      const open = seasonOpens(p, r);
      body.push(seasonRowHTML("ss-played" + open.cls,
        ssCell("ss-wk", r ? weekCell(p, r) : wk) + ssCell("ss-opp-c", opp)
        + ssCell("ss-date", g ? seasonDay(g.kickoff) : "")
        + ssCell("ss-pts", r ? glNum(r.pts) : "—")
        + ssCell("ss-line", r ? seasonLine(pos, r) : t("profile.season.noStats"))
        + stats(c => r ? glNum(r[c.id]) : "—"),
        open.attrs));
      continue;
    }
    const isNext = !nextDone; nextDone = true;       // the first week still to come
    const when = Date.parse(g.kickoff) < now ? t("profile.season.live") : seasonKick(g.kickoff);
    const proj = isNext ? seasonProj(p, prof, pos, wk) : {pts: "", note: ""};
    body.push(seasonRowHTML(isNext ? "ss-next" : "ss-later",
      ssCell("ss-wk", wk) + ssCell("ss-opp-c", opp) + ssCell("ss-date", when)
      + ssCell("ss-pts", proj.pts) + ssCell("ss-line ss-when", when)
      + (proj.note ? ssCell("ss-note", proj.note) : "")));
  }
  if (rows.length) body.push(seasonTotalHTML(pos, rows, stats));
  SEASON_LAST = `<div class="pf-season" role="table" aria-label="${t("profile.season.label")}" style="--ss-n:${Math.max(1, cols.length)}">`
    + seasonHeadHTML(pos, cols) + body.join("") + `</div>`;
  return SEASON_LAST;
}

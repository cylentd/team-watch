/* ============================== LIVE: THE MATCHUP ==============================
   One game of the league on screen: both scores, then both lineups in slot order the way ESPN and
   Yahoo draw them. Each row says where his game is -- PLAYING, FINAL, or its kickoff with his
   projection -- and how he earned his points ("6/7 rec · 82 yds · 2 TD"). A row opens his profile. */

const gdNum = v => (Math.round(v * 10) / 10).toFixed(1);
const gdSigned = v => (v >= 0 ? "+" : "−") + gdNum(Math.abs(v));
/* "B. Purdy"; a defense keeps its name ("Seahawks D/ST"). */
const gdShort = (r) => r.pos === "DEF" ? r.n : r.n.replace(/^(\S)\S*\s+/, "$1. ");
const gdClock = ms => new Date(ms).toLocaleString("en-US", {weekday: "short", hour: "numeric", minute: "2-digit"});

/* Points over his projection, ESPN's way (2026-09-28, storyboard
   https://claude.ai/artifact/WxBrEw9K8CTNu8KftYvPYQ, option B). The second number carries no label:
   under the points it can only be the projection. The points go lime once he has passed it. */
function gdRightHTML(r){
  const pulse = r.sid && GD_PULSE[r.sid] !== undefined ? `<em class="up">${gdSigned(GD_PULSE[r.sid])}</em>` : "";
  const p = projFor(r), proj = `<span class="gd-proj">${p === null ? "" : gdNum(p)}</span>`;
  if (r.state === "pre_game") return `<span class="gd-pts pre">—</span>${proj}`;
  const beat = p !== null && (r.pts || 0) > p;
  return `<span class="gd-pts${beat ? " beat" : ""}">${pulse}${gdNum(r.pts || 0)}</span>${proj}`;
}

/* His game in one line: a lime LIVE and the score from his side while it is on, a lock and W/L
   once it is final, the kickoff before. The score is Sleeper's (nflnow.js gdClubScore). */
function gdGameHTML(r){
  /* A club missing from the schedule still says where its game is, without the score or opponent. */
  const g = gdGameOf(r.team);
  const opp = !g ? "" : g.home ? t("live.game.vs", {opp: esc(g.opp)}) : t("live.game.at", {opp: esc(g.opp)});
  if (r.state === "pre_game"){
    const k = g ? Date.parse(g.kickoff) : gdKickOf(r.team);
    return [k === undefined || isNaN(k) ? "" : esc(gdClock(k)), opp].filter(Boolean).join(" ");
  }
  const a = g ? gdClubScore(r.team, g.opp) : null, b = g ? gdClubScore(g.opp, r.team) : null;
  const known = a !== null && b !== null && a !== undefined && b !== undefined;
  const tail = (sc) => [sc, opp].filter(Boolean).join(" ");
  if (r.state === "in_game"){
    const sc = !known ? "" : a > b ? t("live.game.up", {a, b}) : a < b ? t("live.game.down", {a, b}) : t("live.game.tied", {a, b});
    const rest = tail(sc);
    return `<span class="gd-live">${t("live.now.live")}</span>${rest ? ` · ${rest}` : ""}`;
  }
  const sc = !known ? "" : a > b ? t("live.game.won", {a, b}) : a < b ? t("live.game.lost", {a, b}) : t("live.game.tie", {a, b});
  const rest = tail(sc);
  return `${GD_LOCK}${t("live.state.final")}${rest ? ` · ${rest}` : ""}`;
}

/* A row: the slot as a pill (locked once his game kicks off), his face, name over his game over his
   stats, points over projection. Every other row is shaded, so no rule sits between them. */
function gdRowHTML(r, bench){
  const lock = r.state === "pre_game" ? "" : GD_LOCK;
  return `<button type="button" class="gd-row ${r.state === "in_game" ? "on" : r.state === "pre_game" ? "pre" : ""}${bench ? " bn" : ""}"
    data-gdslug="${esc(r.slug)}" data-gdn="${esc(r.n)}" data-gdpos="${esc(r.pos)}" data-gdteam="${esc(r.team)}">
    <span class="gd-slot${lock ? " locked" : ""}">${lock}${esc(r.slot)}</span>
    <span class="gd-hd">${avatarHTML(r)}</span>
    <span class="gd-who"><b>${esc(r.pos === "DEF" ? r.n.replace(/\s*D\/ST$/, "") : gdShort(r))} <small>${esc(r.team)} ${esc(r.pos === "DEF" ? r.slot : r.pos)}</small></b>
      <span class="gd-game">${gdGameHTML(r)}</span>
      ${r.state === "pre_game" ? "" : `<span class="gd-stat">${r.line ? esc(r.line) : t("live.line.none")}</span>`}</span>
    <span class="gd-right">${gdRightHTML(r)}</span></button>`;
}

/* Starters, then the bench under its own line: dimmed, points shown, never in the total. */
function gdLineupHTML(side, mine){
  const bench = side.bench.length ? `<h4 class="gd-bench"><span>${t("live.bench")}</span>
      <span>${t("live.benchTotal", {n: gdNum(side.benchTotal)})}</span></h4>
    ${side.bench.map(r => gdRowHTML(r, true)).join("")}` : "";
  return `<div class="gd-lineup${mine ? " mine" : ""}">
    <h3><span>${mine ? t("live.yours") : esc(side.name)}</span><span>${gdNum(side.total)}</span></h3>
    ${side.rows.map(r => gdRowHTML(r)).join("")}${bench}</div>`;
}

/* "3 playing · 2 to play", zeros left out so it fits beside a score on a phone. */
const gdCounts = s => [s.playing ? t("live.count.playing", {n: s.playing}) : "",
  s.left ? t("live.count.left", {n: s.left}) : "", s.done && !s.playing && !s.left ? t("live.count.done", {n: s.done}) : ""]
  .filter(Boolean).join(" · ");

/* Who leads, in words: "UP 0.6" / "DOWN 9.8" in my game, "BY 0.6" (the leader bright) in anyone
   else's. Under each score, where it should finish (gdProj) and who is left. */
function gdLeadHTML(a, b, mine){
  const gap = a.total - b.total, n = gdNum(Math.abs(gap));
  if (Math.abs(gap) < 0.05) return `<span class="gd-lead even">${t("live.lead.tied")}</span>`;
  if (!mine) return `<span class="gd-lead even">${t("live.lead.by", {n})}</span>`;
  return gap > 0 ? `<span class="gd-lead up">${t("live.lead.up", {n})}</span>` : `<span class="gd-lead dn">${t("live.lead.down", {n})}</span>`;
}

function gdHeadHTML(a, b, lg){
  const lead = a.total > b.total ? a : b.total > a.total ? b : null;
  const side = (s, cls) => `<div class="gd-side ${cls}${s.id === lg.me ? " mine" : ""}${s === lead ? " lead" : ""}">
      <span>${esc(s.name)}</span><b>${gdNum(s.total)}</b>
      <small>${t("live.projFinish", {n: gdNum(gdProj(s, projFor))})} · ${gdCounts(s)}</small></div>`;
  return `<div class="gd-head">${side(a, "a")}${gdLeadHTML(a, b, a.id === lg.me)}${side(b, "b")}</div>`;
}

function gdStampHTML(){
  const now = Date.now();
  if (GD_ERR && GD_STATS) return `<p class="gd-stamp warn">${t("live.stamp.stale", {when: esc(gdClock(GD_AT))})}</p>`;
  if (GD_ERR) return `<p class="gd-stamp warn">${esc(GD_ERR)}</p>`;
  if (!GD_STATS) return `<p class="gd-stamp">${t("live.stamp.loading")}</p>`;
  const at = new Date(GD_AT).toLocaleTimeString("en-US", {hour: "numeric", minute: "2-digit", second: "2-digit"});
  if (gdPlaying(now)) return `<p class="gd-stamp on">${t("live.stamp.live", {at: esc(at)})}</p>`;
  const next = gdNextKick(now);
  return `<p class="gd-stamp">${next === undefined ? t("live.stamp.done", {at: esc(at)})
    : t("live.stamp.next", {at: esc(at), when: esc(gdClock(next))})}</p>`;
}

function gdBoardHTML(){
  const lg = gdLeague();
  if (!lg) return `<div class="state-empty"><div><b>—</b><span>${t("live.none")}</span></div></div>`;
  const stats = GD_STATS && GD_STATS.stats, states = (GD_STATS && GD_STATS.games) || {};
  const sides = Object.fromEntries(Object.keys(lg.teams).map(id => [id, gdSide(lg, id, stats, states)]));
  const game = gdGame(lg);
  let [a, b] = game ? [sides[game[0]], sides[game[1]]] : [];
  if (b && b.id === lg.me) [a, b] = [b, a];
  return gdNowHTML(lg) + gdLeaguesHTML(lg)
    + (a && b ? `<div class="gd-match">${gdHeadHTML(a, b, lg)}
        <div class="gd-lineups">${gdLineupHTML(a, a.id === lg.me)}${gdLineupHTML(b, false)}</div></div>` : "")
    + `<div class="gd-league">${gdGamesHTML(lg, sides, game)}${gdLadderHTML(lg, sides)}</div>`
    + gdStampHTML();
}

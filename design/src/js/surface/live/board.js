/* ============================== LIVE: THE MATCHUP ==============================
   One game of the league on screen: both scores, then both lineups in slot order the way ESPN and
   Yahoo draw them. Each row says where his game is -- PLAYING, FINAL, or its kickoff with his
   projection -- and how he earned his points ("6/7 rec · 82 yds · 2 TD"). A row opens his profile. */

const gdNum = v => (Math.round(v * 10) / 10).toFixed(1);
const gdSigned = v => (v >= 0 ? "+" : "−") + gdNum(Math.abs(v));
/* "B. Purdy"; a defense keeps its name ("Seahawks D/ST"). */
const gdShort = (r) => r.pos === "DEF" ? r.n : r.n.replace(/^(\S)\S*\s+/, "$1. ");
const gdClock = ms => new Date(ms).toLocaleString("en-US", {weekday: "short", hour: "numeric", minute: "2-digit"});

function gdRightHTML(r){
  const pulse = r.sid && GD_PULSE[r.sid] !== undefined ? `<em class="up">${gdSigned(GD_PULSE[r.sid])}</em>` : "";
  if (r.state === "pre_game"){
    const p = projFor(r);
    return `<span class="gd-pts pre">${p === null ? "—" : gdNum(p)}</span><span class="gd-st pre">${t("live.st.proj")}</span>`;
  }
  if (r.state === "in_game"){
    return `<span class="gd-pts">${pulse}${gdNum(r.pts || 0)}</span><span class="gd-st on">${t("live.st.playing")}</span>`;
  }
  const p = projFor(r), d = p === null ? "" : `<b class="${r.pts >= p ? "up" : "dn"}">${gdSigned((r.pts || 0) - p)}</b>`;
  return `<span class="gd-pts">${pulse}${gdNum(r.pts || 0)}</span><span class="gd-st">${t("live.st.final")} ${d}</span>`;
}

function gdMetaHTML(r){
  if (r.state !== "pre_game") return r.line ? esc(r.line) : t("live.line.none");
  const k = gdKickOf(r.team);
  return k === undefined ? "" : t("live.kick", {when: esc(gdClock(k))});
}

function gdRowHTML(r, bench){
  return `<button type="button" class="gd-row ${r.state === "in_game" ? "on" : r.state === "pre_game" ? "pre" : ""}${bench ? " bn" : ""}"
    data-gdslug="${esc(r.slug)}" data-gdn="${esc(r.n)}" data-gdpos="${esc(r.pos)}" data-gdteam="${esc(r.team)}">
    <span class="gd-slot">${esc(r.slot)}</span>
    <span class="gd-hd">${avatarHTML(r)}</span>
    <span class="gd-who"><b>${esc(gdShort(r))} <small>${esc(r.team)}</small></b><span>${gdMetaHTML(r)}</span></span>
    <span class="gd-right">${gdRightHTML(r)}</span></button>`;
}

/* Starters, then the bench under its own line: dimmed, points shown, never in the total. */
function gdLineupHTML(side, mine){
  const bench = side.bench.length ? `<h4 class="gd-bench"><span>${t("live.bench")}</span>
      <span>${t("live.benchTotal", {n: gdNum(side.benchTotal)})}</span></h4>
    ${side.bench.map(r => gdRowHTML(r, true)).join("")}` : "";
  return `<div class="gd-lineup${mine ? " mine" : ""}">
    <h3><span>${mine ? t("live.yours") : esc(side.name)}</span><span>${gdNum(side.total)}</span></h3>
    ${side.rows.map(gdRowHTML).join("")}${bench}</div>`;
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
  return gdLeaguesHTML(lg)
    + (a && b ? `<div class="gd-match">${gdHeadHTML(a, b, lg)}
        <div class="gd-lineups">${gdLineupHTML(a, a.id === lg.me)}${gdLineupHTML(b, false)}</div></div>` : "")
    + `<div class="gd-league">${gdGamesHTML(lg, sides, game)}${gdLadderHTML(lg, sides)}</div>`
    + gdStampHTML();
}

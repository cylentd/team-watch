/* ============================== LIVE: THE MATCHUP ==============================
   One game of the league on screen: both scores, the league median under them, then both lineups
   mirrored slot by slot (mirror.js). The tabs above it (tabs.js) pick this or the Games, TDs and
   League views; this file draws the Matchup one and assembles the page. */

const gdNum = v => (Math.round(v * 10) / 10).toFixed(1);
const gdSigned = v => (v >= 0 ? "+" : "−") + gdNum(Math.abs(v));
/* "B. Purdy"; a defense keeps its name ("Seahawks D/ST"). */
const gdShort = (r) => r.pos === "DEF" ? r.n : r.n.replace(/^(\S)\S*\s+/, "$1. ");
const gdClock = ms => new Date(ms).toLocaleString("en-US", {weekday: "short", hour: "numeric", minute: "2-digit"});

/* Points over his projection, ESPN's way (2026-09-28, storyboard
   https://claude.ai/artifact/WxBrEw9K8CTNu8KftYvPYQ, option B). The second number carries no label:
   under the points it can only be the projection. Lime points mean one thing, his game is on (David,
   2026-09-29: lime for "beat his projection" read as "active"). A small flame beside the points
   means he smashed it, by the Digest's own "Smashed" margin, the moment his live points pass it
   (David, 2026-09-29: no ring on the face, no flame for merely beating it). */
const GD_FLAME = `<path class="o" d="M12 1.5c.7 3.4 3.6 5 5 7.9 1.5 3 1 6.8-1.5 9.1A6.6 6.6 0 0 1 5.3 15.6c-.3-2.4.7-4.4 2.2-5.8.1 1.8.9 2.8 2 3.3-.8-3.7.4-8 2.5-11.6z"/>
  <path class="i" d="M12.3 11.2c.5 1.6 2.1 2.6 2.4 4.3a3 3 0 0 1-5.9 1.1c-.2-1.3.4-2.4 1.2-3.1.1.8.5 1.2 1 1.4-.2-1.4.4-2.7 1.3-3.7z"/>`;
/* The margin the Digest calls Smashed, from ff-jarvis (weekly_digest_schema.SMASH_MIN, carried out
   as rules.smashed.min); without it nobody gets the flame, never a guessed number. */
const gdSmashMin = () => {
  const m = typeof LIVE_DIGEST !== "undefined" && LIVE_DIGEST && ((LIVE_DIGEST.rules || {}).smashed || {}).min;
  return typeof m === "number" ? m : null;
};
function gdSmashed(r){
  const p = projFor(r), m = gdSmashMin();
  return r.state !== "pre_game" && p !== null && m !== null && (r.pts || 0) - p >= m;
}

/* "3 playing · 2 to play", zeros left out so it fits beside a score on a phone. */
const gdCounts = s => [s.playing ? t("live.count.playing", {n: s.playing}) : "",
  s.left ? t("live.count.left", {n: s.left}) : "", s.done && !s.playing && !s.left ? t("live.count.done", {n: s.done}) : ""]
  .filter(Boolean).join(" · ");

/* Who leads, in words: "UP 0.6" / "DOWN 9.8" in the reader's own game, "BY 0.6" (the leader bright)
   in anyone else's, and in every game while the reader has no team in the league (gdMine). Under
   each score, where it should finish (gdProj) and who is left. */
function gdLeadHTML(a, b, mine){
  const gap = a.total - b.total, n = gdNum(Math.abs(gap));
  if (Math.abs(gap) < 0.05) return `<span class="gd-lead even">${t("live.lead.tied")}</span>`;
  if (!mine) return `<span class="gd-lead even">${t("live.lead.by", {n})}</span>`;
  return gap > 0 ? `<span class="gd-lead up">${t("live.lead.up", {n})}</span>` : `<span class="gd-lead dn">${t("live.lead.down", {n})}</span>`;
}

function gdHeadHTML(a, b, lg){
  const lead = a.total > b.total ? a : b.total > a.total ? b : null, mine = gdMine(lg);
  const side = (s, cls) => `<div class="gd-side ${cls}${mine && s.id === mine ? " mine" : ""}${s === lead ? " lead" : ""}">
      <span>${esc(s.name)}</span><b>${gdNum(s.total)}</b>
      <small>${t("live.projFinish", {n: gdNum(gdProj(s, projFor))})} · ${gdCounts(s)}</small></div>`;
  return `<div class="gd-head">${side(a, "a")}${gdLeadHTML(a, b, !!mine && a.id === mine)}${side(b, "b")}</div>`;
}

/* Where the reader stands against the league's median, under the score: "League median 101.7 · you
   +3.3", green above it, red below. Only a league that pays the top half draws it; without a team
   of theirs in the league it is the median alone, in the neutral colour. */
function gdMedianHTML(lg, sides){
  if (!lg.median) return "";
  const {median} = gdLadder(Object.values(sides)), mine = gdMine(lg), me = mine ? sides[mine] : null;
  const you = me ? ` · ${t("live.med.you", {d: gdSigned(me.total - median)})}` : "";
  return `<p class="gd-medline${me ? (me.total < median ? " dn" : " up") : ""}">${t("live.med.line", {n: gdNum(median)})}${you}</p>`;
}

/* One line above the score while the reader has no team in this league: it opens My teams, where
   they pick (teamswitch.js tsPickFor). Never a nag: it is a line, not a sheet. */
const gdPickHTML = lg => `<button type="button" class="gd-pick" data-gdpick="${esc(lg.key)}">${t("live.pick")}</button>`;

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

/* The Matchup tab: the game on screen (the reader's unless another was tapped in the League tab; the
   league's first when they have no team in it), its score and the median under it, then the mirrored
   lineups, the reader's on the left. */
function gdMatchupHTML(lg, sides){
  const game = gdGame(lg), mine = gdMine(lg);
  let [a, b] = game ? [sides[game[0]], sides[game[1]]] : [];
  if (b && mine && b.id === mine) [a, b] = [b, a];
  if (!(a && b)) return "";
  return `<div class="gd-match">${mine ? "" : gdPickHTML(lg)}${gdHeadHTML(a, b, lg)}${gdMedianHTML(lg, sides)}${gdMirrorHTML(a, b, lg)}</div>`;
}

/* The League tab: every matchup as one row, then the ranking. */
const gdLeagueTabHTML = (lg, sides) => `<div class="gd-league">${gdGamesHTML(lg, sides, gdGame(lg))}${gdLadderHTML(lg, sides)}</div>`;

/* The TDs tab is another file's (surface/live/tds.js); this one only hosts it. */
const gdTdsTabHTML = lg => typeof gdTdsHTML === "function" ? gdTdsHTML(lg)
  : `<div class="state-empty"><div><b>—</b><span>${t("live.tab.tdsEmpty")}</span></div></div>`;

function gdBoardHTML(){
  const lg = gdLeague();
  if (!lg) return `<div class="state-empty"><div><b>—</b><span>${t("live.none")}</span></div></div>`;
  const stats = GD_STATS && GD_STATS.stats, states = (GD_STATS && GD_STATS.games) || {};
  const sides = Object.fromEntries(Object.keys(lg.teams).map(id => [id, gdSide(lg, id, stats, states)]));
  const tab = gdTab();
  const body = tab === "games" ? gdGamesTabHTML(lg) : tab === "tds" ? gdTdsTabHTML(lg)
    : tab === "league" ? gdLeagueTabHTML(lg, sides) : gdMatchupHTML(lg, sides);
  /* The league chips pick a Yahoo or ESPN league: Games and TDs are NFL-wide, so they draw none. */
  const chips = tab === "matchup" || tab === "league" ? gdLeaguesHTML(lg) : "";
  return gdTabsHTML() + chips + body + gdStampHTML();
}

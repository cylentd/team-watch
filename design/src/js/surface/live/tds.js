/* ============================== LIVE: THE TDS TAB ==============================
   Touchdowns tracked with no input (2026-10-04, storyboard https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV).
   David builds TD slips from the top of Parlay's TD chances and will not type them in, so the tab
   follows that same list and says who has scored, who still can, and who missed.

   Scored   every player in GD_STATS.lead (league-wide, api/stats.py `lead`) with a rushing or
            receiving TD: an anytime TD is one of those two, a passing TD is not one. Most TDs first,
            then points.
   Alive    the top TD_ALIVE_N of the TD chances Parlay ranks (PROPS rows with mkt "TD", the model's
            P(score), the order Build's "Model" sort uses), minus whoever has scored. A player is
            matched to Sleeper's row by name and club (gdCodes covers WAS/WSH, JAX/JAC). Each is
              live    his game is on and he has no TD yet (lime, the game clock)
              later   his game has not kicked off (the kickoff)
              missed  his game is final and he has none (red, at the bottom)

   The league argument is unused: both lists are league-wide and the page is public, so no roster
   is read. A row opens the player's profile. */

const TD_ALIVE_N = 15;
const tdCount = s => ((s || {}).rush_td || 0) + ((s || {}).rec_td || 0);

/* The lead rows with a rushing or receiving TD, most first. */
function tdScoredRows(){
  const lead = (GD_STATS && GD_STATS.lead) || {};
  return Object.entries(lead).filter(([, v]) => tdCount(v.s) > 0).map(([id, v]) => ({id, ...v}))
    .sort((a, b) => tdCount(b.s) - tdCount(a.s) || (b.pts || 0) - (a.pts || 0));
}

/* The board's top TD_ALIVE_N, then the ones who have not scored. */
function tdAliveRows(scored){
  const seen = new Set(), board = [];
  /* The sample rows are no TD chances: without the live market there is no board. */
  const props = typeof LIVE_MARKET !== "undefined" && LIVE_MARKET ? PROPS : [];
  for (const p of props.filter(x => x.mkt === "TD" && x.slug).sort(SORTS.model)){
    if (seen.has(p.slug)) continue;
    seen.add(p.slug);
    board.push(p);
    if (board.length >= TD_ALIVE_N) break;
  }
  return board.filter(p => !scored.some(v => slugOf(v.n || "") === slugOf(p.n) && gdSameClub(p.team || "", v.team)));
}

/* One row, whichever list it is in. cls is the game's state: live, later or missed; a row from the
   Scored list (o.scored) has already scored, so its game being over is no miss: it gets `scored`
   (green line, grey Final) instead of `missed`. */
function tdRowHTML(o){
  const c = gdClockOf(o.team);
  const cls = c.state === "in" ? "live" : o.scored ? "scored" : c.state === "post" ? "missed" : "later";
  const line = o.line || (cls === "live" ? t("live.tds.none") : cls === "missed" ? t("live.tds.missed") : "");
  const chance = o.chance === null ? "" : `<small>${t("live.tds.chance", {n: o.chance})}</small>`;
  return `<li><button type="button" class="td-row ${cls}${o.scored && cls !== "scored" ? " scored" : ""}" data-tdslug="${esc(o.slug)}" data-tdn="${esc(o.n)}"
      data-tdpos="${esc(o.pos)}" data-tdteam="${esc(o.team)}">
    <span class="td-pos" data-pos="${esc(o.pos)}">${esc(o.pos)}</span>
    <span class="td-who"><b>${esc(nameInitial(o.n))} <small>${esc(o.team)}</small></b>${line ? `<span class="td-line">${esc(line)}</span>` : ""}</span>
    <span class="td-right"><span class="td-clock">${esc(c.label)}</span>${chance}</span></button></li>`;
}

/* "2 rush TD", "1 rush TD · 1 rec TD". */
function tdScoredLine(s){
  return [s.rush_td ? t("live.tds.rush", {n: s.rush_td}) : "", s.rec_td ? t("live.tds.rec", {n: s.rec_td}) : ""].filter(Boolean).join(" · ");
}

function gdTdsHTML(lg){
  if (!GD_STATS || !GD_STATS.lead) return `<div class="gd-card td-card"><p class="td-empty">${t("live.tds.loading")}</p></div>`;
  const scored = tdScoredRows(), alive = tdAliveRows(scored);
  const aliveRows = alive.map(p => ({n: p.n, slug: p.slug, pos: p.pos, team: p.team || "", chance: tdChanceFor(p)}));
  /* A missed game sinks; the board's order holds within each state. */
  const order = o => gdClockOf(o.team).state === "post" ? 1 : 0;
  aliveRows.sort((a, b) => order(a) - order(b));
  const scoredList = scored.length
    ? `<ul class="td-list">${scored.map(v => tdRowHTML({n: v.n, slug: slugOf(v.n || ""), pos: v.pos, team: v.team, chance: null, line: tdScoredLine(v.s), scored: true})).join("")}</ul>`
    : `<p class="td-empty">${t("live.tds.noneYet")}</p>`;
  const aliveList = aliveRows.length
    ? `<ul class="td-list">${aliveRows.map(tdRowHTML).join("")}</ul>`
    : `<p class="td-empty">${t("live.tds.noBoard")}</p>`;
  return `<section class="gd-card td-card"><h3 class="td-head"><span>${t("live.tds.scored")}</span><span>${t("live.tds.count", {n: scored.length})}</span></h3>${scoredList}</section>
    <section class="gd-card td-card"><h3 class="td-head"><span>${t("live.tds.alive")}</span><span>${t("live.tds.byChance")}</span></h3>${aliveList}</section>`;
}

/* A row opens the player's profile, the way the matchup's rows do. */
function wireTds(host){
  host.querySelectorAll("[data-tdslug]").forEach(b => b.addEventListener("click", () => {
    openProfile({n: b.dataset.tdn, pos: b.dataset.tdpos, team: b.dataset.tdteam, slug: b.dataset.tdslug}, b);
  }));
}

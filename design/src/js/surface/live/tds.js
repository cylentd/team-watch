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

   Two views and four filters (2026-10-05, David: "group by game + filters. I also like the current list
   as well."). Feed is the list above; By game is one card per game (header: the two clubs, the score
   and the clock, a tap opens the game sheet; rows: its scorers). The view is `tw-live-tds` in
   localStorage; the chips (Mine, Pass, Rush, Rec) are memory only and clear on every visit. One chip
   row holds them all, By game last (a toggle, pressed = By game; 2026-10-05, option 2A). Chips
   narrow both views. Rush/Rec/Pass pick the TD types (none on = rush and rec, the anytime TDs; Pass is
   the only way a passer appears); Mine keeps the players of the teams the reader picked or follows
   (mine.js), never David's. Still alive has no TD type, so a type chip hides it; Mine narrows it.
   Sleeper's stats carry no scoring time: By game orders games live first, then the latest kickoff.

   The league argument is unused: both lists are league-wide and the page is public, so no roster
   is read but the reader's own. A row opens the player's profile.

   Feed also draws a TD clips reel above the Scored card (tdclips.js), of the scorers the chips keep. */

const TD_ALIVE_N = 15;
const TD_MODE_KEY = "tw-live-tds";
const TD_MODES = ["feed", "game"];
const TD_CHIPS = ["mine", "pass", "rush", "rec"];
let TD_MODE_MEM = null;    /* the view when localStorage will not answer */
let TD_ON = {};            /* the chips that are on: memory only, none on every visit */

function tdMode(){
  let v = TD_MODE_MEM;
  try { v = localStorage.getItem(TD_MODE_KEY) || v; } catch (e) {}
  return TD_MODES.includes(v) ? v : "feed";
}
function tdSetMode(v){
  if (!TD_MODES.includes(v)) return;
  TD_MODE_MEM = v;
  try { localStorage.setItem(TD_MODE_KEY, v); } catch (e) {}
}

/* The TD types the chips ask for; none on is the anytime TDs. */
function tdKinds(){
  const on = ["rush", "rec", "pass"].filter(k => TD_ON[k]);
  return on.length ? on : ["rush", "rec"];
}
const tdCount = (s, kinds = ["rush", "rec"]) => kinds.reduce((n, k) => n + ((s || {})[k + "_td"] || 0), 0);

/* Sleeper ids and slugs of every player on the reader's teams, in every league. */
function tdMineSet(){
  const ids = new Set();
  for (const lg of GD.leagues) for (const r of gdMineLineup(lg)){ if (r.sid) ids.add(String(r.sid)); if (r.slug) ids.add(r.slug); }
  return ids;
}

/* The lead rows with a TD of the kinds asked, most first; with `mine`, only the reader's players. */
function tdScoredRows(kinds, mine){
  const lead = (GD_STATS && GD_STATS.lead) || {};
  return Object.entries(lead).filter(([id, v]) => tdCount(v.s, kinds) > 0 && (!mine || mine.has(id) || mine.has(slugOf(v.n || ""))))
    .map(([id, v]) => ({id, ...v}))
    .sort((a, b) => tdCount(b.s, kinds) - tdCount(a.s, kinds) || (b.pts || 0) - (a.pts || 0));
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
   (green line, grey Final) instead of `missed`. In a game's card (o.game) the header holds the clock
   and the club, so the row holds neither, and no row is lime. */
function tdRowHTML(o){
  const c = gdClockOf(o.team);
  const cls = o.game ? "scored" : c.state === "in" ? "live" : o.scored ? "scored" : c.state === "post" ? "missed" : "later";
  const line = o.line || (cls === "live" ? t("live.tds.none") : cls === "missed" ? t("live.tds.missed") : "");
  const chance = o.chance === null ? "" : `<small>${t("live.tds.chance", {n: o.chance})}</small>`;
  const club = o.game ? "" : ` <small>${esc(o.team)}</small>`;
  return `<li><button type="button" class="td-row ${cls}${o.scored && cls !== "scored" ? " scored" : ""}${o.game ? " in-game" : ""}" data-tdslug="${esc(o.slug)}" data-tdn="${esc(o.n)}"
      data-tdpos="${esc(o.pos)}" data-tdteam="${esc(o.team)}">
    <span class="td-pos" data-pos="${esc(o.pos)}">${esc(o.pos)}</span>
    <span class="td-who"><b>${esc(nameInitial(o.n))}${club}</b>${line ? `<span class="td-line">${esc(line)}</span>` : ""}</span>
    ${o.game ? "" : `<span class="td-right"><span class="td-clock">${esc(c.label)}</span>${chance}</span>`}</button></li>`;
}

/* "2 rush TD", "1 rush TD · 1 rec TD", "3 pass TD" (only the kinds asked). */
function tdScoredLine(s, kinds = ["rush", "rec"]){
  const part = {rush: n => t("live.tds.rush", {n}), rec: n => t("live.tds.rec", {n}), pass: n => t("live.tds.pass", {n})};
  return ["rush", "rec", "pass"].filter(k => kinds.includes(k) && s[k + "_td"]).map(k => part[k](s[k + "_td"])).join(" · ");
}

const tdScoredRow = (v, kinds, game) =>
  tdRowHTML({n: v.n, slug: slugOf(v.n || ""), pos: v.pos, team: v.team, chance: null, line: tdScoredLine(v.s, kinds), scored: true, game});

/* The week's game a club plays in, or undefined. */
const tdGameOf = club => gdWeekGames().find(g => gdSameClub(g.home, club) || gdSameClub(g.away, club));

/* One card per game: the two clubs, the score and the clock (a tap opens the game sheet), then its
   scorers. Live games first, then the latest kickoff first. A club the schedule lacks gets a card of
   its own, headed by the club. */
function tdGameCardsHTML(rows, kinds){
  const groups = new Map();
  for (const v of rows){
    const g = tdGameOf(v.team), k = g ? gdNflKey(g) : v.team;
    if (!groups.has(k)) groups.set(k, {g, club: v.team, rows: []});
    groups.get(k).rows.push(v);
  }
  const rank = c => c.state === "in" ? 0 : 1;
  const cards = [...groups.values()].map(x => ({...x, c: gdClockOf(x.g ? x.g.home : x.club), at: x.g ? Date.parse(x.g.kickoff) || 0 : 0}))
    .sort((a, b) => rank(a.c) - rank(b.c) || b.at - a.at);
  return cards.map(({g, club, rows, c}) => {
    let head = `<span class="td-gt">${esc(club)}</span>`;
    if (g){
      const a = gdClubScore(g.away, g.home), h = gdClubScore(g.home, g.away), on = c.state !== "pre" && a !== null && h !== null;
      const side = (code, s, o) => `<span class="td-gt${on && s < o ? " behind" : ""}">${esc(code)} <b>${on ? s : "—"}</b></span>`;
      head = `${side(g.away, a, h)}${side(g.home, h, a)}<span class="td-gclock ${c.state}">${esc(c.label)}</span>`;
    }
    const tag = g ? `button type="button" class="td-gh" data-gdnfl="${esc(gdNflKey(g))}" aria-haspopup="dialog"` : `div class="td-gh"`;
    return `<section class="gd-card td-card td-gcard"><h3 class="td-head"><${tag}>${head}</${g ? "button" : "div"}></h3>
      <ul class="td-list">${rows.map(v => tdScoredRow(v, kinds, true)).join("")}</ul></section>`;
  }).join("");
}

/* One chip row (2026-10-05, storyboard option 2A): the four filters, a divider, then By game, a toggle
   for the view (pressed = By game, not pressed = Feed). The row scrolls sideways when it does not fit.
   Every copy key is spelled out (assemble.py --check). */
function tdControlsHTML(){
  const name = {mine: t("live.tds.fMine"), pass: t("live.tds.fPass"), rush: t("live.tds.fRush"), rec: t("live.tds.fRec")};
  const chips = TD_CHIPS.map(k => `<button type="button" class="chip" data-tdchip="${k}" aria-pressed="${!!TD_ON[k]}">${name[k]}</button>`).join("");
  const byGame = `<button type="button" class="chip td-bygame" data-tdgame aria-pressed="${tdMode() === "game"}">${t("live.tds.byGame")}</button>`;
  return `<div class="td-filters" role="group" aria-label="${t("live.tds.filters")}">${chips}<span class="td-sep" aria-hidden="true"></span>${byGame}</div>`;
}

/* The one line a filter that finds nothing says. */
const tdNoneLine = () => TD_ON.mine && !tdMineSet().size ? t("live.tds.pickTeam") : t("live.tds.noMatch");

/* What the chips leave of the Scored list: `all` is everyone who has scored, `scored` what the chips keep. */
function tdFilter(){
  const kinds = tdKinds(), mine = TD_ON.mine ? tdMineSet() : null, filtered = TD_CHIPS.some(k => TD_ON[k]);
  const all = tdScoredRows();
  return {kinds, mine, filtered, all, scored: filtered ? tdScoredRows(kinds, mine) : all};
}

function gdTdsHTML(lg){
  if (!GD_STATS || !GD_STATS.lead) return `<div class="gd-card td-card"><p class="td-empty">${t("live.tds.loading")}</p></div>`;
  const {kinds, mine, filtered, all, scored} = tdFilter();
  const empty = () => `<p class="td-empty">${filtered ? tdNoneLine() : t("live.tds.noneYet")}</p>`;
  if (tdMode() === "game")
    return tdControlsHTML() + (scored.length ? tdGameCardsHTML(scored, kinds) : `<section class="gd-card td-card">${empty()}</section>`);
  /* Still alive has no TD type: a type chip hides it, Mine narrows it, and it never repeats the empty line. */
  const alive = ["pass", "rush", "rec"].some(k => TD_ON[k]) ? [] : tdAliveRows(all).filter(p => !mine || mine.has(p.slug));
  const aliveRows = alive.map(p => ({n: p.n, slug: p.slug, pos: p.pos, team: p.team || "", chance: tdChanceFor(p)}));
  /* A missed game sinks; the board's order holds within each state. */
  const order = o => gdClockOf(o.team).state === "post" ? 1 : 0;
  aliveRows.sort((a, b) => order(a) - order(b));
  const scoredList = scored.length ? `<ul class="td-list">${scored.map(v => tdScoredRow(v, kinds, false)).join("")}</ul>` : empty();
  const aliveCard = aliveRows.length ? `<ul class="td-list">${aliveRows.map(tdRowHTML).join("")}</ul>` : filtered ? "" : `<p class="td-empty">${t("live.tds.noBoard")}</p>`;
  return tdControlsHTML() + tdrHTML(tdrModel(scored, kinds)) + `<section class="gd-card td-card"><h3 class="td-head"><span>${t("live.tds.scored")}</span><span>${t("live.tds.count", {n: scored.length})}</span></h3>${scoredList}</section>`
    + (aliveCard ? `<section class="gd-card td-card"><h3 class="td-head"><span>${t("live.tds.alive")}</span><span>${t("live.tds.byChance")}</span></h3>${aliveCard}</section>` : "");
}

/* A row opens the player's profile, the way the matchup's rows do; the view and the chips repaint in
   place and give the focus back to the control that was pressed. */
function wireTds(host){
  host.querySelectorAll("[data-tdslug]").forEach(b => b.addEventListener("click", () => {
    openProfile({n: b.dataset.tdn, pos: b.dataset.tdpos, team: b.dataset.tdteam, slug: b.dataset.tdslug}, b);
  }));
  const again = sel => { paintLive(); document.querySelector(sel)?.focus(); };
  host.querySelectorAll("[data-tdgame]").forEach(b => b.addEventListener("click", () => {
    tdSetMode(tdMode() === "game" ? "feed" : "game"); again("[data-tdgame]");
  }));
  host.querySelectorAll("[data-tdchip]").forEach(b => b.addEventListener("click", () => {
    TD_ON[b.dataset.tdchip] = !TD_ON[b.dataset.tdchip]; again(`[data-tdchip="${b.dataset.tdchip}"]`);
  }));
  /* The TD clips reel (tdclips.js) is Feed's; fresh clips are asked for here, when the tab paints. */
  if (GD_STATS && GD_STATS.lead && tdMode() === "feed"){ const f = tdFilter(); tdrWire(host, tdrModel(f.scored, f.kinds)); }
  tdcEnsure();
}

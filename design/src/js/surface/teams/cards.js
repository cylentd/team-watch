/* The roster as trading cards (2026-09-25), the Cards half of the Sheet / Cards switch. A card's
   tier is this week's projected rank at his position (LIVE_PROJECTIONS rank/of, design/projections.py),
   never a hand pick: #1 holo, #2-5 signed, #6-8 glitter, #9-12 gold, #13-24 silver, the rest plain
   (bands below). The back prints the rank in words ("#7 RB"), never a tier code. A kicker and a
   defense have no projection, so no tier: they are support cards whose art is the matchup. Tap flips
   a card; its back carries the trend line the front leaves out and the way into the profile. */
/* Tiers widened 2026-09-25, still earned by rank alone, never by being a roster's best: #1 is its
   own tier ("one": a moving holographic frame and foil), #2-5 signed, #6-8 glitter, #9-12 gold.
   Only #1 was signed before, and most rosters never hold one. A roster with nobody in the top
   five gets no signature card: that is the news, not a gap to fill. */
function cardTier(rank){
  if (!rank) return "c";
  return rank === 1 ? "one" : rank <= 5 ? "sig" : rank <= 8 ? "sr" : rank <= 12 ? "ur" : rank <= 24 ? "r" : "c";
}
function cardRank(p){
  if (typeof LIVE_PROJECTIONS === "undefined" || !LIVE_PROJECTIONS) return null;
  const r = LIVE_PROJECTIONS.players[p.slug];
  return r && r.rank ? r.rank : null;
}

/* This week's game for a team, from the schedule: the next kickoff not more than four hours gone.
   The schedule spells two clubs its own way (alias: LA -> LAR, WAS -> WSH), and so do the lines. */
const cardCode = team => (typeof LIVE_SCHEDULE !== "undefined" && LIVE_SCHEDULE && LIVE_SCHEDULE.alias || {})[team] || team;
function cardGame(team){
  if (typeof LIVE_SCHEDULE === "undefined" || !LIVE_SCHEDULE) return null;
  const code = cardCode(team), now = Date.now() - 4 * 3600e3;
  const g = LIVE_SCHEDULE.games
    .filter(x => (x.home === code || x.away === code) && Date.parse(x.kickoff) > now)
    .sort((a, b) => Date.parse(a.kickoff) - Date.parse(b.kickoff))[0];
  return g ? {opp: g.home === code ? g.away : g.home, home: g.home === code, venue: g.home} : null;
}
/* A row of a team-keyed block under either spelling of the club. */
function cardTeamRow(block, team){
  if (!block) return null;
  const alias = (typeof LIVE_SCHEDULE !== "undefined" && LIVE_SCHEDULE && LIVE_SCHEDULE.alias) || {};
  const plain = Object.keys(alias).find(k => alias[k] === team);
  return block.teams[team] || block.teams[alias[team]] || (plain ? block.teams[plain] : null) || null;
}
const cardLines = team => cardTeamRow(typeof LIVE_LINES !== "undefined" ? LIVE_LINES : null, team);
const cardMatchup = (team, g) => g ? `${team} ${g.home ? "vs" : "@"} ${g.opp}` : team;

/* The front says four things: slot, points, who, and the game. The rank is the back's first line
   and the frame's colour, so the front no longer prints it (2026-09-25: a fifth line, and the
   position a second time, is what made a phone row of three read as crowded). */
function cardFront(p, tier, g){
  const pts = projFor(p);
  const sig = tier === "sig" || tier === "one" ? `<span class="tc-sig">${esc(p.n)}</span>` : "";
  // Behind the photo: glitter (#2-3), the pearl etch (signature), or the #1's holo foil and glitter.
  const foil = {sr: `<i class="tc-spark"></i>`, sig: `<i class="tc-etch"></i>`, one: `<i class="tc-holo"></i><i class="tc-spark"></i>`}[tier] || "";
  return `<div class="tc-face tc-front">
      <div class="tc-top"><span>${esc(p.start ? slotLabel(p.slot) : p.pos)}</span><span class="tc-num">${pts === null ? "—" : pts.toFixed(1)}</span></div>
      <div class="tc-art pos-${esc(p.pos)}">${foil}
        <div class="head">${headHTML(p)}</div>${sig}</div>
      <div class="tc-name">${esc(nameInitial(p.n))}</div>
      <div class="tc-meta">${esc(cardMatchup(p.team, g))}</div>
    </div>`;
}

/* The back holds only what the front does not: why the tier, and his role as a stat sheet. Three
   usage stats for his position (WV_PROOF, the waiver card's choice, so the two never disagree),
   each with this week's value, an arrow against last week, and a bar that is his percentile at
   the position that week (the Grid's own `p`). The snap line it replaced was two or three points
   with no numbers. The week is his latest game, not the league's (a Thursday or Monday game can
   leave him a week behind), and the back says which. A player the Grid has no row for keeps the line. */
function cardStats(p){
  if (typeof USAGE === "undefined" || !USAGE || !WV_PROOF[p.pos] || !p.slug) return null;
  const mine = USAGE.rows.filter(x => x.slug === p.slug).sort((a, b) => a.wk - b.wk);
  const row = mine[mine.length - 1], before = mine[mine.length - 2];
  const cols = WV_PROOF[p.pos].map(want => wvCol(p.pos, want)).filter(Boolean);
  if (!row || !cols.length) return null;
  const val = (r, id) => r && r.v[id] !== undefined ? r.v[id] : null;
  const html = `<div class="bk-stats">${cols.map(c => {
    const now = val(row, c.id);
    const pct = row.p && typeof row.p[c.id] === "number" ? row.p[c.id] : null;
    const band = pct === null ? "" : pct >= 67 ? "hi" : pct >= 34 ? "mid" : "lo";
    const tip = pct === null ? esc(c.label) : t("teams.card.pctTip", {stat: esc(c.label), p: pct, pos: esc(p.pos)});
    return `<div class="bk-stat ${band}" title="${tip}">
        <span class="bk-l">${esc(c.label)}</span><b>${usageFmt(now, c.fmt)}${wvTrendHTML(now, before ? val(before, c.id) : null)}</b>
        <span class="bk-bar"><i style="--p:${pct === null ? 0 : pct / 100}"></i></span></div>`;
  }).join("")}</div>`;
  return {html, wk: row.wk};
}
function cardBack(p, rank, teamKey, i){
  const stats = cardStats(p);
  return `<div class="tc-face tc-back">
      <div class="bk-why"><b>${rank ? t("teams.card.rank", {n: rank, pos: esc(p.pos)}) : esc(p.pos)}</b>${stats ? t("teams.card.roleWeek", {wk: stats.wk}) : t("teams.card.thisWeek")}</div>
      ${stats ? stats.html : `<div class="bk-l">${t("teams.card.snap")}</div><div class="bk-sp">${sparkHTML(p.trend, 110, 28)}</div>`}
      <button class="bk-open" type="button" data-cteam="${teamKey}" data-ci="${i}">${t("teams.card.profile")}</button>
    </div>`;
}

/* Support cards. The kicker's art is his venue: turf, the posts, the roof and the wind (today's
   forecast at the home stadium, LIVE_WEATHER). The defense's is its colours and the opponent's
   implied points (LIVE_LINES), where lower is better for you. */
const CARD_POSTS = `<svg class="tc-posts" viewBox="0 0 58 40" aria-hidden="true"><path d="M6 4v20M52 4v20M6 24h46M29 24v16"/></svg>`;
function supportArt(p, g){
  if (p.pos === "K"){
    const w = g ? cardTeamRow(typeof LIVE_WEATHER !== "undefined" ? LIVE_WEATHER : null, g.venue) : null;
    // One chip, the one that decides a kick: a roof means no wind at all; otherwise the wind.
    const chip = !w ? t("teams.card.noForecast") : w.roof === "dome" ? t("teams.card.dome")
      : w.wind ? t("teams.card.wind", {w: esc(w.wind), d: esc(w.wind_dir || "")}) : cardRoof(w);
    return `${CARD_POSTS}<div class="head">${headHTML(p)}</div><span class="tc-chip r">${chip}</span>`;
  }
  const opp = g ? cardLines(g.opp) : null;
  return `<span class="tc-abbr">${esc(p.team)}</span>
    <div class="tc-imp">${opp ? `<b>${opp.implied}</b><span>${t("teams.card.implied", {team: esc(g.opp)})}</span>` : `<span>${t("teams.card.noLine")}</span>`}</div>`;
}
const cardRoof = w => w.roof === "dome" ? t("teams.card.dome") : w.roof === "retractable" ? t("teams.card.retractable") : t("teams.card.outdoor");
function supportBack(p, g, teamKey, i){
  const opp = g ? cardLines(g.opp) : null, mine = cardLines(p.team);
  const w = g ? cardTeamRow(typeof LIVE_WEATHER !== "undefined" ? LIVE_WEATHER : null, g.venue) : null;
  const rows = p.pos === "K"
    ? [[t("teams.card.roof"), w ? cardRoof(w) : "—"],
       [t("teams.card.windLabel"), w && w.wind && w.roof !== "dome" ? `${w.wind} ${w.wind_dir || ""}` : "—"],
       [t("teams.card.teamImplied"), mine ? String(mine.implied) : "—"]]
    : [[t("teams.card.oppImplied"), opp ? String(opp.implied) : "—"], [t("teams.card.spread"), mine ? `${p.team} ${mine.spread > 0 ? "+" : ""}${mine.spread}` : "—"]];
  return `<div class="tc-face tc-back">
      <div class="bk-why"><b>${p.pos === "K" ? t("teams.card.kicking") : t("teams.card.defending")}</b>${esc(cardMatchup(p.team, g))}</div>
      ${rows.map(([l, v]) => `<div class="bk-l">${l}</div><div class="bk-m">${esc(v)}</div>`).join("")}
      ${p.pos === "DST" ? `<div class="bk-note">${t("teams.card.lowerBetter")}</div>` : ""}
      <button class="bk-open" type="button" data-cteam="${teamKey}" data-ci="${i}">${t("teams.card.profile")}</button>
    </div>`;
}

function cardHTML(p, i, teamKey){
  const g = cardGame(p.team);
  const support = p.pos === "K" || p.pos === "DST";
  const rank = support ? null : cardRank(p);
  const tier = support ? (p.pos === "K" ? "k" : "dst") : cardTier(rank);
  const colours = p.pos === "DST" ? teamColourStyle(p.team) : "";
  const front = support
    ? `<div class="tc-face tc-front">
        <div class="tc-top"><span>${esc(p.pos)}</span><span>${esc(g ? `${g.home ? "vs" : "@"} ${g.opp}` : "")}</span></div>
        <div class="tc-art">${supportArt(p, g)}</div>
        <div class="tc-name">${esc(p.pos === "K" ? nameInitial(p.n) : p.n)}</div>
        <div class="tc-meta">${p.pos === "K" ? t("teams.card.kicker", {team: esc(p.team)}) : t("teams.card.defense", {team: esc(p.team)})}</div>
      </div>`
    : cardFront(p, tier, g);
  return `<div class="tc tier-${tier}" ${colours} role="button" tabindex="0" aria-label="${t("teams.card.flip", {name: esc(p.n)})}">
    <div class="tc-flip">${front}${support ? supportBack(p, g, teamKey, i) : cardBack(p, rank, teamKey, i)}</div>
    <div class="tc-glare"></div>
  </div>`;
}

/* The index a card carries is the profile's (drawer.js findPlayer): starters, then bench, then out. */
function cardsHTML(team){
  const start = team.roster.filter(p => p.start);
  const rest = team.roster.filter(p => !p.start && p.slot !== "OUT").concat(team.roster.filter(p => p.slot === "OUT"));
  let n = 0;
  const grid = list => `<div class="cardgrid">${list.map(p => cardHTML(p, n++, team.key)).join("")}</div>`;
  const rule = (label, count) => `<div class="rule"><h2>${label}</h2><span class="count">${String(count).padStart(2,"0")}</span><span class="hair"></span></div>`;
  return `<div class="cards">
    <section class="cards-col">${rule(t("teams.group.starters"), start.length)}${grid(start)}</section>
    ${rest.length ? `<section class="cards-col bench">${rule(t("teams.group.bench"), rest.length)}${grid(rest)}</section>` : ""}
  </div>`;
}

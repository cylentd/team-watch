/* The roster as trading cards (2026-09-25), the Cards half of the Sheet / Cards switch. A card's
   tier is this week's projected rank at his position (LIVE_PROJECTIONS rank/of, design/projections.py),
   never a hand pick. The back prints the rank in words ("#7 RB"), never a tier code. A kicker and
   a defense have no projection, so no tier: they are support cards whose art is the matchup. A
   player not playing this week has no rank, so no tier either. Tap flips a card; its back carries
   the role stats the front leaves out and the way into the profile. */
/* Five tiers, each its own colour family (2026-09-25; earned by rank alone, never by being a
   roster's best):  #1 "one" holo · #2-5 "sig" violet, etched · #6-12 "ur" gold · #13-24 "r" blue ·
   the rest "c" plain. It had gold twice and silver beside grey, so neighbouring tiers looked alike.
   The autograph is not a tier (since 2026-09-25, it was #1-5): it is earned by last week's finish,
   cardSigned. A roster with nobody who finished top 3 gets none: that is the news, not a gap. */
function cardTier(rank){
  if (!rank) return "c";
  return rank === 1 ? "one" : rank <= 5 ? "sig" : rank <= 12 ? "ur" : rank <= 24 ? "r" : "c";
}
/* {rank, pts} when he finished top 3 at his position in the last completed week (design/signed.py). */
function cardSigned(p){
  return typeof LIVE_SIGNED !== "undefined" && LIVE_SIGNED && p.slug ? LIVE_SIGNED.players[p.slug] || null : null;
}
function cardRank(p){
  if (typeof LIVE_PROJECTIONS === "undefined" || !LIVE_PROJECTIONS) return null;
  const r = LIVE_PROJECTIONS.players[p.slug];
  return r && r.rank ? r.rank : null;
}

/* A card's photo is the 256px head where ff-jarvis cut one (HEADS_LG, the draft board's players),
   since a card shows it at 2-3x the 96px file's size and blurs it. Anyone else keeps the 96px
   head, and a failed load still falls back to initials (headImgHTML). */
function cardHeadHTML(p){
  const lg = typeof HEADS_LG !== "undefined" && HEADS_LG && p.slug ? HEADS_LG[p.slug] : null;
  return lg ? headImgHTML(lg, initials(p.n)) : headHTML(p);
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

/* The front says four lines: slot and points, who, and the game, and a small stamp in the photo's
   corner gives the rank ("#7") in the tier's colour. The rank as a text line was dropped earlier the
   same day (a fifth line made a phone row of three crowded); the stamp keeps two cards of one tier
   apart without the line. */
function cardFront(p, tier, g, rank){
  const pts = projFor(p);
  // Hurt: out or doubtful is a band across the foot of the photo, in place of the signature, with
  // the reason as its tooltip; questionable is a small Q in the corner (injury.js, 2026-09-25).
  const inj = injFor(p), band = inj && inj.s !== "Q";
  const hurt = !inj ? "" : band ? `<span class="tc-inj ${inj.s.toLowerCase()}" title="${injLabel(inj)}">${INJ_WORD[inj.s]()}</span>`
    : `<span class="tc-chip q" title="${injLabel(inj)}">${t("teams.inj.q")}</span>`;
  // Signed only when he earned it: top 3 at his position in the last completed week (LIVE_SIGNED),
  // on any tier. The tier is what he is expected to do; the autograph is what he did.
  const won = cardSigned(p);
  const sig = !band && won ? `<span class="tc-sig" title="${t("teams.card.signedTip", {rank: won.rank, pos: esc(p.pos), wk: LIVE_SIGNED.wk, pts: won.pts})}">${esc(p.n)}</span>` : "";
  // Behind the photo: the violet etch (#2-5), or the #1's holo foil and glitter.
  const foil = {sig: `<i class="tc-etch"></i>`, one: `<i class="tc-holo"></i><i class="tc-spark"></i>`}[tier] || "";
  const stamp = rank ? `<span class="tc-rank" title="${t("teams.card.rank", {n: rank, pos: esc(p.pos)})}">${t("teams.card.rankStamp", {n: rank})}</span>` : "";
  // Weather that touches him: moving over the art, and its chip in the other top corner.
  const w = inj && inj.s === "OUT" ? null : cardWeather(g), wx = cardWeatherNote(w, p.pos);
  const sky = wx ? `${cardWeatherFx(w, p.pos)}<span class="tc-chip wx" title="${t("teams.card.wxTip", wx)}">${wx.what}</span>` : "";
  return `<div class="tc-face tc-front">
      <div class="tc-top"><span>${esc(p.start ? slotLabel(p.slot) : p.pos)}</span><span class="tc-num${projOut(p) ? " out" : ""}">${pts !== null ? pts.toFixed(1) : projOut(p) ? t("teams.card.out") : "—"}</span></div>
      <div class="tc-art pos-${esc(p.pos)}">${foil}${sky}${stamp}
        <div class="head">${cardHeadHTML(p)}</div>${sig}${hurt}</div>
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
/* The heading's second line is what matters most this week: his injury ("OUT · Personal"), else
   the weather when it touches him ("RAIN · pass ↓"), else which week the stats are from. */
function cardBack(p, rank, teamKey, i, g){
  const stats = cardStats(p), inj = injFor(p);
  const wx = inj && inj.s === "OUT" ? null : cardWeatherNote(cardWeather(g), p.pos);
  const sub = inj ? `<span class="bk-inj ${inj.s.toLowerCase()}" title="${injLabel(inj)}">${injLabel(inj)}</span>`
    : wx ? `<span class="bk-wx" title="${t("teams.card.wxTip", wx)}">${t("teams.card.wxNote", wx)}</span>`
    : `<span>${stats ? t("teams.card.roleWeek", {wk: stats.wk}) : t("teams.card.thisWeek")}</span>`;
  return `<div class="tc-face tc-back pos-${esc(p.pos)}">
      <div class="bk-why"><b>${rank ? t("teams.card.rank", {n: rank, pos: esc(p.pos)}) : esc(p.pos)}</b>${sub}</div>
      ${stats ? stats.html : `<div class="bk-l">${t("teams.card.snap")}</div><div class="bk-sp">${sparkHTML(p.trend, 110, 28)}</div>`}
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
    : cardFront(p, tier, g, rank);
  return `<div class="tc tier-${tier}${support ? "" : injClass(p)}" ${colours} role="button" tabindex="0" aria-label="${t("teams.card.flip", {name: esc(p.n)})}">
    <div class="tc-flip">${front}${support ? supportBack(p, g, teamKey, i) : cardBack(p, rank, teamKey, i, g)}</div>
    <div class="tc-glare"></div>
  </div>`;
}

/* The index a card carries is the profile's (drawer.js findPlayer): starters, then bench, then out. */
function cardsHTML(team){
  const start = team.roster.filter(p => p.start);
  const rest = team.roster.filter(p => !p.start && p.slot !== "OUT").concat(team.roster.filter(p => p.slot === "OUT"));
  let n = 0;
  // While this week's pack is turning over, its cards are drawn face down in their slots (packreveal.js).
  const grid = list => `<div class="cardgrid">${list.map(p => { const i = n++; return packFaceDown(team, i, cardHTML(p, i, team.key)); }).join("")}</div>`;
  const rule = (label, count) => `<div class="rule"><h2>${label}</h2><span class="count">${String(count).padStart(2,"0")}</span><span class="hair"></span></div>`;
  return `${injWarnHTML(team)}<div class="cards">
    <section class="cards-col">${rule(t("teams.group.starters"), start.length)}${grid(start)}</section>
    ${rest.length ? `<section class="cards-col bench">${rule(t("teams.group.bench"), rest.length)}${grid(rest)}</section>` : ""}
  </div>`;
}

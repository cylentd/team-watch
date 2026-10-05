/* The roster as trading cards (2026-09-25), the Cards half of the Sheet / Cards switch. A card's
   tier is this week's projected rank at his position (LIVE_PROJECTIONS rank/of, design/projections.py),
   never a hand pick. The back prints the rank in words ("#7 RB"), never a tier code. A kicker and
   a defense have no projection, so no tier: they are support cards whose art is the matchup. A
   player not playing this week has no rank, so no tier either. Tap flips a card; its back carries
   the matchup, the role stats the front leaves out and the way into the profile. */
/* Three metals and the stock (2026-10-05; it was five colour tiers, violet and blue are gone):
   #1 "holo" · #2-3 "gold" · #4-6 "silver" · the rest "base", plain card stock. Measured across 36
   teams that is 1.8 metal cards a team, where the old #1-12 cut gave 3.4. Earned by rank alone.
   The autograph is not a tier: it is earned by last week's finish, cardSigned. A roster with nobody
   who finished top 3 gets none: that is the news, not a gap. */
function cardTier(rank){
  if (!rank) return "base";
  return rank === 1 ? "holo" : rank <= 3 ? "gold" : rank <= 6 ? "silver" : "base";
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

/* The autograph on the face: only the gold script name, sized to fit (fitSig). The words ("Signed
   for week 3: #2 TE, 22.6 pts") live on the back and in the pack's label. This structure is the
   contract for the motion: .hot is the pen's white-hot ink and .tip the nib, both hidden here, and
   .cool the finished gold; the pack writes it left to right (cardsign.js). */
function cardAutoHTML(p, won){
  const tip = t("teams.card.signedTip", {rank: won.rank, pos: esc(p.pos), wk: LIVE_SIGNED.wk, pts: won.pts}), n = esc(p.n);
  return `<div class="tc-auto" title="${tip}"><span class="sgw"><span class="sg cool">${n}</span><span class="sg hot">${n}</span><i class="tip"></i></span></div>`;
}
/* A card's photo is the 256px head where ff-jarvis cut one (HEADS_LG, the draft board's players),
   since a card shows it at 2-3x the 96px file's size and blurs it. Anyone else keeps the 96px
   head, and a failed load still falls back to initials (headImgHTML). */
function cardHeadHTML(p){
  const lg = typeof HEADS_LG !== "undefined" && HEADS_LG && p.slug ? HEADS_LG[p.slug] : null;
  return lg ? headImgHTML(lg, initials(p.n), p.slug, 110) : headHTML(p);
}

/* This week's game for a team, from the schedule: the next kickoff not more than four hours gone.
   The schedule spells two clubs its own way (alias: LA -> LAR, WAS -> WSH), and so do the lines
   (data/schedule.js). */
function cardGame(team){
  if (!schedOk()) return null;
  const code = schedCode(team), now = Date.now() - SCHED_GRACE_MS;
  const g = LIVE_SCHEDULE.games
    .filter(x => (x.home === code || x.away === code) && Date.parse(x.kickoff) > now)
    .sort((a, b) => Date.parse(a.kickoff) - Date.parse(b.kickoff))[0];
  return g ? {opp: g.home === code ? g.away : g.home, home: g.home === code, venue: g.home} : null;
}
const cardLines = team => schedTeamRow(typeof LIVE_LINES !== "undefined" ? LIVE_LINES : null, team);
const cardMatchup = (team, g) => g ? `${team} ${g.home ? "vs" : "@"} ${g.opp}` : team;

/* The name on the banner is his last name ("St. Brown", "Pittman" for a Jr.), and a longer one steps
   down the type scale so the badge never covers it. */
function cardLast(n){
  const parts = String(n || "").trim().replace(/\s+(Jr\.?|Sr\.?|II|III|IV)$/i, "").split(/\s+/);
  return parts.length < 2 ? parts[0] : parts.slice(1).join(" ");
}
const cardBanner = name => `<div class="tc-ban" style="--bf:var(${name.length <= 8 ? "--t-2" : "--t-1"})"><span>${esc(name)}</span></div>`;
/* The round badge on the banner's edge: position over rank, its ring the metal (cards.css). */
const cardBadge = (pos, rank, tip = "") => `<span class="tc-badge"${tip ? ` title="${tip}"` : ""}><b>${esc(pos)}</b>${rank ? `<i>${rank}</i>` : ""}</span>`;

/* The front, 2026-10-05 ("3G"): the photo full bleed on the club's colour inside the card stock; the
   projection chip top right; the last name on a club-colour banner across the foot; the badge
   (position over rank) on the banner's right. A hit has a metal border and the #1's photo is tinted
   holo. OUT greys the photo and turns the projection red. Weather and Q/D chips sit on their own row
   under the projection, never on it, the badge or the banner. The game is on the back. */
function cardFront(p, tier, g, rank){
  const pts = projFor(p);
  const inj = injFor(p), sits = inj && (inj.s === "OUT" || inj.s === "D");
  const flag = !inj || inj.s === "OUT" ? ""
    : `<span class="tc-chip ${inj.s === "Q" ? "q" : "d"}" title="${injLabel(inj)}">${inj.s === "Q" ? t("teams.inj.q") : t("teams.card.doubtful")}</span>`;
  // Signed only when he earned it: top 3 at his position in the last completed week (LIVE_SIGNED),
  // on any tier. The tier is what he is expected to do; the autograph is what he did.
  const won = cardSigned(p);
  const auto = !sits && won ? cardAutoHTML(p, won) : "";
  // The #1's photo is tinted holo, over the photo and under everything printed on it.
  const holo = tier === "holo" ? `<i class="tc-holo"></i>` : "";
  // Weather that touches him: moving over the art, and its chip, with what ff-jarvis already took
  // off his projection for it ("−0.5") when it took any.
  const w = inj && inj.s === "OUT" ? null : cardWeather(g), wx = cardWeatherNote(w, p.pos);
  const adj = wx ? cardWxAdj(p) : "";
  const adjHTML = adj ? `<span class="wx-adj" title="${t("teams.card.wxAdjTip", {n: adj})}">${t("teams.card.wxAdj", {n: adj})}</span>` : "";
  const chip = wx ? `<span class="tc-chip wx" title="${t("teams.card.wxTip", wx)}"><span class="wx-long">${wx.what}</span><span class="wx-short">${wx.kind}</span>${adjHTML}</span>` : "";
  const tip = rank ? t("teams.card.rank", {n: rank, pos: esc(p.pos)}) : "";
  // OUT on either source (the projection row or the injury report) reads OUT in red, never a number.
  const out = projOut(p) || (inj && inj.s === "OUT");
  const num = out ? t("teams.card.out") : pts !== null ? pts.toFixed(1) : projDone(p) ? projDoneWord(projDone(p)) : "—";
  return `<div class="tc-face tc-front">
      <div class="tc-art pos-${esc(p.pos)}">${wx ? cardWeatherFx(w, p.pos) : ""}<div class="head">${cardHeadHTML(p)}</div>${holo}</div>
      ${flag || chip ? `<div class="tc-flags">${chip}${flag}</div>` : ""}${auto}
      <span class="tc-num${out ? " out" : ""}">${num}</span>
      ${cardBanner(cardLast(p.n))}${cardBadge(p.pos, rank, tip)}
    </div>`;
}

/* The back holds only what the front does not: the game, why the tier, and his role as a stat sheet.
   Three usage stats for his position (WV_PROOF, the waiver card's choice, so the two never disagree),
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
/* The heading's first line is the rank with the game beside it ("#7 RB", "BAL @ DAL"); its second
   is what matters most this week: his injury ("OUT · Personal"), else the weather when it touches
   him ("RAIN · pass ↓"), else which week the stats are from. A signed card adds the autograph's
   words as one row under the heading. */
function cardBack(p, rank, teamKey, i, g){
  const stats = cardStats(p), inj = injFor(p), won = cardSigned(p);
  const wx = inj && inj.s === "OUT" ? null : cardWeatherNote(cardWeather(g), p.pos);
  const sub = inj ? `<span class="bk-inj ${inj.s.toLowerCase()}" title="${injLabel(inj)}">${injLabel(inj)}</span>`
    : wx ? `<span class="bk-wx" title="${t("teams.card.wxTip", wx)}">${t("teams.card.wxNote", wx)}${cardWxAdj(p) ? ` · ${t("teams.card.wxAdjBack", {n: cardWxAdj(p)})}` : ""}</span>`
    : `<span>${stats ? t("teams.card.roleWeek", {wk: stats.wk}) : t("teams.card.thisWeek")}</span>`;
  const signed = won ? `<div class="bk-signed">${t("teams.card.signedBack", {wk: LIVE_SIGNED.wk, rank: won.rank, pos: esc(p.pos), pts: won.pts})}</div>` : "";
  return `<div class="tc-face tc-back pos-${esc(p.pos)}${won ? " signed" : ""}">
      <div class="bk-why"><b>${rank ? t("teams.card.rank", {n: rank, pos: esc(p.pos)}) : esc(p.pos)}<small>${esc(cardMatchup(p.team, g))}</small></b>${sub}</div>${signed}
      ${stats ? stats.html : `<div class="bk-l">${t("teams.card.snap")}</div><div class="bk-sp">${sparkHTML(p.trend, 110, 28)}</div>`}
      <button class="bk-open" type="button" data-cteam="${teamKey}" data-ci="${i}">${t("teams.card.profile")}</button>
    </div>`;
}

function cardHTML(p, i, teamKey){
  const g = cardGame(p.team);
  const support = p.pos === "K" || p.pos === "DST";
  const rank = support ? null : cardRank(p);
  const tier = support ? (p.pos === "K" ? "k" : "dst") : cardTier(rank);
  // Support cards wear the same stock, banner and badge; the badge says just K or DST.
  const front = support
    ? `<div class="tc-face tc-front">
        <div class="tc-art">${supportArt(p, g)}</div>
        <span class="tc-num">${esc(g ? `${g.home ? "vs" : "@"} ${g.opp}` : "—")}</span>
        ${cardBanner(p.pos === "K" ? cardLast(p.n) : p.n)}${cardBadge(p.pos, null, p.pos === "K" ? t("teams.card.kicker", {team: esc(p.team)}) : t("teams.card.defense", {team: esc(p.team)}))}
      </div>`
    : cardFront(p, tier, g, rank);
  return `<div class="tc tier-${tier}${support ? "" : injClass(p)}" ${teamColourStyle(p.team)} role="button" tabindex="0" aria-label="${t("teams.card.flip", {name: esc(p.n)})}">
    <div class="tc-flip">${front}${support ? supportBack(p, g, teamKey, i) : cardBack(p, rank, teamKey, i, g)}</div>
    <div class="tc-glare"></div><i class="fx"></i>
  </div>`;
}

/* The index a card carries is the profile's (drawer.js findPlayer): starters, then bench, then out. */
function cardsHTML(team){
  const start = team.roster.filter(p => p.start);
  const rest = team.roster.filter(p => !p.start && p.slot !== "OUT").concat(team.roster.filter(p => p.slot === "OUT"));
  let n = 0; cardsFit();
  // While the stage holds this week's pack, its cards' slots are kept empty (packshow.js packFaceDown);
  // while the pack waits in the starters' place, the starters lie face down under it (packgate.js).
  const gated = packGated(team);
  const grid = (list, down) => `<div class="cardgrid"${down ? " inert" : ""}>${list.map(p => {
    const i = n++, html = cardHTML(p, i, team.key);
    return down ? packCardDown(html) : packFaceDown(team, i, html);
  }).join("")}</div>`;
  const rule = (label, count, end = "") => `<div class="rule"><h2>${label}</h2><span class="count">${String(count).padStart(2,"0")}</span><span class="hair"></span>${end}</div>`;
  const starters = gated ? `<div class="pk-zone">${grid(start, true)}${packGateHTML(team)}</div>` : grid(start);
  return `<div class="cards">
    <section class="cards-col">${rule(t("teams.group.starters"), start.length, reripHTML(team))}${starters}</section>
    ${rest.length ? `<section class="cards-col bench">${rule(t("teams.group.bench"), rest.length)}${grid(rest)}</section>` : ""}
  </div>`;
}

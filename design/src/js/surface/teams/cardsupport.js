/* Support cards (2026-09-25): a kicker and a defense have no projection, so no tier; their art is
   the matchup. The kicker's is his venue: turf, the posts off to one side and the weather moving
   over it (the kickoff-hour forecast at the home stadium, cardweather.js). The defense's is the
   club itself, its code large in its colours, with the opponent's implied points (LIVE_LINES) as a
   chip: lower is better for you. Split out of cards.js the same day. */
const CARD_POSTS = `<svg class="tc-posts" viewBox="0 0 58 40" aria-hidden="true"><path d="M6 4v20M52 4v20M6 24h46M29 24v16"/></svg>`;
const cardRoof = w => w.roof === "dome" ? t("teams.card.dome") : w.roof === "retractable" ? t("teams.card.retractable") : t("teams.card.outdoor");

function supportArt(p, g){
  if (p.pos === "K"){
    const w = cardWeather(g);
    // One chip, the one that decides a kick: a roof means no wind at all; otherwise the wind.
    const chip = !w ? t("teams.card.noForecast") : w.roof === "dome" ? t("teams.card.dome")
      : w.wind ? t("teams.card.wind", {w: esc(w.wind), d: esc(w.wind_dir || "")}) : cardRoof(w);
    return `${CARD_POSTS}${cardWeatherFx(w, "K")}<div class="head" data-testid="roster-card-head">${cardHeadHTML(p)}</div><span class="tc-chip r">${chip}</span>`;
  }
  const opp = g ? cardLines(g.opp) : null;
  const chip = opp ? t("teams.card.implied", {n: opp.implied}) : t("teams.card.noLine");
  return `<span class="tc-abbr" data-testid="roster-card-abbr">${esc(p.team)}</span>
    <span class="tc-chip r" title="${t("teams.card.lowerBetter")}">${chip}</span>`;
}

/* A fact's label and value as text. A missing number is a dash, a real minus on the spread. */
function supportFactText(r){
  const none = "—", n = r.v === null ? none : String(r.v);
  switch (r.key){
    case "roof": return [t("teams.card.roof"), t("teams.card.factDome")];
    case "wind": return [t("teams.card.windLabel"), r.v === null ? none : t("teams.card.factMph", {n: r.v})];
    case "team": return [t("teams.card.factTeam"), n];
    case "opp": return [t("teams.card.factOpp"), n];
    case "spread": return [t("teams.card.spread"), spreadText(r.v)];
    default: return [t("teams.card.factProj"), r.v.toFixed(1)];
  }
}

/* The back, the same as every other card's (2026-10-07): the matchup and kickoff on top (cardBackHead), then
   two facts and this week's projection, whole labels, centred between the heading and the button. There are
   no weekly K or D/ST points to draw as bars (supportback.js), so no bars. */
function supportBack(p, g, teamKey, i){
  const opp = g ? cardLines(g.opp) : null, mine = cardLines(p.team), w = cardWeather(g);
  const lg = pbLeague(teamKey), bars = pbBackHTML(p, lg);
  if (bars) return `<div class="tc-face tc-back pos-${esc(p.pos)}" data-testid="roster-card-back">
      ${cardBackHead(p, g)}
      ${bars}
      <button class="bk-open" type="button" data-testid="roster-back-open" data-cteam="${teamKey}" data-ci="${i}">${t("teams.card.profile")}</button>
    </div>`;
  const rows = supportFacts(p.pos, {
    roof: w ? w.roof : "", windMph: w && w.roof !== "dome" && w.wind ? wxWindMph(w) : null,
    team: mine ? mine.implied : null, opp: opp ? opp.implied : null, spread: mine ? mine.spread : null,
    proj: dstPointsFor(typeof LIVE_DST !== "undefined" ? LIVE_DST : null, lg, p.pos, p.team, schedWeek())});
  const fact = r => { const [label, text] = supportFactText(r);
    return `<div class="bk-row${r.key === "proj" ? " proj" : ""}" data-testid="roster-back-fact"><span class="bk-l">${label}</span><b>${esc(text)}</b></div>`; };
  return `<div class="tc-face tc-back" data-testid="roster-card-back">
      ${cardBackHead(p, g)}
      <div class="bk-rows" data-testid="roster-back-facts"${p.pos === "DST" ? ` title="${t("teams.card.lowerBetter")}"` : ""}>${rows.map(fact).join("")}</div>
      <button class="bk-open" type="button" data-testid="roster-back-open" data-cteam="${teamKey}" data-ci="${i}">${t("teams.card.profile")}</button>
    </div>`;
}

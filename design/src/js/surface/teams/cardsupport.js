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
    return `${CARD_POSTS}${cardWeatherFx(w, "K")}<div class="head">${cardHeadHTML(p)}</div><span class="tc-chip r">${chip}</span>`;
  }
  const opp = g ? cardLines(g.opp) : null;
  const chip = opp ? t("teams.card.implied", {team: esc(g.opp), n: opp.implied}) : t("teams.card.noLine");
  return `<span class="tc-abbr">${esc(p.team)}</span>
    <span class="tc-chip r" title="${t("teams.card.lowerBetter")}">${chip}</span>`;
}

function supportBack(p, g, teamKey, i){
  const opp = g ? cardLines(g.opp) : null, mine = cardLines(p.team), w = cardWeather(g);
  const outside = w && w.roof !== "dome";
  const rows = p.pos === "K"
    ? [[t("teams.card.roof"), w ? cardRoof(w) : "—"],
       [t("teams.card.windLabel"), outside && w.wind ? `${w.wind} ${w.wind_dir || ""}` : "—"],
       [t("teams.card.rain"), outside && typeof w.precip_pct === "number" ? `${w.precip_pct}%` : "—"],
       [t("teams.card.teamImplied"), mine ? String(mine.implied) : "—"]]
    : [[t("teams.card.oppImplied"), opp ? String(opp.implied) : "—"],
       [t("teams.card.spread"), mine ? `${mine.spread > 0 ? "+" : ""}${mine.spread}` : "—"],
       [t("teams.card.total"), mine && mine.total ? String(mine.total) : "—"]];
  return `<div class="tc-face tc-back">
      <div class="bk-why"><b>${p.pos === "K" ? t("teams.card.kicking") : t("teams.card.defending")}</b><span>${esc(cardMatchup(p.team, g))}</span></div>
      <div class="bk-rows"${p.pos === "DST" ? ` title="${t("teams.card.lowerBetter")}"` : ""}>${rows.map(([l, v]) => `<div class="bk-row"><span class="bk-l">${l}</span><b>${esc(v)}</b></div>`).join("")}</div>
      <button class="bk-open" type="button" data-cteam="${teamKey}" data-ci="${i}">${t("teams.card.profile")}</button>
    </div>`;
}

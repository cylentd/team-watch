/* DIGEST CARD: Weather (Saturday, Sunday). The games still to play whose forecast moves scoring, from the
   Weather view's own reading (data/weather.js wtRows through dgWxMoves: only a condition the backtest proved).
   One row per game, the home club's tile, "DET @ SEA", the conditions under it, and on the right the biggest
   effect in points per position ("−1.5 pts per QB"). A tap opens every position it moves and the kickoff. A cold
   forecast carries its failed test (weather.cond.coldMark). No roster is read: the page is public. Three rows
   at most; more to Weather. Interface: card.js; returns "" when no game qualifies. */
const DG_WX_ROWS = 3;

/* "15 to 22 mph wind · 70% chance of rain": the proven conditions this forecast meets, as Weather says them. */
function dgWxMeta(r){
  const fc = r.fc, parts = [];
  if (r.conds.includes("wind")) parts.push(t("weather.cond.wind", {wind: esc(fc.wind)}));
  if (r.conds.includes("precip")) parts.push(wxKind(fc.short) === "snow" ? t("weather.cond.snow", {n: fc.precip_pct}) : t("weather.cond.rain", {n: fc.precip_pct}));
  if (r.conds.includes("cold")) parts.push(`<span title="${esc(t("weather.cond.coldMark"))}">${t("profile.weather.temp", {n: fc.temp_f})}</span>`);
  return parts.join(" · ");
}

function dgWxRowHTML(r){
  const top = r.effects.reduce((a, e) => Math.abs(e.pts) > Math.abs(a.pts) ? e : a);
  return dgRowHTML("weather", {tile: r.g.home, n: `${r.g.away} @ ${r.g.home}`, meta: dgWxMeta(r),
    answer: {num: wtSigned(top.pts), change: t("digest.card.weather.per", {pos: top.pos}), dir: top.pts < 0 ? "down" : "up"},
    research: [...r.effects.map(e => [e.pos, t("digest.card.weather.pts", {n: wtSigned(e.pts)})]), [t("digest.card.weather.kick"), kickFmt(r.g.kickoff)]],
    foot: r.conds.includes("cold") ? t("weather.cond.coldMark") : ""});
}

function dgCardWeather(ctx){
  const moves = dgWxMoves().slice(0, DG_WX_ROWS);
  if (!moves.length) return "";
  return dgCardHTML({id: "weather", title: t("digest.card.weather.title"), more: {leaf: "weather"}, body: moves.map(dgWxRowHTML).join("")});
}

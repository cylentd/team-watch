/* Weather on a card (2026-09-25). LIVE_WEATHER is ff-jarvis's forecast for the hour of each
   stadium's next home kickoff, keyed by the home team, so a card reads its game's venue.
   Only an open-air stadium counts: a dome has none, and a retractable roof is the club's call on
   the day. What it does to a player follows the public splits: wind from 15 mph, rain from a 40%
   chance and any snow cut passing and kicking; wet weather tilts a game to the run. A card shows
   it only when it matters, so a fair-weather week draws nothing. */
const cardWeather = g => g ? cardTeamRow(typeof LIVE_WEATHER !== "undefined" ? LIVE_WEATHER : null, g.venue) : null;
/* The top of a forecast's wind range: "5 to 10 mph" is 10. */
const cardWindMph = w => w && w.wind ? Math.max(...(w.wind.match(/\d+/g) || ["0"]).map(Number)) : 0;
const WX_WIND_MPH = 15, WX_WET_PCT = 40;

/* What is falling or blowing: {wind, fall} with fall "snow" / "rain" / "", or null when nothing
   is, or the stadium is covered. */
function cardSky(w){
  if (!w || w.roof !== "outdoor") return null;
  const mph = cardWindMph(w), sky = (w.short || "").toLowerCase();
  const fall = sky.includes("snow") ? "snow" : (w.precip_pct || 0) >= WX_WET_PCT ? "rain" : "";
  return mph >= WX_WIND_MPH || fall ? {wind: mph >= WX_WIND_MPH ? mph : 0, fall} : null;
}

/* The art's weather layer, behind the photo: streaks in the wind (faster the harder it blows),
   rain on a slant, drifting snow. Wind only on a card it hurts: a runner does not mind it. */
function cardWeatherFx(w, pos){
  const s = cardSky(w);
  if (!s) return "";
  const wind = s.wind && pos !== "RB" ? `<i class="tc-wx wind" style="--wx-s:${Math.max(0.5, 2.4 - s.wind / 12).toFixed(2)}s"></i>` : "";
  return wind + (s.fall ? `<i class="tc-wx ${s.fall}"></i>` : "");
}

/* What touches him, three ways: `what` for the front's chip ("RAIN 60%"), `kind` for the back's
   narrow line ("RAIN"), and `effect` ("pass ↓"). Null when the weather does not touch him. */
function cardWeatherNote(w, pos){
  const s = cardSky(w);
  if (!s) return null;
  const what = s.fall === "snow" ? t("teams.card.wxSnow") : s.fall === "rain" ? t("teams.card.wxRain", {n: w.precip_pct})
    : pos === "RB" ? null : t("teams.card.wxWind", {n: s.wind});
  if (!what) return null;
  const kind = s.fall === "snow" ? t("teams.card.wxSnow") : s.fall === "rain" ? t("teams.card.wxRainWord") : t("teams.card.wxWindWord");
  const effect = pos === "K" ? t("teams.card.wxKick") : pos === "RB" ? t("teams.card.wxRun") : t("teams.card.wxPass");
  return {what, kind, effect};
}

/* A game whose weather moves scoring (This week > Weather, reworked 2026-09-26). Four lines, in the
   order a lineup setter asks them:
     MIA @ NE                                   Sun 1:05 PM
     ~ 15 to 22 mph wind · ~ 70% chance of rain · 61°F
     QBs about 1.5 fewer points · WRs about 1 fewer · kickers about 1.5 fewer
     Already counted in our projections. We don't project kickers.
   then who it hits: each side's top QB, WRs and TE, with what is already in his projection.
   Only proven positions are named (data/wxhistory.js); no verdict about a player. */
const wtSigned = v => Math.abs(v) < 0.05 ? "0.0" : (v > 0 ? "+" : "−") + Math.abs(v).toFixed(1);
const wtPosWord = pos => ({QB: t("weather.pos.qb"), RB: t("weather.pos.rb"), WR: t("weather.pos.wr"),
  TE: t("weather.pos.te"), K: t("weather.pos.k")})[pos] || esc(pos);
const wtHalf = v => Number.isInteger(v) ? String(v) : v.toFixed(1);
const WT_STALE_H = 12;   // a forecast older than this says its age on the card

/* The icon for a condition, drawn as the site's own weather icons (ui/weather.js) with each stroke
   its own path, so a still frame is the plain icon and motion only moves those strokes: the wind's
   three lines gust the way it blows, as fast as it blows; the drops under the cloud fall, more of
   them the likelier the rain. Reduced motion keeps the still icon (card.css). */
const WT_WIND = ["M3 8h11a3 3 0 1 0-3-3", "M3 12h15a3 3 0 1 1-3 3", "M3 16h8a2 2 0 1 1-2 2"];
const WT_CLOUD = "M7 15a4 4 0 0 1-.6-7.95A6 6 0 0 1 18 6.5 3.5 3.5 0 0 1 17.5 15Z";
function wtSky(kind, fc){
  const svg = (cls, body, style) => `<svg class="pf-wx-i wt-sky ${cls}" viewBox="0 0 24 24" aria-hidden="true"${style ? ` style="${style}"` : ""}>${body}</svg>`;
  if (kind === "wind"){
    const side = wxWindSide(fc.wind_dir) < 0 ? " west" : "";
    return svg(`wind${side}`, WT_WIND.map((d, i) => `<path class="wt-gust" style="--i:${i}" d="${d}"/>`).join(""),
      `--wx-s:${wxGustS(wxWindMph(fc))}s`);
  }
  const snow = wxKind(fc.short) === "snow";
  const n = Math.max(1, Math.min(4, Math.round((fc.precip_pct || 0) / 25)));
  const xs = [[12], [10, 14], [8, 12, 16], [7, 10.5, 14, 17.5]][n - 1];
  const drop = x => snow ? `M${x} 18v3` : `M${x} 18l-1 3`;
  return svg(snow ? "snow" : "rain", `<path d="${WT_CLOUD}"/>${xs.map((x, i) => `<path class="wt-drop" style="--i:${i}" d="${drop(x)}"/>`).join("")}`);
}

/* Which way the effects point: "lower", "raise", or "mixed". Heading and projections line agree. */
const wtWay = effects => effects.every(e => e.pts < 0) ? "lower" : effects.every(e => e.pts > 0) ? "raise" : "mixed";

function wtCondHTML(r){
  const fc = r.fc, has = c => r.conds.includes(c), parts = [];
  if (has("wind")) parts.push(`<span class="wt-c on">${wtSky("wind", fc)}${t("weather.cond.wind", {wind: esc(fc.wind)})}</span>`);
  if (has("precip")) parts.push(`<span class="wt-c on">${wtSky("precip", fc)}${wxKind(fc.short) === "snow"
    ? t("weather.cond.snow", {n: fc.precip_pct}) : t("weather.cond.rain", {n: fc.precip_pct})}</span>`);
  parts.push(`<span class="wt-c${has("cold") ? " on" : ""}">${t("profile.weather.temp", {n: fc.temp_f})}</span>`);
  if (r.roof === "retractable") parts.push(`<span class="wt-c">${t("profile.weather.retractable")}</span>`);
  return `<p class="wt-cond">${parts.join('<span class="wt-dot"> · </span>')}</p>`;
}

/* "QBs about 1.5 fewer points · WRs about 1 fewer": the unit once, on the first. */
function wtFxHTML(effects){
  const items = effects.map((e, i) => {
    const who = wtPosWord(e.pos), args = {who: i ? who : who[0].toUpperCase() + who.slice(1), n: `<b>${wtHalf(Math.abs(e.pts))}</b>`};
    const said = e.pts < 0 ? (i ? t("weather.fx.fewer", args) : t("weather.fx.fewerFirst", args))
      : (i ? t("weather.fx.more", args) : t("weather.fx.moreFirst", args));
    return `<span class="wt-e">${said}</span>`;
  });
  return `<p class="wt-fx">${items.join('<span class="wt-dot">&nbsp;· </span>')}</p>`;
}

/* How old the forecast is, only once it is old enough to doubt. */
function wtAgeHTML(fc){
  const at = Date.parse(fc.as_of || "");
  if (!Number.isFinite(at)) return "";
  const h = Math.floor((Date.now() - at) / 3600e3);
  if (h <= WT_STALE_H) return "";
  return `<p class="wt-age">${h < 48 ? t("weather.age.hours", {h}) : t("weather.age.days", {d: Math.floor(h / 24)})}</p>`;
}

/* The points ff-jarvis already moved in his projection for this game's weather (`wx.adj`),
   "" when it moved none. */
function wtAdjHTML(wx){
  if (!wx || typeof wx.adj !== "number") return "";
  return `<span class="wt-adj" title="${t("weather.hits.adjTip", {n: wtSigned(wx.adj)})}">${wtSigned(wx.adj)}</span>`;
}

/* A book-priced row (`src: "line"`) is never adjusted: the sportsbook line already prices the
   forecast. A blank there reads as zero, so it says "in the odds", and a tap or Enter opens why
   (a native popover, so touch and keyboard both reach it). */
function wtOddsHTML(id){
  return `<button type="button" class="wt-odds" popovertarget="${id}">${t("weather.hits.odds")}</button>
    <span class="wt-tip" popover id="${id}">${t("weather.hits.oddsTip")}</span>`;
}

/* Who it hits: each side's top QB, two WRs and TE (data/weather.js wtHits), by team then position,
   with what is already in his projection. A tap on the name opens his profile; `data-wt` is
   "<game>:<row>". The number sits beside the button, so the odds label can be its own control. */
function wtHitsHTML(hits, gi){
  if (!hits.length) return "";
  const val = hits.map((h, hi) => wtAdjHTML(h.wx) || (h.src === "line" ? wtOddsHTML(`wt-odds-${gi}-${hi}`) : "<span></span>"));
  const head = hits.some(h => wtAdjHTML(h.wx) || h.src === "line") ? `<span>${t("weather.hits.adjHead")}</span>` : "";
  return `<div class="wt-hits"><h3>${t("weather.hits.title")}${head}</h3><ul>${hits.map((h, hi) => `<li><button type="button" class="wt-p" data-wt="${gi}:${hi}">
      <span class="wt-pos">${esc(h.pos)}</span><span class="wt-nm">${esc(nameInitial(h.n))}</span>
      <span class="wt-tm">${esc(h.team)}</span></button>${val[hi]}</li>`).join("")}</ul></div>`;
}

function wtCardHTML(r, gi){
  return `<article class="wt-card${r.done ? " done" : ""}">
    <div class="wt-top"><b class="wt-match">${esc(r.g.away)} @ ${esc(r.g.home)}</b><span class="wt-kick">${wtKickLabel(r)}</span></div>
    ${wtCondHTML(r)}${wtFxHTML(r.effects)}${r.done ? "" : wtAgeHTML(r.fc)}
    ${wtHitsHTML(r.hits, gi)}
  </article>`;
}

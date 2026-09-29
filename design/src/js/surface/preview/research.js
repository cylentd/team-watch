/* ------------------------------------------------------------------
   PREVIEW's research rows (2026-09-29): Injuries, Weather, Rest & travel. Facts only; an effect is
   printed only where a backtest proved it. Weather's effects come from LIVE_WX_HISTORY, the same
   backtest cells and thresholds the Weather view reads (data/wxhistory.js), never numbers of our own.
   Rest and travel have no backtest yet, and the row says so.

   Colour map: --down Out / IR, --amber doubtful / questionable (tags with their word), --sky weather
   that moves scoring, --amber the Short week tag.
------------------------------------------------------------------ */
const pvInjTag = s => ({out: t("preview.inj.out"), ir: t("preview.inj.ir"), d: t("preview.inj.d"), q: t("preview.inj.q")})[s];

function pvInjTeam(team, rows){
  const list = rows.length ? rows.map(r => `<li><span class="pv-tag ${r.s === "ir" ? "out" : r.s}">${pvInjTag(r.s)}</span>${shortName(r.n)} <small>${esc(r.pos)}${
    r.avg != null ? " · " + t("preview.inj.avg", {n: r.avg.toFixed(1)}) : ""}</small></li>`).join("")
    : `<li class="pv-nil">${t("preview.inj.none")}</li>`;
  return `<div><h4 class="pv-team">${esc(team)}</h4><ul class="pv-inj">${list}</ul></div>`;
}

function pvInjRow(g){
  if (!g.inj) return "";
  return pvRow("inj", t("preview.row.inj"), `<div class="pv-two">${pvInjTeam(g.away, g.inj[g.away] || [])}${pvInjTeam(g.home, g.inj[g.home] || [])}</div>`);
}

/* The backtest's proven effects for the conditions this forecast meets, as "Wind 15+ mph: QB -1.46 ...". */
function pvWxEffects(w){
  if (!wtHistOk()) return [];
  const conds = wtConditions({fc: {precip_pct: w.precip, temp_f: w.temp}, mph: w.wind || 0, roof: w.roof});
  const th = LIVE_WX_HISTORY.thresholds || {};
  const name = c => ({wind: t("preview.wx.wind", {n: th.wind_mph}), precip: t("preview.wx.rain", {n: th.precip_pct}),
    cold: t("preview.wx.cold", {n: th.cold_f})})[c];
  return conds.map(c => `<li><b>${name(c)}</b>${LIVE_WX_HISTORY.conditions[c].matters.map(m =>
    `<span>${esc(m.pos)} ${m.mean.toFixed(2)}</span>`).join("")}</li>`);
}

function pvWxRow(g){
  const w = g.wx;
  if (!w) return "";
  const where = g.site && g.site.stadium ? esc(g.site.stadium) + " · " : "";
  const title = t("preview.row.wx") + (where || w.roof ? ` <em>${where}${w.roof ? esc(w.roof) : ""}</em>` : "");
  if (w.roof === "dome" || w.roof === "closed") return pvRow("wx", title, `<p class="pv-nil">${t("preview.wx.covered")}</p>`);
  if (w.temp == null && w.wind == null) return pvRow("wx", title, `<p class="pv-nil">${t("preview.wx.nofc")}</p>`);
  const rain = w.precip != null ? t("preview.wx.pct", {n: w.precip}) : "";
  const fc = [w.temp != null ? `${w.temp}°` : "", w.wind != null ? t("preview.wx.mph", {n: w.wind}) : "", rain].filter(Boolean).join(" · ");
  const eff = pvWxEffects(w);
  const s = wtHistOk() ? LIVE_WX_HISTORY.seasons || [] : [];
  return pvRow("wx", title, `<p class="pv-fc${eff.length ? " moves" : ""}">${fc}${w.sky ? ` <small>${esc(w.sky)}</small>` : ""}</p>
    ${eff.length ? `<ul class="pv-eff">${eff.join("")}</ul><p class="pv-note">${t("preview.wx.unit")}</p>` : `<p class="pv-nil">${t("preview.wx.none")}</p>`}
    ${s.length === 2 ? `<p class="pv-note">${t("preview.wx.src", {from: s[0], to: s[1]})}</p>` : ""}`);
}

/* "13:25" -> "1:25 PM": the body-clock kickoff as the reader's page writes times. */
const pvClock = hm => { const [h, m] = hm.split(":").map(Number); return `${h % 12 || 12}:${String(m).padStart(2, "0")} ${h < 12 ? "AM" : "PM"}`; };

function pvRestLine(team, g){
  const r = (g.rest || {})[team], tr = (g.travel || {})[team], bits = [];
  if (r && r.days != null) bits.push(t("preview.rest.days", {n: r.days}));
  if (r && r.short) bits.push(`<b class="pv-tag short">${t("preview.rest.short")}</b>`);
  if (r && r.bye) bits.push(`<b class="pv-tag bye">${t("preview.rest.bye")}</b>`);
  const z = tr && {n: Math.abs(tr.zones)};
  if (tr && tr.zones) bits.push((tr.zones > 0 ? t("preview.travel.east", z) : t("preview.travel.west", z))
    + (tr.body ? " · " + t("preview.travel.body", {clock: pvClock(tr.body)}) : ""));
  else if (tr && team === g.home && !(g.site && g.site.neutral)) bits.push(t("preview.travel.home"));
  if (tr && tr.miles) bits.push(t("preview.travel.miles", {n: tr.miles.toLocaleString("en-US")}));
  return pvKV(esc(team), bits.join(" · ") || "–");
}

function pvRestRow(g){
  if (!g.rest && !g.travel) return "";
  const site = g.site && g.site.neutral ? `<p class="pv-site">${t("preview.travel.neutral", {where: esc(g.site.stadium || "")})}</p>` : "";
  return pvRow("rest", t("preview.row.rest"), `${site}<div class="pv-kv">${pvRestLine(g.away, g)}${pvRestLine(g.home, g)}</div>
    <p class="pv-note">${t("preview.rest.tested")}</p>`);
}

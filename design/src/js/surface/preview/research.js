/* ------------------------------------------------------------------
   PREVIEW's research rows (2026-09-29): Injuries, Weather, Rest & travel. Facts only; an effect is
   printed only where a backtest proved it. Weather's effects come from LIVE_WX_HISTORY, the same
   backtest cells and thresholds the Weather view reads (data/wxhistory.js), never numbers of our own.
   No footnotes (2026-09-30): rest and travel are facts, and the row prints them bare.

   Colour map: --down Out / IR, --amber doubtful / questionable (tags with their word), --sky weather
   that moves scoring. Short week and Off a bye are plain text (2026-10-06, METHODOLOGY 12.62).
------------------------------------------------------------------ */
const pvInjTag = s => ({out: t("preview.inj.out"), ir: t("preview.inj.ir"), d: t("preview.inj.d"), q: t("preview.inj.q")})[s];

function pvInjTeam(team, rows){
  const list = rows.length ? rows.map(r => `<li><span class="pv-tag ${r.s === "ir" ? "out" : r.s}">${pvInjTag(r.s)}</span>${shortName(r.n)} <small>${esc(r.pos)}${
    r.avg != null ? " · " + t("preview.inj.avg", {n: r.avg.toFixed(1)}) : ""}${
    r.changed ? " · " + t("preview.inj.changed") : ""}</small></li>`).join("")
    : `<li class="pv-nil">${t("preview.inj.none")}</li>`;
  return `<div><h4 class="pv-team">${esc(team)}</h4><ul class="pv-inj" data-testid="preview-injuries">${list}</ul></div>`;
}

function pvInjRow(g){
  if (!g.inj) return "";
  return pvRow("inj", t("preview.row.inj"), `<div class="pv-two">${pvInjTeam(g.away, g.inj[g.away] || [])}${pvInjTeam(g.home, g.inj[g.home] || [])}</div>`);
}

/* Defenders out (2026-10-06): a chip per defense missing starters, in the box score after Injuries. A fact, not a
   call: no row when neither defense is short, none for an earlier week's game (the block is this week's), and none
   once the game has kicked off (it is for setting lineups). */
function pvDsRow(g){
  const views = PV_ARC_G || pvDone(g) ? [] : dsGameViews(LIVE_D_STARTERS, g, LIVE_PREVIEW.week);
  return views.length ? pvRow("ds", t("ds.row"), views.map(v => dsChipHTML(v, LIVE_D_STARTERS.rules, "preview")).join("")) : "";
}

/* The backtest's proven effects for the conditions this forecast meets, as "Wind 15+ mph: QB -1.46 ...". */
function pvWxEffects(w){
  if (!wtHistOk()) return [];
  const conds = wtConditions({fc: {precip_pct: w.precip, temp_f: w.temp}, mph: w.wind || 0, roof: w.roof});
  const th = LIVE_WX_HISTORY.thresholds || {};
  const name = c => ({wind: t("preview.wx.wind", {n: th.wind_mph}), precip: t("preview.wx.rain", {n: th.precip_pct}),
    cold: t("preview.wx.cold", {n: th.cold_f})})[c];
  // Cold carries its failed test in the tooltip (2026-10-06, METHODOLOGY 12.53).
  return conds.map(c => `<li${c === "cold" ? ` title="${t("weather.cond.coldMark")}"` : ""}><b>${name(c)}</b>${LIVE_WX_HISTORY.conditions[c].matters.map(m =>
    `<span>${esc(m.pos)} ${m.mean.toFixed(2)}</span>`).join("")}</li>`);
}

function pvWxRow(g){
  const w = g.wx;
  if (!w) return "";
  const covered = w.roof === "dome" || w.roof === "closed";
  // A roof is an answer, not a gap: the section says "Dome" (or "Roof closed") instead of vanishing, which
  // read as a forecast that failed (2026-10-05, ATL @ NO). The roof is that word, so the title keeps only
  // the stadium. Open air with no forecast yet has nothing to say, so no section (2026-09-30).
  const tag = covered ? "" : w.roof ? esc(w.roof) : "";
  const place = [g.site && g.site.stadium ? esc(g.site.stadium) : "", tag].filter(Boolean).join(" · ");
  const title = t("preview.row.wx") + (place ? ` <em>${place}</em>` : "");
  if (covered) return pvRow("wx", title, `<p class="pv-fc" data-testid="preview-forecast">${w.roof === "dome" ? t("preview.wx.dome") : t("preview.wx.closed")}</p>`);
  if (w.temp == null && w.wind == null) return "";
  const rain = w.precip != null ? t("preview.wx.pct", {n: w.precip}) : "";
  const fc = [w.temp != null ? `${w.temp}°` : "", w.wind != null ? t("preview.wx.mph", {n: w.wind}) : "", rain].filter(Boolean).join(" · ");
  const eff = pvWxEffects(w);
  return pvRow("wx", title, `<p class="pv-fc${eff.length ? " moves" : ""}" data-testid="preview-forecast">${fc}${w.sky ? ` <small>${esc(w.sky)}</small>` : ""}</p>
    ${eff.length ? `<ul class="pv-eff" data-testid="preview-effects">${eff.join("")}</ul>` : ""}`);
}


function pvRestLine(team, g){
  const r = (g.rest || {})[team], tr = (g.travel || {})[team], bits = [];
  if (r && r.days != null) bits.push(t("preview.rest.days", {n: r.days}));
  // Plain text since 2026-10-06 (12.62: rest is priced into the line, 0 of 23 cells beat it): no tag, no colour.
  if (r && r.short) bits.push(`<span data-testid="preview-rest-short">${t("preview.rest.short")}</span>`);
  if (r && r.bye) bits.push(`<span data-testid="preview-rest-bye">${t("preview.rest.bye")}</span>`);
  const z = tr && {n: Math.abs(tr.zones)};
  // The zones and body clock carry METHODOLOGY 12.62's result in the tooltip (2026-10-06).
  if (tr && tr.zones) bits.push(`<span title="${t("preview.travel.mark")}">${(tr.zones > 0 ? t("preview.travel.east", z) : t("preview.travel.west", z))
    + (tr.body ? " · " + t("preview.travel.body", {clock: kickClock(tr.body)}) : "")}</span>`);
  else if (tr && team === g.home && !(g.site && g.site.neutral)) bits.push(t("preview.travel.home"));
  if (tr && tr.miles) bits.push(t("preview.travel.miles", {n: tr.miles.toLocaleString("en-US")}));
  return pvKV(esc(team), bits.join(" · ") || "–");
}

function pvRestRow(g){
  if (!g.rest && !g.travel) return "";
  const site = g.site && g.site.neutral ? `<p class="pv-site">${t("preview.travel.neutral", {where: esc(g.site.stadium || "")})}</p>` : "";
  return pvRow("rest", t("preview.row.rest"), `${site}<div class="pv-kv">${pvRestLine(g.away, g)}${pvRestLine(g.home, g)}</div>`);
}

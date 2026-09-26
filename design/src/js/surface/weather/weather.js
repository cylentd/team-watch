/* ------------------------------------------------------------------
   WEATHER — This week > Weather (2026-09-26). Every game of this week with the forecast at kickoff
   and the reader's own players in it, so he can weigh kickers, receivers and backs himself.

   Facts only: no verdict word, no tilt tag, no good or bad colour. What a condition has done in the
   past is ff-jarvis's backtest, printed as it stands with whether it held (history.js); the reader
   decides. The one ordering (indoors, then by wind) is named as an ordering in its heading.

   Data: data/weather.js wtRows(). The icons are ui/weather.js, shared with the profile and cards.
------------------------------------------------------------------ */
const wtKick = iso => new Date(iso).toLocaleString([], {weekday: "short", hour: "numeric", minute: "2-digit"});

/* How old the forecast is, from its `as_of` against the reader's clock. */
function wtAge(fc){
  const at = Date.parse(fc.as_of || "");
  if (!Number.isFinite(at)) return "";
  const h = Math.max(0, Math.floor((Date.now() - at) / 3600e3));
  return h < 1 ? t("weather.age.new") : h < 48 ? t("weather.age.hours", {h}) : t("weather.age.days", {d: Math.floor(h / 24)});
}

function wtRoof(roof){
  if (roof === "dome") return `${wxIcon("dome")}<span>${t("profile.weather.dome")}</span>`;
  if (roof === "retractable") return `${wxIcon("dome")}<span>${t("weather.roof.retractable")}</span><em>${t("profile.weather.retractable")}</em>`;
  return `${wxIcon("sun")}<span>${roof === "outdoor" ? t("weather.roof.outdoor") : t("weather.roof.unknown")}</span>`;
}

function wtFactsHTML(fc){
  const cell = (icon, v, l) => `<span class="wt-f">${icon}<b>${v}</b><em>${l}</em></span>`;
  const pct = fc.precip_pct === null || fc.precip_pct === undefined ? "—" : t("weather.precip.pct", {n: fc.precip_pct});
  return `<div class="wt-facts">
      ${cell(wxIcon(wxKind(fc.short)), t("profile.weather.temp", {n: fc.temp_f}), esc(fc.short || ""))}
      ${cell(wxIcon("wind"), esc(fc.wind || "—"), fc.wind_dir ? t("profile.weather.windFrom", {dir: esc(fc.wind_dir)}) : t("profile.weather.wind"))}
      ${cell(wxIcon("drop"), pct, t("weather.precip.label"))}
    </div>`;
}

/* The points ff-jarvis already moved in his projection for this game's weather ({adj, cond} on his
   LIVE_PROJECTIONS row), as a small "wx −1.1" note; "" when none. What it means is said in Why. */
function wtAdjHTML(p){
  const row = typeof LIVE_PROJECTIONS !== "undefined" && LIVE_PROJECTIONS && p.slug ? LIVE_PROJECTIONS.players[p.slug] : null;
  const wx = row && row.wx;
  if (!wx || typeof wx.adj !== "number") return "";
  return `<span class="wt-adj" title="${t("weather.mine.adjTip", {n: wtSigned(wx.adj)})}">${t("weather.mine.adj", {n: wtSigned(wx.adj)})}</span>`;
}

/* A player opens his profile; `data-wt` is "<game>:<player>" into wtAll(), rebuilt on the tap. */
function wtMineHTML(mine, gi){
  if (!mine.length) return `<p class="wt-none-mine">${t("weather.mine.none")}</p>`;
  return `<ul class="wt-mine">${mine.map(({p, leagues}, pi) => `<li><button type="button" class="wt-p" data-wt="${gi}:${pi}">
      <span class="wt-pos">${esc(p.pos)}</span><span class="wt-nm">${esc(nameInitial(p.n))}</span>
      ${wtAdjHTML(p) || "<span></span>"}<span class="wt-lg">${leagues.map(esc).join(" · ")}</span></button></li>`).join("")}</ul>`;
}

function wtGameHTML(r, gi){
  // A game already under way has no forecast: LIVE_WEATHER has moved on to the next home kickoff.
  const started = Date.parse(r.g.kickoff) <= Date.now();
  const body = r.fc ? wtFactsHTML(r.fc) + `<div class="wt-age">${wtAge(r.fc)}</div>`
    : r.roof === "dome" ? "" : `<p class="wt-nofc">${started ? t("weather.fc.started") : t("weather.fc.none")}</p>`;
  // History: ff-jarvis's weather backtest for each condition this game meets (history.js). With
  // no backtest file it is "", and no number is ever written into this file by hand.
  const history = wtHistHTML(r);
  return `<article class="wt-game">
    <div class="wt-top"><b class="wt-match">${esc(r.g.away)} @ ${esc(r.g.home)}</b><span class="wt-kick">${wtKick(r.g.kickoff)}</span></div>
    <div class="wt-roof">${wtRoof(r.roof)}</div>
    ${body}${history}
    ${wtMineHTML(r.mine, gi)}
  </article>`;
}

/* Both groups in page order, so a game's index is the same when drawn and when tapped. */
const wtAll = d => d.indoor.concat(d.open);

function wtViewHTML(){
  const d = wtRows();
  if (!wtAll(d).length) return `<div class="wrap"><div class="state-empty" style="min-height:220px">
    <div><b>${t("weather.empty.title")}</b><span>${t("weather.empty.sub")}</span></div></div></div>`;
  const rule = (label, n) => `<div class="rule"><h2>${label}</h2><span class="count">${String(n).padStart(2, "0")}</span><span class="hair"></span></div>`;
  const group = (label, rows, from) => rows.length ? `<section class="wt-sec">${rule(label, rows.length)}
    <div class="wt-grid">${rows.map((r, i) => wtGameHTML(r, from + i)).join("")}</div></section>` : "";
  return `<div class="wrap wt">
    <div class="wt-headline"><h2>${t("weather.head.title", {week: d.week})}</h2><p>${t("weather.head.sub")}</p></div>
    ${group(t("weather.group.indoor"), d.indoor, 0)}
    ${group(t("weather.group.open"), d.open, d.indoor.length)}
    ${wtHistFootHTML()}
  </div>`;
}

function wireWeather(v){
  v.querySelectorAll("[data-wt]").forEach(el => el.addEventListener("click", () => {
    const [gi, pi] = el.dataset.wt.split(":").map(Number);
    const r = wtAll(wtRows())[gi], m = r && r.mine[pi];
    if (m) openProfile(m.p, el);
  }));
}

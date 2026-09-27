/* ------------------------------------------------------------------
   WEATHER — This week > Weather (2026-09-26; reworked the same day to say only what matters).
   A reader setting a lineup on a phone gets, first, the games whose weather moves scoring and what
   it does (card.js); every other game is one compact row; how we know sits in one disclosure at
   the bottom, with the forecast's source. No verdict word about a player, no good or bad colour.

   Data: data/weather.js wtRows(), data/wxhistory.js. Icons: ui/weather.js.
------------------------------------------------------------------ */
const wtKick = iso => new Date(iso).toLocaleString([], {weekday: "short", hour: "numeric", minute: "2-digit"});

/* One compact row: matchup, kickoff, the sky in brief. */
function wtRowHTML(r){
  const fc = r.fc;
  const sky = r.roof === "dome" ? "" : fc ? `${t("profile.weather.temp", {n: fc.temp_f})} · ${esc(fc.wind || "")}`
    : t("weather.row.nofc");
  return `<li class="wt-row"><b class="wt-match">${esc(r.g.away)} @ ${esc(r.g.home)}</b>
    <span class="wt-kick">${wtKick(r.g.kickoff)}</span><span class="wt-rs">${sky}</span></li>`;
}

/* A section rule; the count is said in words ("3 games"), so it never reads as a section number. */
const wtRule = (label, n) => `<div class="rule"><h2>${label}</h2><span class="wt-n">${n === 1 ? t("weather.count.one") : t("weather.count.many", {n})}</span><span class="hair"></span></div>`;

/* "Games where weather lowers scoring", from the sign of every effect on the page. */
function wtMovesTitle(moves){
  const way = wtWay(moves.flatMap(r => r.effects));
  return way === "lower" ? t("weather.moves.lower") : way === "raise" ? t("weather.moves.raise") : t("weather.moves.mixed");
}

function wtRestHTML(label, rows){
  return rows.length ? `<section class="wt-sec">${wtRule(label, rows.length)}<ul class="wt-rows">${rows.map(wtRowHTML).join("")}</ul></section>` : "";
}

/* "Tested with no effect: domes, running backs, and cold weather except for kickers." */
function wtNoneLine(){
  const n = wtNoEffect();
  const cond = c => ({dome: t("weather.how.dome"), wind: t("weather.how.wind"), cold: t("weather.how.cold"), precip: t("weather.how.precip")})[c] || esc(c);
  const pos = p => ({QB: t("weather.how.pos.qb"), RB: t("weather.how.pos.rb"), WR: t("weather.how.pos.wr"),
    TE: t("weather.how.pos.te"), K: t("weather.how.pos.k")})[p] || esc(p);
  const items = n.none.map(cond).concat(n.pos.map(pos), n.kOnly.map(c => t("weather.how.kOnly", {cond: cond(c)})));
  if (!items.length) return "";
  const and = t("weather.how.and"), last = items[items.length - 1];
  const list = items.length === 1 ? last : items.length === 2 ? `${items[0]} ${and} ${last}`
    : `${items.slice(0, -1).join(", ")}, ${and} ${last}`;
  return `<p>${t("weather.how.none", {list})}</p>`;
}

/* The one disclosure: method, what showed nothing, and the forecast's source. */
function wtHowHTML(){
  const s = wtHistOk() ? LIVE_WX_HISTORY.seasons || [] : [];
  const method = wtHistOk() ? `<p>${t("weather.how.method", {from: s[0] || "", to: s[s.length - 1] || ""})}</p>${wtNoneLine()}` : "";
  return `<details class="wt-how"><summary>${t("weather.how.title")}</summary>
    <div class="wt-how-body"><div>${method}<p>${t("weather.how.source")}</p></div></div></details>`;
}

function wtViewHTML(){
  const d = wtRows();
  if (!d.moves.length && !d.indoor.length && !d.open.length && !d.played.length) return `<div class="wrap"><div class="state-empty" style="min-height:220px">
    <div><b>${t("weather.empty.title")}</b><span>${t("weather.empty.sub")}</span></div></div></div>`;
  const moves = d.moves.length
    ? `<section class="wt-sec">${wtRule(wtMovesTitle(d.moves), d.moves.length)}
        <div class="wt-grid">${d.moves.map(wtCardHTML).join("")}</div></section>`
    : `<p class="wt-calm">${t("weather.moves.none")}</p>`;
  const played = d.played.length
    ? `<p class="wt-played">${t("weather.played", {list: d.played.map(r => `${esc(r.g.away)} @ ${esc(r.g.home)}`).join(", ")})}</p>` : "";
  return `<div class="wrap wt">
    <h2 class="wt-title">${t("weather.head.title", {week: d.week})}</h2>
    ${moves}
    <div class="wt-rest">${wtRestHTML(t("weather.group.open"), d.open)}${wtRestHTML(t("weather.group.indoor"), d.indoor)}</div>
    ${played}${wtHowHTML()}
  </div>`;
}

function wireWeather(v){
  v.querySelectorAll("[data-wt]").forEach(el => el.addEventListener("click", () => {
    const [gi, pi] = el.dataset.wt.split(":").map(Number);
    const r = wtRows().moves[gi], h = r && r.hits[pi];
    if (h) openProfile({n: h.n, pos: h.pos, team: h.team, slug: h.slug}, el);
  }));
}

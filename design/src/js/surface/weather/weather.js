/* ------------------------------------------------------------------
   WEATHER — This week > Weather (2026-09-26; reworked the same day to say only what matters).
   A reader setting a lineup on a phone gets, first, the games whose weather moves scoring and what
   it does (card.js); every other game is one compact row. No verdict word about a player, no good
   or bad colour. No method note or "How we know" (2026-09-30, David: show, don't tell).

   Data: data/weather.js wtRows(), data/wxhistory.js. Icons: ui/weather.js.
------------------------------------------------------------------ */
const wtKick = iso => new Date(iso).toLocaleString([], {weekday: "short", hour: "numeric", minute: "2-digit"});
/* A game already under way or over says so where its kickoff time was: the card is dimmed, not gone. */
const wtKickLabel = r => r.done ? t("weather.done", {kick: wtKick(r.g.kickoff)}) : wtKick(r.g.kickoff);

/* One compact row: matchup, kickoff, the sky in brief. */
function wtRowHTML(r){
  const fc = r.fc;
  const sky = r.roof === "dome" ? "" : fc ? `${t("profile.weather.temp", {n: fc.temp_f})} · ${esc(fc.wind || "")}`
    : r.done ? t("weather.row.nosaved") : t("weather.row.nofc");
  return `<li class="wt-row${r.done ? " done" : ""}"><b class="wt-match">${esc(r.g.away)} @ ${esc(r.g.home)}</b>
    <span class="wt-kick">${wtKickLabel(r)}</span><span class="wt-rs">${sky}</span></li>`;
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

function wtViewHTML(){
  const d = wtRows();
  if (!d.moves.length && !d.indoor.length && !d.open.length) return `<div class="wrap"><div class="state-empty" style="min-height:220px">
    <div><b>${t("weather.empty.title")}</b><span>${t("weather.empty.sub")}</span></div></div></div>`;
  const moves = d.moves.length
    ? `<section class="wt-sec">${wtRule(wtMovesTitle(d.moves), d.moves.length)}
        <div class="wt-grid">${d.moves.map(wtCardHTML).join("")}</div></section>`
    : `<p class="wt-calm">${t("weather.moves.none")}</p>`;
  return `<div class="wrap wt">
    <h2 class="wt-title">${t("weather.head.title", {week: d.week})}</h2>
    ${moves}
    <div class="wt-rest">${wtRestHTML(t("weather.group.open"), d.open)}${wtRestHTML(t("weather.group.indoor"), d.indoor)}</div>
  </div>`;
}

function wireWeather(v){
  v.querySelectorAll("[data-wt]").forEach(el => el.addEventListener("click", () => {
    const [gi, pi] = el.dataset.wt.split(":").map(Number);
    const r = wtRows().moves[gi], h = r && r.hits[pi];
    if (h) openProfile({n: h.n, pos: h.pos, team: h.team, slug: h.slug}, el);
  }));
}

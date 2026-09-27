/* ============================== LEAGUE: THE BACK PAGE (Yahoo) ==============================
   2026-09-27, storyboard https://claude.ai/artifact/LBKkjFWgJ1rLZGrKtQ1Fn3. The Yahoo week as a sports
   tabloid's back page: Claude's headline and dek (ff-jarvis league_roast), every score on one line,
   every game as a card with its punchline (slate.js), then six superlatives and this week's grudge
   (tape.js). The all-time book is its own tab, Records (records.js). ESPN keeps recap.js: it is
   David's work league, not the one his friends read. */

/* The week the back page last drew, per league: a new one arrives with motion (STYLE.md: data
   arriving is the one thing that moves on its own); redrawing the same week does not. */
let LG_DRAWN = null;

function lgMastHTML(w){
  return `<header class="bp-mast">
    <p class="bp-kick">${t("league.back.kick", {n: w.week})}</p>
    ${w.head ? `<h2 class="bp-hl">${esc(w.head)}</h2>` : ""}
    ${w.dek ? `<p class="bp-dek">${esc(w.dek)}</p>` : ""}
  </header>`;
}

/* Every score of the week on one line, low to high: green won its game, red lost it, the team on
   screen ringed. Under it, where that team's score ranked, so a score reads against the week. */
function lgStripHTML(w, id){
  const pts = w.games.flatMap(g => [[g.a, g.ap, g.win === "home"], [g.b, g.bp, g.win === "away"]]);
  const vals = pts.map(p => p[1]), lo = Math.min(...vals), hi = Math.max(...vals), span = hi - lo || 1;
  const dots = pts.sort((x, y) => x[1] - y[1]).map(([tid, v, won], i) =>
    `<i class="bp-dot ${won ? "w" : "l"}${tid === id ? " me" : ""}" style="left:${(100 * (v - lo) / span).toFixed(1)}%;--i:${i}"></i>`).join("");
  const mine = pts.find(p => p[0] === id);
  const rank = mine ? [...vals].sort((x, y) => y - x).indexOf(mine[1]) + 1 : 0;
  return `<div class="bp-strip">
    <div class="bp-axis" role="img" aria-label="${t("league.back.stripAria", {n: vals.length, lo: lgPts(lo), hi: lgPts(hi)})}">${dots}</div>
    <div class="bp-ends"><span>${lgPts(lo)}</span><span>${lgPts(hi)}</span></div>
    ${mine ? `<p class="bp-rank">${t("league.back.rank", {team: lgName(id), v: lgPts(mine[1]), r: rank, n: vals.length})}</p>` : ""}
  </div>`;
}

/* Six superlatives, two to a row at every width. Each label spelled out for assemble.py --check. */
const lgSupLabel = k => ({top: t("league.sup.top"), low: t("league.sup.low"), unluck: t("league.sup.unluck"),
  luck: t("league.sup.luck"), bench: t("league.sup.bench"), close: t("league.sup.close")})[k];

function lgSupHTML(k, a, i){
  if (!a) return "";
  const note = {unluck: t("league.sup.unluckNote"), luck: t("league.sup.luckNote"),
    bench: a.name ? t("league.sup.benchNote", {name: esc(nameInitial(a.name))}) : "",
    close: t("league.sup.closeNote", {opp: lgName(a.opp)})}[k] || "";
  return `<div class="bp-su" style="--i:${i}"><span class="bp-suk">${lgSupLabel(k)}</span>
    <span class="bp-sut">${lgName(a.id)}</span><span class="bp-suv">${k === "close" ? "+" : ""}${lgPts(a.v)}</span>
    ${note ? `<span class="bp-sud">${note}</span>` : ""}</div>`;
}

function lgBackWeekHTML(id){
  const w = lgWeek();
  if (!w) return `<section class="lg-sec bp-week"><p class="lg-none">${t("league.empty")}</p></section>`;
  const key = `${LG.league}|${w.week}`, arrive = key !== LG_DRAWN;
  LG_DRAWN = key;
  const chips = LG.weeks.map(x => `<button class="chip" data-lgweek="${x.week}" aria-pressed="${x === w}">${t("league.recap.wk", {n: x.week})}</button>`).join("");
  const sups = ["top", "low", "unluck", "luck", "bench", "close"].map((k, i) => lgSupHTML(k, w.awards[k], i)).join("");
  return `<section class="lg-sec bp-week${arrive ? " bp-in" : ""}" aria-label="${t("league.recap.aria")}">
    <div class="setrow lg-weeks" role="group" aria-label="${t("league.recap.weeks")}">${chips}</div>
    ${lgMastHTML(w)}${lgStripHTML(w, id)}
    <h3 class="bp-hd">${t("league.back.slate")}<span>${t("league.back.games", {n: w.games.length})}</span></h3>
    <div class="bp-slate">${lgSlateHTML(w, id)}</div>
    <h3 class="bp-hd">${t("league.back.sups")}</h3>
    <div class="bp-sups">${sups}</div>
  </section>`;
}

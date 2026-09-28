/* ============================== THIS WEEK > LEAGUE (Yahoo) ==============================
   2026-09-27, storyboards https://claude.ai/artifact/LBKkjFWgJ1rLZGrKtQ1Fn3 and
   https://claude.ai/artifact/5vFc7Js5EsqJY3EmxgQc84. The league's week as a sports tabloid's back page,
   the same page for every reader whatever team is picked: Claude's headline and dek (ff-jarvis
   league_roast), every score on one line, the standings, every game in story order (slate.js), six
   superlatives, then next week's biggest grudge (tape.js). The team on screen gets its own week in
   My teams > My recap (myrecap.js). ESPN keeps recap.js: it is David's work league. */

/* The week the back page last drew, per league and page: a new one arrives with motion (STYLE.md:
   data arriving is the one thing that moves on its own); redrawing the same week does not. */
let LG_DRAWN = null;

/* The league-wide pages (League, Records) always show the Yahoo league, whatever team is on screen. */
function lgUseYahoo(){
  if (LG !== LGS.yahoo){ LG = LGS.yahoo; LG_WEEK = null; LG_OPEN = null; }
  return LG;
}

/* A league-wide page's own head: the league, not a team, so no team switch. */
const lgPageHead = sub => `<header class="lgp"><h1>${esc(LG.league)}</h1><p>${sub}</p></header>`;

const lgWeekChips = w => `<div class="setrow lg-weeks" role="group" aria-label="${t("league.recap.weeks")}">${
  LG.weeks.map(x => `<button class="chip" data-lgweek="${x.week}" aria-pressed="${x === w}">${t("league.recap.wk", {n: x.week})}</button>`).join("")}</div>`;

/* True once per new (page, league, week): the section that draws it gets the arrival class. */
function lgArrive(page, w){
  const key = `${page}|${LG.league}|${w.week}`, fresh = key !== LG_DRAWN;
  LG_DRAWN = key;
  return fresh;
}

function lgMastHTML(w){
  return `<header class="bp-mast">
    <p class="bp-kick">${t("league.back.kick", {n: w.week})}</p>
    ${w.head ? `<h2 class="bp-hl">${esc(w.head)}</h2>` : ""}
    ${w.dek ? `<p class="bp-dek">${esc(w.dek)}</p>` : ""}
  </header>`;
}

/* Every score of the week on one line, low to high: green won its game, red lost it; `id`, when given
   (My recap), is ringed. */
function lgStripHTML(w, id){
  const pts = w.games.flatMap(g => [[g.a, g.ap, g.win === "home"], [g.b, g.bp, g.win === "away"]]);
  const vals = pts.map(p => p[1]), lo = Math.min(...vals), hi = Math.max(...vals), span = hi - lo || 1;
  const dots = pts.sort((x, y) => x[1] - y[1]).map(([tid, v, won], i) =>
    `<i class="bp-dot ${won ? "w" : "l"}${tid === id ? " me" : ""}" style="left:${(100 * (v - lo) / span).toFixed(1)}%;--i:${i}"></i>`).join("");
  return `<div class="bp-strip">
    <div class="bp-axis" role="img" aria-label="${t("league.back.stripAria", {n: vals.length, lo: lgPts(lo), hi: lgPts(hi)})}">${dots}</div>
    <div class="bp-ends"><span>${lgPts(lo)}</span><span>${lgPts(hi)}</span></div>
  </div>`;
}

/* Standings and a power ranking in one table: the record sets the order, points sit beside it, and a
   tag shows only where the two disagree by 2+ places (design/league_back.py add_standings). */
function lgTableHTML(w){
  const move = m => m > 0 ? `<span class="st-m up">${t("league.table.up", {n: m})}</span>`
    : m < 0 ? `<span class="st-m dn">${t("league.table.down", {n: -m})}</span>` : `<span class="st-m">–</span>`;
  const tag = x => x === "lucky" ? `<small class="st-tag lucky">${t("league.table.lucky")}</small>`
    : x === "robbed" ? `<small class="st-tag robbed">${t("league.table.robbed")}</small>` : "";
  const rows = w.table.map((r, i) => `<li><span class="st-n">${i + 1}</span><span class="st-t"><b>${lgName(r.id)}</b>${tag(r.tag)}</span>
    <span class="st-r">${r.t ? `${r.w}–${r.l}–${r.t}` : `${r.w}–${r.l}`}</span><span class="st-pf">${lgPts(r.pf)}</span>${move(r.move)}</li>`).join("");
  return `<h3 class="bp-hd">${t("league.table.title")}<span>${t("league.table.after", {n: w.week})}</span></h3>
    <ol class="st" aria-label="${t("league.table.title")}"><li class="st-h" aria-hidden="true"><span></span><span>${t("league.table.team")}</span>
      <span>${t("league.table.rec")}</span><span>${t("league.table.pf")}</span><span>${t("league.table.move")}</span></li>${rows}</ol>`;
}

/* Six superlatives as the back page's stamps, two to a row at every width: the award in its colour
   (green a good week, red a bad one, amber a bench mistake), the number, the team, and one line of
   proof. A close game is a nail-biter only under 10 points. Each key spelled out for assemble.py --check. */
const LG_NAILBITER = 10;
const lgSupTone = {top: "g", luck: "g", low: "r", unluck: "r", bench: "a", close: "n"};

function lgSupLabel(k, a){
  if (k === "close") return a.v < LG_NAILBITER ? t("league.sup.close") : t("league.sup.closest");
  return {top: t("league.sup.top"), low: t("league.sup.low"), unluck: t("league.sup.unluck"),
    luck: t("league.sup.luck"), bench: t("league.sup.bench")}[k];
}

/* The proof line: numbers in <b>, so the eye lands on them. */
function lgSupProof(k, a){
  const b = v => `<b>${lgPts(v)}</b>`, opp = a.opp != null ? lgName(a.opp) : "";
  const vs = () => a.m >= 0 ? t("league.sup.beat", {opp, m: b(a.m)}) : t("league.sup.lostTo", {opp, m: b(-a.m)});
  switch (k){
    case "top": case "low": return vs();
    case "luck": return t("league.sup.luckWhy", {rank: ordinal(a.rank), of: a.of, m: b(a.m)});
    case "unluck": return t("league.sup.unluckWhy", {rank: ordinal(a.rank), of: a.of, m: b(-a.m)});
    case "close": return t("league.sup.closeWhy", {p: b(a.p), opp, op: b(a.op)});
    case "bench": return a.started ? t("league.sup.benchWhy", {started: esc(nameInitial(a.started)), sp: b(a.sp),
      name: esc(nameInitial(a.name)), bp: b(a.bp)}) : "";
  }
  return "";
}

function lgSupHTML(k, a, i){
  if (!a) return "";
  const v = k === "bench" ? `−${lgPts(a.v)}` : k === "close" ? `+${lgPts(a.v)}` : lgPts(a.v);
  const proof = lgSupProof(k, a);
  return `<div class="bp-su" style="--i:${i}"><span class="bp-suk ${lgSupTone[k]}">${lgSupLabel(k, a)}</span>
    <span class="bp-suv">${v}</span><span class="bp-sut">${lgName(a.id)}</span>
    ${proof ? `<span class="bp-sud">${proof}</span>` : ""}</div>`;
}

/* The week section: redrawn whole by a week chip (wireLeague). */
function lgBackWeekHTML(){
  const w = lgWeek();
  if (!w) return `<section class="lg-sec bp-week"><p class="lg-none">${t("league.empty")}</p></section>`;
  const sups = ["top", "low", "unluck", "luck", "bench", "close"].map((k, i) => lgSupHTML(k, w.awards[k], i)).join("");
  return `<section class="lg-sec bp-week${lgArrive("league", w) ? " bp-in" : ""}" aria-label="${t("league.recap.aria")}">
    ${lgWeekChips(w)}${lgMastHTML(w)}${lgStripHTML(w, null)}
    ${lgTableHTML(w)}
    <h3 class="bp-hd">${t("league.back.slate")}<span>${t("league.back.games", {n: w.games.length})}</span></h3>
    <div class="bp-slate">${lgSlateHTML(w, null)}</div>
    <h3 class="bp-hd">${t("league.back.sups")}</h3>
    <div class="bp-sups">${sups}</div>
  </section>`;
}

/* This week > League: the head, the week, then next week's biggest grudge beside it on a desktop. */
function lgLeaguePageHTML(){
  if (!lgUseYahoo()) return `<div class="wrap"><p class="lg-none">${t("league.none")}</p></div>`;
  const g = LG.grudge;
  return `<div class="wrap">${lgPageHead(t("league.page.sub", {y: LG.since}))}<div class="lg bp">
    <div class="lg-col">${lgBackWeekHTML()}</div>
    <div class="lg-col">${g ? lgPairGrudgeHTML(g.a, g.b, t("league.grudge.next"), null) : ""}${(LG.classified || []).map(lgClassifiedHTML).join("")}</div>
  </div></div>`;
}

function wireLeaguePage(v){ wireLeague(v, null, lgBackWeekHTML); }

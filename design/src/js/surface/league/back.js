/* ============================== THIS WEEK > LEAGUE (Yahoo) ==============================
   2026-09-27, storyboard https://claude.ai/artifact/5Sj3BRZqyfaVWkvCXCjgFV (it replaced a slate of six
   equal cards, a dot strip and a power-ranking table, which ran 3.3 screens on a desktop). The league's
   week as a newspaper back page, the same for every reader whatever team is picked: Claude's headline
   and dek (ff-jarvis league_roast), the lead story and the briefs (lead.js), the grudges (tape.js), the
   standings in agate, six superlatives. The team on screen gets its own week in My teams > My recap
   (myrecap.js). ESPN keeps recap.js: it is David's work league. */

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

/* The masthead: the league and the week in the kicker, the week chips beside it, the headline, the dek. */
function lgMastHTML(w){
  return `<header class="bp-mast bp2-mast">
    <p class="bp-kick">${t("league.back.kick", {league: esc(LG.league), n: w.week})}</p>
    ${lgWeekChips(w)}
    ${w.head ? `<h2 class="bp-hl">${esc(w.head)}</h2>` : ""}
    ${w.dek ? `<p class="bp-dek">${esc(w.dek)}</p>` : ""}
  </header>`;
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
  const b = v => `<b>${lgPts(v)}</b>`, opp = a.opp != null ? lgMgr(a.opp) : "";
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
    <span class="bp-suv">${v}</span><span class="bp-sut">${lgMgr(a.id)}</span>
    ${proof ? `<span class="bp-sud">${proof}</span>` : ""}</div>`;
}

/* The whole back page for the week on screen, redrawn whole by a week chip (wireLeague): the masthead;
   the lead with the grudges and the standings under it; the briefs beside it; the superlatives along
   the bottom. On a 1440x900 screen it all ends above the fold (test_render). */
function lgBackWeekHTML(){
  const w = lgWeek();
  if (!w) return `<section class="lg-sec bp2"><p class="lg-none">${t("league.empty")}</p></section>`;
  const sups = ["top", "low", "unluck", "luck", "bench", "close"].map((k, i) => lgSupHTML(k, w.awards[k], i)).join("");
  const g = LG.grudge;
  return `<section class="lg-sec bp2${lgArrive("league", w) ? " bp-in" : ""}" aria-label="${t("league.recap.aria")}">
    ${lgMastHTML(w)}
    <div class="bp2-main">
      ${lgLeadHTML(w)}
      <div class="bp2-under">
        ${g ? lgPairGrudgeHTML(g.a, g.b, t("league.grudge.next"), null) : ""}
        ${(LG.classified || []).map(lgClassifiedHTML).join("")}
        ${lgAgateHTML(w, null)}
      </div>
    </div>
    ${lgBriefsHTML(w)}
    <div class="bp-sups bp2-sups" aria-label="${t("league.back.sups")}">${sups}</div>
  </section>`;
}

/* This week > League: the back page, no page head (the league's name is in the kicker). */
function lgLeaguePageHTML(){
  if (!lgUseYahoo()) return `<div class="wrap"><p class="lg-none">${t("league.none")}</p></div>`;
  return `<div class="wrap"><div class="lg lg-one">${lgBackWeekHTML()}</div></div>`;
}

function wireLeaguePage(v){ wireLeague(v, null, lgBackWeekHTML); }

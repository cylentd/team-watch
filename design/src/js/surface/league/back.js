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

/* The league-wide pages (Recap, Records, Trades) show the Yahoo league of the team on screen (data/league.js
   lgLeagueKey; the first Yahoo league when that team is ESPN's or none). */
function lgUsePicked(){
  const L = LGS[lgLeagueKey()] || null;
  if (LG !== L){ LG = L; LG_WEEK = null; LG_OPEN = null; }
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

/* The masthead: the week in the kicker, the week chips beside it. The league's name left the kicker on
   2026-10-05: the League team line right above it already says it (switch.js). No headline since
   2026-09-27 (it told the lead game's story a second time, so the lead's joke is the page's one
   headline, lead.js), and no dek since the same evening: without a headline it read as a stray
   sentence, and it retold what the lead and the briefs already say. The roast still writes both. */
function lgMastHTML(w){
  return `<header class="bp-mast bp2-mast">
    <p class="bp-kick">${t("league.back.kick", {n: w.week})}</p>
    ${lgWeekChips(w)}
  </header>`;
}

/* Streaks going into next week, across seasons (league_back.add_streaks): the two longest winning runs
   and the two longest losing ones, two games or more. It took the Classified grudge's place on
   2026-09-27. */
const LG_STREAK_MIN = 2;

function lgStreaksHTML(w){
  const all = (w.streaks || []).filter(r => r.n >= LG_STREAK_MIN);
  const rows = [...all.filter(r => r.w).slice(0, 2), ...all.filter(r => !r.w).slice(0, 2)];
  if (!rows.length) return "";
  const row = r => `<li><span class="bp2-sk ${r.w ? "hot" : "cold"}">${r.w ? t("league.streak.w", {n: r.n}) : t("league.streak.l", {n: r.n})}</span>
    <b>${lgMgr(r.id)}</b><small>${t("league.streak.since", {y: r.y, wk: r.wk})}</small></li>`;
  return `<section class="lg-sec bp2-streaks" aria-label="${t("league.streak.title")}">
    <h3 class="bp-hd">${t("league.streak.title")}<span>${t("league.streak.sub", {n: w.week + 1})}</span></h3>
    <ul>${rows.map(row).join("")}</ul>
  </section>`;
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
function lgBackWeekHTML(id){
  const w = lgWeek();
  if (!w) return `<section class="lg-sec bp2"><p class="lg-none">${t("league.empty")}</p></section>`;
  const sups = ["top", "low", "unluck", "luck", "bench", "close"].map((k, i) => lgSupHTML(k, w.awards[k], i)).join("");
  const g = LG.grudge;
  // The reader's own team (2026-10-05, Recap merged with My recap): his game first, under the masthead,
  // then his grudge and his lines in the record book after the league's pages.
  return `<section class="lg-sec bp2${id ? " has-mine" : ""}${lgArrive("league", w) ? " bp-in" : ""}" aria-label="${t("league.recap.aria")}">
    ${lgMastHTML(w)}
    ${id ? `<div class="bp2-mine">${lgMineWeekHTML(w, id)}</div>` : ""}
    <div class="bp2-main">
      ${lgLeadHTML(w)}
      <div class="bp2-under">
        ${g ? lgPairGrudgeHTML(g.a, g.b, t("league.grudge.next"), null) : ""}
        ${lgStreaksHTML(w)}
        ${lgAgateHTML(w, null)}
      </div>
    </div>
    ${lgBriefsHTML(w)}
    <div class="bp-sups bp2-sups" aria-label="${t("league.back.sups")}">${sups}</div>
    ${id ? `<div class="bp2-you">${lgGrudgeHTML(id)}${lgMyBookHTML(id)}</div>` : ""}
  </section>`;
}

/* The reader's own team in the league on screen, or null: none picked, or a connected league's team. */
const lgMineId = () => (lgMine() && lgIdOf(lgMine())) || null;

/* League > Recap (leaf `recap`): the league of the team on screen (data/league.js lgFocusKey), the chip
   above it. A Yahoo league gets the back page, the same for every reader but with the reader's own game
   first; an ESPN league keeps its plain recap, rivalry and history (league.js: David's work league). */
function lgRecapPageHTML(){
  const f = lgFocusKey(), L = f && LGS[f];
  if (!L) return `<div class="wrap">${lgChipHTML()}<p class="lg-none">${t("league.none")}</p></div>`;
  if (TEAMS[f].site !== "yahoo") return lgEspnPageHTML(f);
  lgUsePicked();
  return `<div class="wrap" style="--lg-tint:${lgTint()}">${lgChipHTML()}<div class="lg lg-one">${lgBackWeekHTML(lgMineId())}</div></div>`;
}

function wireRecapPage(v){
  const f = lgFocusKey();
  if (f && LGS[f] && TEAMS[f].site !== "yahoo") return wireEspnPage(v, f);
  wireLeague(v, lgMineId(), () => lgBackWeekHTML(lgMineId()));
  wireLgChip(v);
}

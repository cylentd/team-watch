/* ============================== LEAGUE > RECAP (Yahoo): DIRECTION B ==============================
   2026-10-06, plan ~/.claude/plans/2026-10-06-recap-b.md (storyboard https://claude.ai/artifact/4GGAd3Xvk4sh8Sp2ktkDMU).
   One page, two labelled sections, the week stepper over both. YOUR GAME first (myrecap.js: the result,
   the score, three stats, three disclosures), then LEAGUE: Claude's headline and dek, the lead (lead.js),
   every other game as one row with its award tags, the standings with their streaks, the biggest grudge.
   LEAGUE is the same for every reader, because readers screenshot it or Share it to the league: nothing in
   it reads which team is picked. It was a newspaper back page (2026-09-27) with six superlative cards, a
   Streaks block and a stamp on every brief; each award is now a tag on the game it belongs to. ESPN keeps
   recap.js: it is David's work league. */

/* The week the page last drew, per league and page: a new one arrives with motion (STYLE.md: data arriving
   is the one thing that moves on its own); redrawing the same week does not. */
let LG_DRAWN = null;

/* The league-wide pages (Recap, Records, Trades) show the Yahoo league of the team on screen (data/league.js
   lgLeagueKey; the first Yahoo league when that team is ESPN's or none). */
function lgUsePicked(){
  const L = LGS[lgLeagueKey()] || null;
  if (LG !== L){ LG = L; LG_WEEK = null; }
  return LG;
}

/* A league-wide page's own head: the league, not a team, so no team switch. */
const lgPageHead = sub => `<header class="lgp"><h1>${esc(LG.league)}</h1><p>${sub}</p></header>`;

/* True once per new (page, league, week): the section that draws it gets the arrival class. */
function lgArrive(page, w){
  const key = `${page}|${LG.league}|${w.week}`, fresh = key !== LG_DRAWN;
  LG_DRAWN = key;
  return fresh;
}

/* ‹ Week 4 Final ›: it holds 17 weeks where chips held ~6. A button asks for its week by data-lgweek, as a
   chip did (wireLeague); the first week has no back and the last no forward, so each end is disabled. */
function lgStepHTML(w){
  const nums = LG.weeks.map(x => x.week), i = nums.indexOf(w.week);
  const b = (cls, to, glyph, label) => to == null
    ? `<button type="button" class="lg-step-b ${cls}" disabled aria-label="${label}">${glyph}</button>`
    : `<button type="button" class="lg-step-b ${cls}" data-lgweek="${to}" aria-label="${label}">${glyph}</button>`;
  return `<nav class="lg-step" aria-label="${t("league.step.aria")}">
    ${b("lg-step-prev", i > 0 ? nums[i - 1] : null, "‹", t("league.step.prev"))}
    <span class="lg-step-t">${t("league.step.wk", {n: w.week})}<small>${t("league.step.final")}</small></span>
    ${b("lg-step-next", i < nums.length - 1 ? nums[i + 1] : null, "›", t("league.step.next"))}
  </nav>`;
}

/* The awards, as tags on the game they belong to: green a good week, red a bad one, amber a bench mistake,
   neutral a close game. A close game is a nail-biter only under 10 points. Each key is spelled out for
   assemble.py --check. */
const LG_NAILBITER = 10;
const lgSupTone = {top: "g", luck: "g", low: "r", unluck: "r", bench: "a", close: "x"};
const LG_TAG_ORDER = ["top", "low", "unluck", "luck", "bench", "close"];
const LG_TAGS_MAX = 2;

function lgSupLabel(k, a){
  if (k === "close") return a.v < LG_NAILBITER ? t("league.sup.close") : t("league.sup.closest");
  return {top: t("league.sup.top"), low: t("league.sup.low"), unluck: t("league.sup.unluck"),
    luck: t("league.sup.luck"), bench: t("league.sup.bench")}[k];
}

/* The tags of one game, at most two, [{k, label, tone, id}]: the awards whose team plays in it, in the
   priority top, low, unluck, luck, bench, close. The Nail-biter is always on the week's closest game
   (league_recap.awards), so close keeps one of the two places and the other is the top priority left.
   share.js reads this too: keep the name and the shape. */
function lgGameTags(w, g){
  const all = LG_TAG_ORDER.map(k => {
    const a = (w.awards || {})[k];
    return a && (a.id === g.a || a.id === g.b) ? {k, label: lgSupLabel(k, a), tone: lgSupTone[k], id: a.id} : null;
  }).filter(Boolean);
  const close = all.find(x => x.k === "close");
  return close ? [...all.filter(x => x !== close).slice(0, LG_TAGS_MAX - 1), close] : all.slice(0, LG_TAGS_MAX);
}

/* The week's games in the order the page lists them: the lead, then the biggest margin first. */
function lgGamesInOrder(w){
  const lead = w.games.find(x => lgKey(x) === w.lead) || w.games[0], margin = g => Math.abs(g.ap - g.bp);
  return [lead, ...w.games.filter(g => g !== lead).sort((x, y) => margin(y) - margin(x))];
}

const LG_SHARE_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12M7 8l5-5 5 5"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg>`;

/* The LEAGUE section: the same for every reader, so it takes the week and nothing about who is reading. */
function lgLeagueHTML(w){
  const [lead, ...rest] = lgGamesInOrder(w), g = LG.grudge, row = (x, i) => lgRowHTML(w, x, i);
  return `<section class="lg-league" aria-label="${t("league.lg.kick")}">
    <header class="lg-lhd">
      <p class="lg-kick">${t("league.lg.kick")}<b>${esc(LG.league)}</b></p>
      <button type="button" class="lg-share" data-lgshare>${LG_SHARE_ICON}<span class="lg-share-t">${t("league.share.btn")}</span></button>
    </header>
    <div class="lg-games">
      ${lgLeadHTML(w, lead)}
      ${w.head && w.dek ? `<p class="lg-dek">${esc(w.dek)}</p>` : ""}
      <div class="lg-gr">${rest.map(row).join("")}</div>
    </div>
    <div class="lg-after">
      ${lgAgateHTML(w)}
      ${lgLuckHTML(w)}
      ${g ? lgPairGrudgeHTML(g.a, g.b, t("league.grudge.biggest")) : ""}
    </div>
  </section>`;
}

/* The whole Recap for the week on screen, redrawn whole by the stepper (wireLeague). */
function lgBackWeekHTML(id){
  const w = lgWeek();
  if (!w) return `<section class="lg-sec bp2"><p class="lg-none">${t("league.empty")}</p></section>`;
  return `<section class="lg-sec bp2${lgArrive("league", w) ? " bp-in" : ""}" data-lgroot aria-label="${t("league.recap.aria")}">
    ${lgStepHTML(w)}
    ${id ? lgMineWeekHTML(w, id) : ""}
    ${lgLeagueHTML(w)}
  </section>`;
}

/* The reader's own team in the league on screen, or null: none picked, or a connected league's team. */
const lgMineId = () => (lgMine() && lgIdOf(lgMine())) || null;

/* League > Recap (leaf `recap`): the league of the team on screen (data/league.js lgFocusKey), the chip
   above it. A Yahoo league gets this page, the reader's own game first; an ESPN league keeps its plain
   recap, rivalry and history (league.js: David's work league). */
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
  wireLeague(v, () => lgBackWeekHTML(lgMineId()));
  wireLgChip(v);
}

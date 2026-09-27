/* ============================== LEAGUE: RECORD BOOK (Yahoo back page) ==============================
   The league's all-time records as two lists, the Hall of Fame and the Hall of Shame, plus every
   champion, under three tabs. Fixed lists in a fixed order (design/league_back.py book()); the team
   on screen is lit wherever it appears, Shame included. */

/* The tab on screen: "fame", "shame" or "champs". */
let LG_BOOK = "fame";

/* The id of the team on screen, for lighting its rows; set by leagueHTML. */
let LG_ME = null;

/* Every label and detail spelled out, one copy key each (assemble.py --check reads literal lookups). */
function lgBookRow(f){
  const at = {v: lgPts(f.v), y: f.y, wk: f.wk, n: f.n, opp: lgWho(f.opp, f.oppname), w: f.w, l: f.l};
  const R = {
    high: [t("league.book.high"), at.v, t("league.book.when", at)],
    blow: [t("league.book.blow"), `+${at.v}`, t("league.book.over", at)],
    streak: [t("league.book.streak"), f.n, t("league.book.season", at)],
    titles: [t("league.book.titles"), f.n, ""],
    pf: [t("league.book.pf"), at.v, t("league.book.season", at)],
    bestrec: [t("league.book.bestrec"), `${f.w}–${f.l}`, t("league.book.alltime")],
    low: [t("league.book.low"), at.v, t("league.book.when", at)],
    robbed: [t("league.book.robbed"), at.v, t("league.book.lostAnyway", at)],
    stole: [t("league.book.stole"), at.v, t("league.book.wonAnyway", at)],
    lstreak: [t("league.book.lstreak"), f.n, t("league.book.season", at)],
    worstrec: [t("league.book.worstrec"), `${f.w}–${f.l}`, t("league.book.alltime")],
    lasts: [t("league.book.lasts"), f.n, ""],
  }[f.k];
  if (!R) return "";
  const ids = f.ids || [f.id];
  const who = f.ids ? f.ids.map(lgName).join(", ") : lgWho(f.id, f.name);
  const me = ids.includes(LG_ME);
  return `<li${me ? ' class="me"' : ""}><span class="bp-rk">${R[0]}</span><span class="bp-rt">${who}</span>
    <span class="bp-rv">${R[1]}</span>${R[2] ? `<span class="bp-rd">${R[2]}</span>` : ""}</li>`;
}

function lgBookHTML(){
  const tab = k => `<button class="chip" data-lgbook="${k}" aria-pressed="${LG_BOOK === k}">${{fame: t("league.book.fame"),
    shame: t("league.book.shame"), champs: t("league.champs.title")}[k]}</button>`;
  const list = LG_BOOK === "champs" ? `<ol class="lg-champs">${LG.champs.map(lgChampHTML).join("")}</ol>`
    : `<ul class="bp-book">${(LG.book[LG_BOOK] || []).map(lgBookRow).join("")}</ul>`;
  return `<section class="lg-sec bp-booksec" aria-label="${t("league.hist.aria")}">
    <h3 class="bp-hd">${t("league.book.title")}<span>${t("league.hist.since", {y: LG.since})}</span></h3>
    <div class="setrow" role="group" aria-label="${t("league.book.title")}">${["fame", "shame", "champs"].map(tab).join("")}</div>
    ${list}
  </section>`;
}

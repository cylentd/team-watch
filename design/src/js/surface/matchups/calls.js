/* ============================== MATCHUPS: OUR CALLS ==============================
   Under the lineup (ledger #94, draft A): ff-jarvis's SMASH, bold START and bold SIT calls in one card, one kind
   a page at a time (data/lineup.js muCallRows, muPage) instead of 30-odd rows down the page. The record sits in
   the card's head, beside the calls it grades. The kind switch and the pager are the card's foot, in the thumb's
   reach on a phone (STYLE.md). A SMASH row is smash.js's, a START or SIT row rows.js's, which opens in place to
   its reasons. A tap repaints the card in place, so the page keeps its scroll. */

let MU_KIND = "smash";   // the kind on screen
let MU_PAGE = 0;         // its page, from 0

const MU_KIND_LIST = ["smash", "start", "sit"];
const MU_CHEV = d => `<svg class="mu-chev" viewBox="0 0 16 16" aria-hidden="true"><path d="${d}"/></svg>`;

/* The record's one line: each call's hit-miss since its first week, a void count beside one above zero, and the
   for-fun line under it once anyone has a graded call (record.js muFunHTML). */
function muRecordLineHTML(){
  const r = LIVE_SS3.record;
  const head = `${t("matchups.record.label")} ${t("matchups.record.since", {wk: r.since_week})}`;
  if (!ss3Graded(r)) return `<div class="mu-recl" data-testid="matchups-record"><p>${head}: ${t("matchups.record.none")}</p></div>`;
  const one = (k, c) => `<span class="mu-recl-k ${k}"><b>${ss3Wl(c)}</b> ${muCallWord(k.toUpperCase())}${c.void > 0 ? ` <small>${t("matchups.record.void", {n: c.void})}</small>` : ""}</span>`;
  return `<div class="mu-recl" data-testid="matchups-record" aria-label="${t("matchups.record.aria", {wk: r.since_week})}"><p>${head}: ${MU_KIND_LIST.map(k => one(k, r[k])).join(" · ")}</p>${muFunHTML(r.fun)}</div>`;
}

/* Rows a page: six on a phone; beside the lineup (matchups.css, 960px) as many as end the card level with it,
   measured after each draw (muFitCalls). */
const MU_WIDE = window.matchMedia("(min-width:960px)");
let MU_ROWS_FIT = MU_PAGE_ROWS;
const muPerPage = () => MU_WIDE.matches ? MU_ROWS_FIT : MU_PAGE_ROWS;

/* Measure the lineup and the card's own head and foot, and repaint the card once if the rows that fit changed. */
function muFitCalls(v){
  const card = v.querySelector("#mu-calls"), lu = v.querySelector(".mu-lineup");
  if (!MU_WIDE.matches || !card || !lu) return;
  const fit = muFitRows(lu.offsetHeight, card.offsetHeight - card.querySelector(".mu-cl").offsetHeight);
  if (fit === MU_ROWS_FIT) return;
  MU_ROWS_FIT = fit;
  card.innerHTML = muCallsInnerHTML();
}

function muCallsInnerHTML(){
  const rows = muCallRows(LIVE_SS3, MU_KIND), pg = muPage(rows.length, MU_PAGE, muPerPage());
  MU_PAGE = pg.page;
  const smash = MU_KIND === "smash";
  const body = rows.slice(pg.from, pg.to).map(smash ? muSmashRowHTML : muTakeHTML).join("")
    || `<p class="mu-empty">${t("matchups.calls.none", {kind: muCallWord(MU_KIND.toUpperCase())})}</p>`;
  const mark = k => k === "smash" ? ` title="${t("matchups.takes.markSmash")}"` : "";
  const kinds = MU_KIND_LIST.map(k => `<button type="button" class="mu-kd ${k}" data-testid="matchups-kind" data-mukind="${k}" aria-pressed="${MU_KIND === k}"${mark(k)}>
    ${muCallWord(k.toUpperCase())}<b>${muCallRows(LIVE_SS3, k).length}</b></button>`).join("");
  const slips = smash && rows.length ? `<div class="mu-cf"><button type="button" class="mu-go" data-ssgo="parlay">${t("matchups.smash.build")}${MU_ARROW}</button></div>` : "";
  return `<h3 class="mu-ch"><span>${t("matchups.calls.title")}</span><span class="mu-ck">${smash ? t("matchups.smash.cols") : t("matchups.takes.cols")}</span></h3>
    ${muRecordLineHTML()}<div class="mu-cl" style="--mu-rows:${muPerPage()}">${body}</div>${slips}
    <div class="mu-kinds" role="group" aria-label="${t("matchups.calls.kinds")}">
      <button type="button" class="mu-pg" data-testid="matchups-page-prev" data-mupg="-1" aria-label="${t("matchups.calls.prev")}"${pg.page > 0 ? "" : " disabled"}>${MU_CHEV("M10 3L5 8l5 5")}</button>
      ${kinds}
      <button type="button" class="mu-pg" data-testid="matchups-page-next" data-mupg="1" aria-label="${t("matchups.calls.next")}"${pg.page < pg.pages - 1 ? "" : " disabled"}>${MU_CHEV("M6 3l5 5-5 5")}</button></div>
    <p class="mu-pgn" data-testid="matchups-page">${t("matchups.calls.page", {n: pg.page + 1, of: pg.pages})}</p>`;
}

/* No calls at all (ff-jarvis has not posted the week): Blip, in place of the card, with the record under him. */
function muCallsHTML(){
  if (!LIVE_SS3.smash.length && !LIVE_SS3.takes.length) return muBlipHTML(muRecordLineHTML());
  return `<section class="mu-card mu-calls" id="mu-calls" data-testid="matchups-calls" aria-label="${t("matchups.calls.title")}">${muCallsInnerHTML()}</section>`;
}

/* A kind or a page: the card repaints in place, the switch keeps focus where the finger was. */
function muCallsGo(kind, step){
  if (kind){ MU_KIND = kind; MU_PAGE = 0; } else MU_PAGE += step;
  const el = document.getElementById("mu-calls");
  if (!el) return;
  el.innerHTML = muCallsInnerHTML();
  el.querySelector(kind ? `[data-mukind="${kind}"]` : `[data-mupg="${step}"]:not([disabled])`)?.focus();
}

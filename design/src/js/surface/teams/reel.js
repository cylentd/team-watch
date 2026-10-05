/* ============================== ROSTER: THE WEEK PLAYS REEL ==============================
   One card per starter who has an official clip (LIVE_CLIPS, design/clips.py): his best-plays
   thumbnail, how many clips he has (lime when he scored a touchdown), his name, and the points and
   box-score line when the page has them for that week. Best scorer first; with no points, roster
   order. One last card names the starters with no clip and opens their game's highlights.

   It sits above the "This week" list on a phone, and the list folds to its one row while the reel
   shows (brief.js, reelFolds) so the first starter does not drop. From 1100px the list is a column
   beside the rows and keeps its place. The reel pages: STYLE.md allows no sideways scroll in a page
   that scrolls down, so `reelPer` cards show at a time (two on a phone), turned by the two arrows
   and by a swipe (lib/swipe.js), the Leaders and Preview way. A card opens the clip
   sheet (clipsheet.js) on his own clips alone, the end card on the game videos, and Play all on the
   queue of every card in order, which plays on from one to the next.

   A card whose player has no clip that plays here (YouTube refuses the NFL channel, MIN, SEA and SF
   on other sites) and the end card show YouTube's mark on the badge in place of the play triangle;
   Play all walks only the clips that play.

   Interface from clipsheet.js, called at run time: clipData, clipsOf, clipGameOf, clipWeekRow, clipCan,
   clipYtMark, clipSheetOpen. */

let REEL = {team: "", page: 0, unfold: false};   // the page on show, and the list shown anyway after "Show"
const REEL_MIN = 150;                             // px: the narrowest a card is drawn
const REEL_PLAY = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5l12 7-12 7z"/></svg>`;
const reelDesk = () => window.matchMedia("(min-width:1100px)").matches;
const reelThumb = id => `https://i.ytimg.com/vi/${encodeURIComponent(id)}/mqdefault.jpg`;

/* The week the clips are of, from the data: schedWeek() is the week coming up. */
function reelWeek(){
  const wk = clipData().week;
  return Number.isInteger(wk) ? wk : null;
}

/* A touchdown is in his box score; with no box score for the week yet (it lags the clips by a
   night), a clip whose title says touchdown. */
function reelTd(c){
  if (c.pts !== null) return ["pass_td", "rush_td", "rec_td"].some(k => c.row[k] > 0);
  return c.clips.some(x => /touchdown|\bTD\b/i.test(x.title || ""));
}

/* The starters with clips, best scorer first (a tie, or no points, keeps roster order). */
function reelCards(team){
  if (typeof clipsOf !== "function") return [];
  const cards = team.roster.filter(p => p.start && p.slug).map(p => ({p, clips: clipsOf(p.slug)}))
    .filter(c => c.clips.length)
    .map(c => ({...c, ...clipWeekRow(c.p)}));
  return cards.sort((a, b) => (b.pts ?? -999) - (a.pts ?? -999));
}

/* Starters with no clip but a game video, and the one-per-game queue they add after the cards. */
function reelEnds(team, cards){
  if (typeof clipGameOf !== "function") return [];
  const had = new Set(cards.map(c => c.p));
  return team.roster.filter(p => p.start && !had.has(p) && clipGameOf(p.team));
}
function reelByGame(ends){
  const seen = new Set();
  return ends.filter(p => { const id = clipGameOf(p.team).id; return !seen.has(id) && seen.add(id); });
}

/* null when nothing is on show. `queue` is what the clip sheet walks: a card's index is its place. */
function reelModel(team){
  const wk = reelWeek();
  const cards = wk === null ? [] : reelCards(team);
  if (!cards.length) return null;
  const ends = reelEnds(team, cards);
  return {wk, cards, ends, queue: cards.map(c => c.p).concat(reelByGame(ends)),
    n: cards.reduce((sum, c) => sum + c.clips.length, 0)};
}

const reelShows = team => !!reelModel(team);
const reelFolds = team => !REEL.unfold && !reelDesk() && reelShows(team);
function reelUnfold(){ REEL.unfold = true; render(); }

/* The list's folded form, in brief.js's own done row: what is left to check, and the way to open it. */
function reelFoldHTML(team, open){
  return `<section class="brief done" aria-label="${t("teams.brief.title")}" data-bteam="${team.key}">
    <div class="brief-h"><h2>${t("teams.brief.title")}</h2><small>${t("teams.brief.count", {n: open, s: open === 1 ? "" : "s"})}</small>
    <button type="button" class="brief-act" data-briefunfold>${t("teams.brief.show")}</button></div></section>`;
}

/* A thumbnail is an external image: its box has the shape already, so a slow or failed load moves
   nothing, and a failed one just shows the box. */
const reelImg = id => `<img src="${reelThumb(id)}" alt="" loading="lazy" decoding="async" onerror="this.hidden=true">`;

function reelCardHTML(c, i){
  const {pts, line} = c, mark = c.clips.some(clipCan) ? REEL_PLAY : clipYtMark();
  return `<button type="button" class="reel-card" data-reelopen="${i}">
    <span class="reel-thumb">${reelImg(c.clips[0].id)}<b class="reel-n${reelTd(c) ? " td" : ""}">${mark}${c.clips.length}</b></span>
    <span class="reel-who"><span class="reel-nm">${esc(nameInitial(c.p.n))}</span>${pts !== null ? `<span class="reel-pts">${pts.toFixed(1)}</span>` : ""}</span>
    ${line ? `<span class="reel-line">${esc(line)}</span>` : ""}
  </button>`;
}

function reelEndHTML(ends, i){
  return `<button type="button" class="reel-card reel-end" data-reelopen="${i}">
    <span class="reel-thumb">${reelImg(clipGameOf(ends[0].team).id)}<b class="reel-n">${clipYtMark()}</b></span>
    <span class="reel-who"><span class="reel-nm">${t("teams.clips.games", {n: ends.length})}</span></span>
    <span class="reel-line">${ends.map(p => esc(nameInitial(p.n))).join(", ")}</span>
  </button>`;
}

function reelHTML(team){
  const m = reelModel(team);
  if (!m) return "";
  const n = m.n;
  return `<section class="reel" data-reel aria-label="${esc(t("teams.clips.title", {week: m.wk}))}">
    <div class="reel-h">
      <div class="reel-ti"><h2>${t("teams.clips.title", {week: m.wk})}</h2><small>${t("teams.clips.count", {n, s: n === 1 ? "" : "s"})}</small></div>
      <button type="button" class="reel-all" data-reelall>${t("teams.clips.playAll")}</button>
      <button type="button" class="reel-arr" data-reelstep="-1" aria-label="${esc(t("teams.clips.prev"))}">&lsaquo;</button>
      <button type="button" class="reel-arr" data-reelstep="1" aria-label="${esc(t("teams.clips.next"))}">&rsaquo;</button>
    </div>
    <div class="reel-track">${m.cards.map(reelCardHTML).join("")}${m.ends.length ? reelEndHTML(m.ends, m.cards.length) : ""}</div>
  </section>`;
}

/* How many cards fit a page, measured in the reader's browser: as many as fit at REEL_MIN or more. */
function reelPer(track){
  const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
  return Math.min(4, Math.max(2, Math.floor((track.clientWidth + gap) / (REEL_MIN + gap))));
}

/* Shows the page's cards, hides the rest, and enables the arrows that lead somewhere. A turn
   (`dir` +1 / -1) slides the new page in from the side it came from; reduced motion jumps. */
function reelPaint(box, dir){
  if (!box) return;
  const track = box.querySelector(".reel-track"), cards = [...track.children];
  const per = reelPer(track), pages = Math.ceil(cards.length / per);
  REEL.page = Math.min(Math.max(REEL.page, 0), pages - 1);
  track.style.setProperty("--per", per);
  cards.forEach((el, i) => { el.hidden = Math.floor(i / per) !== REEL.page; });
  box.classList.toggle("one", pages < 2);
  box.querySelector("[data-reelstep='-1']").disabled = REEL.page === 0;
  box.querySelector("[data-reelstep='1']").disabled = REEL.page >= pages - 1;
  if (!dir || REDUCED()) return;
  track.classList.remove("in-l", "in-r");
  void track.offsetWidth;   // restart the slide when two turns come close together
  track.classList.add(dir > 0 ? "in-r" : "in-l");
}

function reelStep(box, dir){
  const was = REEL.page;
  const track = box.querySelector(".reel-track"), pages = Math.ceil(track.children.length / reelPer(track));
  REEL.page = Math.min(Math.max(was + dir, 0), pages - 1);
  if (REEL.page !== was) reelPaint(box, dir);
}

function wireReel(v, team){
  const box = v.querySelector("[data-reel]"), m = reelModel(team);
  if (!box || !m) return;
  if (REEL.team !== team.key){ REEL.team = team.key; REEL.page = 0; }
  const open = (queue, el, all) => { if (typeof clipSheetOpen === "function") clipSheetOpen(queue, 0, el, all); };
  /* Only Play all plays on into later cards: a card opens his own clips, the end card the game videos. */
  box.querySelectorAll("[data-reelopen]").forEach(b => b.addEventListener("click", () => {
    const i = +b.dataset.reelopen;
    open(i < m.cards.length ? [m.queue[i]] : m.queue.slice(i), b);
  }));
  box.querySelector("[data-reelall]").addEventListener("click", e => open(m.queue, e.currentTarget, true));
  box.querySelectorAll("[data-reelstep]").forEach(b => b.addEventListener("click", () => reelStep(box, +b.dataset.reelstep)));
  onSwipeX(box.querySelector(".reel-track"), dir => reelStep(box, dir));
  reelPaint(box, 0);
}
window.addEventListener("resize", () => reelPaint(document.querySelector("#view [data-reel]"), 0));

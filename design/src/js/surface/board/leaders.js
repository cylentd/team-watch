/* ------------------------------------------------------------------
   THE BOARD — one stat at a time, as a leaderboard (2026-09-25; a list since 2026-09-26).

   The stats are tabs the reader swipes through, and the list under them is one screen of rows,
   each with a bar, paged with Prev / Next rather than scrolled. Until 2026-09-26 the #1 was a
   208px photo card and #2-#5 sat under him, and the rest hid behind "Show all", so a 360px phone
   showed five players before a tap. The #1 keeps his card, a little shorter, and the list runs on
   from #2 to the bottom of the screen. The rank is said as a number, because "#3" is what a
   reader repeats.

   It reads USAGE.sheet through sheetValues(), the same function the profile's radar ranks from, so
   who counts on a stat has one definition -- including the games floor (sheetQualified, sheet.js).
   A picked player who is not on the page is pinned under it at his own rank, so the reader's
   player never has to be found.
------------------------------------------------------------------ */
const BD_HELD_TOP = 5;   // the footer names who the games floor kept out of the top five

const BD_ROWS = {};
function bdRows(pos){
  if (!BD_ROWS[pos]) BD_ROWS[pos] = ((USAGE.sheet || {}).rows || []).filter(r => r.pos === pos && sheetQualified(r));
  return BD_ROWS[pos];
}
const bdAxes = pos => ((USAGE.sheet || {}).axes || {})[pos] || [];

/* The stat on screen: the reader's pick while it exists at this position, else the stat the Grid
   ranks this position by, else the first. */
function bdStatOf(pos){
  const axes = bdAxes(pos);
  if (axes.some(a => a.id === BD_STAT)) return BD_STAT;
  const by = USAGE.rankBy && USAGE.rankBy[pos];
  return axes.some(a => a.id === by) ? by : (axes[0] || {}).id;
}

/* Everyone with a number on this stat, best first; a tie keeps name order so a rebuild never
   shuffles two equal players. */
function bdRanked(pos, axis){
  const by = sheetValues(pos, axis);
  return bdRows(pos).filter(r => by[r.slug] !== undefined)
    .map(r => ({...r, val: by[r.slug]}))
    .sort((a, b) => b.val - a.val || String(a.n).localeCompare(String(b.n)));
}

/* Who the floor kept off this stat and would otherwise sit in the top five. Named in the footer
   with the number and the games, so a reader who expected him sees why he is missing. */
function bdHeldOut(pos, axis, cut){
  return ((USAGE.sheet || {}).rows || [])
    .filter(r => r.pos === pos && !sheetQualified(r) && r.v[axis] !== null && r.v[axis] !== undefined && r.v[axis] > cut)
    .sort((a, b) => b.v[axis] - a.v[axis]);
}

/* Tabs carry the stat's plain name (axisName, profile/statcard.js), the same name the profile's
   radar and card use; the producer's abbreviation stays as the unit beside the hero's number. */
function bdTabsHTML(axes, sel){
  return `<div class="bd-tabs" role="tablist" aria-label="${t("board.tabs.label")}">${axes.map(a =>
    `<button type="button" class="bd-tab" role="tab" data-bdstat="${esc(a.id)}" aria-selected="${a.id === sel}">${esc(axisName(a))}</button>`).join("")}</div>`;
}

/* The #1. A title, so the name is whole (the page initials names everywhere else). The elite bar
   is said with its number when ff-jarvis publishes one; there is no bar to draw it against here.
   Kept on 2026-09-26 when the rest became a list: without it the view was one more list of six. */
/* The photo names every size cut (headSrcset): the hero draws it up to ~220px tall, so a 2x or 3x
   screen takes the 512px file, and the 96px one stretched to that was visibly soft. Above the fold,
   so not lazy, and so it states its size rather than sizes="auto". */
function bdHeroHTML(a, top, n, picked){
  const lg = typeof HEADS_LG !== "undefined" && HEADS_LG ? HEADS_LG[top.slug] : null;
  const src = lg || HEADS[top.slug], set = headSrcset(top.slug);
  const head = src ? `<img class="bd-hero-img" src="${src}"${set ? ` srcset="${set}" sizes="(min-width: 760px) 420px, 160px"` : ""} alt="" decoding="async" onerror="this.remove()">` : "";
  const elite = a.elite === null || a.elite === undefined ? ""
    : `<span class="bd-hero-elite">${t("board.hero.elite", {v: usageFmt(a.elite, a.fmt)})}</span>`;
  return `<button type="button" class="bd-hero${picked ? " pick" : ""}" data-bdopen="${esc(top.slug)}">
    ${head}
    <span class="bd-hero-txt">
      <span class="bd-hero-rk">${t("board.hero.rank", {n})}</span>
      <span class="bd-hero-v">${usageFmt(top.val, a.fmt)}<small>${esc(a.label)}</small></span>
      <span class="bd-hero-who"><b>${esc(top.n)}</b><span>${t("board.hero.meta", {team: esc(top.team || ""), g: top.g || 0})}</span></span>
      ${elite}
    </span>
  </button>`;
}

/* One row. The bar is the value against the #1's, measured from the position's floor rather than
   zero, so a stat that runs negative (RYOE) still draws a bar that means something. */
function bdRowHTML(r, rank, a, scale, picked, ahead){
  const w = Math.max(4, Math.round(scale(r.val) * 100));
  return `<button type="button" class="bd-row${picked ? " pick" : ""}${ahead ? " ahead" : ""}" data-bdopen="${esc(r.slug)}">
    <span class="bd-rk">${rank}</span>
    <span class="bd-head">${avatarHTML(r)}</span>
    <span class="bd-nm">${esc(nameInitial(r.n))}<i style="--w:${w}%"></i></span>
    <span class="bd-v">${usageFmt(r.val, a.fmt)}</span>
  </button>`;
}

/* Which pick is ahead on this stat, or "" when level or only one has a number. */
function bdAheadOn(by, picks){
  if (picks.length < 2) return "";
  const [x, y] = picks.map(p => by[p.slug]);
  if (x === undefined || y === undefined || x === y) return "";
  return x > y ? picks[0].slug : picks[1].slug;
}

function bdBoardHTML(pos, picks){
  const axes = bdAxes(pos), sel = bdStatOf(pos), a = axes.find(x => x.id === sel);
  const ranked = bdRanked(pos, sel);
  if (!ranked.length) return `${bdTabsHTML(axes, sel)}<div class="state-empty" style="min-height:220px">
    <div><b>${t("board.empty.thinTitle")}</b><span>${t("board.empty.thinSub")}</span></div></div>`;
  const by = sheetValues(pos, sel), lo = ranked[ranked.length - 1].val, hi = ranked[0].val;
  const scale = v => hi === lo ? 1 : (v - lo) / (hi - lo);
  const slugs = picks.map(p => p.slug), ahead = bdAheadOn(by, picks);
  const rankOf = r => rankAmong(by, r.slug)[0];
  const row = r => bdRowHTML(r, rankOf(r), a, scale, slugs.includes(r.slug), r.slug === ahead);
  const shown = bdPageRows(ranked);
  // Picks not on this page, pinned at their own rank. A pick with no number on this stat is said
  // as such rather than left off, because the reader put him there.
  const pinned = picks.filter(p => !shown.some(r => r.slug === p.slug)).map(p => {
    const r = ranked.find(x => x.slug === p.slug);
    return r ? bdRowHTML(r, rankOf(r), a, scale, true, r.slug === ahead)
      : `<div class="bd-row pick none"><span class="bd-rk">—</span><span class="bd-head">${avatarHTML(p)}</span
          ><span class="bd-nm">${esc(nameInitial(p.n))}</span><span class="bd-v">${t("board.row.none")}</span></div>`;
  }).join("");
  const held = bdHeldOut(pos, sel, (ranked[Math.min(BD_HELD_TOP, ranked.length) - 1] || {}).val ?? Infinity);
  const minG = sheetMinGames(pos);
  const foot = (minG > 1 ? t("board.foot.qualified", {n: ranked.length, pos, g: minG}) : t("board.foot.all", {n: ranked.length, pos}))
    + (held.length ? " " + t("board.foot.held", {list: held.map(r =>
        `${esc(nameInitial(r.n))} ${usageFmt(r.v[sel], a.fmt)} (${t("board.foot.games", {g: r.g || 0})})`).join(", ")}) : "");
  return `${bdTabsHTML(axes, sel)}
    <div class="bd-card" data-bdswipe>
      ${bdPageOf(ranked) === 1 ? bdHeroHTML(a, ranked[0], ranked.length, slugs.includes(ranked[0].slug)) : ""}
      <div class="bd-side">
        <div class="bd-list">${shown.map(row).join("")}</div>
        ${pinned ? `<div class="bd-list bd-pinned"><div class="bd-gap" aria-hidden="true"></div>${pinned}</div>` : ""}
        ${bdPagerHTML(ranked)}
      </div>
    </div>
    <p class="note bd-foot">${foot}</p>`;
}

/* A page is one screen: read without scrolling, and Next replaces the scroll. Page 1 is the #1's
   hero and the rows from #2; later pages are rows only, so they hold more. fit.js measures both
   counts in the reader's browser and resets them; 7 and 12 are only the first render's guesses
   (a 360x740 phone). Pages count from 1. */
let BD_FIRST_SIZE = 7, BD_PAGE_SIZE = 12;
function bdPageCount(ranked){ return 1 + Math.max(0, Math.ceil((ranked.length - 1 - BD_FIRST_SIZE) / BD_PAGE_SIZE)); }
const bdPageOf = ranked => Math.min(BD_PAGE, bdPageCount(ranked));
// Where a page starts in `ranked` (0 is the hero), and how many rows it holds.
const bdPageFrom = page => page === 1 ? 1 : 1 + BD_FIRST_SIZE + (page - 2) * BD_PAGE_SIZE;
const bdPageLen = page => page === 1 ? BD_FIRST_SIZE : BD_PAGE_SIZE;
function bdPageRows(ranked){
  const page = bdPageOf(ranked), from = bdPageFrom(page);
  return ranked.slice(from, from + bdPageLen(page));
}

function bdPagerHTML(ranked){
  const pages = bdPageCount(ranked);
  if (pages < 2) return "";
  const page = bdPageOf(ranked);
  const from = page === 1 ? 1 : bdPageFrom(page) + 1, to = Math.min(ranked.length, bdPageFrom(page) + bdPageLen(page));
  return `<div class="filters bd-pager">
      <span class="lbl">${t("board.more.range", {from, to, n: ranked.length})}</span>
      <span style="flex:1"></span>
      <button class="chip" data-bdpage="${page - 1}" ${page <= 1 ? "disabled" : ""}>${t("common.pager.prev")}</button>
      <button class="chip" data-bdpage="${page + 1}" ${page >= pages ? "disabled" : ""}>${t("common.pager.next")}</button>
    </div>`;
}

/* ------------------------------------------------------------------
   THE BOARD — the view: which position, which stat, who leads it.

   With nobody picked it is a leaderboard, one stat at a time (leaders.js). With one pick he is
   pinned under the top five at his own rank. With two it is a duel: the line above the board
   counts the stats each leads, and the one ahead on the stat on screen is lit.

   NO COMPOSITE SCORE. "Overall" here is a count of lanes, not a rating: six stats ff-jarvis
   publishes separately, weighted into one number by this page, would be this page inventing a
   model — and nothing on it is backtested. Counting the lanes each player is ahead on says the
   same thing out of numbers already on the screen, and a reader can check it by looking.
------------------------------------------------------------------ */
const BD_POSITIONS = ["QB", "RB", "WR", "TE"];
let BD_POS = "RB";
/* Which view is drawing: "leaders" (#board) or "movers" (#movers, surface/pool/pool.js). Set from
   SURFACE by render(); the two views share the position chip, so they share this surface. */
let BD_MODE = "leaders";
let BD_STAT = null;  // the axis on screen; null is the position's default (bdStatOf)
let BD_PAGE = 0;     // the full list's page under the top five; 0 is closed (leaders.js)
let BD_PICKS = [];   // slugs, newest last, at most two
let BD_NOTE = "";    // why the last pick did not land, cleared by the next render

const bdPicked = () => BD_PICKS.map(s => bdRows(BD_POS).find(r => r.slug === s)).filter(Boolean);

/* Lanes won, counted only where both players have a number: an unmeasured stat is not a stat he
   lost. A tie is comparable and belongs in the denominator, so "leads 3 of 6" can sit against an
   opponent on 2 without the pair adding to 6. */
function bdTally(pos, axes, picks){
  const out = {a: 0, b: 0, of: 0};
  axes.forEach(x => {
    const by = sheetValues(pos, x.id);
    const va = by[picks[0].slug], vb = by[picks[1].slug];
    if (va === undefined || vb === undefined) return;
    out.of += 1;
    if (va > vb) out.a += 1; else if (vb > va) out.b += 1;
  });
  return out;
}

/* Said only once somebody is picked: with nobody picked the leaderboard itself is the answer. */
function bdLeadHTML(pos, axes, picks){
  if (!picks.length) return "";
  if (picks.length === 1)
    return `<div class="bd-lead">${t("board.lead.one", {name: esc(nameInitial(picks[0].n)), pos})}</div>`;
  const k = bdTally(pos, axes, picks);
  if (!k.of) return `<div class="bd-lead">${t("board.lead.noShared")}</div>`;
  if (k.a === k.b) return `<div class="bd-lead">${t("board.lead.level", {n: k.a, of: k.of})}</div>`;
  const win = k.a > k.b ? picks[0] : picks[1];
  return `<div class="bd-lead">${t("board.lead.two",
    {name: `<b class="on">${esc(nameInitial(win.n))}</b>`, n: Math.max(k.a, k.b), of: k.of})}</div>`;
}

/* The chips are the legend the rail would otherwise need: the same two initials, beside the whole
   name, in the order the lanes read them. Each drops itself and there is no Clear beside them --
   with at most two chips a Clear removes one tap and, at 360px, wraps onto a row of its own. */
function bdChipsHTML(picks){
  if (!picks.length) return "";
  return `<div class="bd-picks">${picks.map(p =>
    `<span class="bd-pick"><span class="bd-key">${esc(initials(p.n))}</span
      ><b>${esc(nameInitial(p.n))}</b><button type="button" class="bd-x" data-bddrop="${esc(p.slug)}"
        aria-label="${t("board.action.remove", {name: esc(p.n)})}">✕</button></span>`).join("")}</div>`;
}

/* A position is offered when this view has something to draw for it: lanes, or movers. A pick
   is a Leaders idea, so "+ Compare" is too. */
function bdControlsHTML(){
  const has = BD_MODE === "movers" ? p => POOL.some(r => r.pos === p) : p => bdAxes(p).length;
  // .setrow, not .filters: the chips fit a phone, so the row never scrolls (STYLE.md audit).
  return `<div class="setrow" role="group" aria-label="${t("board.filter.position")}">
    ${BD_POSITIONS.filter(has).map(p =>
      `<button class="chip" data-bdpos="${p}" aria-pressed="${BD_POS === p}">${p}</button>`).join("")}
    ${BD_MODE === "movers" ? "" : `<span style="flex:1"></span>
    <button class="chip bd-add" data-bdadd>${t("board.action.add")}</button>`}
  </div>`;
}

function bdViewHTML(){
  if (BD_MODE === "movers") return `<div class="wrap">${bdControlsHTML()}${poolHTML(BD_POS)}</div>`;
  const axes = bdAxes(BD_POS);
  if (!axes.length) return `<div class="wrap"><div class="state-empty" style="min-height:220px">
    <div><b>${t("board.empty.noSheetTitle")}</b><span>${t("board.empty.noSheetSub")}</span></div></div></div>`;
  const picks = bdPicked();
  return `<div class="wrap pos-${BD_POS.toLowerCase()}">
    ${bdControlsHTML()}
    ${BD_NOTE ? `<p class="bd-note">${BD_NOTE}</p>` : ""}
    ${bdChipsHTML(picks)}
    ${bdLeadHTML(BD_POS, axes, picks)}
    ${bdBoardHTML(BD_POS, picks)}
    ${bdLabelsHTML(picks)}
  </div>`;
}

/* Sideways through the stats, the same order as the tabs, stopping at either end. */
function bdStep(dir){
  const axes = bdAxes(BD_POS), i = axes.findIndex(a => a.id === bdStatOf(BD_POS)), j = i + dir;
  if (j < 0 || j >= axes.length) return false;
  BD_STAT = axes[j].id; BD_PAGE = 0;
  return true;
}

/* A pick of another position moves the board to his position and keeps only him. The axes are
   position-specific, so two positions cannot share a lane; refusing the pick instead would make
   the reader undo a search he meant, and the position chip visibly moving says what happened. */
function bdAdd(p){
  BD_NOTE = "";
  const row = ((USAGE.sheet || {}).rows || []).find(r => r.slug === p.slug);
  if (!row){
    BD_NOTE = t("board.note.noSheet", {name: esc(nameInitial(p.n))});
  } else if (!sheetQualified(row)){
    BD_NOTE = t("board.note.fewGames", {name: esc(nameInitial(p.n)), g: row.g || 0, min: sheetMinGames(row.pos)});
  } else {
    if (row.pos !== BD_POS){ BD_POS = row.pos; BD_PICKS = []; }
    BD_PICKS = [...BD_PICKS.filter(s => s !== row.slug), row.slug].slice(-2);
  }
  render();
}

function wireBd(v){
  const set = (sel, fn) => v.querySelectorAll(sel).forEach(b => b.addEventListener("click", () => { fn(b); render(); }));
  // Switching position drops the picks: they are rows of the position that just left the screen.
  set("[data-bdpos]", b => { BD_NOTE = ""; POOL_PAGE = 1; if (b.dataset.bdpos !== BD_POS){ BD_POS = b.dataset.bdpos; BD_PICKS = []; BD_STAT = null; BD_PAGE = 0; } });
  // A new stat is a new ranking, so the list closes: page 3 of TPRR is nobody's page 3 of YPRR.
  set("[data-bdstat]", b => { BD_NOTE = ""; BD_STAT = b.dataset.bdstat; BD_PAGE = 0; });
  // Opening or turning a page sizes the page to the screen and brings the list to its top
  // (fit.js). Closing scrolls back to the card only if the list he was reading has just vanished
  // from under him; otherwise he stays where he is.
  v.querySelectorAll("[data-bdpage]").forEach(b => b.addEventListener("click", () => {
    const next = +b.dataset.bdpage, y = window.scrollY;
    BD_PAGE = next; render();
    const card = document.querySelector(".bd-card");
    if (next > 0) bdFitPage();
    else if (card && card.getBoundingClientRect().bottom < 0) card.scrollIntoView({block: "start"});
    else window.scrollTo(0, y);
  }));
  v.querySelectorAll("[data-bdopen]").forEach(el => el.addEventListener("click", () => {
    const r = ((USAGE.sheet || {}).rows || []).find(x => x.slug === el.dataset.bdopen);
    if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
  }));
  // A horizontal swipe on the card moves one stat; a mostly-vertical drag is a scroll and is left alone.
  v.querySelectorAll("[data-bdswipe]").forEach(el => {
    let x0 = null, y0 = 0;
    el.addEventListener("touchstart", e => { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, {passive: true});
    el.addEventListener("touchend", e => {
      if (x0 === null) return;
      const dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
      x0 = null;
      if (Math.abs(dx) > 48 && Math.abs(dx) > 1.5 * Math.abs(dy) && bdStep(dx < 0 ? 1 : -1)){
        BD_NOTE = ""; render();
        const tab = document.querySelector(".bd-tab[aria-selected=true]");
        if (tab) tab.scrollIntoView({block: "nearest", inline: "center"});
      }
    }, {passive: true});
  });
  set("[data-bddrop]", b => { BD_NOTE = ""; BD_PICKS = BD_PICKS.filter(s => s !== b.dataset.bddrop); });
  // The picker is the app's own search sheet, handed a slot to fill instead of a profile to open.
  v.querySelectorAll("[data-bdadd]").forEach(b => b.addEventListener("click", () => searchOpen(bdAdd)));
  if (BD_MODE === "movers") wirePool(v);
}

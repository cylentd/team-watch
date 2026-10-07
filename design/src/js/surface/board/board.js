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
const BD_POSITIONS = statsPosList("board");   // QB RB WR TE (data/statspos.js)
let BD_POS = "RB";
let BD_STAT = null;  // the axis on screen; null is the position's default (bdStatOf)
let BD_PAGE = 1;     // the list's page, from 1 (leaders.js)
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

/* BD_POS is Stats' one position as Leaders shows it (data/statspos.js, 2026-10-06); a new one drops the picks,
   rows of the position that just left the screen, and starts the list over on its default stat. */
function bdUsePos(p){
  if (p === BD_POS) return;
  BD_POS = p; BD_PICKS = []; BD_STAT = null; BD_PAGE = 1; BD_NOTE = "";
}
statsPosView("board", {attr: "bdpos", label: p => p, use: bdUsePos,
  opts: () => ({have: BD_POSITIONS.filter(p => bdAxes(p).length)})});

const bdAddHTML = () => `<button class="chip bd-add" data-bdadd>${t("board.action.add")}</button>`;

/* A position is offered when it has lanes to draw. (Movers shared this row until 2026-09-29, when
   it became Role, a surface of its own.) A desktop's row: on a phone the positions are the strip above
   the bottom bar (chrome/statspos.js) and Add ends the stat tabs' row (leaders.js bdTabsHTML). */
function bdControlsHTML(){
  if (!spChipsOn()) return "";
  // .setrow, not .filters: the chips fit a phone, so the row never scrolls (STYLE.md audit).
  return `<div class="setrow" role="group" aria-label="${t("board.filter.position")}">
    ${BD_POSITIONS.filter(p => bdAxes(p).length).map(p =>
      `<button class="chip" data-bdpos="${p}" aria-pressed="${BD_POS === p}">${p}</button>`).join("")}
    <span style="flex:1"></span>
    ${bdAddHTML()}
  </div>`;
}

function bdViewHTML(){
  const axes = bdAxes(BD_POS);
  if (!axes.length) return `<div class="wrap"><div class="state-empty" style="min-height:220px">
    <div><b>${t("board.empty.noSheetTitle")}</b><span>${t("board.empty.noSheetSub")}</span></div></div></div>`;
  const picks = bdPicked();
  return `<div class="wrap pos-${BD_POS.toLowerCase()}">
    ${navCaptionHTML("board")}
    ${bdControlsHTML()}
    ${BD_NOTE ? `<p class="bd-note">${BD_NOTE}</p>` : ""}
    ${bdChipsHTML(picks)}
    ${bdLeadHTML(BD_POS, axes, picks)}
    ${bdBoardHTML(BD_POS, picks)}
    ${bdLabelsHTML(picks)}
  </div>`;
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
    if (row.pos !== BD_POS){ statsPick(row.pos); bdUsePos(row.pos); }
    BD_PICKS = [...BD_PICKS.filter(s => s !== row.slug), row.slug].slice(-2);
  }
  render();
}

function wireBd(v){
  const set = (sel, fn) => v.querySelectorAll(sel).forEach(b => b.addEventListener("click", () => { fn(b); render(); }));
  // A position chip (a desktop's) picks Stats' one position; the render's bdUsePos drops the picks.
  set("[data-bdpos]", b => { BD_NOTE = ""; statsPick(b.dataset.bdpos); });
  // A new stat is a new ranking, so the list starts over: page 3 of TPRR is nobody's page 3 of YPRR.
  set("[data-bdstat]", b => { BD_NOTE = ""; BD_STAT = b.dataset.bdstat; BD_PAGE = 1; });
  // Turning a page keeps the reader where he is: the page is sized to fit from the top.
  set("[data-bdpage]", b => { BD_PAGE = +b.dataset.bdpage; });
  v.querySelectorAll("[data-bdopen]").forEach(el => el.addEventListener("click", () => {
    const r = ((USAGE.sheet || {}).rows || []).find(x => x.slug === el.dataset.bdopen);
    if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
  }));
  // No swipe of its own since 2026-10-06: a sideways swipe here turns the top tab row, as on every view
  // (chrome/tabswipe.js); the stat tabs above the card turn the stat. It turned the stat until then.
  set("[data-bddrop]", b => { BD_NOTE = ""; BD_PICKS = BD_PICKS.filter(s => s !== b.dataset.bddrop); });
  // The picker is the app's own search sheet, handed a slot to fill instead of a profile to open.
  v.querySelectorAll("[data-bdadd]").forEach(b => b.addEventListener("click", () => searchOpen(bdAdd)));
  bdFitPage();   // the page holds what the screen shows (fit.js); re-renders once if it must
}

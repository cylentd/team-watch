/* ============================== ROSTER: THE WEEK PLAYS RAIL ==============================
   One card per clip (LIVE_CLIPS, design/clips.py) of the starters who have any, in a rail the reader
   drags: native touch scroll, a mouse drag on a desktop, the next card showing past the edge so the
   rail says it goes on (STYLE.md allows this one sideways row, "Roster clips, 2026-10-05"). Best
   scorer first, each player's clips in data order. A clip that plays here wears a lime disc with a
   play triangle and opens the theater on it; one YouTube refuses on other sites wears a YouTube chip
   and is a plain link. A last card names the starters with no clip and opens their game's highlights.
   The header's "Play n" starts the theater on the first clip that plays.

   It sits above the "This week" list on a phone, and the list folds to its one row while the rail
   shows (brief.js, reelFolds) so the first starter does not drop. From 1100px the list is a column
   beside the rows and keeps its place, and the rail gets ‹ › when it overflows.

   The card, header and drag are cliprail.js's (shared with Live > TDs). From clipsheet.js:
   clipData, clipsOf, clipGameOf, clipWeekRow, clipCan, clipYtUrl, clipYtChipHTML. */

let REEL = {unfold: false};                       // the list shown anyway after "Show"
const reelDesk = () => window.matchMedia("(min-width:1100px)").matches;

/* The week the clips are of, from the data: schedWeek() is the week coming up. */
function reelWeek(){
  const wk = clipData().week;
  return Number.isInteger(wk) ? wk : null;
}

/* The starters with clips, best scorer first (a tie, or no points, keeps roster order). */
function reelCards(team){
  const cards = team.roster.filter(p => p.start && p.slug).map(p => ({p, clips: clipsOf(p.slug)}))
    .filter(c => c.clips.length)
    .map(c => ({...c, pts: clipWeekRow(c.p).pts}));
  return cards.sort((a, b) => (b.pts ?? -999) - (a.pts ?? -999));
}

/* One item per clip: [{c, p, ps}] in rail order, the theater's queue, so a card's index is its place.
   A clip credited to two starters (a touchdown pass) is one item at the first's place; `p` is that
   first player and `ps` every starter credited. */
function reelItems(cards){
  const by = new Map(), items = [];
  cards.forEach(card => card.clips.forEach(c => {
    const had = by.get(c.id);
    if (!had){ const it = {c, p: card.p, ps: [card.p]}; by.set(c.id, it); items.push(it); }
    else if (!had.ps.includes(card.p)) had.ps.push(card.p);
  }));
  return items;
}

/* null when nothing is on show. `ends` are the starters with no clip but a game video. */
function reelModel(team){
  const wk = reelWeek(), cards = wk === null ? [] : reelCards(team);
  if (!cards.length) return null;
  const items = reelItems(cards);
  const had = new Set(cards.map(c => c.p));
  const ends = team.roster.filter(p => p.start && !had.has(p) && clipGameOf(p.team));
  const play = items.filter(it => clipCan(it.c)).length;
  return {wk, items, ends, play, first: items.findIndex(it => clipCan(it.c))};
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

/* The starters with no clip, and their game's highlights on YouTube (the first such game's). */
function reelEndHTML(ends){
  const names = ends.map(p => nameInitial(p.n)).join(", ");
  return `<a class="reel-card reel-end" href="${esc(clipYtUrl(clipGameOf(ends[0].team)))}" target="_blank" rel="noopener" draggable="false">
    <span class="reel-thumb"><b class="reel-no">${t("teams.clips.noClip")}</b>
    <span class="reel-endline">${esc(t("teams.clips.noClipLine", {names}))}</span><span class="reel-mark">${clipYtChipHTML()}</span></span></a>`;
}

function reelHTML(team){
  const m = reelModel(team);
  if (!m) return "";
  const title = t("teams.clips.title", {week: m.wk});
  return `<section class="reel" data-reel aria-label="${esc(title)}">
    ${clipRailHeadHTML(title, m.items.length, m.play)}
    <div class="reel-track">${m.items.map((x, i) => clipCardHTML(x, i)).join("")}${m.ends.length ? reelEndHTML(m.ends) : ""}</div>
  </section>`;
}

function wireReel(v, team){
  const box = v.querySelector("[data-reel]"), m = reelModel(team);
  if (box && m) clipRailWire(box, m.items, m.first);
}

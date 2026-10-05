/* ============================== LIVE: THE TD CLIPS REEL ==============================
   Above the Scored card, Feed view of the TDs tab (2026-10-05, storyboard
   https://claude.ai/artifact/5GZZ3GCcsp9znxzjiNrjKB): Roster's clip rail (cliprail.js) of every scorer the
   chips leave in the Scored card. The reel follows the chips, newest clip first, and draws nothing when no
   scorer has a clip. A card's second line is the scorer's TD line from the row ("2 rec TD"), not the clip's
   title; a row still opens the profile; By game has no reel.

   Two sources, one per clip id: LIVE_CLIPS (Claude-matched, the finished week's, so used only when it is
   of the week the leaders are of) and the fresh clips data/gameday/tdclips.js asked our function for. A
   clip credited to two scorers is one card naming both, with the first's line.

   Render is a pure function of that state and the poll's stats. A repaint rebuilds the rail, so the card
   at the reader's left edge is remembered by id (TDR) and put back where it was: a clip that joins on the
   left moves nothing the reader is looking at.
   From cliprail.js: clipCardHTML, clipRailHeadHTML, clipRailWire. */

let TDR = {anchor: null};   /* {id, rel}: the card at the rail's left edge and how far in from it, null at the start */

const tdrTime = c => { const at = Date.parse(c.posted); return isNaN(at) ? -Infinity : at; };

/* One item per clip, newest first; a tie, or no time, keeps the scorers' order. Null when none. */
function tdrModel(rows, kinds){
  const wk = (GD.leagues[0] || {}).week, own = clipData().week === wk;
  const by = new Map(), items = [];
  for (const v of rows){
    const w = {n: v.n, slug: slugOf(v.n || ""), team: v.team}, p = {...w, pos: v.pos};
    const line = tdScoredLine(v.s, kinds);
    for (const c of [...(own ? clipsOf(w.slug) : []), ...tdcFor(w)]){
      const had = by.get(c.id);
      if (!had){ const it = {c, p, ps: [p], line}; by.set(c.id, it); items.push(it); continue; }
      if (!had.ps.includes(p)) had.ps.push(p);
      if (!had.c.posted && c.posted) had.c = {...had.c, posted: c.posted};
    }
  }
  if (!items.length) return null;
  items.sort((a, b) => { const x = tdrTime(a.c), y = tdrTime(b.c); return x === y ? 0 : y > x ? 1 : -1; });
  return {items, play: items.filter(it => clipCan(it.c)).length, first: items.findIndex(it => clipCan(it.c))};
}

function tdrHTML(m){
  if (!m) return "";
  const title = t("live.tds.clips");
  return `<section class="reel td-reel" data-reel data-tdreel aria-label="${esc(title)}">
    ${clipRailHeadHTML(title, m.items.length, m.play)}
    <div class="reel-track">${m.items.map((x, i) => clipCardHTML(x, i, x.line)).join("")}</div>
  </section>`;
}

/* The card at the left edge, by id, and its distance from the rail's edge; the start of the rail is no anchor. */
function tdrMark(track){
  const edge = track.getBoundingClientRect().left;
  const card = track.scrollLeft > 1 && [...track.querySelectorAll("[data-clipid]")].find(c => c.getBoundingClientRect().right - edge > 1);
  TDR.anchor = card ? {id: card.dataset.clipid, rel: card.getBoundingClientRect().left - edge} : null;
}

/* After a repaint: scroll until the remembered card is where it was. */
function tdrRestore(track){
  const a = TDR.anchor;
  if (!a) return;
  const card = [...track.querySelectorAll("[data-clipid]")].find(c => c.dataset.clipid === a.id);
  if (!card){ TDR.anchor = null; return; }
  track.scrollLeft += card.getBoundingClientRect().left - track.getBoundingClientRect().left - a.rel;
}

/* Called by wireTds with the model the paint drew (null in By game, or when there is no reel). */
function tdrWire(host, m){
  const box = host.querySelector("[data-tdreel]");
  if (!box || !m){ TDR.anchor = null; return; }
  const track = clipRailWire(box, m.items, m.first);
  tdrRestore(track);
  track.addEventListener("scroll", () => tdrMark(track), {passive: true});
}

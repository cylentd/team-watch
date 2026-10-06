/* ============================== ROSTER: THE WEEK PLAYS RAIL ==============================
   One card per starter who has clips (LIVE_CLIPS, design/yt_clips.py), best scorer first, in a rail of
   pages: two cards to a phone page, four from 761px, the next page's card never showing (2026-10-05,
   Roster redesign unit C; v2 had a card per clip, 128x160, the next one showing past the edge). The
   card is a 16:10 picture of his first clip with his name, points and stat line laid over its foot
   and a count chip at its top right; no text under it. A card with a clip that plays here opens the
   theater on his clips only; one with none that YouTube allows on other sites is a link to YouTube
   and wears its chip where the count goes. A last card names the starters with no clip and opens
   their game's highlights. The header is one line: "Week N plays", the clip count, Play all (the
   theater on every clip, from the first that plays) and the ‹ › that turn a measured page. The rail
   still scrolls by finger or mouse drag (STYLE.md allows this one sideways row, "Roster clips").

   It sits above the "This week" list on a phone, and the list folds to its one row while the rail
   shows (brief.js, reelFolds) so the first starter does not drop. From 1100px the list is a column
   beside the rows and keeps its place.

   The rail's drag, fit, warm-up and resize are cliprail.js's (shared with Live > TDs); the card, the
   header and the page step are the Roster's own, handed to clipRailWire. From cliprail.js: REEL_PLAY,
   reelImg, reelFit, clipRailWire. From clipsheet.js: clipData, clipsOf, clipGameOf, clipWeekRow,
   clipCan, clipTheaterOpen(items, i, el), clipYtUrl, clipYtChipHTML. */

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
    .map(c => { const w = clipWeekRow(c.p); return {...c, pts: w.pts, line: w.line}; });
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

/* null when nothing is on show. `ends` are the starters with no clip but a game video. `decks` are the
   rail's cards, one per starter: his own queue of items (a clip credited to two is in both), the place
   in it the theater starts (the first that plays here, -1 when none does), and his week's line. */
function reelModel(team){
  const wk = reelWeek(), cards = wk === null ? [] : reelCards(team);
  if (!cards.length) return null;
  const items = reelItems(cards);
  const had = new Set(cards.map(c => c.p));
  const ends = team.roster.filter(p => p.start && !had.has(p) && clipGameOf(p.team));
  const decks = cards.map(c => {
    const own = items.filter(it => it.ps.includes(c.p));
    return {p: c.p, pts: c.pts, line: c.line, items: own, first: own.findIndex(it => clipCan(it.c))};
  });
  return {wk, items, decks, ends, first: items.findIndex(it => clipCan(it.c))};
}

const reelShows = team => !!reelModel(team);
const reelFolds = team => !REEL.unfold && !reelDesk() && reelShows(team);
function reelUnfold(){ REEL.unfold = true; render(); }

/* The list's folded form, in brief.js's own done row: what is left to check, the sit pill when a
   starter will likely sit (`pill`, injury.js), and the way to open it. */
function reelFoldHTML(team, open, pill = ""){
  return `<section class="brief done" aria-label="${t("teams.brief.title")}" data-bteam="${team.key}">
    <div class="brief-h"><h2>${t("teams.brief.title")}</h2>${pill}<small>${briefCount(open, pill)}</small>
    <button type="button" class="brief-act" data-briefunfold>${t("teams.brief.show")}</button></div></section>`;
}

/* One starter: his first clip's picture, his name, points and stat line laid over its foot, and the
   count of his clips at its top right (or, on a link, YouTube's chip). With no stat line the first
   clip's title says what is in it. The card carries its first clip's id (data-clipid), as the shared
   card does, so the theater can find it again on close (clipsheet.js). */
function reelCardHTML(x, i){
  const first = x.items[0].c, can = x.first >= 0, attrs = ` data-clipid="${esc(first.id)}"`;
  const pts = Number.isFinite(x.pts) ? x.pts.toFixed(1) : "";
  const chip = can ? `<span class="reel-n">${REEL_PLAY}${x.items.length}</span>` : `<span class="reel-mark">${clipYtChipHTML()}</span>`;
  const body = `<span class="reel-thumb">${reelImg(first)}${chip}<span class="reel-ov">
      <span class="reel-l1"><span class="reel-nm">${esc(nameInitial(x.p.n))}</span>${pts ? `<b class="reel-pt">${pts}</b>` : ""}</span>
      <span class="reel-l2">${esc(x.line || first.title || "")}</span></span></span>`;
  return can
    ? `<button type="button" class="reel-card" data-reelplay="${i}"${attrs}>${body}</button>`
    : `<a class="reel-card" href="${esc(clipYtUrl(first))}" target="_blank" rel="noopener" draggable="false"${attrs}
        aria-label="${esc(t("teams.clips.opensYouTube", {title: first.title || ""}))}">${body}</a>`;
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
  const title = t("teams.clips.title", {week: m.wk}), n = m.items.length;
  return `<section class="reel reel-wk" data-reel aria-label="${esc(title)}">
    <div class="reel-h">
      <div class="reel-ti"><h2>${esc(title)}</h2><small>${t("teams.clips.count", {n, s: n === 1 ? "" : "s"})}</small></div>
      ${m.first >= 0 ? `<button type="button" class="reel-all" data-reelall>${t("teams.clips.playAll")}</button>` : ""}
      <button type="button" class="reel-arr" data-reelstep="-1" aria-label="${esc(t("teams.clips.prev"))}">&lsaquo;</button>
      <button type="button" class="reel-arr" data-reelstep="1" aria-label="${esc(t("teams.clips.next"))}">&rsaquo;</button>
    </div>
    <div class="reel-track">${m.decks.map(reelCardHTML).join("")}${m.ends.length ? reelEndHTML(m.ends) : ""}</div>
  </section>`;
}

/* A page, measured: as many cards as the track shows whole (two on a phone, four from 761px), each a
   width and a gap. What an arrow scrolls by (Live's rail steps one card). */
function reelPageStep(track, dir){
  const card = track.querySelector(".reel-card"), gap = parseFloat(getComputedStyle(track).columnGap) || 0;
  const w = card.offsetWidth + gap, per = Math.max(1, Math.round((track.clientWidth + gap) / w));
  track.scrollBy({left: dir * per * w, behavior: REDUCED() ? "auto" : "smooth"});
}

/* A card opens the theater on his clips only, from the first that plays; Play all on every clip. */
function wireReel(v, team){
  const box = v.querySelector("[data-reel]"), m = reelModel(team);
  if (!box || !m) return;
  const open = (i, el) => { const d = m.decks[i]; if (d) clipTheaterOpen(d.items, d.first, el); };
  clipRailWire(box, m.items, m.first, {open, step: reelPageStep});
}

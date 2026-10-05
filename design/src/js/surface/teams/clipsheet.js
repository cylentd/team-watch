/* ============================== ROSTER: THE CLIP THEATER ==============================
   A player's official clips (LIVE_CLIPS, design/clips.py), played full screen over the page: opened by
   the ring on a roster head (clipWireRings) or by the Week plays rail (reel.js). The player itself is
   clipplayer.js, one YouTube player for every clip; this part is what is on screen around it.

   The theater plays the items that play here (clipCan) in order and lists the rest on its end card as
   links to YouTube (YouTube refuses the NFL channel, MIN, SEA and SF on other sites: error 150). Where
   the page cannot embed at all (a file, the Artifact frame) nothing plays and it opens on the end card.
   Back, Escape, a pull down and the close button shut it (chrome/layers.js); focus returns to where it
   came from. A sideways swipe, the arrow keys and the two round buttons step.

   Used by the rail and the ring: clipTheaterOpen(items, i, originEl), clipWarm, clipNames, clipCan,
   clipYtUrl, clipThumbOf, clipYtChipHTML, clipYtMark, clipDur, clipsOf, clipGameOf, clipWeekRow,
   clipRingHTML, clipWireRings. items = [{c: a clip, p: a roster player, ps: every player credited, optional}]; i the one to start (-1: the
   end card). */

let CT = null;           /* the theater on screen: {items, play, pos, seen, tok, timer}; null = closed */
let CLIP_RETURN = null;
const CLIP_ERR_MS = 2000;   /* a clip YouTube refuses: Play all moves on after this */
const clipEl = () => document.getElementById("clipsheet");
const clipQ = sel => clipEl().querySelector(sel);

/* ---- data: function declarations, so the rail can call them while the parts load ---- */
function clipData(){ return (typeof LIVE_CLIPS !== "undefined" ? LIVE_CLIPS : null) || {}; }
function clipsOf(slug){ return (clipData().players || {})[slug] || []; }
/* The games are keyed in the schedule's spelling (LAR, WSH). A roster may say LA or WAS: the schedule's
   alias maps it, and so does the block's own, for a page built with no schedule. */
function clipGameOf(team){
  const c = clipData(), g = c.games || {};
  return schedTeamRow({teams: g}, team) || g[(c.alias || {})[team]] || null;
}
const CLIP_POS = ["QB", "RB", "WR", "TE"];   /* the positions whose box score has a stat line */
/* His box score for the week the clips are of (LIVE_CLIPS.week): the points and the stat line, null
   where the page has no row for him yet (it lags the clips by a night). `row` is for the rail's TD badge. */
function clipWeekRow(p){
  const wk = clipData().week, row = p.slug && Number.isInteger(wk) ? gamelogRows(p.slug).find(r => r.wk === wk) || null : null;
  return {row, pts: row && typeof row.pts === "number" ? row.pts : null,
    line: row && CLIP_POS.includes(p.pos) ? seasonLine(p.pos, row) : null};
}
/* His clips in order; a player with none plays his game's highlights. */
function clipItemsOf(p){
  const own = clipsOf(p.slug), g = own.length ? null : clipGameOf(p.team);
  return g ? [{id: g.id, title: g.title, kind: "game", secs: g.secs, shape: g.shape, embed: g.embed}] : own;
}
/* Whether this clip plays on this page: YouTube lets it embed (a block from before the field says yes)
   and the page can load an embed at all. */
function clipCan(c){ return !!c && c.embed !== false && clipEmbedOk(); }
const clipTall = c => !!c && c.shape === "tall";
const clipYtUrl = c => clipTall(c) ? `https://www.youtube.com/shorts/${encodeURIComponent(c.id)}` : `https://www.youtube.com/watch?v=${encodeURIComponent(c.id)}`;
const clipThumbOf = c => `https://i.ytimg.com/vi/${encodeURIComponent(c.id)}/${clipTall(c) ? "oar2" : "hqdefault"}.jpg`;
const clipDur = s => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
const clipPlural = n => ({n, s: n === 1 ? "" : "s"});
/* Every starter credited on an item ("B. Purdy, G. Kittle"); the ring's items carry only `p`. */
const clipNames = x => (x.ps || [x.p]).map(p => nameInitial(p.n)).join(", ");
/* YouTube's mark, for a clip that opens YouTube instead of playing. */
function clipYtMark(){ return `<svg class="yt-mark" viewBox="0 0 24 24" aria-hidden="true"><path fill-rule="evenodd" d="M6 5h12a4 4 0 0 1 4 4v6a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V9a4 4 0 0 1 4-4zm4 4v6l5-3z"/></svg>`; }
/* The "YouTube" chip with its arrow: where a tap leaves for YouTube. */
function clipYtChipHTML(){ return `<span class="clip-ytchip">${esc(t("teams.clips.youtube"))}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17L17 7M8 7h9v9"/></svg></span>`; }

/* ---- open, step, close ---- */
function clipTheaterOpen(items, i, originEl){
  const d = clipEl();
  if (!d || !items || !items.length) return;
  const play = items.map((x, j) => j).filter(j => clipCan(items[j].c)), at = play.indexOf(i);
  const was = !!CT;
  if (!was) CLIP_RETURN = originEl || document.activeElement;
  if (CT) clearTimeout(CT.timer);
  CT = {items, play, pos: 0, seen: new Set(), tok: 0, timer: 0};
  if (play.length) clipWarm();            /* a no-op when the tap that got here already warmed it */
  d.classList.add("on");
  d.setAttribute("aria-hidden", "false");
  clipShow(i < 0 ? play.length : at >= 0 ? at : 0);
  clipQ("[data-clipclose]").focus({preventScroll: true});
  if (!was) layerPush("clipsheet", clipShut);
}

/* The close itself, which also stops the video; clipClose takes back the history entry too. */
function clipShut(){
  const d = clipEl();
  if (!d || !CT) return;
  clearTimeout(CT.timer);
  CT = null;
  clipPlayerStop();
  d.classList.remove("on", "end");
  d.setAttribute("aria-hidden", "true");
  const back = CLIP_RETURN;
  CLIP_RETURN = null;
  if (back && back.focus && back.isConnected) back.focus({preventScroll: true});
}
function clipClose(){ clipShut(); layerDone("clipsheet"); }

/* Show the clip at `pos` of the playable ones, and play it; past the last is the end card. */
function clipShow(pos){
  const d = clipEl(), end = pos >= CT.play.length;
  clearTimeout(CT.timer);
  CT.pos = pos;
  CT.tok++;
  d.classList.toggle("end", end);
  clipQ("[data-clipend]").hidden = !end;
  clipQ("[data-cliplink]").hidden = true;
  clipPaintBar();
  if (end){
    clipPlayerStop();
    clipSoundSync();
    return clipPaintEnd();
  }
  const x = CT.items[CT.play[pos]];
  CT.seen.add(pos);
  clipQ("[data-clipbox]").classList.toggle("tall", clipTall(x.c));
  const ps = x.ps || [x.p], uniq = k => [...new Set(ps.map(p => p[k]))].join("/");
  clipQ("[data-clipcap]").innerHTML = `<p class="clip-who"><b>${esc(ps.length > 1 ? clipNames(x) : x.p.n)}</b>${esc(uniq("pos"))} &middot; ${esc(uniq("team"))}</p><p class="clip-title">${esc(x.c.title)}</p>`;
  clipSoundSync();
  clipPlayerPlay(x.c.id);
}
function clipStep(d){
  const np = CT ? CT.pos + d : -1;
  if (np >= 0 && np <= CT.play.length) clipShow(np);
}

/* The counter, and the bottom row: previous, who is next, next. */
function clipPaintBar(){
  const n = CT.play.length, end = CT.pos >= n, nx = CT.items[CT.play[CT.pos + 1]];
  clipQ("[data-clipcount]").textContent = n ? t("teams.clips.of", {i: Math.min(CT.pos + 1, n), n}) : "";
  clipQ("[data-clipprev]").disabled = CT.pos <= 0;
  clipQ("[data-clipnext]").disabled = end;
  clipQ("[data-clipup]").textContent = end ? "" : nx ? t("teams.clips.upNext", {name: clipNames(nx)}) : t("teams.clips.last");
  const f = document.activeElement;
  if (f && f.disabled) clipQ("[data-clipclose]").focus({preventScroll: true});
}

/* The end card: how many played, then every clip that only plays on YouTube as a link. */
function clipPaintEnd(){
  const rows = CT.items.filter(x => !clipCan(x.c)), n = CT.seen.size;
  clipQ("[data-clipend]").innerHTML = `${n ? `<h2 class="clip-done">${esc(t("teams.clips.done", {n}))}</h2>` : ""}
    <ul class="clip-ends">${rows.map(x => `<li><a class="clip-row" href="${esc(clipYtUrl(x.c))}" target="_blank" rel="noopener">
      <span class="clip-thumb"><img src="${esc(clipThumbOf(x.c))}" alt="" loading="lazy" decoding="async"></span>
      <span class="clip-rw"><b>${esc(clipNames(x))}</b><span>${esc(x.c.title)}</span></span>${clipYtChipHTML()}</a></li>`).join("")}</ul>`;
}

/* ---- what the player tells us ---- */
function clipOnEnded(){ if (CT && CT.pos < CT.play.length) clipStep(1); }
function clipOnPlaying(){ clipSoundSync(); }
/* The pill is for a clip that is on screen while the sound is off. */
function clipSoundSync(){
  if (CT) clipQ("[data-clipsound]").hidden = !(CP.muted && CT.pos < CT.play.length);
}
/* This clip cannot play here: its box becomes the link. 101 and 150 are YouTube refusing an embed, so Play
   all moves on; any other code stays, the reader decides. */
function clipOnError(code){
  if (!CT || CT.pos >= CT.play.length) return;
  const x = CT.items[CT.play[CT.pos]], tok = CT.tok, link = clipQ("[data-cliplink]");
  clipPlayerStop();
  link.innerHTML = `<a class="clip-linka" href="${esc(clipYtUrl(x.c))}" target="_blank" rel="noopener"><img src="${esc(clipThumbOf(x.c))}" alt="">
    <span class="clip-ytchip">${clipYtMark()}${esc(t("teams.clips.onYouTube"))}</span></a>`;
  link.hidden = false;
  clipQ("[data-clipsound]").hidden = true;
  if (code === 101 || code === 150) CT.timer = setTimeout(() => { if (CT && CT.tok === tok) clipStep(1); }, CLIP_ERR_MS);
}

/* ---- the rings on the roster's heads (board.js marks them data-clips) ---- */
function clipRingHTML(p){
  const n = clipsOf(p.slug).length;
  return n ? ` data-clips="${n}" role="button" tabindex="0" aria-label="${esc(t("teams.clips.ring", {name: p.n, ...clipPlural(n)}))}"` : "";
}
function clipWireRings(v){
  v.querySelectorAll(".head[data-clips]").forEach(h => {
    const row = h.closest(".row"), open = e => {
      e.stopPropagation();
      const p = findPlayer(row.dataset.team, +row.dataset.i), items = p ? clipItemsOf(p).map(c => ({c, p})) : [];
      clipTheaterOpen(items, items.findIndex(x => clipCan(x.c)), h);
    };
    h.addEventListener("pointerdown", () => clipWarm());
    h.addEventListener("click", open);
    h.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); open(e); } });
  });
}

/* Bound once: the theater's markup is in shell.html and is never replaced, only painted. */
(() => {
  const d = clipEl();
  if (!d) return;
  d.addEventListener("click", e => {
    if (e.target.closest("[data-clipclose]")) clipClose();
    else if (e.target.closest("[data-clipprev]")) clipStep(-1);
    else if (e.target.closest("[data-clipnext]")) clipStep(1);
    else if (e.target.closest("[data-clipsound]")){ clipUnmute(); clipSoundSync(); }
  });
  d.addEventListener("keydown", e => {
    if (e.key !== "Tab") return;
    const f = [...d.querySelectorAll("button:not([disabled]), a[href]")].filter(x => x.offsetParent);
    if (e.shiftKey && document.activeElement === f[0]){ e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]){ e.preventDefault(); f[0].focus(); }
  });
  onSwipeX(d, clipStep);
  onPullDown(d, () => { const e = clipQ("[data-clipend]"); return e.hidden || e.scrollTop <= 0; }, () => !!CT, clipClose);
  document.addEventListener("keydown", e => {
    if (!CT) return;
    if (e.key === "Escape") clipClose();
    else if (e.key === "ArrowRight") clipStep(1);
    else if (e.key === "ArrowLeft") clipStep(-1);
  });
})();

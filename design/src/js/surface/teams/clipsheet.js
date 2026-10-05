/* ============================== ROSTER: THE CLIP SHEET ==============================
   A player's official clips (LIVE_CLIPS, design/clips.py), opened from the ring on his roster head or
   from the Week plays reel (reel.js). It is the game sheet's shape (surface/live/gamesheet.js): outside
   #view, Back, Escape, the scrim and a pull down close it (chrome/layers.js), focus goes back to
   where it came from.

   The stage shows YouTube's own thumbnail and a play button, and loads nothing else. A tap swaps in
   the nocookie embed, and only then does the IFrame API script load (it tells us a clip ended, so the
   next one starts). Where the embed cannot load (a file, a published Artifact whose frame policy
   refuses YouTube, a video that bans embedding) the stage is a plain link to youtube.com. A clip whose
   `embed` is false (YouTube refuses it on other sites: the NFL channel, MIN, SEA, SF; error 150) starts
   as that link, with a YouTube mark in the list; auto-advance and Play all skip it.

   Used by the reel: clipsOf, clipGameOf, clipWeekRow, clipData, clipCan, clipYtMark,
   clipSheetOpen(queue, i, originEl, all). */

let CLIP = null;         /* {queue, i, k, link} on screen: queue[i] is the player, k his clip; null = closed */
let CLIP_RETURN = null;
let CLIP_API = "";        /* the IFrame API script: "" not asked for, "loading", "ready" */
let CLIP_WAIT = [];       /* what waits for it */
let CLIP_BLOCKED = false; /* the page's frame policy refused YouTube */
const clipEl = () => document.getElementById("clipsheet");
/* Function declarations, so the reel can call them while the parts load, whatever their order. */
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
   where the page has no row for him yet (it lags the clips by a night). `row` is for the reel's TD badge. */
function clipWeekRow(p){
  const wk = clipData().week, row = p.slug && Number.isInteger(wk) ? gamelogRows(p.slug).find(r => r.wk === wk) || null : null;
  return {row, pts: row && typeof row.pts === "number" ? row.pts : null,
    line: row && CLIP_POS.includes(p.pos) ? seasonLine(p.pos, row) : null};
}
/* His clips in order; a player with none plays his game's highlights. */
function clipItemsOf(p){
  const own = clipsOf(p.slug), g = own.length ? null : clipGameOf(p.team);
  return g ? [{id: g.id, title: g.title, kind: "game", secs: g.secs, embed: g.embed}] : own;
}
/* Whether YouTube lets this clip play on another site; a block from before the field says yes. */
function clipCan(c){ return !!c && c.embed !== false; }
const clipFirst = p => clipItemsOf(p).findIndex(clipCan);   /* his first clip that plays here, -1 if none */
/* YouTube's mark, for a clip that opens YouTube instead of playing. */
function clipYtMark(){ return `<svg class="yt-mark" viewBox="0 0 24 24" aria-hidden="true"><path fill-rule="evenodd" d="M6 5h12a4 4 0 0 1 4 4v6a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V9a4 4 0 0 1 4-4zm4 4v6l5-3z"/></svg>`; }
function clipEmbedOk(){ return PAGE_SERVED() && !CLIP_BLOCKED; }
const clipDur = s => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
const clipThumb = id => `https://i.ytimg.com/vi/${encodeURIComponent(id)}/mqdefault.jpg`;
const clipPlural = n => ({n, s: n === 1 ? "" : "s"});
/* The first entry of the queue from `from` on that has anything to show, else -1; `play`: that has a
   clip that plays here. */
const clipSeek = (queue, from, play) => queue.findIndex((p, j) => j >= from && (play ? clipFirst(p) >= 0 : clipItemsOf(p).length));
const clipNow = () => CLIP && clipItemsOf(CLIP.queue[CLIP.i])[CLIP.k];

/* `all` is Play all: it starts at the first clip of the queue that plays here (none: the first entry,
   as its link). Otherwise the sheet opens on queue[i]'s first clip, playable or not. */
function clipSheetOpen(queue, i, originEl, all){
  const d = clipEl(), q = queue || [], from = i || 0, ok = all ? clipSeek(q, from, true) : -1;
  const at = ok >= 0 ? ok : clipSeek(q, from);
  if (!d || at < 0) return;
  if (!CLIP) CLIP_RETURN = originEl || document.activeElement;
  const was = !!CLIP;
  CLIP = {queue, i: at, k: ok >= 0 ? clipFirst(q[at]) : 0, link: false};
  clipPaint();
  d.scrollTop = 0;
  d.classList.add("on");
  d.setAttribute("aria-hidden", "false");
  document.getElementById("clipsheet-scrim").classList.add("on");
  d.querySelector("[data-clipclose]").focus({preventScroll: true});
  if (!was) layerPush("clipsheet", clipShut);
}

/* The close itself, which also stops the video; clipClose takes back the history entry too. */
function clipShut(){
  const d = clipEl();
  if (!d || !CLIP) return;
  CLIP = null;
  d.querySelector("iframe")?.remove();
  d.classList.remove("on");
  d.setAttribute("aria-hidden", "true");
  document.getElementById("clipsheet-scrim").classList.remove("on");
  const back = CLIP_RETURN;
  CLIP_RETURN = null;
  if (back && back.focus && back.isConnected) back.focus({preventScroll: true});
}
function clipClose(){ clipShut(); layerDone("clipsheet"); }

/* Another clip of the queue, in the sheet that is already open; `play` starts it. */
function clipGoto(i, k, play){
  const d = clipEl();
  if (!d || !CLIP) return;
  CLIP = {queue: CLIP.queue, i, k, link: false};
  clipPaint();
  d.scrollTop = 0;
  /* A clip that cannot play here is already its link; a tap on it lands there. */
  if (play && clipCan(clipNow())) clipPlay();
  else d.querySelector(play ? ".clip-poster" : "[data-clipclose]").focus({preventScroll: true});
}

/* A clip ended: his next one that plays here, else the next player of the queue who has one; the last rests. */
function clipAdvance(){
  if (!CLIP) return;
  const k = clipItemsOf(CLIP.queue[CLIP.i]).findIndex((c, j) => j > CLIP.k && clipCan(c));
  if (k >= 0) return clipGoto(CLIP.i, k, true);
  const nx = clipSeek(CLIP.queue, CLIP.i + 1, true);
  if (nx >= 0) clipGoto(nx, clipFirst(CLIP.queue[nx]), true);
}

/* The embed, in place of the thumbnail; focus follows it so the keyboard is not left on a button that went. */
function clipPlay(){
  const stage = clipEl().querySelector("[data-clipstage]"), c = clipNow();
  if (!stage || !c || !clipEmbedOk() || CLIP.link || !clipCan(c)) return;
  const origin = /^https?:/.test(location.origin) ? `&origin=${encodeURIComponent(location.origin)}` : "";
  stage.innerHTML = `<iframe src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(c.id)}?autoplay=1&playsinline=1&rel=0&enablejsapi=1${origin}"
    title="${esc(c.title)}" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe>`;
  const frame = stage.querySelector("iframe");
  frame.focus({preventScroll: true});
  clipApi(() => new YT.Player(frame, {events: {
    onStateChange: e => { if (e.data === 0 && frame.isConnected) clipAdvance(); },
    onError: () => { if (frame.isConnected) clipFailed(); },
  }}));
}

/* This clip cannot play here: its stage becomes the link. */
function clipFailed(){
  if (!CLIP) return;
  CLIP.link = true;
  clipPaint();
  clipEl().querySelector(".clip-poster")?.focus({preventScroll: true});
}

/* The IFrame API script, asked for on the first play and never before. */
function clipApi(then){
  if (CLIP_API === "ready") return then();
  CLIP_WAIT.push(then);
  if (CLIP_API) return;
  CLIP_API = "loading";
  window.onYouTubeIframeAPIReady = () => { CLIP_API = "ready"; CLIP_WAIT.splice(0).forEach(f => f()); };
  const s = document.createElement("script");
  s.src = "https://www.youtube.com/iframe_api";
  s.onerror = () => { CLIP_API = ""; CLIP_WAIT = []; };   /* the clip still plays; it just cannot hand on by itself */
  document.head.appendChild(s);
}

/* ---- the markup ---- */
const clipCloseHTML = () => `<button type="button" class="clip-x" data-clipclose aria-label="${esc(t("teams.clips.close"))}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button>`;
function clipHeadHTML(p){
  const w = clipWeekRow(p), wk = [w.pts !== null ? `<b>${w.pts.toFixed(1)}</b>` : "", w.line ? esc(w.line) : ""].filter(Boolean).join(" · ");
  return `<div class="clip-grab" aria-hidden="true"></div>
    <div class="clip-bar"><span class="clip-av">${headHTML(p)}</span>
      <div class="clip-who"><h2 class="clip-name">${esc(p.n)}</h2><p>${esc(p.pos)} · ${esc(p.team)}</p>${wk ? `<p class="clip-wk">${wk}</p>` : ""}</div>${clipCloseHTML()}</div>`;
}
const clipPlayIcon = `<span class="clip-play"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5l12 7-12 7z"/></svg></span>`;
/* The stage: the thumbnail and a play button; a link to YouTube where the embed cannot load, and from
   the start for a clip YouTube refuses to embed (no play button then: it does not play here). */
function clipStageHTML(c){
  const can = clipCan(c), img = `<img src="${clipThumb(c.id)}" alt="" decoding="async">${can ? clipPlayIcon : ""}`;
  const label = esc(t("teams.clips.play", {title: c.title}));
  const link = !clipEmbedOk() || CLIP.link || !can;
  return `<div class="clip-stage" data-clipstage>${link
    ? `<a class="clip-poster" href="https://www.youtube.com/watch?v=${encodeURIComponent(c.id)}" target="_blank" rel="noopener noreferrer" aria-label="${can ? label : `${esc(c.title)}. ${esc(t("teams.clips.onYouTube"))}`}">${img}<span class="clip-yt">${clipYtMark()}${esc(t("teams.clips.onYouTube"))}</span></a>`
    : `<button type="button" class="clip-poster" data-clipplay aria-label="${label}">${img}</button>`}</div>`;
}
const clipBarsHTML = items => items.length < 2 ? "" :
  `<div class="clip-bars" aria-hidden="true">${items.map((_, j) => `<i class="${j < CLIP.k ? "done" : j === CLIP.k ? "now" : ""}"></i>`).join("")}</div>`;
function clipCaptionHTML(c, items){
  const kick = {best_plays: t("teams.clips.bestPlays"), game: t("teams.clips.gameTitle")}[c.kind] || "";
  const of = items.length > 1 ? t("teams.clips.of", {i: CLIP.k + 1, n: items.length}) : "";
  return `<div class="clip-cap">${kick || of ? `<div class="clip-kick"><span>${esc(kick)}</span><span>${esc(of)}</span></div>` : ""}<p class="clip-title">${esc(c.title)}</p></div>`;
}
/* The rest of his clips, a tap shows one: it plays, or for a clip YouTube refuses to embed (marked)
   its stage is the link to YouTube. */
const clipListHTML = items => items.length < 2 ? "" : `<ul class="clip-list">${items.map((c, j) => j === CLIP.k ? "" :
  `<li><button type="button" class="clip-row" data-cliprow="${j}" aria-label="${esc(clipCan(c) ? t("teams.clips.play", {title: c.title}) : `${c.title}. ${t("teams.clips.onYouTube")}`)}">
    <span class="clip-thumb"><img src="${clipThumb(c.id)}" alt="" loading="lazy" decoding="async"></span>
    <span class="clip-rt">${esc(c.title)}</span>${clipCan(c) ? "" : clipYtMark()}<b>${clipDur(c.secs || 0)}</b></button></li>`).join("")}</ul>`;
/* Opened from Play all: who comes after this player, among those with a clip that plays here. */
function clipNextHTML(){
  const nx = clipSeek(CLIP.queue, CLIP.i + 1, true), q = CLIP.queue[nx];
  if (nx < 0) return "";
  return `<button type="button" class="clip-next" data-clipnext="${nx}"><span class="clip-av">${headHTML(q)}</span>
    <span class="clip-who"><b>${esc(t("teams.clips.upNext", {name: nameInitial(q.n)}))}</b><small>${esc(t("teams.clips.nextPlays", clipPlural(clipItemsOf(q).filter(clipCan).length)))}</small></span></button>`;
}
function clipPaint(){
  const d = clipEl(), p = CLIP && CLIP.queue[CLIP.i];
  if (!d || !p) return;
  const items = clipItemsOf(p), c = items[CLIP.k];
  d.innerHTML = clipHeadHTML(p) + clipStageHTML(c) + clipBarsHTML(items) + clipCaptionHTML(c, items) + clipListHTML(items) + clipNextHTML();
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
      const p = findPlayer(row.dataset.team, +row.dataset.i);
      if (p) clipSheetOpen([p], 0, h);
    };
    h.addEventListener("click", open);
    h.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); open(e); } });
  });
}

/* Bound once: the sheet's markup is replaced on every paint, its listeners are not. */
(() => {
  const d = clipEl();
  if (!d) return;
  d.addEventListener("click", e => {
    if (e.target.closest("[data-clipclose]")) return clipClose();
    if (e.target.closest("[data-clipplay]")) return clipPlay();
    const row = e.target.closest("[data-cliprow]"), nx = e.target.closest("[data-clipnext]");
    if (row) clipGoto(CLIP.i, +row.dataset.cliprow, true);
    else if (nx) clipGoto(+nx.dataset.clipnext, clipFirst(CLIP.queue[+nx.dataset.clipnext]), true);
  });
  d.addEventListener("keydown", e => {
    if (e.key !== "Tab") return;
    const f = [...d.querySelectorAll("button, a[href], iframe")];
    if (e.shiftKey && document.activeElement === f[0]){ e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]){ e.preventDefault(); f[0].focus(); }
  });
  document.getElementById("clipsheet-scrim").addEventListener("click", clipClose);
  onPullDown(d, () => d.scrollTop <= 0, () => !!CLIP, clipClose);
  document.addEventListener("keydown", e => { if (e.key === "Escape" && CLIP) clipClose(); });
  /* A frame policy that refuses YouTube (the published Artifact) says so here: the stage turns into the link. */
  document.addEventListener("securitypolicyviolation", e => {
    if (CLIP && /youtube/.test(e.blockedURI)){ CLIP_BLOCKED = true; clipFailed(); }
  });
})();

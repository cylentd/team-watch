/* ============================== CLIPS: THE ONE PLAYER ==============================
   The theater (clipsheet.js) plays every clip on one YouTube IFrame player, built once, hidden inside
   #clipsheet, and told what to load with loadVideoById. A new iframe per clip was slow to start and
   a phone may stop between clips; one player keeps what a first tap unlocked (sound, autoplay).

   clipWarm() is idempotent: it adds the preconnect hints, loads the IFrame API script, and builds the
   player. The rail's first touch or scroll and a press on a ring call it, so the API and the connection
   are ready by the click. A clip is never cued ahead: a cue the click's loadVideoById follows is lost
   on real YouTube and leaves the clip cued. Nothing here runs where clipEmbedOk() is false.

   Calls into clipsheet.js, which owns what is on screen: clipOnEnded, clipOnError(code), clipOnPlaying.
   Test hook: a page that already has window.YT.Player (a stub) never loads the script. */

let CLIP_API = "";            /* the IFrame API script: "" not asked for, "loading" */
let CLIP_WAIT = [];           /* what waits for it */
let CLIP_BLOCKED = false;     /* the page's frame policy refused YouTube */
const CP = {
  player: null,     /* the one YT.Player, once the API is in */
  ready: false,     /* its onReady has fired */
  load: null,       /* a clip to play the moment it is ready */
  muted: false,     /* the browser blocked sound: playing muted, the pill offers it back */
  loud: false,      /* the reader tapped for sound: every later clip keeps it */
};
const CLIP_HOSTS = ["https://www.youtube-nocookie.com", "https://i.ytimg.com"];

function clipEmbedOk(){ return PAGE_SERVED() && !CLIP_BLOCKED; }

function clipPreconnect(){
  CLIP_HOSTS.forEach(h => {
    if (document.head.querySelector(`link[rel="preconnect"][href="${h}"]`)) return;
    const l = document.createElement("link");
    l.rel = "preconnect";
    l.href = h;
    document.head.appendChild(l);
  });
}

/* The IFrame API script, asked for once. */
function clipApi(then){
  if (window.YT && window.YT.Player) return then();
  CLIP_WAIT.push(then);
  if (CLIP_API) return;
  CLIP_API = "loading";
  window.onYouTubeIframeAPIReady = () => { CLIP_API = ""; CLIP_WAIT.splice(0).forEach(f => f()); };
  const s = document.createElement("script");
  s.src = "https://www.youtube.com/iframe_api";
  /* The script did not come (a blocker, a filter, offline): nothing plays here, and a theater that is
     waiting for the player lists the clips as links. */
  s.onerror = () => { CLIP_API = ""; CLIP_WAIT = []; CLIP_BLOCKED = true; clipOnError(0); };
  document.head.appendChild(s);
}

function clipWarm(){
  if (!clipEmbedOk()) return;
  clipPreconnect();
  if (!CP.player) clipApi(clipMakePlayer);
}

function clipMakePlayer(){
  if (CP.player || !document.getElementById("clip-yt")) return;
  const origin = /^https?:/.test(location.origin) ? {origin: location.origin} : {};
  CP.player = new YT.Player("clip-yt", {
    host: CLIP_HOSTS[0], width: "100%", height: "100%",
    playerVars: {playsinline: 1, rel: 0, enablejsapi: 1, ...origin},
    events: {onReady: clipPlayerReady, onStateChange: clipPlayerState, onError: e => clipOnError(e.data),
      onAutoplayBlocked: clipPlayerBlocked},
  });
}

function clipPlayerReady(){
  CP.ready = true;
  const go = CP.load;
  CP.load = null;
  if (go) CP.player.loadVideoById(go);
}

/* ENDED (0) hands on; PLAYING (1) is where a start the browser muted shows. */
function clipPlayerState(e){
  if (e.data === 0) clipOnEnded();
  else if (e.data === 1){
    if (!CP.loud && CP.player.isMuted && CP.player.isMuted()) CP.muted = true;
    clipOnPlaying();
  }
}

/* The browser refused sound: play muted, and the pill asks for it back. */
function clipPlayerBlocked(){
  CP.muted = true;
  CP.player.mute();
  CP.player.playVideo();
  clipOnPlaying();
}

function clipUnmute(){
  CP.muted = false;
  CP.loud = true;
  if (CP.ready) CP.player.unMute();
}

/* Play `id` now, or the moment the player is ready. */
function clipPlayerPlay(id){
  if (CP.ready) return CP.player.loadVideoById(id);
  CP.load = id;
  clipWarm();
}

function clipPlayerStop(){
  CP.load = null;
  if (CP.ready) CP.player.stopVideo();
}

/* A frame policy that refuses YouTube (the published Artifact) says so here. */
document.addEventListener("securitypolicyviolation", e => {
  if (!/youtube/.test(e.blockedURI)) return;
  CLIP_BLOCKED = true;
  clipOnError(0);
});

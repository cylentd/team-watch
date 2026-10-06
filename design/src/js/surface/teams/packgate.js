/* The pack in the starters' place (2026-10-05, the round-4 storyboard). On a team the reader follows,
   in Cards mode, until this week's pack is ripped or skipped (pack.js packGated): the starters' grid
   keeps its geometry with every card face down and dimmed, and the sealed pack stands over it near
   its top with Rip and Skip under it. The bench and the This week row draw as always.

   It turns by itself as a tap cue (STYLE.md motion rule 1): one slow turn in 14 s, then 2 s at rest
   facing the reader, only while it is on screen and the tab is visible, never under reduced
   motion. A drag turns it with the finger and it springs back to the front; a tap opens it. Rip
   grows it onto the stage (packshow.js pkGrow); Skip shrinks it into the Starters rule's chip
   ("Open week 5") while the cards turn face up in a wave. */
const PK_IDLE_TURN = 14000, PK_IDLE_REST = 2000;
const PK_DRAG = 1.1;              // degrees per pixel dragged: a thumb's swipe across the pack is a turn
const PK_WAVE = 60;               // ms between two cards turning face up after a Skip
const PK_IDLES = new Set();       // the gates on the page whose turn may be running
let PK_IDLE_WIRED = false;        // one visibilitychange listener for all of them
const pkTok = (el, k) => getComputedStyle(el).getPropertyValue(k).trim();
const pkMs = v => parseFloat(v) * (/ms$/.test(v) ? 1 : 1000) || 0;

/* A face-down slot: the card itself, turned to the set's back (cards.css .tc.down, .tc-cb). */
function packCardDown(html){
  return html.replace('class="tc ', 'class="tc down ')
    .replace('<div class="tc-flip">', '<div class="tc-flip"><i class="tc-cb" aria-hidden="true"><b>TW</b></i>');
}

function packGateHTML(team){
  const wk = schedWeek();
  return `<div class="pk-gate${packShowing() ? " away" : ""}" data-testid="roster-pack-gate" data-gate="${wk}">
    <div class="pk-gpack"><div class="pk-gz">${packSealHTML(team, wk, packCards(team))}</div></div>
    <div class="pk-gbtns"><button class="pk-rip" type="button" data-testid="roster-pack-rip" data-pkrip>${t("teams.pack.rip")}</button><button class="pk-skip" type="button" data-testid="roster-pack-skip" data-pkskip>${t("teams.pack.skip")}</button></div>
  </div>`;
}

function packGateWire(v, team, gate){
  const wk = +gate.dataset.gate, pk = gate.querySelector(".pk-gpack");
  const open = () => packShow(team, wk, pk);
  packSpin(pk, packIdle(gate), open);
  gate.querySelector("[data-pkrip]").addEventListener("click", open);
  gate.querySelector("[data-pkskip]").addEventListener("click", () => packSkip(v, team, gate));
}

/* The idle turn. Its clock is the time it has been allowed to run, so a pause (off screen, a hidden
   tab, a finger on it) resumes where it was; it starts in the rest, facing the reader. */
function packIdle(gate){
  const S = {gate, glow: gate.querySelector(".pack-glow"), on: false, held: false, raf: 0, t: PK_IDLE_TURN, last: 0};
  if (!S.glow || REDUCED() || typeof IntersectionObserver === "undefined") return S;
  S.io = new IntersectionObserver(es => { S.on = es[es.length - 1].isIntersecting; packIdleGo(S); });
  S.io.observe(gate);
  PK_IDLES.add(S);
  if (!PK_IDLE_WIRED){
    PK_IDLE_WIRED = true;
    document.addEventListener("visibilitychange", () => PK_IDLES.forEach(packIdleGo));
  }
  return S;
}
const packIdleLive = S => S.gate.isConnected && !S.gate.classList.contains("going") && !S.gate.classList.contains("away");
function packIdleGo(S){
  if (!packIdleLive(S)){ S.io?.disconnect(); PK_IDLES.delete(S); return; }
  if (S.raf || !S.on || S.held || document.visibilityState !== "visible") return;
  S.last = 0;
  S.raf = requestAnimationFrame(now => packIdleFrame(S, now));
}
function packIdleFrame(S, now){
  S.raf = 0;
  if (!packIdleLive(S) || !S.on || S.held || document.visibilityState !== "visible") return packIdleGo(S);
  S.t += S.last ? Math.min(100, now - S.last) : 0;
  S.last = now;
  const k = Math.min(1, S.t % (PK_IDLE_TURN + PK_IDLE_REST) / PK_IDLE_TURN);
  S.glow.style.rotate = `y ${(180 - 180 * Math.cos(Math.PI * k)).toFixed(2)}deg`;
  S.raf = requestAnimationFrame(n => packIdleFrame(S, n));
}

/* A drag turns it as far as the finger goes; let go and it springs to the front nearest it, then the
   turn picks up again from its rest. A press that never moved is a tap, and the click opens it. */
function packSpin(pk, S, open){
  const glow = S.glow, angle = () => parseFloat((getComputedStyle(glow).rotate.match(/(-?[\d.]+)deg/) || [0, 0])[1]);
  let x0 = 0, a0 = 0, down = false, moved = false;
  pk.addEventListener("pointerdown", e => {
    down = true; moved = false; x0 = e.clientX; a0 = angle(); S.held = true;
    glow.getAnimations().forEach(a => a.cancel());
    glow.style.rotate = `y ${a0}deg`;
  });
  pk.addEventListener("pointermove", e => {
    if (!down) return;
    const dx = e.clientX - x0;
    if (!moved && Math.abs(dx) < 6) return;
    if (!moved){ moved = true; pk.setPointerCapture?.(e.pointerId); pk.classList.add("dragging"); }
    glow.style.rotate = `y ${(a0 + dx * PK_DRAG).toFixed(1)}deg`;
  });
  const up = () => {
    if (!down) return;
    down = false; pk.classList.remove("dragging");
    if (!moved){ S.held = false; return packIdleGo(S); }
    const from = angle(), to = Math.round(from / 360) * 360;
    const rest = () => { glow.style.rotate = ""; S.held = false; S.t = PK_IDLE_TURN; packIdleGo(S); };
    if (REDUCED()) return rest();
    glow.style.rotate = `y ${to}deg`;
    glow.animate([{rotate: `y ${from}deg`}, {rotate: `y ${to}deg`}], {duration: pkMs(pkTok(glow, "--dur-pop")), easing: pkTok(glow, "--spring-pop")})
      .finished.then(rest, () => {});
  };
  pk.addEventListener("pointerup", up);
  pk.addEventListener("pointercancel", up);
  pk.addEventListener("click", () => { if (!moved) open(); });
}

/* Skip: the pack shrinks into the chip's small pack, the dimming lifts, and the cards turn face up. */
async function packSkip(v, team, gate){
  if (gate.classList.contains("going")) return;
  packSkipMark(team, +gate.dataset.gate);
  gate.classList.add("going");
  const zone = gate.parentElement, grid = zone.querySelector(".cardgrid"), pk = gate.querySelector(".pk-gpack");
  const chip = v.querySelector("[data-pkopen]"), icon = chip && chip.querySelector(".rm-pk");
  chip?.classList.remove("wait");
  zone.classList.add("open");
  grid.removeAttribute("inert");
  if (icon && !REDUCED()){
    const a = pk.getBoundingClientRect(), b = icon.getBoundingClientRect();
    icon.style.visibility = "hidden";
    await pk.animate([{translate: "0 0", scale: "1"},
      {translate: `${b.left + b.width / 2 - (a.left + a.width / 2)}px ${b.top + b.height / 2 - (a.top + a.height / 2)}px`, scale: String(b.height / a.height)}],
      {duration: pkMs(pkTok(pk, "--dur-pop")), easing: pkTok(pk, "--ease"), fill: "forwards"}).finished.catch(() => {});
    icon.style.visibility = "";
  }
  gate.remove();
  packWave(grid);
}

/* The starters turn face up one after another, left to right and down, the metals shining as they land. */
function packWave(grid){
  const cards = [...grid.querySelectorAll(".tc.down")];
  if (REDUCED()) return cards.forEach(el => el.classList.remove("down"));
  cards.forEach((el, n) => setTimeout(() => {
    if (!el.isConnected) return;
    el.classList.replace("down", "up");
    const flip = el.querySelector(".tc-flip"), done = () => el.classList.remove("up");
    flip.animate([{transform: "rotateY(180deg)"}, {transform: "rotateY(0deg)"}], {duration: pkMs(pkTok(el, "--dur-flip")), easing: pkTok(el, "--spring")})
      .finished.then(() => { done(); if (/\btier-(silver|gold|holo)\b/.test(el.className)) el.classList.add("shine"); }, done);
  }, 200 + n * PK_WAVE));
}

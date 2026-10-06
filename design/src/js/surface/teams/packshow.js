/* The pack's stage (2026-09-25, David's storyboard; reworked 2026-10-05): a dark stage the sealed
   pack grows onto from where it was tapped (the starters' place, or the Starters rule's chip). Rip
   it (drag across the top) and flakes burst from the tear; the cards then rise one at a time to the
   centre, worst first (packdeal.js): stock cards flick past, a metal holds with its label and a
   shine, a signed card holds again while it is signed, and the best card, last, gets the moment.
   Each drops into a pile at the foot of the screen; then the stage fades to the roster, where the
   pack's slots were left empty, and each card flies home into its own slot. ✕ before the rip puts
   the pack back on the page; after it, it skips to the roster. Reduced motion skips straight to the
   roster. One state object (S) carries the run. */
let PACK_SHOW = null;       // {key, order}: the pack on the stage; its slots on the page stay empty
const packShowing = () => !!PACK_SHOW;

/* A pack card is left out of its slot (kept in place, invisible) while the stage shows it. */
function packFaceDown(team, i, html){
  if (!PACK_SHOW || PACK_SHOW.key !== `${team.key}-${schedWeek()}` || !PACK_SHOW.order.has(i)) return html;
  return html.replace('class="tc ', `data-pk="${PACK_SHOW.order.get(i)}" class="tc pk-slot `);
}

const pkSpring = el => getComputedStyle(el).getPropertyValue("--spring").trim() || "ease-out";

/* A tap while the cards are dealt hurries the card on the stage (2026-09-25): its running motion
   plays PK_RUSH times faster, its pauses end, and the next card comes at the normal pace, so a
   reader can tap through the pack card by card. S.rush is cleared as each card is dealt. */
const PK_RUSH = 6;
function pkSleep(S, ms){
  if (S.skip || S.rush) return Promise.resolve();
  return new Promise(r => {
    const done = () => { clearTimeout(id); S.wake.delete(done); r(); };
    const id = setTimeout(done, ms);
    S.wake.add(done);
  });
}
function pkAnim(S, el, frames, opts){
  const a = el.animate(frames, opts);
  if (S.rush) a.updatePlaybackRate(PK_RUSH);
  return a;
}
function pkHurry(S){
  // Not during the best card's reveal (2026-09-27): it is the payoff, and a stray tap skipped it.
  if (!S.ripped || S.homing || S.skip || S.rush || S.hero) return;
  S.rush = true;
  S.st.getAnimations({subtree: true}).forEach(a => { if (a.effect.getTiming().iterations !== Infinity) a.updatePlaybackRate(PK_RUSH); });
  [...S.wake].forEach(done => done());
}

/* `from` is what was tapped (the gate's pack, the chip's small pack): the stage's pack grows out of it. */
function packShow(team, wk, from){
  if (PACK_SHOW || !wk) return;
  const cards = packCards(team);
  if (!packHas(team)) return;
  const at = pkFrom(from);
  PACK_SHOW = {key: `${team.key}-${wk}`, order: new Map(cards.map((c, k) => [c.i, k]))};
  const st = document.createElement("div");
  st.className = "pk-stage"; st.dataset.testid = "roster-pack-stage";
  st.setAttribute("role", "dialog"); st.setAttribute("aria-modal", "true"); st.setAttribute("aria-label", t("teams.pack.stage"));
  st.innerHTML = `<div class="pk-back"></div><div class="pk-rays"></div><div class="pk-flash"></div><div class="pk-wave"></div>
    <button class="pk-close" type="button" aria-label="${t("teams.pack.closeLabel")}">✕</button>
    <p class="pk-msg" data-testid="roster-pack-msg" aria-live="polite">${t("teams.pack.lead", {wk})}</p>
    <div class="pk-center" data-testid="roster-pack-center">${packSealHTML(team, wk, cards)}</div>
    <p class="pk-hint">${t("teams.pack.hint")}</p><p class="pk-count" data-testid="roster-pack-count" aria-hidden="true"></p>`;
  document.body.appendChild(st);
  document.body.classList.add("pk-open");
  const S = {st, team, wk, cards, ripped: false, skip: false, rush: false, homing: false, wake: new Set(), shown: [], best: packBest(cards)};
  st.addEventListener("click", e => { if (!e.target.closest(".pk-close")) pkHurry(S); });
  S.cw = () => document.querySelector("#view .cards .tc")?.offsetWidth || 114;   // a roster card's width, read when dealt
  // The pack's photos, the sharpest size cut, loaded and decoded while the reader tears.
  S.ready = Promise.all(cards.map(c => pkBestHead(c.p)).filter(Boolean).map(src => {
    const im = new Image(); im.src = src;
    return im.decode().catch(() => {});
  }));
  S.key = e => { if (e.key === "Escape") pkQuit(S); };
  document.addEventListener("keydown", S.key);
  layerPush("pack", () => pkQuit(S, true));
  st.querySelector(".pk-close").addEventListener("click", () => pkQuit(S));
  // Each eighth of the tear: a tick under the finger and a pinch of foil from the tear point.
  wireRip(st.querySelector(".pack-seal"), () => pkRip(S), (x, y) => { packBuzz(6); packBurst(x, y, {n: 6, tier: S.best, spread: .35}); },
    (e, nudge) => pkTilt(S, e, nudge));
  pkAim(S);
  render();                     // the page hides its own copy of the pack while the stage holds it
  if (!REDUCED()) pkGrow(S, at);
}

/* Where the tapped thing sits, and how far the gate's pack had turned, read before render() redraws it. */
function pkFrom(el){
  if (!el || !el.isConnected) return null;
  const r = el.getBoundingClientRect(), turn = el.querySelector?.(".pack-glow");
  const deg = turn ? parseFloat((getComputedStyle(turn).rotate.match(/(-?[\d.]+)deg/) || [0, 0])[1]) : 0;
  return {x: r.left + r.width / 2, y: r.top + r.height / 2, h: r.height, deg: ((deg + 180) % 360 + 360) % 360 - 180};
}
/* The pack grows from where it was tapped to the middle of the stage (FLIP: the stage lays it out in
   its place, then it is moved back to the tap and let go), while the room darkens around it. With
   nothing to grow from it spins in to its lean, back first, so it arrives as a thing with a body. */
function pkGrow(S, at){
  S.st.querySelectorAll(".pk-back,.pk-msg,.pk-hint,.pk-close").forEach(x => x.animate([{opacity: 0}, {opacity: 1}], {duration: 260}));
  const glow = S.st.querySelector(".pk-center .pack-glow"), c = S.st.querySelector(".pk-center");
  if (!at){
    glow.animate([{transform: "rotateX(14deg) rotateY(-376deg) scale(.6)"}, {transform: "rotateX(6deg) rotateY(-22deg)"}],
      {duration: 850, easing: "cubic-bezier(.2,.9,.3,1.04)"});
    return;
  }
  const r = c.getBoundingClientRect();
  glow.animate([{translate: `${at.x - (r.left + r.width / 2)}px ${at.y - (r.top + r.height / 2)}px`, scale: String(at.h / r.height), rotate: `y ${at.deg}deg`},
    {translate: "0 0", scale: "1", rotate: "y 0deg"}], {duration: 560, easing: pkSpring(glow)});
}

/* The sealed pack turns toward the mouse and its foil's shine follows it (--mx/--my). It turns
   side to side only (2026-09-27): it used to tip up and down too, and a mouse coming at the strip
   from above tipped it back, away from the tear. The turn is measured against the pack, not the
   window: the pointer a pack's width from its centre is the full 26°. */
const PK_AIM = 26, PK_REST = -22;          // degrees; PK_REST is packshow.css's resting turn
function pkLean(S, deg, shine){
  const c = S.st.querySelector(".pk-center"), seal = c && c.querySelector(".pack-seal");
  if (!seal) return;
  c.style.setProperty("--pry", `${deg.toFixed(1)}deg`);
  seal.style.setProperty("--mx", `${Math.round(50 + Math.max(-1, Math.min(1, shine)) * 40)}%`);
}
function pkAim(S){
  S.st.addEventListener("pointermove", e => {
    if (e.pointerType !== "mouse" || S.ripped || S.st.classList.contains("pk-drag")) return;
    const c = S.st.querySelector(".pk-center"), seal = c && c.querySelector(".pack-seal");
    // Over the strip it holds still (2026-09-26): turning away from a pointer about to grab the
    // strip turned the strip out from under it, and the press landed on the empty stage.
    if (!seal || seal.classList.contains("tearing") || e.target.closest?.(".pack-top")) return;
    const r = c.getBoundingClientRect(), dx = Math.max(-1, Math.min(1, (e.clientX - (r.left + r.width / 2)) / r.width));
    S.st.classList.add("pk-aim");
    pkLean(S, dx * PK_AIM, dx);
  });
}

/* A drag on the pack's body (below the strip) spins it with the finger or the mouse, as far round
   as the drag goes: a drag of the pack's width is three quarters of a turn, so its side, its back and its front
   again come round (2026-09-27; it stopped at 120° and a phone's short drag never reached the
   back). Let go and it settles, on the spring in packshow.css, at its resting turn nearest to
   where it was, so a spin that got most of the way round carries on to the front instead of
   unwinding. Then the whole turns are dropped while no transition runs, which changes nothing on
   screen. A tap that did not move tugs the strip instead, to say where to tear. */
const PK_SPIN = 270;                       // degrees per pack width dragged: one swipe across a phone is a full turn
function pkTilt(S, e, nudge){
  const c = S.st.querySelector(".pk-center"), seal = c && c.querySelector(".pack-seal");
  if (!seal || S.ripped) return;
  const x0 = e.clientX, y0 = e.clientY, w = seal.getBoundingClientRect().width;
  const from = parseFloat(c.style.getPropertyValue("--pry")) || PK_REST;
  let moved = false, deg = from;
  seal.setPointerCapture?.(e.pointerId);
  S.st.classList.add("pk-drag");
  const move = ev => {
    const dx = ev.clientX - x0;
    if (!moved && Math.hypot(dx, ev.clientY - y0) < 6) return;
    moved = true;
    deg = from + dx / w * PK_SPIN;
    pkLean(S, deg, Math.sin((deg - PK_REST) * Math.PI / 180));
  };
  const up = () => {
    seal.removeEventListener("pointermove", move);
    seal.removeEventListener("pointerup", up);
    seal.removeEventListener("pointercancel", up);
    S.st.classList.remove("pk-drag");
    if (!moved) return nudge();
    S.st.classList.remove("pk-aim");
    const turns = Math.round((deg - PK_REST) / 360);
    pkLean(S, PK_REST + turns * 360, 0);
    seal.style.removeProperty("--mx");
    if (!turns) return c.style.removeProperty("--pry");
    const glow = c.querySelector(".pack-glow");
    glow.addEventListener("transitionend", () => {
      if (S.st.classList.contains("pk-drag")) return;          // a new drag has begun from here
      glow.style.transition = "none";
      c.style.removeProperty("--pry");
      void glow.offsetWidth;
      glow.style.transition = "";
    }, {once: true});
  };
  seal.addEventListener("pointermove", move);
  seal.addEventListener("pointerup", up);
  seal.addEventListener("pointercancel", up);
}

/* A pack card's photo: the largest file cut for him (512, else 256, else 96px), or null. */
function pkBestHead(p){
  const pick = m => typeof m !== "undefined" && m && p.slug ? m[p.slug] : null;
  return pick(typeof HEADS_XL !== "undefined" ? HEADS_XL : null) || pick(typeof HEADS_LG !== "undefined" ? HEADS_LG : null) || pick(HEADS);
}

/* ✕, Escape or Back. Before the rip the pack goes back on the page; after it, straight to the end. */
function pkQuit(S, fromBack){
  if (!fromBack) layerDone("pack");
  if (S.ripped){ S.skip = S.quit = true; [...S.wake].forEach(done => done()); S.st.getAnimations({subtree: true}).forEach(a => { if (a.effect.getTiming().iterations !== Infinity) a.finish(); }); return; }
  pkClose(S);
}
function pkClose(S){
  PACK_SHOW = null;
  S.st.remove();
  document.body.classList.remove("pk-open");
  document.removeEventListener("keydown", S.key);
  render();
}

async function pkRip(S){
  S.ripped = true;
  packMark(S.team, S.wk);
  render();                     // the starters' place gives way to their slots, kept empty until each card lands
  packBuzz(18);
  S.st.querySelector(".pk-hint").textContent = t("teams.pack.faster");
  S.st.classList.add("pk-ripped");
  const center = S.st.querySelector(".pk-center"), seal = center.querySelector(".pack-seal");
  if (REDUCED()){ center.remove(); S.skip = true; }
  else {
    // The strip flies off in 3D, turning over as it goes, while the pack turns to face the reader
    // (it tipped back as well until 2026-09-27, which read as the pack pulling away from the tear).
    const r = seal.getBoundingClientRect();
    packBurst(r.left + r.width / 2, r.top + 16, {n: 46, tier: S.best});
    seal.querySelector(".slashes")?.classList.add("morph");   // the logo's // crosses into an X, as the header's does
    const out = "cubic-bezier(.25,1,.5,1)";
    await Promise.all([
      seal.querySelector(".pack-top").animate([
        {transform: "translate3d(0,0,0) rotateX(0) rotateZ(0)", opacity: 1},
        {transform: "translate3d(40px,-46px,40px) rotateX(40deg) rotateZ(-10deg)", opacity: 1, offset: .35},
        {transform: "translate3d(150px,-170px,90px) rotateX(120deg) rotateZ(-38deg)", opacity: 0}],
        {duration: 440, easing: out, fill: "forwards"}).finished,
      center.querySelector(".pack-glow").animate([{transform: "rotateX(6deg) rotateY(0deg)"}],
        {duration: 380, easing: out, fill: "forwards"}).finished]);
    S.pack = center;
  }
  await pkDeal(S);
  await pkHome(S);
}

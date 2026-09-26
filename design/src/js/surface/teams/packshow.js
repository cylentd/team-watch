/* The pack's stage (2026-09-25, David's storyboard): a black stage with the sealed pack in the middle.
   Rip it (drag across the top, or tap) and flakes burst from the tear; the cards then come out one
   at a time in the centre, worst first, turn over by themselves, and shrink away into a pile at the
   foot of the screen. The best card is last and gets the moment: rays behind it, a shake, a flash,
   a burst in its tier's colours, a spin a size up, its signature written in. Then the stage fades
   to the roster, where the pack's slots were left empty, and each card in the pile flies home
   into its own slot. ✕ before the rip puts the pack back on the page; after it, it skips to the
   roster. Reduced motion skips straight to the roster. One state object (S) carries the run. */
let PACK_SHOW = null;       // {key, order}: the pack on the stage; its slots on the page stay empty
const packShowing = () => !!PACK_SHOW;

/* A pack card is left out of its slot (kept in place, invisible) while the stage shows it. */
function packFaceDown(team, i, html){
  if (!PACK_SHOW || PACK_SHOW.key !== `${team.key}-${packWeek()}` || !PACK_SHOW.order.has(i)) return html;
  return html.replace('class="tc ', `data-pk="${PACK_SHOW.order.get(i)}" class="tc pk-slot `);
}

// Spelled out one call each: assemble.py --check finds a key only in a literal lookup.
const PACK_TIER_LABEL = {one: () => t("teams.pack.tier.one"), sig: () => t("teams.pack.tier.sig"), ur: () => t("teams.pack.tier.ur"),
  r: () => t("teams.pack.tier.r"), c: () => t("teams.pack.tier.c")};
const pkLabel = c => `<b>${t("teams.card.rank", {n: c.rank, pos: esc(c.p.pos)})}</b> · ${PACK_TIER_LABEL[cardTier(c.rank)]()}`
  + (cardSigned(c.p) ? ` · <em class="pk-signed-tag">${t("teams.pack.signed")}</em>` : "");
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
  if (!S.ripped || S.homing || S.skip || S.rush) return;
  S.rush = true;
  S.st.getAnimations({subtree: true}).forEach(a => { if (a.effect.getTiming().iterations !== Infinity) a.updatePlaybackRate(PK_RUSH); });
  [...S.wake].forEach(done => done());
}

function packShow(team, wk){
  if (PACK_SHOW || !wk) return;
  const cards = packCards(team);
  if (!cards.length) return;
  PACK_SHOW = {key: `${team.key}-${wk}`, order: new Map(cards.map((c, k) => [c.i, k]))};
  const st = document.createElement("div");
  st.className = "pk-stage";
  st.setAttribute("role", "dialog"); st.setAttribute("aria-modal", "true"); st.setAttribute("aria-label", t("teams.pack.stage"));
  st.innerHTML = `<div class="pk-back"></div><div class="pk-light"></div><div class="pk-floor"></div><div class="pk-rays"></div><div class="pk-flash"></div>
    <button class="pk-close" type="button" aria-label="${t("teams.pack.closeLabel")}">✕</button>
    <p class="pk-msg" aria-live="polite">${t("teams.pack.lead", {wk, n: cards.length})}</p>
    <div class="pk-center">${packSealHTML(team, wk, cards)}</div>
    <p class="pk-hint">${t("teams.pack.hint")}</p>`;
  document.body.appendChild(st);
  document.body.classList.add("pk-open");
  const S = {st, team, wk, cards, ripped: false, skip: false, rush: false, homing: false, wake: new Set(), shown: [], best: cardTier(cards[cards.length - 1].rank)};
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
  render();                     // the page drops its own copy of the pack while the stage holds it
  if (!REDUCED()) st.animate([{opacity: 0}, {opacity: 1}], {duration: 260});
}

/* The sealed pack leans toward the mouse and its foil's shine follows it (--mx/--my). The lean is
   measured against the pack, not the window: the pointer a pack's width from its centre is the
   full 16° up or down and 26° across (it was the window's half, so a big screen needed a long
   reach for 14°, 2026-09-25). */
const PK_AIM_X = 16, PK_AIM_Y = 26;
function pkLean(S, dx, dy){
  const c = S.st.querySelector(".pk-center"), seal = c && c.querySelector(".pack-seal");
  if (!seal) return;
  c.style.setProperty("--prx", `${(-dy * PK_AIM_X).toFixed(1)}deg`);
  c.style.setProperty("--pry", `${(dx * PK_AIM_Y).toFixed(1)}deg`);
  seal.style.setProperty("--mx", `${Math.round(50 + dx * 40)}%`);
  seal.style.setProperty("--my", `${Math.round(50 + dy * 40)}%`);
}
function pkAim(S){
  S.st.addEventListener("pointermove", e => {
    if (e.pointerType !== "mouse" || S.ripped || S.st.classList.contains("pk-drag")) return;
    const c = S.st.querySelector(".pk-center"), seal = c && c.querySelector(".pack-seal");
    if (!seal || seal.classList.contains("tearing")) return;
    const r = c.getBoundingClientRect(), clamp = v => Math.max(-1, Math.min(1, v));
    S.st.classList.add("pk-aim");
    pkLean(S, clamp((e.clientX - (r.left + r.width / 2)) / r.width), clamp((e.clientY - (r.top + r.height / 2)) / r.height));
  });
}

/* A drag on the pack's body (below the strip) turns it with the finger or the mouse, up to 1.6x
   the hover lean, the foil's shine going with it; let go and it springs back to rest (the
   transition in packshow.css). A tap that did not move tugs the strip instead, to say where to tear. */
function pkTilt(S, e, nudge){
  const c = S.st.querySelector(".pk-center"), seal = c && c.querySelector(".pack-seal");
  if (!seal || S.ripped) return;
  const x0 = e.clientX, y0 = e.clientY, r = seal.getBoundingClientRect();
  const clamp = v => Math.max(-1.6, Math.min(1.6, v));
  let moved = false;
  seal.setPointerCapture?.(e.pointerId);
  S.st.classList.add("pk-drag");
  const move = ev => {
    const dx = ev.clientX - x0, dy = ev.clientY - y0;
    if (!moved && Math.hypot(dx, dy) < 6) return;
    moved = true;
    pkLean(S, clamp(dx / (r.width * .6)), clamp(dy / (r.height * .6)));
  };
  const up = () => {
    seal.removeEventListener("pointermove", move);
    seal.removeEventListener("pointerup", up);
    seal.removeEventListener("pointercancel", up);
    S.st.classList.remove("pk-drag");
    if (!moved) return nudge();
    S.st.classList.remove("pk-aim");
    ["--prx", "--pry"].forEach(k => c.style.removeProperty(k));
    ["--mx", "--my"].forEach(k => seal.style.removeProperty(k));
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

/* The stage's light: a card's tier colour, stronger the rarer (null: the room's plain low light). */
const PK_LIGHT = {c: ["--ink-rgb", .12], r: ["--uncommon-2-rgb", .3], ur: ["--gold-2-rgb", .38], sig: ["--epic-2-rgb", .48], one: ["--holo-3-rgb", .6]};
function pkLight(S, tier){
  const [rgb, a] = PK_LIGHT[tier] || ["--ink-rgb", .08];
  S.st.style.setProperty("--pl", `var(${rgb})`);
  S.st.style.setProperty("--pa", String(a));
}

/* ✕, Escape or Back. Before the rip the pack goes back on the page; after it, straight to the end. */
function pkQuit(S, fromBack){
  if (!fromBack) layerDone("pack");
  if (S.ripped){ S.skip = true; S.st.getAnimations({subtree: true}).forEach(a => { if (a.effect.getTiming().iterations !== Infinity) a.finish(); }); return; }
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
  packBuzz(18);
  S.st.querySelector(".pk-hint").textContent = t("teams.pack.faster");
  S.st.classList.add("pk-ripped");
  const center = S.st.querySelector(".pk-center"), seal = center.querySelector(".pack-seal");
  if (REDUCED()){ center.remove(); S.skip = true; }
  else {
    // The strip flies off in 3D, turning over as it goes, while the pack tips back to open its mouth.
    const r = seal.getBoundingClientRect();
    packBurst(r.left + r.width / 2, r.top + 16, {n: 46, tier: S.best});
    seal.querySelector(".slashes")?.classList.add("morph");   // the logo's // crosses into an X, as the header's does
    const out = "cubic-bezier(.25,1,.5,1)";
    await Promise.all([
      seal.querySelector(".pack-top").animate([
        {transform: "translate3d(0,0,0) rotateX(0) rotateZ(0)", opacity: 1},
        {transform: "translate3d(40px,-46px,40px) rotateX(40deg) rotateZ(-10deg)", opacity: 1, offset: .35},
        {transform: "translate3d(150px,-170px,90px) rotateX(120deg) rotateZ(-38deg)", opacity: 0}],
        {duration: 520, easing: out, fill: "forwards"}).finished,
      center.querySelector(".pack-glow").animate([{transform: "rotateX(16deg) rotateY(0deg)"}],
        {duration: 460, easing: out, fill: "forwards"}).finished]);
    S.pack = center;
  }
  await pkDeal(S);
  await pkHome(S);
}

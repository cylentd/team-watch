/* The pack's cards on its stage (packshow.js): dealt one at a time in the centre, turned, sent to the
   pile at the foot of the screen, the best one given its moment, then every card flown home into
   its roster slot. A card's place is its wrapper's `translate`, `scale` and `rotate` (individual
   transforms); pkMove animates to a place and then writes it inline, so no held animation fights
   the next one. With S.skip every step lands at once. */

async function pkMove(S, el, to, ms, easing){
  to = {rotate: el.style.rotate || "0deg", ...to};
  if (!S.skip){
    const a = el.animate([{translate: el.style.translate || "0 0", scale: el.style.scale || "1", rotate: el.style.rotate || "0deg"}, to],
      {duration: ms, easing: easing || pkSpring(el), fill: "forwards"});
    await a.finished;
    a.cancel();
  }
  Object.assign(el.style, to);
}

/* A stage card is a wrapper (.pk-card, placed by pkMove) with perspective, holding a turning layer
   (.pk-inner) with two faces back to back: the pack's card back and the card itself. It starts
   face down (rotated half a turn) and turns in real 3D; the old turn squashed a flat card to its
   edge and swapped faces there, which read as a blink rather than a turn (2026-09-25). */
function pkCardEl(S, c){
  const el = document.createElement("div");
  el.className = "pk-card";
  el.innerHTML = `<div class="pk-inner"><div class="pk-cb" aria-hidden="true"><b><span>TEAM<i>//</i>WATCH</span></b></div>${cardHTML(c.p, c.i, S.team.key)}</div>`;
  return el;
}

/* Turn it face up: a lift and a lean as it goes over, landing on the spring. */
async function pkTurn(S, el, big){
  const inner = el.querySelector(".pk-inner");
  if (!S.skip){
    const a = inner.animate([
      {rotate: "y 180deg", scale: "1"},
      {rotate: "y 90deg", scale: big ? "1.12" : "1.07", offset: .45},
      {rotate: "y 0deg", scale: "1"}], {duration: big ? 900 : 620, easing: pkSpring(el), fill: "forwards"});
    await a.finished;
    a.cancel();
  }
  inner.style.rotate = "y 0deg";
}

/* The autograph writes itself in, left to right, with a sparkle where the pen lifts. It is hidden
   on a stage card until then (.pk-card .tc-sig), so it is never on the card before it is signed. */
async function pkSign(S, el){
  const ink = el.querySelector(".tc-sig");
  if (!ink) return;
  if (!S.skip){
    packBuzz([10, 40, 10]);
    await ink.animate([{clipPath: "inset(-20% 100% -20% -5%)"}, {clipPath: "inset(-20% -5% -20% -5%)"}],
      {duration: 1100, easing: "cubic-bezier(.45,.05,.4,1)", fill: "forwards"}).finished;
    const r = ink.getBoundingClientRect();
    packBurst(r.right - r.width * .12, r.top + r.height / 2, {n: 26, tier: "ur", spread: .6});
  }
  el.classList.add("pk-signed");
}

/* The pile: small at the foot of the screen, fanned so the count shows, each card leaning a little. */
function pkPilePlace(S, k){
  const mid = (S.cards.length - 1) / 2, lift = innerHeight * .55 - 64;
  return {translate: `${(k - mid) * 20}px ${lift}px`, scale: ".3", rotate: `${(k - mid) * 4}deg`};
}

/* Down to the pile on an arc: up a touch first, then away and small, easing out, no bounce (the
   spring's overshoot made a shrinking card wobble). */
async function pkToPile(S, el, k){
  const to = pkPilePlace(S, k);
  if (!S.skip){
    const a = el.animate([
      {translate: "0 0", scale: "1", rotate: "0deg"},
      {translate: "0 -18px", scale: ".96", rotate: "0deg", offset: .18},
      to], {duration: 560, easing: "cubic-bezier(.5,0,.25,1)", fill: "forwards"});
    await a.finished;
    a.cancel();
  }
  Object.assign(el.style, to);
}

async function pkDeal(S){
  for (const [k, c] of S.cards.entries()){
    const el = pkCardEl(S, c);
    if (!S.skip) S.st.querySelector(".pk-msg").innerHTML = "";   // the last card's label goes with it
    S.st.appendChild(el);
    S.shown.push(el);
    const last = k === S.cards.length - 1;
    el.style.translate = "0 70px"; el.style.scale = ".7";
    await pkMove(S, el, {translate: "0 0", scale: "1"}, 360);
    if (last){ await pkHero(S, el, c); break; }
    await pkSleep(S, 120);
    await pkTurn(S, el, false);
    // The label once the face has settled, never while it is still face down.
    await pkSleep(S, 60);
    if (!S.skip) S.st.querySelector(".pk-msg").innerHTML = pkLabel(c);
    await pkSign(S, el);
    await pkSleep(S, 700);
    await pkToPile(S, el, k);
  }
}

/* The best card's moment, in the centre: rays behind it, shake, flash, a burst, a size up. */
async function pkHero(S, el, c){
  S.st.classList.add("pk-dim", `pk-best-${S.best}`);
  S.st.querySelector(".pk-msg").innerHTML = "";
  packBuzz([30, 60, 30]);
  if (!S.skip) await el.animate([0, -4, 4, -5, 5, -3, 3, 0].map(x => ({translate: `${x}px 0`})), {duration: 560}).finished;
  if (!S.skip){
    S.st.querySelector(".pk-flash").animate([{opacity: 0}, {opacity: .85, offset: .25}, {opacity: 0}], {duration: 700, easing: "ease-out"});
    const r = el.getBoundingClientRect();
    packBurst(r.left + r.width / 2, r.top + r.height / 2, {n: S.best === "one" ? 110 : 70, tier: S.best, spread: 2});
  }
  await pkMove(S, el, {translate: "0 0", scale: "1.16"}, 500);
  await pkTurn(S, el, true);
  await pkSign(S, el);
  const top = S.cards[S.cards.length - 1];
  S.st.querySelector(".pk-msg").innerHTML = t("teams.pack.done", {name: esc(nameInitial(top.p.n)), rank: top.rank, pos: esc(top.p.pos)});
  await pkSleep(S, 1500);
}

/* The stage fades to the roster and every card flies from where it is into its empty slot. */
async function pkHome(S){
  S.st.classList.add("pk-home");
  const view = document.getElementById("view");
  view.querySelector(".cards")?.scrollIntoView({block: "start", behavior: "instant"});
  window.scrollBy(0, -90);
  await pkSleep(S, 260);
  await Promise.all(S.shown.map(async (el, k) => {
    const slot = view.querySelector(`.cards .tc[data-pk="${k}"]`);
    if (slot && !S.skip){
      // Centres from the boxes (a leaning card's box is wider than the card; its centre is not
      // moved), the width from the layout, so the lean does not skew the scale. It straightens on the way.
      const a = el.getBoundingClientRect(), b = slot.getBoundingClientRect();
      const [tx, ty] = (el.style.translate || "0 0").split(" ").map(parseFloat);
      await pkSleep(S, k * 90);
      await pkMove(S, el, {translate: `${tx + (b.left + b.width / 2) - (a.left + a.width / 2)}px ${ty + (b.top + b.height / 2) - (a.top + a.height / 2)}px`,
        scale: String(b.width / el.offsetWidth), rotate: "0deg"}, 620, "cubic-bezier(.3,.7,.25,1)");
    }
    slot?.classList.remove("pk-slot");
    el.remove();
  }));
  layerDone("pack");
  pkClose(S);
}

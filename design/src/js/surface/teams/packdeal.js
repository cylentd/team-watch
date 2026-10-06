/* The pack's cards on its stage (packshow.js; the deal reworked 2026-10-05 from the round-4
   storyboard). Every starter rises straight up to the centre, worst first: a stock card flicks past
   on its way to the pile at the foot of the screen; a metal holds with its label ("GOLD", "#2 TE
   THIS WEEK") while a shine crosses its border; a signed card holds again while it is signed
   (cardsign.js); the best card, last, gets the moment (pkHero). A card's place is its wrapper's
   `translate`, `scale` and `rotate` (individual transforms); pkMove animates to a place and then
   writes it inline, so no held animation fights the next one. With S.skip every step lands at once.
   Superseded 2026-10-05: every card dealt face down and turned over, and the autograph wiped in. */

async function pkMove(S, el, to, ms, easing){
  to = {rotate: el.style.rotate || "0deg", ...to};
  if (!S.skip){
    const a = pkAnim(S, el, [{translate: el.style.translate || "0 0", scale: el.style.scale || "1", rotate: el.style.rotate || "0deg"}, to],
      {duration: ms, easing: easing || pkSpring(el), fill: "forwards"});
    await a.finished;
    a.cancel();
  }
  Object.assign(el.style, to);
}

/* A stage card is a wrapper (.pk-card, placed by pkMove) with perspective, holding a turning layer
   (.pk-inner) with two faces back to back: the set's card back and the card itself. Face up from
   the start, except the best card, which turns over in its moment. Its autograph is hidden
   (.pk-unsigned) until its signing. */
function pkCardEl(S, c, faceDown){
  const el = document.createElement("div");
  el.className = cardSigned(c.p) ? "pk-card pk-unsigned" : "pk-card"; el.dataset.testid = "roster-pack-card";
  el.innerHTML = `<div class="pk-inner"><div class="pk-cb" aria-hidden="true"><b>TW</b></div>${cardHTML(c.p, c.i, S.team.key)}</div>`;
  if (!faceDown) el.querySelector(".pk-inner").style.rotate = "y 0deg";
  return el;
}

/* Turn it face up: a lift and a lean as it goes over, landing on the spring. */
async function pkTurn(S, el, big){
  const inner = el.querySelector(".pk-inner");
  if (!S.skip){
    const a = pkAnim(S, inner, [
      {rotate: "y 180deg", scale: "1"},
      {rotate: "y 90deg", scale: big ? "1.12" : "1.07", offset: .45},
      {rotate: "y 0deg", scale: "1"}], {duration: big ? 700 : 560, easing: pkSpring(el), fill: "forwards"});
    await a.finished;
    a.cancel();
  }
  inner.style.rotate = "y 0deg";
}

/* The label over the card: a metal's name in its colour over "#2 TE THIS WEEK", or SIGNED in gold
   over the finish that earned it. Spelled out one call each: assemble.py --check finds a key only
   in a literal lookup. */
const PK_TAG = {holo: () => t("teams.pack.tier.holo"), gold: () => t("teams.pack.tier.gold"), silver: () => t("teams.pack.tier.silver")};
function pkTag(S, kind, big, small){
  const m = S.st.querySelector(".pk-msg");
  m.className = "pk-msg deal";
  m.innerHTML = `<b class="pk-tag t-${kind}">${big}</b><small>${small}</small>`;
  if (!S.skip) pkAnim(S, m, [{opacity: 0, translate: "0 8px"}, {opacity: 1, translate: "0 0"}], {duration: 250, easing: pkSpring(m)});
}
const pkUntag = S => { S.st.querySelector(".pk-msg").innerHTML = ""; };

/* A metal's hold: its label and the shine across its border (cards.css .tc.shine). */
async function pkMetal(S, el, c){
  const tier = cardTier(c.rank);
  await pkSleep(S, 300);
  pkTag(S, tier, PK_TAG[tier](), t("teams.pack.thisWeek", {n: c.rank, pos: esc(c.p.pos)}));
  el.querySelector(".tc").classList.add("shine");
}

/* The signing, its own beat: the label turns to SIGNED and the finish, the pen writes (cardsign.js),
   and the phone buzzes as it does. */
async function pkSigned(S, el, c){
  const won = cardSigned(c.p);
  pkUntag(S);
  await pkSleep(S, 150);
  pkTag(S, "signed", t("teams.pack.signedTag"), t("teams.pack.signedLine", {rank: won.rank, pos: esc(c.p.pos), wk: LIVE_SIGNED.wk, pts: won.pts}));
  el.classList.remove("pk-unsigned");
  if (!S.skip) cardSign(el.querySelector(".tc"));
  await pkSleep(S, 450);
  packBuzz(25);
}

/* The pile: small at the foot of the screen, fanned so the count shows, each card leaning a little. */
function pkPilePlace(S, k){
  // Its foot 18px above the window's: the card is sized by the window (--pkw), so the lift is too.
  const mid = (S.cards.length - 1) / 2, w = S.shown[0] ? S.shown[0].offsetWidth : 220;
  const lift = innerHeight * .55 - w * 1.4 * .3 / 2 - 18;
  return {translate: `${(k - mid) * 14}px ${lift}px`, scale: ".3", rotate: `${(k - mid) * 3}deg`};
}

/* Down to the pile on an arc: up a touch first, then away and small, easing out, no bounce (the
   spring's overshoot made a shrinking card wobble). A flick goes quicker. */
async function pkToPile(S, el, k, quick){
  const to = pkPilePlace(S, k);
  if (!S.skip){
    const a = pkAnim(S, el, [
      {translate: "0 0", scale: "1", rotate: "0deg"},
      {translate: "0 -18px", scale: ".96", rotate: "0deg", offset: .18},
      to], {duration: quick ? 320 : 440, easing: "cubic-bezier(.5,0,.25,1)", fill: "forwards"});
    await a.finished;
    a.cancel();
  }
  Object.assign(el.style, to);
  if (!S.skip) S.st.querySelector(".pk-count").textContent = t("teams.pack.count", {n: k + 1});
}

/* The first card comes out of the pack (2026-09-25; the pack used to fade and the cards appear
   from nowhere). It starts behind the pack, the pack's body hiding it, rises out of the open mouth,
   comes forward over it, and the empty pack drops away. */
async function pkOutOfPack(S, el){
  const pack = S.pack, h = el.offsetWidth * 1.4;
  S.pack = null;
  if (S.skip){ pack.remove(); return; }
  el.style.zIndex = "2";                          // behind the pack (z 3) until it is out
  el.style.translate = `0 ${Math.round(h * .12)}px`; el.style.scale = ".88";
  await pkMove(S, el, {translate: `0 ${Math.round(-h * .62)}px`, scale: ".9"}, 480, "cubic-bezier(.3,.8,.3,1)");
  el.style.zIndex = "";
  pkAnim(S, pack, [{translate: "-50% -50%", opacity: 1}, {translate: "-50% 10%", opacity: 0}],
    {duration: 340, easing: "cubic-bezier(.5,0,.75,0)", fill: "forwards"}).finished.then(() => pack.remove());
  await pkMove(S, el, {translate: "0 0", scale: "1"}, 400);
}

/* Every later card rises straight up from where the pack stood, never sideways: its x is the stage's
   centre throughout, as the card is centred by its margins (packshow.css .pk-card). */
async function pkRise(S, el, hit){
  el.style.translate = `0 ${Math.round(el.offsetWidth * .3)}px`; el.style.scale = ".82";
  if (!S.skip) pkAnim(S, el, [{opacity: 0}, {opacity: 1, offset: .3}, {opacity: 1}], {duration: hit ? 420 : 220});
  await pkMove(S, el, {translate: "0 0", scale: "1"}, hit ? 420 : 220, hit ? undefined : "cubic-bezier(.2,.8,.3,1)");
}

async function pkDeal(S){
  await Promise.race([S.ready, pkSleep(S, 1500)]);   // the photos, sharp, before the first card (1.5s at most)
  const going = [];
  for (const [k, c] of S.cards.entries()){
    S.rush = false;                                // a tap hurried the last card, not this one
    const last = k === S.cards.length - 1, hit = packHit(c), hero = last && hit;
    const el = pkCardEl(S, c, hero);
    pkUntag(S);                                    // the last card's label goes with it
    S.st.appendChild(el);
    // Laid out at the roster card's width, scaled up whole to the stage's (packshow.css .pk-inner > .tc).
    const cw = S.cw();
    el.style.setProperty("--cw0", `${cw}px`);
    el.style.setProperty("--pkz", (el.offsetWidth / cw).toFixed(4));
    // The photo is the sharpest file there is, already loaded (packShow preloads the pack's), set
    // directly: a srcset would start from its small layout size (it is scaled up by transform) and
    // swap a blurry photo for a sharp one in front of the reader.
    const img = el.querySelector(".tc-art img"), best = pkBestHead(c.p);
    if (img && best){ img.removeAttribute("srcset"); img.removeAttribute("sizes"); img.loading = "eager"; img.src = best; }
    fitSig(el); fitBanner(el);
    S.shown.push(el);
    if (S.pack) await pkOutOfPack(S, el); else await pkRise(S, el, hit);
    if (hero){ await pkHero(S, el, c); break; }
    if (!hit){
      // A flick: it leaves for the pile while the next one rises.
      await pkSleep(S, 80);
      going.push(pkToPile(S, el, k, true));
      await pkSleep(S, 120);
      continue;
    }
    if (cardTier(c.rank) !== "base"){ await pkMetal(S, el, c); await pkSleep(S, cardSigned(c.p) ? 1100 : 1300); }
    if (cardSigned(c.p)){ await pkSigned(S, el, c); await pkSleep(S, 1300); }
    await pkToPile(S, el, k);
  }
  await Promise.all(going);
  if (!S.cards.some(packHit)) await pkNone(S);
}

/* No metal and nobody signed: the line says so, a moment, before the cards go home. A tap goes sooner. */
async function pkNone(S){
  const m = S.st.querySelector(".pk-msg");
  m.className = "pk-msg";
  m.textContent = t("teams.pack.none");
  if (S.quit) return;
  await new Promise(r => { setTimeout(r, 2200); S.wake.add(r); S.st.addEventListener("click", r, {once: true}); });
}

/* The best card's moment, in the centre (reworked 2026-09-26, packshow.css "The best card's
   reveal"): the charge, a line running round the face-down card faster each lap while it shakes
   harder; then a flash, a shock ring and a burst, the turn a size up, two lines circling the card
   and a sheen across its face, a second fall of foil from above; then its label, and its signing. */
const PK_CHARGE = 1100;
async function pkHero(S, el, c){
  S.hero = true;                                 // taps wait until its line is up (packshow.js pkHurry)
  S.rush = false;
  S.st.classList.add("pk-dim", `pk-best-${S.best}`);
  el.insertAdjacentHTML("beforeend", `<i class="pk-aura"></i><span class="pk-ring"><i></i></span><span class="pk-sheen"></span>`);
  const ring = el.querySelector(".pk-ring"), aura = el.querySelector(".pk-aura");
  packBuzz([30, 60, 30]);
  let orbit = null;
  if (!S.skip){
    // The line starts slow and ends at three laps a second; the shake grows with it.
    orbit = pkAnim(S, ring.firstElementChild, [{rotate: "0deg"}, {rotate: "360deg"}], {duration: 900, iterations: Infinity});
    pkAnim(S, ring, [{opacity: 0}, {opacity: 1}], {duration: 250});
    const t0 = performance.now(), speed = () => {
      if (!ring.isConnected || ring.classList.contains("lit")) return;
      orbit.updatePlaybackRate((S.rush ? PK_RUSH : 1) * (1 + 2.2 * Math.min(1, (performance.now() - t0) / PK_CHARGE)));
      requestAnimationFrame(speed);
    };
    requestAnimationFrame(speed);
    pkAnim(S, aura, [{opacity: 0}, {opacity: .9}], {duration: PK_CHARGE, easing: "ease-in", fill: "forwards"});
    await pkAnim(S, el, [0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5, 0].map(x => ({translate: `${x}px 0`})),
      {duration: PK_CHARGE, easing: "ease-in"}).finished;
    packBuzz([20, 30, 40]);
    pkAnim(S, S.st.querySelector(".pk-flash"), [{opacity: 0}, {opacity: .9, offset: .2}, {opacity: 0}], {duration: 650, easing: "ease-out"});
    pkAnim(S, S.st.querySelector(".pk-wave"), [{scale: ".6", opacity: .9}, {scale: "3.2", opacity: 0}], {duration: 750, easing: "cubic-bezier(.2,.8,.3,1)"});
    const r = el.getBoundingClientRect();
    packBurst(r.left + r.width / 2, r.top + r.height / 2, {n: S.best === "holo" ? 110 : 70, tier: S.best, spread: 2});
  }
  // The size up, then the turn: run together, the two scales at once left the photo painted small
  // and stretched until the turn ended.
  await pkMove(S, el, {translate: "0 0", scale: "1.16"}, 320);
  el.classList.add("pk-turning");
  await pkTurn(S, el, true);
  el.classList.remove("pk-turning");
  ring.classList.add("lit");
  orbit?.updatePlaybackRate(1.2);                 // two lines at an even pace once it is face up
  if (!S.skip){
    el.querySelector(".pk-sheen").classList.add("go");
    pkAnim(S, aura, [{opacity: .9}, {opacity: .45}], {duration: 1200, direction: "alternate", iterations: Infinity, easing: "ease-in-out"});
    // The foil falls a second time, from above the card's two top corners.
    const r = el.getBoundingClientRect();
    [r.left + r.width * .1, r.right - r.width * .1].forEach(x => packBurst(x, r.top, {n: 24, tier: S.best, spread: .8}));
  }
  if (cardTier(c.rank) !== "base"){ await pkMetal(S, el, c); await pkSleep(S, cardSigned(c.p) ? 1100 : 0); }
  if (cardSigned(c.p)) await pkSigned(S, el, c);
  // Long enough to read the label above it; a tap anywhere goes on sooner, and only from here: the
  // reveal itself cannot be hurried.
  S.hero = false;
  // 2.2s since 2026-09-27 (it was 3s; with the signature before it, the card sat still for 4s).
  await Promise.race([pkSleep(S, 2200), new Promise(r => S.st.addEventListener("click", r, {once: true}))]);
}

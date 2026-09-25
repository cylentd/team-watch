/* The pack's stage (2026-09-25): the cards come out of a ripped pack onto their own dark stage, as a
   face-down stack. Each tap turns the top card; the next tap sends it down to the tray and turns the
   one under it, worst first. The last card is the best, and gets the moment: the stage dims, light
   rays turn behind it, the stack shakes, the card spins up larger than the rest with a flash and a
   burst of flakes in its tier's colours, and its signature writes itself across the photo.
   Skip lays everything out at once; so does reduced motion. Back, Escape and Done close it.
   One state object (S) carries the stage between the steps below. */

// Spelled out one call each: assemble.py --check finds a key only in a literal lookup.
const PACK_TIER_LABEL = {one: () => t("teams.pack.tier.one"), sig: () => t("teams.pack.tier.sig"),
                         sr: () => t("teams.pack.tier.sr"), ur: () => t("teams.pack.tier.ur")};

function packStageHTML(team, cards){
  return `<div class="pk-rays"></div><div class="pk-flash"></div>
    <div class="pk-bar"><span class="pk-count"></span><button class="chip pk-skip" type="button">${t("teams.pack.skip")}</button></div>
    <p class="pk-msg" aria-live="polite"></p>
    <div class="pk-stack">${cards.map((c, k) => cardHTML(c.p, c.i, team.key).replace('class="tc ', `style="--k:${cards.length - 1 - k}" class="tc pk-down pk-in `)).join("")}</div>
    <p class="pk-hint">${t("teams.pack.tapFlip")}</p>
    <div class="cardgrid pack-grid pk-tray"></div>
    <div class="pk-foot"></div>`;
}

function packStage(team){
  const cards = packCards(team);
  const st = document.createElement("div");
  st.className = "pk-stage";
  st.setAttribute("role", "dialog");
  st.setAttribute("aria-modal", "true");
  st.setAttribute("aria-label", t("teams.pack.stage"));
  st.innerHTML = packStageHTML(team, cards);
  document.body.appendChild(st);
  document.body.classList.add("pk-open");
  const S = {st, cards, els: [...st.querySelectorAll(".pk-stack .tc")],    // lowest rank first: the top of the stack
    tray: st.querySelector(".pack-grid"), msg: st.querySelector(".pk-msg"), count: st.querySelector(".pk-count"),
    next: 0, busy: false, shown: null, over: false};
  S.best = cardTier(cards[cards.length - 1].rank);
  S.key = e => { if (e.key === "Escape"){ layerDone("pack"); pkClose(S); } };
  document.addEventListener("keydown", S.key);
  layerPush("pack", () => pkClose(S));
  // A tap while a card is still turning or signing hurries it to its end rather than being lost,
  // so a fast tapper is never stuck waiting on an animation they have already seen.
  st.addEventListener("click", e => {
    if (S.over || e.target.closest(".pk-skip, .pack-done")) return;
    if (S.busy){ pkHurry(S); return; }
    pkStep(S);
  });
  st.querySelector(".pk-skip").addEventListener("click", e => { e.stopPropagation(); pkSkip(S); });
  pkTally(S);
  if (REDUCED()) pkSkip(S);
  else st.animate([{opacity: 0}, {opacity: 1}], {duration: 240});
}

function pkClose(S){
  S.st.remove();
  document.body.classList.remove("pk-open");
  document.removeEventListener("keydown", S.key);
  render();
}
const pkHurry = S => S.st.getAnimations({subtree: true})
  .forEach(a => { if (a.effect && a.effect.getTiming().iterations !== Infinity) a.finish(); });
const pkTally = S => { S.count.textContent = t("teams.pack.progress", {i: Math.min(S.next, S.els.length), n: S.els.length}); };
function pkLabel(S, el){
  const c = S.cards[S.els.indexOf(el)];
  return `<b>${t("teams.card.rank", {n: c.rank, pos: esc(c.p.pos)})}</b> · ${PACK_TIER_LABEL[cardTier(c.rank)]()}`;
}

/* The shown card drops into the tray: measured before and after the move, then animated across
   the gap, so it travels from the stack to its place (FLIP). */
function pkToTray(S, el, animate){
  const a = el.getBoundingClientRect();
  el.classList.remove("pk-in", "pk-shown");
  S.tray.appendChild(el);
  if (!animate) return;
  const b = el.getBoundingClientRect();
  el.animate([{transformOrigin: "0 0", transform: `translate(${a.left - b.left}px,${a.top - b.top}px) scale(${a.width / b.width})`},
    {transformOrigin: "0 0", transform: "none"}], {duration: 420, easing: getComputedStyle(S.st).getPropertyValue("--spring").trim() || "ease-out"});
}
/* Turn a card face up: edge-on, swap the face, and on round with a little overshoot. */
async function pkTurn(el, big){
  await el.animate([{rotate: "y 0deg"}, {rotate: "y 90deg"}], {duration: big ? 220 : 150, easing: "ease-in", fill: "forwards"}).finished;
  el.classList.remove("pk-down");
  el.classList.add("pk-shown");
  await el.animate([{rotate: "y -90deg", scale: big ? ".7" : "1"}, {rotate: "y 0deg", scale: big ? "1.12" : "1.04"}],
    {duration: big ? 620 : 340, easing: getComputedStyle(el).getPropertyValue("--spring").trim() || "ease-out", fill: "forwards"}).finished;
  el.getAnimations().forEach(a => a.cancel());
}
async function pkSign(el){
  const ink = el.querySelector(".tc-sig");
  if (ink) await ink.animate([{clipPath: "inset(0 100% 0 0)"}, {clipPath: "inset(0 0 0 0)"}], {duration: 900, easing: "ease-in-out"}).finished;
}

async function pkFinale(S, el){
  S.st.classList.add("pk-dim", `pk-best-${S.best}`);
  S.msg.innerHTML = "";
  packBuzz([30, 60, 30]);
  await el.animate([0, -4, 4, -5, 5, -3, 3, 0].map(x => ({translate: `${x}px 0`})), {duration: 560}).finished;
  S.st.querySelector(".pk-flash").animate([{opacity: 0}, {opacity: .85, offset: .25}, {opacity: 0}], {duration: 700, easing: "ease-out"});
  const r = el.getBoundingClientRect();
  packBurst(r.left + r.width / 2, r.top + r.height / 2, {n: S.best === "one" ? 110 : 70, tier: S.best, spread: 2});
  await pkTurn(el, true);
  await pkSign(el);
}

async function pkStep(S){
  S.busy = true;
  if (S.shown){ pkToTray(S, S.shown, true); S.shown = null; }
  const el = S.els[S.next++];
  pkTally(S);
  if (S.next === S.els.length){ await pkFinale(S, el); pkEnd(S); return; }
  await pkTurn(el, false);
  if (S.over) return;      // skipped mid-turn: the stage already shows the end
  S.msg.innerHTML = pkLabel(S, el);
  if (el.querySelector(".tc-sig")) await pkSign(el);
  S.shown = el;
  S.busy = false;
}

/* Everything at once: every card face up, all but the best in the tray, the best on the stack. */
function pkSkip(S){
  pkHurry(S);
  S.els.forEach((el, k) => { el.classList.remove("pk-down"); if (k < S.els.length - 1) pkToTray(S, el, false); });
  S.els[S.els.length - 1].classList.add("pk-shown");
  S.st.classList.add("pk-dim", `pk-best-${S.best}`);
  S.next = S.els.length; S.shown = null;
  pkTally(S);
  pkEnd(S);
}

function pkEnd(S){
  if (S.over) return;      // Skip can land while a turn is still awaiting; the stage ends once
  S.over = true; S.busy = false;
  S.st.classList.add("pk-over");
  const top = S.cards[S.cards.length - 1];
  S.msg.innerHTML = t("teams.pack.done", {name: esc(nameInitial(top.p.n)), rank: top.rank, pos: esc(top.p.pos)});
  const done = document.createElement("button");
  done.type = "button"; done.className = "chip pack-done"; done.textContent = t("teams.pack.close");
  done.addEventListener("click", e => { e.stopPropagation(); layerDone("pack"); pkClose(S); });
  S.st.querySelector(".pk-foot").appendChild(done);
  S.st.querySelector(".pk-skip")?.remove();
  S.st.querySelector(".pk-hint")?.remove();
  wireCards(S.st);
  done.focus({preventScroll: true});
}

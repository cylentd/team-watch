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
const pkSleep = (S, ms) => S.skip ? Promise.resolve() : new Promise(r => setTimeout(r, ms));

function packShow(team, wk){
  if (PACK_SHOW || !wk) return;
  const cards = packCards(team);
  if (!cards.length) return;
  PACK_SHOW = {key: `${team.key}-${wk}`, order: new Map(cards.map((c, k) => [c.i, k]))};
  const st = document.createElement("div");
  st.className = "pk-stage";
  st.setAttribute("role", "dialog"); st.setAttribute("aria-modal", "true"); st.setAttribute("aria-label", t("teams.pack.stage"));
  st.innerHTML = `<div class="pk-back"></div><div class="pk-rays"></div><div class="pk-flash"></div>
    <button class="pk-close" type="button" aria-label="${t("teams.pack.closeLabel")}">✕</button>
    <p class="pk-msg" aria-live="polite">${t("teams.pack.lead", {wk, n: cards.length})}</p>
    <div class="pk-center">${packSealHTML(team, wk, cards)}</div>
    <p class="pk-hint">${t("teams.pack.hint")}</p>`;
  document.body.appendChild(st);
  document.body.classList.add("pk-open");
  const S = {st, team, wk, cards, ripped: false, skip: false, shown: [], best: cardTier(cards[cards.length - 1].rank)};
  S.key = e => { if (e.key === "Escape") pkQuit(S); };
  document.addEventListener("keydown", S.key);
  layerPush("pack", () => pkQuit(S, true));
  st.querySelector(".pk-close").addEventListener("click", () => pkQuit(S));
  // Each eighth of the tear: a tick under the finger and a pinch of foil from the tear point.
  wireRip(st.querySelector(".pack-seal"), () => pkRip(S), (x, y) => { packBuzz(6); packBurst(x, y, {n: 6, tier: S.best, spread: .35}); });
  render();                     // the page drops its own copy of the pack while the stage holds it
  if (!REDUCED()) st.animate([{opacity: 0}, {opacity: 1}], {duration: 260});
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
  S.st.querySelector(".pk-hint").remove();
  const seal = S.st.querySelector(".pack-seal");
  if (!REDUCED()){
    const r = seal.getBoundingClientRect();
    packBurst(r.left + r.width / 2, r.top + 16, {n: 46, tier: S.best});
    await seal.querySelector(".pack-top").animate(
      [{translate: "0 0", rotate: "0deg", opacity: 1}, {translate: "40px -40px", rotate: "-12deg", opacity: 1, offset: .35},
       {translate: "130px -150px", rotate: "-34deg", opacity: 0}],
      {duration: 460, easing: "cubic-bezier(.25,.7,.35,1)", fill: "forwards"}).finished;
    await seal.animate([{translate: "0 0", opacity: 1}, {translate: "0 90px", scale: ".9", opacity: 0}],
      {duration: 300, easing: "ease-in", fill: "forwards"}).finished;
  }
  S.st.querySelector(".pk-center").remove();
  if (REDUCED()) S.skip = true;
  await pkDeal(S);
  await pkHome(S);
}

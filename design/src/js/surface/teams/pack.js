/* The week's pack (2026-09-25): once per league per week, the Cards view opens with a sealed pack
   holding the players who rank in the top 12 at their position this week (cards.js cardTier "ur" and
   up), so how many cards it holds is itself the news. Opening is remembered in localStorage, which
   can refuse: then the pack simply shows again next load.

   Ripping it (rebuilt 2026-09-25): the sealed pack glows in the colour of the best card inside;
   dragging a finger across it tears the strip off the top, following the finger, and a tap tears it
   in one go. Foil flakes burst from the tear (packfx.js) and the cards open on their own stage
   (packstage.js). "Rip again" on the Sheet / Cards row puts this week's pack back, sealed. */
const PACK_TIERS = ["ur", "sr", "sig", "one"];
let PACK_REPLAY = null;     // "<league>-<week>" while a replayed pack is on the page

/* The week of the next kickoff on the schedule, or null when there is none to name. */
function packWeek(){
  if (typeof LIVE_SCHEDULE === "undefined" || !LIVE_SCHEDULE) return null;
  const now = Date.now() - 4 * 3600e3;
  const next = LIVE_SCHEDULE.games.filter(g => Date.parse(g.kickoff) > now)
    .sort((a, b) => Date.parse(a.kickoff) - Date.parse(b.kickoff))[0];
  return next ? next.week : null;
}
const packKey = (team, wk) => `tw-pack-${team.key}-${wk}`;
function packOpened(team, wk){
  try { return localStorage.getItem(packKey(team, wk)) === "1"; } catch (e) { return false; }
}
function packMark(team, wk){
  try { localStorage.setItem(packKey(team, wk), "1"); } catch (e) { /* shows again next load */ }
}

/* The pack's players with their profile index, lowest rank first so the best turns last. */
function packCards(team){
  const ordered = team.roster.filter(p => p.start)
    .concat(team.roster.filter(p => !p.start && p.slot !== "OUT"), team.roster.filter(p => p.slot === "OUT"));
  return ordered.map((p, i) => ({p, i, rank: cardRank(p)}))
    .filter(c => c.rank && PACK_TIERS.includes(cardTier(c.rank)))
    .sort((a, b) => b.rank - a.rank);
}

/* This week's pack has been opened and still holds cards: the Sheet / Cards row offers it again. */
function packReplayable(team){
  const wk = packWeek();
  return !!wk && packOpened(team, wk) && packCards(team).length > 0 && PACK_REPLAY !== `${team.key}-${wk}`;
}
function packReplay(team){
  PACK_REPLAY = `${team.key}-${packWeek()}`;
  render();
  document.querySelector(".pack")?.scrollIntoView({behavior: "smooth", block: "center"});
}

function packHTML(team){
  const wk = packWeek(), cards = packCards(team);
  if (!wk || !cards.length || (packOpened(team, wk) && PACK_REPLAY !== `${team.key}-${wk}`)) return "";
  const best = cardTier(cards[cards.length - 1].rank);   // the glow gives away how good, never who
  return `<div class="pack" data-pack="${wk}">
    <p class="pack-msg">${t("teams.pack.lead", {wk, n: cards.length})}</p>
    <div class="pack-glow tease-${best}"><button class="pack-seal" type="button" aria-label="${t("teams.pack.open")}">
      <span class="pack-top"></span><b>TEAM<i>//</i>WATCH</b>
      <span class="pack-wk">${t("teams.pack.week", {wk})}</span><span class="pack-n">${t("teams.pack.count", {n: cards.length})}</span>
    </button></div>
    <p class="pack-hint">${t("teams.pack.hint")}</p>
  </div>`;
}

/* The tear follows the finger: --tear runs 0..1 across 80% of the pack's width. Let go past half
   way and it finishes on its own; short of that it springs back. A tap without a drag tears it at
   once, and Enter or Space on the focused pack does the same. */
function wirePack(v, team){
  const box = v.querySelector(".pack");
  if (!box) return;
  const wk = +box.dataset.pack, seal = box.querySelector(".pack-seal");
  let x0 = null, tear = 0, done = false;
  const set = p => { tear = p; seal.style.setProperty("--tear", p.toFixed(3)); };
  const finish = () => { if (done) return; done = true; packRip(box, seal, team, wk); };
  seal.addEventListener("pointerdown", e => { x0 = e.clientX; seal.classList.add("tearing"); seal.setPointerCapture?.(e.pointerId); });
  seal.addEventListener("pointermove", e => {
    if (x0 === null) return;
    set(Math.min(1, Math.abs(e.clientX - x0) / (seal.offsetWidth * .8)));
    if (tear >= 1) finish();
  });
  const release = e => {
    if (x0 === null) return;
    const tapped = Math.abs(e.clientX - x0) < 8;
    x0 = null; seal.classList.remove("tearing");
    if (tapped || tear > .5) finish(); else set(0);
  };
  seal.addEventListener("pointerup", release);
  seal.addEventListener("pointercancel", () => { x0 = null; seal.classList.remove("tearing"); set(0); });
  // A click from the keyboard has no pointer before it (detail 0); a pointer's click was handled above.
  seal.addEventListener("click", e => { e.stopPropagation(); if (e.detail === 0) finish(); });
}

/* The strip flies off, flakes burst from the tear, the pack drops away, and the stage opens. */
async function packRip(box, seal, team, wk){
  packMark(team, wk);
  PACK_REPLAY = null;
  const still = REDUCED();
  packBuzz(18);
  if (!still){
    const r = seal.getBoundingClientRect();
    seal.style.setProperty("--tear", 1);
    seal.classList.add("ripped");
    packBurst(r.left + r.width / 2, r.top + 16, {n: 46, tier: cardTier(packCards(team).slice(-1)[0].rank)});
    await seal.querySelector(".pack-top").animate(
      [{translate: "0 0", rotate: "-14deg", opacity: 1}, {translate: "90px -120px", rotate: "-38deg", opacity: 0}],
      {duration: 380, easing: "cubic-bezier(.3,.6,.4,1)", fill: "forwards"}).finished;
    await seal.animate([{translate: "0 0", opacity: 1}, {translate: "0 60px", scale: ".9", opacity: 0}],
      {duration: 280, easing: "ease-in", fill: "forwards"}).finished;
  }
  box.hidden = true;
  packStage(team);
}

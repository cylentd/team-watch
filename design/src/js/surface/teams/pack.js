/* The week's pack (2026-09-25): once per league per week, the Cards view holds a sealed pack of the
   players who rank in the top 12 at their position this week (cards.js cardTier "ur" and up), so
   how many cards it holds is itself the news. Opening is remembered in localStorage, which can
   refuse: then the pack simply shows again next load.

   The first time the Cards view draws an unopened pack in a page load, the pack opens on its own
   black stage, centred (packshow.js). Closing the stage leaves the pack on the page as the way
   back in; "Rip again" on the Sheet / Cards row puts an opened pack back on the stage. The sealed
   pack glows in the colour of the best card inside: how good, never who. */
const PACK_TIERS = ["ur", "sig", "one"];
let PACK_REPLAY = null;          // "<league>-<week>" while a replayed pack is waiting to be ripped
const PACK_AUTO_SEEN = new Set(); // "<league>-<week>" whose stage already opened on its own this load

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
  return !!wk && packOpened(team, wk) && packCards(team).length > 0 && !packShowing();
}

/* The sealed pack: crimped foil, a tear strip, the week and the count; the glow is the best tier. */
function packSealHTML(team, wk, cards){
  const best = cardTier(cards[cards.length - 1].rank);
  return `<div class="pack-glow tease-${best}"><button class="pack-seal" type="button" aria-label="${t("teams.pack.open")}">
      <span class="pack-top"></span><b>TEAM<i>//</i>WATCH</b>
      <span class="pack-wk">${t("teams.pack.week", {wk})}</span><span class="pack-n">${t("teams.pack.count", {n: cards.length})}</span>
    </button></div>`;
}

/* On the page: the unopened pack, small, as the way onto the stage. */
function packHTML(team){
  const wk = packWeek(), cards = packCards(team);
  if (!wk || !cards.length || packOpened(team, wk) || packShowing()) return "";
  return `<div class="pack" data-pack="${wk}">
    <p class="pack-msg">${t("teams.pack.lead", {wk, n: cards.length})}</p>
    ${packSealHTML(team, wk, cards)}
    <p class="pack-hint">${t("teams.pack.tapOpen")}</p>
  </div>`;
}

function wirePack(v, team){
  const box = v.querySelector(".pack"), seal = box && box.querySelector(".pack-seal");
  if (!seal) return;
  const wk = +box.dataset.pack, key = `${team.key}-${wk}`;
  seal.addEventListener("click", e => { e.stopPropagation(); packShow(team, wk); });
  if (!PACK_AUTO_SEEN.has(key)){
    PACK_AUTO_SEEN.add(key);
    setTimeout(() => { if (document.body.contains(seal)) packShow(team, wk); }, 350);
  }
}
function packReplay(team){ packShow(team, packWeek()); }

/* The tear follows the finger: --tear runs 0..1 across 80% of the pack's width. Let go past half
   way and it finishes on its own; short of that it springs back. A tap without a drag tears it at
   once, and Enter or Space on the focused pack does the same. */
function wireRip(seal, onRip){
  let x0 = null, tear = 0, done = false;
  const set = p => { tear = p; seal.style.setProperty("--tear", p.toFixed(3)); };
  const finish = () => { if (done) return; done = true; onRip(); };
  seal.addEventListener("pointerdown", e => { x0 = e.clientX; seal.classList.add("tearing"); seal.setPointerCapture?.(e.pointerId); });
  seal.addEventListener("pointermove", e => {
    if (x0 === null) return;
    set(Math.min(1, Math.abs(e.clientX - x0) / (seal.offsetWidth * .8)));
    if (tear >= 1) finish();
  });
  seal.addEventListener("pointerup", e => {
    if (x0 === null) return;
    const tapped = Math.abs(e.clientX - x0) < 8;
    x0 = null; seal.classList.remove("tearing");
    if (tapped || tear > .5) finish(); else set(0);
  });
  seal.addEventListener("pointercancel", () => { x0 = null; seal.classList.remove("tearing"); set(0); });
  // A click from the keyboard has no pointer before it (detail 0); a pointer's click was handled above.
  seal.addEventListener("click", e => { e.stopPropagation(); if (e.detail === 0) finish(); });
}

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

/* The pack's players with their profile index, lowest rank first so the best turns last: the top
   12 at a position, and any signed card (cards.js cardSigned) whatever its tier, the chase card. */
function packCards(team){
  const ordered = team.roster.filter(p => p.start)
    .concat(team.roster.filter(p => !p.start && p.slot !== "OUT"), team.roster.filter(p => p.slot === "OUT"));
  return ordered.map((p, i) => ({p, i, rank: cardRank(p)}))
    .filter(c => c.rank && (PACK_TIERS.includes(cardTier(c.rank)) || cardSigned(c.p)))
    .sort((a, b) => b.rank - a.rank);
}

/* This week's pack has been opened and still holds cards: the Sheet / Cards row offers it again. */
function packReplayable(team){
  const wk = packWeek();
  return !!wk && packOpened(team, wk) && packCards(team).length > 0 && !packShowing();
}

/* The sealed pack (art reworked 2026-09-25: it was a plain gradient with a dark band for a strip).
   Holo foil, ridged heat seals at both ends and a perforated tear strip in the same foil. The key
   art is drawn as SVG so it scales with the pack: the brand's // as two lime stripes across it,
   faint yard lines, and the week's number, huge and embossed. The logo and the week at the top,
   the card count in a round holo badge, the season up the side in small print. The glow is the best
   tier: how good, never who. */
function packArtSVG(wk){
  const size = String(wk).length > 1 ? 74 : 104;
  return `<svg class="pack-art" viewBox="0 0 100 140" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <path class="pa-yards" d="M0 46h100M0 66h100M0 86h100M0 106h100M0 126h100M33 55v3M67 55v3M33 75v3M67 75v3M33 95v3M67 95v3M33 115v3M67 115v3"/>
      <path class="pa-slash" d="M-8 140H14L68 0H46ZM20 140H30L84 0H74Z"/>
      <text class="pa-wk" x="50" y="${size > 90 ? 132 : 124}" text-anchor="middle" font-size="${size}">${wk}</text>
    </svg>`;
}
function packSealHTML(team, wk, cards){
  const best = cardTier(cards[cards.length - 1].rank);
  return `<div class="pack-glow tease-${best}"><button class="pack-seal" type="button" aria-label="${t("teams.pack.open")}">
      <span class="pack-foil">${packArtSVG(wk)}</span>
      <span class="pack-top"><i class="pt-base"></i><i class="pt-flap"></i><i class="pt-edge"></i></span>
      <b>TEAM<i>//</i>WATCH</b>
      <span class="pack-wk">${t("teams.pack.week", {wk})}</span>
      <span class="pack-n">${cards.length}<small>${t("teams.pack.cards")}</small></span>
      <span class="pack-side">${t("teams.pack.side", {season: packSeason()})}</span>
    </button></div>`;
}
/* The season the pack's week belongs to: the year of its first kickoff on the schedule. */
function packSeason(){
  const g = typeof LIVE_SCHEDULE !== "undefined" && LIVE_SCHEDULE && LIVE_SCHEDULE.games[0];
  return g ? new Date(g.kickoff).getUTCFullYear() : "";
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
function packReplay(team){
  packShow(team, packWeek());
}

/* The tear (2026-09-25, reworked twice the same day: it jumped, then it always began at the left
   edge wherever the finger was). It has to be torn: a drag that starts on the strip across the top.
   It starts under the finger and runs the way the finger goes, either way: the torn stretch of the
   strip runs from --ta to --tb (0..1 of the width), --te is the end the finger is on and --tdir its
   direction, and --tear is how far along the gesture is (the torn length over 75% of the width).
   The torn stretch lifts off at the finger while the rest stays on (pack.css). Every eighth of the
   way ticks: a buzz and a few flakes from the tear point (onTick). Let go past 55% and the whole
   strip tears by itself; short of that it closes back up to where it started, both eased by the
   registered properties' transitions, not a jump. A touch anywhere else only tugs the strip.
   Enter or Space on the focused pack tears it at once. */
const RIP_STEPS = 8, RIP_DONE = .55;
function wireRip(seal, onRip, onTick){
  let s = null, tear = 0, step = 0, done = false;
  const put = (a, b, end, dir, p) => {
    tear = p;
    [["--ta", a], ["--tb", b], ["--te", end], ["--tdir", dir], ["--tear", p]].forEach(([k, v]) => seal.style.setProperty(k, v.toFixed(3)));
  };
  const frac = e => { const r = seal.getBoundingClientRect(); return Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)); };
  const finish = () => {
    if (done) return;
    const dir = Number(seal.style.getPropertyValue("--tdir")) || 1;
    done = true; s = null; seal.classList.remove("tearing");
    put(0, 1, dir > 0 ? 1 : 0, dir, 1);
    setTimeout(onRip, REDUCED() ? 0 : 220);    // the transitions run the rest of the tear first
  };
  const nudge = () => {
    seal.classList.remove("nudge"); void seal.offsetWidth; seal.classList.add("nudge");
    packBuzz(8);
  };
  seal.addEventListener("pointerdown", e => {
    if (done) return;
    const r = seal.getBoundingClientRect();
    if (e.clientY - r.top > r.height * .3) return nudge();   // the strip, and a thumb's width under it
    s = frac(e); step = 0;
    seal.classList.add("tearing"); seal.setPointerCapture?.(e.pointerId);
    put(s, s, s, 1, 0);                          // closed, at the finger, before it moves
  });
  seal.addEventListener("pointermove", e => {
    if (s === null) return;
    const end = frac(e), dir = end >= s ? 1 : -1;
    put(Math.min(s, end), Math.max(s, end), end, dir, Math.min(1, Math.abs(end - s) / .75));
    const now = Math.floor(tear * RIP_STEPS);
    if (now > step){
      step = now;
      const r = seal.getBoundingClientRect();
      onTick?.(r.left + r.width * end, r.top + 16, tear);
    }
    if (tear >= 1 || (end <= 0 || end >= 1) && tear > RIP_DONE) finish();
  });
  const release = () => {
    if (s === null) return;
    const at = s;
    s = null; seal.classList.remove("tearing");
    if (tear > RIP_DONE) finish(); else { const p = tear; put(at, at, at, 1, 0); if (p < .04) nudge(); }
  };
  seal.addEventListener("pointerup", release);
  seal.addEventListener("pointercancel", release);
  // A click from the keyboard has no pointer before it (detail 0); a pointer's is the drag's.
  seal.addEventListener("click", e => { e.stopPropagation(); if (e.detail === 0) finish(); });
}

/* The week's pack (2026-09-25; rebuilt 2026-10-05 from the round-4 storyboard): this week's nine
   starters, sealed. Until it is ripped or skipped this week, it sits where the starters go on a team
   the reader follows, in Cards mode only (packgate.js): the slots face down behind it, Rip and Skip
   under it. Rip opens the stage (packshow.js), Skip turns the cards face up and leaves a chip on the
   Starters rule ("Open week 5") that opens the stage directly; once opened the chip says "Rip again".
   A team only browsed, and Sheet mode, never wait: the roster shows, with the chip. Opened and
   skipped are remembered per team per week in localStorage, which can refuse: then a Set keeps them
   for this load. The sealed pack glows in the colour of the best card inside: how good, never who.
   Superseded 2026-10-05: the stage that opened by itself once a week (tw-pack-auto-<wk>), and a
   pack of only the top 6 at their position above the cards. */
const PACK_MEM = new Set();      // keys a refusing localStorage could not keep, for this load

function packGet(k){
  if (PACK_MEM.has(k)) return true;
  try { return localStorage.getItem(k) === "1"; } catch (e) { return false; }
}
function packPut(k){
  try { localStorage.setItem(k, "1"); } catch (e) { PACK_MEM.add(k); }
}
/* The pack's week is the schedule's this-week (data/schedule.js schedWeek). */
const packKey = (team, wk) => `tw-pack-${team.key}-${wk}`;
const packSkipKey = (team, wk) => `tw-pack-skip-${team.key}-${wk}`;
const packOpened = (team, wk) => packGet(packKey(team, wk));
const packMark = (team, wk) => packPut(packKey(team, wk));
const packSkipped = (team, wk) => packGet(packSkipKey(team, wk));
const packSkipMark = (team, wk) => packPut(packSkipKey(team, wk));
/* A metal or a signed card is a hit: it holds the stage. Metal tiers count up from the stock. */
const PACK_METAL = {base: 0, silver: 1, gold: 2, holo: 3};
const packHit = c => PACK_METAL[cardTier(c.rank)] > 0 || !!cardSigned(c.p);
/* Worst first, best last: the stock by rank (K, DST and the unranked first), then the hits by metal
   and rank, a signed card of the same rank after an unsigned one. A signed stock card is a hit, so
   it comes after every stock card. */
function packScore(c){
  if (!packHit(c)) return c.rank ? 500 - c.rank : 0;
  return 1000 + PACK_METAL[cardTier(c.rank)] * 100 + (100 - (c.rank || 100)) + (cardSigned(c.p) ? .5 : 0);
}
/* The pack is the starters, each with his profile index (starters come first, drawer.js findPlayer). */
function packCards(team){
  const support = p => p.pos === "K" || p.pos === "DST";
  return team.roster.filter(p => p.start).map((p, i) => ({p, i, rank: support(p) ? null : cardRank(p)}))
    .sort((a, b) => packScore(a) - packScore(b));
}

/* There is a pack this week when the projections rank anyone on the roster (2026-09-27): a bad week
   gets its pack too. With no ranks at all (no projections yet) there is nothing to open. */
const packHas = team => team.roster.some(p => p.start) && team.roster.some(p => cardRank(p));
/* The best card's tier, which the pack glows in; "none" when the best is stock, which does not glow. */
const packBest = cards => {
  const top = cards[cards.length - 1];
  return top && cardTier(top.rank) !== "base" ? cardTier(top.rank) : "none";
};

/* The pack waits in the starters' place: Cards mode, a followed team (data/mates.js followLoad), and
   this week's pack neither opened nor skipped. */
function packGated(team){
  const wk = schedWeek();
  return ROSTER_MODE === "cards" && !!wk && packHas(team) && followLoad().includes(team.key)
    && !packOpened(team, wk) && !packSkipped(team, wk);
}
/* What the Starters rule offers (cardmotion.js reripHTML): "again" once opened, "open" when skipped
   or only browsed, "wait" (drawn, hidden) while the gate stands, so Skip has a chip to shrink into. */
function packChip(team){
  const wk = schedWeek();
  if (!wk || !packHas(team) || packShowing()) return "";
  return packOpened(team, wk) ? "again" : packGated(team) ? "wait" : "open";
}

/* The sealed pack (art reworked 2026-09-25: it was a plain gradient with a dark band for a strip).
   Holo foil, ridged heat seals at both ends and a perforated tear strip in the same foil. The key
   art is drawn as SVG so it scales with the pack: the brand's // as two lime stripes across it,
   faint yard lines, and the week's number, huge and embossed under a small WEEK (a printed
   "WEEK 3" line as well said it twice). The logo at the top, its // the header's two bars, which
   cross into an X as the pack opens, and the season up the side. No card count (2026-09-27).
   Under the strip is the pack's open mouth, dark with the cards' top edges, so a tear shows an
   opening rather than more foil. The glow is the best tier: how good, never who. */
function packArtSVG(wk){
  const size = String(wk).length > 1 ? 74 : 104;
  return `<svg class="pack-art" viewBox="0 0 100 140" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <path class="pa-yards" d="M0 46h100M0 66h100M0 86h100M0 106h100M0 126h100M33 55v3M67 55v3M33 75v3M67 75v3M33 95v3M67 95v3M33 115v3M67 115v3"/>
      <path class="pa-slash" d="M-8 140H14L68 0H46ZM20 140H30L84 0H74Z"/>
      <text class="pa-wl" x="50" y="${size > 90 ? 58 : 70}" text-anchor="middle" font-size="7">${t("teams.pack.weekWord")}</text>
      <text class="pa-wk" x="50" y="${size > 90 ? 132 : 124}" text-anchor="middle" font-size="${size}">${wk}</text>
    </svg>`;
}
/* The back's creases (pack.css .pr-creases), in a 100x140 box stretched to the pack: short folds
   fanning in from both crimps, and a few long soft wrinkles across the body. Each is drawn twice,
   the lit side a hair off the dark one. */
const PACK_CREASES = "M18 5L24 22M34 5L33 17M52 5L57 19M70 5L66 21M86 5L80 18"
  + "M16 135L22 118M36 135L35 122M56 135L61 117M74 135L69 120M88 135L82 121"
  + "M5 44Q26 48 40 64M95 72Q72 80 60 98M8 104Q22 99 32 112M92 30Q80 36 74 48";
function packRearHTML(){
  return `<span class="pack-rear" aria-hidden="true"><i class="pack-bulge"></i><i class="pr-fin"></i>
    <svg class="pr-creases" viewBox="0 0 100 140" preserveAspectRatio="none"><path class="dip" d="${PACK_CREASES}" vector-effect="non-scaling-stroke"/>
      <path class="rise" d="${PACK_CREASES}" transform="translate(.6 .4)" vector-effect="non-scaling-stroke"/></svg>
    <svg class="pr-mark" viewBox="0 0 40 40"><circle class="ring" cx="20" cy="20" r="18.5"/><circle class="in" cx="20" cy="20" r="15"/>
      <path class="bars" d="M13.5 29.5L20 10.5h3.4l-6.5 19zM20.6 29.5l6.5-19h3.4l-6.5 19z"/></svg>
    <b>TEAM<i>//</i>WATCH</b><small>${t("teams.pack.backLine", {season: packSeason()})}</small><i class="pr-code"></i></span>`;
}
function packSealHTML(team, wk, cards){
  const best = packBest(cards);
  // The rear and the side seams give the pack its body (pack.css); only the front is a control.
  // No wrapper around the seams: an element between them and .pack-glow would flatten them.
  return `<div class="pack-glow tease-${best}">${packRearHTML()}<i class="pack-wall l" aria-hidden="true"></i><i class="pack-wall r" aria-hidden="true"></i>
    <button class="pack-seal" type="button" aria-label="${t("teams.pack.open")}">
      <span class="pack-foil">${packArtSVG(wk)}<i class="pack-bulge"></i></span>
      <span class="pack-top"><i class="pt-mouth"></i><i class="pt-base"></i><i class="pt-flap"></i><i class="pt-edge"></i></span>
      <b>TEAM<i class="slashes" aria-hidden="true"><b></b><b></b></i>WATCH</b>
      <span class="pack-side">${t("teams.pack.side", {season: packSeason()})}</span>
    </button></div>`;
}
/* The season the pack's week belongs to: the year of its first kickoff on the schedule. */
function packSeason(){
  const g = typeof LIVE_SCHEDULE !== "undefined" && LIVE_SCHEDULE && LIVE_SCHEDULE.games[0];
  return g ? new Date(g.kickoff).getUTCFullYear() : "";
}

/* The page's ways onto the stage: the gate (packgate.js), and the Starters rule's chip, which grows
   the pack out of itself. */
function wirePack(v, team){
  const gate = v.querySelector(".pk-gate");
  if (gate) packGateWire(v, team, gate);
  v.querySelectorAll("[data-pkopen],[data-rerip]").forEach(b => b.addEventListener("click", () => {
    packShow(team, schedWeek(), b.querySelector(".rm-pk, svg") || b);
  }));
}

/* The tear (2026-09-25, reworked twice the same day: it jumped, then it always began at the left
   edge wherever the finger was). It has to be torn: a drag that starts on the strip across the top.
   It starts under the finger and runs the way the finger goes, either way: the torn stretch of the
   strip runs from --ta to --tb (0..1 of the width), --te is the end the finger is on and --tdir its
   direction, and --tear is how far along the gesture is (the torn length over 75% of the width).
   The torn stretch lifts off at the finger while the rest stays on (pack.css). Every eighth of the
   way ticks: a buzz and a few flakes from the tear point (onTick). Let go past 55% and the whole
   strip tears by itself; short of that it closes back up to where it started, both eased by the
   registered properties' transitions, not a jump. A touch anywhere else goes to onBody (the stage
   turns the pack with it, packshow.js pkTilt), which tugs the strip when it was only a tap.
   Enter or Space on the focused pack tears it at once. */
const RIP_STEPS = 8, RIP_DONE = .55, RIP_EDGE = .3;
function wireRip(seal, onRip, onTick, onBody){
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
    if (e.clientY - r.top > r.height * .3) return onBody ? onBody(e, nudge) : nudge();   // the strip, and a thumb's width under it
    // A grip near either end starts the tear at that end (2026-09-27): a finger never lands on the
    // very edge, and the tear then left a stub of strip standing beside it.
    s = frac(e); step = 0;
    if (s < RIP_EDGE) s = 0; else if (s > 1 - RIP_EDGE) s = 1;
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

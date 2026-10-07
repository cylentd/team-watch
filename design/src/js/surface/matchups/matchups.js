/* ============================== MATCHUPS ==============================
   This week > Matchups (leaf `matchups`, hash #matchups, #startsit or #takes; was Takes until 2026-10-03,
   Start/Sit until 2026-10-06 and Matchups until 2026-09-29). Top down: the matchup board with its "Compare
   two" link, the record (record.js), our SMASH players (smash.js), our bold START and SIT calls (rows.js),
   then last week's calls. The picker (picker.js) is behind "Compare two" (David, 2026-10-06): it opens as a
   full page in the view, with a back link, and is a layer, so the browser's Back closes it and returns to the
   board where it was left (never a bottom sheet, STYLE.md "Overlays"). Version 3 (2026-10-04, David: "SMASH, START, SIT for only those we have confidence
   in. No coin flips."): our own projections only, no close calls, and the experts only as a for-fun
   line of the record. The page computes nothing: every call and the record are ff-jarvis's
   (LIVE_SS3). The matchup itself moved to Ranks, a tag on the row. No method footer, scoring rules
   or version notes (2026-09-30, David: show, don't tell). */

/* No calls at all (ff-jarvis has not posted the week): Blip says so, in place of the two cards. */
function muBlipHTML(){
  return `<section class="mu-blip">${blipSVG(t("matchups.blip.name"), "bored")}
    <div><q>${t("matchups.blip.none")}</q><p>${t("matchups.blip.noneWhen")}</p></div></section>`;
}

/* SMASH and the bold calls, two columns on a desktop when both have rows. */
function muCallsHTML(){
  const d = LIVE_SS3;
  if (!d.smash.length && !d.takes.length) return muBlipHTML();
  return `<div class="mu-calls${d.smash.length && d.takes.length ? " two" : ""}">${muSmashHTML()}${muTakesHTML()}</div>`;
}

let SS_CMP = false;    // the Compare two page is open, a layer Back closes
let SS_Y = 0;          // where the board was scrolled when it opened

/* Compare two opens the picker over the board as a page; Back (the layer) and the back link close it. Safe
   after the reader left the view: closing only resets state. */
function ssCmpOpen(){
  if (SS_CMP) return;
  SS_Y = window.scrollY;
  SS_CMP = true;
  layerPush("sscmp", ssCmpClose);
  render();
  window.scrollTo(0, 0);
}

function ssCmpClose(){
  SS_CMP = false;
  if (SURFACE !== "matchups") return;
  render();
  window.scrollTo(0, SS_Y);
  requestAnimationFrame(() => window.scrollTo(0, SS_Y));
}

function matchupsHTML(){
  if (SS_CMP) return `<div class="mu cmp"><button type="button" class="ssv-back" data-ssback>${t("matchups.compare.back")}</button>
    <div class="ssv one">${ssPickHTML()}</div></div>`;
  return `<div class="mu">
    <div class="ssv one">${ssBoardHTML() || ssCmpCardHTML()}</div>
    ${muRecordHTML()}
    ${muCallsHTML()}
    ${muLastHTML()}
  </div>`;
}

/* A row opens in place, never by re-render: its own spring is the motion, and the list must not
   be redrawn under the reader. One open at a time; a second tap closes it. */
function wireMatchups(v){
  ssWirePick(v);
  ssWireBoard(v);
  // Delegated on the page, since a board tab repaints the card (and its link) in place.
  v.querySelector(".mu").addEventListener("click", e => {
    if (e.target.closest("[data-sscmp]")) ssCmpOpen();
    else if (e.target.closest("[data-ssback]")){ ssCmpClose(); layerDone("sscmp"); }
  });
  v.querySelectorAll(".mu-call-h").forEach(h => h.addEventListener("click", () => {
    const key = h.parentElement.dataset.mukey;
    MU_OPEN = MU_OPEN === key ? "" : key;
    v.querySelectorAll(".mu-call").forEach(r => muSetOpen(r, r.dataset.mukey === MU_OPEN));
  }));
  v.querySelectorAll("[data-muslug]").forEach(el => el.addEventListener("click", () => {
    const r = [...LIVE_SS3.smash, ...LIVE_SS3.takes].find(x => x.slug === el.dataset.muslug);
    if (r) openProfile({n: r.name, pos: r.pos, team: r.team, slug: r.slug}, el);
  }));
  v.querySelectorAll("[data-ssgo]").forEach(b => b.addEventListener("click", () => {
    navGo(b.dataset.ssgo);
    window.scrollTo({top: 0});
  }));
}

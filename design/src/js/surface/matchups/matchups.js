/* ============================== MATCHUPS ==============================
   Matchup > Start/Sit (leaf `matchups`, hash #matchups, #startsit or #takes; was Takes until 2026-10-03).
   Top down since 2026-10-09 (ledger #94, draft A; David: the first card did not answer the question): the
   reader's lineup with our one swap (lineup.js), our SMASH, START and SIT calls a page at a time with the record
   in their head (calls.js), last week's calls (record.js), then the matchup board (board.js), the research. The
   picker (picker.js) is the Compare page, opened from the lineup card: a full page in the view with a back
   link, and a layer, so the browser's Back closes it and returns to where the reader was (never a bottom sheet,
   STYLE.md "Overlays"). Our own projections only (METHODOLOGY 12.75); the page computes nothing: every call and
   the record are ff-jarvis's (LIVE_SS3), every point the Ranks rows'. No method footer (David: show, don't tell). */

/* No calls at all (ff-jarvis has not posted the week): Blip says so, in place of the calls card; `rec` is the
   record's line, which stands (calls.js). */
function muBlipHTML(rec){
  return `<section class="mu-blip">${blipSVG(t("matchups.blip.name"), "bored")}
    <div><q>${t("matchups.blip.none")}</q><p>${t("matchups.blip.noneWhen")}</p>${rec}</div></section>`;
}

let SS_CMP = false;    // the Compare page is open, a layer Back closes
let SS_Y = 0;          // where the view was scrolled when it opened

/* The Compare page opens over the view; Back (the layer) and the back link close it. Safe after the reader
   left the view: closing only resets state. */
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
    <div class="mu-duo">${muLineupHTML()}${muCallsHTML()}</div>
    ${muLastHTML()}
    <div class="ssv one">${ssBoardHTML()}</div>
  </div>`;
}

/* Every tap is delegated on the view, since the calls card and a board tab repaint their own card in place.
   A bold call opens in place, never by re-render: its own spring is the motion, and the list must not be
   redrawn under the reader. One open at a time; a second tap closes it. */
function wireMatchups(v){
  ssWirePick(v);
  ssWireBoard(v);
  muFitCalls(v);
  v.querySelector(".mu").addEventListener("click", e => {
    const at = sel => e.target.closest(sel);
    if (at("[data-mucmp]")) return muCompareSwap();
    if (at("[data-sscmp]")) return ssCmpOpen();
    if (at("[data-ssback]")){ ssCmpClose(); return layerDone("sscmp"); }
    if (at("[data-mupick]")){ e.stopPropagation(); return muOpenSwitch(); }
    const kind = at("[data-mukind]"), step = at("[data-mupg]");
    if (kind) return muCallsGo(kind.dataset.mukind, 0);
    if (step) return muCallsGo("", +step.dataset.mupg);
    const head = at(".mu-call-h");
    if (head){
      const key = head.parentElement.dataset.mukey;
      MU_OPEN = MU_OPEN === key ? "" : key;
      return v.querySelectorAll(".mu-call").forEach(r => muSetOpen(r, r.dataset.mukey === MU_OPEN));
    }
    const lu = at("[data-mulu]"), sm = at("[data-muslug]");
    if (lu){ const p = ssPlayer(lu.dataset.mulu); return p && openProfile({n: p.n, pos: p.pos, team: p.team, slug: p.slug}, lu); }
    if (sm){
      const r = [...LIVE_SS3.smash, ...LIVE_SS3.takes].find(x => x.slug === sm.dataset.muslug);
      return r && openProfile({n: r.name, pos: r.pos, team: r.team, slug: r.slug}, sm);
    }
    const go = at("[data-ssgo]");
    if (go){ navGo(go.dataset.ssgo); window.scrollTo({top: 0}); }
  });
}

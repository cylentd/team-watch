/* ------------------------------------------------------------------
   PREVIEW — This week > Preview. A slate and a dossier (2026-09-29, storyboard option A; it
   superseded option C, one game a screen, the same day: David wanted "more research and evaluation
   of this matchup" and "all slates so it's easy to find and click one").

   A phone opens on the slate (slate.js); a tap opens that game's dossier (dossier.js) and pushes a
   URL-less history entry (chrome/layers.js), so Back returns to the slate at the scroll it left. The
   game is not in the hash: only the view is (CLAUDE.md, Navigation), and a reload lands on the slate,
   one tap from any game. A desktop (960px+) draws both, the slate as a rail beside the dossier, and a
   click only changes the game. Inside the dossier the arrows and a sideways swipe walk the games in
   kickoff order (lib/swipe.js). The take is opinion and the footer says so once.
------------------------------------------------------------------ */
let PV_ENTER = "";         // the side the dossier slides in from after a turn; "" on a plain draw
let PV_SCROLLED = false;   // the slate scrolls to the next game once per load, once the week has begun
const pvWide = () => matchMedia("(min-width:960px)").matches;

function pvViewHTML(){
  const gs = pvGames();
  if (!gs.length) return `<div class="wrap"><div class="state-empty" style="min-height:220px">
    <div><b>${t("preview.empty.title")}</b><span>${t("preview.empty.sub")}</span></div></div></div>`;
  const i = pvIndex();
  const rec = PV_REC && pvRecord() && pvRecord().weeks.length;
  // The slip's tray joins the page once a pick is in it (handoff.js), the same tray as Slips'.
  const tray = SLIP.length || BETS_SHEET;
  const html = `<div class="wrap pv${PV_OPEN ? " open" : ""}${rec ? " rec" : ""}${tray ? " pv-tray" : ""}">
    ${pvSlateHTML(rec ? -1 : i)}
    ${rec ? pvRecSheetHTML() : pvDossierHTML(gs[i], i, gs.length, PV_ENTER)}
  </div>${tray ? trayHTML() + sheetHTML() : ""}`;
  PV_ENTER = "";
  return html;
}

/* A turn redraws the view with the new dossier sliding in from the side it came from. */
function pvTurn(d){
  if (!pvStep(d)) return;
  PV_ENTER = d > 0 ? " in-r" : " in-l";
  render();
  if (!pvWide()) window.scrollTo(0, 0);
}

/* The dossier opens over the slate on a phone, as a layer Back closes. */
function pvOpen(i){
  PV_I = i;
  if (pvWide()){
    if (PV_REC){ PV_REC = false; layerDone("pvrecord"); }   // a desktop: a game takes the record's place
    render();
    return;
  }
  PV_Y = window.scrollY;
  PV_OPEN = true;
  layerPush("preview", pvClose);
  render();
  window.scrollTo(0, 0);
}

/* Back to the slate where it was left. Safe after the reader left the view: it only resets state. */
function pvClose(){
  PV_OPEN = false;
  if (SURFACE !== "preview") return;
  render();
  window.scrollTo(0, PV_Y);
  requestAnimationFrame(() => window.scrollTo(0, PV_Y));
}

/* The every-week record opens as a layer Back closes: over the slate on a phone, in the dossier's
   place on a desktop. */
function pvRecOpen(){
  PV_Y = window.scrollY;
  PV_REC = true;
  layerPush("pvrecord", pvRecClose);
  render();
  if (!pvWide()) window.scrollTo(0, 0);
}

function pvRecClose(){
  PV_REC = false;
  if (SURFACE !== "preview") return;
  render();
  if (pvWide()) return;
  window.scrollTo(0, PV_Y);
  requestAnimationFrame(() => window.scrollTo(0, PV_Y));
}

/* Once the week has begun, the slate opens scrolled to the next game to kick off. */
function pvScrollToNext(v){
  if (PV_SCROLLED || PV_OPEN || PV_REC || pvWide()) return;
  PV_SCROLLED = true;
  const gs = pvGames(), next = gs.findIndex(g => !pvDone(g));
  if (next > 0) v.querySelector(`[data-pvopen="${next}"]`)?.scrollIntoView({block: "start"});
}

function wirePreview(v){
  v.querySelectorAll("[data-pvopen]").forEach(b => b.addEventListener("click", () => pvOpen(+b.dataset.pvopen)));
  v.querySelectorAll("[data-pvstep]").forEach(b => b.addEventListener("click", () => pvTurn(+b.dataset.pvstep)));
  v.querySelector("[data-pvback]")?.addEventListener("click", () => { pvClose(); layerDone("preview"); });
  const recShut = () => { pvRecClose(); layerDone("pvrecord"); };
  v.querySelector("[data-pvrec]")?.addEventListener("click", () => PV_REC ? recShut() : pvRecOpen());   // a desktop's card toggles
  v.querySelector("[data-pvrecback]")?.addEventListener("click", recShut);
  const g = pvGames()[pvIndex()];
  v.querySelectorAll("[data-pvp]").forEach(el => el.addEventListener("click", () => {
    const p = g && g.take && g.take.players[+el.dataset.pvp];
    if (p) openProfile({n: p.n, pos: p.pos, team: p.team, slug: p.slug}, el);
  }));
  // A horizontal swipe turns the game; a mostly-vertical drag is a scroll and is left alone (lib/swipe.js).
  const card = v.querySelector("[data-pvswipe]");
  if (card) onSwipeX(card, pvTurn);
  if (PV_OPEN && history.state?.layer === "preview") layerAdopt("preview", pvClose);   // Back from Slips lands on the dossier
  wirePvSlip(v);
  pvScrollToNext(v);
}

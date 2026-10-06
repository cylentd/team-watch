/* ============================== LEAGUE > TRADES: THE EDIT PAGE ==============================
   2026-10-06 (trade finder, unit U4; the page machinery of the retired Teams page, lbpage.js). Edit and Make your own
   offer (lboard/tbedit.js) open on a page of their own in the Trades view: no sheet, no scrim (David, 2026-10-05: nothing
   slides up from the bottom), the nav bar and League sub-row still on screen. The page is a history entry
   (chrome/layers.js, no URL change, so a reload lands on the finder): Back and the "‹ Offers" link each return to the
   finder, and it comes back at the scroll the reader left (TF_Y). */
let TF_Y = 0;               // the finder's scroll, put back when the page closes

const tfChev = `<svg class="lbp-chev" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 4L6 8l4 4"/></svg>`;
const tfBackHTML = label => `<button type="button" class="lbp-back" data-tfback data-testid="finder-back">${tfChev}<span>${label}</span></button>`;
const tbSwap = `<svg class="tb-swap" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7h12M15 3l4 4-4 4M17 17H5M9 13l-4 4 4 4"/></svg>`;

/* Forward remembers the scroll and starts the page at the top; back draws the finder again and puts that scroll back
   (twice: the browser also restores one of its own after a Back, a frame later). */
function tfForward(){ TF_Y = window.scrollY; }
function tfShow(){
  render();
  window.scrollTo({top: 0, behavior: "instant"});
  document.querySelector(".lbp-back")?.focus({preventScroll: true});
}
function tfBack(){
  const y = TF_Y, put = () => window.scrollTo({top: y, behavior: "instant"});
  render();
  put();
  requestAnimationFrame(put);
}

/* Make your own with no partner chosen: the page lets the reader pick one, every other team in the league. */
function tfPartnerPickHTML(){
  const opts = TB.lg.teams.filter(x => x.key !== TB.me.key).map(x =>
    `<option value="${esc(x.key)}"${x.key === TB.tm.key ? " selected" : ""}>${esc(x.name)}</option>`).join("");
  return `<label class="selwrap tf-pick"><span class="lbl">${t("finder.edit.partner")}</span>
    <select class="msel" data-tbpartner data-testid="finder-partner-pick">${opts}</select></label>`;
}

function tfEditPageHTML(){
  return `<div class="wrap lbp">${tfBackHTML(t("lboard.offer.backOffers"))}
    <h1 class="lbp-title" id="tb-title" aria-label="${t("lboard.offer.title", {name: esc(TB.tm.name)})}">${t("lboard.offer.you")}${tbSwap}${esc(TB.tm.name)}</h1>
    ${TB_EDIT.pick ? tfPartnerPickHTML() : ""}
    <div class="tb-body tb-ed">${tbEditHTML()}</div></div>`;
}

/* The reader left Trades with the edit page open (a tap on another view): nothing of it is kept. */
function tfLeft(){
  TB = null; TB_EDIT = null; TF_Y = 0;
  layerForget("tbedit");
}

/* The page's taps, wired per draw: the page is new each time, so its one listener never stacks on the view. */
function wireTfPage(v){
  const root = v.querySelector(".lbp");
  if (!root) return;
  root.addEventListener("click", e => {
    const hit = sel => e.target.closest(sel);
    if (hit("[data-tfback]")) return tbEditClose();
    tbEditClick(hit);
  });
  root.addEventListener("change", e => {
    if (!e.target.matches("[data-tbpartner]")) return;
    const tm = TB.lg.teams.find(x => x.key === e.target.value);
    if (tm) tbEditPartner(tm);
  });
}

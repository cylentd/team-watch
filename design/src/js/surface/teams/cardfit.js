/* Sizing what a card prints to the card it is printed on (2026-10-05, out of cards.js): the
   autograph and the banner's name are measured in the reader's browser, never guessed. */

/* Shrink each signature until its .sgw fits the box it is drawn in, never under 9px, so a long
   name is never cut off; a name too long even at 9px is signed with the last name alone. It reads
   and sets only what is under `root`, and can be run again (a resize, a font arriving). */
function fitSig(root){
  root.querySelectorAll(".tc-auto").forEach(a => {
    const w = a.querySelector(".sgw");
    if (!w) return;
    const names = [...w.querySelectorAll(".sg")], full = a.dataset.full || (a.dataset.full = names[0].textContent);
    const shrink = () => {
      a.style.fontSize = "";
      let fs = parseFloat(getComputedStyle(a).fontSize) || 24;
      while (w.offsetWidth > a.clientWidth && fs > 9){ fs -= 1; a.style.fontSize = fs + "px"; }
      return w.offsetWidth <= a.clientWidth;
    };
    names.forEach(n => { n.textContent = full; });
    if (!shrink()){ names.forEach(n => { n.textContent = cardLast(full); }); shrink(); }
  });
}
/* The same for the name on a banner ("MONTGOMERY"): down to 10px until it ends before the badge. It
   measures by offsets, which a turned-over card's 3D transform does not change. */
function fitBanner(root){
  root.querySelectorAll(".tc-ban span").forEach(s => {
    const badge = s.closest(".tc-front")?.querySelector(".tc-badge");
    s.style.fontSize = "";
    s.style.maxWidth = "none";
    const room = (badge ? badge.offsetLeft : s.offsetParent.offsetWidth) - 3;
    let fs = parseFloat(getComputedStyle(s).fontSize) || 12;
    while (s.offsetLeft + s.offsetWidth > room && fs > 10){ fs -= .5; s.style.fontSize = fs + "px"; }
    s.style.maxWidth = "";
  });
}
/* A Sheet row's name (David, 2026-10-07): the full name on one line, or initials when the full one would wrap
   ("Jacory Croskey-Merritt" took two lines on a desktop bench). Measured in the reader's browser: the full name
   goes in first, a second line box means it does not fit. A phone already shows initials from CSS (nm-full is
   hidden there, so it has no boxes and is left alone). */
function fitRowNames(root){
  root.querySelectorAll(".row .nm-1 b").forEach(b => {
    const full = b.querySelector(".nm-full");
    b.classList.remove("ini", "sm");
    if (!full || full.getClientRects().length < 2) return;
    b.classList.add("ini");
    const ini = b.querySelector(".nm-ini");
    if (ini && ini.getClientRects().length > 1) b.classList.add("sm");   // initials still wrap: a size down, never cut
  });
}
let ROWNAMES_FIT_WIRED = false;
function rowNamesFit(){
  const run = () => fitRowNames(document);
  requestAnimationFrame(run);
  if (ROWNAMES_FIT_WIRED) return;
  ROWNAMES_FIT_WIRED = true;
  if (document.fonts) document.fonts.addEventListener("loadingdone", run);
  addEventListener("resize", () => requestAnimationFrame(run));
}

/* After a render, again whenever fonts finish loading (a face's width is not known before they do:
   the first render asks for them) and when the window resizes (a desktop card's width follows it). */
let CARDS_FIT_WIRED = false;
function cardsFit(){
  const run = () => { fitSig(document); fitBanner(document); };
  requestAnimationFrame(run);
  if (CARDS_FIT_WIRED) return;
  CARDS_FIT_WIRED = true;
  if (document.fonts) document.fonts.addEventListener("loadingdone", run);
  addEventListener("resize", () => requestAnimationFrame(run));
}

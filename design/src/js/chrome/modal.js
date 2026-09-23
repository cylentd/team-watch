/* Centered popups, distinct from #drawer's slide-over (still used by the pool and DFS explain
   drawers). One opens with a scale+fade grown out of the element that was clicked -- motion says
   "this is that row, expanded," not "a new screen appeared" -- and reverses the same way on close.
   Dialog mechanics (focus trap, Escape, scrim) mirror showDrawer/closeDrawer.

   There are two of them, and they stack: the drive strip opens FROM the player profile (a week in
   his game log), so it cannot reuse #modal without throwing away the profile the reader is still
   in the middle of. Each dialog names its own scrim in data-scrim and owns its own return focus,
   so the two never fight over one element's listeners, and Escape closes the topmost rather than
   all of them. */
const MODAL_RETURN = new Map();

const modalScrim = d => document.getElementById(d.dataset.scrim);
const modalOpen = () => [...document.querySelectorAll(".modal.on")];

function showModal(d, originEl, labelledby){
  MODAL_RETURN.set(d.id, document.activeElement);
  d.setAttribute("role", "dialog"); d.setAttribute("aria-modal", "true");
  if (labelledby) d.setAttribute("aria-labelledby", labelledby); else d.removeAttribute("aria-labelledby");
  const r = originEl && originEl.getBoundingClientRect ? originEl.getBoundingClientRect() : null;
  d.style.setProperty("--dx", r ? `${(r.left + r.width / 2 - window.innerWidth / 2).toFixed(0)}px` : "0px");
  d.style.setProperty("--dy", r ? `${(r.top + r.height / 2 - window.innerHeight / 2).toFixed(0)}px` : "0px");
  d.scrollTop = 0;
  // Force the "from" transform to paint before the "on" class animates it away -- without a
  // reflow between them the browser coalesces both into one frame and nothing moves.
  d.classList.remove("on"); void d.offsetWidth;
  d.classList.add("on"); d.setAttribute("aria-hidden", "false");
  modalScrim(d).classList.add("on");
  const close = d.querySelector(".dr-close");
  close.addEventListener("click", () => closeModal(d));
  close.focus({preventScroll: true});
}

/* Closes one dialog, or the topmost open one. "Topmost" is the last in document order, which is
   also the one with the higher z-index, so Escape and a scrim click agree with what is on top. */
function closeModal(d){
  d = d || modalOpen().pop();
  if (!d || !d.classList.contains("on")) return;
  d.classList.remove("on");
  d.setAttribute("aria-hidden", "true");
  modalScrim(d).classList.remove("on");
  const back = MODAL_RETURN.get(d.id);
  MODAL_RETURN.delete(d.id);
  if (back && back.focus && back.isConnected) back.focus({preventScroll: true});
}

document.querySelectorAll(".modal-scrim").forEach(s => s.addEventListener("click", () => {
  closeModal([...document.querySelectorAll(".modal.on")].find(d => d.dataset.scrim === s.id));
}));
document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });
document.querySelectorAll(".modal").forEach(d => d.addEventListener("keydown", e => {
  if (e.key !== "Tab") return;
  const f = [...e.currentTarget.querySelectorAll("button:not([hidden]), a[href], summary, input, [tabindex]:not([tabindex='-1'])")];
  if (!f.length) return;
  if (e.shiftKey && document.activeElement === f[0]){ e.preventDefault(); f[f.length - 1].focus(); }
  else if (!e.shiftKey && document.activeElement === f[f.length - 1]){ e.preventDefault(); f[0].focus(); }
}));

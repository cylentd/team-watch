/* The player profile as a centered popup, distinct from #drawer's slide-over (still used by the
   pool and DFS explain drawers). Opens with a scale+fade grown out of the row that was clicked --
   motion says "this is that row, expanded," not "a new screen appeared" -- and reverses the same
   way on close. Dialog mechanics (focus trap, Escape, scrim) mirror showDrawer/closeDrawer, on
   #modal's own scrim so the two never fight over one element's listeners. */
let MODAL_RETURN = null;

function showModal(d, originEl, labelledby){
  MODAL_RETURN = document.activeElement;
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
  document.getElementById("modal-scrim").classList.add("on");
  const close = d.querySelector(".dr-close");
  close.addEventListener("click", closeModal);
  close.focus({preventScroll: true});
}

function closeModal(){
  const d = document.getElementById("modal");
  if (!d.classList.contains("on")) return;
  d.classList.remove("on");
  d.setAttribute("aria-hidden", "true");
  document.getElementById("modal-scrim").classList.remove("on");
  if (MODAL_RETURN && MODAL_RETURN.focus) MODAL_RETURN.focus({preventScroll: true});
  MODAL_RETURN = null;
}
document.getElementById("modal-scrim").addEventListener("click", closeModal);
document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });
document.getElementById("modal").addEventListener("keydown", e => {
  if (e.key !== "Tab") return;
  const f = [...e.currentTarget.querySelectorAll("button:not([hidden]), a[href], summary, [tabindex]:not([tabindex='-1'])")];
  if (!f.length) return;
  if (e.shiftKey && document.activeElement === f[0]){ e.preventDefault(); f[f.length - 1].focus(); }
  else if (!e.shiftKey && document.activeElement === f[f.length - 1]){ e.preventDefault(); f[0].focus(); }
});

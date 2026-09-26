/* The cards' motion (surface/teams/cards.js): tilt toward the pointer or a dragging finger, the foil
   and glare following the same point through --mx/--my, the photo drifting against the tilt
   through --px/--py, and a flip on tap. Plain CSS transitions
   driven by custom properties -- no animation library, the page carries its own weight. Reduced
   motion keeps the light and the flip's result and drops the tilt and the turn. */
function wireCards(v){
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  v.querySelectorAll(".tc").forEach(el => {
    el.addEventListener("pointermove", e => {
      const r = el.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      el.classList.add("live");
      el.style.setProperty("--mx", `${(x * 100).toFixed(1)}%`);
      el.style.setProperty("--my", `${(y * 100).toFixed(1)}%`);
      if (!still){
        el.style.setProperty("--ry", `${((x - .5) * 20).toFixed(1)}deg`);
        el.style.setProperty("--rx", `${((.5 - y) * 20).toFixed(1)}deg`);
        // -0.5..0.5, unitless: the photo's parallax multiplies it into pixels (cards.css).
        el.style.setProperty("--px", (x - .5).toFixed(3));
        el.style.setProperty("--py", (y - .5).toFixed(3));
      }
    });
    el.addEventListener("pointerleave", () => {
      el.classList.remove("live");
      ["--mx", "--my", "--rx", "--ry", "--px", "--py"].forEach(k => el.style.removeProperty(k));
    });
    const turn = () => el.classList.toggle("back");
    el.addEventListener("click", e => { if (!e.target.closest(".bk-open")) turn(); });
    el.addEventListener("keydown", e => {
      if (e.target !== el || (e.key !== "Enter" && e.key !== " ")) return;
      e.preventDefault(); turn();
    });
  });
  v.querySelectorAll(".bk-open").forEach(b => b.addEventListener("click", e => {
    e.stopPropagation();
    openProfile(findPlayer(b.dataset.cteam, +b.dataset.ci), b);
  }));
}

/* Sheet or Cards: one choice per phone, kept in localStorage, which can be missing or refuse. */
function rosterModeLoad(){
  try { return localStorage.getItem("tw-roster-mode") === "cards" ? "cards" : "sheet"; } catch (e) { return "sheet"; }
}
function rosterModeSave(m){
  try { localStorage.setItem("tw-roster-mode", m); } catch (e) { /* a private window keeps it for this load */ }
}
/* "Rip again" (2026-09-25) follows the Cards chip once this week's pack is open: it puts the pack
   back on the page, sealed, with the same cards (pack.js packReplay). The arrow says "again". */
const RERIP_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/></svg>`;
function rosterModeHTML(team){
  const again = ROSTER_MODE === "cards" && team && packReplayable(team);
  return `<div class="filters rmode" role="group" aria-label="${t("teams.mode.label")}">
    <button class="chip" data-rmode="sheet" aria-pressed="${ROSTER_MODE === "sheet"}">${t("teams.mode.sheet")}</button>
    <button class="chip" data-rmode="cards" aria-pressed="${ROSTER_MODE === "cards"}">${t("teams.mode.cards")}</button>${again ? `
    <button class="chip rm-again" data-rerip>${RERIP_ICON}${t("teams.pack.again")}</button>` : ""}
  </div>`;
}
function wireRosterMode(v, team){
  v.querySelectorAll("[data-rmode]").forEach(b => b.addEventListener("click", () => {
    if (ROSTER_MODE === b.dataset.rmode) return;
    ROSTER_MODE = b.dataset.rmode;
    rosterModeSave(ROSTER_MODE);
    render();
  }));
  v.querySelector("[data-rerip]")?.addEventListener("click", () => packReplay(team));
  if (ROSTER_MODE === "cards") wireCards(v);
}

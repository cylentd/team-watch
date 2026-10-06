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

/* Sheet or Cards: one choice per phone, kept in localStorage, which can be missing or refuse.
   Cards is the default since 2026-09-28, so a new reader meets the week's pack; a stored Sheet wins. */
function rosterModeLoad(){
  try { return localStorage.getItem("tw-roster-mode") === "sheet" ? "sheet" : "cards"; } catch (e) { return "cards"; }
}
function rosterModeSave(m){
  try { localStorage.setItem("tw-roster-mode", m); } catch (e) { /* a private window keeps it for this load */ }
}
/* The pack's chip (2026-09-25; two states since 2026-10-05, pack.js packChip) ends the Starters rule
   over the cards, never in the Sheet / Cards switch: there it came and went with the mode and moved
   both chips each time (2026-09-25). "Open week 5", with a small pack, opens a skipped or browsed
   pack; "Rip again", with an arrow, puts an opened one back on the stage, sealed. While the pack
   waits in the starters' place the chip is drawn but hidden, so Skip has somewhere to shrink it to. */
const RERIP_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/></svg>`;
function reripHTML(team){
  const chip = packChip(team);
  if (chip === "again") return `<button class="rm-again" type="button" data-testid="roster-rerip" data-rerip>${RERIP_ICON}${t("teams.pack.again")}</button>`;
  if (!chip) return "";
  return `<button class="rm-again rm-open${chip === "wait" ? " wait" : ""}" type="button" data-testid="roster-open-week" data-pkopen><i class="rm-pk" aria-hidden="true"></i>${t("teams.pack.openWeek", {wk: schedWeek()})}</button>`;
}
/* Two icon buttons at the hero's right end (2026-10-05): a list is the Sheet, a grid the Cards. */
const RMODE_ICON = {
  sheet: `<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="1" y="2.5" width="14" height="2.4" rx="1"/><rect x="1" y="6.8" width="14" height="2.4" rx="1"/><rect x="1" y="11.1" width="14" height="2.4" rx="1"/></svg>`,
  cards: `<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="1.5" y="1.5" width="5.5" height="5.5" rx="1.3"/><rect x="9" y="1.5" width="5.5" height="5.5" rx="1.3"/><rect x="1.5" y="9" width="5.5" height="5.5" rx="1.3"/><rect x="9" y="9" width="5.5" height="5.5" rx="1.3"/></svg>`,
};
function rosterModeHTML(){
  const btn = (m, name) => `<button type="button" class="chip" data-testid="roster-mode" data-rmode="${m}" aria-pressed="${ROSTER_MODE === m}" aria-label="${name}" title="${name}">${RMODE_ICON[m]}</button>`;
  return `<div class="rmode" role="group" aria-label="${t("teams.mode.label")}">${btn("sheet", t("teams.mode.sheet"))}${btn("cards", t("teams.mode.cards"))}</div>`;
}
function wireRosterMode(v, team){
  v.querySelectorAll("[data-rmode]").forEach(b => b.addEventListener("click", () => {
    if (ROSTER_MODE === b.dataset.rmode) return;
    ROSTER_MODE = b.dataset.rmode;
    rosterModeSave(ROSTER_MODE);
    render();
  }));
  if (ROSTER_MODE === "cards") wireCards(v);
}

/* The player profile as a centered popup in #modal (chrome/modal.js), opened by tapping a
   roster row, a waiver target, or a usage row. `p` needs n/pos/team/slug; `originEl` is the
   clicked element, for the scale-from-row motion. The body is two columns (panel.css): the stat
   sheet on the left (the radar, whose stats are buttons for the trend card under it, then
   facts and projection); the matchup, red zone, target depth, weekly history and Details on
   the right. The three matchup blocks and Details need
   ff-jarvis's per-player profile (LIVE_PROFILES) and say so quietly when it has none; every
   other block reads its own source and simply renders nothing without one, so a player with no
   matchup profile still opens with whatever else the page knows about him. */
function openProfile(p, originEl){
  if (!p) return;
  searchRemember(p);   // the search sheet's "recent" list (chrome/search.js)
  const prof = profileFor(p);
  const d = document.getElementById("modal");
  d.innerHTML = `
    <div class="dr-head pf-head">
      <button type="button" class="dr-close" aria-label="${t("common.action.close")}">✕</button>
      <div class="dr-id">
        ${headHTML(p)}
        <div class="pf-who">
          <h3 id="pf-title">${esc(p.n)}</h3>
          <div class="lbl">${identityHTML(p, prof)}</div>
        </div>
      </div>
      ${p.note ? `<div class="dr-note">${esc(p.note)}</div>` : ""}
    </div>
    <div class="dr-body pf-body">
      <aside class="pf-side">
        ${radarHTML(p)}
        ${factsHTML(p)}
        ${projectionHTML(p)}
      </aside>
      <div class="pf-main">
        ${prof
          ? headlineHTML(prof) + redZoneHTML(prof) + roleHTML(prof)
          : `<div class="state-empty pf-empty"><div><b>—</b><span>${t("profile.empty.none")}</span></div></div>`}
        ${weeklyHistoryHTML(p)}
        ${prof ? detailsHTML(prof) : ""}
      </div>
    </div>`;
  wireSheet(d);
  showModal(d, originEl, "pf-title");
  /* A week in the game log opens that game's drive strip, over this profile rather than instead
     of it (shell.html has a second dialog for exactly this). Bound after the markup, because
     openProfile rebuilds #modal on every open. */
  d.querySelectorAll("[data-stripwk]").forEach(b => b.addEventListener("click", () => {
    const g = stGameFor(b.dataset.stripclub, +b.dataset.stripwk);
    if (g) openStrip(g, b.dataset.stripname, b);
  }));
}

/* Roster rows and waiver cards both open the profile; one wiring for both. */
function wireProfiles(v){
  const open = el => el.dataset.team !== undefined
    ? openProfile(findPlayer(el.dataset.team, +el.dataset.i), el)
    : openProfile(waiverPlayers()[+el.dataset.wire], el);
  v.querySelectorAll(".row, [data-wire]").forEach(el => {
    el.addEventListener("click", () => open(el));
    el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); open(el); } });
  });
}

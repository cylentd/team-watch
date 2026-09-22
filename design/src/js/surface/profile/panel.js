/* The player profile as a centered popup in #modal (chrome/modal.js), opened by tapping a
   roster row, a waiver target, or a usage row. `p` needs n/pos/team/slug; `sub` is the context
   line (league and slot); `originEl` is the clicked element, for the scale-from-row motion. The
   matchup/role/red-zone blocks and Details disclosure need ff-jarvis's per-player profile
   (LIVE_PROFILES) and say so quietly when it has none; the bio strip and the three history
   blocks below them each read their own source and simply render nothing without one, so a
   player with no matchup profile still opens with whatever else the page knows about him. */
function openProfile(p, sub, originEl){
  if (!p) return;
  const prof = profileFor(p);
  const d = document.getElementById("modal");
  const meta = [esc(prof ? prof.pos : p.pos), esc(prof ? prof.team : p.team), sub ? esc(sub) : ""].filter(Boolean).join(" · ");
  d.innerHTML = `
    <div class="dr-head pf-head">
      <button type="button" class="dr-close" aria-label="${t("common.action.close")}">✕</button>
      <div class="dr-id">
        ${headHTML(p)}
        <div>
          <h3 id="pf-title">${esc(p.n)}</h3>
          <div class="lbl">${meta}</div>
        </div>
      </div>
      ${bioHTML(p)}
      ${p.note ? `<div class="dr-note">${esc(p.note)}</div>` : ""}
    </div>
    <div class="dr-body pf-body">
      ${prof
        ? headlineHTML(prof) + weatherHTML(prof) + roleHTML(prof) + redZoneHTML(prof)
        : `<div class="state-empty pf-empty"><div><b>—</b><span>${t("profile.empty.none")}</span></div></div>`}
      ${usageTrendHTML(p)}
      ${weeklyHistoryHTML(p)}
      ${projectionHTML(p)}
      ${prof ? detailsHTML(prof) : ""}
    </div>`;
  showModal(d, originEl, "pf-title");
}

/* Roster rows and waiver rows both open the profile; one wiring for both. */
function wireProfiles(v){
  const open = el => el.dataset.team !== undefined
    ? openProfile(findPlayer(el.dataset.team, +el.dataset.i), `${TEAMS[el.dataset.team].plat} ${findPlayer(el.dataset.team, +el.dataset.i).slot}`, el)
    : openProfile(waiverFor(VIEW).wire[+el.dataset.wire], t("profile.head.waiver"), el);
  v.querySelectorAll(".row, [data-wire]").forEach(el => {
    el.addEventListener("click", () => open(el));
    el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); open(el); } });
  });
}

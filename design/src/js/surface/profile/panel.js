/* The player profile as a slide-over in the shared #drawer, opened by tapping a roster row or a
   waiver target. `p` needs n/pos/team/slug; `sub` is the context line (league and slot). With no
   profile for him (or no LIVE_PROFILES at all) the panel says so quietly instead of guessing. */
function openProfile(p, sub){
  if (!p) return;
  const prof = profileFor(p);
  const d = document.getElementById("drawer");
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
      ${p.note ? `<div class="dr-note">${esc(p.note)}</div>` : ""}
      ${prof ? `<div class="pf-thru">${verdictChipHTML(prof)}<span>${t("profile.head.through", {wk: LIVE_PROFILES.through_week, season: LIVE_PROFILES.season})}</span></div>` : ""}
    </div>
    <div class="dr-body pf-body">
      ${prof
        ? usageHTML(prof) + coverageHTML(prof) + redZoneHTML(prof) + nextHTML(prof)
        : `<div class="state-empty pf-empty"><div><b>—</b><span>${t("profile.empty.none")}</span></div></div>`}
    </div>`;
  showDrawer(d, "pf-title");
  const tag = d.querySelector(".pf-untested");
  if (tag) tag.addEventListener("click", () => {
    const m = d.querySelector("#pf-method");
    m.hidden = !m.hidden;
    tag.setAttribute("aria-expanded", String(!m.hidden));
  });
}

/* Roster rows and waiver cards both open the profile; one wiring for both. */
function wireProfiles(v){
  const open = el => el.dataset.team !== undefined
    ? openProfile(findPlayer(el.dataset.team, +el.dataset.i), `${TEAMS[el.dataset.team].plat} ${findPlayer(el.dataset.team, +el.dataset.i).slot}`)
    : openProfile(WIRE[+el.dataset.wire].in_, t("profile.head.waiver"));
  v.querySelectorAll(".row, [data-wire]").forEach(el => {
    el.addEventListener("click", () => open(el));
    el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); open(el); } });
  });
}

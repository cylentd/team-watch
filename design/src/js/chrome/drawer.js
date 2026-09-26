/* ---------------------------- drawer ---------------------------- */
function findPlayer(teamKey, i){
  const ordered = TEAMS[teamKey].roster.filter(p=>p.start)
    .concat(TEAMS[teamKey].roster.filter(p=>!p.start && p.slot!=="OUT"))
    .concat(TEAMS[teamKey].roster.filter(p=>p.slot==="OUT"));
  return ordered[i];
}

function openLeagueInfo(key){
  const team = TEAMS[key];
  const leagueName = team.meta[team.meta.length-1];
  const format = team.meta.slice(0, -1);
  const d = document.getElementById("drawer");
  d.innerHTML = `
    <div class="dr-head">
      <button class="dr-close" aria-label="${t("common.action.close")}">✕</button>
      <div class="dr-id">
        <div>
          <h3>${esc(leagueName)}</h3>
          <div class="lbl">${t("drawer.league.meta", {plat: esc(team.plat), slot: team.slot, record: esc(team.record)})}</div>
        </div>
      </div>
    </div>
    <div class="dr-body">
      <div class="dr-sec">
        <span class="lbl">${t("drawer.league.format")}</span>
        <div class="hero-meta" style="margin-top:12px">${format.map(m=>`<span class="pill">${esc(m)}</span>`).join("")}</div>
      </div>
    </div>`;
  showDrawer(d);
}

/* Open as a modal slide-over: focus moves to the close control, Tab stays inside, and closing
   hands focus back to whatever opened it. */
let DRAWER_RETURN = null;
function showDrawer(d, labelledby){
  DRAWER_RETURN = document.activeElement;
  d.setAttribute("role", "dialog"); d.setAttribute("aria-modal", "true");
  if (labelledby) d.setAttribute("aria-labelledby", labelledby); else d.removeAttribute("aria-labelledby");
  d.classList.add("on"); d.setAttribute("aria-hidden","false");
  document.getElementById("scrim").classList.add("on");
  const close = d.querySelector(".dr-close");
  close.addEventListener("click", closeDrawer);
  close.focus({preventScroll: true});
}

function closeDrawer(){
  const d = document.getElementById("drawer");
  if (!d.classList.contains("on")) return;
  d.classList.remove("on");
  d.setAttribute("aria-hidden","true");
  document.getElementById("scrim").classList.remove("on");
  if (DRAWER_RETURN && DRAWER_RETURN.focus) DRAWER_RETURN.focus({preventScroll: true});
  DRAWER_RETURN = null;
}
document.getElementById("scrim").addEventListener("click", closeDrawer);
document.addEventListener("keydown", e=>{ if(e.key==="Escape") closeDrawer(); });
document.getElementById("drawer").addEventListener("keydown", e=>{
  if (e.key !== "Tab") return;
  const f = [...e.currentTarget.querySelectorAll("button:not([hidden]), a[href], summary, [tabindex]:not([tabindex='-1'])")];
  if (!f.length) return;
  if (e.shiftKey && document.activeElement === f[0]){ e.preventDefault(); f[f.length-1].focus(); }
  else if (!e.shiftKey && document.activeElement === f[f.length-1]){ e.preventDefault(); f[0].focus(); }
});


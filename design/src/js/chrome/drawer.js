/* ---------------------------- drawer ---------------------------- */
function findPlayer(teamKey, i){
  const ordered = TEAMS[teamKey].roster.filter(p=>p.start)
    .concat(TEAMS[teamKey].roster.filter(p=>!p.start && p.slot!=="OUT"))
    .concat(TEAMS[teamKey].roster.filter(p=>p.slot==="OUT"));
  return ordered[i];
}

function openPoolDrawer(i){
  const r = POOL[i];
  if (!r) return;
  const d = document.getElementById("drawer");
  const bar = (label, val, max, neg) => `
    <div class="why-row"><div class="t"><b>${label}</b> ${val>0?"+":""}${val}</div>
      <div class="why-bar ${neg?"neg":""}"><i style="width:${Math.min(100,Math.abs(val)/max*100).toFixed(0)}%"></i></div></div>`;
  d.innerHTML = `
    <div class="dr-head">
      <button class="dr-close" aria-label="${t("common.action.close")}">✕</button>
      <div class="dr-id">
        ${avatarHTML(r)}
        <div>
          <h3>${esc(r.n)}</h3>
          <div class="lbl">${esc(r.pos)} · ${esc(r.team)} · ${t("drawer.pool.rostered", {n: r.own})}</div>
        </div>
      </div>
      <div style="margin-top:14px"><span class="vchip ${VCLASS[r.v]}" style="display:inline-block;padding:5px 10px">${esc(r.v.toUpperCase())}</span></div>
    </div>
    <div class="dr-body">
      <div class="dr-sec">
        <span class="lbl">${t("drawer.pool.gap")}</span>
        <div class="why">
          ${bar(t("drawer.pool.snapChange"), r.dSnap, 18, r.dSnap<0)}
          ${bar(t("drawer.pool.shareChange"), r.dShare, 14, r.dShare<0)}
          ${bar(t("drawer.pool.luck"), r.luck, 10, r.luck<0)}
        </div>
        <p style="margin:16px 0 0;color:var(--ink-2);font-size:12.5px;line-height:1.6">
          ${r.dShare > 0 && r.luck < 0
            ? t("drawer.pool.readBuy")
            : r.dShare < 0 && r.luck > 0
            ? t("drawer.pool.readSell")
            : r.dShare > 0
            ? t("drawer.pool.readAgree")
            : t("drawer.pool.readFlat")}
        </p>
      </div>
      <div class="dr-sec">
        <span class="lbl">${t("drawer.pool.raw")}</span>
        <div class="why" style="margin-top:2px">
          <div class="why-row"><div class="t"><b>${t("drawer.pool.snaps")}</b> ${r.snaps}</div><div class="why-bar"><i style="width:${r.snaps}%"></i></div></div>
          <div class="why-row"><div class="t"><b>${t("drawer.pool.share")}</b> ${r.share}%</div><div class="why-bar"><i style="width:${(r.share*3).toFixed(0)}%"></i></div></div>
          <div class="why-row"><div class="t"><b>${t("drawer.pool.redzone")}</b> ${r.rz}</div><div class="why-bar"><i style="width:${r.rz*18}%"></i></div></div>
          <div class="why-row"><div class="t"><b>${t("drawer.pool.ppg")}</b> ${r.ppg}</div><div class="why-bar"><i style="width:${(r.ppg*5).toFixed(0)}%"></i></div></div>
        </div>
      </div>
      <div class="dr-sec">
        <span class="lbl">${t("drawer.pool.where")}</span>
        <div class="newsitem ${r.dShare>0?"up":"down"}"><div class="bar"></div><div>
          <h4>${t("drawer.pool.waiver")}</h4><p>${t("drawer.pool.waiverText", {n: r.own, what: r.own<35?t("drawer.pool.claimable"):t("drawer.pool.gone")})}</p></div></div>
        <div class="newsitem ${r.luck>0?"down":"up"}"><div class="bar"></div><div>
          <h4>${t("drawer.pool.trade")}</h4><p>${r.luck>2?t("drawer.pool.tradeSell"):t("drawer.pool.tradeBuy")}</p></div></div>
        <div class="newsitem"><div class="bar"></div><div>
          <h4>${t("drawer.pool.prop")}</h4><p>${t("drawer.pool.propText")} ${r.dShare>3?t("drawer.pool.propCheck"):t("drawer.pool.propSkip")}</p></div></div>
      </div>
    </div>
    <div class="dr-foot">
      <button class="btn ghost">${t("drawer.action.watchNews")}</button>
      <button class="btn">${t("drawer.action.addBuilder")}</button>
    </div>`;
  showDrawer(d);
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
  const f = [...e.currentTarget.querySelectorAll("button:not([hidden]), a[href], [tabindex]:not([tabindex='-1'])")];
  if (!f.length) return;
  if (e.shiftKey && document.activeElement === f[0]){ e.preventDefault(); f[f.length-1].focus(); }
  else if (!e.shiftKey && document.activeElement === f[f.length-1]){ e.preventDefault(); f[0].focus(); }
});


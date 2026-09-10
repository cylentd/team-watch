/* ---------------------------- drawer ---------------------------- */
function findPlayer(teamKey, i){
  const ordered = TEAMS[teamKey].roster.filter(p=>p.start)
    .concat(TEAMS[teamKey].roster.filter(p=>!p.start && p.slot!=="OUT"))
    .concat(TEAMS[teamKey].roster.filter(p=>p.slot==="OUT"));
  return ordered[i];
}

function openDrawer(teamKey, i){
  const p = findPlayer(teamKey, i);
  if (!p) return;
  const d = document.getElementById("drawer");
  const bars = Array.from({length:12}, (_,k)=>{
    const h = 20 + ((k*37)%70);
    const me = k === 4;
    return `<i class="${me?"me":""}" style="height:${me?86:h}%"></i>`;
  }).join("");
  const news = (p.news ? [
    {t:"up", h:`${p.n.split(" ").slice(-1)} takes first-team reps through camp`, p:"Beat writer notes a full practice load and a bump in the two-minute package.", m:"BEAT REPORT · 4H AGO"},
    {t:"flat", h:"Coach non-committal on week 1 workload", p:"Split backfield language from the podium, no depth-chart change announced.", m:"PRESSER · 1D AGO"},
    {t:"down", h:"Snap projection trimmed in the latest model run", p:"Rotation risk keeps the floor low until the first live game.", m:"MODEL · 2D AGO"},
  ] : []);

  d.innerHTML = `
    <div class="dr-head">
      <button class="dr-close" aria-label="${t("common.action.close")}">✕</button>
      <div class="dr-id">
        ${headHTML(p)}
        <div>
          <h3>${esc(p.n)}</h3>
          <div class="lbl">${esc(p.pos)} · ${esc(p.team)} · ${esc(TEAMS[teamKey].plat)} ${esc(p.slot)}</div>
        </div>
      </div>
      ${p.note ? `<div style="margin-top:14px;padding:10px 12px;border:1px solid rgba(255,90,82,.3);background:rgba(255,90,82,.06);font-size:12px;color:var(--ink-2);line-height:1.5">${esc(p.note)}</div>` : ""}
    </div>
    <div class="dr-body">
      <div class="dr-sec">
        <span class="lbl">${t("drawer.player.form")}</span>
        ${p.trend ? sparkHTML(p.trend, 386, 88).replace('class="spark"','class="spark bigspark"') :
          `<div class="state-empty" style="height:88px"><div><b>—</b><span>${t("drawer.player.noGames")}</span></div></div>`}
        <div class="axis"><span>${t("drawer.axis.wk6")}</span><span>${t("drawer.axis.wk4")}</span><span>${t("drawer.axis.wk2")}</span><span>${t("drawer.axis.now")}</span></div>
      </div>
      <div class="dr-sec">
        <span class="lbl">${t("drawer.player.why")}</span>
        <div class="why">
          <div class="why-row"><div class="t">${t("drawer.why.snapShare")}</div><div class="why-bar"><i style="width:78%"></i></div></div>
          <div class="why-row"><div class="t">${t("drawer.why.targetShare")}</div><div class="why-bar"><i style="width:64%"></i></div></div>
          <div class="why-row"><div class="t">${t("drawer.why.redzone")}</div><div class="why-bar neg"><i style="width:31%"></i></div></div>
        </div>
      </div>
      <div class="dr-sec">
        <span class="lbl">${t("drawer.player.news", {n: p.news||0})}</span>
        ${news.length ? news.slice(0, Math.min(3, p.news)).map(x=>`
          <div class="newsitem ${x.t}"><div class="bar"></div>
            <div><h4>${esc(x.h)}</h4><p>${esc(x.p)}</p><div class="meta">${esc(x.m)}</div></div></div>`).join("")
          : `<div class="state-empty" style="min-height:76px"><div><b>0</b><span>${t("drawer.player.noNews")}</span></div></div>`}
      </div>
      <div class="dr-sec">
        <span class="lbl">${t("drawer.player.league", {pos: esc(p.pos)})}</span>
        <div class="leaguebars">${bars}</div>
        <div class="leaguecap"><span>${t("drawer.player.managers")}</span><span>${t("drawer.player.you", {rank: p.rank[0]?p.pos+p.rank[0]:t("drawer.player.unranked")})}</span></div>
      </div>
    </div>
    <div class="dr-foot">
      <button class="btn ghost">${t("drawer.action.watchNews")}</button>
      <button class="btn">${t("drawer.action.suggest")}</button>
    </div>`;
  d.classList.add("on"); d.setAttribute("aria-hidden","false");
  document.getElementById("scrim").classList.add("on");
  d.querySelector(".dr-close").addEventListener("click", closeDrawer);
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
        ${HEADS[r.slug] ? `<img src="${HEADS[r.slug]}" alt="">` : `<div class="fallback">${esc(initials(r.n))}</div>`}
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
  d.classList.add("on"); d.setAttribute("aria-hidden","false");
  document.getElementById("scrim").classList.add("on");
  d.querySelector(".dr-close").addEventListener("click", closeDrawer);
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
  d.classList.add("on"); d.setAttribute("aria-hidden","false");
  document.getElementById("scrim").classList.add("on");
  d.querySelector(".dr-close").addEventListener("click", closeDrawer);
}

function closeDrawer(){
  document.getElementById("drawer").classList.remove("on");
  document.getElementById("drawer").setAttribute("aria-hidden","true");
  document.getElementById("scrim").classList.remove("on");
}
document.getElementById("scrim").addEventListener("click", closeDrawer);
document.addEventListener("keydown", e=>{ if(e.key==="Escape") closeDrawer(); });


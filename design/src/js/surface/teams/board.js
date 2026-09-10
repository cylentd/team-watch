function rowHTML(p, i, teamKey){
  const cls = p.slot === "OUT" ? "out" : p.start ? "start" : "bench";
  const st = p.statusText || p.status;
  const tag = st ? `<span class="tag ${p.status==="OUT"?"o":"q"}">${esc(st)}</span>` : "";
  const dual = p.dual ? `<span class="tag dual">${t("teams.row.dual")}</span>` : "";
  const badge = p.status ? `<span class="badge ${p.status==="OUT"?"o":"q"}">${p.status==="OUT"?"!":"Q"}</span>` : "";
  const rd = 40+i*32;
  return `<div class="row ${cls}" style="animation-delay:${rd}ms;--rowdelay:${rd}ms" data-team="${teamKey}" data-i="${i}" role="button" tabindex="0">
    <div class="slot"><span>${esc(p.slot)}</span></div>
    <div class="head">${headHTML(p)}${badge}</div>
    <div class="nm">
      <div class="nm-1"><b>${esc(p.n)}</b>${tag}${dual}</div>
      <div class="nm-2">
        <span class="slotm">${esc(p.slot)}</span>
        <span><em class="posx" style="font-style:normal">${esc(p.pos)} · </em>${esc(p.team)}</span>
        <span class="sep"></span>
        <span>${t("teams.row.week")} ${p.pos==="DST"?"vs":"@"} ${["HOU","LV","NYJ","ARI","CHI"][i%5]}</span>
      </div>
    </div>
    <div class="trend">${sparkHTML(p.trend,128,34)}${deltaHTML(p.d)}</div>
    <div class="rk">${rankHTML(p)}</div>
    <div class="news">${p.news
      ? `<span class="newstag ${p.hot?"hot":""}">${NEWS_ICON}<b>${p.news}</b></span>`
      : `<span class="newstag empty">–</span>`}</div>
  </div>`;
}

function boardHTML(team){
  const groups = [
    [t("teams.group.starters"), team.roster.filter(p=>p.start)],
    [t("teams.group.bench"),    team.roster.filter(p=>!p.start && p.slot!=="OUT")],
    [t("teams.group.out"), team.roster.filter(p=>p.slot==="OUT")],
  ].filter(g=>g[1].length);
  let n = 0;
  return groups.map(([label, list], gi) => `
    <div class="rule">
      <h2>${label}</h2><span class="count">${String(list.length).padStart(2,"0")}</span>
      <span class="hair"></span>
    </div>
    ${gi===0 ? `<div class="colhead">
      <span class="ch ch-trend">${t("teams.col.trend")}</span>
      <span class="ch ch-rank">${t("teams.col.rank")}</span>
      <span class="ch ch-news">${t("teams.col.news")}</span>
    </div>` : ""}
    <div class="board">${list.map(p=>rowHTML(p, n++, team.key)).join("")}</div>
  `).join("");
}

function signalsHTML(team){
  const up = team.roster.filter(p=>p.d>1.5).length;
  const dn = team.roster.filter(p=>p.d<-1.5).length;
  return `<div class="signals">
    <div class="sig up"><div class="lbl">${t("teams.sig.upLabel")}</div><div class="sig-val">${up}</div><div class="sig-sub">${t("teams.sig.upSub", {n: team.roster.length})}</div></div>
    <div class="sig down"><div class="lbl">${t("teams.sig.downLabel")}</div><div class="sig-val">${dn}</div><div class="sig-sub">${t("teams.sig.downSub")}</div></div>
    <div class="sig empty"><div class="lbl">${t("teams.sig.rankLabel")}</div><div class="sig-val">—</div><div class="sig-sub">${t("teams.sig.rankSub")}</div></div>
  </div>`;
}


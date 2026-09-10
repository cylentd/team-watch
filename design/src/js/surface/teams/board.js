function rowHTML(p, i, teamKey){
  const cls = p.slot === "OUT" ? "out" : p.start ? "start" : "bench";
  const st = p.statusText || p.status;
  const tag = st ? `<span class="tag ${p.status==="OUT"?"o":"q"}">${esc(st)}</span>` : "";
  const dual = p.dual ? `<span class="tag dual">2 leagues</span>` : "";
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
        <span>wk1 ${p.pos==="DST"?"vs":"@"} ${["HOU","LV","NYJ","ARI","CHI"][i%5]}</span>
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
    ["Starters", team.roster.filter(p=>p.start)],
    ["Bench",    team.roster.filter(p=>!p.start && p.slot!=="OUT")],
    ["Out / exempt", team.roster.filter(p=>p.slot==="OUT")],
  ].filter(g=>g[1].length);
  let n = 0;
  return groups.map(([label, list], gi) => `
    <div class="rule">
      <h2>${label}</h2><span class="count">${String(list.length).padStart(2,"0")}</span>
      <span class="hair"></span>
    </div>
    ${gi===0 ? `<div class="colhead">
      <span class="ch ch-trend">Trend</span>
      <span class="ch ch-rank">Rank</span>
      <span class="ch ch-news">News</span>
    </div>` : ""}
    <div class="board">${list.map(p=>rowHTML(p, n++, team.key)).join("")}</div>
  `).join("");
}

function signalsHTML(team){
  const up = team.roster.filter(p=>p.d>1.5).length;
  const dn = team.roster.filter(p=>p.d<-1.5).length;
  return `<div class="signals">
    <div class="sig up"><div class="lbl">Up trend</div><div class="sig-val">${up}</div><div class="sig-sub">OF ${team.roster.length} ROSTERED</div></div>
    <div class="sig down"><div class="lbl">Down trend</div><div class="sig-val">${dn}</div><div class="sig-sub">2 ARE STARTERS</div></div>
    <div class="sig empty"><div class="lbl">League rank</div><div class="sig-val">—</div><div class="sig-sub">NO GAMES YET</div></div>
  </div>`;
}


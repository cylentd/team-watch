/* The roster row at every width since 2026-09-25: who, which way, one number (the storyboard's
   rule, design/DESIGN.md "Phone layout"). A head with its Q/O badge, the name over "RB · BAL @ DAL
   16th", the snap-share line, the projection pill. Desktop used to add a slot box, a matchup column,
   a market delta, a rank and a news count -- five more things per row, most of them a dash until
   the books priced the week. The rank and the market are the profile's; news is the brief's. */
function rowHTML(p, i, teamKey){
  const cls = p.slot === "OUT" ? "out" : p.start ? "start" : "bench";
  const badge = p.status ? `<span class="badge ${p.status==="OUT"?"o":"q"}">${p.status==="OUT"?"!":"Q"}</span>` : "";
  const rd = 40+i*32;
  const snap = p.trend ? t("teams.row.snapTip", {n: Math.round(p.trend[p.trend.length-1])}) : t("teams.row.snapNone");
  return `<div class="row ${cls}" style="animation-delay:${rd}ms;--rowdelay:${rd}ms" data-team="${teamKey}" data-i="${i}" role="button" tabindex="0">
    <div class="head">${headHTML(p)}${badge}</div>
    <div class="nm">
      <div class="nm-1"><b>${esc(p.n)}</b></div>
      <div class="nm-2">
        <span>${esc(p.pos)} · ${esc(p.team)}</span>
        ${matchupMetaHTML(profileFor(p))}
      </div>
    </div>
    <div class="trend" title="${snap}">${sparkHTML(p.trend,80,30)}</div>
    ${projPillHTML(p)}
  </div>`;
}

function boardHTML(team){
  const groups = [
    [t("teams.group.starters"), team.roster.filter(p=>p.start)],
    [t("teams.group.bench"),    team.roster.filter(p=>!p.start && p.slot!=="OUT")],
    [t("teams.group.out"), team.roster.filter(p=>p.slot==="OUT")],
  ].filter(g=>g[1].length);
  let n = 0;
  return groups.map(([label, list]) => `
    <div class="rule">
      <h2>${label}</h2><span class="count">${String(list.length).padStart(2,"0")}</span>
      <span class="hair"></span>
    </div>
    <div class="board">${list.map(p=>rowHTML(p, n++, team.key)).join("")}</div>
  `).join("");
}

/* The roster as a lineup sheet (2026-09-25). A starter row is slot, head, name over
   "RB · BAL @ DAL", the snap-share line, and the projection with an arrow that says which way the
   line went. The number itself stays neutral: the old filled pill repeated the line's colour, so
   six red boxes on eight starters read as an alarm. Bench and out rows drop the slot and the line;
   on a desktop the bench sits beside the starters. The rank and the market are the profile's;
   news is the checklist's. */
function rowHTML(p, i, teamKey){
  const cls = (p.slot === "OUT" ? "out" : p.start ? "start" : "bench") + injClass(p);
  // The injury badge on the head: ! out, D doubtful, Q questionable; the reason is its tooltip.
  const inj = injFor(p);
  const badge = inj ? `<span class="badge ${{OUT: "o", D: "d", Q: "q"}[inj.s]}" title="${injLabel(inj)}">${{OUT: "!", D: "D", Q: "Q"}[inj.s]}</span>` : "";
  const rd = 40+i*24;
  const snap = p.trend ? t("teams.row.snapTip", {n: Math.round(p.trend[p.trend.length-1])}) : t("teams.row.snapNone");
  return `<div class="row ${cls}" style="animation-delay:${rd}ms;--rowdelay:${rd}ms" data-team="${teamKey}" data-i="${i}" role="button" tabindex="0">
    ${p.start ? `<span class="slot">${esc(slotLabel(p.slot))}</span>` : ""}
    <div class="head">${headHTML(p)}${badge}</div>
    <div class="nm">
      <div class="nm-1"><b><span class="nm-full">${esc(p.n)}</span><span class="nm-ini">${esc(nameInitial(p.n))}</span></b></div>
      <div class="nm-2">
        <span>${esc(p.pos)}<span class="nm-tm"> · ${esc(p.team)}</span></span>
        ${matchupMetaHTML(profileFor(p))}
      </div>
    </div>
    ${p.start ? `<div class="trend" title="${snap}">${sparkHTML(p.trend,72,24)}</div>` : ""}
    ${projNumHTML(p)}
  </div>`;
}

/* A lineup slot as the sheet prints it: RB1 and FLX2 lose their number, every flex spelling is FLX,
   and ESPN's D/ST is DST. */
function slotLabel(slot){
  const s = String(slot || "").replace(/\d+$/, "");
  return {FLEX: "FLX", "D/ST": "DST", DEF: "DST"}[s] || s;
}

function boardHTML(team){
  const groups = [
    ["start", t("teams.group.starters"), team.roster.filter(p=>p.start)],
    ["bench", t("teams.group.bench"),    team.roster.filter(p=>!p.start && p.slot!=="OUT")],
    ["out",   t("teams.group.out"),      team.roster.filter(p=>p.slot==="OUT")],
  ].filter(g=>g[2].length);
  let n = 0;
  const group = ([key, label, list]) => `
    <div class="rule">
      <h2>${label}</h2><span class="count">${String(list.length).padStart(2,"0")}</span>
      <span class="hair"></span>
    </div>
    <div class="board ${key === "start" ? "" : "two"}">${list.map(p=>rowHTML(p, n++, team.key)).join("")}</div>`;
  const [start, ...rest] = groups[0] && groups[0][0] === "start" ? groups : [null, ...groups];
  return `${injWarnHTML(team)}<div class="sheet">
    ${start ? `<section class="sheet-col">${group(start)}</section>` : ""}
    ${rest.length ? `<section class="sheet-col">${rest.map(group).join("")}</section>` : ""}
  </div>`;
}

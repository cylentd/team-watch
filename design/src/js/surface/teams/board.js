/* The roster as a lineup sheet (2026-09-25). A starter row is slot, head, name over
   the matchup line ("@ DAL 16th" over the kickoff, mlRowHTML), his fantasy points week by week as bars
   (pbRowHTML; usage numbers were here until 2026-10-07), and the projection with his TD chance under it.
   The number stays neutral: an old filled pill coloured by trend made six red boxes on eight
   starters read as an alarm. Bench and out rows drop the slot;
   on a desktop the bench sits beside the starters. The rank and the market are the profile's;
   news is the checklist's. */
function rowHTML(p, i, teamKey){
  const cls = (p.slot === "OUT" ? "out" : p.start ? "start" : "bench") + injClass(p);
  // The injury badge on the head: ! out, D doubtful, Q questionable; the reason is its tooltip.
  const inj = injFor(p);
  const badge = inj ? `<span class="badge ${{OUT: "o", D: "d", Q: "q"}[inj.s]}" title="${injLabel(inj)}">${{OUT: "!", D: "D", Q: "Q"}[inj.s]}</span>` : "";
  // A lime ring and a count on a head whose player has official clips; a tap opens the clip sheet (clipsheet.js).
  const nc = clipsOf(p.slug).length;
  const ring = nc ? `<span class="clipn" aria-hidden="true">${nc}</span>` : "";
  const rd = 40+i*24;
  return `<div class="row pbr ${cls}" data-testid="roster-row" style="animation-delay:${rd}ms;--rowdelay:${rd}ms" data-team="${teamKey}" data-i="${i}" role="button" tabindex="0">
    ${p.start ? `<span class="slot" data-testid="roster-row-slot">${esc(slotLabel(p.slot))}</span>` : ""}
    <div class="head" data-testid="roster-row-head"${clipRingHTML(p)}>${headHTML(p)}${badge}${ring}</div>
    <div class="nm" data-testid="roster-row-name">
      <div class="nm-1"><b><span class="nm-full">${esc(p.n)}</span><span class="nm-ini">${esc(nameInitial(p.n))}</span></b></div>
      <div class="nm-2" data-testid="roster-row-matchup">${mlRowHTML(p)}</div>
    </div>
    <div class="rbars">${pbRowHTML(p)}</div>
    ${projNumHTML(p)}
  </div>`;
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
  return `<div class="sheet">
    ${start ? `<section class="sheet-col" data-testid="roster-sheet-col">${group(start)}</section>` : ""}
    ${rest.length ? `<section class="sheet-col" data-testid="roster-sheet-col">${rest.map(group).join("")}</section>` : ""}
  </div>`;
}

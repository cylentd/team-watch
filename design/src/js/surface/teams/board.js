/* The roster as a lineup sheet (2026-09-25). A starter row is slot, head, name over
   "RB · BAL @ DAL 16th", his usage (rowUsage), and the projection with his TD chance under it.
   The number stays neutral: an old filled pill coloured by trend made six red boxes on eight
   starters read as an alarm. Bench and out rows drop the slot and the usage;
   on a desktop the bench sits beside the starters. The rank and the market are the profile's;
   news is the checklist's. */
function rowHTML(p, i, teamKey){
  const cls = (p.slot === "OUT" ? "out" : p.start ? "start" : "bench") + injClass(p);
  // The injury badge on the head: ! out, D doubtful, Q questionable; the reason is its tooltip.
  const inj = injFor(p);
  const badge = inj ? `<span class="badge ${{OUT: "o", D: "d", Q: "q"}[inj.s]}" title="${injLabel(inj)}">${{OUT: "!", D: "D", Q: "Q"}[inj.s]}</span>` : "";
  const rd = 40+i*24;
  const use = rowUsage(p);
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
    ${p.start ? `<div class="ruse">${use ? `<b>${use.v}</b><small>${use.what}</small>` : ""}</div>` : ""}
    ${projNumHTML(p)}
  </div>`;
}

/* How much his offense uses him, the one number per position that best predicts fantasy points
   after the projection (2026-09-25; it replaced the snap-share line, which says he was on the
   field, not that the ball went to him): target share for a receiver or tight end, touches for a
   back, dropbacks for a quarterback. Averaged over the weeks he has played, from the Grid's rows. */
function rowUsage(p){
  const rows = (typeof USAGE !== "undefined" && USAGE.rows || []).filter(r => r.slug === p.slug);
  const avg = f => { const v = rows.map(r => f(r.v)).filter(x => typeof x === "number"); return v.length ? v.reduce((a, x) => a + x, 0) / v.length : null; };
  let n = null, what = "";
  if (p.pos === "WR" || p.pos === "TE"){ n = avg(v => v.tgt_pct); what = t("teams.row.targets"); if (n !== null) n = `${Math.round(n)}%`; }
  else if (p.pos === "RB"){ n = avg(v => typeof v.car === "number" || typeof v.tgt === "number" ? (v.car || 0) + (v.tgt || 0) : null); what = t("teams.row.touches"); if (n !== null) n = Math.round(n); }
  else if (p.pos === "QB"){ n = avg(v => v.dropbacks); what = t("teams.row.dropbacks"); if (n !== null) n = Math.round(n); }
  return n === null ? null : {v: n, what};
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

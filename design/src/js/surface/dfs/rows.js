/* Best-value marker: the single highest points-per-$1000 player at each position (min 2 players
   at that position, else "best" is meaningless). Computed once per pool, not per row, so every
   row at a position agrees on who holds it. */
function dfsValueLeaders(pool, cap){
  const byPos = {};
  pool.filter(p => p.status !== "OUT" && p.status !== "IR").forEach(p=>(byPos[p.pos] ||= []).push(p));
  const leaders = new Set();
  Object.values(byPos).forEach(list=>{
    if (list.length < 2) return;
    const best = list.reduce((a,b) => (b.proj/b.sal) > (a.proj/a.sal) ? b : a);
    leaders.add(best.n);
  });
  return leaders;
}
/* A player's `team` field, checked against `game` ("AWAY@HOME") when the pool carries one — the
   Yahoo export has shipped rows where `team` doesn't match either side of the player's own game
   (seen 2026-09-09: a bench RB tagged with a teammate's team while `game` had him elsewhere). A
   row that fails this check is real (right salary/proj/status) but its team is not trustworthy
   enough to group into a same-team handcuff read, so it's left out of that grouping entirely. */
function teamVerified(p){
  if (!p.game) return true;
  const at = p.game.indexOf("@");
  if (at < 0) return true;
  return p.team === p.game.slice(0, at) || p.team === p.game.slice(at + 1);
}
/* Handcuff marker: same team, same position, the starter (highest salary) carries an OUT/IR
   status — the cheapest teammate left at that spot is the one who inherits the workload, and the
   field usually hasn't priced that in yet. Keyed by name -> the starter's name it backs up. */
function dfsHandcuffs(pool){
  const byTeamPos = {};
  pool.forEach(p=>{
    if (!teamVerified(p)) return;
    (byTeamPos[`${p.team}|${p.pos}`] ||= []).push(p);
  });
  const handcuffs = new Map();
  Object.values(byTeamPos).forEach(list=>{
    if (list.length < 2) return;
    const starter = list.reduce((a,b) => b.sal > a.sal ? b : a);
    if (starter.status !== "OUT" && starter.status !== "IR") return;
    const backups = list.filter(p => p !== starter && p.status !== "OUT" && p.status !== "IR").sort((a,b)=>a.sal-b.sal);
    if (!backups.length) return;
    handcuffs.set(backups[0].n, starter.n);
  });
  return handcuffs;
}
function dfsPoolRow(p, i, cap, valueLeaders, handcuffs, poolIndex, activeEligible){
  const value = (p.proj / (p.sal/(cap/50))).toFixed(2);
  const status = INJ[p.status] || (p.status ? p.status : null);
  const handcuffFor = handcuffs.get(p.n);
  const tags = (status ? ` <span class="tag ${status==="Q"?"q":"o"}">${esc(status)}</span>` : "")
    + (p.src === "yahoo" ? ` <span class="tag t-bk" title="${t("dfs.tag.yahooTitle", {pos: esc(p.pos)})}">${t("dfs.tag.yahoo")}</span>` : "")
    + (p.src === "line" ? ` <span class="tag t-bk" title="${t("dfs.tag.lineTitle")}">${t("dfs.tag.line")}</span>` : "")
    + (valueLeaders.has(p.n) ? ` <span class="tag t-cbup" title="${t("dfs.tag.valueTitle", {pos: esc(p.pos)})}">${t("dfs.tag.value")}</span>` : "")
    + (handcuffFor ? ` <span class="tag t-role" title="${t("dfs.tag.handcuffTitle", {name: esc(handcuffFor), pos: esc(p.pos)})}">${t("dfs.tag.handcuff")}</span>` : "");
  // activeEligible: null when no lineup slot is being filled (a tap auto-picks the first open
  // slot this player fits); true/false once a slot IS selected, so a wrong-position player reads
  // as disabled rather than silently doing nothing when tapped.
  const addLabel = activeEligible === false ? t("dfs.row.wrongPos") : activeEligible === true ? t("dfs.row.swapIn") : t("dfs.row.add");
  return `<div class="prow dfsrow ${p.mine?"mine":""} ${activeEligible===false?"ineligible":""}" style="animation-delay:${40+i*18}ms" data-dfs="${poolIndex}" role="button" tabindex="0">
    <div>${HEADS[p.slug] ? `<img class="pool-head" src="${HEADS[p.slug]}" alt="">`
        : `<div class="pool-head" style="display:grid;place-items:center;font-family:var(--mono);font-size:11px;color:var(--ink-3)">${esc(p.abbr||initials(p.n))}</div>`}</div>
    <div class="pname"><b>${esc(p.n)}${tags}</b><span>${esc(p.pos)} · ${esc(p.team)}</span></div>
    <div class="pnum">$${p.sal.toLocaleString()}</div>
    <div class="pnum">${p.proj.toFixed(1)}</div>
    <div class="pnum ${value>2.6?"pos":""}">${value}</div>
    <div class="pnum" style="color:var(--ink-2)">${typeof p.own === "number" ? `${p.own}%` : "—"}</div>
    <div><button class="chip ${activeEligible===true?"go":""}" tabindex="-1">${addLabel}</button></div>
  </div>`;
}


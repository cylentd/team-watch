/* One row above the lineups (STYLE.md audit, 2026-09-25): the strategy, which changes what the
   three lineups are, and a chip naming the site and cap that opens the rest. It replaces a hero
   line, a site switch and a two-box strategy toggle, three rows that put the first lineup at
   294px on a phone. */
function dfsBarHTML(){
  const site = dfsSite();
  const row = `<div class="setrow">
    <button class="chip" data-topmode="greedy" aria-pressed="${TOP_MODE==="greedy"}">${t("dfs.top.greedy")}</button>
    <button class="chip" data-topmode="contrarian" aria-pressed="${TOP_MODE==="contrarian"}">${t("dfs.top.contrarian")}</button>
    <button type="button" class="chip setchip" data-dfspanel aria-expanded="${DFS_PANEL}" aria-label="${t("dfs.set.label")}">${t("dfs.set.chip", {site: site.label, cap: site.cap.toLocaleString()})}<span class="caret" aria-hidden="true"></span></button>
  </div>`;
  if (!DFS_PANEL) return row;
  return row + `<div class="setpanel">
    <span class="lbl">${t("dfs.book.label")}</span>
    <button class="chip" data-dfssite="yahoo" aria-pressed="${DFS_SITE==="yahoo"}">${t("dfs.book.yahoo")}</button>
    <button class="chip" data-dfssite="dk" aria-pressed="${DFS_SITE==="dk"}">${t("dfs.book.dk")}</button>
    <span style="flex:1"></span>
    ${explainButtonHTML("dfs")}
    <span class="lbl">${t("dfs.top.greedy")}: ${t("dfs.top.greedySub")} · ${t("dfs.top.contrarian")}: ${t("dfs.top.contrarianSub")}</span>
  </div>`;
}
function wireDfsBar(v){
  v.querySelectorAll("[data-dfspanel]").forEach(b => b.addEventListener("click", () => { DFS_PANEL = !DFS_PANEL; render(); }));
}

function dfsSurfaceHTML(){
  const site = dfsSite();
  return `<div class="wrap">
    ${dfsBarHTML()}
    ${topLineupsHTML()}
    <div class="build" style="margin-top:24px">
      <div class="side">${dfsHTML()}</div>
      <div>
        ${marketHead("dfs")}
        <div class="filters dfs-pos">
          <span class="lbl">${t("dfs.filter.position")}</span>
          ${["ALL","QB","RB","WR","TE","DST"].map(p=>`<button class="chip" data-dpos="${p}" aria-pressed="${DFS_POS===p}">${p}</button>`).join("")}
          <span style="flex:1"></span>
          <span class="lbl">${t("dfs.filter.valueNote", {n: (site.cap/50).toLocaleString()})}</span>
        </div>
        ${(() => {
          const cap = site.cap;
          const valueLeaders = dfsValueLeaders(site.pool, cap);
          const handcuffs = dfsHandcuffs(site.pool);
          const all = site.pool.filter(p => DFS_POS==="ALL"||p.pos===DFS_POS);
          const pages = Math.max(1, Math.ceil(all.length / DFS_PAGE_SIZE));
          const page = Math.min(DFS_PAGE, pages);
          const rows = all.slice((page-1)*DFS_PAGE_SIZE, page*DFS_PAGE_SIZE);
          const pager = `<div class="filters" style="margin-top:8px">
            <span class="lbl">${t("dfs.pager.players", {n: all.length, s: all.length===1?"":"s"})}</span>
            <span style="flex:1"></span>
            <button class="chip" data-dfspage="prev" ${page<=1?"disabled":""}>${t("common.pager.prev")}</button>
            <span class="lbl">${t("common.pager.page", {page: page, pages: pages})}</span>
            <button class="chip" data-dfspage="next" ${page>=pages?"disabled":""}>${t("common.pager.next")}</button>
          </div>`;
          const pickSlot = ACTIVE_SLOT !== null ? site.lineup[ACTIVE_SLOT] : null;
          return `${pager}
          <div class="ptable dfstable">
            <div class="phead"><div></div><div>${t("dfs.table.player")}</div><div>${t("dfs.table.salary")}</div><div>${t("dfs.table.proj")}</div>
              <div>${t("dfs.table.value")}</div><div>${t("dfs.table.own")}</div><div></div></div>
            ${rows.length ? rows.map((p,i)=>dfsPoolRow(p,i,cap,valueLeaders,handcuffs,
                site.pool.indexOf(p), pickSlot ? slotEligible(pickSlot.slot, p.pos) : null)).join("")
              : `<div class="state-empty" style="margin:20px 0;min-height:110px"><div><b>0</b><span>${t("dfs.empty.noPlayers")}</span></div></div>`}
          </div>`;
        })()}
      </div>
    </div>
  </div>`;
}


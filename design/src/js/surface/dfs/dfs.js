function dfsSurfaceHTML(){
  const site = dfsSite();
  return `<section class="hero">
    <div class="numghost">${site.lineup.filter(d=>d.n).length}</div>
    <div class="wrap hero-in">
      <div>
        <div class="hero-eyebrow" style="--tint:var(--lime)">
          <span class="league-mark"></span><span class="lbl">${site.label} · $${site.cap.toLocaleString()} cap</span>
        </div>
        <h1>Build the<br><em>lineup</em></h1>
        <div class="modes-sub" style="margin-top:14px">
          <span class="lbl" style="margin-right:8px">Book</span>
          <button class="mode-sub" data-dfssite="yahoo" aria-pressed="${DFS_SITE==="yahoo"}">Yahoo</button>
          <button class="mode-sub" data-dfssite="dk" aria-pressed="${DFS_SITE==="dk"}">DraftKings</button>
        </div>
      </div>
      <div><div class="signals">
        <div class="sig up"><div class="lbl">Slots filled</div><div class="sig-val">${site.lineup.filter(d=>d.n).length}</div><div class="sig-sub">OF ${site.lineup.length}</div></div>
        <div class="sig"><div class="lbl">Pool</div><div class="sig-val">${site.pool.length}</div><div class="sig-sub">PLAYERS</div></div>
      </div></div>
    </div>
  </section>
  <div class="wrap">
    ${explainHTML("dfs")}
    ${topLineupsHTML()}
    <div class="build" style="margin-top:24px">
      <div class="side">${dfsHTML()}</div>
      <div>
        ${marketHead("dfs")}
        <div class="filters">
          <span class="lbl">Position</span>
          ${["ALL","QB","RB","WR","TE","DST"].map(p=>`<button class="chip" data-dpos="${p}" aria-pressed="${DFS_POS===p}">${p}</button>`).join("")}
          <span style="flex:1"></span>
          <span class="lbl">Value = points per $${(site.cap/50).toLocaleString()}</span>
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
            <span class="lbl">${all.length} player${all.length===1?"":"s"}</span>
            <span style="flex:1"></span>
            <button class="chip" data-dfspage="prev" ${page<=1?"disabled":""}>‹ Prev</button>
            <span class="lbl">Page ${page} of ${pages}</span>
            <button class="chip" data-dfspage="next" ${page>=pages?"disabled":""}>Next ›</button>
          </div>`;
          const pickSlot = ACTIVE_SLOT !== null ? site.lineup[ACTIVE_SLOT] : null;
          return `${pager}
          <div class="ptable dfstable">
            <div class="phead"><div></div><div>Player</div><div>Salary</div><div>Proj</div>
              <div>Value</div><div>Own</div><div></div></div>
            ${rows.length ? rows.map((p,i)=>dfsPoolRow(p,i,cap,valueLeaders,handcuffs,
                site.pool.indexOf(p), pickSlot ? slotEligible(pickSlot.slot, p.pos) : null)).join("")
              : `<div class="state-empty" style="margin:20px 0;min-height:110px"><div><b>0</b><span>NO PLAYERS AT THAT POSITION</span></div></div>`}
          </div>`;
        })()}
      </div>
    </div>
  </div>`;
}


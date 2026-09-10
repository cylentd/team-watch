function poolRow(r, i){
  const sgn = v => (v>0?"+":"") + v.toFixed(1);
  const cls = v => v>0.5 ? "pos" : v<-0.5 ? "neg" : "";
  // `i` is the display rank (1-based, correct across pages); the drawer needs the full POOL
  // array's index, which diverges from `i` the moment a position filter is active.
  return `<div class="prow ${r.mine?"mine":""}" style="animation-delay:${60+i*26}ms" data-pool="${POOL.indexOf(r)}" role="button" tabindex="0">
    <div class="pnum" style="color:var(--ink-3)">${String(i+1).padStart(2,"0")}</div>
    <div>${HEADS[r.slug] ? `<img class="pool-head" src="${HEADS[r.slug]}" alt="">` : `<div class="pool-head" style="display:grid;place-items:center;font-family:var(--mono);font-size:11px;color:var(--ink-3)">${esc(initials(r.n))}</div>`}</div>
    <div class="pname"><b>${esc(r.n)}</b><span>${esc(r.pos)} · ${esc(r.team)}</span></div>
    <div class="pnum">${r.snaps}</div>
    <div class="pnum ${cls(r.dSnap)}">${sgn(r.dSnap)}</div>
    <div class="pnum">${r.share.toFixed(1)}</div>
    <div class="pnum ${cls(r.dShare)}">${sgn(r.dShare)}</div>
    <div><span class="vchip ${VCLASS[r.v]}">${esc(r.v.toUpperCase())}</span></div>
    <div class="pnum" style="color:var(--ink-2)">${r.own}%</div>
  </div>`;
}

function poolHTML(){
  const rows = POOL_FILTER === "ALL" ? POOL : POOL.filter(r=>r.pos===POOL_FILTER);
  const rising = POOL.filter(r=>r.dShare>3).length;
  const falling = POOL.filter(r=>r.dShare<-3).length;
  return `<section class="hero">
    <div class="numghost">${POOL.length}</div>
    <div class="wrap hero-in">
      <div>
        <div class="hero-eyebrow" style="--tint:var(--lime)">
          <span class="league-mark"></span><span class="lbl">${t("pool.hero.eyebrow")}</span>
        </div>
        <h1>${t("pool.hero.title")}</h1>
        <div class="hero-meta">
          <span class="pill">${t("pool.hero.pillUsage")}</span>
          <span class="pill">${t("pool.hero.pillRostered")}</span>
        </div>
      </div>
      <div><div class="signals">
        <div class="sig up"><div class="lbl">${t("pool.sig.risingLabel")}</div><div class="sig-val">${rising}</div><div class="sig-sub">${t("pool.sig.risingSub")}</div></div>
        <div class="sig down"><div class="lbl">${t("pool.sig.fallingLabel")}</div><div class="sig-val">${falling}</div><div class="sig-sub">${t("pool.sig.fallingSub")}</div></div>
        <div class="sig empty"><div class="lbl">${t("pool.sig.trackedLabel")}</div><div class="sig-val">—</div><div class="sig-sub">${t("pool.sig.trackedSub")}</div></div>
      </div></div>
    </div>
  </section>
  ${tickerHTML()}
  <div class="wrap">
    ${scatterHTML(rows)}
    <div class="filters">
      <span class="lbl">${t("pool.filter.position")}</span>
      ${["ALL","QB","RB","WR","TE"].map(p=>`<button class="chip" data-pos="${p}" aria-pressed="${POOL_FILTER===p}">${p}</button>`).join("")}
      <span style="flex:1"></span>
      <span class="lbl">${t("pool.filter.sorted")}</span>
    </div>
    ${(() => {
      const pages = Math.max(1, Math.ceil(rows.length / POOL_PAGE_SIZE));
      const page = Math.min(POOL_PAGE, pages);
      const pageRows = rows.slice((page-1)*POOL_PAGE_SIZE, page*POOL_PAGE_SIZE);
      const pager = `<div class="filters" style="margin-top:8px">
        <span class="lbl">${t("pool.pager.players", {n: rows.length, s: rows.length===1?"":"s"})}</span>
        <span style="flex:1"></span>
        <button class="chip" data-poolpage="prev" ${page<=1?"disabled":""}>${t("common.pager.prev")}</button>
        <span class="lbl">${t("common.pager.page", {page: page, pages: pages})}</span>
        <button class="chip" data-poolpage="next" ${page>=pages?"disabled":""}>${t("common.pager.next")}</button>
      </div>`;
      return `${pager}
      <div class="ptable">
        <div class="phead">
          <div>#</div><div></div><div>${t("pool.table.player")}</div><div>${t("pool.table.snaps")}</div><div>${t("pool.table.dSnaps")}</div>
          <div>${t("pool.table.share")}</div><div>${t("pool.table.dShare")}</div><div>${t("pool.table.verdict")}</div><div>${t("pool.table.rostered")}</div>
        </div>
        ${pageRows.length ? pageRows.map((r,i)=>poolRow(r, (page-1)*POOL_PAGE_SIZE + i)).join("")
          : `<div class="state-empty" style="margin:26px 0;min-height:120px"><div><b>0</b><span>${t("pool.empty.noPlayers")}</span></div></div>`}
      </div>`;
    })()}
  </div>`;
}


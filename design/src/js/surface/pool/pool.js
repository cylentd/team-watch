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
          <span class="league-mark"></span><span class="lbl">Every player who logged a snap · week 1</span>
        </div>
        <h1>Who is<br>getting<br><em>the ball</em></h1>
        <div class="hero-meta">
          <span class="pill">Ranked on usage, not points</span>
          <span class="pill">Rostered % from both leagues</span>
        </div>
      </div>
      <div><div class="signals">
        <div class="sig up"><div class="lbl">Role growing</div><div class="sig-val">${rising}</div><div class="sig-sub">SHARE +3 OR MORE</div></div>
        <div class="sig down"><div class="lbl">Role shrinking</div><div class="sig-val">${falling}</div><div class="sig-sub">SHARE -3 OR MORE</div></div>
        <div class="sig empty"><div class="lbl">Tracked</div><div class="sig-val">—</div><div class="sig-sub">FILLS AFTER WEEK 1</div></div>
      </div></div>
    </div>
  </section>
  ${tickerHTML()}
  <div class="wrap">
    ${scatterHTML(rows)}
    <div class="filters">
      <span class="lbl">Position</span>
      ${["ALL","QB","RB","WR","TE"].map(p=>`<button class="chip" data-pos="${p}" aria-pressed="${POOL_FILTER===p}">${p}</button>`).join("")}
      <span style="flex:1"></span>
      <span class="lbl">Sorted by share change</span>
    </div>
    ${(() => {
      const pages = Math.max(1, Math.ceil(rows.length / POOL_PAGE_SIZE));
      const page = Math.min(POOL_PAGE, pages);
      const pageRows = rows.slice((page-1)*POOL_PAGE_SIZE, page*POOL_PAGE_SIZE);
      const pager = `<div class="filters" style="margin-top:8px">
        <span class="lbl">${rows.length} player${rows.length===1?"":"s"}</span>
        <span style="flex:1"></span>
        <button class="chip" data-poolpage="prev" ${page<=1?"disabled":""}>‹ Prev</button>
        <span class="lbl">Page ${page} of ${pages}</span>
        <button class="chip" data-poolpage="next" ${page>=pages?"disabled":""}>Next ›</button>
      </div>`;
      return `${pager}
      <div class="ptable">
        <div class="phead">
          <div>#</div><div></div><div>Player</div><div>Snaps</div><div>Δ snaps</div>
          <div>Share</div><div>Δ share</div><div>Verdict</div><div>Rostered</div>
        </div>
        ${pageRows.length ? pageRows.map((r,i)=>poolRow(r, (page-1)*POOL_PAGE_SIZE + i)).join("")
          : `<div class="state-empty" style="margin:26px 0;min-height:120px"><div><b>0</b><span>NO PLAYERS AT THIS POSITION</span></div></div>`}
      </div>`;
    })()}
  </div>`;
}


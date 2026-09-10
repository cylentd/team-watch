function dfsHTML(){
  const site = dfsSite();
  const DFS = site.lineup, CAP = site.cap;
  const filled = DFS.filter(d=>d.n);
  const spent = filled.reduce((a,d)=>a+d.sal,0);
  const proj  = filled.reduce((a,d)=>a+d.proj,0);
  const hasOwn = filled.some(d=>typeof d.own === "number");
  const own   = filled.reduce((a,d)=>a+(d.own||0),0);
  const pct   = Math.min(100, (spent/CAP)*100);
  const open = DFS.filter(d=>!d.n).length;
  const picking = ACTIVE_SLOT !== null && ACTIVE_SLOT < DFS.length;
  return `<div class="slip">
    <div class="sliphead"><span class="lbl">My ${esc(site.label)} lineup</span>
      <span class="pill">${filled.length}/${DFS.length} filled</span></div>
    ${picking || PICK_ERR ? `<div class="pickbar">
        <span>${picking ? `Picking <b>${esc(DFS[ACTIVE_SLOT].slot)}</b> — tap a player below` : ""}${PICK_ERR ? `${picking ? ", or " : ""}<span class="err">${esc(PICK_ERR)}</span>` : ""}</span>
        ${picking ? `<button class="chip" data-cancelpick="1">Cancel</button>` : ""}
      </div>` : ""}
    ${DFS.map((d,i) => d.n ? `
      <div class="lslot ${ACTIVE_SLOT===i?"active":""}" data-slot="${i}" role="button" tabindex="0">
        <span class="slottag">${esc(d.slot)}</span>
        ${HEADS[d.slug] ? `<img src="${HEADS[d.slug]}" alt="">` : `<div class="fallback">${esc(d.abbr || initials(d.n))}</div>`}
        <div style="min-width:0">
          <div class="sn">${esc(d.n)}</div>
          <div class="sm">${d.proj.toFixed(1)} PROJ${typeof d.own === "number" ? ` · ${d.own}% OWN` : ""}</div>
        </div>
        <div class="lsal">$${d.sal.toLocaleString()}</div>
        <button class="lremove" data-remove="${i}" title="Remove" tabindex="-1">✕</button>
      </div>` : `
      <div class="lslot vacant ${ACTIVE_SLOT===i?"active":""}" data-slot="${i}" role="button" tabindex="0">
        <span class="slottag">${esc(d.slot)}</span>
        <div class="vhint">${ACTIVE_SLOT===i ? "Tap a player below" : "Pick from the pool"} · $${(CAP-spent).toLocaleString()} left</div>
      </div>`).join("")}
    <div class="payout">
      <div class="salbar ${spent>CAP?"over":""}"><i style="--w:${pct.toFixed(1)}%"></i></div>
      <div class="payrow" style="margin-top:12px"><span>SPENT</span><b>$${spent.toLocaleString()}</b></div>
      <div class="payrow"><span>LEFT FOR ${open} SLOT${open===1?"":"S"}</span>
        <b style="color:var(--lime)">$${(CAP-spent).toLocaleString()}</b></div>
      <div class="payrow"><span>PROJECTED</span><b>${proj.toFixed(1)}</b></div>
      ${hasOwn ? `<div class="payrow"><span>SUMMED OWNERSHIP</span><b>${own}%</b></div>` : ""}
      <button class="btn" style="width:100%;margin-top:14px">Export lineup</button>
    </div>
  </div>`;
}

function lineupCard(l, i, cap){
  const pct = Math.min(100, (l.spent/cap)*100);
  return `<div class="lineupcard ${i===0?"best":""}">
    <div class="sliphead"><span class="lbl">${i===0?"★ Best · ":""}Lineup ${i+1}</span>
      <span class="pill">${l.proj.toFixed(1)} PROJ · ~${Math.round(l.chalk*100)}% PROJ OWN</span></div>
    ${l.players.map(d => `
      <div class="lslot" style="padding:8px 15px">
        <span class="slottag">${esc(d.slot)}</span>
        ${HEADS[d.slug] ? `<img src="${HEADS[d.slug]}" alt="">` : `<div class="fallback">${esc(d.abbr || initials(d.n))}</div>`}
        <div style="min-width:0"><div class="sn">${esc(d.n)}</div>
          <div class="sm">${esc(d.pos)} · ${esc(d.team)} · ${d.proj.toFixed(1)} PROJ</div></div>
        <div class="lsal">$${d.sal.toLocaleString()}</div>
      </div>`).join("")}
    <div class="payout" style="padding-top:10px">
      <div class="payrow"><span>SPENT</span><b>$${l.spent.toLocaleString()} <span style="color:var(--ink-3)">of $${cap.toLocaleString()}</span></b></div>
      <div class="salbar"><i style="--w:${pct.toFixed(1)}%"></i></div>
      <button class="btn" style="width:100%;margin-top:12px" data-loadlineup="${i}">Load into my lineup</button>
    </div>
  </div>`;
}


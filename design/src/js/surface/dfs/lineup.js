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
    <div class="sliphead"><span class="lbl">${t("dfs.lineup.title", {site: esc(site.label)})}</span>
      <span class="pill">${t("dfs.lineup.filled", {n: filled.length, of: DFS.length})}</span></div>
    ${picking || PICK_ERR ? `<div class="pickbar">
        <span>${picking ? t("dfs.lineup.picking", {slot: esc(DFS[ACTIVE_SLOT].slot)}) : ""}${PICK_ERR ? `${picking ? t("dfs.lineup.orSep") : ""}<span class="err">${esc(PICK_ERR)}</span>` : ""}</span>
        ${picking ? `<button class="chip" data-cancelpick="1">${t("dfs.lineup.cancel")}</button>` : ""}
      </div>` : ""}
    ${DFS.map((d,i) => d.n ? `
      <div class="lslot ${ACTIVE_SLOT===i?"active":""}" data-slot="${i}" role="button" tabindex="0">
        <span class="slottag">${esc(d.slot)}</span>
        ${HEADS[d.slug] ? `<img src="${HEADS[d.slug]}" alt="">` : `<div class="fallback">${esc(d.abbr || initials(d.n))}</div>`}
        <div style="min-width:0">
          <div class="sn">${esc(d.n)}</div>
          <div class="sm">${t("dfs.lineup.proj", {v: d.proj.toFixed(1)})}${typeof d.own === "number" ? ` · ${t("dfs.lineup.own", {n: d.own})}` : ""}</div>
        </div>
        <div class="lsal">$${d.sal.toLocaleString()}</div>
        <button class="lremove" data-remove="${i}" title="${t("common.action.remove")}" tabindex="-1">✕</button>
      </div>` : `
      <div class="lslot vacant ${ACTIVE_SLOT===i?"active":""}" data-slot="${i}" role="button" tabindex="0">
        <span class="slottag">${esc(d.slot)}</span>
        <div class="vhint">${ACTIVE_SLOT===i ? t("dfs.lineup.tapBelow") : t("dfs.lineup.pickFromPool")} · ${t("dfs.lineup.left", {n: (CAP-spent).toLocaleString()})}</div>
      </div>`).join("")}
    <div class="payout">
      <div class="salbar ${spent>CAP?"over":""}"><i style="--w:${pct.toFixed(1)}%"></i></div>
      <div class="payrow" style="margin-top:12px"><span>${t("dfs.lineup.spent")}</span><b>$${spent.toLocaleString()}</b></div>
      <div class="payrow"><span>${t("dfs.lineup.leftFor", {n: open, s: open===1?"":"S"})}</span>
        <b style="color:var(--lime)">$${(CAP-spent).toLocaleString()}</b></div>
      <div class="payrow"><span>${t("dfs.lineup.projected")}</span><b>${proj.toFixed(1)}</b></div>
      ${hasOwn ? `<div class="payrow"><span>${t("dfs.lineup.summedOwn")}</span><b>${own}%</b></div>` : ""}
      <button class="btn" style="width:100%;margin-top:14px">${t("dfs.lineup.export")}</button>
    </div>
  </div>`;
}

function lineupCard(l, i, cap){
  const pct = Math.min(100, (l.spent/cap)*100);
  return `<div class="lineupcard ${i===0?"best":""}">
    <div class="sliphead"><span class="lbl">${i===0 ? t("dfs.card.titleBest", {n: i+1}) : t("dfs.card.title", {n: i+1})}</span>
      <span class="pill">${t("dfs.card.stats", {proj: l.proj.toFixed(1), own: Math.round(l.chalk*100)})}</span></div>
    ${l.players.map(d => `
      <div class="lslot" style="padding:8px 15px">
        <span class="slottag">${esc(d.slot)}</span>
        ${HEADS[d.slug] ? `<img src="${HEADS[d.slug]}" alt="">` : `<div class="fallback">${esc(d.abbr || initials(d.n))}</div>`}
        <div style="min-width:0"><div class="sn">${esc(d.n)}</div>
          <div class="sm">${esc(d.pos)} · ${esc(d.team)} · ${t("dfs.lineup.proj", {v: d.proj.toFixed(1)})}</div></div>
        <div class="lsal">$${d.sal.toLocaleString()}</div>
      </div>`).join("")}
    <div class="payout" style="padding-top:10px">
      <div class="payrow"><span>${t("dfs.lineup.spent")}</span><b>$${l.spent.toLocaleString()} <span style="color:var(--ink-3)">${t("dfs.card.of", {n: cap.toLocaleString()})}</span></b></div>
      <div class="salbar"><i style="--w:${pct.toFixed(1)}%"></i></div>
      <button class="btn" style="width:100%;margin-top:12px" data-loadlineup="${i}">${t("dfs.card.load")}</button>
    </div>
  </div>`;
}


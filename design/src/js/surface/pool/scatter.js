function scatterHTML(rows){
  // A taller, narrower geometry on mobile -- close to 1:1 with the actual container width --
  // means the SVG's own viewBox units render near their real size instead of scaled down to
  // ~35% (1080-wide box in a 362px container), which is what forced the horizontal swipe.
  // Per-dot name labels are dropped there (16 of them at that scale collide anyway, and the
  // ranked table right below already names every player); tap still opens the same drawer.
  const mobile = typeof window !== "undefined" && window.matchMedia && window.matchMedia("(max-width:760px)").matches;
  const W = mobile ? 380 : 1080, H = mobile ? 460 : 400, PX = mobile ? 30 : 54, PY = mobile ? 22 : 34;
  const xs = rows.map(r=>r.dShare), ys = rows.map(r=>r.luck);
  const xm = Math.max(14, ...xs.map(Math.abs)) * 1.15;
  const ym = Math.max(8,  ...ys.map(Math.abs)) * 1.2;
  const X = v => PX + ((v + xm) / (2*xm)) * (W - PX*2);
  const Y = v => H - PY - ((v + ym) / (2*ym)) * (H - PY*2);
  const cx = X(0), cy = Y(0);

  const quads = [
    [W-PX-8, PY+16,  "end",   t("pool.quad.confirmed")],
    [PX+8,   PY+16,  "start", t("pool.quad.sellHigh")],
    [W-PX-8, H-PY-10,"end",   t("pool.quad.buyLow")],
    [PX+8,   H-PY-10,"start", t("pool.quad.fading")],
  ].map(([x,y,a,t]) => `<text class="qname" x="${x}" y="${y}" text-anchor="${a}">${t}</text>`).join("");

  // Labels sit to the right of their dot; when that would collide with one already
  // placed, the label flips above instead. Cheap, and it keeps every name readable.
  const placed = [];
  const dots = rows.map((r,i) => {
    const rad = (mobile ? 3.5 : 4) + Math.min(mobile ? 5 : 6, r.snaps/14);
    const px = X(r.dShare), py = Y(r.luck);
    let lx = px + rad + 5, ly = py + 3.5, anchor = "start";
    const hits = () => placed.some(p => Math.abs(p.x-lx) < 64 && Math.abs(p.y-ly) < 11);
    if (hits()){ ly = py - rad - 6; lx = px; anchor = "middle"; }
    if (hits()){ ly = py + rad + 13; lx = px; anchor = "middle"; }
    if (hits()){ lx = px - rad - 5; ly = py + 3.5; anchor = "end"; }
    placed.push({x:lx, y:ly});
    // The drawer opens by index into the full POOL array, not this (possibly filtered) rows
    // array -- POOL.indexOf, not the map index, or a position filter opens the wrong player.
    return `<g class="dotg" data-i="${POOL.indexOf(r)}">
      <circle class="dot" cx="${px.toFixed(1)}" cy="${py.toFixed(1)}" r="${rad.toFixed(1)}"
        fill="${VDOT[r.v]}" fill-opacity=".8" stroke="${r.mine?"var(--lime)":"none"}" stroke-width="${r.mine?2:0}">
        <title>${t("pool.scatter.dotTip", {name: esc(r.n), usage: `${r.dShare>0?"+":""}${r.dShare}`, luck: `${r.luck>0?"+":""}${r.luck}`})}</title>
      </circle>
      ${mobile ? "" : `<text class="dotlab" x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" text-anchor="${anchor}">${esc(r.n.split(" ").slice(-1)[0])}</text>`}
    </g>`;
  }).join("");

  return `<div class="quadwrap">
    <div class="quadhead">
      <div><span class="lbl">${t("pool.scatter.heading")}</span>
        <div style="margin-top:6px;font-size:12.5px;color:var(--ink-2)">${t("pool.scatter.sub")}${mobile ? ` ${t("pool.scatter.tapHint")}` : ""}</div></div>
      <span class="pill">${t("pool.scatter.count", {n: rows.length})}</span>
    </div>
    <div class="quadscroll" data-railkey="pool-scatter">
      <svg class="quad ${mobile ? "quad-compact" : ""}" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">
        <line class="qgrid" x1="${PX}" y1="${PY}" x2="${W-PX}" y2="${PY}"/>
        <line class="qgrid" x1="${PX}" y1="${H-PY}" x2="${W-PX}" y2="${H-PY}"/>
        <line class="axis-line" x1="${cx}" y1="${PY}" x2="${cx}" y2="${H-PY}"/>
        <line class="axis-line" x1="${PX}" y1="${cy}" x2="${W-PX}" y2="${cy}"/>
        ${quads}
        <text class="qtick" x="${W-PX}" y="${cy+16}" text-anchor="end">${t("pool.axis.usagePos")}</text>
        <text class="qtick" x="${PX}" y="${cy+16}">${t("pool.axis.usageNeg")}</text>
        <text class="qtick" x="${cx+8}" y="${PY+12}">${t("pool.axis.luckPos")}</text>
        <text class="qtick" x="${cx+8}" y="${H-PY-6}">${t("pool.axis.luckNeg")}</text>
        ${dots}
      </svg>
    </div>
    <div class="quadkey">
      <span><i style="background:var(--up)"></i>${t("pool.key.confirmed")}</span>
      <span><i style="background:var(--lime)"></i>${t("pool.key.buyLow")}</span>
      <span><i style="background:var(--down)"></i>${t("pool.key.sell")}</span>
      <span><i style="background:var(--ink-3)"></i>${t("pool.key.hold")}</span>
      <span><i style="background:none;border:2px solid var(--lime)"></i>${t("pool.key.mine")}</span>
    </div>
  </div>`;
}


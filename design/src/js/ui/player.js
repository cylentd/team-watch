function headHTML(p, cls){
  if (p.pos === "DST") return `<div class="dst">${esc(p.team)}</div>`;
  const src = HEADS[p.slug];
  if (!src) return `<div class="fallback">${esc(initials(p.n))}</div>`;
  return `<img src="${src}" alt="" loading="lazy">`;
}

function sparkHTML(v, w, h){
  if (!v) {
    return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
      <line x1="1" y1="${h/2}" x2="${w-1}" y2="${h/2}" stroke="var(--line-2)" stroke-width="1.4" stroke-dasharray="3 4"/>
    </svg>`;
  }
  const min = Math.min(...v), max = Math.max(...v), span = (max-min)||1;
  const x = i => 1 + i*((w-2)/(v.length-1));
  const y = k => (h-3) - ((k-min)/span)*(h-6);
  const pts = v.map((k,i)=>`${x(i).toFixed(1)},${y(k).toFixed(1)}`);
  const col = v[v.length-1] > v[0] ? "var(--up)" : v[v.length-1] < v[0] ? "var(--down)" : "var(--ink-3)";
  const area = `M ${pts[0]} L ${pts.slice(1).join(" L ")} L ${x(v.length-1).toFixed(1)},${h} L ${x(0).toFixed(1)},${h} Z`;
  return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
    <g class="reveal">
      <path class="area" d="${area}" fill="${col}"/>
      <path class="line" d="M ${pts[0]} L ${pts.slice(1).join(" L ")}" stroke="${col}"/>
      <circle class="cap" cx="${x(v.length-1).toFixed(1)}" cy="${y(v[v.length-1]).toFixed(1)}" r="2.6" fill="${col}"/>
    </g>
  </svg>`;
}

function deltaHTML(d){
  if (d === null || d === undefined) return `<span class="delta new">No data</span>`;
  const k = d > 1.5 ? "up" : d < -1.5 ? "down" : "flat";
  const g = k === "up" ? "▲" : k === "down" ? "▼" : "—";
  return `<span class="delta ${k}">${g} ${d>0?"+":""}${d.toFixed(1)}%</span>`;
}

function rankHTML(p){
  const [r, of, mv, pct] = p.rank;
  if (r === null) return `<div class="rk-1"><b style="color:var(--ink-3)">—</b><small>unranked</small></div>
    <div class="pctbar"></div>`;
  const mk = mv > 0 ? "up" : mv < 0 ? "down" : "flat";
  const mg = mv > 0 ? `▲${mv}` : mv < 0 ? `▼${Math.abs(mv)}` : "—";
  return `<div class="rk-1"><b>${p.pos}${r}</b><small>of ${of}</small><span class="mv ${mk}">${mg}</span></div>
    <div class="pctbar"><i style="--w:${Math.round(pct*100)}%"></i></div>`;
}


/* Headshot or initials, the fragment every card starts with. `label` overrides the initials
   (a lineup slot shows the position abbreviation instead). headHTML below is the roster-board
   variant: it knows about DST and lazy-loads, so the two stay separate on purpose. */
function avatarHTML(p, label){
  const text = label || initials(p.n);
  return HEADS[p.slug] ? headImgHTML(HEADS[p.slug], text) : `<div class="fallback">${esc(text)}</div>`;
}
function headHTML(p, cls){
  if (p.pos === "DST") return `<div class="dst">${esc(p.team)}</div>`;
  const src = HEADS[p.slug];
  if (!src) return `<div class="fallback">${esc(initials(p.n))}</div>`;
  return headImgHTML(src, initials(p.n));
}

/* Heads are files beside the page (heads/<slug>.webp), so one can fail to load: a published
   Artifact without the folder, a deploy mid-flight. The failed image becomes the same initials
   block a player with no head gets, never a broken-image glyph. */
function headImgHTML(src, text){
  return `<img src="${src}" alt="" loading="lazy" data-i="${esc(text)}" onerror="headFail(this)">`;
}
function headFail(img){
  const d = document.createElement("div");
  d.className = "fallback";
  d.textContent = img.dataset.i;
  img.replaceWith(d);
}

/* `ref`, when given, draws a dashed rule across the chart at that value -- the profile card's
   elite bar, so a week above the bar is visibly above it. It is only drawn when it falls inside
   the series' own range: a bar off the top of the chart would either flatten every point to
   make room for it, or sit on the frame pretending to be the last gridline. */
function sparkHTML(v, w, h, ref){
  if (!v || v.length < 2) {   // one point has no shape to draw; same flat line as no data
    return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
      <line x1="1" y1="${h/2}" x2="${w-1}" y2="${h/2}" stroke="var(--line-2)" stroke-width="1.4" stroke-dasharray="3 4"/>
    </svg>`;
  }
  const min = Math.min(...v), max = Math.max(...v), span = (max-min)||1;
  const x = i => 1 + i*((w-2)/(v.length-1));
  const y = k => (h-3) - ((k-min)/span)*(h-6);
  const pts = v.map((k,i)=>`${x(i).toFixed(1)},${y(k).toFixed(1)}`);
  const col = {up: "var(--up)", down: "var(--down)", flat: "var(--ink-3)"}[trendDir(v)];
  const area = `M ${pts[0]} L ${pts.slice(1).join(" L ")} L ${x(v.length-1).toFixed(1)},${h} L ${x(0).toFixed(1)},${h} Z`;
  const bar = ref !== null && ref !== undefined && ref > min && ref < max
    ? `<line class="ref" x1="1" y1="${y(ref).toFixed(1)}" x2="${w-1}" y2="${y(ref).toFixed(1)}"/>` : "";
  return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${bar}
    <g class="reveal">
      <path class="area" d="${area}" fill="${col}"/>
      <path class="line" d="M ${pts[0]} L ${pts.slice(1).join(" L ")}" stroke="${col}"/>
      <circle class="cap" cx="${x(v.length-1).toFixed(1)}" cy="${y(v[v.length-1]).toFixed(1)}" r="2.6" fill="${col}"/>
    </g>
  </svg>`;
}

/* Which way a series moved, first week to last. The sparkline's colour and the roster pill's
   colour both come from here, so the line and the number beside it never disagree. */
function trendDir(v){
  if (!v || v.length < 2) return "flat";
  return v[v.length-1] > v[0] ? "up" : v[v.length-1] < v[0] ? "down" : "flat";
}

/* This week's projected points from ff-jarvis's player projections, or null. */
function projFor(p){
  if (typeof LIVE_PROJECTIONS === "undefined" || !LIVE_PROJECTIONS) return null;
  const proj = LIVE_PROJECTIONS.players[p.slug];
  return proj && typeof proj.pts === "number" ? proj.pts : null;
}

/* The roster row's one number at every width: projected points in the ink colour, with a small
   arrow in the trend line's colour (2026-09-25). The pill used to be filled with that colour, which
   said the line's direction a second time at full volume. No projection prints a dash, never a zero;
   a flat or missing line draws no arrow. */
function projNumHTML(p){
  const pts = projFor(p);
  if (pts === null) return `<div class="rproj none">—</div>`;
  const dir = trendDir(p.trend);
  const arrow = dir === "flat" ? "" : `<svg class="rp-ar ${dir}" viewBox="0 0 8 8" aria-hidden="true"><path d="${dir === "up" ? "M4 1 7.5 7h-7z" : "M4 7 .5 1h7z"}"/></svg>`;
  return `<div class="rproj">${pts.toFixed(1)}${arrow}</div>`;
}


/* Headshot or initials, the fragment every card starts with. `label` overrides the initials
   (a lineup slot shows the position abbreviation instead). headHTML below is the roster-board
   variant: it knows about DST and lazy-loads, so the two stay separate on purpose. */
function avatarHTML(p, label){
  const text = label || initials(p.n);
  return HEADS[p.slug] ? headImgHTML(HEADS[p.slug], text, p.slug) : `<div class="fallback">${esc(text)}</div>`;
}
function headHTML(p, cls){
  if (p.pos === "DST") return `<div class="dst">${esc(p.team)}</div>`;
  const src = HEADS[p.slug];
  if (!src) return `<div class="fallback">${esc(initials(p.n))}</div>`;
  return headImgHTML(src, initials(p.n), p.slug);
}

/* Every size ff-jarvis cut for a player, as a srcset: 96px (HEADS), 256px (HEADS_LG), 512px
   (HEADS_XL, since 2026-09-25). The browser takes the smallest one sharp at the size the photo is
   drawn on that screen, so a row never loads the big file and the pack stage never blurs. */
function headSrcset(slug){
  const maps = [[typeof HEADS !== "undefined" ? HEADS : null, 96],
                [typeof HEADS_LG !== "undefined" ? HEADS_LG : null, 256],
                [typeof HEADS_XL !== "undefined" ? HEADS_XL : null, 512]];
  return maps.filter(([m]) => m && m[slug]).map(([m, w]) => `${m[slug]} ${w}w`).join(", ");
}

/* Heads are files beside the page (heads/<slug>.webp), so one can fail to load: a published
   Artifact without the folder, a deploy mid-flight. The failed image becomes the same initials
   block a player with no head gets, never a broken-image glyph. `px` is the width it is drawn at,
   for a browser that cannot measure it itself (sizes="auto" is Chrome 126+, Firefox 150+ and
   Safari 27+, as of 2026-09-25); the others take the first size that fits. */
function headImgHTML(src, text, slug, px){
  const set = slug ? headSrcset(slug) : "";
  const pick = set ? ` srcset="${set}" sizes="auto, ${px || 48}px"` : "";
  return `<img src="${src}"${pick} alt="" loading="lazy" decoding="async" data-i="${esc(text)}" onerror="headFail(this)">`;
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
/* Sleeper's code when he is not playing this week (design/projections.py OUT_INJURY), or null. */
function projOut(p){
  if (typeof LIVE_PROJECTIONS === "undefined" || !LIVE_PROJECTIONS) return null;
  const proj = LIVE_PROJECTIONS.players[p.slug];
  return proj && proj.out ? proj.out : null;
}

/* Is he hurt this week: {s: "OUT" / "D" / "Q", code, note} from Sleeper (LIVE_INJURY,
   design/injury.py), or null. A player Sleeper has no row for falls back to his league's own flag,
   which says only out or not. */
function injFor(p){
  const r = typeof LIVE_INJURY !== "undefined" && LIVE_INJURY && p.slug ? LIVE_INJURY.players[p.slug] : null;
  if (r) return r;
  return p.status ? {s: p.status === "OUT" ? "OUT" : "Q", code: p.status, note: null} : null;
}
/* Will he likely sit: out, or doubtful. The lineup warning's test. */
const injSits = p => { const r = injFor(p); return !!r && (r.s === "OUT" || r.s === "D"); };
/* "OUT · Personal", "DOUBTFUL · Hamstring": the level and Sleeper's reason. */
const INJ_WORD = {OUT: () => t("teams.inj.out"), D: () => t("teams.inj.doubtful"), Q: () => t("teams.inj.questionable")};
const injLabel = r => r.note ? t("teams.inj.withNote", {s: INJ_WORD[r.s](), note: esc(r.note)}) : INJ_WORD[r.s]();

/* His chance to score this week, from the props model's P(score): the one model number grading
   found honest (ff-jarvis METHODOLOGY 12.31). Null without a TD line. */
function tdChanceFor(p){
  if (typeof PROPS === "undefined" || !p.slug) return null;
  const r = PROPS.find(x => x.slug === p.slug && x.mkt === "TD");
  return r && typeof r.model === "number" ? Math.round(r.model) : null;
}
const TD_SHOW = 25, TD_HOT = 45;

/* The roster row's one number at every width: projected points in the ink colour, and under it
   his TD chance from 25% up, lime from 45% (2026-09-25; it replaced an arrow that repeated the
   snap-share line, which left the row). No projection prints a dash, never a zero. */
function projNumHTML(p){
  const pts = projFor(p);
  if (pts === null) return projOut(p)
    ? `<div class="rproj none out" title="${t("teams.card.outTip", {code: esc(projOut(p))})}">${t("teams.card.out")}</div>`
    : `<div class="rproj none">—</div>`;
  const td = tdChanceFor(p);
  const chip = td !== null && td >= TD_SHOW
    ? `<small class="rtd ${td >= TD_HOT ? "hot" : ""}" title="${t("teams.row.tdTip", {n: td})}">${t("teams.row.td", {n: td})}</small>` : "";
  return `<div class="rproj">${pts.toFixed(1)}${chip}</div>`;
}


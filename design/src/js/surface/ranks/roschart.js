/* ------------------------------------------------------------------
   REST OF SEASON: THE TWO CHARTS (2026-10-06). Both draw rank by week, never points (data/ros.js says why), as inline SVG
   whose colours are classes (css/surface/ranks/ros.css for Ranks, css/surface/profile/ros.css for the profile).

   The bump chart (Ranks > Rest of season): the top 10 at a position, rank 1 at the top, one line per player, the top
   three in the position's colour and the rest quiet, each name at its line's right end and tappable. The profile's line
   chart: one player, his own axis. A rank past the axis is a hollow dot on the bottom edge; one week is dots only.
------------------------------------------------------------------ */
const rosWeekText = n => t("ros.chart.week", {n});

/* The week names along the foot, one per week the chart has. */
const rosWeeksSVG = (weeks, box) => weeks.map(w =>
  `<text data-testid="ros-week" x="${rosX(w, weeks, box).toFixed(1)}" y="${box.h - 4}" text-anchor="middle">${rosWeekText(w)}</text>`).join("");

/* A line's points: its polyline (two weeks or more) and a dot at each week, hollow past the axis. */
function rosPathSVG(points, weeks, axis, box, cls){
  const xy = points.map(p => `${rosX(p.week, weeks, box).toFixed(1)},${rosY(p.shown, axis, box).toFixed(1)}`);
  const line = points.length > 1 ? `<polyline class="${cls}-pl" points="${xy.join(" ")}"/>` : "";
  const r = cls === "ros" ? 2.6 : 3.4;
  return line + points.map((p, i) => {
    const [cx, cy] = xy[i].split(",");
    return `<circle class="${cls}-dot${p.over ? " over" : ""}" cx="${cx}" cy="${cy}" r="${r}"/>`;
  }).join("");
}

/* The top 10 at one position. A line's name sits at the right of the plot, level with his rank this week. */
function rosBumpHTML(chart, pos, box){
  const axis = chart.axis, last = chart.weeks[chart.weeks.length - 1];
  const ticks = Array.from({length: axis}, (_, i) => i + 1).filter(k => k % 2)
    .map(k => `<text data-testid="ros-axis" x="4" y="${(rosY(k, axis, box) + 3.5).toFixed(1)}">${k}</text>`).join("");
  const gap = (box.h - box.t - box.b) / (axis - 1);
  const lines = chart.lines.map(ln => {
    const end = ln.points[ln.points.length - 1], y = rosY(end.shown, axis, box), x = rosX(last, chart.weeks, box) + 8;
    return `<g class="ros-ln${ln.lead ? " lead" : ""}" data-testid="ros-line" data-slug="${esc(ln.slug)}">${rosPathSVG(ln.points, chart.weeks, axis, box, "ros")}
      <g class="ros-lbl" data-testid="ros-label" data-rosopen="${esc(ln.slug)}" role="button" tabindex="0" aria-label="${esc(ln.n)}">
        <rect class="ros-hit" x="${(x - 4).toFixed(1)}" y="${(y - gap / 2).toFixed(1)}" width="${box.r - 4}" height="${gap.toFixed(1)}"/>
        <text x="${x.toFixed(1)}" y="${(y + 4).toFixed(1)}">${esc(nameInitial(ln.n))}</text></g></g>`;
  }).join("");
  return `<svg viewBox="0 0 ${box.w} ${box.h}" role="img" aria-label="${t("ros.chart.label", {pos: esc(pos)})}">${ticks}${rosWeeksSVG(chart.weeks, box)}${lines}</svg>`;
}

/* One player's rank by week: gridlines at #1 and his worst week, so the line fills the box. */
function rosLineHTML(hist, pos, box){
  const weeks = hist.map(h => h[0]), axis = rosAxis(hist.map(h => h[1]));
  const points = hist.map(([week, rank]) => ({week, rank, over: false, shown: rank}));
  const grid = [1, axis].map(k => {
    const y = rosY(k, axis, box).toFixed(1);
    return `<line class="pfr-grid" x1="${box.l}" x2="${box.w - box.r}" y1="${y}" y2="${y}"/><text data-testid="ros-axis" x="4" y="${(+y + 3.5).toFixed(1)}">#${k}</text>`;
  }).join("");
  return `<svg class="pfr-pchart" data-testid="profile-ros-chart" viewBox="0 0 ${box.w} ${box.h}" role="img" aria-label="${t("ros.profile.chart", {pos: esc(pos)})}">${grid}${rosWeeksSVG(weeks, box)}${rosPathSVG(points, weeks, axis, box, "pfr")}</svg>`;
}

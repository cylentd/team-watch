/* Rest of season, as rows and a chart (2026-10-06). Pure and DOM-free, so Node tests it (tests/test_js_ros.py).
   The numbers are ff-jarvis's (LIVE_ROS via design/ros.py, METHODOLOGY 12.97): each QB/RB/WR/TE's expected points from
   the week still to play through week 17, his rank at the position, and that rank by week. This only picks the
   reader's scoring, lists a position in the file's rank order, and places ranks on a chart. The page computes no points.

   The chart is rank, never points: ROS points fall every week for everyone as games run out, so a points line would
   slope down for the whole league and say nothing. A rank past the axis (a back who was 18th last week) sits on the
   chart's bottom edge as a hollow dot, so no line leaves the box. A single week of history draws dots, not lines. */
const ROS_POSITIONS = ["QB", "RB", "WR", "TE"];
const ROS_LINES = 10;     // the bump chart's lines: the top 10 at the position, the top 3 in the position's colour
const ROS_LEAD = 3;
const ROS_AXIS = 12;      // the bump chart's rows: ranks 1 to 12
const ROS_MIN_AXIS = 6;   // the profile's chart never reads shorter than this

const rosBlock = () => {
  const b = typeof LIVE_ROS !== "undefined" && LIVE_ROS;
  return b && (b.players || []).length ? b : null;
};

/* The reader's scoring: ESPN's numbers for a team picked in the ESPN league, half-PPR for everyone else (no team,
   Yahoo, AYO). ESPN's are the file's own scaling and not backtested, so a file that lacks them for anyone stays half-PPR. */
function rosScoring(picked, focus, block){
  const has = block && block.players.every(p => p.espn && p.espn.rank != null);
  return picked && focus === "espn" && has ? "espn" : "half";
}

/* One player on one scoring: the numbers the row, the chart and the profile read. */
function rosRow(p, scoring, span, poWeeks){
  const s = scoring === "espn" ? p.espn : p;
  if (span === "po") {   // the fantasy playoff weeks (2026-10-07): half-PPR only, no history, no FantasyPros (it ranks the whole rest of season)
    return {slug: p.slug, n: p.n, pos: p.pos, team: p.team, rank: p.po_rank ?? null, pts: p.po_pts ?? null, pg: p.ros_pg,
      games: p.po_games ?? null, of: poWeeks, hist: [], fp: null};
  }
  return {slug: p.slug, n: p.n, pos: p.pos, team: p.team, rank: s.rank, pts: s.ros_pts, pg: s.ros_pg,
    games: p.games_left, of: p.sched_left, hist: s.hist,
    fp: scoring === "espn" ? null : p.fp || null};   // FantasyPros is half-PPR, and its gap is against our half-PPR rank
}

/* A position's list in the file's rank order; a tie (never in a real file) goes to the points, then the name. `span` "po" is
   the playoff weeks: a player with no playoff rank sits last with blanks. */
function rosRows(block, pos, scoring, span){
  if (!block || !ROS_POSITIONS.includes(pos)) return [];
  const weeks = (block.po_weeks || []).length, big = Number.MAX_SAFE_INTEGER, at = r => r.rank == null ? big : r.rank;
  return block.players.filter(p => p.pos === pos).map(p => rosRow(p, scoring, span, weeks))
    .sort((a, b) => at(a) - at(b) || (b.pts ?? 0) - (a.pts ?? 0) || a.n.localeCompare(b.n));
}

/* The Playoffs toggle exists only when the file names the playoff weeks. */
function rosHasPlayoffs(block){
  return !!(block && block.po_weeks && block.po_weeks.length && block.players.some(p => p.po_rank != null));
}

/* His row, or null: not in the file (a bench player under its floor, a kicker) or no file. */
function rosOne(block, slug, scoring){
  const p = block && block.players.find(x => x.slug === slug);
  return p ? rosRow(p, scoring) : null;
}

/* The bump chart: the top lines' rank at each week of their history. `over` marks a rank past the axis, drawn on its
   bottom edge (`shown`). `dots` when the whole history is one week. */
function rosChart(rows){
  const lines = rows.slice(0, ROS_LINES).map((r, i) => ({
    slug: r.slug, n: r.n, lead: i < ROS_LEAD,
    points: r.hist.map(([week, rank]) => ({week, rank, over: rank > ROS_AXIS, shown: Math.min(rank, ROS_AXIS)})),
  }));
  const weeks = [...new Set(lines.flatMap(l => l.points.map(p => p.week)))].sort((a, b) => a - b);
  return {lines, weeks, dots: weeks.length < 2, axis: ROS_AXIS};
}

/* The bump chart's box for a screen `vw` px wide: the screen less the gutters and the card's padding, never past the
   list's column (--list-w, 1128px) and never narrower than the names need. A box past 520px has the room to be taller and to
   give the names a wider column at the right. Its SVG scales to the card, so the box only fixes the proportions. */
function rosBox(vw){
  const w = Math.min(Math.max(vw - 44, 300), 1100), wide = w > 520;
  return {w, h: wide ? 300 : 236, l: 28, r: wide ? 150 : 108, t: 12, b: 22};
}
const ROS_PROFILE_BOX = {w: 312, h: 150, l: 34, r: 14, t: 12, b: 22};

/* Where a week and a rank sit in a box {w, h, l, r, t, b}: the plot is the box less its margins, rank 1 at the top,
   the first week at the left, a lone week mid-plot. */
function rosX(week, weeks, box){
  const span = box.w - box.l - box.r;
  return weeks.length < 2 ? box.l + span / 2 : box.l + weeks.indexOf(week) * span / (weeks.length - 1);
}
function rosY(rank, axis, box){
  return box.t + (Math.min(rank, axis) - 1) * (box.h - box.t - box.b) / (axis - 1);
}

/* The profile's own axis: his worst week, so the line fits, and never fewer than six rows. */
const rosAxis = ranks => Math.max(ROS_MIN_AXIS, ...ranks);

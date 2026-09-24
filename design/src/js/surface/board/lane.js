/* ------------------------------------------------------------------
   THE BOARD — one lane per stat, the position's whole field on it.

   THE LANE'S X IS THE STAT'S OWN VALUE, NEVER A RANK. A rank axis is uniform by construction:
   every tick evenly spaced, the middle always dead centre, and the gap between two players a
   count of the players between them rather than the distance between them. On a value axis the
   pack clusters where the pack is, the elite bar lands where ff-jarvis put it, and two dots a
   thumb apart really are a thumb apart. The rank still gets said — in the header, as a number —
   because "#3" is what a reader repeats to someone else.

   It reads USAGE.sheet, the same season-to-date block the profile's radar ranks from, through
   the same sheetValues(): one definition of who counts on an axis, not two. Axes are
   position-specific (a back has no YPRR), so a lane holds one position and the board switches
   whole rather than mixing two.
------------------------------------------------------------------ */

/* Percent of the rail kept clear at each end, so the best and the worst player keep their own
   dot's width inside the box instead of being clipped by it. */
const BD_PAD = 6;

const BD_ROWS = {};
function bdRows(pos){
  if (!BD_ROWS[pos]) BD_ROWS[pos] = ((USAGE.sheet || {}).rows || []).filter(r => r.pos === pos);
  return BD_ROWS[pos];
}
const bdAxes = pos => ((USAGE.sheet || {}).axes || {})[pos] || [];

/* One axis, scaled to the rail. `q1`/`q3` bound the middle half of the position, drawn as a band
   rather than named in a key: a reader sees whether a dot is inside the pack or out past it, and
   nothing has to explain what a line means. Under two players there is no distribution to draw
   and the lane says so.

   THE SCALE STOPS AT TUKEY'S FENCE, not at the maximum. A rate stat over two weeks throws real
   outliers -- one receiver ran a route, caught it for 40, and holds a YPRR of 13.6 against a
   position whose middle half is 0.8 to 2.1. Drawn to the maximum, that one player owns 80% of
   the rail and the other 110 pile into the left edge, which answers nothing about any of them.
   The fence is the box plot's own rule (a quartile and a half of spread past the quartiles), so
   a lane with no outlier is scaled exactly to its own min and max and nothing moves. A value
   past the fence pins to the end, the rail draws a rule there to say it was cut, and the number
   itself is never lost: the head carries it in full. */
function bdScale(pos, axis){
  const by = sheetValues(pos, axis);
  const vals = Object.values(by);
  if (vals.length < 2) return null;
  const sorted = vals.slice().sort((a, b) => a - b);
  const lo = sorted[0], hi = sorted[sorted.length - 1];
  const q = f => sorted[Math.min(sorted.length - 1, Math.floor(f * (sorted.length - 1)))];
  const q1 = q(.25), q3 = q(.75), reach = 1.5 * (q3 - q1);
  /* Tukey's fence, but never tighter than the 97th and the 3rd. On a stat whose middle half is
     narrow the fence alone cuts far too much: RYOE's quartiles are 0.00 and 0.24 across 74
     backs, which put 20 of them on the two walls -- and two players both pinned read as level
     when one is twice the other. The percentile floor caps the loss at a handful per end.
     A position with no spread in its middle half at all has no fence to speak of. */
  const top = reach > 0 ? Math.min(hi, Math.max(q3 + reach, q(.97))) : hi;
  const bot = reach > 0 ? Math.max(lo, Math.min(q1 - reach, q(.03))) : lo;
  const span = (top - bot) || 1;
  const at = v => BD_PAD + ((Math.min(top, Math.max(bot, v)) - bot) / span) * (100 - 2 * BD_PAD);
  return {by, sorted, n: vals.length, at, q1, q3,
          cutHi: hi > top, cutLo: lo < bot, inside: v => v > bot && v < top};
}

/* The best value on an axis, and who has it: the lane's own leader, which is what the header
   carries before anybody has been picked. */
function bdTop(pos, axis){
  const by = sheetValues(pos, axis);
  let best = null;
  bdRows(pos).forEach(r => {
    const v = by[r.slug];
    if (v !== undefined && (!best || v > best.v)) best = {n: r.n, slug: r.slug, v};
  });
  return best;
}

/* Which of the two picks is ahead on this lane, or "" when they tie or one has no number. With
   a single pick he is always the subject, so he is always the filled dot: there is no contest
   for him to be winning. */
function bdAhead(sc, picks){
  const have = picks.filter(p => sc.by[p.slug] !== undefined);
  if (have.length < 2) return have.length ? have[0].slug : "";
  const [x, y] = have, a = sc.by[x.slug], b = sc.by[y.slug];
  return a === b ? "" : (a > b ? x.slug : y.slug);
}

/* Geometry only. The viewBox is stretched to whatever width the rail happens to be
   (preserveAspectRatio="none"), which would stretch a glyph with it, so the one word on the rail
   is HTML over the top. Stroke widths survive the stretch through non-scaling-stroke.

   A tick fades toward the left end. Direction is then a property of the surface — the same move
   the radar's disc makes from hub to rim — rather than a sentence under the chart saying which
   way is more. */
function bdRailHTML(sc, elite){
  const x = v => sc.at(v).toFixed(2);
  const band = `<rect class="bd-iqr" x="${x(sc.q1)}" y="2" width="${(sc.at(sc.q3) - sc.at(sc.q1)).toFixed(2)}" height="10"/>`;
  const ticks = sc.sorted.map(v => {
    const p = sc.at(v);
    return `<line class="bd-tick" style="--o:${(.22 + .0058 * p).toFixed(3)}" x1="${p.toFixed(2)}" y1="3.5" x2="${p.toFixed(2)}" y2="10.5"/>`;
  }).join("");
  const bar = elite === null || elite === undefined || !sc.inside(elite) ? ""
    : `<line class="bd-bar" x1="${x(elite)}" y1="0" x2="${x(elite)}" y2="14"/>`;
  // The cut, at whichever end runs past the fence: a rule the ticks stack against, so a dot
  // sitting on it reads as pinned to the wall rather than as the true top of the position.
  const rule = at => `<line class="bd-cut" x1="${at}" y1="0" x2="${at}" y2="14"/>`;
  const cut = (sc.cutLo ? rule(BD_PAD) : "") + (sc.cutHi ? rule(100 - BD_PAD) : "");
  return `<svg class="bd-scale" viewBox="0 0 100 14" preserveAspectRatio="none" aria-hidden="true">
    ${band}${ticks}${bar}${cut}</svg>`;
}

/* The elite bar is named in the lane's head, with its number, not on the rail. On the rail the
   word wants the band directly above the dash — which is the band a pick's initials already own,
   and at phone width the two ran through each other ("ELIBRTE"). In the head it costs nothing,
   it says where the threshold is as well as that there is one, and the dashed rule stays the
   only dashed mark on the lane. */
function bdEliteHTML(sc, a){
  return a.elite === null || a.elite === undefined || !sc.inside(a.elite) ? ""
    : `<span class="bd-elite">${t("board.lane.elite", {v: usageFmt(a.elite, a.fmt)})}</span>`;
}

/* A pick on the rail: a dot on the axis, his initials above (first pick) or below (second). The
   split is collision avoidance, not a code — the initials say who it is, and they are the same
   letters the chip above the lanes carries. Filled means ahead on this lane. */
function bdMarkHTML(sc, p, k, ahead){
  const v = sc.by[p.slug];
  if (v === undefined) return "";
  return `<span class="bd-mk bd-${k ? "b" : "a"}${p.slug === ahead ? " ahead" : ""}" style="--x:${sc.at(v).toFixed(2)}">
    <i class="bd-pin"></i><b class="bd-tag">${esc(initials(p.n))}</b></span>`;
}

/* The right of the lane head. With nobody picked it is the lane's leader, which makes the board
   a leaderboard on arrival rather than an empty frame. With picks it is their numbers, in the
   order the chips list them, so the same player holds the same column all the way down.

   A player the sheet has no number for on this axis reads as a dash. Elsewhere on this page a
   missing cell is left out rather than dashed, because a dash reads as a number that failed —
   but in a two-column comparison the dash IS the comparison: he has one, the other does not. */
function bdValsHTML(pos, sc, a, picks){
  if (!picks.length){
    const top = bdTop(pos, a.id);
    return top ? `<span class="bd-vals"><span class="bd-nm">${esc(nameInitial(top.n))}</span
      ><b class="bd-v on">${usageFmt(top.v, a.fmt)}</b></span>` : "";
  }
  const ahead = bdAhead(sc, picks);
  return `<span class="bd-vals">${picks.map(p => {
    const v = sc.by[p.slug];
    return `<b class="bd-v${p.slug === ahead ? " on" : ""}">${v === undefined ? "—" : usageFmt(v, a.fmt)}</b>`;
  }).join("")}</span>`;
}

function bdLaneHTML(pos, a, picks, i){
  const sc = bdScale(pos, a.id);
  const ahead = sc ? bdAhead(sc, picks) : "";
  const rail = sc
    ? bdRailHTML(sc, a.elite) + picks.map((p, k) => bdMarkHTML(sc, p, k, ahead)).join("")
    : `<span class="bd-thin">${t("board.lane.thin")}</span>`;
  return `<div class="bd-lane" style="animation-delay:${40 + i * 46}ms">
    <div class="bd-lh">
      <span class="bd-ax">${esc(a.label)}</span>
      ${sc ? `<span class="bd-meta"><span class="bd-of">${t("board.lane.of", {n: sc.n})}</span
        >${bdEliteHTML(sc, a)}</span>` : ""}
      ${sc ? bdValsHTML(pos, sc, a, picks) : ""}
    </div>
    <div class="bd-rail bd-reveal">${rail}</div>
  </div>`;
}

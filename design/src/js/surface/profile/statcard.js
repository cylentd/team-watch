/* The card under the radar, and the wiring that drives both from one tap. Split out of sheet.js
   on 2026-09-22 when the glossary took that part past the 250-line budget: the chart is one
   concern, what a stat means and what the reader does with it is another. */

/* His weeks on one stat, oldest first. The Grid carries every sheet stat weekly as well as
   season-to-date, so the card's line and the radar's radius are the same number over different
   windows -- never two different definitions of the stat. */
function statWeeks(slug, axis){
  if (typeof USAGE === "undefined" || !USAGE) return [];
  return USAGE.rows.filter(r => r.slug === slug && r.v[axis] !== null && r.v[axis] !== undefined)
    .sort((a, b) => a.wk - b.wk);
}

/* What each axis is, in one line. The chart labels have to be short enough for six of them to
   ring the box, so "RYOE" and "Wtd Opp" arrive as initials and nothing on the page said what
   they measure. Each line is ff-jarvis's own formula in words (model/season/sheet.py's AGG table
   and usage.py), not a gloss: Breakaway really is carries of 15+ yards over carries, Wtd Opp
   really is carries and 2.5 times targets.

   Spelled out one literal t() per axis rather than built from `a.id`, the same call GAMELOG_COLS
   and nav.js make: assemble.py --check finds a copy key by scanning for the literal form and
   cannot see one assembled from a template. */
const AXIS_DEF = {
  wopr:         () => t("profile.def.wopr"),
  route_pct:    () => t("profile.def.routePct"),
  tprr:         () => t("profile.def.tprr"),
  yprr:         () => t("profile.def.yprr"),
  fdrr:         () => t("profile.def.fdrr"),
  rz_tgt:       () => t("profile.def.rzTgt"),
  wopp:         () => t("profile.def.wopp"),
  opp_pct:      () => t("profile.def.oppPct"),
  rz:           () => t("profile.def.rz"),
  ryoe:         () => t("profile.def.ryoe"),
  brk_rate:     () => t("profile.def.brkRate"),
  dropbacks:    () => t("profile.def.dropbacks"),
  designed_pct: () => t("profile.def.designedPct"),
  scr_rate:     () => t("profile.def.scrRate"),
  gl_pct:       () => t("profile.def.glPct"),
  rz_att:       () => t("profile.def.rzAtt"),
  fp_db:        () => t("profile.def.fpDb"),
};

/* And why it is on the chart at all -- what a high one gets you, in the reader's terms. The
   definition says what the number is; this says what to do with it. One clause each: the pair
   has to stay short enough that a reader tapping through six axes reads all six. */
const AXIS_WHY = {
  wopr:         () => t("profile.why.wopr"),
  route_pct:    () => t("profile.why.routePct"),
  tprr:         () => t("profile.why.tprr"),
  yprr:         () => t("profile.why.yprr"),
  fdrr:         () => t("profile.why.fdrr"),
  rz_tgt:       () => t("profile.why.rzTgt"),
  wopp:         () => t("profile.why.wopp"),
  opp_pct:      () => t("profile.why.oppPct"),
  rz:           () => t("profile.why.rz"),
  ryoe:         () => t("profile.why.ryoe"),
  brk_rate:     () => t("profile.why.brkRate"),
  dropbacks:    () => t("profile.why.dropbacks"),
  designed_pct: () => t("profile.why.designedPct"),
  scr_rate:     () => t("profile.why.scrRate"),
  gl_pct:       () => t("profile.why.glPct"),
  rz_att:       () => t("profile.why.rzAtt"),
  fp_db:        () => t("profile.why.fpDb"),
};

/* How far he is from the position's elite bar, and which side of it. `usageFmt` formats the gap
   in the stat's own units, so a percentage reads as points and a rate as a rate. */
function eliteGapHTML(v, a){
  const gap = v - a.elite;
  const n = {gap: usageFmt(Math.abs(gap), a.fmt), bar: usageFmt(a.elite, a.fmt)};
  // Two literal t() calls, not one built from a ternary: assemble.py --check finds a copy key by
  // scanning for the literal form, and a key assembled at runtime reads to it as an orphan.
  return gap >= 0
    ? `<small class="pf-stat-d up">${t("profile.stat.overElite", n)}</small>`
    : `<small class="pf-stat-d down">${t("profile.stat.underElite", n)}</small>`;
}

/* The card under the sheet for one stat: what it measures, what a high one gets you, his season
   number, the bar it has to clear, and the weeks as a line. No rank, deliberately. The rank had
   three homes on one screen -- the lede at hero size, the radar's own axis label, and here --
   and three copies of one number read as three numbers. */
function statDetailHTML(s, axis){
  const a = s.axes.find(x => x.id === axis) || s.axes[0];
  const slug = s.row.slug, v = s.row.v[a.id];
  /* The gap, not the threshold. "elite >= 0.00" printed in red said the elite bar was the bad
     thing; what is actually red is him being 0.42 under it. So the line states the distance and
     which side of the bar he is on, and the colour agrees with the sign instead of contradicting
     a number nobody was being asked to judge. The bar itself still appears, because "0.42 short"
     of what is not a number. */
  // Not under the sample floor either: "over the elite bar" on 12 routes is the claim it can't make.
  const thin = sheetThin(s.row, a.id);
  const bar = a.elite === null || a.elite === undefined || v === null || v === undefined || thin ? ""
    : eliteGapHTML(v, a);
  const wk = statWeeks(slug, a.id);
  // The spark is read against the same bar, so a week above it is visibly a week above it.
  const line = wk.length ? sparkHTML(wk.map(r => r.v[a.id]), 160, 30, a.elite) : "";
  /* The window comes from the stat's own weeks, not from his games played. "2 gm · wk 1-1" was
     a contradiction on every route-derived stat: he played two games, but heatradar has only
     published week 1, so TPRR, YPRR, 1D/RR and Route% are a one-week number sitting on the same
     chart as two-week ones. The card says which, per stat. */
  const span = !wk.length ? "" : wk.length === 1 || wk[0].wk === wk[wk.length - 1].wk
    ? t("profile.stat.week", {n: wk[0].wk})
    : t("profile.stat.weeks", {a: wk[0].wk, b: wk[wk.length - 1].wk});
  const meta = [statMetaText(s, a.id, !span)].concat(span ? [span] : []).filter(Boolean).join(" · ");
  const weeks = `<span class="pf-stat-wk">${meta}</span>`;
  const def = AXIS_DEF[a.id]
    ? `<p class="pf-stat-def">${AXIS_DEF[a.id]()}${AXIS_WHY[a.id] ? `<span class="pf-stat-why">${AXIS_WHY[a.id]()}</span>` : ""}</p>` : "";
  return `<div class="pf-stat-h"><span class="pf-stat-l">${esc(axisName(a))}</span>${weeks}</div>
    ${def}<b${thin ? ` class="thin"` : ""}>${usageFmt(v, a.fmt)}</b><span class="pf-stat-side">${sampleHTML(s.row, a)}${bar}</span>${line}`;
}

/* Each stat's name in plain words, 2026-09-25. ff-jarvis's labels are the analyst's shorthand
   ("Wtd Opp", "RYOE", "1D/RR"), which a reader has to decode before reading; these say what the
   stat is about, and the card's definition under the chart still gives the exact formula. One
   name per stat everywhere it appears -- radar, card, lede, Board -- so the reader never has to
   match two names for one thing. An axis with no entry falls back to the producer's label. */
const AXIS_NAME = {
  wopr:         () => t("profile.axis.wopr"),
  route_pct:    () => t("profile.axis.routePct"),
  tprr:         () => t("profile.axis.tprr"),
  yprr:         () => t("profile.axis.yprr"),
  fdrr:         () => t("profile.axis.fdrr"),
  rz_tgt:       () => t("profile.axis.rzTgt"),
  wopp:         () => t("profile.axis.wopp"),
  opp_pct:      () => t("profile.axis.oppPct"),
  rz:           () => t("profile.axis.rz"),
  ryoe:         () => t("profile.axis.ryoe"),
  brk_rate:     () => t("profile.axis.brkRate"),
  dropbacks:    () => t("profile.axis.dropbacks"),
  designed_pct: () => t("profile.axis.designedPct"),
  scr_rate:     () => t("profile.axis.scrRate"),
  gl_pct:       () => t("profile.axis.glPct"),
  rz_att:       () => t("profile.axis.rzAtt"),
  fp_db:        () => t("profile.axis.fpDb"),
};
const axisName = a => AXIS_NAME[a.id] ? AXIS_NAME[a.id]() : a.label;

/* Tapping a stat on the sheet swaps the card under it and moves the highlight. One `data-col`
   sweep lights the label, its spoke, its vertex and its elite tick together, so the chart and
   the card are visibly the same stat; the ring fires at the vertex to mark the change, and the
   card replays its entrance so the number reads as changed rather than as always having been
   that. */
/* Hold the tallest of the six, so picking a stat never moves what is under it.

   Both blocks change height with the axis. The card's definition runs one line for "Targets per
   route run." and three for WOPR's, which moved it by up to 63px on a tap; the caption carries
   that axis's own denominator, and "Out of 120 WRs" wraps where "Out of 20 WRs" does not, for
   another 21px on a phone. Either one shoves the tab bar and the whole pane down while the
   reader is looking at them.

   Measured here rather than guessed in CSS: the height depends on the font, the column width and
   where each sentence happens to wrap, so a hard-coded reservation is wrong on the first phone
   that disagrees. Two elements, six layouts each, once, before the modal animates in. A resize
   while the modal is open leaves the reservation stale -- the next open measures again. */
function reserveTallest(el, axes, render){
  const keep = el.innerHTML;
  let tallest = 0;
  axes.forEach(a => {
    el.innerHTML = render(a.id);
    tallest = Math.max(tallest, el.offsetHeight);
  });
  el.innerHTML = keep;
  if (tallest) el.style.minHeight = tallest + "px";
}

function wireSheet(d){
  const el = d.querySelector(".pf-sheet");
  if (!el) return;
  const s = sheetFor({slug: el.dataset.slug});
  if (!s) return;
  const card = el.querySelector(".pf-stat");
  reserveTallest(card, s.axes, id => statDetailHTML(s, id));
  const ping = el.querySelector(".pf-radar-ping"), mark = el.querySelector(".pf-radar-mark");
  const pick = node => {
    const col = node.dataset.col;
    el.querySelectorAll("[data-col]").forEach(x => x.classList.toggle("on", x.dataset.col === col));
    card.innerHTML = statDetailHTML(s, col);
    card.classList.remove("swap"); void card.offsetWidth; card.classList.add("swap");
    countUp(card.querySelector(".pf-stat > b"));
    const dot = el.querySelector(`.pf-radar-dot[data-col="${col}"]`);
    if (!dot) return;
    [mark, ping].forEach(c => {
      if (!c) return;
      c.setAttribute("cx", dot.getAttribute("cx"));
      c.setAttribute("cy", dot.getAttribute("cy"));
    });
    if (!ping) return;
    ping.classList.remove("on"); void ping.getBoundingClientRect(); ping.classList.add("on");
  };
  // Buttons: Enter and Space already arrive as a click.
  el.querySelectorAll(".pf-radar-l").forEach(node => node.addEventListener("click", () => pick(node)));
  const g = radarGeo(el);
  if (!g) return;
  radarGrow(g);
  countUp(card.querySelector(".pf-stat > b"), 380);
  wireRadarTouch(el, s, g, pick);
}

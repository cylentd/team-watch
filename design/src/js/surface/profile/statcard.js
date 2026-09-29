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
  /* The gap, not the threshold. "elite >= 0.00" printed in red said the elite bar was the bad
     thing; what is actually red is him being 0.42 under it. So the line states the distance and
     which side of the bar he is on, and the colour agrees with the sign. */
  return gap >= 0
    ? `<small class="pf-lr-d up">${t("profile.stat.overElite", n)}</small>`
    : `<small class="pf-lr-d down">${t("profile.stat.underElite", n)}</small>`;
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

/* One stat lit on the chart and the ladder at once. One `data-col` sweep lights the label, its
   vertex, its elite arc and its ladder row together, so the chart and the list are visibly the
   same stat; the ring fires at the vertex to mark the change. A label tap also opens that row's
   fold, which is where the card's definition went; a drag across the dial (radartouch.js) only
   moves the light, since folds opening and shutting under a moving finger would jump the list. */

/* `o.grow` false skips the vertices' entrance: the sphere's morph (orb.js) has already brought the
   shape in, and a second arrival on top of the first would be the chart arriving twice. */
function wireSheet(d, o = {}){
  const el = d.querySelector(".pf-sheet");
  if (!el) return;
  const s = sheetFor({slug: el.dataset.slug});
  if (!s) return;
  const ping = el.querySelector(".pf-radar-ping"), mark = el.querySelector(".pf-radar-mark");
  let cur = sheetDefaultAxis(s);
  const pick = node => {
    const col = node.dataset.col;
    if (col === cur) return;
    cur = col;
    el.querySelectorAll("[data-col]").forEach(x => x.classList.toggle("on", x.dataset.col === col));
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
  el.querySelectorAll(".pf-radar-l").forEach(node => node.addEventListener("click", () => {
    pick(node);
    const row = el.querySelector(`.pf-lr[data-col="${node.dataset.col}"]`);
    if (!row || row.open) return;
    row.open = true;
    row.scrollIntoView({block: "nearest", behavior: REDUCED() ? "auto" : "smooth"});
  }));
  el.querySelectorAll(".pf-lr").forEach(row => row.addEventListener("toggle", () => { if (row.open) pick(row); }));
  const g = radarGeo(el);
  if (!g) return;
  if (o.grow !== false) radarGrow(g);
  wireRadarTouch(el, s, g, pick);
}

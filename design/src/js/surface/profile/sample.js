/* What a rate is out of, said beside it (2026-09-26). A bare "33%" read the same whether it was
   1 of 3 or 30 of 90, and early in a season most of the sheet's rates are the first kind: M.
   Stafford's goal-line share was 1 of the Rams' 3 carries inside the 5, T. Higbee's targets per
   route 2 of 4. ff-jarvis publishes each rate's [numerator, denominator] and the axis's `floor`;
   below the floor the number stays, dimmed, and sheetThin (sheet.js) keeps it out of every rank.

   A share says "n of d"; a per-chance average (points per dropback, yards per route) says only
   the d, because "91 of 4 routes" is not a sentence.

   Before sheet.js, whose sheetValues() calls sheetThin: that is the one definition of who is
   ranked, so the radar, the lede and Leaders all drop a thin rate together. */
const sheetAxis = (pos, axis) => ((USAGE.sheet.axes || {})[pos] || []).find(a => a.id === axis) || {};
const sheetSample = (r, axis) => (r.s || {})[axis] || null;
function sheetThin(r, axis){
  const floor = sheetAxis(r.pos, axis).floor, s = sheetSample(r, axis);
  return !!floor && !!s && s[1] !== null && s[1] < floor;
}

/* One literal t() per denominator, the same reason AXIS_DEF spells its keys out: assemble.py
   --check finds a copy key by scanning for the literal form. */
const SAMPLE_UNIT = {
  team_gl_car:   () => t("profile.sample.teamGlCar"),
  team_designed: () => t("profile.sample.teamDesigned"),
  team_rb_opp:   () => t("profile.sample.teamRbOpp"),
  team_db_r:     () => t("profile.sample.teamDb"),
  dropbacks:     () => t("profile.sample.dropbacks"),
  car:           () => t("profile.sample.carries"),
  routes:        () => t("profile.sample.routes"),
};

function sampleText(row, a){
  const smp = sheetSample(row, a.id);
  if (!smp || smp[1] === null || !SAMPLE_UNIT[a.den]) return "";
  const unit = SAMPLE_UNIT[a.den]();
  return a.fmt === "pct" && smp[0] !== null
    ? t("profile.sample.of", {n: smp[0], d: smp[1], unit})
    : t("profile.sample.on", {d: smp[1], unit});
}

/* The short form for a list of names (the Leaders footer): "1/3" for a share, since the stat's tab
   is right above it and already says what the 3 are. */
function sampleShort(row, a){
  const smp = sheetSample(row, a.id);
  if (!smp || smp[1] === null) return "";
  return a.fmt === "pct" && smp[0] !== null ? `${smp[0]}/${smp[1]}` : sampleText(row, a);
}

/* The card's side column: the sample, and under it why there is no rank when there is none. */
function sampleHTML(row, a){
  const say = sampleText(row, a);
  if (!say) return "";
  const thin = sheetThin(row, a.id)
    ? `<small class="pf-stat-thin">${t("profile.sample.thin", {floor: a.floor})}</small>` : "";
  return `<small class="pf-stat-smp">${say}</small>${thin}`;
}

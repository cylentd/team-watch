/* ------------------------------------------------------------------
   PREVIEW's "Defenses lately" (2026-11-14, TODO "Outcome ranges" d): under Defense rank in the box score, one line
   per defense and position whose recent form flagged, away offense's opponent first (dfSides, data/defform.js). Each
   line is two rows: the defense and the trend in words ("JAX run D ↑ allowing more"), then the file's two numbers
   ("112 rush yds a game, last 3 · 68 season"). Nothing flagged, no section. The head carries "context only", its tip
   saying form failed as a price (ff-jarvis METHODOLOGY 12.73). An earlier week's game never shows it: the form is
   this week's.
------------------------------------------------------------------ */
function pvFormLineHTML(f){
  const n = dfNum(f), args = {last: n(f.last3), season: n(f.season), pos: f.pos};
  const who = f.kind === "rush" ? t("preview.form.who.rush", {df: esc(f.def)}) : t("preview.form.who.pts", {df: esc(f.def), pos: f.pos});
  const nums = f.kind === "rush" ? t("preview.form.rush", args) : t("preview.form.pts", args);
  return `<li class="pv-df ${f.trend}" data-testid="preview-form-line" data-trend="${f.trend}"><span class="pv-dfw">${who} <b>${dfTrendText(f)}</b></span><span class="pv-dfn">${nums}</span></li>`;
}

function pvFormRow(g){
  if (PV_ARC_G) return "";
  const sides = dfSides(typeof LIVE_SOS === "undefined" ? null : LIVE_SOS, g.away, g.home);
  if (!sides.length) return "";
  const head = `${t("preview.row.form")}<em title="${t("dform.markTip")}">${t("dform.mark")}</em>`;
  return pvRow("form", head, `<ul class="pv-dfl">${sides.flatMap(s => s.forms).map(pvFormLineHTML).join("")}</ul>`);
}

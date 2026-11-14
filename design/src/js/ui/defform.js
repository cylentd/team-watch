/* Defense form's words, shared by Schedule's note and Preview's lines (2026-11-14). A form is dfForm's (data/defform.js).
   The trend always reads in words beside its arrow, "↑ allowing more" / "↓ allowing less", said for the offense; the
   colour (--up more, --down less, as Preview's soft / tough defense rank) only repeats it. Points keep one decimal,
   rush yards none, as the file's own example prints them. */
const dfNum = f => v => (f.kind === "rush" ? String(Math.round(v)) : v.toFixed(1));
const dfTrendText = f => (f.trend === "up" ? t("dform.trend.up") : t("dform.trend.down"));

/* The two numbers in a sentence, then the context mark: the tip on Schedule's note. */
function dfTip(f){
  const n = dfNum(f), args = {df: esc(f.def), pos: f.pos, last: n(f.last3), season: n(f.season)};
  return `${f.kind === "rush" ? t("dform.tip.rush", args) : t("dform.tip.pts", args)} ${t("dform.markTip")}`;
}

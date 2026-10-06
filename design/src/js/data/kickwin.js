/* A Bets kickoff window's words (2026-10-05). design/slate.py gives each window a `slot`, the league's Eastern
   one (et_slot, the same function Preview's slate uses), and the page names it here with Preview's own words
   ("Sunday early", "Monday night"), because the times beside it are in the reader's clock: a New York reader
   saw "Sunday morning · 1:00 PM" when the window was named by a Pacific hour. Pure; `slot` is the only input.
   A window with no slot (a Saturday, an old file) keeps its Python label. */

/* Preview's name for the window, or null. A day ("All Sunday") keeps its own label. */
function kickWinName(w){
  if (!w || w.wins) return null;
  return {thu: t("preview.win.thu"), sunam: t("preview.win.sunam"), sun1: t("preview.win.sun1"),
    sunlate: t("preview.win.sunlate"), sunnight: t("preview.win.sunnight"), mon: t("preview.win.mon")}[w.slot] || null;
}

/* The one word a window wears on a tab beside its day ("Sun Early"). Falls back to the key's old bucket. */
function kickWinPart(w){
  const part = {sunam: t("parlay.kick.morning"), sun1: t("parlay.kick.early"), sunlate: t("parlay.kick.late"),
    sunnight: t("parlay.kick.night"), thu: t("parlay.kick.night"), mon: t("parlay.kick.night")}[w && w.slot];
  if (part) return part;
  const k = (w && w.k) || "";
  return /^morning/.test(k) ? t("parlay.kick.early") : /^afternoon/.test(k) ? t("parlay.kick.late") : t("parlay.kick.night");
}

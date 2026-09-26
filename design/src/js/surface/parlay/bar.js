/* The Bets bar: the one row of controls above the data (design/STYLE.md), and the settings panel
   it opens.

   Slips' row is its legs filter as tabs; Build's is its position chips. Both end in the same chip,
   which names the book and the kickoff in force and opens the panel: book and kickoff there are
   one setting for both views, and Build adds its market, sort and "my players" beside them. What
   used to be three filter bars on one page is one row, and a panel you open when you want it. */
/* The book's full name where there is room and its initials on a phone, where five position
   chips and this one share 330px; the kickoff only when one is chosen, since "all" is the default. */
function betsSettingLabel(){
  const ud = PARLAY_BOOK === "underdog";
  const book = `<span class="full">${ud ? t("parlay.bar.ud") : t("parlay.bar.dk")}</span><span class="abbr">${ud ? t("parlay.bar.udShort") : t("parlay.bar.dkShort")}</span>`;
  const win = GAL_WINDOWS.find(w => w.k === GAL_WIN);
  return win ? `${book} · ${esc(win.label)}` : book;
}

function betsBarHTML(build){
  const set = `<button type="button" class="chip bets-set" data-betspanel aria-expanded="${BETS_PANEL}"
    aria-label="${t("parlay.bar.settings")}">${betsSettingLabel()}<span class="bets-caret" aria-hidden="true"></span></button>`;
  if (build) return `<div class="filters bets-bar">
    ${["ALL","QB","RB","WR","TE"].map(p=>`<button class="chip" data-mpos="${p}" aria-pressed="${MKT_POS===p}">${p === "ALL" ? t("parlay.option.all") : p}</button>`).join("")}
    ${set}</div>`;
  return `<div class="bets-bar bets-tabsrow">
    <div class="bd-tabs" role="tablist" aria-label="${t("parlay.gallery.legsLabel")}">${galleryScopes(PARLAY_BOOK).map(([k, label]) =>
      `<button type="button" class="bd-tab" role="tab" data-scope="${k}" aria-selected="${SLIP_SCOPE===k}">${label}</button>`).join("")}</div>
    ${set}</div>`;
}

/* Book first because it changes everything below it; kickoff second; then Build's own three. */
function betsPanelHTML(build){
  if (!BETS_PANEL) return "";
  const sel = (k, label, opts, cur) => `<label class="selwrap"><span class="lbl">${label}</span>
    <select class="msel" data-msel="${k}">${opts.map(([v, l]) => `<option value="${v}" ${cur===v?"selected":""}>${l}</option>`).join("")}</select></label>`;
  const sorts = PARLAY_BOOK === "underdog"
    // Anytime TD on Underdog is a model read at P(score) on every row, so one sort, named for
    // what it is, instead of three that visibly do nothing.
    ? (MKT_KIND === "TD" ? [["model",t("parlay.sort.model")]] : [["conf",t("parlay.sort.conf")],["model",t("parlay.sort.model")],["ready",t("parlay.sort.ready")]])
    : [["edge",t("parlay.sort.edge")],["model",t("parlay.sort.model")],["ready",t("parlay.sort.ready")]];
  return `<div class="bets-panel">
    <div class="modes-sub bets-book">
      <button class="mode-sub" data-parlaybook="underdog" aria-pressed="${PARLAY_BOOK==="underdog"}">${t("parlay.book.underdog")}</button>
      <button class="mode-sub" data-parlaybook="dk" aria-pressed="${PARLAY_BOOK==="dk"}">${t("parlay.book.dk")}</button>
    </div>
    <div class="filters">
      ${sel("gwin", t("parlay.filter.kickoff"), [["ALL", t("parlay.option.all")], ...GAL_WINDOWS.map(w => [w.k, esc(w.label)])], GAL_WIN)}
      ${build ? sel("mkind", t("parlay.filter.market"), [["ALL",t("parlay.option.all")],["TD",MKT.TD],["RUSH",MKT.RUSH],["REC",MKT.REC],["RECS",MKT.RECS],["PASS",MKT.PASS]], MKT_KIND)
        + sel("msort", t("parlay.filter.sort"), sorts, MKT_SORT)
        + `<button class="chip" data-mine="1" aria-pressed="${MKT_MINE}">${t("parlay.filter.mineOnly")}</button>` : ""}
      <span style="flex:1"></span>
      ${explainButtonHTML("parlay")}
    </div>
  </div>`;
}

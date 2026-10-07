/* The Bets bar: the one row of controls above the data (design/STYLE.md), and the settings panel
   it opens.

   Slips' row is its kickoff as tabs (each game's own chips sit in its card, board.js); Build's is Best odds and its position chips (no "All"
   since 2026-09-29: a pressed position tapped again clears it, so six chips fit 360px). Both end in the same chip,
   which names the book and the kickoff in force and opens the panel: book and kickoff there are
   one setting for both views, and Build adds its market, sort and "my players" beside them. What
   used to be three filter bars on one page is one row, and a panel you open when you want it. */
/* The book's full name where there is room and its initials on a phone, where five position
   chips and this one share 330px; the kickoff only when one is chosen, since "all" is the default. */
function betsSettingLabel(build){
  const ud = PARLAY_BOOK === "underdog";
  const book = `<span class="full">${ud ? t("parlay.bar.ud") : t("parlay.bar.dk")}</span><span class="abbr">${ud ? t("parlay.bar.udShort") : t("parlay.bar.dkShort")}</span>`;
  const win = GAL_WINDOWS.find(w => w.k === GAL_WIN);
  return win && build ? `${book} · ${esc(galGroupName(win))}` : book;
}

function betsBarHTML(build){
  const set = `<button type="button" class="chip bets-set" data-betspanel aria-expanded="${BETS_PANEL}"
    aria-label="${t("parlay.bar.settings")}">${betsSettingLabel(build)}<span class="bets-caret" aria-hidden="true"></span></button>`;
  if (build) return `<div class="filters bets-bar" data-testid="parlay-bar">
    <button class="chip bets-best" data-mbest aria-pressed="${MKT_BEST}">${t("parlay.bar.best")}</button>
    ${["QB","RB","WR","TE"].map(p=>`<button class="chip" data-mpos="${p}" aria-pressed="${MKT_POS===p}">${p}</button>`).join("")}
    ${set}</div>`;
  const on = slWin();
  return `<div class="bets-bar bets-tabsrow" data-testid="parlay-bar">
    <div class="bd-tabs view-tabs" role="tablist" data-testid="parlay-kick-tabs" aria-label="${t("parlay.filter.kickoff")}">${KICK_CHIPS.map(w =>
      `<button type="button" class="bd-tab" role="tab" data-testid="parlay-kick-tab" data-gwin="${esc(w.k)}" aria-selected="${on === w}"
        aria-label="${esc(galGroupName(w))}">${esc(kickChipLabel(w))}</button>`).join("")}</div>
    ${set}</div>`;
}

/* Slips' kickoff tabs (2026-09-29): Thu · Sun · Early · Late · Night · Mon (AM · PM · Night until 2026-10-05,
   Pacific hours beside a clock that is the reader's). A day of several windows is its weekday (the whole
   day), followed by its parts; a day of one window is its weekday. Six tabs and the book chip fit 360px
   only this way: "Sun AM" and "All Sun" ran 82px over. */
const KICK_CHIPS = GAL_GROUPS;
const kickDay = w => new Date(`${w.date}T12:00:00`).toLocaleDateString("en-US", {weekday: "short"});
const kickPart = kickWinPart;   // Preview's Eastern slot words, not a Pacific AM/PM (data/kickwin.js)
const kickInDay = w => !w.wins && DAYS.some(d => d.wins.includes(w.k) && GAL_WINDOWS.includes(d));
function kickChipLabel(w){ return kickInDay(w) ? kickPart(w) : kickDay(w); }

/* On a phone the kickoffs are the Slips pill's segments in the tab row (2026-10-05, data/tabrow.js), and
   the row above keeps only the book chip (.view-tabs hides these tabs there, chrome/phonenav.css). The
   page holds its place, as a tap on the tabs here does (flight.js wireBets). */
navModes("parlay", () => ({ids: KICK_CHIPS.map(w => w.k), cur: (slWin() || {}).k, attr: "gwin", name: t("parlay.filter.kickoff"),
  label: k => esc(kickChipLabel(KICK_CHIPS.find(w => w.k === k))),
  select: k => { GAL_WIN = k; MKT_PAGE = 1; const y = window.scrollY; render(); window.scrollTo(0, y); }}));
/* The same kickoff named on its own, off the tab row: "Sun Early", "All Sun", "Thu". */
function kickName(w){
  if (w.wins) return t("parlay.kick.day", {day: kickDay(w)});
  return kickInDay(w) ? `${kickDay(w)} ${kickPart(w)}` : kickDay(w);
}

/* Book first because it changes everything below it; kickoff second; then Build's own three. */
function betsPanelHTML(build){
  if (!BETS_PANEL) return "";
  const mine = mineSlugs();   // a reader who follows no team has no players of their own, so no chip (2026-10-06)
  const sel = (k, label, opts, cur) => `<label class="selwrap"><span class="lbl">${label}</span>
    <select class="msel" data-testid="parlay-select" data-msel="${k}">${opts.map(([v, l]) => `<option value="${v}" ${cur===v?"selected":""}>${l}</option>`).join("")}</select></label>`;
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
      ${build ? sel("gwin", t("parlay.filter.kickoff"), [["ALL", t("parlay.option.all")], ...GAL_WINDOWS.map(w => [w.k, esc(galGroupName(w))])], GAL_WIN) : ""}
      ${build ? sel("mkind", t("parlay.filter.market"), [["ALL",t("parlay.option.all")],["TD",MKT.TD],["RUSH",MKT.RUSH],["REC",MKT.REC],["RECS",MKT.RECS],["PASS",MKT.PASS]], MKT_KIND)
        + sel("msort", t("parlay.filter.sort"), sorts, MKT_SORT)
        + (mine.size ? `<button class="chip" data-testid="parlay-mine-only" data-mine="1" aria-pressed="${betsMineOn(mine)}">${t("parlay.filter.mineOnly")}</button>` : "") : ""}
      <span style="flex:1"></span>
      ${explainButtonHTML("parlay")}
    </div>
  </div>`;
}

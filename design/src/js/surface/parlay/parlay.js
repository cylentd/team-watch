/* BETS -- Slips and Build, two views of one surface (2026-09-25).

   Slips is the ready-made tickets; Build is the line market you pick from. They were one page with
   three sections and three filter bars, and every visit scrolled past the half it had not come
   for. Now each view is one job with one row of controls above its data (design/STYLE.md), and
   the slip both views fill is a tray on the bottom edge (tray.js) rather than a column mid-page.
   Book and kickoff are one setting for both views, behind the chip at the end of the bar (bar.js).
   The leaf of Slips is still `parlay`, so its bookmarks land. */
function parlayHTML(){
  const build = SURFACE === "build";
  return `<div class="wrap bets">
    ${betsBarHTML(build)}
    ${betsPanelHTML(build)}
    ${build ? buildHTML() : galleryHTML()}
    <p class="note bets-foot">${build ? "" : `${t("parlay.gallery.sub")} · `}${SLATE_WEEK ? t("parlay.hero.eyebrow", {n: PROPS.length, week: SLATE_WEEK}) : t("parlay.hero.eyebrowNoWeek", {n: PROPS.length})}</p>
  </div>
  ${trayHTML()}${sheetHTML()}`;
}

/* The lines that pass Build's filters, in the chosen sort. Kickoff is the shared GAL_WIN, read
   through inWin so a whole-day choice ("Sunday") covers its windows. */
function buildLines(){
  const win = GAL_WINDOWS.find(w => w.k === GAL_WIN);
  return PROPS.filter(p => (MKT_POS==="ALL"||p.pos===MKT_POS) && (MKT_KIND==="ALL"||p.mkt===MKT_KIND)
    && (GAL_WIN==="ALL"||inWin(p, win)) && (!MKT_MINE||p.mine)
    // A real Underdog price without a model rating yet has no higher/lower call to show; udPick
    // covers that plus the TD rows Underdog has no line for at all.
    && (PARLAY_BOOK !== "underdog" || udPick(p))).sort(SORTS[MKT_SORT]);
}

/* Underdog groups the sorted lines by player, first appearance keeping the sort (so a Confidence
   sort orders players by their strongest call), and pages by player. DK stays one row per line. */
function buildHTML(){
  const all = buildLines(), ud = PARLAY_BOOK === "underdog";
  const groups = ud ? [...all.reduce((m, p) => (m.get(p.n) || m.set(p.n, []).get(p.n)).push(p) && m, new Map()).values()] : null;
  const units = ud ? groups : all, size = ud ? UD_PAGE_SIZE : MKT_PAGE_SIZE;
  const pages = Math.max(1, Math.ceil(units.length / size));
  const page = Math.min(MKT_PAGE, pages);
  const rows = units.slice((page-1)*size, page*size);
  const pager = `<div class="filters bets-pager">
    <span class="lbl">${t("parlay.pager.lines", {n: all.length, s: all.length===1?"":"s"})}${ud ? ` · ${t("parlay.pager.players", {n: groups.length, s: groups.length===1?"":"s"})}` : ""}${ud && all.some(p => udPick(p).synthetic) ? ` · ${t("parlay.pager.tdNote")}` : ""}</span>
    <span style="flex:1"></span>
    <button class="chip" data-mktpage="prev" ${page<=1?"disabled":""}>${t("common.pager.prev")}</button>
    <span class="lbl">${t("common.pager.page", {page: page, pages: pages})}</span>
    <button class="chip" data-mktpage="next" ${page>=pages?"disabled":""}>${t("common.pager.next")}</button>
  </div>`;
  return rows.length
    ? `<div class="legs ${ud ? "pgrid" : "lgrid"}">${ud ? rows.map(udPlayerCard).join("") : rows.map(p=>propCard(p, PROPS.indexOf(p))).join("")}</div>${pager}`
    : `<div class="state-empty" style="margin:20px 0;min-height:120px"><div><b>0</b><span>${t("parlay.empty.noLines")}</span></div></div>`;
}

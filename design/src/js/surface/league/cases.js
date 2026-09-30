/* ============================== RECORDS: THE TWO CASES ==============================
   2026-09-28, storyboard https://claude.ai/artifact/8un5qeN8s5LwMaEKTfXGmV (option A). The trophy case
   and the last-place case, one season per slot, four to a shelf. A season whose final lineup ff-jarvis
   has read (LG.rosters, from yahoo_case_rosters.json) is a button that opens that lineup in the sheet;
   one it has not (2018) is a plain slot, the same shape. Styles: css/surface/league/cases.css. */

/* The gradients once per page: gold, a cup's black base, porcelain, chrome, grime. Their colours are
   classes (cases.css), so no colour sits in the markup. */
const CS_DEFS = `<svg class="cs-defs" aria-hidden="true" focusable="false"><defs>
  <linearGradient id="cs-gold" x1="0" y1="0" x2="1" y2="0"><stop offset="0" class="s-gold-lo"/><stop offset=".28" class="s-gold"/>
    <stop offset=".42" class="s-gold-hi"/><stop offset=".62" class="s-gold-mid"/><stop offset="1" class="s-gold-lo"/></linearGradient>
  <linearGradient id="cs-base" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="s-plinth"/><stop offset="1" class="s-plinth-lo"/></linearGradient>
  <linearGradient id="cs-shine" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="s-gold-hi"/><stop offset="1" class="s-gold-hi"/></linearGradient>
  <linearGradient id="cs-porc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" class="s-porc-lo"/><stop offset=".35" class="s-porc-hi"/><stop offset="1" class="s-porc"/></linearGradient>
  <linearGradient id="cs-seat" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="s-porc-hi"/><stop offset="1" class="s-porc"/></linearGradient>
  <linearGradient id="cs-foot" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="s-porc-lo"/><stop offset="1" class="s-porc-lo"/></linearGradient>
  <linearGradient id="cs-chrome" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="s-chrome"/><stop offset="1" class="s-chrome"/></linearGradient>
  <linearGradient id="cs-grime" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="s-grime"/><stop offset="1" class="s-grime"/></linearGradient>
</defs></svg>`;

/* A cup with two handles on a black base, lit from the left. */
const CS_CUP = `<svg class="cs-ico" viewBox="0 0 48 64" aria-hidden="true">
  <path fill="url(#cs-gold)" d="M13 6h22v14c0 7-5 12-11 12S13 27 13 20zM13 9H6v5c0 6 4 10 9 10v-3c-3 0-6-3-6-7v-2h4M35 9h7v5c0 6-4 10-9 10v-3c3 0 6-3 6-7v-2h-4M21 32h6v9h-6zM16 41h16l2 5H14z"/>
  <rect x="11" y="46" width="26" height="12" rx="1" fill="url(#cs-base)"/>
  <path d="M17 8v11c0 3 1 6 3 8" stroke="url(#cs-shine)" stroke-width="1.6" fill="none" stroke-linecap="round" opacity=".9"/>
</svg>`;

/* A toilet side on: tank, handle, seat, bowl, foot, and a stain. */
const CS_TOILET = `<svg class="cs-ico" viewBox="0 0 48 64" aria-hidden="true">
  <rect x="5" y="4" width="17" height="4" rx="1.5" fill="url(#cs-porc)"/>
  <rect x="6" y="7" width="15" height="23" rx="2" fill="url(#cs-porc)"/>
  <rect x="15" y="11" width="5" height="2" rx="1" fill="url(#cs-chrome)"/>
  <rect x="17" y="28" width="28" height="4.5" rx="2.2" fill="url(#cs-seat)"/>
  <path fill="url(#cs-porc)" d="M18 32.5h26c0 9-6 15-14 16l-1 8.5H18.5l1.2-8.5C18.4 44 18 38 18 32.5z"/>
  <rect x="15.5" y="56" width="17" height="4" rx="1.2" fill="url(#cs-foot)"/>
  <path d="M40 34c-1 6-5 10-10 11" stroke="url(#cs-grime)" stroke-width="1.2" fill="none" opacity=".55"/>
</svg>`;

/* The crack in the cheap pane's top-right corner, clear of every name. */
const CS_CRACK = `<svg class="cs-crack" viewBox="0 0 34 24" preserveAspectRatio="none" aria-hidden="true">
  <path d="M34 1L26 5l3 3-9 4M26 5l-2-4M29 8l4 5"/></svg>`;

const csRoster = (y, kind) => ((LG.rosters || {})[y] || {})[kind] || null;

/* One season: `kind` is "champ" or "last". A button when its lineup is in, else the same shape. */
function csSlotHTML(kind, r){
  // The team line only when it says something the holder line does not: a league with no managers
  // file (AYO's podiums, 2026-09-29) names each champion by the team it won as, once.
  const who = lgHolder(r.mgr, r.id, r.name), named = r.name ? esc(r.name.trim()) : "", team = named === who ? "" : named;
  const inner = `${kind === "champ" ? CS_CUP : CS_TOILET}<span class="cs-plate">${r.y}</span>
    <span class="cs-mgr">${who}</span><span class="cs-team">${team}</span>`;
  const est = r.final === false ? " est" : "";
  if (!csRoster(r.y, kind)) return `<li><div class="cs-slot${est}">${inner}</div></li>`;
  const aria = kind === "champ" ? t("records.case.open.champ", {y: r.y, mgr: who}) : t("records.case.open.last", {y: r.y, mgr: who});
  return `<li><button type="button" class="cs-slot${est}" data-csroster="${r.y}:${kind}" aria-label="${aria}">${inner}</button></li>`;
}

/* The cabinet: shelves of four, the season-order kept (newest first). */
function csCaseHTML(kind, rows){
  const shelves = [];
  for (let i = 0; i < rows.length; i += 4) shelves.push(rows.slice(i, i + 4));
  const cheap = kind === "last";
  return `<div class="cs${cheap ? " cheap" : ""}" lang="en"><div class="cs-pane">${cheap ? CS_CRACK : ""}
    ${shelves.map(s => `<ul class="cs-shelf">${s.map(r => csSlotHTML(kind, r)).join("")}</ul>`).join("")}
  </div><div class="cs-rail"></div></div>`;
}

/* A season's final lineup in the sheet: starters with their points and the total, then the bench. */
function csOpenRoster(y, kind, originEl){
  const ros = csRoster(y, kind);
  const r = (kind === "champ" ? LG.champs : LG.spoons).find(x => x.y === y);
  if (!ros || !r) return;
  const bench = p => p.slot === "BN" || p.slot === "IR";
  // Position only: Yahoo's past pages give a moved player's team today, not that season's (ff-jarvis).
  const row = p => `<li><span class="cs-sl">${esc(p.slot || "")}</span><span class="cs-nm">${esc(p.name)}<small>${esc(p.pos || "")}</small></span>
    <span class="cs-pt">${p.pts == null ? "–" : lgPts(p.pts)}</span></li>`;
  const start = ros.players.filter(p => !bench(p)), rest = ros.players.filter(bench);
  const tot = start.reduce((s, p) => s + (p.pts || 0), 0);
  const mgr = lgHolder(r.mgr, r.id, r.name);
  const title = kind === "champ" ? t("records.case.sheet.champ", {y, mgr}) : t("records.case.sheet.last", {y, mgr});
  const sub = [r.name ? esc(r.name.trim()) : "", ros.week ? t("records.case.sheet.week", {wk: ros.week}) : ""].filter(Boolean).join(" · ");
  const d = document.getElementById("modal");
  d.innerHTML = `<div class="dr-head">
      <button type="button" class="dr-close" aria-label="${t("common.action.close")}">✕</button>
      <h3 id="cs-sheet-title" class="bp2-sheet-t">${title}</h3>
    </div><div class="dr-body cs-roster">
      <div class="cs-roster-hd">${kind === "champ" ? CS_CUP : CS_TOILET}<p><b>${sub}</b>${t("records.case.sheet.note")}</p></div>
      <ol class="cs-list">${start.map(row).join("")}
        <li class="tot"><span class="cs-sl"></span><span class="cs-nm">${t("records.case.sheet.total")}</span><span class="cs-pt">${lgPts(tot)}</span></li></ol>
      ${rest.length ? `<p class="cs-bench">${t("records.case.sheet.bench")}</p><ol class="cs-list">${rest.map(row).join("")}</ol>` : ""}
    </div>`;
  showModal(d, originEl, "cs-sheet-title");
}

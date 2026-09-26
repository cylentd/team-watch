function marketHead(){
  // DFS only since 2026-09-25: Build is the props market, and its view name is its heading. The DFS
  // pool keeps its line since its cap/salary source is specific to the site toggled.
  const site = dfsSite();
  const when = site.when;
  return `<div class="mkthead">
    <div>
      <span class="lbl">${t("dfs.market.heading", {site: site.label})}</span>
      <div class="mktsrc">${t("dfs.market.source", {n: site.pool.length, cap: site.cap.toLocaleString()})}${site.key==="yahoo" && !LIVE_YAHOO_DFS ? ` · ${t("dfs.market.sample")}` : ""}
          ${site.key === "yahoo" && LIVE_YAHOO_DFS && typeof LIVE_YAHOO_DFS.modeled === "number"
              ? ` · ${t("dfs.market.modeled", {n: LIVE_YAHOO_DFS.modeled})}`
                + (LIVE_YAHOO_DFS.lined ? `, ${t("dfs.market.lined", {n: LIVE_YAHOO_DFS.lined})}` : "")
                + `, ${t("dfs.market.rest")}` : ""}</div>
    </div>
    <span class="pill ${when?"":"warn"}">${when ? t("dfs.market.fetched", {when: esc(when)}) : t("dfs.market.noExport")}</span>
  </div>`;
}

/* "How this works" for Parlay and DFS: a small button beside the book/site toggle that opens the
   steps in the drawer. It used to be a collapsed card above the gallery, which still cost a full
   row of height before the slips and lineups -- the part of the page worth seeing first. */
const INFO_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16.5"/><circle cx="12" cy="7.6" r=".6" fill="currentColor"/></svg>`;
function explainButtonHTML(kind){
  return `<button type="button" class="explain-btn" data-explain="${kind}" aria-label="${t("builder.explain.title")}">${INFO_ICON}<span>${t("builder.explain.title")}</span></button>`;
}
function openExplain(kind){
  const d = document.getElementById("drawer");
  d.innerHTML = `
    <div class="dr-head">
      <button type="button" class="dr-close" aria-label="${t("common.action.close")}">✕</button>
      <div class="dr-id"><div><h3 id="ex-title">${t("builder.explain.title")}</h3></div></div>
    </div>
    <div class="dr-body"><div class="ex-body">${explainBody(kind)}</div></div>`;
  showDrawer(d, "ex-title");
}
function explainBody(kind){
  const parlay = kind === "parlay";
  return `
      ${parlay ? `<ol>
        <li>${t("parlay.explain.step1")}</li>
        <li>${t("parlay.explain.step2")}</li>
        <li>${t("parlay.explain.step3")}</li>
      </ol>
      <p class="ex-note">${t("parlay.explain.note")}</p>`
      : `<ol>
        <li>${t("dfs.explain.step1")}</li>
        <li>${t("dfs.explain.step2")}</li>
        <li>${t("dfs.explain.step3")}</li>
      </ol>
      <p class="ex-note">${t("dfs.explain.note")}</p>`}`;
}


function marketHead(kind){
  // The props market used to repeat line/player/game counts and a fetched timestamp here --
  // exactly what the topbar's DATA status pill and dropdown already say once, globally. Showing
  // the work twice reads as "trust us," not as more trustworthy; the DFS pool keeps its line
  // since its cap/salary source is specific to the site toggled, not covered by that dropdown.
  if (kind === "props") return `<div class="mkthead"><div><span class="lbl">${t("parlay.market.heading")}</span></div></div>`;
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

/* A short, collapsed-by-default "how this works" card at the top of Parlay and DFS. Open
   state survives a re-render (e.g. paging the pool) but never triggers one on its own --
   <details> animates itself, so the toggle listener only records what happened. */
let EXPLAIN = {parlay:false, dfs:false};
function explainHTML(kind){
  const parlay = kind === "parlay";
  return `<details class="explain" data-explain="${kind}" ${EXPLAIN[kind]?"open":""}>
    <summary><span class="lbl">${t("builder.explain.title")}</span><span class="ex-chev">▾</span></summary>
    <div class="ex-body">
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
      <p class="ex-note">${t("dfs.explain.note")}</p>`}
    </div>
  </details>`;
}


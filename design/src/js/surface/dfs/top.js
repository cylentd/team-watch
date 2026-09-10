function topLineupsHTML(){
  const site = dfsSite();
  const lineups = topLineups();
  return `<div class="rule"><h2>${t("dfs.top.heading", {n: TOP_COUNT})}</h2><span class="hair"></span>
    <span class="side">${t("dfs.top.sub")}</span></div>
  <div class="strategy">
    <button class="strat-btn" data-topmode="greedy" aria-pressed="${TOP_MODE==="greedy"}">
      <span class="st-name">${t("dfs.top.greedy")}</span><span class="st-sub">${t("dfs.top.greedySub")}</span>
    </button>
    <button class="strat-btn" data-topmode="contrarian" aria-pressed="${TOP_MODE==="contrarian"}">
      <span class="st-name">${t("dfs.top.contrarian")}</span><span class="st-sub">${t("dfs.top.contrarianSub")}</span>
    </button>
  </div>
  ${lineups.length ? `
  <div class="rail" data-railkey="dfs-lineups"><div class="railscroll">${lineups.map((l,i)=>lineupCard(l,i,site.cap)).join("")}</div></div>`
  : `<div class="state-empty" style="min-height:120px"><div><b>0</b><span>${t("dfs.top.empty")}</span></div></div>`}`;
}


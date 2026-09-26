function topLineupsHTML(){
  const site = dfsSite();
  const lineups = topLineups();
  // The strategy moved to the bar (dfsBarHTML). The lineups stack down the page on a phone and
  // sit three across on a desktop: no sideways rail inside a page that scrolls down (STYLE.md).
  return `${lineups.length ? `
  <div class="lu-grid">${lineups.map((l,i)=>lineupCard(l,i,site.cap)).join("")}</div>`
  : `<div class="state-empty" style="min-height:120px"><div><b>0</b><span>${t("dfs.top.empty")}</span></div></div>`}`;
}


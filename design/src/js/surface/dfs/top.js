function topLineupsHTML(){
  const site = dfsSite();
  const lineups = topLineups();
  return `<div class="rule"><h2>Top ${TOP_COUNT} lineups</h2><span class="hair"></span>
    <span class="side">randomized-greedy, not exact-optimal</span></div>
  <div class="strategy">
    <button class="strat-btn" data-topmode="greedy" aria-pressed="${TOP_MODE==="greedy"}">
      <span class="st-name">Greedy</span><span class="st-sub">Max points</span>
    </button>
    <button class="strat-btn" data-topmode="contrarian" aria-pressed="${TOP_MODE==="contrarian"}">
      <span class="st-name">Non-chalk</span><span class="st-sub">For GPPs</span>
    </button>
  </div>
  ${lineups.length ? `
  <div class="rail" data-railkey="dfs-lineups"><div class="railscroll">${lineups.map((l,i)=>lineupCard(l,i,site.cap)).join("")}</div></div>`
  : `<div class="state-empty" style="min-height:120px"><div><b>0</b><span>NOT ENOUGH PRICED PLAYERS AT EVERY POSITION TO FILL A LINEUP</span></div></div>`}`;
}


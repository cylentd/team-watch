function marketHead(kind){
  // The props market used to repeat line/player/game counts and a fetched timestamp here --
  // exactly what the topbar's DATA status pill and dropdown already say once, globally. Showing
  // the work twice reads as "trust us," not as more trustworthy; the DFS pool keeps its line
  // since its cap/salary source is specific to the site toggled, not covered by that dropdown.
  if (kind === "props") return `<div class="mkthead"><div><span class="lbl">Player prop market</span></div></div>`;
  const site = dfsSite();
  const when = site.when;
  return `<div class="mkthead">
    <div>
      <span class="lbl">${site.label} DFS player pool</span>
      <div class="mktsrc">${site.pool.length} players · $${site.cap.toLocaleString()} cap · salaries as posted${site.key==="yahoo" && !LIVE_YAHOO_DFS ? " · SAMPLE" : ""}
          ${site.key === "yahoo" && LIVE_YAHOO_DFS && typeof LIVE_YAHOO_DFS.modeled === "number"
              ? ` · projections: the model for ${LIVE_YAHOO_DFS.modeled}`
                + (LIVE_YAHOO_DFS.lined ? `, the book's line for ${LIVE_YAHOO_DFS.lined} with no game log (LINE)` : "")
                + `, Yahoo's FPPG rescaled for the rest (Y)` : ""}</div>
    </div>
    <span class="pill ${when?"":"warn"}">${when ? `Fetched ${esc(when)}` : "No salary export loaded"}</span>
  </div>`;
}

/* A short, collapsed-by-default "how this works" card at the top of Parlay and DFS. Open
   state survives a re-render (e.g. paging the pool) but never triggers one on its own --
   <details> animates itself, so the toggle listener only records what happened. */
let EXPLAIN = {parlay:false, dfs:false};
function explainHTML(kind){
  const parlay = kind === "parlay";
  return `<details class="explain" data-explain="${kind}" ${EXPLAIN[kind]?"open":""}>
    <summary><span class="lbl">How this works</span><span class="ex-chev">▾</span></summary>
    <div class="ex-body">
      ${parlay ? `<ol>
        <li>Browse the model's best slips below — each card is one scope (yards, TDs, or both) inside one kickoff window, and never mixes two days.</li>
        <li>Tap <b>Load into my slip</b> to start from one, or scroll to the lines and tap any player to add a leg yourself.</li>
        <li>Your slip prices itself as you go. <b>Copy slip</b> puts it on the clipboard, ready to type into the book.</li>
      </ol>
      <p class="ex-note"><b>MODEL %</b> is the chance the over hits, from the player's last 24 games, nudged by what his opponent allows to his position. <b>EDGE</b> is model % minus the book's break-even, in points — +5 means the model likes the over 5 points more than the price needs. Both live behind each line's chevron, not on the card.</p>`
      : `<ol>
        <li><b>Greedy</b> builds the highest-projected lineup — what most of the field lands on. <b>Non-chalk</b> sits the single most-projected play at each position and trades a little projection for a lineup the field isn't all rostering, which is the point of a GPP.</li>
        <li>Swipe the lineups below, tap <b>Load into my lineup</b> to start from one.</li>
        <li>Fill or swap slots from the pool underneath.</li>
      </ol>
      <p class="ex-note"><b>PROJ</b> is the model's fantasy points on Yahoo scoring — its yards, receptions and touchdown rates for this week, half-PPR, for every player it has a rate for and not only the ones a book prices. A player with no game log at all (a rookie) wears a <b>LINE</b>: his own line this week, read as a role. Whoever is left — the deep bench, K, DST — wears a <b>Y</b>: Yahoo's last-season average, rescaled to the model's level at his position, a placeholder rather than a read. No site publishes real ownership before lock — PROJ OWN is a rank-based estimate, same idea any pre-lock ownership projection tool uses.</p>`}
    </div>
  </details>`;
}


/* The topbar badge used to say "Sample data" unconditionally, even on Parlay/DFS once props
   and the Yahoo DFS pool went live -- it never checked what was actually loaded. This does. */
function topbarBadge(){
  if (SURFACE === "parlay"){
    return LIVE_MARKET
      ? {tone:"live", full:t("chrome.badge.parlayLiveFull"), abbr:t("chrome.badge.parlayLiveAbbr")}
      : {tone:"warn", full:t("chrome.badge.parlaySampleFull"), abbr:t("chrome.badge.sampleAbbr")};
  }
  if (SURFACE === "dfs"){
    const live = dfsSite().key === "yahoo" && !!LIVE_YAHOO_DFS;
    return live
      ? {tone:"live", full:t("chrome.badge.dfsLiveFull"), abbr:t("chrome.badge.dfsLiveAbbr")}
      : {tone:"warn", full:t("chrome.badge.dfsSampleFull"), abbr:t("chrome.badge.sampleAbbr")};
  }
  if (SURFACE === "news")
    return LIVE_NEWS
      ? {tone:"live", full:t("chrome.badge.newsLiveFull"), abbr:t("chrome.badge.newsLiveAbbr")}
      : {tone:"warn", full:t("chrome.badge.newsSampleFull"), abbr:t("chrome.badge.sampleAbbr")};
  return LIVE_SIGNALS
    ? {tone:"live", full:t("chrome.badge.teamsLiveFull"), abbr:t("chrome.badge.teamsLiveAbbr")}
    : {tone:"warn", full:t("chrome.badge.defaultFull"), abbr:t("chrome.badge.sampleAbbr")};
}
/* Shown only when a view runs on sample data (2026-09-25). "Live" is the normal state, and a pill
   announcing the normal state on every view is one more thing competing for the eye. */
function paintBadge(){
  const b = topbarBadge(), el = document.getElementById("topbadge");
  el.hidden = b.tone === "live";
  el.classList.toggle("warn", b.tone==="warn");
  el.classList.toggle("live", b.tone==="live");
  el.querySelector(".full").textContent = b.full;
  el.querySelector(".abbr").textContent = b.abbr;
}

/* Until a reader picks a team, Roster asks which (teamswitch.js pickHTML). Waivers does not (2026-10-05, the
   League merge): the wire is the league's, not the team's, so it opens on the league's public list under the
   chip. David's own browser has no such list: it asks. */
function renderAsk(v){
  const wire = SURFACE === "waivers" && !isOwner();
  v.dataset.view = wire ? "waivers" : "pick";
  v.innerHTML = wire ? wvPublicHTML() : pickHTML();
  if (wire){ wireHot(v); wireLgChip(v); } else wirePick(v);
}

function render(){
  const v = document.getElementById("view");
  v.dataset.view = SURFACE;   // the view drawn, which its CSS is fenced to (design/scope_css.py)
  paintBadge();
  markEnter(v);

  if (SURFACE === "news"){
    v.innerHTML = newsHTML();
    wireNews(v);
    return;
  }
  if (SURFACE === "live"){
    /* liveHTML() kicks off a fetch when what it has is stale, and paintLive() redraws the board
       in place when the reply lands -- render() is never called again for a poll. */
    v.innerHTML = liveHTML();
    wireLive(v);
    return;
  }
  if (SURFACE === "board"){
    v.innerHTML = bdViewHTML(); wireBd(v);
    return;
  }
  /* Views that are one HTML function and one wiring function. `movers` is Role (2026-09-29). */
  const plain = {ranks: [ranksHTML, wireRanks], digest: [digestHTML, wireDigest], matchups: [matchupsHTML, wireMatchups],
    movers: [rvViewHTML, wireRv], highlights: [hlViewHTML, wireHl], weekrecap: [wrViewHTML, wireWeekRecap],
    weather: [wtViewHTML, wireWeather], preview: [pvViewHTML, wirePreview], recap: [lgRecapPageHTML, wireRecapPage], records: [lgRecordsPageHTML, wireRecords], trades: [tfViewHTML, wireTf],
    teams: [lbViewHTML, wireLb], schedule: [sosPageHTML, wireSos]}[SURFACE];
  if (plain){ v.innerHTML = plain[0](); plain[1](v); return; }
  if (SURFACE === "usage"){
    v.innerHTML = usageHTML(); wireUsage(v); nudgeScrollers(v);
    return;
  }
  if (SURFACE === "parlay" || SURFACE === "build" || SURFACE === "dfs"){
    v.innerHTML = SURFACE === "dfs" ? dfsSurfaceHTML() : parlayHTML();
    wireBuilder(v);
    if (SURFACE !== "dfs") wireBets(v); else wireDfsBar(v);
    nudgeScrollers(v);
    return;
  }
  if (needsPick()) return renderAsk(v);
  const team = TEAMS[VIEW] || TEAMS.yahoo;
  // A connected league has no Waivers (nav.js hides the tab); a stale #waivers draws its roster.
  const wire = SURFACE === "waivers" && hasWaivers(team);
  v.dataset.view = wire ? "waivers" : "roster";
  const reel = wire ? "" : reelHTML(team);   // the Week plays reel, above the "This week" list (reel.js)
  // The deal and the rail's "new" flash are taken once per page load, on the first Waivers render.
  // The League team line (surface/league/switch.js) heads both, as it heads every League leaf.
  v.innerHTML = wire
    ? `<div class="wrap">${lgChipHTML(waiverHeroHTML(team), team)}${waiverHTML(wvMotionTake())}</div>`
    : `<div class="wrap">${lgChipHTML(rosterModeHTML(), team)}</div><div class="wrap rl${reel ? " rl-reel" : ""}">${reel}${briefHTML(team)}<div class="rl-rows">${
        ROSTER_MODE === "cards" ? cardsHTML(team) : boardHTML(team)}</div></div>`;
  if (!wire){ wireBrief(v); wireReel(v, team); wireRosterMode(v, team); wirePack(v, team); }
  wireLgChip(v);
  wireProfiles(v);
  if (wire) wireWaivers(v);
}


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

function render(){
  const v = document.getElementById("view");
  paintBadge();
  markEnter(v);

  if (SURFACE === "news"){
    v.innerHTML = newsHTML();
    v.querySelectorAll("[data-newscat]").forEach(b=>b.addEventListener("click",()=>{
      NEWS_CAT = b.dataset.newscat; render();
    }));
    return;
  }
  if (SURFACE === "live"){
    /* liveHTML() kicks off a fetch when what it has is stale, and paintLive() redraws the board
       in place when the reply lands -- render() is never called again for a poll. */
    v.innerHTML = liveHTML();
    wireLive(v);
    return;
  }
  if (SURFACE === "board" || SURFACE === "movers"){
    BD_MODE = SURFACE === "movers" ? "movers" : "leaders";
    v.innerHTML = bdViewHTML(); wireBd(v);
    return;
  }
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

  const team = TEAMS[VIEW] || TEAMS.yahoo;
  // A connected league has no Waivers (nav.js hides the tab); a stale #waivers draws its roster.
  const wire = SURFACE === "waivers" && !team.connected;
  // The deal and the rail's "new" flash are taken once per page load, on the first Waivers render.
  v.innerHTML = wire
    ? heroHTML(team) + `<div class="wrap">${waiverHTML(wvMotionTake())}</div>`
    : heroHTML(team, rosterModeHTML(team)) + `<div class="wrap rl">${briefHTML(team)}<div class="rl-rows">${
        ROSTER_MODE === "cards" ? packHTML(team) + cardsHTML(team) : boardHTML(team)}</div></div>`;
  fitTitle(v);
  if (!wire){ wireBrief(v); wireRosterMode(v, team); wirePack(v, team); }
  v.querySelector(".leaguechip")?.addEventListener("click", ()=>openLeagueInfo(team.key));
  wireTeamSwitch(v);
  wireProfiles(v);
  if (wire) wireWaivers(v);
}


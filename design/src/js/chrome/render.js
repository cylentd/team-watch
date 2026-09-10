/* The topbar badge used to say "Sample data" unconditionally, even on Parlay/DFS once props
   and the Yahoo DFS pool went live -- it never checked what was actually loaded. This does. */
function topbarBadge(){
  if (SURFACE === "parlay"){
    return LIVE_MARKET
      ? {tone:"live", full:"Live props · trend, rank & news still sample", abbr:"Props live"}
      : {tone:"warn", full:"Sample props — BettingPros not pulled", abbr:"Sample data"};
  }
  if (SURFACE === "dfs"){
    const live = dfsSite().key === "yahoo" && !!LIVE_YAHOO_DFS;
    return live
      ? {tone:"live", full:"Live Yahoo pool · rest of app sample", abbr:"Pool live"}
      : {tone:"warn", full:"Sample DFS pool — no salary export loaded", abbr:"Sample data"};
  }
  if (SURFACE === "news")
    return LIVE_NEWS
      ? {tone:"live", full:"Live news", abbr:"News live"}
      : {tone:"warn", full:"Sample news — scanner not pulled", abbr:"Sample data"};
  return {tone:"warn", full:"Sample signals — skill not wired", abbr:"Sample data"};
}
function paintBadge(){
  const b = topbarBadge(), el = document.getElementById("topbadge");
  el.classList.toggle("warn", b.tone==="warn");
  el.classList.toggle("live", b.tone==="live");
  el.querySelector(".full").textContent = b.full;
  el.querySelector(".abbr").textContent = b.abbr;
}

function render(){
  const v = document.getElementById("view");
  paintBadge();

  if (SURFACE === "news"){
    v.innerHTML = newsHTML();
    v.querySelectorAll("[data-newscat]").forEach(b=>b.addEventListener("click",()=>{
      NEWS_CAT = b.dataset.newscat; render();
    }));
    return;
  }
  if (SURFACE === "pool"){
    v.innerHTML = poolHTML();
    v.querySelectorAll(".chip[data-pos]").forEach(b=>b.addEventListener("click",()=>{
      POOL_FILTER = b.dataset.pos; POOL_PAGE = 1; render();
    }));
    v.querySelectorAll("[data-poolpage]").forEach(b=>b.addEventListener("click",()=>{
      POOL_PAGE = Math.max(1, POOL_PAGE + (b.dataset.poolpage === "next" ? 1 : -1));
      const y = window.scrollY; render(); window.scrollTo(0, y);
    }));
    v.querySelectorAll("[data-pool]").forEach(el=>{
      const open = ()=>openPoolDrawer(+el.dataset.pool);
      el.addEventListener("click", open);
      el.addEventListener("keydown", e=>{ if(e.key==="Enter"||e.key===" "){e.preventDefault();open();} });
    });
    v.querySelectorAll(".dotg").forEach(g=>g.addEventListener("click",()=>openPoolDrawer(+g.dataset.i)));
    nudgeScrollers(v);
    return;
  }
  if (SURFACE === "parlay" || SURFACE === "dfs"){
    v.innerHTML = SURFACE === "parlay" ? parlayHTML() : dfsSurfaceHTML();
    wireBuilder(v);
    nudgeScrollers(v);
    return;
  }

  const team = TEAMS[VIEW];
  v.innerHTML = heroHTML(team) + tickerHTML() + `<div class="wrap">
    ${boardHTML(team)}
    <div class="rule"><h2>The wire</h2><span class="hair"></span><span class="side">waiver replacements</span></div>
    ${wireHTML()}
  </div>`;
  v.querySelector(".leaguechip")?.addEventListener("click", ()=>openLeagueInfo(team.key));
  wireTeamSwitch(v);
  document.querySelectorAll(".row").forEach(r=>{
    r.addEventListener("click", ()=>openDrawer(r.dataset.team, +r.dataset.i));
    r.addEventListener("keydown", e=>{ if(e.key==="Enter"||e.key===" "){e.preventDefault();openDrawer(r.dataset.team,+r.dataset.i);} });
  });
}


/* ============================== LEAGUE ==============================
   My teams > League for the team on screen: the week (recap.js), then the rivalry and the league's
   history (history.js). One column on a phone; beside each other from 960px. */

function leagueHTML(team){
  if (!LG) return `<p class="lg-none">${t("league.none")}</p>`;
  const id = lgIdOf(team);
  return `<div class="lg">
    <div class="lg-col">${lgRecapHTML(id)}${lgRivalHTML(id)}</div>
    <div class="lg-col">${lgHistoryHTML()}</div>
  </div>`;
}

/* The whole view under the roster's own hero, so the team switch stays on top (render.js). */
function renderLeague(v, team){
  v.innerHTML = heroHTML(team) + `<div class="wrap">${leagueHTML(team)}</div>`;
  fitTitle(v); wireLeague(v, team); wireTeamSwitch(v);
  v.querySelector(".leaguechip")?.addEventListener("click", ()=>openLeagueInfo(team.key));
}

/* A week chip redraws only the recap section in place: the rivalry and history below never move. */
function wireLeague(v, team){
  v.querySelectorAll("[data-lgweek]").forEach(b => b.addEventListener("click", () => {
    LG_WEEK = Number(b.dataset.lgweek);
    const sec = b.closest(".lg-sec");
    sec.outerHTML = lgRecapHTML(lgIdOf(team));
    wireLeague(v, team);
  }));
}

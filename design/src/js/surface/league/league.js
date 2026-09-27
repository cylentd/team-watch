/* ============================== LEAGUE (ESPN) ==============================
   My teams > League for an ESPN team: the plain recap (recap.js), rivalry and history (history.js).
   ESPN is David's work league. The Yahoo league, the one his friends read, has This week > League and
   Records (back.js, records.js), the same for every reader, and My teams > My recap (myrecap.js).
   One column on a phone; beside each other from 960px. */

function leagueHTML(team){
  const L = lgOf(team);
  if (L !== LG){ LG = L; LG_WEEK = null; LG_OPEN = null; }   // the other league's weeks are its own
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
  const id = lgIdOf(team);   // after leagueHTML, which sets LG: the id is looked up in the league on screen
  fitTitle(v); wireLeague(v, id, () => lgRecapHTML(id)); wireTeamSwitch(v);
  v.querySelector(".leaguechip")?.addEventListener("click", ()=>openLeagueInfo(team.key));
}

/* One listener on the view's own container (rebuilt on every render, so it never stacks), for every
   league page. Each control redraws only its own part in place, so nothing above it moves: a week
   chip the week section (`weekHTML`, the page's own), a box toggle its one card, the margins toggle
   its grudge card. The arrival motion
   is for a new week only, so any tap first takes it off. */
function wireLeague(v, id, weekHTML){
  const root = v.querySelector(".lg");
  if (!root) return;
  root.addEventListener("click", e => {
    const b = e.target.closest("[data-lgweek],[data-lgbox],[data-lgmargins]");
    if (!b) return;
    root.querySelector(".bp-in")?.classList.remove("bp-in");
    if (b.hasAttribute("data-lgmargins")){
      const card = b.closest(".bp-gcard");
      LG_MARGINS = !LG_MARGINS;
      card.outerHTML = lgGrudgeCardHTML(Number(card.dataset.a), Number(card.dataset.b));
    } else if (b.dataset.lgweek){
      LG_WEEK = Number(b.dataset.lgweek); LG_OPEN = null;
      b.closest(".lg-sec").outerHTML = weekHTML();
    } else {
      const k = b.dataset.lgbox, g = lgWeek().games.find(x => lgKey(x) === k);
      lgToggleBox(k, id);
      b.closest(".bp-game").outerHTML = lgGameHTML(g, id, 0);
    }
  });
}

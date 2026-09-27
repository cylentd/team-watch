/* ============================== LEAGUE ==============================
   My teams > League for the team on screen. Yahoo, the league David's friends read, is the back page
   (back.js, slate.js, tape.js, book.js; since 2026-09-27). ESPN keeps the plain recap (recap.js),
   rivalry and history (history.js). One column on a phone; beside each other from 960px. */

function leagueHTML(team){
  const L = lgOf(team);
  if (L !== LG){ LG = L; LG_WEEK = null; LG_OPEN = null; }   // the other league's weeks are its own
  if (!LG) return `<p class="lg-none">${t("league.none")}</p>`;
  const id = lgIdOf(team);
  if (LG === LGS.yahoo){
    LG_ME = id;
    return `<div class="lg bp">
      <div class="lg-col">${lgBackWeekHTML(id)}</div>
      <div class="lg-col">${lgTapeHTML(id)}${lgBookHTML()}</div>
    </div>`;
  }
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

/* One listener on the view's own container (rebuilt on every render, so it never stacks). Each
   control redraws only its own part in place, so nothing above it moves: a week chip the week, a box
   toggle its one card, a record-book tab the book. The arrival motion is for a new week only, so any
   tap first takes it off the section. */
function wireLeague(v, team){
  const root = v.querySelector(".lg"), id = lgIdOf(team);
  if (!root) return;
  root.addEventListener("click", e => {
    const b = e.target.closest("[data-lgweek],[data-lgbox],[data-lgbook]");
    if (!b) return;
    root.querySelector(".bp-in")?.classList.remove("bp-in");
    if (b.dataset.lgweek){
      LG_WEEK = Number(b.dataset.lgweek); LG_OPEN = null;
      const sec = b.closest(".lg-sec");
      sec.outerHTML = sec.classList.contains("bp-week") ? lgBackWeekHTML(id) : lgRecapHTML(id);
    } else if (b.dataset.lgbox){
      const k = b.dataset.lgbox, g = lgWeek().games.find(x => lgKey(x) === k);
      lgToggleBox(k, id);
      b.closest(".bp-game").outerHTML = lgGameHTML(g, id, 0);
    } else {
      LG_BOOK = b.dataset.lgbook;
      b.closest(".lg-sec").outerHTML = lgBookHTML();
    }
  });
}

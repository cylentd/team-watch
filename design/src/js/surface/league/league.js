/* ============================== LEAGUE (ESPN) ==============================
   My teams > League for an ESPN team: the plain recap (recap.js), rivalry and history (history.js).
   ESPN is David's work league. The Yahoo league, the one his friends read, has This week > League and
   Records (back.js, records.js), the same for every reader, and My teams > My recap (myrecap.js).
   One column on a phone; beside each other from 960px. */

function leagueHTML(team){
  const L = lgOf(team);
  if (L !== LG){ LG = L; LG_WEEK = null; }   // the other league's weeks are its own
  if (!LG) return `<p class="lg-none">${t("league.none")}</p>`;
  const id = lgIdOf(team);
  return `<div class="lg">
    <div class="lg-col">${lgRecapHTML(id)}${lgRivalHTML(id)}</div>
    <div class="lg-col">${lgHistoryHTML()}</div>
  </div>`;
}

/* The team the ESPN page is about: the reader's when it plays in league `f`, else David's own there. */
const lgEspnTeam = f => lgFocusKey() === f && lgSeat() && !lgSeat().connected ? lgSeat() : TEAMS[f];

/* The ESPN league's Recap (2026-10-05; it was My teams > League, under the roster's hero): the chip on top,
   so the team switch stays within reach. The page is the team on screen's game, rivalry and history. */
function lgEspnPageHTML(f){
  return `<div class="wrap">${lgChipHTML()}${leagueHTML(lgEspnTeam(f))}</div>`;
}
function wireEspnPage(v, f){
  const id = lgIdOf(lgEspnTeam(f));   // after leagueHTML, which sets LG: the id is looked up in the league on screen
  wireLeague(v, () => lgRecapHTML(id)); wireLgChip(v);
}

/* One listener on the view's own container (rebuilt on every render, so it never stacks), for every
   league page. Each control redraws only its own part in place, so nothing above it moves: a week
   chip or the stepper the week section (`weekHTML`, the page's own), the margins toggle its grudge
   card; a game's sheet and Share open over the page. The arrival motion is for a new week only, so
   any tap first takes it off. */
function wireLeague(v, weekHTML){
  const root = v.querySelector(".lg");
  if (!root) return;
  if (root.querySelector("[data-lgshare]")) lgShareWarm(lgWeek());
  root.addEventListener("click", e => {
    const b = e.target.closest("[data-lgweek],[data-lgmargins],[data-lgsheet],[data-lgshare]");
    if (!b) return;
    root.querySelector(".bp-in")?.classList.remove("bp-in");
    if (b.dataset.lgsheet){
      lgOpenGameSheet(lgWeek().games.find(x => lgKey(x) === b.dataset.lgsheet), b);
    } else if (b.hasAttribute("data-lgshare")){
      lgShare(lgWeek(), b);
    } else if (b.hasAttribute("data-lgmargins")){
      const card = b.closest(".bp-gcard");
      LG_MARGINS = !LG_MARGINS;
      card.outerHTML = lgGrudgeCardHTML(Number(card.dataset.a), Number(card.dataset.b));
    } else if (b.dataset.lgweek){
      const forward = b.classList.contains("lg-step-next");
      LG_WEEK = Number(b.dataset.lgweek);
      (b.closest("[data-lgroot]") || b.closest(".lg-sec")).outerHTML = weekHTML();
      if (root.querySelector("[data-lgshare]")) lgShareWarm(lgWeek());
      // The button that was tapped is gone with the old stepper: keep the keyboard on the same side.
      const step = root.querySelector(forward ? ".lg-step-next:not([disabled])" : ".lg-step-prev:not([disabled])");
      if (step) step.focus({preventScroll: true});
    }
  });
}

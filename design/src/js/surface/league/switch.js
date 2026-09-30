/* ============================== LEAGUE > THE LEAGUE SWITCH ==============================
   2026-09-29, the third league (David: "a switch on the page"). Recap, Records and Trades each show one
   of David's Yahoo leagues, the Madden Curse or AYO, picked by two chips above the page and kept in
   this browser (data/league.js lgLeagueKey). One row of controls, the same chips as the week's
   (STYLE.md). Hidden with one league: a switch of one is a label pretending to be a choice. */

/* Each league's label spelled out, so assemble.py --check sees the keys; a league added later with no
   label reads its own name from its data. */
const lgSwitchLabel = k => ({yahoo: t("league.switch.yahoo"), ayo: t("league.switch.ayo")})[k] || esc(LGS[k].league);

/* The picked league's colour, for the back page's rule and kicker (back.css --lg-tint). */
const lgTint = () => (TEAMS[lgLeagueKey()] || TEAMS.yahoo).tint;

function lgSwitchHTML(){
  const ks = lgLeagueKeys(), on = lgLeagueKey();
  if (ks.length < 2) return "";
  return `<div class="setrow lg-switch" role="group" aria-label="${t("league.switch.aria")}">${ks.map(k =>
    `<button type="button" class="chip" data-lgpick="${esc(k)}" aria-pressed="${k === on}">${lgSwitchLabel(k)}</button>`).join("")}</div>`;
}

/* A pick redraws the view on the other league. What the view held (its week, an open manager, a picked
   head to head) belongs to the league it came from, so each starts over; focus stays on the chip. */
function wireLgSwitch(v){
  v.querySelectorAll("[data-lgpick]").forEach(b => b.addEventListener("click", () => {
    const k = b.dataset.lgpick;
    if (k === lgLeagueKey()) return;
    lgLeagueSave(k);
    TR_OPEN = null; RC_MGR = null;
    render();
    v.querySelector(`[data-lgpick="${CSS.escape(k)}"]`)?.focus();
  }));
}

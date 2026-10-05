/* ============================== LEAGUE > THE LEAGUE SWITCH ==============================
   2026-09-29, the third league (David: "a switch on the page"). Recap, Records and Trades each show one
   of David's Yahoo leagues, the Madden Curse or AYO, picked by two chips above the page and kept in
   this browser (data/league.js lgLeagueKey). One row of controls, the same chips as the week's
   (STYLE.md). Hidden with one league: a switch of one is a label pretending to be a choice. */

/* Each league's label spelled out, so assemble.py --check sees the keys; a league added later with no
   label reads its own name from its data. */
const lgSwitchLabel = k => ({yahoo: t("league.switch.yahoo"), ayo: t("league.switch.ayo"), espn: t("league.switch.espn")})[k] || esc(LGS[k].league);

/* The picked league's colour, for the back page's rule and kicker (back.css --lg-tint). */
const lgTint = () => (TEAMS[lgLeagueKey()] || TEAMS.yahoo).tint;

/* The chips for `ks` with `on` pressed: Recap, Records and Trades list the Yahoo leagues and read the
   saved pick; Teams (surface/lboard/) passes all three and its own pick (2026-10-05). */
function lgSwitchHTML(ks = lgLeagueKeys(), on = lgLeagueKey()){
  if (ks.length < 2) return "";
  return `<div class="setrow lg-switch" role="group" aria-label="${t("league.switch.aria")}">${ks.map(k =>
    `<button type="button" class="chip" data-lgpick="${esc(k)}" aria-pressed="${k === on}">${lgSwitchLabel(k)}</button>`).join("")}</div>`;
}

/* Recap's pick: saved in this browser, and what the view held (an open manager, a picked head to head)
   belongs to the league it came from, so each starts over. False when it is already the league on screen. */
function lgPickSaved(k){
  if (k === lgLeagueKey()) return false;
  lgLeagueSave(k);
  TR_OPEN = null; RC_MGR = null;
  return true;
}

/* A pick redraws the view on the other league; focus stays on the chip. `pick` is the view's own rule. */
function wireLgSwitch(v, pick = lgPickSaved){
  v.querySelectorAll("[data-lgpick]").forEach(b => b.addEventListener("click", () => {
    const k = b.dataset.lgpick;
    if (!pick(k)) return;
    render();
    v.querySelector(`[data-lgpick="${CSS.escape(k)}"]`)?.focus();
  }));
}

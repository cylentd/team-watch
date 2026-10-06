/* ============================== LEAGUE > THE ONE CHIP ==============================
   2026-10-05 (David: merge Teams and League; "pick your team, the league follows"). It replaced the
   League switch of 2026-09-29 (two chips, the Madden Curse and AYO, saved as `tw-league`; ESPN joined
   them on the Teams board): the league was picked in two places, here and in the team switch. Now there
   is one control, the team switch (chrome/teamswitch.js) drawn as a chip above the page, and the league
   is the league of the team it names (data/league.js lgFocusKey). A reader who has picked no team sees
   "Pick your team" in it. The league's name sits beside it, so the page says whose book it is.
   Every League leaf draws it: Recap, Records, Trades, Teams; Roster and Waivers carry the same switch
   in their hero. */

/* Each league's label spelled out, so assemble.py --check sees the keys; a league added later with no
   label reads its own name from its data. */
const lgSwitchLabel = k => ({yahoo: t("league.switch.yahoo"), ayo: t("league.switch.ayo"), espn: t("league.switch.espn")})[k]
  || esc(((LGS[k] || {}).league) || k);

/* The picked league's colour, for the back page's rule and kicker (back.css --lg-tint). */
const lgTint = () => (TEAMS[lgLeagueKey()] || TEAMS.yahoo).tint;

function lgChipHTML(){
  const mine = lgMine(), k = lgFocusKey();
  return `<div class="lgchip">${teamSwitchHTML(mine ? esc(mine.name) : t("league.chip.pick"))}${
    k ? `<span class="lgchip-lg">${lgSwitchLabel(k)}</span>` : ""}</div>`;
}

/* The chip is the team switch: its own wiring, its own menu. A team picked there runs pickTeam
   (chrome/teamswitch.js), which redraws the view on the new team's league. */
const wireLgChip = v => wireTeamSwitch(v);

/* What a view held (an open manager, a picked head to head) belongs to the league it came from, so
   each starts over when the league changes. Called by pickTeam. */
function lgLeagueChanged(){
  TR_OPEN = null; RC_MGR = null;
}

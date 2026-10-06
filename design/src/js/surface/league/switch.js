/* ============================== LEAGUE > THE ONE CHIP ==============================
   2026-10-05 (David: merge Teams and League; "pick your team, the league follows"). It replaced the
   League switch of 2026-09-29 (two chips, the Madden Curse and AYO, saved as `tw-league`; ESPN joined
   them on the Teams board): the league was picked in two places, here and in the team switch. Now there
   is one control, the team switch (chrome/teamswitch.js) drawn as a chip above the page, and the league
   is the league of the team it names (data/league.js lgFocusKey). A reader who has picked no team sees
   "Pick your team" in it. The league's name sits beside it, so the page says whose book it is.
   Every League leaf draws it, Roster and Waivers too since their heroes went (2026-10-05). */

/* Each league's label spelled out, so assemble.py --check sees the keys; a league added later with no
   label reads its own name from its data. */
const lgSwitchLabel = k => ({yahoo: t("league.switch.yahoo"), ayo: t("league.switch.ayo"), espn: t("league.switch.espn")})[k]
  || esc(((LGS[k] || {}).league) || k);

/* The picked league's colour, for the back page's rule and kicker (back.css --lg-tint). */
const lgTint = () => (TEAMS[lgLeagueKey()] || TEAMS.yahoo).tint;

/* The team line, the same on all six League leaves at every width (2026-10-05, David: "the team selector is on
   every single tab and is also different"; storyboard https://claude.ai/artifact/WBatgHQtCYuVBPHykJcEQo). It
   replaced three shapes: Roster's hero title, Waivers' full hero with a second boxed switch, and this chip.
   The team switch as the title, then the league (its ⓘ opens the league's format) and the record. A phone
   hides the switch (chrome/phonenav.css): the header bar's is the one there. `side` is a view's own control at
   the line's right end: Roster's Sheet / Cards icons, Waivers' wire line. `team` is the team the line names:
   the reader's on a league page, the one on screen on Roster and Waivers (a profile's owner link opens
   another's, profile/owners.js). */
function lgChipHTML(side = "", team = lgMine()){
  const seat = team || lgSeat() || TEAMS.yahoo, k = team ? navFocusKey(team, lbKeys()) : lgFocusKey();
  const rec = team && team.record ? `<span class="lgchip-rec">${esc(team.record)}</span>` : "";
  const lg = k ? `<button type="button" class="lgchip-info" data-lginfo="${esc(seat.key)}"><span class="lgchip-lg">${
    lgSwitchLabel(k)}</span><span class="lc-info" aria-hidden="true">ⓘ</span></button>` : "";
  return `<div class="lgchip" style="--tint:${seat.tint}"><div class="lgchip-id">${
    teamSwitchHTML(team ? esc(team.name) : t("league.chip.pick"), team ? "" : "ts-pick")}${
    lg || rec ? `<div class="lgchip-sub">${lg}${rec}</div>` : ""}</div>${
    side ? `<div class="lgchip-side">${side}</div>` : ""}</div>`;
}

/* The line's own controls: the team switch (a team picked there runs pickTeam, chrome/teamswitch.js, which
   redraws the view on the new team's league) and the league's ⓘ. */
function wireLgChip(v){
  wireTeamSwitch(v);
  const b = v.querySelector(".lgchip [data-lginfo]");
  if (b) b.addEventListener("click", () => openLeagueInfo(b.dataset.lginfo));
}

/* What a view held (an open manager, a picked head to head) belongs to the league it came from, so
   each starts over when the league changes. Called by pickTeam. */
function lgLeagueChanged(){
  TR_OPEN = null; RC_MGR = null;
}

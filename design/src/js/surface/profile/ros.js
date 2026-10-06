/* The profile's Rest of season block (2026-10-06): what he is expected to score from the week still to play through week 17,
   his points a game, the games he is expected to play of his team's left ("9.8 of 12"), and his rank among his position
   by week as a line chart. Rank, never points: ROS points fall every week for everyone (data/ros.js).

   The numbers are ff-jarvis's (LIVE_ROS, METHODOLOGY 12.97). A reader whose team is in the ESPN league reads ESPN's, said
   in one line as not backtested; everyone else half-PPR. Nothing for a player the file does not list. It sits in the Season
   pane, under the table of his weeks. */
function rosProfileHTML(p){
  const block = rosBlock(), r = block && rosOne(block, p.slug, rosReaderScoring(block));
  if (!r) return "";
  const espn = rosReaderScoring(block) === "espn";
  const games = `<b>${r.games.toFixed(1)}</b> ${t("ros.profile.of", {of: r.of})}`;
  const body = `<div data-testid="profile-ros" class="pf-ros">
    <div class="pf-lead"><b data-testid="profile-ros-pts">${Math.round(r.pts)}</b><span data-testid="profile-ros-lead">${t("ros.profile.lead", {from: block.week, to: block.last_week, rank: r.rank, pos: esc(r.pos)})}</span></div>
    <div class="pfr-cells"><span class="pfr-cell"><b data-testid="profile-ros-pg">${r.pg.toFixed(1)}</b> ${t("ros.profile.pg")}</span>
      <span class="pfr-cell" data-testid="profile-ros-games">${games}</span></div>
    <div class="pfr-chart"><span class="lbl">${t("ros.profile.chart", {pos: esc(r.pos)})}</span>${rosLineHTML(r.hist, r.pos, ROS_PROFILE_BOX)}</div>
    <p class="pf-cap pf-fine" data-testid="profile-ros-note">${espn ? t("ros.profile.noteEspn") : t("ros.profile.noteHalf")}</p>
  </div>`;
  return secHTML(t("ros.profile.label"), body);
}

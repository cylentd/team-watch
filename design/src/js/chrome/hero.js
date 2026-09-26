/* Roster and Waivers used to be a pair of buttons docked in this hero. They moved up into the
   nav's sub-row when the nav went two-level, because two sub-tab rows on one screen -- one in
   the chrome, one in the page -- read as two different kinds of choice when they are the same
   kind. The hero keeps only what it is for: whose team this is. The roster's three KPI tiles
   (trending up, trending down, news) went on 2026-09-24: each counted something the rows below
   already show on their own, and on a phone they cost a screen-third before the first player.
   Since 2026-09-25 the roster's hero is the phone's one line at every width (.hero.team, hero.css):
   the team switch is the title. Waivers keeps the full hero, which carries its FAAB and claims. */
/* `side` sits at the hero's right end: the roster's Sheet / Cards switch (2026-09-25), moved up out
   of the rows' column so the starters, the bench and "This week" share one top edge. */
function heroHTML(team, side = ""){
  const wire = SURFACE === "waivers" && hasWaivers(team);
  const rec = team.record ? `${team.plat} · ${team.record}` : team.plat;   // a leaguemate's record is not pulled
  return `<section class="hero${wire ? "" : " team"}">
    <div class="numghost">${team.slot}</div>
    <div class="wrap hero-in">
      <div>
        <div class="hero-eyebrow" style="--tint:${team.tint}">
          <span class="league-mark"></span>
          <span class="lbl">${rec}</span>
          ${teamSwitchHTML()}
        </div>
        <h1 class="fit">${esc(team.name)}</h1>
        <div class="hero-sub">
          <span class="hero-rec">${rec}</span>
          <button class="leaguechip">${esc(team.meta[team.meta.length-1])} <span class="lc-info">ⓘ</span></button>
        </div>
        ${heroAskHTML()}
      </div>
      ${wire ? `<div>${waiverHeroHTML(team)}</div>` : side ? `<div class="hero-side">${side}</div>` : ""}
    </div>
  </section>`;
}

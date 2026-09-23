/* Roster and Waivers used to be a pair of buttons docked in this hero. They moved up into the
   nav's sub-row when the nav went two-level, because two sub-tab rows on one screen -- one in
   the chrome, one in the page -- read as two different kinds of choice when they are the same
   kind. The hero keeps only what it is for: whose team this is. Roster's up/down/news tiles and
   the outlined slot number behind the title went on 2026-09-22: the tiles mostly read 0, and the
   board below already carries every trend and story they counted. Waivers keeps its tiles. */
function heroHTML(team){
  const side = SURFACE === "waivers" ? `<div>${waiverHeroHTML(team)}</div>` : "";
  return `<section class="hero">
    <div class="wrap hero-in${side ? "" : " solo"}">
      <div>
        <div class="hero-eyebrow" style="--tint:${team.tint}">
          <span class="league-mark"></span>
          <span class="lbl">${team.plat} · ${team.record}</span>
          ${teamSwitchHTML()}
        </div>
        <h1 class="fit">${esc(team.name)}</h1>
        <button class="leaguechip">${esc(team.meta[team.meta.length-1])} <span class="lc-info">ⓘ</span></button>
      </div>
      ${side}
    </div>
  </section>`;
}

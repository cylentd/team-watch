/* Roster and Waivers used to be a pair of buttons docked in this hero. They moved up into the
   nav's sub-row when the nav went two-level, because two sub-tab rows on one screen -- one in
   the chrome, one in the page -- read as two different kinds of choice when they are the same
   kind. The hero keeps only what it is for: whose team this is, and the tiles for the view. */
function heroHTML(team){
  return `<section class="hero">
    <div class="numghost">${team.slot}</div>
    <div class="wrap hero-in">
      <div>
        <div class="hero-eyebrow" style="--tint:${team.tint}">
          <span class="league-mark"></span>
          <span class="lbl">${team.plat} · ${team.record}</span>
          ${teamSwitchHTML()}
        </div>
        <h1 class="fit">${esc(team.name)}</h1>
        <button class="leaguechip">${esc(team.meta[team.meta.length-1])} <span class="lc-info">ⓘ</span></button>
      </div>
      <div>${SURFACE === "waivers" ? waiverTilesHTML(team) : signalsHTML(team)}</div>
    </div>
  </section>`;
}

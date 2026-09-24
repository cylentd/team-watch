/* Roster and Waivers used to be a pair of buttons docked in this hero. They moved up into the
   nav's sub-row when the nav went two-level, because two sub-tab rows on one screen -- one in
   the chrome, one in the page -- read as two different kinds of choice when they are the same
   kind. The hero keeps only what it is for: whose team this is. The roster's three KPI tiles
   (trending up, trending down, news) went on 2026-09-24: each counted something the rows below
   already show on their own, and on a phone they cost a screen-third before the first player. */
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
        <div class="hero-sub">
          <span class="hero-rec">${team.plat} · ${team.record}</span>
          <button class="leaguechip">${esc(team.meta[team.meta.length-1])} <span class="lc-info">ⓘ</span></button>
        </div>
      </div>
      <div>${SURFACE === "waivers" ? waiverHeroHTML(team) : ""}</div>
    </div>
  </section>`;
}

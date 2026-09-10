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
        <h1>${esc(team.name)}</h1>
        <button class="leaguechip">${esc(team.meta[team.meta.length-1])} <span class="lc-info">ⓘ</span></button>
      </div>
      <div>${signalsHTML(team)}</div>
    </div>
  </section>`;
}


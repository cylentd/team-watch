function heroHTML(team){
  const lg = waiverFor(team.key);
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
        <div class="modes-sub teamstabs" role="group" aria-label="${t("teams.tab.label")}">
          <button class="mode-sub" data-teamstab="roster" aria-pressed="${TEAMS_TAB==="roster"}">${t("teams.tab.roster")}</button>
          <button class="mode-sub" data-teamstab="waivers" aria-pressed="${TEAMS_TAB==="waivers"}">${t("teams.tab.waivers")}${lg ? ` <span class="tabcount">${lg.wire.length}</span>` : ""}</button>
        </div>
      </div>
      <div>${TEAMS_TAB === "waivers" ? waiverTilesHTML(team) : signalsHTML(team)}</div>
    </div>
  </section>`;
}

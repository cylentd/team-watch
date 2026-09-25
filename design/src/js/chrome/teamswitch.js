/* The team switch. It used to live in the navbar next to the tabs, crowding them on mobile; now
   it rides the hero's own eyebrow line, which already has the room and is where a reader looks
   first to confirm which team they're on. It lists David's two baked leagues, then any league the
   visitor connected (data/connect.js), then "Add a league", which opens the connect sheet. */
function teamSwitchCells(){
  const cells = [
    {k:"yahoo", plat:t("chrome.teamswitch.yahoo"), team:TEAMS.yahoo.name, tint:"var(--yahoo)"},
    {k:"espn",  plat:t("chrome.teamswitch.espn"),  team:TEAMS.espn.name,  tint:"var(--espn)"},
  ];
  return cells.concat(connectedKeys().map(k =>
    ({k, plat:TEAMS[k].plat, team:TEAMS[k].name, tint:TEAMS[k].tint})));
}

function teamSwitchHTML(){
  const cells = teamSwitchCells();
  const cur = cells.find(c=>c.k===VIEW) || cells[0];
  return `<div class="teamswitch" id="switch" style="--tint:${cur.tint}">
    <button class="ts-btn" data-tsbtn aria-haspopup="listbox" aria-expanded="false">
      <span class="ts-dot"></span>
      <span class="ts-team">${esc(cur.team)}</span>
      <span class="ts-chev">▾</span>
    </button>
    <div class="ts-menu" data-tsmenu role="listbox" hidden>
      ${cells.map(c=>`<button class="ts-item" role="option" data-k="${esc(c.k)}" style="--tint:${c.tint}" aria-selected="${c.k===VIEW}">${c.plat} · ${esc(c.team)}</button>`).join("")}
      <button class="ts-item ts-add" data-tsadd>${t("connect.add")}</button>
    </div>
  </div>`;
}
function wireTeamSwitch(v){
  const sw = v.querySelector("#switch");
  if (!sw) return;
  const btn = sw.querySelector("[data-tsbtn]"), menu = sw.querySelector("[data-tsmenu]");
  btn.addEventListener("click", e=>{
    e.stopPropagation();
    const open = menu.hidden;
    menu.hidden = !open;
    btn.setAttribute("aria-expanded", String(open));
  });
  sw.querySelector("[data-tsadd]").addEventListener("click", () => {
    menu.hidden = true;
    connectOpen();
  });
  sw.querySelectorAll(".ts-item[data-k]").forEach(b=>b.addEventListener("click", ()=>{
    // No scroll: the switch sits in the hero, and a smooth scroll on top of a re-render was
    // half of the jump. The title keeps one line (fitTitle), so the height holds too.
    const changed = VIEW !== b.dataset.k;
    VIEW = b.dataset.k;
    // A connected league has no Waivers (ff-jarvis builds them for David's leagues only).
    if (TEAMS[VIEW].connected && SURFACE === "waivers") SURFACE = "roster";
    render();
    paintSubnav();       // the Waivers count is per league, and a connected league has none
    if (changed) zipFootball();
  }));
}

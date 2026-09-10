/* The Yahoo/ESPN team switch. It used to live in the navbar next to the tabs, crowding them on
   mobile; now it rides the hero's own eyebrow line ("YAHOO · 0-0"), which already has the room
   and is where a reader looks first to confirm which team they're on. */
function teamSwitchHTML(){
  const cells = [
    {k:"yahoo", plat:"Yahoo", team:TEAMS.yahoo.name, tint:"var(--yahoo)"},
    {k:"espn",  plat:"ESPN",  team:TEAMS.espn.name,  tint:"var(--espn)"},
  ];
  const cur = cells.find(c=>c.k===VIEW);
  return `<div class="teamswitch" id="switch" style="--tint:${cur.tint}">
    <button class="ts-btn" data-tsbtn aria-haspopup="listbox" aria-expanded="false">
      <span class="ts-dot"></span>
      <span class="ts-team">${esc(cur.team)}</span>
      <span class="ts-chev">▾</span>
    </button>
    <div class="ts-menu" data-tsmenu role="listbox" hidden>
      ${cells.map(c=>`<button class="ts-item" role="option" data-k="${c.k}" style="--tint:${c.tint}" aria-selected="${c.k===VIEW}">${c.plat} · ${esc(c.team)}</button>`).join("")}
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
  sw.querySelectorAll(".ts-item").forEach(b=>b.addEventListener("click", ()=>{
    VIEW = b.dataset.k;
    render(); window.scrollTo({top:0, behavior:"smooth"});
  }));
}


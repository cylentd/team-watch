const NEWS_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v11H9l-4 4V16H4z"/></svg>`;
const NAV_ICON = {
  teams: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5"/><circle cx="17" cy="7" r="2.4" opacity=".55"/><path d="M15.5 14.2c2.6.4 4.5 2.2 4.5 5.3" opacity=".55"/></svg>`,
  pool: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4v16h16"/><circle cx="9" cy="14" r="1.6" fill="currentColor" stroke="none"/><circle cx="14" cy="9" r="1.6" fill="currentColor" stroke="none"/><circle cx="18" cy="12" r="1.6" fill="currentColor" stroke="none"/></svg>`,
  parlay: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="7" x2="20" y2="7"/><circle cx="9" cy="7" r="2" fill="var(--panel)"/><line x1="4" y1="12" x2="20" y2="12"/><circle cx="15" cy="12" r="2" fill="var(--panel)"/><line x1="4" y1="17" x2="20" y2="17"/><circle cx="11" cy="17" r="2" fill="var(--panel)"/></svg>`,
  dfs: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="3.5" width="6" height="6" rx="1"/><rect x="14.5" y="3.5" width="6" height="6" rx="1"/><rect x="3.5" y="14.5" width="6" height="6" rx="1"/><rect x="14.5" y="14.5" width="6" height="6" rx="1"/></svg>`,
  news: NEWS_ICON,
};
function buildNav(){
  const n = document.getElementById("nav");
  // Two labels per tab, same pattern as the topbar pills' full/abbr swap: five tabs' full
  // labels don't fit a phone width without the row overflowing into a faded, scrollable strip
  // (a tab someone actually wants -- News -- shouldn't be the one left half-hidden past the edge).
  const items = [["teams","My teams","Teams"],["pool","The pool","Pool"],["parlay","Parlay","Parlay"],["dfs","DFS","DFS"],["news","News","News"]];
  n.innerHTML = items.map(([k,label,short])=>
    `<button class="navitem" data-s="${k}" aria-current="${SURFACE===k}">
      <span class="ix">${NAV_ICON[k]}</span><span class="full">${label}</span><span class="abbr">${short}</span></button>`).join("");
  n.querySelectorAll(".navitem").forEach(b=>b.addEventListener("click",()=>{
    SURFACE = b.dataset.s;
    n.querySelectorAll(".navitem").forEach(x=>x.setAttribute("aria-current", x.dataset.s===SURFACE));
    render(); window.scrollTo({top:0,behavior:"smooth"});
  }));
}

/* One global listener, registered once, rather than one per render -- render() rebuilds
   #switch's markup from scratch every time (see teamSwitchHTML/wireTeamSwitch above), so a
   listener attached inside render() would stack a new copy on every re-render. */
document.addEventListener("click", e=>{
  const sw = document.getElementById("switch");
  if (!sw) return;
  const menu = sw.querySelector("[data-tsmenu]"), btn = sw.querySelector("[data-tsbtn]");
  if (menu && !menu.hidden && !sw.contains(e.target)){
    menu.hidden = true; btn.setAttribute("aria-expanded","false");
  }
});


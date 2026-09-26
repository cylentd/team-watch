/* The team switch. It used to live in the navbar next to the tabs, crowding them on mobile; now
   it rides the hero's own eyebrow line, which already has the room and is where a reader looks
   first to confirm which team they're on. Since 2026-09-25 it lists every team in David's two
   leagues (data/mates.js), under each league's name and by team name, so a leaguemate finds
   theirs; then any league the visitor connected (data/connect.js), then "Add a league". */
function teamSwitchCells(){
  const league = (k, plat, tint) => [k, ...mateKeys(k)]
    .map(key => ({k: key, plat, team: TEAMS[key].name, tint, group: k}))
    .sort((a, b) => a.team.localeCompare(b.team, undefined, {sensitivity: "base"}));
  return [...league("yahoo", t("chrome.teamswitch.yahoo"), "var(--yahoo)"),
    ...league("espn", t("chrome.teamswitch.espn"), "var(--espn)"),
    ...connectedKeys().map(k => ({k, plat: TEAMS[k].plat, team: TEAMS[k].name, tint: TEAMS[k].tint, group: "connected"}))];
}
/* A league's heading in the menu: its name, the last of the team's meta (hydrate.js). */
const tsGroupName = g => g === "connected" ? t("chrome.teamswitch.connected") : esc(TEAMS[g].meta[TEAMS[g].meta.length - 1]);

/* The chevron sits in its own round well (2026-09-25): a bare ▾ after a long team name read as
   punctuation, so readers never found the switch. The league dot before the name went the same
   day: "YAHOO" is spelled out on the line under it, so the dot was a colour code saying it again. */
const TS_CHEV = `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
function teamSwitchHTML(){
  const cells = teamSwitchCells();
  const cur = cells.find(c=>c.k===VIEW) || cells[0];
  return `<div class="teamswitch" id="switch" style="--tint:${cur.tint}">
    <button class="ts-btn" data-tsbtn aria-haspopup="listbox" aria-expanded="false" aria-label="${t("chrome.teamswitch.label", {team: esc(cur.team)})}">
      <span class="ts-team">${esc(cur.team)}</span>
      <span class="ts-chev">${TS_CHEV}</span>
    </button>
    <div class="ts-menu" data-tsmenu role="listbox" hidden>
      ${[...new Set(cells.map(c => c.group))].map(g => `<div class="ts-head" role="presentation">${tsGroupName(g)}</div>
        ${cells.filter(c => c.group === g).map(c=>`<button class="ts-item" role="option" data-k="${esc(c.k)}" style="--tint:${c.tint}" aria-selected="${c.k===VIEW}">${esc(c.team)}</button>`).join("")}`).join("")}
      <button class="ts-item ts-add" data-tsadd>${t("connect.add")}</button>
      ${discordItemHTML()}
    </div>
  </div>`;
}
/* Until a reader picks a team, the roster asks once, under the team's name: a leaguemate lands on
   David's team and would otherwise never learn theirs is one tap away. Gone after any pick. */
function heroAskHTML(){
  return MATES.length && !myTeamLoad() ? `<button class="ts-ask" type="button" data-tsask>${t("chrome.teamswitch.ask")}</button>` : "";
}
/* A phone hides the bar's Discord link (760.css), and this menu is the one every reader opens.
   The address is read from the bar's link, so the invite lives in shell.html only. The item is
   drawn on every screen; a desktop simply has a second way in. */
function discordItemHTML(){
  const a = document.querySelector(".discordlink");
  if (!a) return "";
  return `<a class="ts-item ts-discord" href="${esc(a.href)}" target="_blank" rel="noopener noreferrer">${t("chrome.discord.join")}</a>`;
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
  // The first-visit nudge (heroAskHTML) opens the same menu.
  v.querySelectorAll("[data-tsask]").forEach(a => a.addEventListener("click", e => { e.stopPropagation(); btn.click(); }));
  sw.querySelector("[data-tsadd]").addEventListener("click", () => {
    menu.hidden = true;
    connectOpen();
  });
  sw.querySelectorAll(".ts-item[data-k]").forEach(b=>b.addEventListener("click", ()=>{
    // No scroll: the switch sits in the hero, and a smooth scroll on top of a re-render was
    // half of the jump. The title keeps one line (fitTitle), so the height holds too.
    const changed = VIEW !== b.dataset.k;
    VIEW = b.dataset.k;
    myTeamSave(VIEW);    // the reader's pick opens next time too (data/mates.js)
    SEARCH_INDEX = null; // a leaguemate's roster counts as "yours" in search only while on screen
    // A connected league or a leaguemate's team has no Waivers (ff-jarvis builds David's only).
    if (notMine(TEAMS[VIEW]) && SURFACE === "waivers") SURFACE = "roster";
    render();
    paintSubnav();       // the Waivers count is per league, and a connected league has none
    if (changed) zipFootball();
  }));
}

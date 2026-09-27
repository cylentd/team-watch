/* The team switch. It used to live in the navbar next to the tabs, crowding them on mobile; now
   it rides the hero's own eyebrow line, which already has the room and is where a reader looks
   first to confirm which team they're on. Since 2026-09-26 it lists the teams the reader follows
   (data/mates.js followLoad) and the leagues they connected (data/connect.js); every other team
   in David's two leagues waits behind "Leaguemates", under each league's name, with a star to
   follow it. Then "Add a league" for a team in another league. */
const TS_LEAGUES = ["yahoo", "espn"];
let TS_MORE = false;          // the Leaguemates list is open
const tsByName = (a, b) => TEAMS[a].name.localeCompare(TEAMS[b].name, undefined, {sensitivity: "base"});
const tsLeagueName = k => esc(TEAMS[k].meta[TEAMS[k].meta.length - 1]);
const tsFollowed = () => [...followLoad(), ...connectedKeys()];
const TS_STAR = `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.8l1.9 3.9 4.3.6-3.1 3 .7 4.3L8 11.6l-3.8 2 .7-4.3-3.1-3 4.3-.6z"/></svg>`;

/* One team: tap the name to view it, the star to follow or unfollow. A connected league has no
   star; the Add a league sheet removes it. The league's name under the team only in Following,
   which mixes leagues; under Leaguemates the heading already says it. */
function tsRowHTML(k, followed){
  const lg = followed ? `<small>${tsLeagueName(k)}</small>` : "";
  const tm = TEAMS[k], star = tm.connected ? "" : `<button class="ts-star" type="button" data-follow="${esc(k)}" aria-pressed="${followed}"
    aria-label="${followed ? t("chrome.teamswitch.unfollow", {team: esc(tm.name)}) : t("chrome.teamswitch.follow", {team: esc(tm.name)})}">${TS_STAR}</button>`;
  return `<div class="ts-row" style="--tint:${tm.tint}"><button class="ts-item" role="option" data-k="${esc(k)}" aria-selected="${k === VIEW}">${esc(tm.name)}${lg}</button>${star}</div>`;
}
function tsMenuHTML(){
  const mine = tsFollowed(), rest = TS_LEAGUES.map(lg => [lg, [lg, ...mateKeys(lg)].filter(k => !mine.includes(k)).sort(tsByName)]);
  const n = rest.reduce((s, [, ks]) => s + ks.length, 0);
  return `<div class="ts-head" role="presentation">${t("chrome.teamswitch.following")}</div>
    ${mine.length ? mine.map(k => tsRowHTML(k, true)).join("") : `<p class="ts-empty">${t("chrome.teamswitch.empty")}</p>`}
    ${n ? `<button class="ts-more" type="button" data-tsmore aria-expanded="${TS_MORE}">${t("chrome.teamswitch.mates", {n})}<span class="ts-chev">${TS_CHEV}</span></button>` : ""}
    ${TS_MORE ? rest.filter(([, ks]) => ks.length).map(([lg, ks]) => `<div class="ts-head sub" role="presentation">${tsLeagueName(lg)}</div>
      ${ks.map(k => tsRowHTML(k, false)).join("")}`).join("") : ""}
    <button class="ts-item ts-add" data-tsadd>${t("connect.add")}</button>
    ${discordItemHTML()}`;
}

/* The chevron sits in its own round well (2026-09-25): a bare ▾ after a long team name read as
   punctuation, so readers never found the switch. The league dot before the name went the same
   day: "YAHOO" is spelled out on the line under it, so the dot was a colour code saying it again. */
const TS_CHEV = `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
function teamSwitchHTML(){
  const cur = TEAMS[VIEW] || TEAMS.yahoo;
  return `<div class="teamswitch" id="switch" style="--tint:${cur.tint}">
    <button class="ts-btn" data-tsbtn aria-haspopup="listbox" aria-expanded="false" aria-label="${t("chrome.teamswitch.label", {team: esc(cur.name)})}">
      <span class="ts-team">${esc(cur.name)}</span>
      <span class="ts-chev">${TS_CHEV}</span>
    </button>
    <div class="ts-menu" data-tsmenu role="listbox" hidden>${tsMenuHTML()}</div>
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
  // The first-visit nudge (heroAskHTML) opens the same menu, with the leaguemates showing: a
  // leaguemate's own team is among them.
  v.querySelectorAll("[data-tsask]").forEach(a => a.addEventListener("click", e => {
    e.stopPropagation();
    if (!TS_MORE){ TS_MORE = true; menu.innerHTML = tsMenuHTML(); wireTsMenu(sw, menu); }
    btn.click();
  }));
  wireTsMenu(sw, menu);
}
/* The menu's own controls. A star or the Leaguemates toggle redraws the menu in place, open; each
   stops its click, because the document's close-on-outside listener (nav.js) would otherwise see
   a target the redraw has already detached and close the menu. */
function wireTsMenu(sw, menu){
  const redraw = () => { menu.innerHTML = tsMenuHTML(); wireTsMenu(sw, menu); };
  menu.querySelector("[data-tsmore]")?.addEventListener("click", e => {
    e.stopPropagation();
    TS_MORE = !TS_MORE;
    redraw();
  });
  menu.querySelectorAll("[data-follow]").forEach(b => b.addEventListener("click", e => {
    e.stopPropagation();
    followToggle(b.dataset.follow);
    redraw();
    menu.querySelector(`[data-follow="${CSS.escape(b.dataset.follow)}"]`)?.focus();
  }));
  menu.querySelector("[data-tsadd]").addEventListener("click", () => {
    menu.hidden = true;
    connectOpen();
  });
  menu.querySelectorAll(".ts-item[data-k]").forEach(b=>b.addEventListener("click", ()=>{
    // No scroll: the switch sits in the hero, and a smooth scroll on top of a re-render was
    // half of the jump. The title keeps one line (fitTitle), so the height holds too.
    const changed = VIEW !== b.dataset.k;
    VIEW = b.dataset.k;
    myTeamSave(VIEW);    // the reader's pick opens next time too (data/mates.js)
    SEARCH_INDEX = null; // a leaguemate's roster counts as "yours" in search only while on screen
    // A connected league has no Waivers (ff-jarvis builds David's two leagues only).
    if (!hasWaivers(TEAMS[VIEW]) && SURFACE === "waivers") SURFACE = "roster";
    if (!hasLeague(TEAMS[VIEW]) && SURFACE === "league") SURFACE = "roster";   // League is ESPN's only
    render();
    paintSubnav();       // the Waivers count is per league, and a connected league has none
    if (changed) zipFootball();
  }));
}

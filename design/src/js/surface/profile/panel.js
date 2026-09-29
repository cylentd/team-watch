/* The player profile as a centered popup in #modal (chrome/modal.js), opened by tapping a
   roster row, a waiver target, or a usage row. `p` needs n/pos/team/slug; `originEl` is the
   clicked element, for the scale-from-row motion.

   In the order a reader asks about a player (2026-09-28, David): what did he score, who does he
   play next, how much does he play, who has him, is he good.

     the head    name, the bye, and the sphere: his stat sheet as a solid (orb.js), a tap from
                 the full radar (orbsheet.js)
     the strip   rank by points per game, ppg, role share, snap share (lede.js)
     the owners  one pill per league: yours, a leaguemate's team, or free (owners.js)
     the panes   Season first -- every week, played and to come -- then usage, matchup, bio

   One column at every width since the radar moved into the sphere: the table is the widest thing
   in here and gets the whole modal. Every block reads its own source and renders nothing without
   one, so a player ff-jarvis has no matchup profile for still opens with whatever else the page
   knows; when that is nothing at all, the pane area says so once instead of four times. */
function openProfile(p, originEl){
  if (!p) return;
  searchRemember(p);   // the search sheet's "recent" list (chrome/search.js)
  const prof = profileFor(p);
  const d = document.getElementById("modal");
  d.innerHTML = `
    <div class="dr-head pf-head">
      <button type="button" class="dr-close" aria-label="${t("common.action.close")}">✕</button>
      <div class="dr-id">
        ${headHTML(p)}
        <div class="pf-who">
          <h3 id="pf-title">${esc(p.n)}</h3>
          <div class="lbl">${identityHTML(p, prof)}</div>
          ${archTagsHTML(p, "in")}
          ${sheetTagsHTML(p)}
        </div>
        ${archTagsHTML(p, "side")}
        ${orbBadgeHTML(p)}
      </div>
      ${p.note ? `<div class="dr-note">${esc(p.note)}</div>` : ""}
    </div>
    <div class="dr-body pf-body">
      ${ledeHTML(p, prof)}
      ${ownersHTML(p)}
      ${tabsHTML(prof, p)}
    </div>`;
  wireOrbSheet(d, p);
  wireTabs(d, prof, p);
  showModal(d, originEl, "pf-title");
}

/* A week in the Season table opens that game's drive strip, over this profile rather than instead
   of it (shell.html has a second dialog for exactly this).

   Delegated from #modal, and bound once at load rather than per button inside openProfile: tabs.js
   renders a pane only when the reader opens that tab, and openProfile refills #modal every open,
   so delegation is the one binding that survives every re-render without stacking listeners. */
document.getElementById("modal").addEventListener("click", e => {
  const b = e.target.closest("[data-stripwk]");
  if (!b) return;
  const g = stGameFor(b.dataset.stripclub, +b.dataset.stripwk);
  if (g) openStrip(g, b.dataset.stripname, b);
});

/* Roster rows and waiver cards both open the profile; one wiring for both. */
function wireProfiles(v){
  const open = el => el.dataset.team !== undefined
    ? openProfile(findPlayer(el.dataset.team, +el.dataset.i), el)
    : openProfile(waiverPlayers()[+el.dataset.wire], el);
  v.querySelectorAll(".row, [data-wire]").forEach(el => {
    el.addEventListener("click", () => open(el));
    el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); open(el); } });
  });
}

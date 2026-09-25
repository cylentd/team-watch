/* The player profile as a centered popup in #modal (chrome/modal.js), opened by tapping a
   roster row, a waiver target, or a usage row. `p` needs n/pos/team/slug; `originEl` is the
   clicked element, for the scale-from-row motion.

   Three tiers, and the order is the answer to "what do I do with him this week":

     1. the lede -- three numbers, nothing else in the modal is this large (lede.js)
     2. the stat sheet -- his shape against his position, and the card under it (sheet.js)
     3. the panes -- usage, matchup, log, bio, one at a time (tabs.js)

   Desktop puts 2 and 3 side by side; a phone stacks them (panel.css). Every block reads its own
   source and renders nothing without one, so a player ff-jarvis has no matchup profile for still
   opens with whatever else the page knows; when that is nothing at all, the pane area says so
   once instead of four times. */
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
          ${sheetTagsHTML(p)}
        </div>
      </div>
      ${p.note ? `<div class="dr-note">${esc(p.note)}</div>` : ""}
    </div>
    <div class="dr-body pf-body">
      ${ledeHTML(p, prof)}
      <div class="pf-cols">
        <div class="pf-side">${radarHTML(p)}</div>
        <div class="pf-main">${tabsHTML(prof, p)}</div>
      </div>
    </div>`;
  wireSheet(d);
  wireTabs(d, prof, p);
  showModal(d, originEl, "pf-title");
}

/* A week in the game log opens that game's drive strip, over this profile rather than instead of
   it (shell.html has a second dialog for exactly this).

   Delegated from #modal, and bound once at load rather than per button inside openProfile. The
   game log lives in the Log pane, and tabs.js renders a pane only when the reader opens that tab,
   so a one-shot querySelectorAll at open time finds no buttons at all -- the default pane is
   Usage. Delegation also survives every later re-render without stacking a second listener on an
   element openProfile keeps and refills. */
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

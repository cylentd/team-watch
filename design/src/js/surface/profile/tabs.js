/* The modal's panes. Eleven blocks stacked at one weight is a wall: the reader scrolls past the
   whole thing looking for the one they came for, and on a phone that was 1,400px of it. As three
   tabs, each named for the question it answers, the modal is one screen and a tap.

   `.modes-sub` is the app's sub-tab component -- the builder's book toggle, the roster/waivers
   switch, the nav's second row. nav.css already names the rule this follows: a third caller is a
   component, not a coincidence. This is the fourth.

   Only the open pane is rendered, not all three with two hidden. Two reasons: every chart in
   here animates on insert, so a hidden pane would finish its entrance unseen and be static by
   the time it is opened; and the modal's focus trap walks the live buttons, which should be the
   ones on screen. */
const PF_TABS = [
  {id: "usage", label: () => t("profile.tab.usage"),
   body: (prof, p) => prof ? roleHTML(prof) + redZoneHTML(prof) + (pfReceiver(prof) ? sidesHTML(prof) : "") : ""},
  {id: "matchup", label: () => t("profile.tab.matchup"),
   body: (prof, p) => !prof ? "" : headlineHTML(prof) + opponentHTML(prof)
     + (pfReceiver(prof) ? zoneReadHTML(prof) + coverageHTML(prof) : "")
     + marketHTML(prof) + blendedHTML(prof)},
  {id: "log", label: () => t("profile.tab.log"),
   body: (prof, p) => weeklyHistoryHTML(p) + projectionHTML(p)},
  /* Last, and the only pane that needs no profile and no usage row: it reads LIVE_PEDIGREE
     alone, so a player the model knows nothing about still has one tab worth opening. */
  {id: "bio", label: () => t("profile.tab.bio"), body: (prof, p) => bioBlockHTML(p)},
];

function pfReceiver(prof){ return prof.pos === "WR" || prof.pos === "TE"; }

/* Which pane was open last, kept across opens on purpose: reading two players against each other
   means opening the same pane twice, and the tab is the reader's choice, not the player's. A
   player with nothing in it falls back to his own first pane rather than opening on empty. */
let PF_TAB = "usage";

function pfPanes(prof, p){
  return PF_TABS.map(tb => ({id: tb.id, label: tb.label(), html: tb.body(prof, p)}))
    .filter(x => x.html.trim());
}

function pfNoneHTML(){
  return `<div class="state-empty pf-empty"><div><b>—</b><span>${t("profile.empty.none")}</span></div></div>`;
}

function tabsHTML(prof, p){
  const panes = pfPanes(prof, p);
  /* No ff-jarvis profile: two of the three panes have nothing, so say why once, above whatever
     the page does know about him. Dropping straight to a lone Log tab would leave the reader to
     infer the absence from a tab bar that never appeared. */
  const none = prof ? "" : pfNoneHTML();
  if (!panes.length) return pfNoneHTML();
  const on = panes.some(x => x.id === PF_TAB) ? PF_TAB : panes[0].id;
  // One pane draws no tab bar: a switch with one position is a label pretending to be a control.
  const bar = panes.length < 2 ? "" :
    `<div class="modes-sub pf-tabs" role="tablist" aria-label="${t("profile.tab.label")}">
      ${panes.map(x => `<button class="mode-sub" type="button" role="tab" data-pftab="${esc(x.id)}"
        aria-selected="${x.id === on}">${x.label}</button>`).join("")}
    </div>`;
  return none + bar + `<div class="pf-tabpane" role="tabpanel">${panes.find(x => x.id === on).html}</div>`;
}

/* Arrow keys move along the row and open as they go, which is what role="tablist" promises. */
function wireTabs(d, prof, p){
  const bar = d.querySelector(".pf-tabs");
  if (!bar) return;
  const pane = d.querySelector(".pf-tabpane");
  const tabs = [...bar.querySelectorAll("[data-pftab]")];
  const open = b => {
    if (b.getAttribute("aria-selected") === "true") return;
    PF_TAB = b.dataset.pftab;
    tabs.forEach(x => x.setAttribute("aria-selected", x === b));
    pane.innerHTML = PF_TABS.find(tb => tb.id === PF_TAB).body(prof, p);
  };
  tabs.forEach((b, i) => {
    b.addEventListener("click", () => open(b));
    b.addEventListener("keydown", e => {
      const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (!step) return;
      e.preventDefault();
      const next = tabs[(i + step + tabs.length) % tabs.length];
      open(next); next.focus();
    });
  });
}

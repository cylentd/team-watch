/* The modal's panes. Eleven blocks stacked at one weight is a wall: the reader scrolls past the
   whole thing looking for the one they came for, and on a phone that was 1,400px of it. As tabs,
   each named for the question it answers, the modal is one screen and a tap.

   Season comes first and always opens first (2026-09-28, David: "log should be displayed by default
   instead of Usage. It should be the first one"). The pane a reader left open used to carry over to
   the next player; now every player opens on his points and his schedule, which is what the
   profile is opened for.

   `.modes-sub` is the app's sub-tab component -- the builder's book toggle, the roster/waivers
   switch, the nav's second row. nav.css already names the rule this follows: a third caller is a
   component, not a coincidence. This is the fourth.

   Only the open pane is rendered, not all of them with the rest hidden. Two reasons: every chart in
   here animates on insert, so a hidden pane would finish its entrance unseen and be static by
   the time it is opened; and the modal's focus trap walks the live buttons, which should be the
   ones on screen. */
const PF_TABS = [
  {id: "season", label: () => t("profile.tab.season"),
   body: (prof, p) => { const s = seasonHTML(p, prof); return s ? s + projectionHTML(p) : ""; }},
  {id: "usage", label: () => t("profile.tab.usage"),
   body: (prof, p) => teamShareHTML(p) + archBlockHTML(p)
     + (prof ? roleHTML(prof) + redZoneHTML(prof) + (pfReceiver(prof) ? sidesHTML(prof) : "") : "")},
  {id: "props", label: () => t("profile.tab.props"), body: (prof, p) => propsHTML(p)},
  {id: "matchup", label: () => t("profile.tab.matchup"), body: (prof, p) => !prof ? "" : matchupPaneHTML(prof)},
  /* Last, and the only pane that needs no profile and no usage row: it reads LIVE_PEDIGREE
     alone, so a player the model knows nothing about still has one tab worth opening. */
  {id: "bio", label: () => t("profile.tab.bio"), body: (prof, p) => bioBlockHTML(p)},
];

function pfReceiver(prof){ return prof.pos === "WR" || prof.pos === "TE"; }

/* The matchup in the order it is read (2026-09-29, David: "should fit without scrolling"): the
   verdict across the top, then one card per subject under it (2026-09-29, cards): their defense,
   him against its looks (a receiver's zone read and coverage split), and his side (his blockers
   and the market's number). A desktop reads them side by side, each about 370px wide instead of
   bars 1,000px long; a phone stacks them in the same order. */
function matchupPaneHTML(prof){
  const card = h => h.trim() ? `<div class="pf-col">${h}</div>` : "";
  const rec = pfReceiver(prof);
  const cards = card(opponentHTML(prof))
    + card(rec ? zoneReadHTML(prof) + coverageHTML(prof) : "")
    + card(lineHTML(prof) + marketHTML(prof));
  return headlineHTML(prof) + (cards ? `<div class="pf-cols">${cards}</div>` : "");
}

// The pane's class names the tab, so each pane lays itself out (panel.css) without a wrapper.
const pfPaneClass = id => `pf-tabpane pf-pane-${id}`;

function pfPanes(prof, p){
  return PF_TABS.map(tb => ({id: tb.id, label: tb.label(), html: tb.body(prof, p)}))
    .filter(x => x.html.trim());
}

function pfNoneHTML(){
  return `<div class="state-empty pf-empty"><div><b>—</b><span>${t("profile.empty.none")}</span></div></div>`;
}

function tabsHTML(prof, p){
  const panes = pfPanes(prof, p);
  /* No ff-jarvis profile: two of the panes have nothing, so say why once, above whatever the page
     does know about him. Dropping straight to a lone tab would leave the reader to infer the
     absence from a tab bar that never appeared. */
  const none = prof ? "" : pfNoneHTML();
  if (!panes.length) return pfNoneHTML();
  const on = panes[0].id;
  // One pane draws no tab bar: a switch with one position is a label pretending to be a control.
  const bar = panes.length < 2 ? "" :
    `<div class="modes-sub pf-tabs" role="tablist" aria-label="${t("profile.tab.label")}">
      ${panes.map(x => `<button class="mode-sub" type="button" role="tab" data-pftab="${esc(x.id)}"
        aria-selected="${x.id === on}">${x.label}</button>`).join("")}
    </div>`;
  return none + bar + `<div class="${pfPaneClass(on)}" role="tabpanel">${panes[0].html}</div>`;
}

/* Arrow keys move along the row and open as they go, which is what role="tablist" promises. */
/* A sideways swipe on the open profile turns its tab (2026-09-29): on a phone the tab bar is at the top,
   a thumb's stretch away. It walks the tabs drawn, not PF_TABS, since an empty pane draws none, and stops
   at either end. The pane slides in from the side the swipe came from. chrome/modal.js binds it once. */
function pfSwipeTab(d, step){
  const tabs = [...d.querySelectorAll(".pf-tabs [data-pftab]")];
  const i = tabs.findIndex(b => b.getAttribute("aria-selected") === "true"), next = tabs[i + step];
  if (i < 0 || !next) return;
  next.click();
  const pane = d.querySelector(".pf-tabpane");
  if (pane && !REDUCED()) pane.classList.add(step > 0 ? "in-r" : "in-l");
}
/* Touches the profile's gestures leave alone: the radar owns its drag, the tab bar and the orb sheet their own taps. */
const pfOwnsTouch = el => !!(el.closest && el.closest(".pf-radar-hit, .pf-tabs, .pf-orbsheet"));

function wireTabs(d, prof, p){
  const bar = d.querySelector(".pf-tabs");
  if (!bar) return;
  const pane = d.querySelector(".pf-tabpane");
  const tabs = [...bar.querySelectorAll("[data-pftab]")];
  const open = b => {
    if (b.getAttribute("aria-selected") === "true") return;
    tabs.forEach(x => x.setAttribute("aria-selected", x === b));
    pane.className = pfPaneClass(b.dataset.pftab);
    pane.innerHTML = PF_TABS.find(tb => tb.id === b.dataset.pftab).body(prof, p);
  };
  // A head archetype tag (archetype.js) opens Usage on the block that explains it.
  d.querySelectorAll("[data-pfarch]").forEach(tag => tag.addEventListener("click", () => {
    const u = tabs.find(x => x.dataset.pftab === "usage");
    if (!u) return;
    open(u);
    const sec = pane.querySelector(".pf-sec-arch");
    if (sec) sec.scrollIntoView({block: "start", behavior: REDUCED() ? "auto" : "smooth"});
  }));
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

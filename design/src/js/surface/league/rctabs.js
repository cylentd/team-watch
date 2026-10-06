/* ============================== LEAGUE > RECORDS: ITS TWO VIEWS ==============================
   2026-10-06 (trade finder, unit U4). Records holds All-time (records.js) and Trade history (the old Trades leaf,
   surface/trades/, one tab here: it is the league's book of past trades; the Trades leaf is the finder now). Trade
   history is the Madden Curse's and AYO's: the tab is absent where the league has no graded trades (trData(), trades/cards.js).
   Declared with navModes (data/tabrow.js) at the end of this file, so a phone draws them as the Records pill's own
   tabs and a desktop the bar below (.view-tabs, hidden on a phone). The tab is kept for the session. */
let RC_TAB = "alltime";
const rcTabIds = () => trData() ? ["alltime", "trades"] : ["alltime"];
const rcTab = () => rcTabIds().includes(RC_TAB) ? RC_TAB : "alltime";
const rcTabName = id => id === "trades" ? t("records.tab.trades") : t("records.tab.alltime");

/* The desktop's bar; "" with one view, since a lone tab names nothing to switch to. */
const rcTabsHTML = () => rcTabIds().length < 2 ? "" : `<div class="setrow rc-tabs view-tabs" role="group" aria-label="${t("records.tabs.label")}">${
  rcTabIds().map(id => `<button type="button" class="chip" data-rctab="${id}" aria-pressed="${id === rcTab()}">${rcTabName(id)}</button>`).join("")}</div>`;

/* A tab opens its view in place: the page again from the top, the row's pressed state following (chrome/nav.js). */
function rcSelect(id){
  if (id === rcTab()) return;
  RC_TAB = id;
  render();
  window.scrollTo({top: 0});
  document.querySelector(`[data-rctab="${id}"]`)?.focus({preventScroll: true});
}

navModes("records", () => ({ids: rcTabIds(), cur: rcTab(), attr: "rctab", name: t("records.tabs.label"), label: rcTabName, select: rcSelect}));

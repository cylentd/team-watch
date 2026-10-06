/* ============================== RECAP: THE VIEW ==============================
   This week > Recap (leaf `weekrecap`, 2026-10-05). The banner, then one segmented control, Players /
   Scores / Claude, then that tab's cards. Tabs are an exception to STYLE.md's "one job per view", like
   Live's (2026-10-04): the three questions on one page measured 2,265px at 360px wide, and "that is a
   lot of scrolling" (David). The picked tab is kept in localStorage; a tap repaints the body in place,
   never through render(), so the banner and the bar hold still. DESIGN.md "Recap (This week)". */

/* The bar is Live's own segmented control (.gd-tabs, surface/live/live.css, fenced to this view too);
   recap.css sets it to three columns. */
const wrTabsHTML = (open, on) => `<div class="gd-tabs" role="group" aria-label="${t("weekrecap.tabs.label")}">${open.map(k =>
  `<button type="button" data-wrtab="${k}" aria-pressed="${k === on}">${wrTabName(k)}</button>`).join("")}</div>`;

const wrBodyHTML = (d, tab) => tab === "players" ? wrPlayersHTML(d) : tab === "scores" ? wrScoresHTML(d)
  : tab === "accuracy" ? acHTML(wrAcc()) : wrClaudeHTML(d);

function wrViewHTML(){
  const d = wrD(), open = wrAvail(d);
  if (!open.length && !(d && d.top)) return `<div class="wrap"><div class="state-empty" style="min-height:220px">
    <div><b>${t("weekrecap.empty.title")}</b><span>${t("weekrecap.empty.sub")}</span></div></div></div>`;
  const on = wrTab(d);
  return `<div class="wrap wr-page">${d ? wrBannerHTML(d) : ""}${open.length > 1 ? wrTabsHTML(open, on) : ""}
    <div class="wr-body" data-wrbody data-wrtabname="${on || ""}">${on ? wrBodyHTML(d, on) : ""}</div></div>`;
}

/* The links out of a card: to Preview, to one of its games, to its every-week record. Each opens the other
   view the way a tap on its own nav would: the logo morphs, the page returns to the top. */
function wrGo(fn){
  if (typeof morphLogo === "function") morphLogo();
  fn();
  window.scrollTo({top: 0});
}

function wrWireBody(v){
  const body = v.querySelector("[data-wrbody]");
  body.querySelectorAll("[data-wrslug]").forEach(el => el.addEventListener("click", () => wrOpenPlayer(el.dataset.wrslug, el)));
  body.querySelectorAll("[data-wrlist]").forEach(b => b.addEventListener("click", () => {
    WR_LIST = b.dataset.wrlist;
    body.querySelectorAll("[data-wrlist]").forEach(x => x.setAttribute("aria-pressed", x === b));
    body.querySelectorAll("[data-wrpanel]").forEach(p => p.toggleAttribute("data-off", p.dataset.wrpanel !== WR_LIST));
  }));
  body.querySelector("[data-wrtds]")?.addEventListener("click", () => { WR_TDS_ALL = !WR_TDS_ALL; wrPaint(v); });
  body.querySelectorAll("[data-wrgame]").forEach(b => b.addEventListener("click", () => wrGo(() => { navGo("preview"); pvOpen(+b.dataset.wrgame); })));
  body.querySelector("[data-wrgo='preview']")?.addEventListener("click", () => wrGo(() => navGo("preview")));
  body.querySelector("[data-wrrec]")?.addEventListener("click", () => wrGo(() => { navGo("preview"); pvRecOpen(); }));
}

/* The body again for the picked tab, in place: the bar's pressed state follows, nothing else moves. */
function wrPaint(v){
  const d = wrD(), tab = wrTab(d), body = v.querySelector("[data-wrbody]");
  v.querySelectorAll("[data-wrtab]").forEach(b => b.setAttribute("aria-pressed", b.dataset.wrtab === tab));
  body.dataset.wrtabname = tab;
  body.innerHTML = wrBodyHTML(d, tab);
  wrWireBody(v);
}

function wireWeekRecap(v){
  if (!v.querySelector("[data-wrbody]")) return;
  v.querySelectorAll("[data-wrtab]").forEach(b => b.addEventListener("click", () => {
    if (wrTab(wrD()) === b.dataset.wrtab) return;
    wrSetTab(b.dataset.wrtab);
    wrPaint(v);
  }));
  v.querySelector(".wr-go")?.addEventListener("click", e => wrOpenPlayer(e.currentTarget.dataset.wrslug, e.currentTarget));
  wrWireBody(v);
}

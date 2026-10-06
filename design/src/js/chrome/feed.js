/* The credits the footer carried until 2026-10-04: where the data comes from, and the archetype
   icons' CC BY attribution, which has to stay reachable. Drawn here under the week pill (a desktop)
   and on the team switch's About screen (teamswitch.js), since a phone hides the pill. */
function creditsHTML(){
  return `<dl class="credits" data-testid="teamswitch-credits">
    <dt>${t("chrome.credits.sources")}</dt><dd>${t("chrome.credits.sourcesList")}</dd>
    <dt>${t("chrome.credits.icons")}</dt><dd>${t("chrome.credits.iconsList")}</dd>
  </dl>`;
}

/* What `python -m model.refresh` last wrote, per source. This is the honest version of a
   "last updated" line: five sources, each with its own state, because they fail separately. */
function buildFeed(){
  const el = document.getElementById("feed");
  const F = (typeof LIVE_FEED !== "undefined" && LIVE_FEED) ? LIVE_FEED : null;
  const f = F ? F.fetched : {};
  const cells = [
    [t("chrome.feed.espn"),  f.espn  ? ["ok", f.espn]  : ["off", t("chrome.feed.neverPulled")]],
    [t("chrome.feed.yahoo"), f.yahoo ? ["ok", f.yahoo] : ["off", t("chrome.feed.neverPulled")]],
    // The third league's roster (2026-09-29), only once the page carries its team.
    ...(TEAMS.ayo ? [[t("chrome.feed.ayo"), f.ayo ? ["ok", f.ayo] : ["off", t("chrome.feed.neverPulled")]]] : []),
    [t("chrome.feed.usage"), F && F.usage_ready ? ["ok", t("chrome.feed.poolSize", {n: F.pool_size})]
            : ["wait", t("chrome.feed.waiting")]],
    [t("chrome.feed.props"), f.props_bp ? ["ok", f.props_bp] : (f.props ? ["ok", f.props] : ["off", t("chrome.feed.notPulled")])],
    [t("chrome.feed.dfs"),   f.dfs   ? ["ok", f.dfs]   : ["off", t("chrome.feed.noExport")]],
  ];
  const okCount = cells.filter(([,[s]])=>s==="ok").length;
  const worst = cells.some(([,[s]])=>s==="wait") ? "wait" : okCount===cells.length ? "ok" : "off";
  const dotColor = {ok:"var(--up)", wait:"var(--amber)", off:"var(--line-2)"}[worst];
  // One pill, not two (2026-09-25): the week is its label, the dot is the sources' health, and the
  // per-source detail is one tap away. The separate week pill went.
  const count = t("chrome.feed.dataCount", {ok: okCount, n: cells.length});
  const wk = schedWeek();   // the one week every view says (data/schedule.js, one page week)
  const label = wk ? t("chrome.weekpill.week", {week: wk}) : count;
  el.innerHTML = `
    <button class="status-btn" id="statusbtn" aria-haspopup="true" aria-expanded="false" title="${count}">
      <span class="dot" style="background:${dotColor}"></span>${label}
    </button>
    <div class="status-menu" id="statusmenu" hidden>
      ${cells.map(([label,[state,text]]) =>
        `<div class="src ${state}"><i></i>${label} <b>${esc(text)}</b></div>`).join("")}
      ${F && F.generated ? `<div class="src stamp"><i style="visibility:hidden"></i>${t("chrome.feed.refreshed")} <b>${esc(F.generated.replace("T"," ").slice(0,16))}</b></div>` : ""}
      ${creditsHTML()}
    </div>`;
  const btn = el.querySelector("#statusbtn"), menu = el.querySelector("#statusmenu");
  btn.addEventListener("click", e=>{
    e.stopPropagation();
    const open = menu.hidden;
    menu.hidden = !open;
    btn.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("click", e=>{ if(!el.contains(e.target)) menu.hidden = true; });
}


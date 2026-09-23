/* What `python -m model.refresh` last wrote, per source. This is the honest version of a
   "last updated" line: five sources, each with its own state, because they fail separately. */
function buildFeed(){
  const el = document.getElementById("feed");
  const F = (typeof LIVE_FEED !== "undefined" && LIVE_FEED) ? LIVE_FEED : null;
  const f = F ? F.fetched : {};
  const cells = [
    [t("chrome.feed.espn"),  f.espn  ? ["ok", f.espn]  : ["off", t("chrome.feed.neverPulled")]],
    [t("chrome.feed.yahoo"), f.yahoo ? ["ok", f.yahoo] : ["off", t("chrome.feed.neverPulled")]],
    [t("chrome.feed.usage"), F && F.usage_ready ? ["ok", t("chrome.feed.poolSize", {n: F.pool_size})]
            : ["wait", t("chrome.feed.waiting")]],
    [t("chrome.feed.props"), f.props_bp ? ["ok", f.props_bp] : (f.props ? ["ok", f.props] : ["off", t("chrome.feed.notPulled")])],
    [t("chrome.feed.dfs"),   f.dfs   ? ["ok", f.dfs]   : ["off", t("chrome.feed.noExport")]],
  ];
  const okCount = cells.filter(([,[s]])=>s==="ok").length;
  const worst = cells.some(([,[s]])=>s==="wait") ? "wait" : okCount===cells.length ? "ok" : "off";
  const dotColor = {ok:"var(--up)", wait:"var(--amber)", off:"var(--line-2)"}[worst];
  el.innerHTML = `
    <button class="status-btn" id="statusbtn" aria-haspopup="true" aria-expanded="false">
      <span class="dot" style="background:${dotColor}"></span>${t("chrome.feed.dataCount", {ok: okCount, n: cells.length})}
    </button>
    <div class="status-menu" id="statusmenu" hidden>
      ${cells.map(([label,[state,text]]) =>
        `<div class="src ${state}"><i></i>${label} <b>${esc(text)}</b></div>`).join("")}
      ${F && F.generated ? `<div class="src stamp"><i style="visibility:hidden"></i>${t("chrome.feed.refreshed")} <b>${esc(F.generated.replace("T"," ").slice(0,16))}</b></div>` : ""}
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


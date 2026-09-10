/* What `python -m model.refresh` last wrote, per source. This is the honest version of a
   "last updated" line: five sources, each with its own state, because they fail separately. */
function buildFeed(){
  const el = document.getElementById("feed");
  const F = (typeof LIVE_FEED !== "undefined" && LIVE_FEED) ? LIVE_FEED : null;
  const f = F ? F.fetched : {};
  const cells = [
    ["ESPN",  f.espn  ? ["ok", f.espn]  : ["off","never pulled"]],
    ["Yahoo", f.yahoo ? ["ok", f.yahoo] : ["off","never pulled"]],
    ["Usage", F && F.usage_ready ? ["ok", `${F.pool_size} players`]
            : ["wait","waiting for week 1"]],
    ["Props", f.props_bp ? ["ok", f.props_bp] : (f.props ? ["ok", f.props] : ["off","not pulled yet"])],
    ["DFS",   f.dfs   ? ["ok", f.dfs]   : ["off","no salary export"]],
  ];
  const okCount = cells.filter(([,[s]])=>s==="ok").length;
  const worst = cells.some(([,[s]])=>s==="wait") ? "wait" : okCount===cells.length ? "ok" : "off";
  const dotColor = {ok:"var(--up)", wait:"var(--amber)", off:"var(--line-2)"}[worst];
  el.innerHTML = `
    <button class="status-btn" id="statusbtn" aria-haspopup="true" aria-expanded="false">
      <span class="dot" style="background:${dotColor}"></span>DATA ${okCount}/${cells.length}
    </button>
    <div class="status-menu" id="statusmenu" hidden>
      ${cells.map(([label,[state,text]]) =>
        `<div class="src ${state}"><i></i>${label} <b>${esc(text)}</b></div>`).join("")}
      ${F && F.generated ? `<div class="src stamp"><i style="visibility:hidden"></i>refreshed <b>${esc(F.generated.replace("T"," ").slice(0,16))}</b></div>` : ""}
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


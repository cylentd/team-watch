/* The "Add a league" sheet. The one place the brand shows on a phone: it is the first thing a
   friend sees before the page holds anything of theirs.

   Three ways in, in the order the plan ranks them (docs: claude.ai/artifact/4ynPcsonQ7NkyUV8CNsNJM):
   a public league by its link; a private one through a bookmark tapped on espn.com, which reads
   espn_s2 and SWID (neither is HttpOnly) and comes back here as #connect=...; or the two cookies
   pasted by hand from a computer's DevTools. */
let CONNECT = {step: "link", league: "", swid: "", s2: "", pick: null, error: "", busy: false};

const connectEl = () => document.getElementById("connect");

/* The bookmark's code. It reads espn.com's own cookies and the league id from the address bar,
   and hands both back after a # so they never reach this site's server logs as a query. */
function connectBookmarklet(){
  const home = location.origin + location.pathname;
  return "javascript:(()=>{const c={};document.cookie.split('; ').forEach(x=>{const i=x.indexOf('=');"
    + "c[x.slice(0,i)]=x.slice(i+1)});const l=new URLSearchParams(location.search).get('leagueId')||'';"
    + `location.href='${home}#connect='+encodeURIComponent(JSON.stringify({l,s:c.espn_s2||'',w:c.SWID||''}))})()`;
}

function connectListHTML(){
  const keys = connectedKeys();
  const bad = CONNECT_ERRORS.map(e => `<li class="cn-row"><span>${esc(e.key)}</span>
    <em class="cn-bad">${e.error === "expired" ? t("connect.list.expired") : t("connect.list.down")}</em>
    <button class="cn-x" data-cnremove="${esc(e.key)}">${t("common.action.remove")}</button></li>`);
  if (!keys.length && !bad.length) return "";
  return `<h3 class="cn-h">${t("connect.list.title")}</h3><ul class="cn-list">
    ${keys.map(k => `<li class="cn-row"><span>${esc(TEAMS[k].name)}<small>${esc(TEAMS[k].meta[0])}</small></span>
      <button class="cn-x" data-cnremove="${esc(k)}">${t("common.action.remove")}</button></li>`).join("")}
    ${bad.join("")}</ul>`;
}

function connectPrivateHTML(){
  return `<details class="cn-private" ${CONNECT.step === "private" ? "open" : ""}>
    <summary>${t("connect.private.summary")}</summary>
    <p class="cn-p">${t("connect.private.lm")}</p>
    <h4 class="cn-h4">${t("connect.phone.title")}</h4>
    <ol class="cn-steps">
      <li>${t("connect.phone.copy")} <button class="cn-btn quiet" data-cncopy>${t("connect.phone.copyBtn")}</button></li>
      <li>${t("connect.phone.iphone")}</li>
      <li>${t("connect.phone.android")}</li>
      <li>${t("connect.phone.tap")}</li>
    </ol>
    <h4 class="cn-h4">${t("connect.desk.title")}</h4>
    <p class="cn-p">${t("connect.desk.how")}</p>
    <label class="cn-f"><span>espn_s2</span><input id="cn-s2" autocomplete="off" spellcheck="false" value="${esc(CONNECT.s2)}"></label>
    <label class="cn-f"><span>SWID</span><input id="cn-swid" autocomplete="off" spellcheck="false" value="${esc(CONNECT.swid)}"></label>
  </details>`;
}

function connectPickHTML(){
  return `<p class="cn-p">${t("connect.pick.ask", {league: esc(CONNECT.pick.league || "")})}</p>
    <div class="cn-pick">${CONNECT.pick.teams.map(tm =>
      `<button class="cn-team" data-cnteam="${tm.id}">${esc(tm.name)}<small>${esc(tm.record)}</small></button>`).join("")}</div>`;
}

function connectHTML(){
  return `<div class="cn-in">
    <div class="cn-top">
      <div class="brand-name" aria-hidden="true">Team<i class="slashes"><b></b><b></b></i>Watch</div>
      <button class="cn-close" data-cnclose aria-label="${t("common.action.close")}">✕</button>
    </div>
    <h2 class="cn-title">${t("connect.title")}</h2>
    <p class="cn-p">${t("connect.lede")}</p>
    ${CONNECT.pick ? connectPickHTML() : `
    <label class="cn-f"><span>${t("connect.link.label")}</span>
      <input id="cn-league" inputmode="url" autocomplete="off" spellcheck="false"
        placeholder="${t("connect.link.placeholder")}" value="${esc(CONNECT.league)}"></label>
    ${connectPrivateHTML()}
    <button class="cn-btn" data-cngo ${CONNECT.busy ? "disabled" : ""}>${CONNECT.busy ? t("connect.busy") : t("connect.go")}</button>`}
    ${CONNECT.error ? `<p class="cn-err" role="alert">${esc(CONNECT.error)}</p>` : ""}
    <p class="cn-note">${t("connect.yahooSoon")}</p>
    ${connectListHTML()}
  </div>`;
}

function connectPaint(){
  const el = connectEl();
  el.innerHTML = connectHTML();
  const val = id => (el.querySelector(id) || {}).value || "";
  const keep = () => { CONNECT.league = val("#cn-league") || CONNECT.league;
    CONNECT.s2 = val("#cn-s2") || CONNECT.s2; CONNECT.swid = val("#cn-swid") || CONNECT.swid; };
  el.querySelector("[data-cnclose]").addEventListener("click", () => connectClose());
  el.querySelector("[data-cngo]")?.addEventListener("click", () => { keep(); connectSubmit(); });
  el.querySelector("[data-cncopy]")?.addEventListener("click", e => {
    const btn = e.target, code = connectBookmarklet();
    // Some in-app browsers refuse the clipboard; then the code shows, selected, to copy by hand.
    const show = () => { btn.insertAdjacentHTML("afterend", `<textarea class="cn-code" readonly rows="3">${esc(code)}</textarea>`);
      const ta = btn.nextElementSibling; ta.focus(); ta.select(); btn.remove(); };
    if (!navigator.clipboard) return show();
    navigator.clipboard.writeText(code).then(() => { btn.textContent = t("connect.phone.copied"); }, show);
  });
  el.querySelectorAll("[data-cnteam]").forEach(b => b.addEventListener("click", () => connectSubmit(+b.dataset.cnteam)));
  el.querySelectorAll("[data-cnremove]").forEach(b => b.addEventListener("click", async () => {
    await connectRemove(b.dataset.cnremove);
    CONNECT_ERRORS = CONNECT_ERRORS.filter(x => x.key !== b.dataset.cnremove);
    connectPaint(); render();
  }));
}

async function connectSubmit(teamId){
  CONNECT.busy = true; CONNECT.error = ""; connectPaint();
  const got = await connectPost({league: CONNECT.league, swid: CONNECT.swid, s2: CONNECT.s2,
    team_id: teamId || undefined});
  CONNECT.busy = false;
  if (got.pick) CONNECT.pick = {league: got.league, teams: got.pick};
  else if (got.error){ CONNECT.error = got.error; if (got.private) CONNECT.step = "private"; }
  else if (got.league){
    connectClose();
    VIEW = got.league.key;
    SURFACE = "roster";
    paintSubnav(); render();
    return;
  }
  connectPaint();
}

function connectOpen(prefill){
  CONNECT = Object.assign({step: "link", league: "", swid: "", s2: "", pick: null, error: "", busy: false}, prefill || {});
  const el = connectEl();
  el.hidden = false;
  connectPaint();
  layerPush("connect", () => connectClose(true));
}

function connectClose(fromBack){
  const el = connectEl();
  if (el.hidden) return;
  el.hidden = true;
  if (!fromBack) layerDone("connect");
}

/* The bookmark lands here as #connect={l,s,w}. The hash is wiped at once so a reload, a copied
   link or a screenshot of the address bar never carries the cookies further. */
function buildConnect(){
  const m = /^#connect=(.+)$/.exec(location.hash);
  if (!m) return;
  history.replaceState(null, "", location.pathname + location.search);
  let got = {};
  try { got = JSON.parse(decodeURIComponent(m[1])); } catch (e) { /* a mangled paste: open empty */ }
  connectOpen({league: got.l || "", s2: got.s || "", swid: got.w || "", step: "private"});
  if (got.l && got.s) connectSubmit();
}

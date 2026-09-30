/* The Compare picker: who to set beside the profile's player. With nothing typed it offers what the
   reader is most likely deciding between (2026-09-30, David: "typically it starts with their own
   team"): his own team at this position, then the other FLEX spots on it, then the waiver wire,
   each sorted by this week's projection. Search reaches anyone else, any position; a mixed set
   drops the radar, not the player (cmpshow.js). */
let CMP_ROWS = [];

const cmpRankRow = p => typeof LIVE_RANKS !== "undefined" && LIVE_RANKS && p.slug
  ? LIVE_RANKS.rows.find(r => r.slug === p.slug) || null : null;
const cmpProjDesc = (a, b) => (projFor(b) ?? -1) - (projFor(a) ?? -1);
const CMP_FLEX = ["RB", "WR", "TE"];

/* The team to offer from: the one of the reader's that holds the profile's player, else the team
   on screen, else the first. */
function cmpLeague(){
  const mine = myLeagueKeys().filter(k => TEAMS[k] && (TEAMS[k].roster || []).length);
  const holds = mine.find(k => TEAMS[k].roster.some(r => (r.slug || slugOf(r.n)) === CMP.base.slug));
  return holds || (mine.includes(VIEW) ? VIEW : mine[0]) || null;
}

function cmpGroups(){
  const b = CMP.base, key = cmpLeague();
  const withSlug = r => Object.assign({}, r, {slug: r.slug || slugOf(r.n)});
  const roster = key ? TEAMS[key].roster.map(withSlug).filter(r => r.slug !== b.slug) : [];
  const same = roster.filter(r => r.pos === b.pos).sort(cmpProjDesc);
  const flex = CMP_FLEX.includes(b.pos) ? roster.filter(r => r.pos !== b.pos && CMP_FLEX.includes(r.pos)).sort(cmpProjDesc).slice(0, 4) : [];
  const wire = key && WAIVER && isOwner()
    ? waiverIn(key).map(([r]) => withSlug(r)).filter(r => r.pos === b.pos && r.slug !== b.slug).sort(cmpProjDesc).slice(0, 4) : [];
  const team = key ? TEAMS[key].name : "";
  return [
    [t("profile.compare.mine", {team: esc(team), pos: esc(b.pos)}), same],
    [t("profile.compare.flex"), flex],
    [t("profile.compare.wire", {pos: esc(b.pos)}), wire],
  ].filter(([, rows]) => rows.length);
}

function cmpRowHTML(p, i){
  const on = CMP.picks.some(x => x.slug === p.slug), full = !on && CMP.picks.length >= CMP_MAX - 1;
  const rk = cmpRankRow(p), pts = projFor(p);
  const sub = [p.pos, p.team, rk && rk.opp ? t("profile.compare.vs", {opp: esc(rk.opp)}) : ""].filter(Boolean).join(" · ");
  return `<li><button type="button" class="cmp-row${on ? " on" : ""}" data-cmp="pick" data-i="${i}" data-slug="${esc(p.slug)}" aria-pressed="${on}"${full ? " disabled" : ""}>
    <span class="cmp-check" aria-hidden="true"></span><span class="cmp-head">${headHTML(p)}</span>
    <span class="cmp-who"><b>${shortName(p.n)}</b><span class="lbl">${esc(sub)}</span></span>
    <span class="cmp-pts">${pts === null ? "—" : pts.toFixed(1)}${rk ? `<small>${esc(rk.pos)}${rk.rank}</small>` : ""}</span></button></li>`;
}

function cmpListHTML(){
  CMP_ROWS = [];
  const add = p => { CMP_ROWS.push(p); return cmpRowHTML(p, CMP_ROWS.length - 1); };
  if (CMP.q.trim()){
    const hits = searchFind(CMP.q, 8).map(x => searchPlayer(x.e)).filter(p => p.slug !== CMP.base.slug);
    return hits.length ? `<ol class="cmp-group">${hits.map(add).join("")}</ol>`
      : `<p class="cmp-empty">${t("profile.compare.none")}</p>`;
  }
  const groups = cmpGroups();
  // A pick found by search is on none of the lists; he stays on screen, first, so he can be unticked.
  const listed = new Set(groups.flatMap(([, rows]) => rows.map(r => r.slug)));
  const found = CMP.picks.filter(p => !listed.has(p.slug));
  if (found.length) groups.unshift([t("profile.compare.picked"), found]);
  if (!groups.length) return `<p class="cmp-empty">${t("profile.compare.hint")}</p>`;
  return groups.map(([cap, rows]) => `<div class="cmp-cap lbl">${cap}</div><ol class="cmp-group">${rows.map(add).join("")}</ol>`).join("");
}

function cmpTrayHTML(){
  const ps = cmpPlayers();
  return `<div class="cmp-tray">
    <span class="cmp-heads">${ps.map((p, i) => `<span class="cmp-head cmp-s${i}">${headHTML(p)}</span>`).join("")}</span>
    <span class="cmp-count lbl">${t("profile.compare.count", {n: ps.length, max: CMP_MAX})}</span>
    <button type="button" class="cmp-go" data-cmp="go"${CMP.picks.length ? "" : " disabled"}>${t("profile.compare.go")}</button></div>`;
}

function cmpPickHTML(){
  return `<div class="cmp-h"><h4 id="cmp-t">${t("profile.compare.title", {n: shortName(CMP.base.n)})}</h4>
      <button type="button" class="dr-close cmp-x" data-cmp="close" aria-label="${t("profile.compare.close")}">✕</button></div>
    <input id="cmp-q" class="cmp-q" type="search" autocomplete="off" spellcheck="false"
      placeholder="${t("profile.compare.search")}" aria-label="${t("profile.compare.search")}" value="${esc(CMP.q)}">
    <div class="cmp-list">${cmpListHTML()}</div>${cmpTrayHTML()}`;
}

/* The list and the tray repaint without the box, so typing keeps its caret and a tick keeps the
   reader's place in the list. */
function cmpPaintList(sheet){
  if (!sheet) return;
  const list = sheet.querySelector(".cmp-list"), tray = sheet.querySelector(".cmp-tray");
  if (list) list.innerHTML = cmpListHTML();
  if (tray) tray.outerHTML = cmpTrayHTML();
}

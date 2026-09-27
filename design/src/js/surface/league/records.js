/* ============================== RECORDS (My teams, Yahoo) ==============================
   2026-09-27, storyboard https://claude.ai/artifact/JAp2FLPRYAXSVxnNtR8HKU. The league's all-time book
   on its own page, apart from the week: a trophy case by team as it is named today (with every team
   that has never won named in one line), then the Hall of Fame and the Hall of Shame as record cards.
   Nothing hides behind a tab. A record is filed under today's team, with the name it carried then
   underneath; the team on screen is lit wherever it appears. Data: design/league_back.py book(). */

/* Titles by today's team, most first, then the latest title first; a manager who has left keeps the
   name they won under. */
function lgTrophyHTML(id){
  const by = new Map();
  LG.champs.forEach(c => {
    const k = c.id != null ? `id:${c.id}` : `nm:${c.name}`;
    if (!by.has(k)) by.set(k, {id: c.id, name: c.name, ys: []});
    by.get(k).ys.push(c.y);
  });
  const rows = [...by.values()].sort((a, b) => b.ys.length - a.ys.length || Math.max(...b.ys) - Math.max(...a.ys));
  const won = new Set(rows.map(r => r.id).filter(x => x != null));
  const zero = LG.teams.filter(x => !won.has(x.id)).map(x => esc(x.name));
  const li = r => `<li${r.id === id ? ' class="me"' : ""}><span class="rc-tn">${r.id != null ? lgName(r.id) : esc(r.name || t("league.former"))}</span>
    <span class="rc-ys">${[...r.ys].sort().map(y => `<span>${y}</span>`).join("")}</span></li>`;
  return `<section class="lg-sec" aria-label="${t("records.trophy.title")}">
    <h2 class="bp-hd">${t("records.trophy.title")}<span>${t("records.trophy.sub", {n: LG.champs.length})}</span></h2>
    <ul class="rc-trophy">${rows.map(li).join("")}
      ${zero.length ? `<li class="rc-zero">${t("records.trophy.zero", {teams: zero.join(", ")})}</li>` : ""}</ul>
  </section>`;
}

/* One record card: what it is, the number, whose it is today, and when (with the name it had then). */
function lgRecordHTML(f, id){
  const val = {high: lgPts(f.v), blow: `+${lgPts(f.v)}`, streak: f.n, pf: lgPts(f.v), bestrec: `${f.w}–${f.l}`,
    low: lgPts(f.v), robbed: lgPts(f.v), stole: lgPts(f.v), lstreak: f.n, worstrec: `${f.w}–${f.l}`, lasts: `${f.n}×`}[f.k];
  const label = {high: t("records.k.high"), blow: t("records.k.blow"), streak: t("records.k.streak"), pf: t("records.k.pf"),
    bestrec: t("records.k.bestrec"), low: t("records.k.low"), robbed: t("records.k.robbed"), stole: t("records.k.stole"),
    lstreak: t("records.k.lstreak"), worstrec: t("records.k.worstrec"), lasts: t("records.k.lasts")}[f.k];
  if (val == null) return "";
  const ids = f.ids || [f.id];
  const today = f.ids ? f.ids.map(lgName).join(", ") : f.id != null ? lgName(f.id) : esc(f.name || t("league.former"));
  const was = f.id != null && f.name && LG.teams.find(x => x.id === f.id)?.name !== f.name ? t("records.as", {name: esc(f.name.trim())}) : "";
  const gone = f.id == null && !f.ids ? t("records.gone") : "";
  const when = f.wk ? t("records.when", {y: f.y, wk: f.wk}) : f.y ? String(f.y) : f.w != null ? t("records.alltime") : "";
  const d = [was || gone, when].filter(Boolean).join(", ");
  return `<div class="rc-card${ids.includes(id) ? " me" : ""}"><span class="rc-k">${label}</span><span class="rc-v">${val}</span>
    <span class="rc-t">${today}</span>${d ? `<span class="rc-d">${d}</span>` : ""}</div>`;
}

function lgHallHTML(kind, id){
  // Titles are the trophy case's; the Hall of Fame does not count them twice.
  const list = (LG.book[kind] || []).filter(f => f.k !== "titles");
  if (!list.length) return "";
  const title = kind === "fame" ? t("records.fame") : t("records.shame");
  return `<section class="lg-sec rc-${kind}" aria-label="${title}">
    <h2 class="bp-hd">${title}</h2>
    <div class="rc-grid">${list.map(f => lgRecordHTML(f, id)).join("")}</div>
  </section>`;
}

function renderRecords(v, team){
  const L = lgOf(team);
  if (L !== LG){ LG = L; LG_WEEK = null; LG_OPEN = null; }
  const id = lgIdOf(team);
  v.innerHTML = heroHTML(team) + `<div class="wrap"><div class="lg rc">
    <div class="lg-col">${lgTrophyHTML(id)}</div>
    <div class="lg-col">${lgHallHTML("fame", id)}${lgHallHTML("shame", id)}</div>
  </div></div>`;
  fitTitle(v); wireTeamSwitch(v);
  v.querySelector(".leaguechip")?.addEventListener("click", ()=>openLeagueInfo(team.key));
}

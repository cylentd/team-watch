/* ============================== THIS WEEK > RECORDS (Yahoo) ==============================
   2026-09-27, storyboard https://claude.ai/artifact/JAp2FLPRYAXSVxnNtR8HKU. The league's all-time book
   on its own page, apart from the week: a trophy case by manager (with every manager who has never
   won named in one line), then the Hall of Fame and the Hall of Shame as record cards. Nothing hides
   behind a tab. A record is filed under its manager's first name (David's call, 2026-09-27: team names
   change every season), with the team it was then underneath. A league-wide page since the second storyboard (5vFc7Js5EsqJY3EmxgQc84): no team is lit;
   the team on screen's own lines are in My recap. Data: design/league_back.py book(). */

/* Who holds a record: the manager by name (ff-jarvis yahoo_league_managers.json, David's call on
   2026-09-27: team names change every season, managers do not), else today's team, else the name it
   won under. */
const lgHolder = (mgr, id, name) => mgr ? esc(mgr) : id != null ? lgName(id) : esc(name || t("league.former"));

/* Titles by manager, most first, then the latest title first. */
function lgTrophyHTML(id){
  const by = new Map();
  LG.champs.forEach(c => {
    const k = c.mgr ? `m:${c.mgr}` : c.id != null ? `id:${c.id}` : `nm:${c.name}`;
    if (!by.has(k)) by.set(k, {id: c.id, mgr: c.mgr, name: c.name, ys: []});
    by.get(k).ys.push(c.y);
  });
  const rows = [...by.values()].sort((a, b) => b.ys.length - a.ys.length || Math.max(...b.ys) - Math.max(...a.ys));
  const won = new Set(rows.map(r => r.id).filter(x => x != null));
  const zero = LG.teams.filter(x => !won.has(x.id)).map(x => esc(x.mgr || x.name));
  const li = r => `<li${id != null && r.id === id ? ' class="me"' : ""}><span class="rc-tn">${lgHolder(r.mgr, r.id, r.name)}</span>
    <span class="rc-ys">${[...r.ys].sort().map(y => `<span>${y}</span>`).join("")}</span></li>`;
  return `<section class="lg-sec" aria-label="${t("records.trophy.title")}">
    <h2 class="bp-hd">${t("records.trophy.title")}<span>${t("records.trophy.sub", {n: LG.champs.length})}</span></h2>
    <ul class="rc-trophy">${rows.map(li).join("")}
      ${zero.length ? `<li class="rc-zero">${t("records.trophy.zero", {teams: zero.join(", ")})}</li>` : ""}</ul>
  </section>`;
}

/* A record's number and its name, shared with My recap's own lines (myrecap.js). */
const lgRecordValue = f => ({high: lgPts(f.v), blow: `+${lgPts(f.v)}`, streak: f.n, pf: lgPts(f.v), bestrec: `${f.w}–${f.l}`,
  low: lgPts(f.v), robbed: lgPts(f.v), stole: lgPts(f.v), lstreak: f.n, worstrec: `${f.w}–${f.l}`, lasts: `${f.n}×`})[f.k];
const lgRecordLabel = k => ({high: t("records.k.high"), blow: t("records.k.blow"), streak: t("records.k.streak"), pf: t("records.k.pf"),
  bestrec: t("records.k.bestrec"), low: t("records.k.low"), robbed: t("records.k.robbed"), stole: t("records.k.stole"),
  lstreak: t("records.k.lstreak"), worstrec: t("records.k.worstrec"), lasts: t("records.k.lasts")})[k];

/* One record card: what it is, the number, whose it is (the manager), and the team and when. */
function lgRecordHTML(f, id){
  const val = lgRecordValue(f), label = lgRecordLabel(f.k);
  if (val == null) return "";
  const ids = f.ids || [f.id];
  const who = f.ids ? f.ids.map((x, i) => lgHolder((f.mgrs || [])[i], x)).join(", ") : lgHolder(f.mgr, f.id, f.name);
  // Under the manager, the team it was: the name it had that season, or today's for an all-time record.
  const team = f.name ? t("records.as", {name: esc(f.name.trim())}) : f.mgr && f.id != null ? lgName(f.id) : "";
  const gone = !f.mgr && f.id == null && !f.ids ? t("records.gone") : "";
  const when = f.wk ? t("records.when", {y: f.y, wk: f.wk}) : f.y ? String(f.y) : f.w != null ? t("records.alltime") : "";
  const d = [team || gone, when].filter(Boolean).join(", ");
  return `<div class="rc-card${id != null && ids.includes(id) ? " me" : ""}"><span class="rc-k">${label}</span><span class="rc-v">${val}</span>
    <span class="rc-t">${who}</span>${d ? `<span class="rc-d">${d}</span>` : ""}</div>`;
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

/* This week > Records: the same page for every reader, so no team is lit. */
function lgRecordsPageHTML(){
  if (!lgUseYahoo()) return `<div class="wrap"><p class="lg-none">${t("league.none")}</p></div>`;
  return `<div class="wrap">${lgPageHead(t("league.page.sub", {y: LG.since}))}<div class="lg rc">
    <div class="lg-col">${lgTrophyHTML(null)}</div>
    <div class="lg-col">${lgHallHTML("fame", null)}${lgHallHTML("shame", null)}</div>
  </div></div>`;
}

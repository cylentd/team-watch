/* ============================== MY TEAMS > MY RECAP (Yahoo) ==============================
   2026-09-27, storyboard https://claude.ai/artifact/5vFc7Js5EsqJY3EmxgQc84. The team on screen's week:
   the result, its game with the box score open, where it stands three ways (this week's score rank,
   the standings with the move, points), its grudge against next week's opponent,
   and every line of the record book with its name on it. Follows the team switch, so a leaguemate
   picking their team gets their own recap. The league-wide week is This week > League (back.js). */

/* Where the team stands, three ways: this week's score among all of them, the standings, points. */
function lgMyStatsHTML(w, id, pts){
  const row = w.table.find(r => r.id === id), place = w.table.indexOf(row) + 1;
  const scores = w.games.flatMap(g => [g.ap, g.bp]).sort((x, y) => y - x);
  const mv = row.move > 0 ? t("league.table.up", {n: row.move}) : row.move < 0 ? t("league.table.down", {n: -row.move}) : t("myrecap.same");
  const cell = (k, v, sub) => `<div class="mr-stat"><span class="mr-k">${k}</span><b>${v}</b><span class="mr-sub">${sub}</span></div>`;
  return `<div class="mr-stats">
    ${cell(t("myrecap.week"), lgOrd(scores.indexOf(pts) + 1), t("myrecap.ofScores", {n: scores.length}))}
    ${cell(t("myrecap.standing"), lgOrd(place), mv)}
    ${cell(t("myrecap.points"), lgOrd(row.pfr), lgPts(row.pf))}
  </div>`;
}

/* 1 -> "1st", 22 -> "22nd": every case in the copy file, keyed by the last digit (teens are "th"). */
const lgOrd = n => {
  const k = n % 100 >= 11 && n % 100 <= 13 ? "th" : ({1: "st", 2: "nd", 3: "rd"})[n % 10] || "th";
  return ({st: t("myrecap.ord.st", {n}), nd: t("myrecap.ord.nd", {n}), rd: t("myrecap.ord.rd", {n}), th: t("myrecap.ord.th", {n})})[k];
};

/* The team on screen's week: result, game (its box open, the bench mistake in it), standing. Redrawn
   whole by a week chip. */
function lgMyWeekHTML(id){
  const w = lgWeek();
  if (!w) return `<section class="lg-sec bp-week"><p class="lg-none">${t("league.empty")}</p></section>`;
  const g = w.games.find(x => x.a === id || x.b === id);
  const arrive = lgArrive("mine", w) ? " bp-in" : "";
  if (!g) return `<section class="lg-sec bp-week${arrive}">${lgWeekChips(w)}<p class="lg-none">${t("league.yours.none")}</p></section>`;
  const home = g.a === id, mine = home ? g.ap : g.bp, theirs = home ? g.bp : g.ap, m = lgPts(Math.abs(mine - theirs));
  const res = mine > theirs ? `<p class="mr-res w">${t("myrecap.won", {m})}</p>`
    : mine < theirs ? `<p class="mr-res l">${t("myrecap.lost", {m})}</p>` : `<p class="mr-res">${t("league.yours.tied")}</p>`;
  // The bench mistake is the box score's own line (slate.js), so it is not said a second time here.
  return `<section class="lg-sec bp-week${arrive}" aria-label="${t("myrecap.aria")}">
    ${lgWeekChips(w)}${res}
    <div class="bp-slate">${lgGameHTML(g, id, 0)}</div>
    ${lgMyStatsHTML(w, id, mine)}
  </section>`;
}

/* Every record-book line with this team's name on it: titles, then Fame, then Shame (last places
   by season). The number the record is, and the name it was set under when that differs. */
function lgMyBookHTML(id){
  const me = LG.teams.find(x => x.id === id);
  if (!me) return "";
  const row = (label, v, shame) => `<li${shame ? ' class="sh"' : ""}><span>${label}</span><b>${v}</b></li>`;
  const was = f => f.name && f.name !== me.name ? ` <small>${t("records.as", {name: esc(f.name.trim())})}</small>` : "";
  const mine = kind => (LG.book[kind] || []).filter(f => !["titles", "lasts"].includes(f.k) && (f.ids || [f.id]).includes(id));
  const rows = [
    me.titles.length ? row(t("myrecap.titles"), me.titles.join(" · "), false) : "",
    ...mine("fame").map(f => row(lgRecordLabel(f.k) + was(f), lgRecordValue(f), false)),
    ...mine("shame").map(f => row(lgRecordLabel(f.k) + was(f), lgRecordValue(f), true)),
    me.lasts.length ? row(t("myrecap.lasts"), me.lasts.join(" · "), true) : "",
  ].filter(Boolean);
  return `<section class="lg-sec" aria-label="${t("myrecap.book")}">
    <h3 class="bp-hd">${t("myrecap.book")}</h3>
    ${rows.length ? `<ul class="mr-book">${rows.join("")}</ul>` : `<p class="lg-none">${t("myrecap.bookNone")}</p>`}
  </section>`;
}

function renderMyRecap(v, team){
  const L = lgOf(team);
  if (L !== LG){ LG = L; LG_WEEK = null; LG_OPEN = null; }
  const id = lgIdOf(team);
  v.innerHTML = heroHTML(team) + `<div class="wrap"><div class="lg bp">
    <div class="lg-col">${lgMyWeekHTML(id)}</div>
    <div class="lg-col">${lgGrudgeHTML(id)}${lgMyBookHTML(id)}</div>
  </div></div>`;
  fitTitle(v); wireLeague(v, id, () => lgMyWeekHTML(id)); wireTeamSwitch(v);
  v.querySelector(".leaguechip")?.addEventListener("click", ()=>openLeagueInfo(team.key));
}

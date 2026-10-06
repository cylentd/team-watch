/* ============================== LEAGUE > RECAP: THE TEAM'S OWN PART (Yahoo) ==============================
   2026-09-27, storyboard https://claude.ai/artifact/5vFc7Js5EsqJY3EmxgQc84 (it was My teams > My recap).
   The team on screen's week: the result, its game with the box score open, where it stands three ways
   (this week's score rank, the standings with the move, points), its grudge against next week's
   opponent, and every line of the record book with its name on it. Follows the team chip, so a
   leaguemate picking their team gets their own. Since 2026-10-05 it is part of Recap, not a leaf of its
   own: the game sits first under the masthead, the grudge and the book after the league's page (back.js). */

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

/* The team on screen's game that week: result, the game (its box open, the bench mistake in it), where it
   stands. Recap's block under the masthead (back.js); the week chips above it pick the week for the page. */
function lgMineWeekHTML(w, id){
  const g = w.games.find(x => x.a === id || x.b === id);
  if (!g) return `<section class="lg-sec bp-mine"><p class="lg-none">${t("league.yours.none")}</p></section>`;
  const home = g.a === id, mine = home ? g.ap : g.bp, theirs = home ? g.bp : g.ap, m = lgPts(Math.abs(mine - theirs));
  const res = mine > theirs ? `<p class="mr-res w">${t("myrecap.won", {m})}</p>`
    : mine < theirs ? `<p class="mr-res l">${t("myrecap.lost", {m})}</p>` : `<p class="mr-res">${t("league.yours.tied")}</p>`;
  // The bench mistake is the box score's own line (slate.js), so it is not said a second time here.
  return `<section class="lg-sec bp-mine" aria-label="${t("myrecap.aria")}">
    ${res}
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

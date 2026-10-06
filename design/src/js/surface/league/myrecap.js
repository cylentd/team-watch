/* ============================== LEAGUE > RECAP: THE TEAM'S OWN PART (Yahoo) ==============================
   2026-09-27, storyboard https://claude.ai/artifact/5vFc7Js5EsqJY3EmxgQc84 (it was My teams > My recap).
   YOUR GAME, the Recap's first section (back.js): the result, the score, the game's line, where the team
   stands three ways (this week's score rank, the standings with the move, points), then three
   disclosures that open in place and start closed: the box score, next week's grudge against the
   opponent, and every line of the record book with the team's name on it. Follows the team chip, so a
   leaguemate picking their team gets their own. Since 2026-10-05 it is part of Recap, not a leaf of its
   own; since 2026-10-06 the grudge and the book are folded into the box, not after the league's page. */

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

/* One disclosure: a native <details>, so it opens in place with no script and starts closed. The summary
   names the row and says what is inside in a few words; the body is drawn now, shown on a tap. */
const lgDisc = (label, sum, body) => `<details class="lg-disc"><summary><span>${label}</span><span class="lg-dsum">${sum}</span></summary>
  <div class="lg-dbody">${body}</div></details>`;

/* Every record-book line with this team's name on it, as list items: titles, then Fame, then Shame (last
   places by season). The number the record is, and the name it was set under when that differs. */
function lgMyBookRows(id){
  const me = LG.teams.find(x => x.id === id);
  if (!me) return [];
  const row = (label, v, shame) => `<li${shame ? ' class="sh"' : ""}><span>${label}</span><b>${v}</b></li>`;
  const was = f => f.name && f.name !== me.name ? ` <small>${t("records.as", {name: esc(f.name.trim())})}</small>` : "";
  const mine = kind => (LG.book[kind] || []).filter(f => !["titles", "lasts"].includes(f.k) && (f.ids || [f.id]).includes(id));
  return [
    me.titles.length ? row(t("myrecap.titles"), me.titles.join(" · "), false) : "",
    ...mine("fame").map(f => row(lgRecordLabel(f.k) + was(f), lgRecordValue(f), false)),
    ...mine("shame").map(f => row(lgRecordLabel(f.k) + was(f), lgRecordValue(f), true)),
    me.lasts.length ? row(t("myrecap.lasts"), me.lasts.join(" · "), true) : "",
  ].filter(Boolean);
}

/* The record-book disclosure's body: the lines, or one that says there are none. */
function lgMyBookHTML(id){
  const rows = lgMyBookRows(id);
  return rows.length ? `<ul class="mr-book">${rows.join("")}</ul>` : `<p class="lg-none">${t("myrecap.bookNone")}</p>`;
}

/* The team's own game, one line per fact: how it went, the score with managers as names and the team
   beside each, the game's line, three stats, then the disclosures. */
function lgMineWeekHTML(w, id){
  const g = w.games.find(x => x.a === id || x.b === id);
  const head = `<p class="lg-kick lime">${t("league.you.kick")}<b>${lgName(id)}</b></p>`;
  if (!g) return `<div class="lg-you" role="region" aria-label="${t("myrecap.aria")}">${head}<p class="lg-none">${t("league.yours.none")}</p></div>`;
  const home = g.a === id, mine = home ? g.ap : g.bp, theirs = home ? g.bp : g.ap, opp = home ? g.b : g.a;
  const m = lgPts(Math.abs(mine - theirs));
  const res = mine > theirs ? `<p class="mr-res w">${t("myrecap.won", {m})}</p>`
    : mine < theirs ? `<p class="mr-res l">${t("myrecap.lost", {m})}</p>` : `<p class="mr-res">${t("league.yours.tied")}</p>`;
  const side = (tid, pts, lost) => `<div${lost ? ' class="lo"' : ""}><span><b>${lgMgr(tid)}</b><small>${lgName(tid)}</small></span><span class="n">${lgPts(pts)}</span></div>`;
  const first = mine >= theirs;
  const left = g.box && g.box.left[home ? 0 : 1];
  const next = lgOpp(id), h = next != null ? lgH2H(id, next) : null;
  const series = h ? (h.t ? `${h.w}–${h.l}–${h.t}` : `${h.w}–${h.l}`) : "";
  const lines = lgMyBookRows(id).length, grudge = lgGrudgeBodyHTML(id);
  const discs = [
    g.box ? lgDisc(t("league.box.show"), left ? t("league.you.bench", {name: esc(nameInitial(left.benched)), pts: `<b>${left.bp.toFixed(1)}</b>`}) : "", lgBoxHTML(g)) : "",
    grudge ? lgDisc(t("league.you.next", {opp: lgMgr(next)}), h ? t("league.you.series", {rec: `<b>${series}</b>`}) : t("league.you.first"), grudge) : "",
    lgDisc(t("myrecap.book"), lines === 1 ? t("league.you.line1", {n: `<b>${lines}</b>`}) : t("league.you.lines", {n: `<b>${lines}</b>`}), lgMyBookHTML(id)),
  ].join("");
  return `<div class="lg-you" role="region" aria-label="${t("myrecap.aria")}">
    ${head}
    <div class="lg-ytop">${res}<div class="lg-ysc">${first ? side(id, mine, false) + side(opp, theirs, mine > theirs) : side(opp, theirs, false) + side(id, mine, true)}</div></div>
    ${g.punch ? `<p class="lg-yline">${esc(g.punch)}</p>` : ""}
    ${lgMyStatsHTML(w, id, mine)}
    <div class="lg-discs">${discs}</div>
  </div>`;
}

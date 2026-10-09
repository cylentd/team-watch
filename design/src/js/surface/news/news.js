/* Players > News as an injury report (ledger #95, 2026-10-09; DESIGN.md "News"). A row per player the reader
   follows (data/newsreport.js picks and orders them): his Sunday word, Wednesday to Friday, his newest story,
   and the next man up when the read names one free in the reader's leagues. Facts only: the page is not linked
   to the reader's fantasy app, so it never says what to do with a lineup. On a Tuesday no practice has happened:
   the cells go, and each row opens the rest of his stories in place (the blend with draft B). */
const newsSvg = body => `<svg viewBox="0 0 24 24" aria-hidden="true">${body}</svg>`;
const NEWS_ST_ICON = {
  out: newsSvg(`<circle cx="12" cy="12" r="8.5"/><path d="M6 6l12 12"/>`),
  doubtful: newsSvg(`<path d="M12 4 3 20h18z"/><path d="M12 10v4"/>`),
  questionable: newsSvg(`<path d="M12 4 3 20h18z"/><path d="M12 10v4"/>`),
  dnp: newsSvg(`<path d="M12 4 3 20h18z"/><path d="M12 10v4"/>`),
  cleared: newsSvg(`<path d="m5 12.5 4.5 4.5L19 7"/>`),
  full: newsSvg(`<path d="m5 12.5 4.5 4.5L19 7"/>`),
};
/* Every word spelled out, so assemble.py --check sees each key. */
const NEWS_ST = {
  out: () => t("news.st.out"), doubtful: () => t("news.st.doubtful"), questionable: () => t("news.st.questionable"),
  dnp: () => t("news.st.dnp"), limited: () => t("news.st.limited"), full: () => t("news.st.full"),
  cleared: () => t("news.st.cleared"), none: () => t("news.st.none"),
};
const NEWS_MARK = {dnp: () => t("news.mark.dnp"), limited: () => t("news.mark.limited"), full: () => t("news.mark.full")};
const NEWS_DAY = {Wed: () => t("news.day.wed"), Thu: () => t("news.day.thu"), Fri: () => t("news.day.fri")};
const NEWS_GROUP = {mine: () => t("news.group.mine"), wire: () => t("news.group.wire"), starter: () => t("news.group.starter")};

function newsStHTML(word){
  const k = NEWS_ST[word] ? word : "none";
  return `<span class="nr-st ${k}" data-testid="news-sunday">${NEWS_ST_ICON[k] || ""}${esc(NEWS_ST[k]())}</span>`;
}
function newsDaysHTML(r){
  return `<div class="nr-days">${NR_DAYS.map(d => {
    const w = r.days[d];
    return `<span class="nr-cell ${w || ""}" data-testid="news-day"><i>${esc(NEWS_DAY[d]())}</i>${w ? esc(NEWS_MARK[w]()) : ""}</span>`;
  }).join("")}</div>`;
}
/* A league by its short name; a league the page knows no short name for (a connected one) by its own. */
const NEWS_LG = {espn: () => t("news.lg.espn"), yahoo: () => t("news.lg.yahoo"), ayo: () => t("news.lg.ayo")};
const newsLeague = lg => NEWS_LG[lg] ? esc(NEWS_LG[lg]()) : TEAMS[lg] ? tsLeagueName(lg) : esc(lg);
function newsNextHTML(r){
  return r.next.map(x => `<p class="nr-next" data-testid="news-next">${t("news.next", {
    name: `<b>${esc(x.n)}</b>`, where: x.free.map(newsLeague).join(", ")})}</p>`).join("");
}
function newsStoryHTML(it, name, cls, also){
  const href = it.link || `https://www.google.com/search?tbm=nws&q=${encodeURIComponent(it.title || "")}`;
  const when = [kickFmt(it.at) || it.when, ...(also || [])].filter(Boolean).join(" · ");
  return `<a class="${cls}" data-testid="news-story" href="${esc(href)}" target="_blank" rel="noopener noreferrer">${esc(nrWhat(it.title, name))}${when ? `<span class="nr-when">${esc(when)}</span>` : ""}</a>`;
}
/* The week's cells; while ff-jarvis's report carries a note (no marks yet) and no headline gave him one, one line
   says so in their place (ledger #100). */
function newsWeekHTML(r){
  const note = LIVE_NEWS && LIVE_NEWS.practice && LIVE_NEWS.practice.note;
  return note && !NR_DAYS.some(d => r.days[d])
    ? `<p class="nr-noreport" data-testid="news-noreport">${esc(t("news.noreport"))}</p>` : newsDaysHTML(r);
}
function newsRowHTML(r, tuesday){
  const open = NEWS_OPEN.has(r.slug);
  const meta = [r.pos, r.team].filter(Boolean);
  const newest = r.newest ? newsStoryHTML(r.newest, r.n, "nr-story nr-newest", meta)
    : `<span class="nr-when">${esc(meta.join(" · "))}</span>`;
  const more = tuesday && r.more.length ? `<button class="nr-more" data-testid="news-more" data-nrmore="${esc(r.slug)}" aria-expanded="${open}">${esc(t("news.more", {n: r.more.length}))}</button>
    <div class="nr-earlier" ${open ? "" : "hidden"}>${r.more.map(it => newsStoryHTML(it, r.n, "nr-story")).join("")}</div>` : "";
  return `<article class="nr-row" data-testid="news-player" data-slug="${esc(r.slug)}">
    <div class="nhead">${avatarHTML({n: r.n, slug: r.slug})}</div>
    <div class="nr-body">
      <div class="nr-l1"><b class="nr-name" data-testid="news-name">${esc(r.n)}</b>${newsStHTML(r.sunday)}</div>
      ${tuesday ? "" : newsWeekHTML(r)}
      ${newest}
      ${newsNextHTML(r)}${more}
    </div></article>`;
}

/* The wire: the players each followed team's own packet lists, only where the reader may see that packet. */
const newsWire = keys => keys.flatMap(k => {
  const tm = TEAMS[k];
  return tm && wvOwn(tm) ? waiverIn(nrLeagueOf(tm), waiverBlock(tm)).map(([r]) => r.slug) : [];
});

function newsHTML(){
  const ms = Date.now(), tuesday = nrTuesday(ms), keys = tsFollowed();
  const scope = nrScope(TEAMS, keys);
  const groups = nrGroups(nrRows(LIVE_NEWS, scope, newsWire(keys), ms));
  const body = groups.map(g => {
    const pg = g.key === "starter" ? nrPage(g.rows, NEWS_AT) : {rows: g.rows, at: 0, pages: 1};
    NEWS_AT = g.key === "starter" ? pg.at : NEWS_AT;
    const pager = pg.pages > 1 ? `<div class="nr-pager" data-testid="news-pager">
      <button data-nrpage="-1" ${pg.at ? "" : "disabled"}>${esc(t("news.page.prev"))}</button>
      <span>${esc(t("news.page.of", {a: pg.at * NR_PAGE + 1, b: pg.at * NR_PAGE + pg.rows.length, n: g.rows.length}))}</span>
      <button data-nrpage="1" ${pg.at < pg.pages - 1 ? "" : "disabled"}>${esc(t("news.page.next"))}</button></div>` : "";
    return `<section class="nr-group" data-testid="news-group" data-group="${g.key}">
      <h2 class="nr-h">${esc(NEWS_GROUP[g.key]())}<small>${g.rows.length}</small></h2>
      <div class="nr-list">${pg.rows.map(r => newsRowHTML(r, tuesday)).join("")}</div>${pager}</section>`;
  }).join("");
  return `<div class="wrap nrwrap ${tuesday ? "tue" : ""}" data-testid="news-report">${body ||
    `<div class="state-empty" data-testid="news-empty"><div><span>${esc(t("news.empty"))}</span></div></div>`}</div>`;
}

function wireNews(v){
  v.querySelectorAll("[data-nrmore]").forEach(b => b.addEventListener("click", () => {
    const s = b.dataset.nrmore, open = !NEWS_OPEN.has(s);
    open ? NEWS_OPEN.add(s) : NEWS_OPEN.delete(s);
    b.setAttribute("aria-expanded", open);
    b.nextElementSibling.hidden = !open;      // in place: nothing above it moves
  }));
  v.querySelectorAll("[data-nrpage]").forEach(b => b.addEventListener("click", () => {
    NEWS_AT += Number(b.dataset.nrpage); render();
    const h = v.querySelector('[data-group="starter"]');
    if (h) h.scrollIntoView({block: "start"});
  }));
}

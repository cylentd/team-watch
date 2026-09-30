/* A story's kind leads its row as an icon and a word, in that kind's color, so severity reads
   before the headline does -- and a colorblind reader still gets the icon and the word. */
function newsKindTag(kind){
  const k = NEWS_KIND[kind];
  return `<span class="nkind ${kind}">${k.icon}${k.label()}</span>`;
}

/* The player the story leads with: a head when HEADS has one of the build's candidate slugs,
   initials when the title names the player but no head exists, an empty slot for a story with no
   player, so every row's text starts on one edge (2026-09-29: rows without a head ran 52px left of
   the rest). The build parses the name; the page picks the slug, because only HEADS knows which exist. */
function newsHeadHTML(it){
  const slug = (it.slugs || []).find(s => HEADS[s]);
  if (!slug && !it.player) return `<div class="nhead"></div>`;
  return `<div class="nhead">${avatarHTML({n: it.player || "", slug})}</div>`;
}

/* The headline with the player's name set bright and heavy, the rest a step quieter, so a scan down
   the list reads names first (2026-09-30, David: "Player names are hard to find on a scan"). The
   headline's words are unchanged; a title that does not name the parsed player stays whole. */
let NEWS_NAMES = null;   // every name search knows, longest first, built on first use
/* The build parses a name only from "Name (injury) ..." headlines; "Christian Watson good to go" has
   none, so a headline that starts with a known player's name is matched against search's index. */
function newsLeadName(title){
  if (!NEWS_NAMES) NEWS_NAMES = typeof searchIndex === "function"
    ? [...new Set(searchIndex().map(e => e.n).filter(Boolean))].sort((a, b) => b.length - a.length) : [];
  return NEWS_NAMES.find(n => title.startsWith(n + " ")) || null;
}

function newsTitleHTML(it){
  const title = it.title || "", name = it.player || newsLeadName(title);
  const at = name ? title.indexOf(name) : -1;
  if (at < 0) return esc(title);
  const end = at + name.length;
  return `${esc(title.slice(0, at))}<b class="nname">${esc(name)}</b>${esc(title.slice(end))}`;
}

/* What a search matches: the player, his team and the headline, lower-cased once at render. */
const newsQueryText = it => [it.player, it.team, it.title].filter(Boolean).join(" ").toLowerCase();

/* A row: head, kind, time and team, the headline, then the scanner's read on it. The scanner's own
   summary (.ndesc) restates the headline, so it shows only when a story has no read (2026-09-30,
   David: "the first paragraph of each news repeats the headline"). */
function newsRowHTML(it, featured, i){
  const href = it.link || `https://www.google.com/search?tbm=nws&q=${encodeURIComponent(it.title)}`;
  const kind = newsKind(it);
  const head = newsHeadHTML(it);
  return `<a class="newsrow ${kind} ${featured ? "featured" : ""}" data-newsq="${esc(newsQueryText(it))}" style="animation-delay:${Math.min(i || 0, 14) * 30}ms" href="${esc(href)}" target="_blank" rel="noopener noreferrer">
    ${head}<div class="nbody">
    <div class="newstop">
      ${featured ? `<span class="livedot"></span>` : ""}
      ${newsKindTag(kind)}
      ${it.when ? `<span class="when">${esc(it.when)}</span>` : ""}
      ${it.team ? `<span class="nteam">${esc(it.team)}</span>` : ""}
    </div>
    <div class="ntitle">${newsTitleHTML(it)}</div>
    ${it.desc && it.desc !== it.title && !it.impact ? `<div class="ndesc">${esc(it.desc)}</div>` : ""}
    ${it.impact ? `<div class="nimpact">${esc(it.impact)}</div>` : ""}
    </div>
  </a>`;
}

function newsHTML(){
  const items = NEWS_ITEMS;
  // The freshest out story leads on its own above the filter: the one thing that changes a
  // lineup today. Everything else, filtered or not, is chronological below it.
  const lead = items.find(it => newsKind(it) === "out");
  const rest = lead ? items.filter(it => it !== lead) : items;
  const counts = {};
  rest.forEach(it => counts[newsKind(it)] = (counts[newsKind(it)] || 0) + 1);
  const shown = NEWS_CAT === "all" ? rest : rest.filter(it => newsKind(it) === NEWS_CAT);
  const chips = [`<button class="chip" data-newscat="all" aria-pressed="${NEWS_CAT==="all"}">${t("news.kind.all")} (${rest.length})</button>`]
    .concat(NEWS_KINDS.filter(k => counts[k.k]).map(k =>
      `<button class="chip nchip ${k.k}" data-newscat="${k.k}" aria-pressed="${NEWS_CAT===k.k}">${k.icon}${k.label()} (${counts[k.k]})</button>`));
  const label = NEWS_KIND[NEWS_CAT] ? NEWS_KIND[NEWS_CAT].label() : t("news.kind.all");
  return `<section class="hero slim">
    <div class="wrap hero-in">
      <div>
        <div class="hero-eyebrow" style="--tint:var(--lime)">
          <span class="league-mark"></span><span class="lbl">${t("news.hero.eyebrow", {n: items.length})}</span>
        </div>
      </div>
    </div>
  </section>
  <div class="wrap newswrap">
    ${lead ? `<div class="newslead">${newsRowHTML(lead, true, 0)}</div>` : ""}
    <div class="filters" style="margin-top:${lead?"18":"0"}px">
      <span class="lbl">${t("news.filter.label")}</span>
      ${chips.join("")}
      <label class="nsearch"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5L14 14"/></svg>
        <input type="search" id="news-q" value="${esc(NEWS_Q)}" placeholder="${t("news.search.placeholder")}" aria-label="${t("news.search.placeholder")}" autocomplete="off"></label>
    </div>
    ${shown.length
      ? `<div class="newslist" style="margin-top:14px">${shown.map((it, i) => newsRowHTML(it, false, i)).join("")}</div>`
      : `<div class="state-empty" style="margin:14px 0;min-height:110px"><div><b>0</b><span>${t("news.empty.noStories", {cat: esc(label.toUpperCase())})}</span></div></div>`}
    <div class="state-empty nsearch-none" style="margin:14px 0;min-height:110px" hidden><div><b>0</b><span></span></div></div>
  </div>`;
}

/* The search narrows the rows already drawn, in place: a re-render would take the caret out of the box
   on every letter. The lead story is searched too; the kind chips keep their counts. */
function newsApplyQuery(v){
  const q = NEWS_Q.trim().toLowerCase();
  let hits = 0;
  v.querySelectorAll(".newsrow[data-newsq]").forEach(r => {
    const on = !q || r.dataset.newsq.includes(q);
    r.hidden = !on;
    if (on && r.closest(".newslist")) hits++;
  });
  const lead = v.querySelector(".newslead");
  if (lead) lead.hidden = !!lead.querySelector(".newsrow[hidden]");
  const none = v.querySelector(".nsearch-none"), list = v.querySelector(".newslist");
  if (none) {
    none.hidden = !q || hits > 0 || !list;
    none.querySelector("span").textContent = q ? t("news.search.none", {q: NEWS_Q.trim()}) : "";
  }
}

function wireNews(v){
  v.querySelectorAll("[data-newscat]").forEach(b => b.addEventListener("click", () => {
    NEWS_CAT = b.dataset.newscat; render();
  }));
  const box = v.querySelector("#news-q");
  if (box) box.addEventListener("input", () => { NEWS_Q = box.value; newsApplyQuery(v); });
  newsApplyQuery(v);
}

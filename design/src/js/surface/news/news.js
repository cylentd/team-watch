/* A story's kind leads its row as an icon and a word, in that kind's color, so severity reads
   before the headline does -- and a colorblind reader still gets the icon and the word. */
function newsKindTag(kind){
  const k = NEWS_KIND[kind];
  return `<span class="nkind ${kind}">${k.icon}${k.label()}</span>`;
}

function newsRowHTML(it, featured, i){
  const href = it.link || `https://www.google.com/search?tbm=nws&q=${encodeURIComponent(it.title)}`;
  const kind = newsKind(it);
  return `<a class="newsrow ${kind} ${featured ? "featured" : ""}" style="animation-delay:${Math.min(i || 0, 14) * 30}ms" href="${esc(href)}" target="_blank" rel="noopener noreferrer">
    <div class="newstop">
      ${featured ? `<span class="livedot"></span>` : ""}
      ${newsKindTag(kind)}
      ${it.when ? `<span class="when">${esc(it.when)}</span>` : ""}
      ${it.team ? `<span class="nteam">${esc(it.team)}</span>` : ""}
    </div>
    <div class="ntitle">${esc(it.title)}</div>
    ${it.desc && it.desc !== it.title ? `<div class="ndesc">${esc(it.desc)}</div>` : ""}
    ${it.impact ? `<div class="nimpact">${esc(it.impact)}</div>` : ""}
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
    </div>
    ${shown.length
      ? `<div class="newslist" style="margin-top:14px">${shown.map((it, i) => newsRowHTML(it, false, i)).join("")}</div>`
      : `<div class="state-empty" style="margin:14px 0;min-height:110px"><div><b>0</b><span>${t("news.empty.noStories", {cat: esc(label.toUpperCase())})}</span></div></div>`}
  </div>`;
}

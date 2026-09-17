/* The My Teams ticker: real breaking/injury news now, same NEWS_ITEMS the News tab reads, so a
   story that's actually breaking shows up here too instead of the old fixed six-line sample
   loop. Filtered to what's actually urgent (severity), not every routine practice-report line --
   a ticker that scrolls past in a few seconds is the wrong place for "logged a full practice."
   Falls back to the plain feed on a quiet day with nothing severe, so it's never empty. Just the
   headline: the timestamp/team detail lives one click away on the News tab, and repeating it
   here for a dozen scrolling items was noise a glance doesn't need. */
function tickerHTML(){
  const severe = NEWS_ITEMS.filter(it => newsSeverity(it));
  // Every item left after that filter is already Breaking or Injury, so coloring the dot by
  // severity here (red/amber, the News tab's language) would just paint the whole row the same
  // color and say nothing -- a plain lime dot marks "live," which is the thing this row of
  // filtered-down items has left to say that the headline itself doesn't already.
  const run = (severe.length ? severe : NEWS_ITEMS).slice(0, 12).map(it =>
    `<a class="tick" href="${esc(it.link || `https://www.google.com/search?tbm=nws&q=${encodeURIComponent(it.title)}`)}" target="_blank" rel="noopener noreferrer">
      <span class="arrow">●</span>${esc(it.title)}</a>`
  ).join("");
  return `<div class="wrap" style="margin:16px auto"><div class="ticker">
    <div class="ticker-tag">${t("news.ticker.tag")}</div>
    <div class="ticker-track">${run}${run}</div>
  </div></div>`;
}

function newsRowHTML(it, featured){
  const href = it.link || `https://www.google.com/search?tbm=nws&q=${encodeURIComponent(it.title)}`;
  const sev = newsSeverity(it);
  return `<a class="newsrow ${sev} ${featured ? "featured" : ""}" href="${esc(href)}" target="_blank" rel="noopener noreferrer">
    <div class="newstop">
      ${featured ? `<span class="livedot"></span>` : ""}
      ${it.when ? `<span class="when">${esc(it.when)}</span>` : ""}
      ${it.team ? `<span class="nteam">${esc(it.team)}</span>` : ""}
      ${(it.categories || []).map(c => `<span class="ncat ${CAT_CLASS[c] || ""}">${esc(c)}</span>`).join("")}
    </div>
    <div class="ntitle">${esc(it.title)}</div>
    ${it.desc && it.desc !== it.title ? `<div class="ndesc">${esc(it.desc)}</div>` : ""}
    ${it.impact ? `<div class="nimpact">${esc(it.impact)}</div>` : ""}
  </a>`;
}
function newsHTML(){
  const items = NEWS_ITEMS;
  // The freshest Breaking story leads on its own, above the filter -- the one thing "most
  // recent, or breaking" actually means when a page can only lead with one story. Everything
  // else, filtered or not, is chronological below it.
  const lead = items.find(it => newsSeverity(it) === "breaking");
  const rest = lead ? items.filter(it => it !== lead) : items;
  const counts = {};
  rest.forEach(it => (it.categories || []).forEach(c => counts[c] = (counts[c]||0) + 1));
  const shown = NEWS_CAT === "All" ? rest : rest.filter(it => (it.categories||[]).includes(NEWS_CAT));
  return `<section class="hero">
    <div class="numghost">${items.length}</div>
    <div class="wrap hero-in">
      <div>
        <div class="hero-eyebrow" style="--tint:var(--lime)">
          <span class="league-mark"></span><span class="lbl">${t("news.hero.eyebrow", {n: items.length})}</span>
        </div>
        <h1>${t("news.hero.title")}</h1>
      </div>
    </div>
  </section>
  <div class="wrap">
    ${lead ? `<div class="newslead">${newsRowHTML(lead, true)}</div>` : ""}
    <div class="filters" style="margin-top:${lead?"18":"0"}px">
      <span class="lbl">${t("news.filter.label")}</span>
      ${NEWS_FILTERS.map(f => `<button class="chip" data-newscat="${f}" aria-pressed="${NEWS_CAT===f}">${f}${f!=="All" && counts[f] ? ` (${counts[f]})` : ""}</button>`).join("")}
    </div>
    ${shown.length
      ? `<div class="newslist" style="margin-top:14px">${shown.map(it => newsRowHTML(it, false)).join("")}</div>`
      : `<div class="state-empty" style="margin:14px 0;min-height:110px"><div><b>0</b><span>${t("news.empty.noStories", {cat: esc(NEWS_CAT.toUpperCase())})}</span></div></div>`}
  </div>`;
}


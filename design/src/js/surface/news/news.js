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
    <div class="ticker-tag">LIVE</div>
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
  const teams = new Set(items.map(i => i.team).filter(Boolean)).size;
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
          <span class="league-mark"></span><span class="lbl">${items.length} items · newest first</span>
        </div>
        <h1>What's<br><em>breaking</em></h1>
      </div>
      <div><div class="signals">
        <div class="sig up"><div class="lbl">Teams in play</div><div class="sig-val">${teams}</div><div class="sig-sub">OF 32</div></div>
        <div class="sig"><div class="lbl">Latest</div><div class="sig-val" style="font-size:22px">${items[0] && items[0].when ? esc(items[0].when) : "—"}</div><div class="sig-sub">MOST RECENT</div></div>
      </div></div>
    </div>
  </section>
  <div class="wrap">
    ${lead ? `<div class="newslead">${newsRowHTML(lead, true)}</div>` : ""}
    <div class="filters" style="margin-top:${lead?"18":"0"}px">
      <span class="lbl">Filter</span>
      ${NEWS_FILTERS.map(f => `<button class="chip" data-newscat="${f}" aria-pressed="${NEWS_CAT===f}">${f}${f!=="All" && counts[f] ? ` (${counts[f]})` : ""}</button>`).join("")}
    </div>
    ${shown.length
      ? `<div class="newslist" style="margin-top:14px">${shown.map(it => newsRowHTML(it, false)).join("")}</div>`
      : `<div class="state-empty" style="margin:14px 0;min-height:110px"><div><b>0</b><span>NO ${esc(NEWS_CAT.toUpperCase())} STORIES RIGHT NOW</span></div></div>`}
  </div>`;
}

function wireHTML(){
  const side = (p, kind) => `
    <div class="side-${kind==="out"?"o":"i"}">
      <div class="lbl">${kind==="out"?"Drop":"Add"}</div>
      <div class="side-h" style="margin-top:10px">
        ${HEADS[p.slug] ? `<img src="${HEADS[p.slug]}" alt="">` : `<div class="fallback">${esc(initials(p.n))}</div>`}
        <div><div class="side-n">${esc(p.n)}</div><div class="side-m">${esc(p.m)}</div></div>
      </div>
      <div class="side-stats">
        <div class="stat"><b>${esc(p.pos)}</b><span>POS RANK</span></div>
        <div class="stat"><b style="color:${p.d>0?"var(--up)":"var(--down)"}">${p.d>0?"+":""}${p.d}%</b><span>6-WK TREND</span></div>
      </div>
    </div>`;
  return `<div class="wire">${WIRE.map(w=>`
    <div class="swap">
      <div class="swap-head">
        <span class="lbl">Suggested swap</span>
        <span class="pill" style="border-color:${w.team==="ESPN"?"rgba(255,45,45,.4)":"rgba(139,92,255,.4)"};color:var(--ink-2)">${w.team}</span>
      </div>
      <div class="swap-body">${side(w.out,"out")}<div class="arrowcell">→</div>${side(w.in_,"in")}</div>
      <div class="swap-foot">
        <div style="display:flex;gap:18px">
          <div class="stat"><b style="color:var(--lime)">${w.gain}</b><span>LINEUP DELTA</span></div>
          <div class="stat"><b>${w.faab}</b><span>SUGGESTED BID</span></div>
        </div>
        <button class="btn">Queue claim</button>
      </div>
    </div>`).join("")}</div>`;
}


/* ============================== DIGEST: WHAT A ROW OPENS TO ==============================
   Each topic's opened state: the fact, then a foot that says where the numbers come from and links
   to the view that holds all of them. "Not backtested" lives here, on the opened row, never on the
   closed line (plan, 2026-09-26): the closed line is the fact, the caveat is for whoever reads on. */

/* A player line: head, name over one meta line, one number at the right. It opens his profile. */
function dgLnHTML(p, meta, right, extra){
  return `<button type="button" class="dg-ln${extra ? " wide" : ""}" data-testid="digest-ln" data-dgslug="${esc(p.slug)}">
    <span class="dg-hd">${avatarHTML(p)}</span>
    <span class="dg-ln-t"><b>${esc(p.n)}</b><span>${meta}</span>${extra || ""}</span>
    <span class="dg-ln-r" data-testid="digest-ln-right">${right}</span></button>`;
}

function dgFootHTML(text, leaf, label, caveat){
  const go = leaf ? `<button type="button" class="dg-go" data-testid="digest-go" data-dggo="${leaf}">${label}${DG_ARROW}</button>` : "";
  return `<div class="dg-foot" data-testid="digest-foot"><span data-testid="digest-foot-text">${text}${caveat ? ` <span class="dg-nb">${t("digest.nb")}</span>` : ""}</span>${go}</div>`;
}

const dgVs = r => r.home ? t("digest.vs.home", {team: esc(r.team), opp: esc(r.opp)}) : t("digest.vs.away", {team: esc(r.team), opp: esc(r.opp)});
const DG_TAG = {Out: ["out", () => t("digest.tag.out")], IR: ["out", () => t("digest.tag.ir")],
                Doubtful: ["d", () => t("digest.tag.d")], Questionable: ["q", () => t("digest.tag.q")]};

/* Hurt's body left with its row on 2026-09-29: Need to know (need.js) draws the same packet list. */

/* Starters (2026-09-29, storyboard JBN1kirnN6jMZNdZK7EmbF): "QB1 over Sanders", "MIN → NYG", or both
   when a traded player starts. `name` shortens the old #1 as the line around it does; `bare` leaves
   out his status. Need to know (need.js) draws them since 2026-09-29. */
function dgStartWhat(r, name, bare){
  const o = r.over;
  const v = o && {pos: esc(r.pos), name: esc(name(o.n)), status: esc(o.status || "")};
  const over = !o ? "" : o.status && !bare ? t("digest.start.overStatus", v) : t("digest.start.over", v);
  // A move says where he stands on the new chart (McCarthy: the Giants' QB3); a new #1 already said it.
  const m = {from: esc(r.from), team: esc(r.team), pos: esc(r.pos), depth: r.depth};
  const moved = !r.from ? "" : !o && r.depth ? t("digest.start.movedDepth", m) : t("digest.start.moved", m);
  return [over, moved].filter(Boolean).join(", ");
}

/* Start of the week (2026-10-03, David: yes): our boldest START, the call's own row on Start/Sit (the
   widest gap between our rank and his season average), leading the card in lime. Our rank on the
   right with his average under it, as Start/Sit shows it. */
function dgSotwHTML(){
  const s = LIVE_SS3.takes.find(r => r.call === "START");
  return s ? dgLnHTML({n: s.name, slug: s.slug}, `<b class="dg-sotw" data-testid="digest-sotw">${t("digest.mu.sotw")}</b> · ${esc(s.pos)} · ${dgVs(s)}`,
    `${esc(s.pos)}${s.rank}<small>${t("matchups.takes.avg", {avg: s.avg_rank == null ? "—" : esc(s.pos) + s.avg_rank})}</small>`) : "";
}

/* The foot is Start/Sit's record (SMASH, START, SIT as hit-miss since week 5), the same numbers the view prints. */
function dgMuBody(d){
  const lines = dgSotwHTML() + d.best.map(b => dgLnHTML(b, [esc(b.pos), dgVs(b), b.why ? esc(b.why) : ""].filter(Boolean).join(" · "),
    b.pts.toFixed(1))).join("");
  const r = LIVE_SS3.record;
  const rec = ss3Graded(r) ? t("digest.foot.mu", {wk: r.since_week, smash: ss3Wl(r.smash), start: ss3Wl(r.start), sit: ss3Wl(r.sit)})
    : t("digest.foot.muNone", {wk: r.since_week});
  return lines + dgFootHTML(rec, "matchups", t("digest.go.matchups"));
}

/* Each bar grows when the row opens (adds.css): from last week's % rostered to this week's on the
   ESPN fallback, and from nothing to his share of the top count on Sleeper's (2026-09-28). */
function dgAddsBody(d){
  if (d.adds_source === "sleeper"){
    const top = Math.max(1, ...d.adds.map(a => a.count || 0));
    const lines = d.adds.map((a, i) => dgLnHTML(a, a.now != null
      ? t("digest.adds.metaEspn", {pos: esc(a.pos), team: esc(a.team), pct: dgPct(a.now)}) : `${esc(a.pos)} · ${esc(a.team)}`,
      `<span class="dg-plus" data-testid="digest-plus">${dgBig(a.count)}</span>`,
      `<span class="dg-bar" style="--a:0%;--b:${(100 * a.count / top).toFixed(1)}%;--i:${i}"><i></i><u></u></span>`)).join("");
    return lines + dgFootHTML(t("digest.foot.addsSleeper", {h: d.adds_hours}), "waivers", t("digest.go.waivers"));
  }
  const lines = d.adds.map((a, i) => dgLnHTML(a, t("digest.adds.meta", {pos: esc(a.pos), team: esc(a.team), was: dgPct(a.was), now: dgPct(a.now)}),
    `<span class="dg-plus" data-testid="digest-plus">${dgSigned(Math.round(a.delta), 0)}</span>`,
    `<span class="dg-bar" style="--a:${a.was}%;--b:${a.now}%;--i:${i}"><i></i><u></u></span>`)).join("");
  const [a, b] = d.adds_weeks;
  return lines + dgFootHTML(a != null ? t("digest.foot.adds", {a, b}) : t("digest.foot.addsNoWeeks"), "waivers", t("digest.go.waivers"));
}

/* Top 5 and Weather open to ahead.js's bodies (2026-09-29). */

/* Risers & fallers left the Digest on 2026-09-29 (David: "is a +-1 move significant?"). Its move was
   the books' implied points against his last game: 45 of 64 priced players cleared its 0.5 bar in
   week 4, 11 moved more than one sector's usual week-to-week wobble, part of every move was only the
   opponent changing, and the signal failed its backtest (ff-jarvis METHODOLOGY 12.46). Role, from the
   work itself, is where a changing role is read. */

/* A gem is a usage number, so the line also reaches his row in the Grid in 1 tap (2026-10-05, David: A + C,
   nav.js navGoRow); the line itself still opens his profile. */
function dgGemsBody(d){
  const lines = d.gems.map(g => `<div class="dg-lnrow">${dgLnHTML(g, t("digest.gems.meta", {pos: esc(g.pos), team: esc(g.team), pct: dgPct(g.rostered)}),
    `${g.metric === "tgt_pct" ? dgPct(g.usage) + "%" : g.usage.toFixed(1)}<small>${t("digest.gems.ecr", {pos: esc(g.pos), ecr: g.ecr})}</small>`)}
    <button type="button" class="dg-go dg-grid" data-dggrid="${esc(g.slug)}" aria-label="${t("digest.gems.row", {name: esc(g.n)})}">${t("digest.go.gridRow")}${DG_ARROW}</button></div>`).join("");
  return lines + dgFootHTML(t("digest.foot.gems", d.rules.gems),"usage", t("digest.go.grid"), true);
}

/* News by player, not as a log (2026-09-28): one block per player, in the order his newest line
   ranks, his lines newest first; a headline naming no player is a block of its own. The name keeps
   the colour of his newest line's severity. A block opens his profile. The wall lays the blocks out
   as cards three across (wall.css); a phone reads them as one list. */
const DG_KIND = {out: "out", injury: "q"};
function dgNewsGroups(news){
  const groups = [], by = new Map();
  /* Keyed by name: one headline can carry his slug and the next not. */
  for (const it of news){
    let g = it.n && by.get(it.n);
    if (!g){ g = {key: null, n: it.n, kind: it.kind, lines: []}; groups.push(g); if (it.n) by.set(it.n, g); }
    /* Only a named headline opens a profile. One naming no player can still carry a slug (a defender's
       IR move, 2026-09-29), and a block keyed to it with no name broke the whole Digest in avatarHTML. */
    g.key = g.key || (it.n ? (it.slugs && it.slugs[0]) || slugOf(it.n) : null);
    g.lines.push(it);
  }
  return groups;
}

/* The small out-arrow a line wears to say it leaves the page for the story. */
const DG_EXT = `<svg class="dg-out" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3h7v7M13 3L5 11"/></svg>`;

function dgNewsBody(d){
  const who = typeof searchIndex === "function" ? new Map(searchIndex().map(e => [e.slug, e])) : new Map();
  /* Each line opens its story (2026-09-30, David: "it should link to the news source"): the story's own
     page, or a search for the headline when the row predates ff-jarvis keeping the link, as the News tab
     does. The face and name still open his profile, so the block is a div holding both kinds of tap. */
  const line = it => {
    const href = it.link || `https://www.google.com/search?tbm=nws&q=${encodeURIComponent(it.headline)}`;
    return `<li><a data-testid="digest-news-link" href="${esc(href)}" target="_blank" rel="noopener noreferrer"><time>${esc(it.when || "")}</time>
      <span>${esc(it.n ? dgCap(it.rest) : it.headline)}${DG_EXT}</span></a></li>`;
  };
  const blocks = dgNewsGroups(d.news).map(g => {
    if (!g.key) return `<div class="dg-nw" data-testid="digest-news-block"><ul>${g.lines.map(line).join("")}</ul></div>`;
    const e = who.get(g.key), p = {n: g.n, slug: g.key, pos: e && e.pos, team: e && e.team};
    const meta = [p.pos, p.team].filter(Boolean).map(esc).join(" · ");
    return `<div class="dg-nw who" data-testid="digest-news-block">
      <button type="button" class="dg-hd" data-dgslug="${esc(g.key)}" tabindex="-1" aria-hidden="true">${avatarHTML(p)}</button>
      <span class="dg-nw-t"><button type="button" class="dg-nw-who" data-testid="digest-news-who" data-dgslug="${esc(g.key)}"><b class="${DG_KIND[g.kind] || ""}">${esc(g.n)}</b><small>${meta}</small></button>
      <ul>${g.lines.map(line).join("")}</ul></span></div>`;
  }).join("");
  return `<div class="dg-nws" data-testid="digest-news">${blocks}</div>` + dgFootHTML(t("digest.foot.news"), "news", t("digest.go.news"));
}

/* One short list in Top 5's shape: a head, then "K. Mumpfield" and one number per line (Tonight's lists). */
function dgResList(title, rows, num){
  return rows.length ? `<div><h4>${title}</h4><ol>${rows.map(r => `<li><span class="dg-hd sm">${avatarHTML(r)}</span>`
    + `<span>${esc(dgShort(r.n))}</span>${num(r)}</li>`).join("")}</ol></div>` : "";
}

/* The Recap row opens no body: it is a link (recaprow.js). */
const DG_BODY = {mu: dgMuBody, wx: dgWxBody, adds: dgAddsBody, t5: dgTop5Body,
                 gems: dgGemsBody, news: dgNewsBody};

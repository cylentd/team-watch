/* ============================== DIGEST: WHAT A ROW OPENS TO ==============================
   Each topic's opened state: the fact, then a foot that says where the numbers come from and links
   to the view that holds all of them. "Not backtested" lives here, on the opened row, never on the
   closed line (plan, 2026-09-26): the closed line is the fact, the caveat is for whoever reads on. */

/* A player line: head, name over one meta line, one number at the right. It opens his profile. */
function dgLnHTML(p, meta, right, extra){
  return `<button type="button" class="dg-ln${extra ? " wide" : ""}" data-dgslug="${esc(p.slug)}">
    <span class="dg-hd">${avatarHTML(p)}</span>
    <span class="dg-ln-t"><b>${esc(p.n)}</b><span>${meta}</span>${extra || ""}</span>
    <span class="dg-ln-r">${right}</span></button>`;
}

function dgFootHTML(text, leaf, label, caveat){
  const go = leaf ? `<button type="button" class="dg-go" data-dggo="${leaf}">${label}${DG_ARROW}</button>` : "";
  return `<div class="dg-foot"><span>${text}${caveat ? ` <span class="dg-nb">${t("digest.nb")}</span>` : ""}</span>${go}</div>`;
}

const dgVs = r => r.home ? t("digest.vs.home", {team: esc(r.team), opp: esc(r.opp)}) : t("digest.vs.away", {team: esc(r.team), opp: esc(r.opp)});
const DG_TAG = {Out: ["out", () => t("digest.tag.out")], IR: ["out", () => t("digest.tag.ir")],
                Doubtful: ["d", () => t("digest.tag.d")], Questionable: ["q", () => t("digest.tag.q")]};

function dgHurtBody(d){
  const q = d.hurt.filter(r => r.status === "Questionable");
  const line = r => {
    const [cls, word] = DG_TAG[r.status] || ["q", () => esc(r.status)];
    const meta = [esc(r.pos), r.game ? dgGame(r.game) : esc(r.team), r.injury ? esc(r.injury) : ""].filter(Boolean).join(" · ");
    return dgLnHTML(r, meta, `<span class="dg-st ${cls}">${word()}</span>`);
  };
  // The questionable get a line each on the wall, where the panel has the room; a phone keeps the one-line list.
  const lines = d.hurt.filter(r => r.status !== "Questionable").map(line).join("")
    + (q.length ? `<div class="dg-qlines">${q.map(line).join("")}</div>` : "");
  const also = q.length ? `<p class="dg-also"><b>${t("digest.tag.q")}</b>${q.map(r => esc(dgShort(r.n))).join(", ")}</p>` : "";
  return lines + also + dgFootHTML(t("digest.foot.hurt"), "news", t("digest.go.news"));
}

/* Starters (2026-09-29, storyboard JBN1kirnN6jMZNdZK7EmbF): "QB1 over Sanders", "MIN → NYG", or both
   when a traded player starts. `name` shortens the old #1 as the line around it does; the closed
   line (`bare`) leaves out his status, which the phone would cut mid-word. */
const DG_UP = `<svg class="dg-sk dg-sk-up" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 13V3M4 7l4-4 4 4"/></svg>`;
const DG_SWAP = `<svg class="dg-sk dg-sk-mv" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 5h9l-2.5-2.5M13 11H4l2.5 2.5"/></svg>`;
function dgStartWhat(r, name, bare){
  const o = r.over;
  const v = o && {pos: esc(r.pos), name: esc(name(o.n)), status: esc(o.status || "")};
  const over = !o ? "" : o.status && !bare ? t("digest.start.overStatus", v) : t("digest.start.over", v);
  // A move says where he stands on the new chart (McCarthy: the Giants' QB3); a new #1 already said it.
  const m = {from: esc(r.from), team: esc(r.team), pos: esc(r.pos), depth: r.depth};
  const moved = !r.from ? "" : !o && r.depth ? t("digest.start.movedDepth", m) : t("digest.start.moved", m);
  return [over, moved].filter(Boolean).join(", ");
}

/* A new starter is a News block of its own, first in the list (2026-09-29, David: "merge starters";
   it was a row of its own, empty most days and a full-width panel of Blip asleep on the wall). The
   block wears a green tag, "New QB1" or "New team", and its line says over whom or which teams, on
   the day Sleeper's chart changed. The source differs from the headlines' (Sleeper's depth chart, not
   FantasyPros), and the foot names both. */
function dgStartNewsHTML(r){
  const tag = r.over ? t("digest.nw.newStarter", {pos: esc(r.pos)}) : t("digest.nw.newTeam");
  return `<button type="button" class="dg-nw start" data-dgslug="${esc(r.slug)}">
    <span class="dg-hd">${avatarHTML(r)}</span>
    <span class="dg-nw-t"><span class="dg-nw-who"><b>${esc(r.n)}</b><small>${esc(r.pos)} · ${esc(r.team)}</small></span>
    <span class="dg-nw-tag ${r.over ? "up" : "mv"}">${r.over ? DG_UP : DG_SWAP}${tag}</span>
    <ul><li><time>${esc(r.day || "")}</time><span>${dgStartWhat(r, dgShort)}</span></li></ul></span></button>`;
}

function dgMuBody(d){
  const lines = d.best.map(b => dgLnHTML(b, [esc(b.pos), dgVs(b), b.why ? esc(b.why) : ""].filter(Boolean).join(" · "),
    b.pts.toFixed(1))).join("");
  const r = d.record;
  const rec = r ? t("digest.foot.mu", {us: r.ours.score == null ? "—" : r.ours.score.toFixed(2),
                                        pl: r.pl.score == null ? "—" : r.pl.score.toFixed(2), wk: r.through})
    : t("digest.foot.muNone");
  return lines + dgFootHTML(rec, "matchups", d.calls === 1 ? t("digest.go.matchupsOne") : t("digest.go.matchups", {n: d.calls}));
}

/* Each bar grows when the row opens (adds.css): from last week's % rostered to this week's on the
   ESPN fallback, and from nothing to his share of the top count on Sleeper's (2026-09-28). */
function dgAddsBody(d){
  if (d.adds_source === "sleeper"){
    const top = Math.max(1, ...d.adds.map(a => a.count || 0));
    const lines = d.adds.map((a, i) => dgLnHTML(a, a.now != null
      ? t("digest.adds.metaEspn", {pos: esc(a.pos), team: esc(a.team), pct: dgPct(a.now)}) : `${esc(a.pos)} · ${esc(a.team)}`,
      `<span class="dg-plus">${dgBig(a.count)}</span>`,
      `<span class="dg-bar" style="--a:0%;--b:${(100 * a.count / top).toFixed(1)}%;--i:${i}"><i></i><u></u></span>`)).join("");
    return lines + dgFootHTML(t("digest.foot.addsSleeper", {h: d.adds_hours}), "waivers", t("digest.go.waivers"));
  }
  const lines = d.adds.map((a, i) => dgLnHTML(a, t("digest.adds.meta", {pos: esc(a.pos), team: esc(a.team), was: dgPct(a.was), now: dgPct(a.now)}),
    `<span class="dg-plus">${dgSigned(Math.round(a.delta), 0)}</span>`,
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

function dgGemsBody(d){
  const lines = d.gems.map(g => dgLnHTML(g, t("digest.gems.meta", {pos: esc(g.pos), team: esc(g.team), pct: dgPct(g.rostered)}),
    `${g.metric === "tgt_pct" ? dgPct(g.usage) + "%" : g.usage.toFixed(1)}<small>${t("digest.gems.ecr", {pos: esc(g.pos), ecr: g.ecr})}</small>`)).join("");
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
    g.key = g.key || (it.slugs && it.slugs[0]) || (it.n ? slugOf(it.n) : null);
    g.lines.push(it);
  }
  return groups;
}

function dgNewsBody(d){
  const who = typeof searchIndex === "function" ? new Map(searchIndex().map(e => [e.slug, e])) : new Map();
  const line = it => `<li><time>${esc(it.when || "")}</time><span>${esc(it.n ? dgCap(it.rest) : it.headline)}</span></li>`;
  const blocks = dgNewsGroups(d.news).map(g => {
    if (!g.key) return `<div class="dg-nw"><ul>${g.lines.map(line).join("")}</ul></div>`;
    const e = who.get(g.key), p = {n: g.n, slug: g.key, pos: e && e.pos, team: e && e.team};
    const meta = [p.pos, p.team].filter(Boolean).map(esc).join(" · ");
    return `<button type="button" class="dg-nw" data-dgslug="${esc(g.key)}">
      <span class="dg-hd">${avatarHTML(p)}</span>
      <span class="dg-nw-t"><span class="dg-nw-who"><b class="${DG_KIND[g.kind] || ""}">${esc(g.n)}</b><small>${meta}</small></span>
      <ul>${g.lines.map(line).join("")}</ul></span></button>`;
  }).join("");
  const start = d.starters.map(dgStartNewsHTML).join("");
  return `<div class="dg-nws">${start}${blocks}</div>`
    + dgFootHTML(d.starters.length ? t("digest.foot.newsStart") : t("digest.foot.news"), "news", t("digest.go.news"));
}

/* One short list in Top 5's shape: a head, then "K. Mumpfield" and one number per line (Tonight's lists). */
function dgResList(title, rows, num){
  return rows.length ? `<div><h4>${title}</h4><ol>${rows.map(r => `<li><span class="dg-hd sm">${avatarHTML(r)}</span>`
    + `<span>${esc(dgShort(r.n))}</span>${num(r)}</li>`).join("")}</ol></div>` : "";
}

/* Results' body is results.js's (dgResBody). */
const DG_BODY = {res: dgResBody, hurt: dgHurtBody, mu: dgMuBody, wx: dgWxBody, adds: dgAddsBody, t5: dgTop5Body,
                 gems: dgGemsBody, news: dgNewsBody};

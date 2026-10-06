/* ============================== DIGEST: NEED TO KNOW ==============================
   2026-09-29, storyboard https://claude.ai/artifact/96B1dMss6vfyhhsQLUSK4x (option B, David's pick).
   Who will not play and who starts instead, open under the banner, so a reader who never opens a
   row still sees it. It replaced the Hurt row, and new starters left News for it: a new QB1 is the
   other half of the same fact. Both lists are the packet's (ff-jarvis ranks hurt by projected rank);
   the page only joins next week's rank from Ranks so each line says why it matters. */

const DG_NEED_FIRST = 5;    // lines shown before "N more", the list cap every Digest list keeps
let DG_NEED_ALL = false;

/* "RB30", next week's rank from Ranks, or nothing for a player Ranks does not carry. */
function dgNeedRank(slug){
  const r = typeof LIVE_RANKS !== "undefined" && LIVE_RANKS ? LIVE_RANKS.rows.find(x => x.slug === slug) : null;
  return r ? `${esc(r.pos)}${r.rank}` : "";
}

/* A line: his face, his name, then the tag and what happened, with next week's rank at its end
   (2026-09-29, David: "either add headshots or lessen the wide gap"; the rank sat alone at the far
   right of a 550px panel, and the tag stood in a column of its own). */
function dgNeedLine(r, tag, what){
  const rank = dgNeedRank(r.slug);
  return `<button type="button" class="dg-nd" data-testid="digest-need-line" data-dgslug="${esc(r.slug)}">
    <span class="dg-hd">${avatarHTML(r)}</span>
    <span class="dg-nd-t"><b>${esc(dgShort(r.n))}</b><span data-testid="digest-need-what">${tag}<span class="dg-nd-w">${what}${rank ? ` · <i>${rank}</i>` : ""}</span></span></span></button>`;
}

/* A new starter: "New QB1" and over whom (the tag already says QB1); a moved player, "New team". */
function dgNeedStart(r){
  const tag = `<span class="dg-nw-tag ${r.over ? "up" : "mv"}" data-testid="digest-need-tag">${r.over ? t("digest.nw.newStarter", {pos: esc(r.pos)}) : t("digest.nw.newTeam")}</span>`;
  const o = r.over, v = o && {name: esc(dgShort(o.n)), status: esc(o.status || "")};
  const over = !o ? "" : o.status ? t("digest.need.overStatus", v) : t("digest.need.over", v);
  // A move with no one displaced keeps Starters' own words, which name his spot on the new chart.
  if (!o) return dgNeedLine(r, tag, dgStartWhat(r, dgShort));
  const moved = r.from ? t("digest.start.moved", {from: esc(r.from), team: esc(r.team)}) : "";
  return dgNeedLine(r, tag, [over, moved].filter(Boolean).join(" · "));
}

/* Out, IR or doubtful: the tag, then the injury and the game. */
function dgNeedHurt(r){
  const [cls, word] = DG_TAG[r.status] || ["q", () => esc(r.status)];
  const what = [r.injury ? esc(dgCap(r.injury)) : "", r.game ? dgGame(r.game) : esc(r.team)].filter(Boolean).join(" · ");
  return dgNeedLine(r, `<span class="dg-st ${cls}">${word()}</span>`, what);
}

/* The banner's own player is not repeated here, as the Hurt row's line skipped him. */
function dgNeedHTML(d){
  // Not the banner's own player, unless a live headline took the banner (now.js): then he is news here.
  const lead = d.lead && d.lead.rule === "hurt" && !dgLeadLive(d) ? d.hurt[d.lead.index] : null;
  const hurt = d.hurt.filter(r => r !== lead);
  const sit = hurt.filter(r => r.status !== "Questionable"), q = hurt.filter(r => r.status === "Questionable");
  const lines = [...d.starters.map(dgNeedStart), ...sit.map(dgNeedHurt)];
  const shown = DG_NEED_ALL ? lines : lines.slice(0, DG_NEED_FIRST);
  const more = lines.length > shown.length
    ? `<button type="button" class="dg-nd-more" data-testid="digest-need-more" data-dgneedall>${t("digest.need.more", {n: lines.length - shown.length})}</button>` : "";
  // Questionable: a chip each, his face and name, so the list is as tappable as the lines above it
  // and wraps to fill the panel's width (2026-09-30, David: "fill the box better").
  const also = q.length ? `<div class="dg-q" data-testid="digest-need-q"><span class="dg-st q">${t("digest.tag.q")}</span>${q.map(r =>
    `<button type="button" class="dg-q-p" data-testid="digest-need-qp" data-dgslug="${esc(r.slug)}"><span class="dg-hd">${avatarHTML(r)}</span>${esc(dgShort(r.n))}</button>`).join("")}</div>` : "";
  const list = shown.length ? `<div class="dg-nd-list">${shown.join("")}${more}</div>` : "";
  const body = lines.length || q.length ? list + also
    : `<p class="dg-nd-none" data-testid="digest-need-none">${dgWaiting(d) ? t("digest.line.hurtNext", {week: dgRowWeek(d)}) + "." : t("digest.need.none")}</p>`;
  return `<section class="dg-need" data-testid="digest-need" aria-labelledby="dg-need-h">
    <h3 class="dg-sec" data-testid="digest-sec" id="dg-need-h">${t("digest.need.title")}</h3>${body}
    ${dgFootHTML(t("digest.foot.need"), "news", t("digest.go.news"))}</section>`;
}

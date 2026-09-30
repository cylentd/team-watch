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

const dgNeedLine = (slug, tag, name, what) => `<button type="button" class="dg-nd" data-dgslug="${esc(slug)}">
    ${tag}<span class="dg-nd-t"><b>${esc(dgShort(name))}</b><span>${what}</span></span><i>${dgNeedRank(slug)}</i></button>`;

/* A new starter: "New QB1" and over whom; a moved player, "New team". */
function dgNeedStart(r){
  const tag = `<span class="dg-nw-tag ${r.over ? "up" : "mv"}">${r.over ? t("digest.nw.newStarter", {pos: esc(r.pos)}) : t("digest.nw.newTeam")}</span>`;
  return dgNeedLine(r.slug, tag, r.n, dgStartWhat(r, dgShort));
}

/* Out, IR or doubtful: the tag, then the injury and the game. */
function dgNeedHurt(r){
  const [cls, word] = DG_TAG[r.status] || ["q", () => esc(r.status)];
  const what = [r.injury ? esc(dgCap(r.injury)) : "", r.game ? dgGame(r.game) : esc(r.team)].filter(Boolean).join(" · ");
  return dgNeedLine(r.slug, `<span class="dg-st ${cls}">${word()}</span>`, r.n, what);
}

/* The banner's own player is not repeated here, as the Hurt row's line skipped him. */
function dgNeedHTML(d){
  const lead = d.lead && d.lead.rule === "hurt" ? d.hurt[d.lead.index] : null;
  const hurt = d.hurt.filter(r => r !== lead);
  const sit = hurt.filter(r => r.status !== "Questionable"), q = hurt.filter(r => r.status === "Questionable");
  const lines = [...d.starters.map(dgNeedStart), ...sit.map(dgNeedHurt)];
  const shown = DG_NEED_ALL ? lines : lines.slice(0, DG_NEED_FIRST);
  const more = lines.length > shown.length
    ? `<button type="button" class="dg-nd-more" data-dgneedall>${t("digest.need.more", {n: lines.length - shown.length})}</button>` : "";
  const also = q.length ? `<p class="dg-also"><b>${t("digest.tag.q")}</b>${q.map(r => esc(dgShort(r.n))).join(", ")}</p>` : "";
  const body = lines.length || q.length ? shown.join("") + more + also
    : `<p class="dg-nd-none">${dgWaiting(d) ? t("digest.line.hurtNext", {week: d.week + 1}) + "." : t("digest.need.none")}</p>`;
  return `<section class="dg-need" aria-labelledby="dg-need-h">
    <h3 class="dg-sec" id="dg-need-h">${t("digest.need.title")}</h3>${body}
    ${dgFootHTML(t("digest.foot.need"), "news", t("digest.go.news"))}</section>`;
}

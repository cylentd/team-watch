/* ============================== TAKES: THE ROWS ==============================
   One 52px line per take: a tag, a head, the name over his game, our rank over the experts', the
   projection. Our takes lead with the position, since their section already says start or sit and
   the list mixes positions; Pitcher List's lead with their call, since their list mixes both. A tap
   opens the row in place, one open at a time across both lists: ours opens to its evidence and a
   link to the profile, Pitcher List's to their own words and a link to the column. */

const MU_ARROW = `<svg class="mu-arrow" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h9M8.5 4.5L12 8l-3.5 3.5"/></svg>`;
const muTag = tag => tag === "sit" ? t("matchups.call.sit") : t("matchups.call.start");

/* "CIN @ PIT · Sun 10:00 AM", or the game alone when the schedule does not hold it. Our takes add
   whether a reason backs them (v2), so a gut call is visible before the row is opened. */
function muMeta(r){
  const kick = muKick(r);
  const base = kick ? t("matchups.row.meta", {game: muVs(r), kick: esc(kick)}) : muVs(r);
  if (!("backed" in r)) return base;
  return `${base} · <span class="mu-bk${r.backed ? " yes" : ""}">${r.backed ? t("matchups.row.backed") : t("matchups.row.gut")}</span>`;
}

function muRowHTML(key, r, tag, right, body){
  const on = MU_OPEN === key, id = "mu-b-" + key.replace(/[^\w-]/g, "");
  return `<div class="mu-call" data-mukey="${esc(key)}"${on ? " data-open" : ""}>
    <button type="button" class="mu-call-h" aria-expanded="${on}" aria-controls="${id}">
      ${tag}<span class="xf-head mu-hd">${avatarHTML(r)}</span>
      <span class="mu-nm"><b>${esc(r.n)}</b><span>${muMeta(r)}</span></span>${right}</button>
    <div class="mu-b" id="${id}"${on ? "" : " inert"}><div class="mu-in"><div class="mu-pad">${body}</div></div></div>
  </div>`;
}

/* Our take. One no stat backs is shown anyway and says so: the record grades it, and hiding it
   would make the page and the record disagree. */
function muCallHTML(r){
  const ecr = r.ecr == null ? "—" : r.ecr;
  // v2 (week 4 on): the reasons pointing the take's way lead; with none it is a gut call, said once.
  const reasons = (r.reasons || []).length
    ? `<p class="mu-why"><b>${t("matchups.row.backed")}</b> ${r.reasons.map(w => esc(w.t)).join(" · ")}</p>`
    : `<p class="mu-why gut"><b>${t("matchups.row.gut")}</b> ${t("matchups.row.gutWhy")}</p>`;
  const body = `${reasons}<div class="mu-evs">${muEvidence(r, 4)}</div>
    <p class="mu-src"><span>${t("matchups.row.src", {pts: r.pts.toFixed(1)})}</span>
      <button type="button" class="mu-go" data-muslug="${esc(r.slug)}">${t("matchups.row.profile")}${MU_ARROW}</button></p>`;
  const tag = `<span class="mu-tag pos ${esc(r.pos.toLowerCase())}">${esc(r.pos)}</span>`;
  return muRowHTML("c:" + r.slug, r, tag, `<span class="mu-rk"><b>${r.rank}</b> / ${ecr}</span><span class="mu-pt">${r.pts.toFixed(1)}</span>`, body);
}

/* Pitcher List's call: their mark where our ranks sit, their words (clamped) when opened. */
function muPlRowHTML(r){
  const d = LIVE_STARTSIT;
  const link = d.article ? `<a class="mu-go" href="${esc(d.article)}" target="_blank" rel="noopener noreferrer">${t("matchups.pl.read")}${MU_ARROW}</a>` : "";
  const body = `${r.rationale ? `<p class="mu-quote">${t("matchups.pl.quote", {q: esc(r.rationale)})}</p>` : ""}
    <p class="mu-src"><span>${t("matchups.pl.src", {week: d.week})}</span>${link}</p>`;
  const tag = `<span class="mu-tag ${esc(r.call)}">${muTag(r.call)}</span>`;
  return muRowHTML("p:" + r.slug, r, tag, `<span class="mu-plm">${esc(r.pos)}</span><span></span>`, body);
}

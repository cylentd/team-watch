/* ============================== MATCHUPS: THE CALL ROWS ==============================
   One 52px line per call: the tag, a head, the name over his game, our rank over the experts',
   the projection. A tap opens the row in place, one open at a time across both lists: our call
   opens to its evidence and a link to the profile, Pitcher List's to their own words and a link
   to the column. Nothing on the closed line argues; the argument is for whoever opens it. */

const MU_ARROW = `<svg class="mu-arrow" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h9M8.5 4.5L12 8l-3.5 3.5"/></svg>`;
const muTag = tag => tag === "sit" ? t("matchups.call.sit") : t("matchups.call.start");

/* "CIN @ PIT · Sun 10:00 AM", or the game alone when the schedule does not hold it. */
function muMeta(r){
  const kick = muKick(r);
  return kick ? t("matchups.row.meta", {game: muVs(r), kick: esc(kick)}) : muVs(r);
}

function muRowHTML(key, r, right, body){
  const on = MU_OPEN === key, id = "mu-b-" + key.replace(/[^\w-]/g, "");
  return `<div class="mu-call" data-mukey="${esc(key)}"${on ? " data-open" : ""}>
    <button type="button" class="mu-call-h" aria-expanded="${on}" aria-controls="${id}">
      <span class="mu-tag ${esc(r.tag || r.call)}">${muTag(r.tag || r.call)}</span>
      <span class="xf-head mu-hd">${avatarHTML(r)}</span>
      <span class="mu-nm"><b>${esc(r.n)}</b><span>${muMeta(r)}</span></span>${right}</button>
    <div class="mu-b" id="${id}"${on ? "" : " inert"}><div class="mu-in"><div class="mu-pad">${body}</div></div></div>
  </div>`;
}

/* Our call. A call no stat backs is shown anyway and says so: the record grades it, and hiding it
   would make the page and the record disagree. */
function muCallHTML(r){
  const ecr = r.ecr == null ? "—" : r.ecr;
  const unbacked = r.why.length ? "" : `<span class="mu-ev con">${t("matchups.row.unbacked")}</span>`;
  const body = `<div class="mu-evs">${unbacked}${muEvidence(r, 4)}</div>
    <p class="mu-src"><span>${t("matchups.row.src", {pts: r.pts.toFixed(1)})}</span>
      <button type="button" class="mu-go" data-muslug="${esc(r.slug)}">${t("matchups.row.profile")}${MU_ARROW}</button></p>`;
  return muRowHTML("c:" + r.slug, r, `<span class="mu-rk"><b>${r.rank}</b> / ${ecr}</span><span class="mu-pt">${r.pts.toFixed(1)}</span>`, body);
}

/* Pitcher List's call: their mark where our ranks sit, their words (clamped) when opened. */
function muPlRowHTML(r){
  const d = LIVE_STARTSIT;
  const link = d.article ? `<a class="mu-go" href="${esc(d.article)}" target="_blank" rel="noopener noreferrer">${t("matchups.pl.read")}${MU_ARROW}</a>` : "";
  const body = `${r.rationale ? `<p class="mu-quote">${t("matchups.pl.quote", {q: esc(r.rationale)})}</p>` : ""}
    <p class="mu-src"><span>${t("matchups.pl.src", {week: d.week})}</span>${link}</p>`;
  return muRowHTML("p:" + r.slug, r, `<span class="mu-plm">${t("matchups.pl.mark")}</span><span></span>`, body);
}

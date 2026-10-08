/* ============================== START/SIT: BOLD CALLS ==============================
   The calls where our rank and the player's own season average disagree by six spots or more (our
   projection inside the starter line and his average outside it, or the other way; METHODOLOGY
   12.75): a START group, then a SIT group, the widest disagreement first. One 52px line per call:
   the tag, a head, the name over his game, our rank over his season average. A tap opens the row in
   place, one open at a time, to the reasons behind the call and a link to his profile. A group with
   no calls is not drawn; a week with none says so in one line. */

const muTag = call => call === "SIT" ? t("matchups.call.sit") : t("matchups.call.start");

/* Our rank over his season average: "WR17" bold, "avg WR41" under it. */
function muRankHTML(r){
  const avg = r.avg_rank == null ? "—" : `${esc(r.pos)}${r.avg_rank}`;
  return `<span class="mu-rk"><b>${esc(r.pos)}${r.rank}</b><span>${t("matchups.takes.avg", {avg})}</span></span>`;
}

function muTakeHTML(r){
  const key = "t:" + r.slug, on = MU_OPEN === key, id = "mu-b-" + r.slug.replace(/[^\w-]/g, "");
  const chips = r.reasons.length ? `<div class="mu-evs">${r.reasons.map(w => `<span class="mu-ev">${esc(w.t)}</span>`).join("")}</div>` : "";
  return `<div class="mu-call" data-mukey="${esc(key)}"${on ? " data-open" : ""}>
    <button type="button" class="mu-call-h" aria-expanded="${on}" aria-controls="${id}">
      <span class="mu-tag ${r.call === "SIT" ? "sit" : "start"}">${muTag(r.call)}</span>
      <span class="xf-head mu-hd">${avatarHTML({n: r.name, slug: r.slug})}</span>
      <span class="mu-nm"><b>${esc(nameInitial(r.name))}</b><span>${muGame(r)}</span></span>${muRankHTML(r)}</button>
    <div class="mu-b" id="${id}"${on ? "" : " inert"}><div class="mu-in"><div class="mu-pad">${chips}
      <p class="mu-src"><button type="button" class="mu-go" data-muslug="${esc(r.slug)}">${t("matchups.row.profile")}${MU_ARROW}</button></p>
    </div></div></div>
  </div>`;
}

function muTakesHTML(){
  const group = (title, rows) => rows.length ? `<h4 class="mu-grp">${title}</h4>${rows.map(muTakeHTML).join("")}` : "";
  const start = LIVE_SS3.takes.filter(r => r.call === "START"), sit = LIVE_SS3.takes.filter(r => r.call === "SIT");
  if (!start.length && !sit.length) return `<p class="mu-empty">${t("matchups.takes.none")}</p>`;
  return `<section class="mu-card mu-takes" aria-label="${t("matchups.takes.title")}">
    <h3 class="mu-ch"><span>${t("matchups.takes.title")}</span><span class="mu-ck">${t("matchups.takes.cols")}</span></h3>
    ${group(t("matchups.takes.start"), start)}${group(t("matchups.takes.sit"), sit)}</section>`;
}

function muSetOpen(row, open){
  row.toggleAttribute("data-open", open);
  row.querySelector(".mu-call-h").setAttribute("aria-expanded", open);
  row.querySelector(".mu-b").inert = !open;
}

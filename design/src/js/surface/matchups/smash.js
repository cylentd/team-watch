/* ============================== START/SIT: SMASH ==============================
   The players our own projection puts at the top of their position (top 3 QB and TE, top 6 RB and
   WR; METHODOLOGY 12.75), each with the book's main yardage line and anytime-TD price: the legs a
   slip is built from, so the card ends in a link to Slips. One list in position order, QB first.
   A player no book prices shows the number he has; one with neither shows his row alone. */

const MU_ARROW = `<svg class="mu-arrow" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h9M8.5 4.5L12 8l-3.5 3.5"/></svg>`;

/* Every stat spelled out: assemble.py --check finds a copy key only as a literal lookup. */
const MU_STAT = () => ({pass_yds: t("matchups.stat.pass"), rush_yds: t("matchups.stat.rush"), rec_yds: t("matchups.stat.rec")});

/* "72.5 rec yds" over "TD +135"; either may be missing. */
function muLegsHTML(r){
  const l = r.line, stat = l && (MU_STAT()[l.stat] || esc(l.stat));
  const main = l ? `<span><b>${l.value.toFixed(1)}</b> ${stat}</span>` : "";
  const td = r.td_price == null ? "" : `<span>${t("matchups.smash.td", {price: fmtAm(r.td_price)})}</span>`;
  return `<span class="mu-lg">${main}${td}</span>`;
}

function muSmashRowHTML(r){
  return `<button type="button" class="mu-sm" data-muslug="${esc(r.slug)}">
    <span class="xf-head mu-hd">${avatarHTML({n: r.name, slug: r.slug})}</span>
    <span class="mu-nm"><b>${esc(nameInitial(r.name))}</b><span>${esc(r.pos)}${r.rank} · ${muGame(r)}</span></span>
    ${muLegsHTML(r)}</button>`;
}

function muSmashHTML(){
  const rows = LIVE_SS3.smash;
  if (!rows.length) return "";
  return `<section class="mu-card mu-smash" aria-label="${t("matchups.call.smash")}">
    <h3 class="mu-ch"><span class="mu-tag smash" title="${t("matchups.takes.markSmash")}">${t("matchups.call.smash")}</span><span class="mu-ck">${t("matchups.smash.cols")}</span></h3>
    ${rows.map(muSmashRowHTML).join("")}
    <div class="mu-cf"><button type="button" class="mu-go" data-ssgo="parlay">${t("matchups.smash.build")}${MU_ARROW}</button></div>
  </section>`;
}

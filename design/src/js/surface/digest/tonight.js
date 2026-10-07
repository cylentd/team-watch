/* ============================== DIGEST: TONIGHT ==============================
   A standalone slot's game (Thursday, Saturday, Monday) as one card above the ticker (2026-09-28,
   storyboard https://claude.ai/artifact/JSPwg21i9YaTSzhYqAEnQZ). A sentence first, built here from
   ff-jarvis's facts and this page's copy, never written by a model; then who is out, our calls,
   and the top projections. No word of what the books moved since 2026-10-06: that move failed its
   backtest (ff-jarvis METHODOLOGY 12.46, wrong sign), the same result that took Risers & fallers out.
   After kickoff the card is one line and a link to Gameday's Live board. data/digest.js decides when
   it shows and which rows it takes over. */

const dgTnStatus = s => ({Out: t("digest.status.out"), IR: t("digest.status.ir"), Doubtful: t("digest.status.doubtful")})[s] || esc(s);

/* "Caleb Williams is out (hamstring). Case Keenum is CHI's projected QB." */
function dgTnStory(g){
  const o = g.out[0];
  if (!o) return "";
  const say = [t("digest.tn.out", {name: esc(o.n), status: dgTnStatus(o.status)})
    + (o.injury ? ` (${esc(o.injury.toLowerCase())})` : "") + "."];
  const nx = g.next_up.find(n => n.for === o.n);
  if (nx) say.push(t("digest.tn.next", {name: esc(nx.n), team: esc(nx.team)}));
  return say.join(" ");
}

function dgTnSky(w){
  const bits = [w.roof === "dome" ? t("digest.tn.dome") : "", w.temp_f != null ? t("digest.lead.wx.temp", {f: w.temp_f}) : "",
    w.roof !== "dome" && w.wind_mph != null ? t("digest.wx.mph", {n: w.wind_mph}) + " " + t("digest.tn.wind") : "",
    w.short ? esc(w.short) : ""];
  return bits.filter(Boolean).join(" · ");
}

function dgTnCard(g, now){
  const game = `${esc(g.away)} @ ${esc(g.home)}`;
  if (Date.parse(g.ko) <= now){
    // Once it is on, the game is the same block as the last game's (mnf.js): its clock, score and best performer, one tap to its sheet.
    const sched = gdWeekGames().find(x => gdSameClub(x.home, g.home) || gdSameClub(x.away, g.home));
    return `<section class="dg-tn dg-mnf on" data-testid="digest-tn" aria-label="${t("digest.tn.label")}">${sched ? dgMnfFor(sched)
      : `<p class="dg-tn-on"><b>${game}</b> ${t("digest.tn.playing")}</p>`}</section>`;
  }
  const tag = r => `<em class="${r.status === "Doubtful" ? "q" : "dn"}">${r.status === "IR" ? t("digest.tag.ir") : r.status === "Doubtful" ? t("digest.tag.d") : t("digest.tag.out")}</em>`;
  // A START or SIT carries the test it has had (12.75), in its tooltip.
  const call = r => r.call === "BEST" ? `<em>${(r.pts || 0).toFixed(1)}</em>`
    : `<em title="${r.call === "START" ? t("matchups.takes.markStart") : t("matchups.takes.markSit")}">${r.call === "START" ? t("digest.tn.start") : t("digest.tn.sit")}</em>`;
  const lists = dgResList(t("digest.tn.out.h"), g.out, tag) + dgResList(t("digest.tn.calls.h"), g.tcalls, call)
    + dgResList(t("digest.tn.proj.h"), g.projected, r => `<em>${r.pts.toFixed(1)}</em>`);
  const story = dgTnStory(g);
  return `<section class="dg-tn" data-testid="digest-tn" aria-label="${t("digest.tn.label")}">
    <header class="dg-tn-h"><b>${t("digest.tn.head", {game})}</b><time>${esc(dgKick(g))}</time></header>
    <p class="dg-tn-sky">${dgTnSky(g.wx)}</p>${story ? `<p class="dg-tn-story" data-testid="digest-tn-story">${story}</p>` : ""}
    ${lists ? `<div class="dg-t5 dg-tn-lists">${lists}</div>` : ""}
    ${dgFootHTML(t("digest.foot.tn"), "matchups", t("digest.go.matchupsAll"))}</section>`;
}

/* `mnf` is the last game's card (mnf.js) when one shows: it stands in for Tonight's card of the same
   game, so that game's card is skipped here. */
function dgTonightHTML(d, mnf){
  const now = Date.now(), late = mnf ? dgMnfSlot(now) || [] : [];
  const held = g => late.some(x => gdSameClub(x.g.home, g.home) || gdSameClub(x.g.away, g.home));
  const cards = (d.tn || []).filter(g => !held(g)).map(g => dgTnCard(g, now)).join("");
  return mnf || cards ? `<div class="dg-tns">${mnf || ""}${cards}</div>` : "";
}

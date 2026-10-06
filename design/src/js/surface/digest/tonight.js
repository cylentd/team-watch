/* ============================== DIGEST: TONIGHT ==============================
   A standalone slot's game (Thursday, Saturday, Monday) as one card above the ticker (2026-09-28,
   storyboard https://claude.ai/artifact/JSPwg21i9YaTSzhYqAEnQZ). A sentence first, built here from
   ff-jarvis's facts and this page's copy, never written by a model; then who is out, our calls,
   the top projections and what the books moved. After kickoff the card is one line and a link to
   Gameday's Live board. data/digest.js decides when it shows and which rows it takes over. */

const DG_TN_SAY = 3;      // a group's summed move, in points, that earns a sentence; display only
const DG_TN_FLAT = 1;     // under this the other side is "flat"
const DG_TN_GROUP = {QB: "qb", RB: "rb", WR: "pass", TE: "pass"};
const dgTnGroupWord = g => ({qb: t("digest.tn.group.qb"), rb: t("digest.tn.group.rb"), pass: t("digest.tn.group.pass")})[g];
const dgTnStatus = s => ({Out: t("digest.status.out"), IR: t("digest.status.ir"), Doubtful: t("digest.status.doubtful")})[s] || esc(s);

/* "Caleb Williams is out (hamstring). Case Keenum is CHI's projected QB. The books moved CHI's pass
   catchers −9.8 combined: C. Loveland −4.0, L. Burden −3.2, R. Odunze −1.7. PHI is flat (+0.3)." */
function dgTnStory(g){
  const o = g.out[0];
  if (!o) return "";
  const say = [t("digest.tn.out", {name: esc(o.n), status: dgTnStatus(o.status)})
    + (o.injury ? ` (${esc(o.injury.toLowerCase())})` : "") + "."];
  const nx = g.next_up.find(n => n.for === o.n);
  if (nx) say.push(t("digest.tn.next", {name: esc(nx.n), team: esc(nx.team)}));
  const own = g.groups.filter(x => x.team === o.team).sort((a, b) => Math.abs(b.d_pts) - Math.abs(a.d_pts))[0];
  if (own && Math.abs(own.d_pts) >= DG_TN_SAY){
    const names = g.moved.filter(m => m.team === o.team && DG_TN_GROUP[m.pos] === own.group).slice(0, 3)
      .map(m => `${esc(dgShort(m.n))} <span class="${m.d_pts < 0 ? "dn" : "up"}">${dgSigned(m.d_pts, 1)}</span>`).join(", ");
    say.push(t("digest.tn.moved", {team: esc(o.team), group: dgTnGroupWord(own.group),
      pts: `<span class="${own.d_pts < 0 ? "dn" : "up"}">${dgSigned(own.d_pts, 1)}</span>`, names}));
  }
  const other = o.team === g.home ? g.away : g.home;
  const theirs = g.groups.filter(x => x.team === other).reduce((s, x) => s + x.d_pts, 0);
  const pts = `<span class="${theirs < 0 ? "dn" : "up"}">${dgSigned(theirs, 1)}</span>`;
  say.push(Math.abs(theirs) < DG_TN_FLAT ? t("digest.tn.flat", {team: esc(other), pts}) : t("digest.tn.other", {team: esc(other), pts}));
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
  const call = r => `<em>${r.call === "BEST" ? (r.pts || 0).toFixed(1) : r.call === "START" ? t("digest.tn.start") : t("digest.tn.sit")}</em>`;
  const lists = dgResList(t("digest.tn.out.h"), g.out, tag) + dgResList(t("digest.tn.calls.h"), g.tcalls, call)
    + dgResList(t("digest.tn.proj.h"), g.projected, r => `<em>${r.pts.toFixed(1)}</em>`)
    + dgResList(t("digest.tn.moved.h"), g.moved, r => `<em class="${r.d_pts < 0 ? "dn" : "up"}">${dgSigned(r.d_pts, 1)}</em>`);
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

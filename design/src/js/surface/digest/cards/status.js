/* DIGEST CARD: Game status (Friday) and Injury watch (Thursday). The packet's hurt list (LIVE_DIGEST.hurt) as one
   row each: the status at the right, Wednesday to Friday's practice marks between, the injury, the news line and the
   man next in the research. Friday shows every row as ranked; Thursday only the Questionable, because the Out are
   already decided and the Q are the ones still to watch. Facts only: the status is the league's word, not a call.
   Interface: card.js. The status words below are shared with the gains and adds cards. */

/* The DG_PILL key (row.js) for a status; one it has no pill for shows as the data writes it. */
function dgStatusPill(status){
  return ({Questionable: "Q", Doubtful: "D", Out: "OUT", IR: "IR"})[status] || String(status || "");
}

/* "out", "doubtful", "on IR": the status as a verb phrase after a name. */
function dgStatusWord(status){
  return ({Out: t("digest.card.status.wordOut"), Doubtful: t("digest.card.status.wordDoubtful"), IR: t("digest.card.status.wordIr"),
    Questionable: t("digest.card.status.wordQuestionable")})[status] || String(status || "").toLowerCase();
}

/* The injury as the source wrote it ("Hip", "ACL", "Coach's Decision"): lowercasing a first letter turned a
   two-word entry into "coach's Decision". The meta lines put it after a dot, where a capital reads fine. */
const dgInjury = s => String(s || "");

const dgPracticeMark = m => ({DNP: () => t("digest.card.status.markDnp"), LP: () => t("digest.card.status.markLtd"),
  FP: () => t("digest.card.status.markFull")})[m];

/* Three chips, Wednesday, Thursday, Friday; a day with no report logged is an empty chip. [] draws nothing. */
function dgPracticeHTML(practice){
  if (!practice || !practice.length) return "";
  const chips = practice.map(p => {
    const word = dgPracticeMark(p.mark);
    return `<i class="dg-st-mark ${word ? String(p.mark).toLowerCase() : "none"}">${word ? word() : ""}</i>`;
  });
  return `<span class="dg-st-prac" data-testid="digest-st-practice">${chips.join("")}</span>`;
}

function dgStatusRow(r, d){
  const gain = ((d && d.gains) || []).find(g => g.out && g.out.slug === r.slug);
  const next = gain && gain.next ? dgShort(gain.next.name) : "";
  const news = ((d && d.news) || []).find(n => (n.slugs || []).includes(r.slug));
  const v = {team: esc(r.team), injury: esc(dgInjury(r.injury)), next: esc(next)};
  const meta = !r.injury ? t("digest.card.status.metaTeam", v) : next ? t("digest.card.status.metaNext", v) : t("digest.card.status.meta", v);
  const research = [r.injury ? [t("digest.card.status.injury"), r.injury] : null,
    news ? [t("digest.card.status.news"), news.headline] : null,
    next ? [t("digest.card.status.next"), next] : null].filter(Boolean);
  return dgStatusRowHTML(r.status, "status", {slug: r.slug, n: dgShort(r.n), meta, mid: dgPracticeHTML(r.practice), research});
}

/* A row whose answer is the status pill (row.js styles Q, D, OUT and IR; the gains card's rows for a starter
   with no backup use this too). */
const dgStatusRowHTML = (status, card, r) => dgRowHTML(card, {...r, answer: {pill: dgStatusPill(status)}});

function dgCardStatus(ctx){
  const d = ctx.d, thu = ctx.day === "thu";
  const rows = ((d && d.hurt) || []).filter(r => !thu || r.status === "Questionable");
  if (!rows.length) return "";
  // The legend explains the marks, so it is drawn only when some row has one.
  const marked = rows.some(r => (r.practice || []).some(p => p && p.mark));
  return dgCardHTML({id: "status", title: thu ? t("digest.card.status.titleThu") : t("digest.card.status.title"), more: {leaf: "news"},
    body: rows.map(r => dgStatusRow(r, d)).join(""), foot: marked ? t("digest.card.status.foot") : ""});
}

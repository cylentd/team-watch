/* ============================== LEAGUE > TRADES: WHAT CHANGED SINCE THE PRICE ==============================
   2026-10-29 (David: "things can change fast and the edge is in being fast"). ff-jarvis's `trade_signals` puts a
   league's fresh facts in the offers file, `leagues.<league>.signals`, {slug: [{kind, text, stale, date, nums}]}: a
   player back at practice after missed games, a fill-in whose starter is returning, a falling or rising share, a
   trade or role headline. An offer card (lboard/tbcard.js) lists the ones on its players under the To IR and You drop
   lines, the facts the price may lag first, so a reader sees what the number has not caught up with. The text is the
   file's; nothing here computes it. A file from before 2026-10-29 has no signals: the card is as it was. */
const TF_SIG_MAX = 3;          // signal lines a card shows
const TF_SIG_ORDER = ["hurt", "returning", "starter_back", "fill_in", "inherited", "usage_down", "usage_up", "rumor", "role_news"];

/* An offer's signals, pure: [{name, kind, text, stale}] for the players it sends and gets, the kinds the price lags
   (`stale`) first, then the file's kind order, then send before get; at most TF_SIG_MAX. A kind the page does not
   know is left out. */
function tfSignals(o, sigs){
  const rows = [];
  [...o.send, ...o.get].forEach((p, i) => ((sigs || {})[p.slug] || []).forEach(s => {
    if (TF_SIG_ORDER.includes(s.kind)) rows.push({name: p.name, kind: s.kind, text: s.text, stale: !!s.stale, i});
  }));
  const rank = r => [r.stale ? 0 : 1, TF_SIG_ORDER.indexOf(r.kind), r.i];
  rows.sort((a, b) => { const x = rank(a), y = rank(b); return x[0] - y[0] || x[1] - y[1] || x[2] - y[2]; });
  return rows.slice(0, TF_SIG_MAX).map(({name, kind, text, stale}) => ({name, kind, text, stale}));
}

/* Every copy key spelled out: assemble.py --check finds a key only by a literal lookup. */
const tfSigName = kind => ({hurt: t("finder.sig.hurt"), returning: t("finder.sig.returning"),
  starter_back: t("finder.sig.starterBack"), fill_in: t("finder.sig.fillIn"), inherited: t("finder.sig.inherited"),
  usage_down: t("finder.sig.usageDown"), usage_up: t("finder.sig.usageUp"), rumor: t("finder.sig.rumor"),
  role_news: t("finder.sig.roleNews")})[kind];

/* The card's signal lines: "Returning · R. Rice: practiced (Wed LP) ..." each, quiet, the lagging ones marked. */
const tfSignalsHTML = (o, lgd) => tfSignals(o, (lgd || {}).signals)
  .map(s => `<p class="tf-sig${s.stale ? " lag" : ""}" data-testid="finder-signal" title="${s.stale ? t("finder.sig.mark") : ""}"><b>${
    tfSigName(s.kind)}</b> ${esc(nameInitial(s.name))}: ${esc(s.text)}</p>`).join("");

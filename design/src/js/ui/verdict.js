/* The player profile ff-jarvis writes (LIVE_PROFILES), looked up by slug, and the matchup chip a
   row carries when he has a next game with a verdict. The chip only hints that the profile is
   worth opening. An untested verdict gets a dashed outline and the flask mark, never the bare word. */
function profileFor(p){
  if (typeof LIVE_PROFILES === "undefined" || !LIVE_PROFILES || !p) return null;
  return LIVE_PROFILES.players[p.slug || slugOf(p.n)] || null;
}

const VERDICT_CLASS = {PLUS: "plus", MINUS: "minus", EVEN: "even"};
function verdictWord(v){
  return {PLUS: t("profile.verdict.plus"), MINUS: t("profile.verdict.minus"), EVEN: t("profile.verdict.even")}[v];
}

const FLASK_ICON = `<svg class="flask" viewBox="0 0 12 14" aria-hidden="true"><path d="M3.5 1h5M4.5 1v4L1.2 11.6c-.4.8.1 1.4.9 1.4h7.8c.8 0 1.3-.6.9-1.4L7.5 5V1" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round" stroke-linecap="round"/><path d="M2.6 9h6.8l1.4 2.6c.3.6 0 1-.6 1H1.8c-.6 0-.9-.4-.6-1z" fill="currentColor"/></svg>`;

function verdictChipHTML(prof){
  const nx = prof && prof.next;
  if (!nx || !VERDICT_CLASS[nx.verdict]) return "";
  const word = verdictWord(nx.verdict);
  const where = nx.home ? t("profile.next.home") : t("profile.next.away");
  const tip = nx.tested
    ? t("profile.chip.tip", {v: word, where, opp: esc(nx.opp)})
    : t("profile.chip.tipUntested", {v: word, where, opp: esc(nx.opp), method: esc(nx.method)});
  return `<span class="mchip ${VERDICT_CLASS[nx.verdict]}${nx.tested ? "" : " untested"}" title="${tip}">${word}${nx.tested ? "" : FLASK_ICON}</span>`;
}

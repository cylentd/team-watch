/* The lineup warning (2026-09-25): a strip above the roster, Sheet or Cards, naming every starter
   who is out or doubtful this week (injFor, LIVE_INJURY). It says who and why; the swap is yours.
   Questionable starters are not named: most of them play, and a strip that is always there stops
   being read. Nothing when the lineup is clean. */
function injWarnHTML(team){
  const sits = team.roster.filter(p => p.start && injSits(p));
  if (!sits.length) return "";
  const who = sits.map(p => `<b>${esc(nameInitial(p.n))}</b> <span>${injLabel(injFor(p))}</span>`).join(`<i aria-hidden="true">·</i>`);
  return `<div class="inj-warn" role="status">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5 2.8 19.5h18.4z"/><line x1="12" y1="10" x2="12" y2="14"/><circle cx="12" cy="16.9" r=".4"/></svg>
      <p><strong>${sits.length === 1 ? t("teams.inj.warnOne") : t("teams.inj.warnMany", {n: sits.length})}</strong> ${who}</p>
    </div>`;
}

/* A card's or a row's classes for its level: inj-out / inj-d / inj-q, and inj-alert on a starter
   who will likely sit. */
function injClass(p){
  const r = injFor(p);
  if (!r) return "";
  return ` inj-${r.s.toLowerCase()}${p.start && injSits(p) ? " inj-alert" : ""}`;
}

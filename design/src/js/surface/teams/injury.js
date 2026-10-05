/* The lineup warning, a red pill in the "This week" row (2026-10-05; 2026-09-25 it was a full-width
   strip above the roster that cost 50px): one starter who is out or doubtful is named ("S. Barkley
   out", the reason in its tooltip), several are counted ("2 starters out"). Sheet and Cards alike
   (brief.js briefHTML, reel.js reelFoldHTML). Questionable starters are not named: most of them
   play, and a pill that is always there stops being read. Nothing when the lineup is clean. */
function injWarnHTML(team){
  const sits = team.roster.filter(p => p.start && injSits(p));
  if (!sits.length) return "";
  const one = sits.length === 1 ? sits[0] : null;
  const text = one ? t("teams.inj.pillOne", {name: esc(nameInitial(one.n)), status: INJ_WORD[injFor(one).s]().toLowerCase()})
    : t("teams.inj.pillMany", {n: sits.length});
  const tip = sits.map(p => { const r = injFor(p); return `${nameInitial(p.n)}: ${INJ_WORD[r.s]()}${r.note ? ` · ${r.note}` : ""}`; }).join(" / ");
  return `<span class="inj-warn" role="status" title="${esc(tip)}">${text}</span>`;
}

/* The "This week" row's count: "N things to check", or "N to check" beside the sit pill, which takes the
   room of a phone's row (brief.js, reel.js). */
const briefCount = (n, pill) => pill ? t("teams.brief.countShort", {n}) : t("teams.brief.count", {n, s: n === 1 ? "" : "s"});

/* A card's or a row's classes for its level: inj-out / inj-d / inj-q, and inj-alert on a starter
   who will likely sit. */
function injClass(p){
  const r = injFor(p);
  if (!r) return "";
  return ` inj-${r.s.toLowerCase()}${p.start && injSits(p) ? " inj-alert" : ""}`;
}

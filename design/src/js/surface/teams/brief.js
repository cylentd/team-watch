/* "This week": the roster's opening lines, 2026-09-24. It took the ticker's place, but where the
   ticker crawled league-wide injury news, the brief names only this team's players and only what
   asks for a decision: a starter with a status, a must-claim on this league's wire, a player the
   news is about. Three lines at most, in that order, each one a tap to the thing it names. Read
   from data the rows already carry -- nothing here computes a verdict of its own. */

/* The profile index a roster row carries: starters, then bench, then out (drawer.js findPlayer). */
function briefOrder(team){
  return team.roster.filter(p=>p.start)
    .concat(team.roster.filter(p=>!p.start && p.slot!=="OUT"))
    .concat(team.roster.filter(p=>p.slot==="OUT"));
}

function briefLines(team){
  const order = briefOrder(team), at = p => order.indexOf(p);
  const names = ps => ps.map(p => esc(nameInitial(p.n))).join(", ");
  const out = [];

  const flagged = team.roster.filter(p => p.start && p.status);
  if (flagged.length){
    const worst = flagged.some(p => p.status === "OUT") ? "down" : "warn";
    out.push({tone: worst, i: at(flagged[0]),
      text: flagged.length === 1
        ? t("teams.brief.status", {name: esc(nameInitial(flagged[0].n)), status: esc(flagged[0].statusText || flagged[0].status)})
        : t("teams.brief.statusMany", {n: flagged.length, names: names(flagged)})});
  }

  const must = typeof waiverMustIn === "function" ? waiverMustIn(team.key) : 0;
  if (must) out.push({tone: "lime", go: "waivers",
    text: must === 1 ? t("teams.brief.mustOne") : t("teams.brief.mustMany", {n: must})});

  const told = team.roster.filter(p => p.news).sort((a, b) => b.news - a.news || at(a) - at(b));
  // "soft": worth reading, nothing to decide. A phone shows one line and never this kind (brief.css).
  if (told.length) out.push({tone: "soft", i: at(told[0]),
    text: told.length === 1
      ? t("teams.brief.newsOne", {name: esc(nameInitial(told[0].n)), n: told[0].news})
      : t("teams.brief.newsMany", {names: names(told.slice(0, 3))})});

  return out.slice(0, 3);
}

function briefHTML(team){
  const lines = briefLines(team);
  const body = lines.length
    ? lines.map(l => `<button class="brief-line ${l.tone}" ${l.go ? `data-go="${l.go}"` : `data-team="${team.key}" data-i="${l.i}"`}>
        <span class="brief-dot"></span><span class="brief-txt">${l.text}</span><span class="brief-go" aria-hidden="true">&rsaquo;</span>
      </button>`).join("")
    : `<p class="brief-quiet">${t("teams.brief.quiet")}</p>`;
  return `<section class="brief" aria-label="${t("teams.brief.title")}">
    <h2 class="brief-h">${t("teams.brief.title")}</h2>${body}
  </section>`;
}

/* From 1100px the brief is a sticky column beside the rows, pinned just under the nav -- the same
   measurement Waivers' rail takes (wdesk.js wvRailSide), since the nav's height is not a token. */
function wireBrief(v){
  const rl = v.querySelector(".rl"), nav = document.querySelector(".navbar");
  if (rl && nav) rl.style.setProperty("--rl-stick", `${Math.round((parseFloat(getComputedStyle(nav).top) || 0) + nav.offsetHeight)}px`);
  v.querySelectorAll(".brief-line").forEach(el => el.addEventListener("click", () => {
    if (el.dataset.go) navGo(el.dataset.go);
    else openProfile(findPlayer(el.dataset.team, +el.dataset.i), el);
  }));
}

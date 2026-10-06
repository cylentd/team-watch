/* The sheet's body: every stat as one row, best first (2026-09-29, David: "decide what is the most
   important thing the reader wants to see"). The reader tapped the sphere to ask where he is good
   and where he isn't. The card this replaces showed one stat in two sentences, so the answer took
   six taps; the ladder answers it at a glance, with the top and the bottom of the list.

   A row is name, number, a bar that is his rank (full = first), and the rank. A stat too thin to
   rank shows how far he is from its floor instead ("17 of 20 routes"), on a dashed track. Each row
   folds out what the card used to say -- what the rate is out of, the gap to the elite bar, the
   window, what the stat is and why it matters, the weeks as a line -- one row open at a time. */

// Where he sits in the field, 1 at the top: the radar's own radius (sheet.js radarHTML's k).
const ladderPct = rk => rk[1] > 1 ? 1 - (rk[0] - 1) / (rk[1] - 1) : 1;

/* Best first: ranked stats by how high he sits in their field (#6 of 62 above #3 of 12), then the
   ones too thin to rank, then any with no number at all. */
function ladderOrder(s){
  return s.axes.map(a => {
    const rk = sheetRank(s.pos, a.id, s.row.slug), v = s.row.v[a.id];
    const band = rk ? 0 : v !== null && v !== undefined ? 1 : 2;
    return {a, rk, v, band, pct: rk ? ladderPct(rk) : 0, elite: sheetElite(s, a, rk)};
  }).sort((x, y) => x.band - y.band || y.pct - x.pct);
}

/* Top tenth (at least the top three) in the position's tint, the bottom half dim: one bright bar
   per strength, so the eye lands on those and the weak spots recede, as the radar's labels do. */
function ladderBarHTML(s, x){
  if (x.rk){
    const cls = x.rk[0] <= Math.max(3, Math.floor(x.rk[1] / 10)) ? "top" : x.pct < .5 ? "low" : "";
    return `<span class="pf-lr-bar"><i class="${cls}" style="--w:${Math.max(3, x.pct * 100).toFixed(0)}%"></i></span>`;
  }
  const smp = sheetSample(s.row, x.a.id), floor = x.a.floor;
  const w = x.band === 1 && smp && floor ? Math.min(1, smp[1] / floor) : 0;
  return `<span class="pf-lr-bar thin"><i style="--w:${(w * 100).toFixed(0)}%"></i></span>`;
}

// The rank over its field, or under the floor what he has of what it needs, or a dash.
function ladderRankHTML(s, x){
  if (x.rk) return `<b>${rankMark(x.rk)}</b><small>${t("profile.ladder.of", {of: x.rk[1]})}</small>`;
  const smp = sheetSample(s.row, x.a.id), unit = SAMPLE_UNIT[x.a.den];
  if (x.band === 1 && smp && x.a.floor && unit)
    return `<b class="dim">${t("profile.ladder.have", {n: smp[1], floor: x.a.floor})}</b><small>${unit()}</small>`;
  return `<b class="dim">—</b>`;
}

/* The window comes from the stat's own weeks, not his games played: route stats wait on heatradar,
   which publishes a week at a time, so one row can be a week behind the one above it. With no
   weekly rows, games played is the only sample there is to name. */
function ladderWindow(s, wk){
  if (!wk.length) return t("profile.sheet.games", {g: s.row.g});
  const a = wk[0].wk, b = wk[wk.length - 1].wk;
  return a === b ? t("profile.stat.week", {n: a}) : t("profile.stat.weeks", {a, b});
}

function ladderMoreHTML(s, x){
  const a = x.a, wk = statWeeks(s.row.slug, a.id), thin = x.band === 1;
  // Never "over the elite bar" on a sample too thin to rank: that is the claim it can't make.
  const gap = a.elite === null || a.elite === undefined || x.band ? "" : eliteGapHTML(x.v, a, s.row);
  const smp = sampleText(s.row, a);
  // Where the bar comes from, when it is not 2018-2025 history (ff-jarvis `elite_src`).
  const src = !gap ? "" : a.elite_src === "season" ? `<span>${t("profile.stat.barSeason")}</span>`
    : a.elite_src === "published" ? `<span>${t("profile.stat.barPublished")}</span>` : "";
  const facts = [smp ? `<span>${smp}</span>` : "", gap, src, `<span>${ladderWindow(s, wk)}</span>`].join("");
  const unit = SAMPLE_UNIT[a.den];
  const floor = thin && unit ? `<p class="pf-lr-floor" data-testid="profile-lr-floor">${t("profile.ladder.floor", {floor: a.floor, unit: unit()})}</p>` : "";
  const def = AXIS_DEF[a.id]
    ? `<p class="pf-lr-def" data-testid="profile-lr-def">${AXIS_DEF[a.id]()}${AXIS_WHY[a.id] ? `<span class="pf-lr-why" data-testid="profile-lr-why">${AXIS_WHY[a.id]()}</span>` : ""}</p>` : "";
  // Read against the same bar, so a week above it is visibly a week above it. One week is a
  // point, not a line, and the window already names it.
  const line = wk.length > 1 ? sparkHTML(wk.map(r => r.v[a.id]), 160, 30, a.elite) : "";
  return `<div class="pf-lr-more"><div class="pf-lr-facts" data-testid="profile-lr-facts">${facts}</div>${floor}${def}${line}</div>`;
}

/* `name` makes the rows one accordion natively: opening one closes the last, so the list never
   grows more than one fold longer than it was. */
function ladderHTML(s, sel){
  return `<div class="pf-ladder">${ladderOrder(s).map((x, i) => `<details class="pf-lr${x.a.id === sel ? " on" : ""}${x.elite ? " elite" : ""}" data-testid="profile-lr" name="pf-ladder" data-col="${esc(x.a.id)}" style="--i:${i}">
    <summary data-testid="profile-lr-toggle"><span class="pf-lr-n" data-testid="profile-lr-name">${esc(axisName(x.a))}</span><b class="pf-lr-v${x.band ? " dim" : ""}" data-testid="profile-lr-value">${usageFmt(x.v, x.a.fmt)}</b>${ladderBarHTML(s, x)}<span class="pf-lr-rk" data-testid="profile-lr-rank">${ladderRankHTML(s, x)}</span></summary>
    ${ladderMoreHTML(s, x)}</details>`).join("")}</div>`;
}

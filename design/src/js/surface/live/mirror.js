/* ============================== LIVE: THE MIRRORED LINEUPS ==============================
   One row per starter slot, ESPN's way (2026-10-04, storyboard
   https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV, option A): my starter on the left, the
   opponent's on the right, the slot between them as a pill in the position's colour. Each half is
   his name over his game's clock (a second button: it opens that game's sheet), points beside the
   name and the projection under them. A row is one line of two, so nine starters and the score
   above them fit one phone screen. The benches sit behind a toggle, mirrored the same way. */

/* The slot pill's colour: a slot that is one position wears it; a flex slot wears a blend of the
   positions it takes (David, 2026-10-05). */
const GD_SLOT_POS = {
  QB: "qb", RB: "rb", WR: "wr", TE: "te", K: "k", DEF: "def", "D/ST": "def", DST: "def",
  FLEX: "mix flex", FLX: "mix flex", "W/R/T": "mix flex", "RB/WR/TE": "mix flex",
  "W/R": "mix wrrb", "W/T": "mix wrte", OP: "mix op", SFLX: "mix op", SUPERFLEX: "mix op", "Q/W/R/T": "mix op",
};

const gdName = r => r.pos === "DEF" ? r.n.replace(/\s*D\/ST$/, "") : gdShort(r);

/* Points over projection: lime while his game is on (the row's tint says it too), a flame beside
   them once he smashed it (board.js gdSmashed), a dash before kickoff. */
function gdPtsHTML(r){
  const pulse = r.sid && GD_PULSE[r.sid] !== undefined ? `<em class="up">${gdSigned(GD_PULSE[r.sid])}</em>` : "";
  if (r.state === "pre_game") return `<span class="gd-pts pre">—</span>`;
  const flame = gdSmashed(r) ? `<svg class="gd-flame" viewBox="0 0 24 24" role="img" aria-label="${t("live.row.smashed")}">${GD_FLAME}</svg>` : "";
  return `<span class="gd-pts">${pulse}${flame}${gdNum(r.pts || 0)}</span>`;
}
function gdProjHTML(r){
  const p = projFor(r);
  return `<span class="gd-proj">${p === null ? "" : gdNum(p)}</span>`;
}

/* His name; a starter of the reader's who left his game hurt and is not back wears a red "Hurt" beside
   it (data/gameday/hurt.js, 2026-10-04). Anyone else draws the bare name, as before: `own` is whether
   his side of the row is the reader's team (gdMine). */
function gdNameHTML(r, own){
  const h = GD_HURT[r.slug];
  if (!own || !h || h.back || r.state === "pre_game") return `<b>${esc(gdName(r))}</b>`;
  return `<span class="gd-nm"><b>${esc(gdName(r))}</b><i class="gd-hurt" aria-label="${esc(t("live.hurt.label"))}">${t("live.hurt.chip")}</i></span>`;
}

/* His game's second line: the clock, then the club's side of it. Before kickoff the opponent, while
   it is on the score from his club's side, once final the result. The clock is ESPN's, the score
   Sleeper's (nflnow.js gdClubScore). */
function gdClockLine(r){
  const c = gdClockOf(r.team), g = gdGameOf(r.team);
  let tail = "";
  if (g){
    const a = gdClubScore(r.team, g.opp), b = gdClubScore(g.opp, r.team), known = a !== null && b !== null && a !== undefined && b !== undefined;
    if (c.state === "pre" || !known) tail = g.home ? t("live.game.vs", {opp: esc(g.opp)}) : t("live.game.at", {opp: esc(g.opp)});
    else if (c.state === "in") tail = t("live.row.score", {a, b});
    else tail = a > b ? t("live.game.won", {a, b}) : a < b ? t("live.game.lost", {a, b}) : t("live.game.tie", {a, b});
  }
  return [esc(c.label), tail].filter(Boolean).join(" · ");
}

/* One half of a row. Two buttons, never nested: the name opens his profile, the clock his game.
   `own`: this half is the reader's team. */
function gdHalfHTML(r, cls, own){
  if (!r) return `<div class="gd-h ${cls} empty"></div>`;
  const line = gdClockLine(r), g = gdGameOf(r.team);
  const clock = line && g
    ? `<button type="button" class="gd-ck" data-gdnfl="${esc(g.key)}" data-gdfocus="${esc(r.slug)}" aria-haspopup="dialog">${line}</button>`
    : `<span class="gd-ck">${line}</span>`;
  return `<div class="gd-h ${cls}${r.state === "in_game" ? " on" : r.state === "pre_game" ? " pre" : ""}">
    <button type="button" class="gd-nb" data-gdslug="${esc(r.slug)}" data-gdn="${esc(r.n)}" data-gdpos="${esc(r.pos)}" data-gdteam="${esc(r.team)}">
      ${gdNameHTML(r, own)}${gdPtsHTML(r)}</button>
    <span class="gd-sub">${clock}${gdProjHTML(r)}</span></div>`;
}

/* Mine against theirs, slot by slot: each of my slots takes the next opponent starter in the same
   slot, then what is left pairs in order; the shorter side is padded with an empty half. */
function gdPairs(mine, theirs){
  const used = new Set();
  const out = mine.map(r => {
    const j = theirs.findIndex((x, i) => !used.has(i) && x.slot === r.slot);
    if (j >= 0) used.add(j);
    return [r, j >= 0 ? theirs[j] : null];
  });
  const rest = theirs.filter((x, i) => !used.has(i));
  for (const p of out) if (!p[1] && rest.length) p[1] = rest.shift();
  return out.concat(rest.map(x => [null, x]));
}

/* `own` is [the left half is the reader's, the right half is]. */
function gdMirrorRowHTML(l, r, own){
  const slot = (l || r).slot;
  return `<div class="gd-mr"><span class="gd-sl ${GD_SLOT_POS[slot] || ""}">${esc(slot)}</span>
    ${gdHalfHTML(l, "l", own[0])}${gdHalfHTML(r, "r", own[1])}</div>`;
}

const gdMirrorRows = (a, b, own) => gdPairs(a, b).map(([l, r]) => gdMirrorRowHTML(l, r, own)).join("");

const GD_CHEVRON = `<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M3 4.5 6 7.5l3-3"/></svg>`;

/* Starters, then a Benches row that opens the two benches under it: dimmed, points shown, never in
   the total. Open or closed is remembered in memory only (GD_BENCHES). */
function gdMirrorHTML(a, b, lg){
  const mine = gdMine(lg), own = [!!mine && a.id === mine, !!mine && b.id === mine];
  const bench = a.bench.length || b.bench.length ? `<button type="button" class="gd-bt" data-gdbench aria-expanded="${GD_BENCHES}">
      <span>${t("live.bench.toggle")}</span>${GD_CHEVRON}</button>
    ${GD_BENCHES ? `<section class="gd-mirror bn">${gdMirrorRows(a.bench, b.bench, own)}</section>` : ""}` : "";
  return `<section class="gd-mirror">${gdMirrorRows(a.rows, b.rows, own)}</section>${bench}`;
}

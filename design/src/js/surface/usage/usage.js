/* The Usage grid. One position, one week, the seven columns that position is judged on. */

const usageCols = pos => (USAGE.cols || {})[pos] || [];

/* Every kept row for a position and week, keyed by slug, so the previous week is one lookup
   away. Change mode needs it; so does knowing that a blank week is a week he did not play. */
function usageWeekMap(pos, wk){
  const out = {};
  (USAGE.rows || []).forEach(r => { if (r.pos === pos && r.wk === wk) out[r.slug] = r; });
  return out;
}

function usageRows(){
  const rows = (USAGE.rows || []).filter(r => r.pos === USAGE_POS && r.wk === USAGE_WEEK);
  const mine = USAGE_MINE ? usageMine() : null;
  const shown = mine ? rows.filter(r => mine.has(r.slug)) : rows;
  const sort = USAGE_SORT || (USAGE.rankBy || {})[USAGE_POS] || (usageCols(USAGE_POS)[0] || {}).id;
  const prev = USAGE_MODE === "change" ? usageWeekMap(USAGE_POS, USAGE_WEEK - 1) : null;
  const key = r => {
    if (!prev) return r.v[sort];
    const was = prev[r.slug];
    return was ? (r.v[sort] ?? 0) - (was.v[sort] ?? 0) : null;
  };
  // A null sorts last in either direction: "he has no number here" is not a big or a small one.
  return shown.slice().sort((a, b) => {
    const x = key(a), y = key(b);
    if (x === null || x === undefined) return 1;
    if (y === null || y === undefined) return -1;
    return USAGE_DESC ? y - x : x - y;
  });
}

function usageCell(r, was, col){
  if (USAGE_MODE === "change"){
    if (!was) return `<div class="ucell u-none">—</div>`;
    const d = (r.v[col.id] ?? 0) - (was.v[col.id] ?? 0);
    return `<div class="ucell ${usageTone(d)}">${usageFmtDelta(d, col.fmt)}</div>`;
  }
  return `<div class="ucell ${usageBand(r.p[col.id])}">${usageFmt(r.v[col.id], col.fmt)}</div>`;
}

/* shortName, not the full name: at 360px this column ellipsised "Omarion Hampt...", "Jacory
   Croskey..." and "TreVeyon Hend...", and a surname cut in half is the one part of the row a
   reader needs. "O. Hampton" fits where "Omarion Hampton" does not, and it is the app's spelling
   for a name in small type everywhere else. */
function usageRow(r, i, cols, prev){
  const was = prev ? prev[r.slug] : null;
  const mine = usageMine().has(r.slug);
  // The stagger stops at the tenth row. Carried down all 60, the last one starts a full second
  // after the first, which reads as a broken table rather than an entrance -- and it made the
  // rendered-DOM golden depend on when the screenshot happened to fire.
  return `<div class="urow ${mine ? "u-mine" : ""}" style="animation-delay:${40 + Math.min(i, 10) * 18}ms"
    data-usage="${esc(r.slug)}" role="button" tabindex="0">
    <div class="uname"><b>${shortName(r.n)}</b>${mine ? `<i class="udot" aria-hidden="true"></i>` : ""}</div>
    <div class="uteam">${esc(r.team || "—")}</div>
    ${cols.map(c => usageCell(r, was, c)).join("")}
  </div>`;
}

function usageHead(cols){
  const active = USAGE_SORT || (USAGE.rankBy || {})[USAGE_POS];
  return `<div class="uhead">
    <div>${t("usage.table.player")}</div>
    <div>${t("usage.table.team")}</div>
    ${cols.map(c => `<button class="ucol ${c.id === active ? "on" : ""}" data-usort="${c.id}"
      aria-pressed="${c.id === active}">${esc(c.label)}${c.id === active ? (USAGE_DESC ? " ▾" : " ▴") : ""}</button>`).join("")}
  </div>`;
}

/* The legend says what the colour is, in the one sentence that stops it being read as a grade.
   Percentile bands, not "elite" and "trash": a red 0 at goal line is one game script, not a
   judgment on the player. */
function usageLegend(){
  const bands = [["b5", t("usage.band.top10")], ["b4", t("usage.band.top25")],
                 ["b3", t("usage.band.middle")], ["b2", t("usage.band.low25")],
                 ["b1", t("usage.band.low10")]];
  return `<div class="ukey">
    <span class="lbl">${t("usage.key.label")}</span>
    ${bands.map(([c, l]) => `<span class="ubadge ${c}">${l}</span>`).join("")}
    <span style="flex:1"></span>
    <span class="note">${USAGE_MODE === "change" ? t("usage.key.changeNote") : t("usage.key.levelNote")}</span>
  </div>`;
}

function usageControls(){
  const weeks = USAGE.weeks || [];
  return `<div class="filters">
    <span class="lbl">${t("usage.filter.position")}</span>
    ${USAGE_POSITIONS.filter(p => usageCols(p).length).map(p =>
      `<button class="chip" data-upos="${p}" aria-pressed="${USAGE_POS === p}">${p}</button>`).join("")}
    <span class="lbl uspace">${t("usage.filter.week")}</span>
    ${weeks.map(w => `<button class="chip" data-uweek="${w}" aria-pressed="${USAGE_WEEK === w}">${w}</button>`).join("")}
    <span style="flex:1"></span>
    <button class="chip" data-umode="level" aria-pressed="${USAGE_MODE === "level"}">${t("usage.mode.level")}</button>
    <button class="chip" data-umode="change" aria-pressed="${USAGE_MODE === "change"}" ${weeks.length < 2 ? "disabled" : ""}>${t("usage.mode.change")}</button>
    <button class="chip" data-umine aria-pressed="${USAGE_MINE}">${t("usage.filter.mine")}</button>
  </div>`;
}

function usageHTML(){
  const cols = usageCols(USAGE_POS);
  if (!cols.length) return `<div class="wrap"><div class="state-empty"><div><b>${t("usage.empty.noGridTitle")}</b><span>${t("usage.empty.noGridSub")}</span></div></div></div>`;
  const rows = usageRows();
  const prev = USAGE_MODE === "change" ? usageWeekMap(USAGE_POS, USAGE_WEEK - 1) : null;
  // Two fixed columns (player, team) then one per stat: the count changes with the position, so
  // the template is built here rather than pinned in the stylesheet.
  const template = `minmax(128px,1.6fr) 46px repeat(${cols.length}, minmax(52px, 1fr))`;
  return `<div class="wrap">
    ${usageControls()}
    ${usageLegend()}
    <div class="utable" style="--ucols:${template}">
      ${usageHead(cols)}
      ${rows.length ? rows.map((r, i) => usageRow(r, i, cols, prev)).join("")
        : `<div class="state-empty" style="margin:26px 0;min-height:120px"><div><b>0</b><span>${t("usage.empty.noPlayers")}</span></div></div>`}
    </div>
    <div class="note ufoot">${t("usage.foot.source", {n: rows.length, week: USAGE_WEEK, pos: USAGE_POS})}</div>
  </div>`;
}

function wireUsage(v){
  const set = (sel, fn) => v.querySelectorAll(sel).forEach(b => b.addEventListener("click", () => { fn(b); render(); }));
  set("[data-upos]",  b => { USAGE_POS = b.dataset.upos; USAGE_SORT = null; USAGE_DESC = true; });
  set("[data-uweek]", b => { USAGE_WEEK = +b.dataset.uweek; });
  set("[data-umode]", b => { USAGE_MODE = b.dataset.umode; });
  set("[data-umine]", () => { USAGE_MINE = !USAGE_MINE; });

  /* Clicking the live column flips the direction; a new column starts descending, because the
     question a usage column answers is always "who had the most". Scroll is held because a
     re-sort is a read of the same list, not a move to a new one. */
  v.querySelectorAll("[data-usort]").forEach(b => b.addEventListener("click", () => {
    const id = b.dataset.usort, active = USAGE_SORT || USAGE.rankBy[USAGE_POS];
    if (id === active) USAGE_DESC = !USAGE_DESC; else { USAGE_SORT = id; USAGE_DESC = true; }
    const y = window.scrollY; render(); window.scrollTo(0, y);
  }));

  v.querySelectorAll("[data-usage]").forEach(el => {
    const r = USAGE.rows.find(x => x.slug === el.dataset.usage && x.pos === USAGE_POS && x.wk === USAGE_WEEK);
    const open = () => openProfile(r && {n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
    el.addEventListener("click", open);
    el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); open(); } });
  });
}

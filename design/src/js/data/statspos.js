/* ============================== STATS' ONE POSITION ==============================
   2026-10-06 (David picked "A Slide", storyboard https://claude.ai/artifact/G93YHzFMaUAHo1fvmMx3h7). Each
   Stats view kept its own position until then, so WR on Ranks opened Leaders on RB. Now the reader picks
   once and every Stats view that has the position shows it; on a phone the pick is a strip above the
   bottom bar (chrome/statspos.js). Pure and DOM-free (tests/test_js_statspos.py).

   The choice is {shared, core}: the position last picked anywhere in Stats (null until the first pick, so
   each view opens where it always did), and the last of QB to TE picked, which a view of QB to TE only
   falls back to. Kept for the session only: not in the hash, not
   in storage (CLAUDE.md, "the grid's position and week reset on purpose").

   A view declares itself once, at load, with statsPosView(leaf, {attr, opts, label, use}):
     attr    the data attribute its own chips carry ("rkpos" -> data-rkpos); a strip segment carries it
             too, so a selector for the view's chip finds the one on screen
     opts    () -> what statsPosList needs from the view now: {ros, extra, have}
     label   position -> the words on the segment (literal copy keys in the view)
     use     position -> make it the one the view draws (and drop what belonged to the old one) */
const STATS_CORE = ["QB", "RB", "WR", "TE"];
const STATS_POS_BASE = {ranks: [...STATS_CORE, "FLEX"], board: STATS_CORE, movers: ["ALL", "RB", "WR", "TE"],
  usage: STATS_CORE, schedule: STATS_CORE};
let STATS_POS = {shared: null, core: "RB"};   // nothing picked yet: Work vs points opens on All, the rest on RB

const STATS_VIEWS = {};
function statsPosView(leaf, declare){ STATS_VIEWS[leaf] = declare; }

/* statsPosList(leaf, o) -> the view's positions, in strip order. [] for a view with no position (Highlights).
   o.ros: Ranks' Rest of season, QB to TE only. o.extra: Ranks' D/ST and K tabs the league has (data/dst.js
   dstTabs). o.have: the positions the view has data for (Leaders' lanes, Usage's columns), when it says. */
function statsPosList(leaf, o = {}){
  const base = STATS_POS_BASE[leaf];
  if (!base) return [];
  const all = leaf === "ranks" ? (o.ros ? STATS_CORE : [...base, ...(o.extra || [])]) : base;
  return o.have ? all.filter(p => o.have.includes(p)) : all;
}

/* statsPosShown(list, state) -> what the view shows. The shared position when it has it. FLEX (Ranks) and All
   (Work vs points) are both RB, WR and TE together, so each stands for the other, and All stands in for a
   position Work vs points lacks (QB, D/ST, K). Otherwise the last of QB to TE picked, else RB, else the first. */
function statsPosShown(list, state){
  if (!list.length) return null;
  if (list.includes(state.shared)) return state.shared;
  const twin = {ALL: "FLEX", FLEX: "ALL"}[state.shared];
  if (twin && list.includes(twin)) return twin;
  if (list.includes("ALL")) return "ALL";
  if (list.includes(state.core)) return state.core;
  return list.includes("RB") ? "RB" : list[0];
}

/* statsPosPick(state, pos) -> the new state: pos is shared, and remembered as the core when it is QB to TE. */
const statsPosPick = (state, pos) => ({shared: pos, core: STATS_CORE.includes(pos) ? pos : state.core});

/* statsSegAt(x, left, width, n) -> the index of the segment under a finger at x, on a strip of n equal
   segments from left, width wide. A finger past either end holds the end segment, as the prototype did. */
const statsSegAt = (x, left, width, n) => Math.max(0, Math.min(n - 1, Math.floor((x - left) / (width / n))));
